"""Transactional deterministic normalization of supported handoff envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any

from ..plugin_authoring import (
    PluginAuthoringError,
    extract_archive,
    inventory_archive,
    tree_sha256,
    write_deterministic_zip,
)
from .contract import (
    HANDOFF_CONTRACT,
    HANDOFF_SCHEMA,
    RUNTIME_SCOPE,
    canonical_json_bytes,
    validate_canonical_handoff,
)
from .profiles import HandoffProfile, classify_handoff_profile


ADAPTER_VERSION = "workbench-handoff-0.1.3"


@dataclass(frozen=True)
class HandoffNormalizationOutcome:
    status: str
    profile: str
    diagnostics: tuple[str, ...]
    report: dict[str, Any]
    source_archive_sha256: str | None = None
    output_archive_sha256: str | None = None
    output_tree_sha256: str | None = None


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("handoff.json_invalid") from exc
    if not isinstance(value, dict):
        raise ValueError("handoff.json_invalid")
    return value


def _safe_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts) or ":" in path.parts[0]:
        return None
    return path.as_posix()


def _safe_declared_path(value: object) -> tuple[str, bool] | None:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        return None
    prefix = value.endswith("/")
    path = _safe_path(value[:-1] if prefix else value)
    return None if path is None else (path, prefix)


def _report(
    status: str,
    profile: str,
    diagnostics: tuple[str, ...],
    source_hash: str | None,
    runtime_scope: str,
    tree_hash: str | None = None,
    archive_hash: str | None = None,
) -> dict[str, Any]:
    return {
        "schema": "workbench-handoff-normalization-v1",
        "status": status,
        "profile": profile,
        "adapter_version": ADAPTER_VERSION,
        "runtime_scope": runtime_scope,
        "source_archive_sha256": source_hash,
        "output_tree_sha256": tree_hash,
        "output_archive_sha256": archive_hash,
        "diagnostics": list(diagnostics),
    }


def _outcome(
    status: str,
    profile: str,
    diagnostics: list[str] | tuple[str, ...],
    source_hash: str | None,
    runtime_scope: str,
    tree_hash: str | None = None,
    archive_hash: str | None = None,
) -> HandoffNormalizationOutcome:
    stable = tuple(sorted(set(diagnostics)))
    return HandoffNormalizationOutcome(
        status,
        profile,
        stable,
        _report(status, profile, stable, source_hash, runtime_scope, tree_hash, archive_hash),
        source_hash,
        archive_hash,
        tree_hash,
    )


def _member_map(root: Path) -> dict[str, tuple[int, str]]:
    result: dict[str, tuple[int, str]] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        content = path.read_bytes()
        result[relative] = (len(content), sha256(content).hexdigest())
    return result


def _artifact_role(row: dict[str, Any]) -> str:
    explicit = row.get("role")
    if isinstance(explicit, str) and explicit:
        return explicit
    prefix = str(row.get("id", "")).partition("-")[0]
    return {
        "SPEC": "approved_specification",
        "DS": "approved_design_statement",
        "BW": "workflow_definitions_and_instruction_modules",
        "RM": "reference_material_inventory_evaluation_and_usage_map",
        "INV": "application_invariants_and_hitl_checkpoints",
        "TEST": "acceptance_criteria_and_representative_scenarios",
        "DEC": "rights_and_redistribution_decisions",
    }.get(prefix, "")


def _design_assistant_to_v11(
    root: Path,
    profile: str,
    source_hash: str,
    runtime_scope: str,
) -> list[str]:
    filename = "handoff_manifest.json" if profile == "COOL_DESIGN_ASSISTANT_FULL_V1" else "delta_handoff_manifest.json"
    legacy = _load_object(root / filename)
    operation = "create" if profile == "COOL_DESIGN_ASSISTANT_FULL_V1" else "update"
    diagnostics: list[str] = []
    records = legacy.get("requirements")
    if not isinstance(records, list) or not records:
        diagnostics.append("requirements.explicit_records_required")
        records = []
    artifacts = legacy.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        diagnostics.append("package.manifest_invalid")
        artifacts = []
    members = _member_map(root)
    normalized_artifacts: list[dict[str, Any]] = []
    authority: list[dict[str, Any]] = []
    represented: set[str] = set()
    for index, raw in enumerate(artifacts):
        if not isinstance(raw, dict):
            diagnostics.append(f"package.artifact_invalid:{index}")
            continue
        path = _safe_path(raw.get("file"))
        requirement_ids = raw.get("requirements")
        if path is None or path not in members:
            diagnostics.append(f"package.declared_member_missing:{path or ''}")
            continue
        if not isinstance(requirement_ids, list) or any(not isinstance(item, str) or not item for item in requirement_ids):
            diagnostics.append(f"requirements.artifact_index_invalid:{path}")
            requirement_ids = []
        role = _artifact_role(raw)
        if not role:
            diagnostics.append(f"package.artifact_role_invalid:{path}")
        size, digest = members[path]
        row = {
            "file": path,
            "id": raw.get("id", ""),
            "provenance": raw.get("provenance", ""),
            "requirements": requirement_ids,
            "role": role,
            "sha256": digest,
            "size": size,
            "state": raw.get("state", ""),
            "version": raw.get("version", ""),
        }
        normalized_artifacts.append(row)
        represented.add(path)
        if role == "approved_specification":
            authority.append(row)
    allowed_legacy_members = represented | {filename, "README.md"}
    for path in sorted(set(members) - allowed_legacy_members):
        diagnostics.append(f"package.undeclared_member:{path}")
    if len(authority) != 1:
        diagnostics.append("normalization.authoritative_specification_required")

    decisions = legacy.get("unresolved_owner_decisions")
    if not isinstance(decisions, list):
        diagnostics.append("owner_decisions.invalid")
        decisions = []
    approved = (
        isinstance(legacy.get("approval_evidence"), str)
        and bool(legacy["approval_evidence"].strip())
        and isinstance(legacy.get("gate"), str)
        and legacy["gate"].startswith("APPROVED")
        and len(authority) == 1
        and authority[0].get("state") == "approved"
    )
    handoff: dict[str, Any] = {
        "schema": HANDOFF_SCHEMA,
        "operation": operation,
        "approval": {
            "state": "approved" if approved else "pending",
            "confirmed_by": "decision owner recorded by Design Assistant handoff",
            "evidence": legacy.get("approval_evidence", ""),
            "specification_version": legacy.get("spec_version", ""),
        },
        "approved_specification": {
            "state": authority[0].get("state", "") if len(authority) == 1 else "",
            "file": authority[0].get("file", "") if len(authority) == 1 else "",
            "id": authority[0].get("id", "") if len(authority) == 1 else "",
            "version": authority[0].get("version", "") if len(authority) == 1 else "",
        },
        "requirements": records,
        "unresolved_owner_decisions": decisions,
        "source_archive_sha256": source_hash,
        "source_profile": profile,
    }
    by_role = {item["role"]: item for item in normalized_artifacts}
    design_statement = by_role.get("approved_design_statement")
    if design_statement is not None:
        handoff["approved_design_statement"] = {
            "id": design_statement["id"],
            "version": design_statement["version"],
            "state": "approved",
            "file": design_statement["file"],
        }
    role_shapes: dict[str, tuple[str, object]] = {
        "workflow_definitions_and_instruction_modules": (
            "workflow_definitions_and_instruction_modules", []
        ),
        "application_invariants_and_hitl_checkpoints": (
            "application_invariants_and_hitl_checkpoints", []
        ),
        "acceptance_criteria_and_representative_scenarios": (
            "acceptance_criteria_and_representative_scenarios", []
        ),
    }
    for field, (role, default) in role_shapes.items():
        row = by_role.get(role)
        if row is not None:
            handoff[field] = [f"{row['id']}|{row['file']}|{row['version']}"]
        elif field not in handoff:
            handoff[field] = default
    specification = authority[0] if len(authority) == 1 else None
    invariants = by_role.get("application_invariants_and_hitl_checkpoints")
    reference_map = by_role.get("reference_material_inventory_evaluation_and_usage_map")
    decisions_row = by_role.get("rights_and_redistribution_decisions")
    handoff.setdefault(
        "deterministic_operation_candidates",
        [f"{specification['id']}#deterministic-operations"] if specification else [],
    )
    handoff.setdefault(
        "tool_data_runtime_and_service_requirements",
        {
            "runtime_scope": runtime_scope,
            "target_runtimes": ["ChatGPT Work Local/Desktop", "Codex"],
            "excluded_runtimes": ["OpenClaw", "Claude"],
            "source_artifacts": [
                row["id"] for row in (specification, invariants) if row is not None
            ],
        },
    )
    handoff.setdefault(
        "reference_material_inventory_evaluation_and_usage_map",
        ([{
            "artifact": f"{reference_map['id']}|{reference_map['file']}|{reference_map['version']}",
            "provenance": reference_map["provenance"],
        }] if reference_map is not None else []),
    )
    handoff.setdefault(
        "rights_and_redistribution_decisions",
        {
            "source_artifacts": [
                row["id"] for row in (reference_map, decisions_row) if row is not None
            ],
            "normalization_authority": "format-only derivative; no additional rights granted",
        },
    )
    handoff.setdefault("explicit_exclusions", legacy.get("exclusions", []))
    for key in (
        "approved_design_statement",
        "workflow_definitions_and_instruction_modules",
        "reference_material_inventory_evaluation_and_usage_map",
        "application_invariants_and_hitl_checkpoints",
        "deterministic_operation_candidates",
        "tool_data_runtime_and_service_requirements",
        "acceptance_criteria_and_representative_scenarios",
        "rights_and_redistribution_decisions",
        "explicit_exclusions",
    ):
        if key in legacy:
            handoff[key] = legacy[key]
    if operation == "update":
        if "baseline" in legacy:
            handoff["baseline"] = legacy["baseline"]
        if "baseline_preservation" in legacy:
            handoff["baseline_preservation"] = legacy["baseline_preservation"]

    handoff_bytes = canonical_json_bytes(handoff)
    (root / "workbench-handoff.json").write_bytes(handoff_bytes)
    represented.add(filename)
    supporting: list[dict[str, Any]] = []
    for path, (size, digest) in sorted(members.items()):
        if path != filename and path not in {item["file"] for item in normalized_artifacts}:
            supporting.append({"file": path, "sha256": digest, "size": size})
    manifest = {
        "application": legacy.get("application", ""),
        "artifacts": normalized_artifacts,
        "canonical_handoff": {
            "file": "workbench-handoff.json",
            "sha256": sha256(handoff_bytes).hexdigest(),
            "size": len(handoff_bytes),
        },
        "gate": legacy.get("gate", ""),
        "handoff_contract": HANDOFF_CONTRACT,
        "normalization": {"adapter_version": ADAPTER_VERSION, "profile": profile},
        "operation": operation,
        "package_kind": "normalized-workbench-handoff",
        "package_schema_version": 1,
        "runtime_scope": runtime_scope,
        "source_archive_sha256": source_hash,
        "spec_version": legacy.get("spec_version", ""),
        "supporting_files": supporting,
    }
    (root / "package-manifest.json").write_bytes(canonical_json_bytes(manifest))
    (root / filename).unlink()
    return diagnostics


def _legacy_role(value: object) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value).casefold()).strip("_")
    if normalized in {"authoritative_specification", "approved_specification"}:
        return "approved_specification"
    if any(token in normalized for token in ("reference", "knowledge", "resource")):
        return "required_reference_material"
    return normalized


def _legacy_workbench_to_canonical(root: Path, source_hash: str, runtime_scope: str) -> list[str]:
    legacy = _load_object(root / "workbench_handoff_manifest.json")
    members = _member_map(root)
    diagnostics: list[str] = []
    artifacts: list[dict[str, Any]] = []
    authorities: list[dict[str, Any]] = []
    included = legacy.get("included_artifacts", [])
    if not isinstance(included, list):
        return ["legacy.included_artifacts_invalid"]
    seen: set[str] = set()
    for index, raw in enumerate(included):
        if not isinstance(raw, dict):
            diagnostics.append(f"legacy.artifact_invalid:{index}")
            continue
        identifier = raw.get("artifact_id")
        if not isinstance(identifier, str) or not identifier.strip():
            diagnostics.append("legacy.artifact_id_invalid")
        for field in ("provenance", "state", "version"):
            value = raw.get(field)
            if not isinstance(value, str) or not value.strip():
                diagnostics.append(f"legacy.artifact_{field}_invalid:{identifier or ''}")
        declared = _safe_declared_path(raw.get("path"))
        if declared is None:
            diagnostics.append(f"legacy.artifact_path_invalid:{identifier or ''}")
            continue
        path, prefix = declared
        matches = (
            [(member_path, value) for member_path, value in sorted(members.items()) if member_path.startswith(f"{path}/")]
            if prefix else ([(path, members[path])] if path in members else [])
        )
        if not matches:
            diagnostics.append(f"legacy.artifact_missing:{path}")
            continue
        for member_path, (size, digest) in matches:
            if member_path.casefold() in seen:
                diagnostics.append(f"legacy.artifact_collision:{member_path}")
                continue
            seen.add(member_path.casefold())
            relative = member_path[len(path) + 1:] if prefix else ""
            row = {
                "file": member_path,
                "id": identifier if not relative else f"{identifier}/{relative}",
                "provenance": raw.get("provenance", ""),
                "role": _legacy_role(raw.get("relation")),
                "sha256": digest,
                "size": size,
                "state": raw.get("state", ""),
                "version": raw.get("version", ""),
            }
            if "requirements" in raw:
                row["requirements"] = raw["requirements"]
            artifacts.append(row)
            if row["role"] == "approved_specification":
                authorities.append(row)
    if len(authorities) != 1:
        diagnostics.append("normalization.authoritative_specification_required")
    elif authorities[0].get("state") != "approved":
        diagnostics.append("legacy.artifact_authority_state_invalid")
    elif authorities[0].get("version") != legacy.get("specification_version"):
        diagnostics.append("legacy.artifact_authority_version_mismatch")
    decisions = legacy.get("unresolved_owner_decisions", [])
    if not isinstance(decisions, list):
        diagnostics.append("legacy.owner_decisions_invalid")
        decisions = []
    else:
        normalized_decisions = []
        for item in decisions:
            valid = (
                isinstance(item, dict)
                and set(item) == {"blocking", "decision_id", "impact", "owner", "summary"}
                and type(item.get("blocking")) is bool
                and all(isinstance(item.get(key), str) and item[key].strip() for key in ("decision_id", "impact", "owner", "summary"))
            )
            if not valid:
                diagnostics.append("legacy.owner_decision_invalid")
            else:
                normalized_decisions.append(item)
        decisions = normalized_decisions
    approved = (
        legacy.get("specification_state") == "approved"
        and isinstance(legacy.get("approval_evidence"), str)
        and bool(legacy["approval_evidence"].strip())
        and isinstance(legacy.get("gate_result"), str)
        and legacy["gate_result"].startswith("APPROVED")
        and len(authorities) == 1
        and authorities[0]["state"] == "approved"
        and not any(item["blocking"] for item in decisions)
        and not diagnostics
    )
    if not approved:
        diagnostics.append("approval.not_approved")
    authority = authorities[0] if len(authorities) == 1 else {"file": "", "id": "", "version": ""}
    handoff = {
        "approval": {
            "confirmed_by": "decision owner recorded by legacy handoff",
            "evidence": legacy.get("approval_evidence", ""),
            "specification_version": legacy.get("specification_version", ""),
            "state": "approved" if approved else "pending",
        },
        "approved_specification": {
            "file": authority["file"], "id": authority["id"],
            "state": legacy.get("specification_state", ""), "version": authority["version"],
        },
        "source_archive_sha256": source_hash,
        "source_profile": "LEGACY_WORKBENCH_V1",
        "unresolved_owner_decisions": decisions,
    }
    handoff_bytes = canonical_json_bytes(handoff)
    (root / "workbench-handoff.json").write_bytes(handoff_bytes)
    represented = {item["file"] for item in artifacts}
    supporting = [
        {"file": path, "size": size, "sha256": digest}
        for path, (size, digest) in sorted(members.items())
        if path not in represented and path != "workbench_handoff_manifest.json"
    ]
    manifest = {
        "application": legacy.get("application_name", ""),
        "artifacts": artifacts,
        "canonical_handoff": {"file": "workbench-handoff.json", "sha256": sha256(handoff_bytes).hexdigest(), "size": len(handoff_bytes)},
        "gate": legacy.get("gate_result", ""),
        "normalization": {"adapter_version": ADAPTER_VERSION, "profile": "LEGACY_WORKBENCH_V1"},
        "package_kind": "normalized-workbench-handoff",
        "package_schema_version": 1,
        "runtime_scope": runtime_scope,
        "source_archive_sha256": source_hash,
        "spec_version": legacy.get("specification_version", ""),
        "supporting_files": supporting,
    }
    (root / "package-manifest.json").write_bytes(canonical_json_bytes(manifest))
    (root / "workbench_handoff_manifest.json").unlink()
    return diagnostics


def _publish(stage: Path, destination: Path, staged_zip: Path | None, zip_destination: Path | None, temporary: Path) -> None:
    backup = temporary / "previous-tree"
    backup_zip = temporary / "previous.zip"
    tree_moved = zip_moved = tree_published = False
    try:
        if destination.exists():
            os.replace(destination, backup)
            tree_moved = True
        if zip_destination is not None and zip_destination.exists():
            os.replace(zip_destination, backup_zip)
            zip_moved = True
        os.replace(stage, destination)
        tree_published = True
        if staged_zip is not None and zip_destination is not None:
            os.replace(staged_zip, zip_destination)
    except OSError:
        if tree_published and destination.exists():
            os.replace(destination, temporary / "failed-tree")
        if tree_moved and backup.exists() and not destination.exists():
            os.replace(backup, destination)
        if zip_moved and zip_destination is not None and backup_zip.exists() and not zip_destination.exists():
            os.replace(backup_zip, zip_destination)
        raise


def normalize_handoff_archive(
    source: Path,
    destination_root: Path,
    normalized_zip: Path | None = None,
    *,
    runtime_scope: str = RUNTIME_SCOPE,
) -> HandoffNormalizationOutcome:
    """Normalize one archive and publish outputs only after all checks pass."""
    source_path = Path(source)
    destination = Path(destination_root).absolute()
    zip_destination = Path(normalized_zip).absolute() if normalized_zip is not None else None
    if runtime_scope != RUNTIME_SCOPE:
        return _outcome("BLOCKED", "UNKNOWN", ["handoff.runtime_scope_mismatch"], None, runtime_scope)
    try:
        inventory = inventory_archive(source_path)
    except PluginAuthoringError as exc:
        return _outcome("FAIL", "UNKNOWN", [exc.code], None, runtime_scope)
    source_hash = inventory.archive_sha256
    destination.parent.mkdir(parents=True, exist_ok=True)
    if zip_destination is not None:
        zip_destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=f".{destination.name}.normalize-") as temporary_name:
        temporary = Path(temporary_name)
        stage = temporary / "stage"
        extract_archive(source_path, stage)
        classified = classify_handoff_profile(stage)
        if classified.profile in {"UNKNOWN", "AMBIGUOUS"}:
            return _outcome("BLOCKED", classified.profile, classified.diagnostics, source_hash, runtime_scope)

        diagnostics: list[str] = []
        if classified.profile in {"COOL_DESIGN_ASSISTANT_FULL_V1", "COOL_DESIGN_ASSISTANT_DELTA_V1"}:
            diagnostics.extend(_design_assistant_to_v11(stage, classified.profile, source_hash, runtime_scope))
        elif classified.profile == "LEGACY_WORKBENCH_V1":
            collisions = sorted(
                name for name in ("package-manifest.json", "workbench-handoff.json")
                if (stage / name).exists()
            )
            if collisions:
                return _outcome(
                    "BLOCKED", classified.profile,
                    [f"normalization.canonical_collision:{name}" for name in collisions],
                    source_hash, runtime_scope,
                )
            diagnostics.extend(_legacy_workbench_to_canonical(stage, source_hash, runtime_scope))

        if classified.profile in {
            "WORKBENCH_HANDOFF_V1_1",
            "COOL_DESIGN_ASSISTANT_FULL_V1",
            "COOL_DESIGN_ASSISTANT_DELTA_V1",
        }:
            manifest = _load_object(stage / "package-manifest.json")
            handoff = _load_object(stage / "workbench-handoff.json")
            validation_zip = temporary / "validation.zip"
            write_deterministic_zip(stage, validation_zip)
            validation_inventory = inventory_archive(validation_zip)
            validation = validate_canonical_handoff(manifest, handoff, validation_inventory, stage)
            diagnostics.extend(validation.diagnostics)

        stable = sorted(set(diagnostics))
        if stable:
            return _outcome("BLOCKED", classified.profile, stable, source_hash, runtime_scope)
        output_tree_hash = tree_sha256(stage)
        staged_zip = temporary / "normalized.zip" if zip_destination is not None else None
        output_archive_hash = write_deterministic_zip(stage, staged_zip) if staged_zip is not None else None
        _publish(stage, destination, staged_zip, zip_destination, temporary)
        return _outcome(
            "PASS", classified.profile, (), source_hash, runtime_scope,
            output_tree_hash, output_archive_hash,
        )


__all__ = ["ADAPTER_VERSION", "HandoffNormalizationOutcome", "normalize_handoff_archive"]
