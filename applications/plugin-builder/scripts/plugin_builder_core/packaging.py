"""Guarded deterministic packaging of W2-approved plugin candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile

from .bootstrap import plugin_authoring
from .implementation_plan import canonical_bytes, write_bytes_transactionally
from .session_contract import validate_session


@dataclass(frozen=True)
class PackageOutcome:
    status: str
    errors: tuple[str, ...]
    package_sha256: str | None = None
    path: str | None = None


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
    if errors:
        return PackageOutcome("BLOCKED", tuple(sorted(set(errors))))

    report = _load(report_path)
    manifest = _load(candidate / "PLUGIN-BUILDER-MANIFEST.json")
    plugin = _load(candidate / "plugin.json")
    if report is None or manifest is None or plugin is None:
        return PackageOutcome("FAIL", ("package.input_manifest_invalid",))
    if any(item.get("required") is True and item.get("state") != "PASS" for item in report.get("checks", [])):
        return PackageOutcome("BLOCKED", ("package.required_check_incomplete",))
    plan_identity = session.get("plan") or {}
    plan_path = root / str(plan_identity.get("path", ""))
    try:
        plan_hash = sha256(plan_path.read_bytes()).hexdigest()
    except OSError:
        plan_hash = ""
    if plan_hash != plan_identity.get("sha256") or plan_hash != (session.get("w1") or {}).get("plan_sha256") or plan_hash != candidate_id.get("plan_sha256") or plan_hash != manifest.get("plan_sha256"):
        return PackageOutcome("BLOCKED", ("package.plan_sha256_mismatch",))
    name = plugin.get("name")
    if not isinstance(name, str) or not name or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in name):
        return PackageOutcome("FAIL", ("package.plugin_name_invalid",))
    report_contracts = {item.get("tool_id"): item.get("contract_sha256") for item in report.get("tools", []) if isinstance(item, dict)}
    manifest_contracts = {item.get("tool_id"): item.get("contract_sha256") for item in manifest.get("tool_bindings", []) if isinstance(item, dict)}
    if report_contracts != manifest_contracts:
        return PackageOutcome("BLOCKED", ("package.tool_evidence_mismatch",))

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
                "schema": "plugin-builder-package-v1",
                "plugin_id": name,
                "archive_sha256": archive_sha,
                "candidate_sha256": candidate_id["sha256"],
                "verification_sha256": verification_id["sha256"],
                "member_manifest_sha256": member_manifest_sha,
                "members": members_payload,
                "candidate_members": [asdict(item) for item in plugin_authoring.tree_manifest(candidate)],
                "envelope_profile": located.profile,
                "tool_bindings": manifest.get("tool_bindings", []),
                "tool_contracts_sha256": sha256(canonical_bytes(manifest.get("tool_contracts", []))).hexdigest(),
                "extracted_validation": {"state": "PASS", "diagnostics": []},
                "safety_validation": {"state": "PASS", "diagnostics": []},
            }
            staged_metadata = temporary / "package-metadata.json"
            staged_metadata.write_bytes(canonical_bytes(metadata))
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
    }
    session["stage"] = "E1"
    write_bytes_transactionally(session_file, canonical_bytes(session))
    return PackageOutcome("PASS", (), archive_sha, f"dist/{name}.zip")
