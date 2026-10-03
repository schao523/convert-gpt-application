"""Deterministic approved-package inspection and session initialization."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

from .bootstrap import plugin_authoring, workbench_handoff
from .handoff_normalization import normalize_handoff_archive


ArchiveInventory = plugin_authoring.ArchiveInventory
PluginAuthoringError = plugin_authoring.PluginAuthoringError
extract_archive = plugin_authoring.extract_archive
inventory_archive = plugin_authoring.inventory_archive
tree_sha256 = plugin_authoring.tree_sha256

_REQUIREMENT = re.compile(r"\b(RQ|AC|T)(\d+)(?:[\u2013-](?:RQ|AC|T)?(\d+))?\b")


@dataclass(frozen=True)
class InspectionOutcome:
    status: str
    stage: str
    errors: tuple[str, ...]
    inspection_sha256: str | None = None
    session_sha256: str | None = None


def _canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def _write_bytes(path: Path, payload: bytes) -> None:
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
            temporary = output.name
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def _load_json(path: Path, code: str, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append(code)
        return None
    if not isinstance(value, dict):
        errors.append(code)
        return None
    return value


def _declared_members(manifest: dict[str, Any], errors: list[str]) -> list[dict[str, Any]]:
    artifacts = manifest.get("artifacts")
    supporting = manifest.get("supporting_files", [])
    handoff = manifest.get("canonical_handoff")
    if not isinstance(artifacts, list) or not isinstance(supporting, list) or not isinstance(handoff, dict):
        errors.append("package.manifest_invalid")
        return []
    values = [*artifacts, *supporting, handoff]
    if any(not isinstance(item, dict) for item in values):
        errors.append("package.manifest_invalid")
        return []
    return values


def _expand_requirements(value: object) -> set[str]:
    if not isinstance(value, str):
        return set()
    result: set[str] = set()
    for match in _REQUIREMENT.finditer(value):
        prefix, first_text, last_text = match.groups()
        first = int(first_text)
        last = int(last_text) if last_text is not None else first
        if last < first or last - first > 100:
            continue
        result.update(f"{prefix}{number}" for number in range(first, last + 1))
    return result


def _member_payload(inventory: ArchiveInventory) -> list[dict[str, object]]:
    return [asdict(member) for member in inventory.members]


def _replace_workspace(stage: Path, destination: Path, temporary: Path) -> None:
    backup = temporary / "previous"
    moved = False
    try:
        if destination.exists():
            os.replace(destination, backup)
            moved = True
        os.replace(stage, destination)
    except OSError:
        if moved and backup.exists() and not destination.exists():
            os.replace(backup, destination)
        raise


def inspect_design_package(
    design_package: Path,
    workspace: Path,
    operation: str,
    baseline: Path | None = None,
    normalized_package: Path | None = None,
) -> InspectionOutcome:
    if operation not in {"create", "update"}:
        return InspectionOutcome("FAIL", "F1", ("operation.unsupported",))
    if operation == "update" and baseline is None:
        return InspectionOutcome("BLOCKED", "F1", ("baseline.required_for_update",))

    try:
        source_inventory = inventory_archive(Path(design_package))
    except PluginAuthoringError as error:
        return InspectionOutcome("FAIL", "F1", (f"package.{error.code}",))
    baseline_inventory = None
    baseline_profile = None
    if baseline is not None:
        try:
            baseline_inventory = inventory_archive(Path(baseline))
        except PluginAuthoringError as error:
            return InspectionOutcome("FAIL", "F1", (f"baseline.{error.code}",))

    destination = Path(workspace).absolute()
    package_path = Path(design_package).absolute()
    try:
        package_path.relative_to(destination)
    except ValueError:
        pass
    else:
        return InspectionOutcome("FAIL", "F1", ("package.inside_workspace",))
    if destination.exists():
        if not destination.is_dir():
            return InspectionOutcome("FAIL", "F1", ("workspace.invalid",))
        try:
            if next(destination.iterdir(), None) is not None:
                return InspectionOutcome("BLOCKED", "F1", ("workspace.nonempty",))
        except OSError:
            return InspectionOutcome("FAIL", "F1", ("workspace.unreadable",))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=f".{destination.name}.inspect-") as name:
        temporary = Path(name)
        stage = temporary / "workspace"
        stage.mkdir()
        normalized_zip = stage / "normalized-input.zip"
        normalization = normalize_handoff_archive(
            Path(design_package), stage / "input", normalized_zip,
        )
        report_bytes = _canonical_bytes(normalization.report)
        _write_bytes(stage / "normalization-report.json", report_bytes)
        report_sha256 = sha256(report_bytes).hexdigest()
        if normalization.status != "PASS":
            pending = [{
                "blocking": True,
                "id": "handoff-profile-selection",
                "owner": "decision owner",
                "summary": "Resolve the reported handoff intake diagnostics.",
            }]
            inspection = {
                "schema": "plugin-builder-inspection-v1", "operation": operation,
                "package": None, "approval": None, "approved_specification": None,
                "authoritative_files": [], "resources": [], "requirements": [],
                "pending_decisions": pending,
                "baseline": None,
                "normalization": normalization.report,
                "diagnostics": list(normalization.diagnostics),
            }
            inspection_bytes = _canonical_bytes(inspection)
            inspection_digest = sha256(inspection_bytes).hexdigest()
            _write_bytes(stage / "inspection.json", inspection_bytes)
            session = {
                "schema_version": 2, "operation": operation, "stage": "F1", "workspace_path": ".",
                "approved_spec_sha256": "0" * 64,
                "inspection": {
                    "path": "inspection.json", "sha256": inspection_digest,
                    "package_sha256": source_inventory.archive_sha256,
                    "baseline_sha256": None if baseline_inventory is None else baseline_inventory.archive_sha256,
                    "normalization": {
                        "source_sha256": source_inventory.archive_sha256,
                        "profile": normalization.profile,
                        "normalized_tree_sha256": None,
                        "normalized_archive_sha256": None,
                        "report_path": "normalization-report.json",
                        "report_sha256": report_sha256,
                    },
                },
                "pending_decisions": pending, "requirements": [], "baseline": None,
                "plan": None, "w1": None, "candidate": None, "verification": None,
                "w2": None, "package": None,
            }
            session_bytes = _canonical_bytes(session)
            session_digest = sha256(session_bytes).hexdigest()
            _write_bytes(stage / "session.json", session_bytes)
            _replace_workspace(stage, destination, temporary)
            return InspectionOutcome("BLOCKED", "F1", normalization.diagnostics, inspection_digest, session_digest)
        if normalization.output_archive_sha256 is None or normalization.output_tree_sha256 is None:
            return InspectionOutcome("FAIL", "F1", ("normalization.output_missing",))
        package_inventory = inventory_archive(normalized_zip)
        if baseline is not None:
            raw_baseline = temporary / "raw-baseline"
            try:
                extract_archive(Path(baseline), raw_baseline)
                located = plugin_authoring.locate_plugin_archive_root(raw_baseline)
            except PluginAuthoringError as error:
                return InspectionOutcome("FAIL", "F1", (f"baseline.{error.code}",))
            baseline_profile = located.profile
            shutil.copytree(located.path, stage / "baseline", copy_function=shutil.copy2)

        errors: list[str] = []
        manifest = _load_json(stage / "input" / "package-manifest.json", "package.manifest_invalid", errors)
        handoff = _load_json(stage / "input" / "workbench-handoff.json", "package.handoff_invalid", errors)
        declared: list[dict[str, Any]] = []
        if manifest is not None:
            if manifest.get("package_schema_version") != 1 or manifest.get("package_kind") != "normalized-workbench-handoff":
                errors.append("package.manifest_unsupported")
            if not isinstance(manifest.get("gate"), str) or not manifest["gate"].startswith("APPROVED"):
                errors.append("package.gate_not_approved")
            declared = _declared_members(manifest, errors)

        by_path = {member.path: member for member in package_inventory.members}
        for item in declared:
            path = item.get("file")
            if not isinstance(path, str) or not path:
                errors.append("package.manifest_invalid")
                continue
            member = by_path.get(path)
            if member is None:
                errors.append(f"package.declared_member_missing:{path}")
                continue
            if item.get("sha256") != member.sha256 or item.get("size") != member.size:
                errors.append(f"package.declared_member_mismatch:{path}")

        approval = handoff.get("approval") if handoff is not None else None
        approved_specification = handoff.get("approved_specification") if handoff is not None else None
        if not isinstance(approval, dict) or approval.get("state") != "approved":
            errors.append("approval.not_approved")
        if not isinstance(approved_specification, dict) or approved_specification.get("state") != "approved":
            errors.append("approval.specification_not_approved")

        artifacts = manifest.get("artifacts", []) if manifest is not None else []
        authoritative: list[dict[str, object]] = []
        resources: list[dict[str, object]] = []
        requirements: dict[str, set[str]] = {}
        if isinstance(artifacts, list):
            for artifact in artifacts:
                if not isinstance(artifact, dict) or not isinstance(artifact.get("file"), str):
                    continue
                path = artifact["file"]
                member = by_path.get(path)
                if member is None:
                    continue
                record = {
                    "id": artifact.get("id", ""),
                    "path": path,
                    "role": artifact.get("role", ""),
                    "sha256": member.sha256,
                    "size": member.size,
                    "state": artifact.get("state", ""),
                    "version": artifact.get("version", ""),
                }
                authoritative.append(record)
                role = str(artifact.get("role", "")).casefold()
                if "reference" in role or "resource" in role:
                    resources.append({
                        "path": path,
                        "required": True,
                        "rights_state": artifact.get("state", ""),
                        "sha256": member.sha256,
                        "size": member.size,
                    })
                for requirement_id in _expand_requirements(artifact.get("requirements")):
                    requirements.setdefault(requirement_id, set()).add(f"input/{path}")

        requirement_records: list[dict[str, Any]] | None = None
        baseline_identity = None
        is_v11 = (
            normalization.profile in {
                "WORKBENCH_HANDOFF_V1_1",
                "COOL_DESIGN_ASSISTANT_FULL_V1",
                "COOL_DESIGN_ASSISTANT_DELTA_V1",
            }
            and isinstance(handoff, dict)
            and handoff.get("schema") == workbench_handoff.HANDOFF_SCHEMA
        )
        if is_v11:
            if handoff.get("operation") != operation:
                errors.append("handoff.operation_mismatch")
            raw_requirements = handoff.get("requirements")
            if not isinstance(raw_requirements, list):
                errors.append("requirements.explicit_records_required")
            else:
                requirement_records = []
                for item in raw_requirements:
                    if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                        continue
                    source = item.get("source")
                    source_path = source.partition("#")[0] if isinstance(source, str) else ""
                    record = {
                        "id": item["id"],
                        "required": True,
                        "source": source,
                        "source_paths": [f"input/{source_path}"],
                        "verbatim": item.get("verbatim"),
                    }
                    if "change" in item:
                        record["change"] = item["change"]
                    requirement_records.append(record)
            if operation == "update":
                try:
                    baseline_identity = (
                        workbench_handoff.baseline_identity_from_archive(Path(baseline))
                        if baseline is not None else None
                    )
                except PluginAuthoringError as error:
                    errors.append(f"baseline.{error.code}")
                errors.extend(
                    workbench_handoff.validate_update_baseline(handoff, baseline_identity)
                )

        approved_spec_path = approved_specification.get("file") if isinstance(approved_specification, dict) else None
        approved_spec_member = by_path.get(approved_spec_path) if isinstance(approved_spec_path, str) else None
        if approved_spec_member is None:
            errors.append("approval.specification_member_missing")

        pending = []
        if handoff is not None and isinstance(handoff.get("unresolved_owner_decisions"), list):
            for item in handoff["unresolved_owner_decisions"]:
                if isinstance(item, dict):
                    pending.append({
                        "blocking": item.get("blocking") is True,
                        "id": str(item.get("decision_id", "")),
                        "owner": str(item.get("owner", "")),
                        "summary": str(item.get("summary", "")),
                    })
        stage_name = "F1" if errors or any(item["blocking"] for item in pending) else "S2"
        status = "BLOCKED" if stage_name == "F1" else "PASS"
        inspection = {
            "schema": "plugin-builder-inspection-v1",
            "operation": operation,
            "package": {
                "sha256": package_inventory.archive_sha256,
                "members": _member_payload(package_inventory),
                "total_bytes": package_inventory.total_bytes,
            },
            "approval": approval if isinstance(approval, dict) else None,
            "approved_specification": approved_specification if isinstance(approved_specification, dict) else None,
            "authoritative_files": sorted(authoritative, key=lambda item: str(item["path"])),
            "resources": sorted(resources, key=lambda item: str(item["path"])),
            "requirements": requirement_records if requirement_records is not None else [
                {"id": key, "required": True, "source_paths": sorted(value)}
                for key, value in sorted(requirements.items())
            ],
            "pending_decisions": sorted(pending, key=lambda item: str(item["id"])),
            "normalization": normalization.report,
            "baseline": None if baseline_inventory is None else {
                "sha256": baseline_inventory.archive_sha256,
                "members": _member_payload(baseline_inventory),
                "total_bytes": baseline_inventory.total_bytes,
                "tree_sha256": tree_sha256(stage / "baseline"),
                "envelope_profile": baseline_profile,
                **({
                    "plugin_id": baseline_identity.plugin_id,
                    "version": baseline_identity.version,
                } if baseline_identity is not None else {}),
            },
            "diagnostics": sorted(set(errors)),
        }
        inspection_bytes = _canonical_bytes(inspection)
        inspection_digest = sha256(inspection_bytes).hexdigest()
        _write_bytes(stage / "inspection.json", inspection_bytes)
        baseline_value = None if baseline_inventory is None else {
            "path": "baseline",
            "sha256": baseline_inventory.archive_sha256,
            "manifest_sha256": inspection["baseline"]["tree_sha256"],
        }
        session = {
            "schema_version": 2,
            "operation": operation,
            "stage": stage_name,
            "workspace_path": ".",
            "approved_spec_sha256": approved_spec_member.sha256 if approved_spec_member is not None else "0" * 64,
            "inspection": {
                "path": "inspection.json",
                "sha256": inspection_digest,
                "package_sha256": package_inventory.archive_sha256,
                "baseline_sha256": None if baseline_inventory is None else baseline_inventory.archive_sha256,
                "normalization": {
                    "source_sha256": source_inventory.archive_sha256,
                    "profile": normalization.profile,
                    "normalized_tree_sha256": normalization.output_tree_sha256,
                    "normalized_archive_sha256": normalization.output_archive_sha256,
                    "report_path": "normalization-report.json",
                    "report_sha256": report_sha256,
                },
            },
            "pending_decisions": inspection["pending_decisions"],
            "requirements": inspection["requirements"],
            "baseline": baseline_value,
            "plan": None,
            "w1": None,
            "candidate": None,
            "verification": None,
            "w2": None,
            "package": None,
        }
        session_bytes = _canonical_bytes(session)
        session_digest = sha256(session_bytes).hexdigest()
        _write_bytes(stage / "session.json", session_bytes)
        if normalized_package is not None:
            requested = Path(normalized_package).absolute()
            if requested == package_path or requested == destination or destination in requested.parents:
                return InspectionOutcome("FAIL", "F1", ("normalized_package.destination_invalid",))
            requested.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=requested.parent, prefix=f".{requested.name}.", delete=False) as output:
                output.write(normalized_zip.read_bytes())
                temporary_output = Path(output.name)
            os.replace(temporary_output, requested)
        _replace_workspace(stage, destination, temporary)
    return InspectionOutcome(status, stage_name, tuple(sorted(set(errors))), inspection_digest, session_digest)
