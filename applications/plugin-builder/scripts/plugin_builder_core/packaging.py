"""Guarded deterministic packaging of W2-approved plugin candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile

from .bootstrap import plugin_authoring
from .candidate_identity import expected_tool_bindings, runtime_approval_errors, runtime_identity_fields
from .mcp_realization import validate_mcp_projection
from .implementation_plan import canonical_bytes, write_bytes_transactionally
from .session_contract import validate_session


@dataclass(frozen=True)
class PackageOutcome:
    status: str
    errors: tuple[str, ...]
    package_sha256: str | None = None
    path: str | None = None
    metadata_sha256: str | None = None


def _load(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _publish_pair(source_zip: Path, source_metadata: Path, destination_zip: Path, destination_metadata: Path, temporary: Path) -> None:
    destination_zip.parent.mkdir(parents=True, exist_ok=True)
    backup_zip = temporary / "previous.zip"
    backup_metadata = temporary / "previous-metadata.json"
    moved_zip = moved_metadata = False
    try:
        if destination_zip.exists():
            os.replace(destination_zip, backup_zip)
            moved_zip = True
        if destination_metadata.exists():
            os.replace(destination_metadata, backup_metadata)
            moved_metadata = True
        os.replace(source_zip, destination_zip)
        os.replace(source_metadata, destination_metadata)
    except OSError:
        destination_zip.unlink(missing_ok=True)
        destination_metadata.unlink(missing_ok=True)
        if moved_zip and backup_zip.exists():
            os.replace(backup_zip, destination_zip)
        if moved_metadata and backup_metadata.exists():
            os.replace(backup_metadata, destination_metadata)
        raise


def package_candidate(session_path: Path) -> PackageOutcome:
    session_file = Path(session_path)
    session = _load(session_file)
    if session is None or session.get("schema_version") != 2:
        return PackageOutcome("FAIL", ("package.session_invalid",))
    if not isinstance(session.get("w2"), dict) or session["w2"].get("approved") is not True:
        return PackageOutcome("BLOCKED", ("package.w2_required",))
    if session.get("stage") in {"H1", "E2"}:
        return PackageOutcome("BLOCKED", ("package.session_inactive",))
    candidate_id = session.get("candidate")
    verification_id = session.get("verification")
    if not isinstance(candidate_id, dict) or not isinstance(verification_id, dict):
        return PackageOutcome("BLOCKED", ("package.evidence_required",))
    root = session_file.parent
    candidate = root / str(candidate_id.get("path", ""))
    report_path = root / str(verification_id.get("path", ""))
    errors: list[str] = []
    if not candidate.is_dir() or plugin_authoring.tree_sha256(candidate) != candidate_id.get("sha256"):
        errors.append("package.candidate_sha256_mismatch")
    try:
        report_bytes = report_path.read_bytes()
    except OSError:
        report_bytes = b""
    if sha256(report_bytes).hexdigest() != verification_id.get("sha256"):
        errors.append("package.verification_sha256_mismatch")
    if session["w2"].get("candidate_sha256") != candidate_id.get("sha256"):
        errors.append("package.w2_candidate_mismatch")
    if session["w2"].get("verification_sha256") != verification_id.get("sha256"):
        errors.append("package.w2_verification_mismatch")
    if any(item.get("required") is True and item.get("state") == "FAIL" for item in verification_id.get("results", [])):
        errors.append("package.required_failure")
    contract_errors = validate_session(session)
    if contract_errors:
        errors.extend(f"package.session:{item}" for item in contract_errors)
    existing_package = session.get("package")
    if isinstance(existing_package, dict):
        existing_archive = root / str(existing_package.get("path", ""))
        existing_metadata = root / str(existing_package.get("metadata_path", ""))
        try:
            existing_archive_hash = sha256(existing_archive.read_bytes()).hexdigest()
        except OSError:
            existing_archive_hash = ""
        try:
            existing_metadata_hash = sha256(existing_metadata.read_bytes()).hexdigest()
        except OSError:
            existing_metadata_hash = ""
        if existing_archive_hash != existing_package.get("sha256"):
            errors.append("package.existing_archive_sha256_mismatch")
        if existing_metadata_hash != existing_package.get("metadata_sha256"):
            errors.append("package.existing_metadata_sha256_mismatch")
    if errors:
        return PackageOutcome("BLOCKED", tuple(sorted(set(errors))))

    report = _load(report_path)
    manifest = _load(candidate / "PLUGIN-BUILDER-MANIFEST.json")
    plugin = _load(candidate / "plugin.json")
    if report is None or manifest is None or plugin is None:
        return PackageOutcome("FAIL", ("package.input_manifest_invalid",))
    if report.get("schema") not in {"plugin-builder-verification-report-v2", "plugin-builder-verification-report-v3"}:
        return PackageOutcome("BLOCKED", ("package.verification_schema_unsupported",))
    if report.get("status") != "PASS":
        return PackageOutcome("BLOCKED", ("package.verification_incomplete",))
    if any(item.get("required") is True and item.get("state") != "PASS" for item in report.get("checks", [])):
        return PackageOutcome("BLOCKED", ("package.required_check_incomplete",))
    plan_identity = session.get("plan") or {}
    plan_path = root / str(plan_identity.get("path", ""))
    try:
        plan_bytes = plan_path.read_bytes()
        plan_hash = sha256(plan_bytes).hexdigest()
        plan = json.loads(plan_bytes.decode("ascii"))
    except OSError:
        plan_hash = ""
        plan = None
    except (UnicodeError, json.JSONDecodeError):
        plan_hash = ""
        plan = None
    if plan_hash != plan_identity.get("sha256") or plan_hash != (session.get("w1") or {}).get("plan_sha256") or plan_hash != candidate_id.get("plan_sha256") or plan_hash != manifest.get("plan_sha256"):
        return PackageOutcome("BLOCKED", ("package.plan_sha256_mismatch",))
    if manifest.get("tool_contracts") != plan.get("tools") or manifest.get("tool_bindings") != expected_tool_bindings(plan.get("tools", [])):
        return PackageOutcome("BLOCKED", ("package.tool_bindings_mismatch",))
    if isinstance(plan.get("capabilities"), list):
        runtime_errors = list(runtime_approval_errors(plan, plan_identity, session.get("w1") or {}))
        if manifest.get("schema") != "plugin-builder-candidate-manifest-v3" or report.get("schema") != "plugin-builder-verification-report-v3":
            runtime_errors.append("package.runtime_schema_mismatch")
        try:
            expected_runtime = runtime_identity_fields(plan, candidate)
        except (ValueError, OSError, KeyError, TypeError) as error:
            runtime_errors.append(f"package.runtime_identity_invalid:{error}")
        else:
            for key, value in expected_runtime.items():
                if manifest.get(key) != value:
                    runtime_errors.append(f"package.{key}_mismatch")
        if any(report.get(key) != plan.get(key) for key in ("capabilities_sha256", "realizations_sha256", "adapter_registry_sha256")):
            runtime_errors.append("package.report_runtime_identity_mismatch")
        runtime_errors.extend(validate_mcp_projection(plan, candidate))
        if runtime_errors:
            return PackageOutcome("BLOCKED", tuple(sorted(set(runtime_errors))))
    name = plugin.get("name")
    if not isinstance(name, str) or not name or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in name):
        return PackageOutcome("FAIL", ("package.plugin_name_invalid",))
    report_contracts = {item.get("tool_id"): item.get("contract_sha256") for item in report.get("tools", []) if isinstance(item, dict)}
    manifest_contracts = {item.get("tool_id"): item.get("contract_sha256") for item in manifest.get("tool_bindings", []) if isinstance(item, dict)}
    if report_contracts != manifest_contracts:
        return PackageOutcome("BLOCKED", ("package.tool_evidence_mismatch",))
    preflight_evidence = plan.get("preflight_evidence") if isinstance(plan, dict) else None
    if not isinstance(preflight_evidence, dict) or report.get("preflight_evidence") != preflight_evidence:
        return PackageOutcome("BLOCKED", ("package.preflight_evidence_mismatch",))
    if manifest.get("preflight_evidence_sha256") != sha256(canonical_bytes(preflight_evidence)).hexdigest():
        return PackageOutcome("BLOCKED", ("package.preflight_evidence_sha256_mismatch",))

    destination = root / "dist" / f"{name}.zip"
    metadata_destination = root / "dist" / "package-metadata.json"
    try:
        with tempfile.TemporaryDirectory(dir=root, prefix=".package-build-") as temporary_name:
            temporary = Path(temporary_name)
            staged_zip = temporary / f"{name}.zip"
            archive_sha = plugin_authoring.write_deterministic_zip(candidate, staged_zip, prefix=name)
            inventory = plugin_authoring.inventory_archive(staged_zip)
            extracted = temporary / "extracted"
            plugin_authoring.extract_archive(staged_zip, extracted)
            located = plugin_authoring.locate_plugin_archive_root(extracted)
            if located.profile != "PORTABLE_SINGLE_DIRECTORY":
                return PackageOutcome("FAIL", ("package.envelope_invalid",))
            candidate_members = {item.path: item.sha256 for item in plugin_authoring.tree_manifest(candidate)}
            extracted_members = {item.path: item.sha256 for item in plugin_authoring.tree_manifest(located.path)}
            archive_members = {
                item.path.removeprefix(f"{name}/"): item.sha256 for item in inventory.members
                if item.path.startswith(f"{name}/")
            }
            if candidate_members != extracted_members or candidate_members != archive_members:
                return PackageOutcome("FAIL", ("package.extracted_member_mismatch",))
            validation = plugin_authoring.validate_plugin_tree(located.path)
            if validation:
                return PackageOutcome("FAIL", tuple(f"package.extracted:{item.code}:{item.path}" for item in validation))
            for contract in manifest.get("tool_contracts", []):
                validated = plugin_authoring.validate_application_tool_contract(contract)
                if validated.errors or validated.blockers:
                    return PackageOutcome("FAIL", tuple(f"package.tool:{item}" for item in (*validated.errors, *validated.blockers)))
            forbidden_imports = []
            for path in located.path.rglob("*.py"):
                text = path.read_text(encoding="utf-8", errors="replace")
                if "obvious_one_plugin_framework" in text or "plugin_builder_core" in text:
                    forbidden_imports.append(path.relative_to(located.path).as_posix())
            if forbidden_imports:
                return PackageOutcome("FAIL", tuple(f"package.development_import:{item}" for item in forbidden_imports))
            members_payload = [asdict(item) for item in inventory.members]
            member_manifest_sha = sha256(canonical_bytes(members_payload)).hexdigest()
            metadata = {
                "schema": "plugin-builder-package-v3" if isinstance(plan.get("capabilities"), list) else "plugin-builder-package-v2",
                "plugin_id": name,
                "archive_sha256": archive_sha,
                "candidate_sha256": candidate_id["sha256"],
                "verification_sha256": verification_id["sha256"],
                "member_manifest_sha256": member_manifest_sha,
                "members": members_payload,
                "candidate_members": [asdict(item) for item in plugin_authoring.tree_manifest(candidate)],
                "envelope_profile": located.profile,
                "preflight_evidence": preflight_evidence,
                "manifest_profile": preflight_evidence["manifest_profile"],
                "command_evidence": report.get("tools", []),
                "fallback_activations": report.get("fallback_activations", []),
                "evidence_states": report.get("evidence_states", {}),
                "tool_bindings": manifest.get("tool_bindings", []),
                "tool_contracts_sha256": sha256(canonical_bytes(manifest.get("tool_contracts", []))).hexdigest(),
                **({
                    "capabilities_sha256": plan["capabilities_sha256"],
                    "realizations_sha256": plan["realizations_sha256"],
                    "adapter_registry_sha256": plan["adapter_registry_sha256"],
                    "generated_runtime_configuration_sha256": manifest["generated_runtime_configuration_sha256"],
                    "runtime_realizations": report.get("runtime_realizations", []),
                    "runtime_realization_state": "NOT VERIFIED",
                } if isinstance(plan.get("capabilities"), list) else {}),
                "extracted_validation": {"state": "PASS", "diagnostics": []},
                "safety_validation": {"state": "PASS", "diagnostics": []},
            }
            staged_metadata = temporary / "package-metadata.json"
            metadata_bytes = canonical_bytes(metadata)
            metadata_sha = sha256(metadata_bytes).hexdigest()
            staged_metadata.write_bytes(metadata_bytes)
            _publish_pair(staged_zip, staged_metadata, destination, metadata_destination, temporary)
    except plugin_authoring.PluginAuthoringError as error:
        return PackageOutcome("FAIL", (f"package.{error.code}",))
    except OSError:
        return PackageOutcome("FAIL", ("package.local_io_failure",))

    session["package"] = {
        "path": f"dist/{name}.zip", "sha256": archive_sha,
        "candidate_sha256": candidate_id["sha256"],
        "verification_sha256": verification_id["sha256"],
        "member_manifest_sha256": member_manifest_sha,
        "metadata_path": "dist/package-metadata.json",
        "metadata_sha256": metadata_sha,
    }
    session["stage"] = "E1"
    write_bytes_transactionally(session_file, canonical_bytes(session))
    return PackageOutcome("PASS", (), archive_sha, f"dist/{name}.zip", metadata_sha)
