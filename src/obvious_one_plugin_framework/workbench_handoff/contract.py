"""Semantic validation for the versioned Workbench handoff contract."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from typing import Any

from ..plugin_authoring import ArchiveInventory


HANDOFF_CONTRACT = "WORKBENCH_HANDOFF_V1_1"
HANDOFF_SCHEMA = "workbench-handoff-v1.1"
RUNTIME_SCOPE = "OPENAI_ONLY_PHASE_ONE"
_OPERATIONS = {"create", "update"}
_CHANGES = {"add", "modify", "remove", "preserve"}
_SEMANTIC_FIELD_TYPES = {
    "approved_design_statement": dict,
    "workflow_definitions_and_instruction_modules": list,
    "reference_material_inventory_evaluation_and_usage_map": list,
    "application_invariants_and_hitl_checkpoints": list,
    "deterministic_operation_candidates": list,
    "tool_data_runtime_and_service_requirements": dict,
    "acceptance_criteria_and_representative_scenarios": list,
    "rights_and_redistribution_decisions": dict,
    "explicit_exclusions": list,
}


@dataclass(frozen=True)
class HandoffValidation:
    status: str
    diagnostics: tuple[str, ...]


def canonical_json_bytes(value: object) -> bytes:
    """Serialize canonical handoff JSON without environment-dependent text handling."""
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def _safe_member_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        return None
    raw = value.partition("#")[0]
    path = PurePosixPath(raw)
    if (
        not raw
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or ":" in path.parts[0]
        or path.as_posix() != raw
    ):
        return None
    return raw


def _declared_members(manifest: dict[str, Any], diagnostics: list[str]) -> list[dict[str, Any]]:
    artifacts = manifest.get("artifacts")
    supporting = manifest.get("supporting_files", [])
    handoff = manifest.get("canonical_handoff")
    if not isinstance(artifacts, list) or not isinstance(supporting, list) or not isinstance(handoff, dict):
        diagnostics.append("package.manifest_invalid")
        return []
    records = [*artifacts, *supporting, handoff]
    if any(not isinstance(item, dict) for item in records):
        diagnostics.append("package.manifest_invalid")
        return []
    return records


def _validate_physical_manifest(
    manifest: dict[str, Any], inventory: ArchiveInventory, input_root: Path, diagnostics: list[str]
) -> tuple[list[dict[str, Any]], set[str]]:
    declared = _declared_members(manifest, diagnostics)
    by_path = {member.path: member for member in inventory.members}
    declared_paths: set[str] = set()
    for item in declared:
        path = _safe_member_path(item.get("file"))
        if path is None:
            diagnostics.append("package.declared_path_invalid")
            continue
        if path in declared_paths:
            diagnostics.append(f"package.declared_member_duplicate:{path}")
            continue
        declared_paths.add(path)
        member = by_path.get(path)
        if member is None or not (input_root / path).is_file():
            diagnostics.append(f"package.declared_member_missing:{path}")
            continue
        if item.get("sha256") != member.sha256 or item.get("size") != member.size:
            diagnostics.append(f"package.declared_member_mismatch:{path}")
    allowed = declared_paths | {"package-manifest.json"}
    for path in sorted(set(by_path) - allowed):
        diagnostics.append(f"package.undeclared_member:{path}")
    return [item for item in manifest.get("artifacts", []) if isinstance(item, dict)], declared_paths


def _validate_requirements(
    handoff: dict[str, Any], artifacts: list[dict[str, Any]], declared_paths: set[str],
    input_root: Path, operation: object, diagnostics: list[str],
) -> None:
    records = handoff.get("requirements")
    if not isinstance(records, list) or not records:
        diagnostics.append("requirements.explicit_records_required")
        return
    bindings: dict[str, set[str]] = {}
    artifact_paths: set[str] = set()
    for artifact in artifacts:
        path = _safe_member_path(artifact.get("file"))
        values = artifact.get("requirements")
        if path is None or not isinstance(values, list) or any(not isinstance(item, str) or not item for item in values):
            diagnostics.append(f"requirements.artifact_index_invalid:{path or ''}")
            continue
        artifact_paths.add(path)
        for identifier in values:
            bindings.setdefault(identifier, set()).add(path)

    seen: set[str] = set()
    changes: dict[str, set[str]] = {}
    valid_ids: set[str] = set()
    removals: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            diagnostics.append(f"requirements.record_invalid:{index}")
            continue
        identifier = record.get("id")
        if not isinstance(identifier, str) or not identifier or identifier.strip() != identifier:
            diagnostics.append(f"requirements.id_invalid:{index}")
            continue
        if identifier in seen:
            diagnostics.append(f"requirements.duplicate_id:{identifier}")
        seen.add(identifier)
        valid_ids.add(identifier)
        change = record.get("change")
        if operation == "update":
            if change not in _CHANGES:
                diagnostics.append(f"requirements.change_required:{identifier}")
            else:
                changes.setdefault(identifier, set()).add(change)
                if change == "remove":
                    removals.add(identifier)
        elif "change" in record:
            diagnostics.append(f"requirements.change_forbidden:{identifier}")

        source = record.get("source")
        member_path = _safe_member_path(source)
        if member_path is None:
            diagnostics.append(f"requirements.source_invalid:{identifier}")
            continue
        if member_path not in declared_paths or not (input_root / member_path).is_file():
            diagnostics.append(f"requirements.source_missing:{identifier}")
            continue
        if member_path not in artifact_paths:
            diagnostics.append(f"requirements.source_not_artifact:{identifier}")
        elif member_path not in bindings.get(identifier, set()):
            diagnostics.append(f"requirements.source_artifact_binding_missing:{identifier}")
        verbatim = record.get("verbatim")
        if not isinstance(verbatim, str) or not verbatim.strip():
            diagnostics.append(f"requirements.text_invalid:{identifier}")
            continue
        try:
            source_text = (input_root / member_path).read_bytes().decode("utf-8")
        except (OSError, UnicodeError):
            diagnostics.append(f"requirements.source_unreadable:{identifier}")
            continue
        if verbatim not in source_text:
            diagnostics.append(f"requirements.text_mismatch:{identifier}")

    for identifier, values in changes.items():
        if len(values) > 1:
            diagnostics.append(f"requirements.change_conflict:{identifier}")
    for identifier in sorted(valid_ids):
        if identifier not in bindings:
            diagnostics.append(f"requirements.artifact_binding_missing:{identifier}")
    for identifier in sorted(removals):
        if identifier not in bindings:
            diagnostics.append(f"requirements.removal_unbound:{identifier}")
    for identifier in sorted(set(bindings) - valid_ids):
        diagnostics.append(f"requirements.artifact_binding_unknown:{identifier}")


def _validate_update_fields(handoff: dict[str, Any], operation: object, diagnostics: list[str]) -> None:
    if operation == "create":
        if "baseline" in handoff or "baseline_preservation" in handoff:
            diagnostics.append("baseline.forbidden_for_create")
        return
    if operation != "update":
        return
    baseline = handoff.get("baseline")
    if not isinstance(baseline, dict):
        diagnostics.append("baseline.required_for_update")
    else:
        if not isinstance(baseline.get("plugin_id"), str) or not baseline["plugin_id"]:
            diagnostics.append("baseline.identity_invalid")
        if not isinstance(baseline.get("version"), str) or not baseline["version"]:
            diagnostics.append("baseline.identity_invalid")
        digest = baseline.get("archive_sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            diagnostics.append("baseline.archive_sha256_invalid")
    preservation = handoff.get("baseline_preservation")
    expected = {
        "preserve_unaffected_members": True,
        "removal_requires_requirement": True,
        "identity_must_match": True,
    }
    if not isinstance(preservation, dict) or any(preservation.get(key) is not value for key, value in expected.items()):
        diagnostics.append("baseline.preservation_required")


def _validate_semantic_fields(handoff: dict[str, Any], diagnostics: list[str]) -> None:
    for field, expected_type in _SEMANTIC_FIELD_TYPES.items():
        if field not in handoff:
            diagnostics.append(f"handoff.semantic_field_missing:{field}")
        elif not isinstance(handoff[field], expected_type):
            diagnostics.append(f"handoff.semantic_field_invalid:{field}")
    runtime = handoff.get("tool_data_runtime_and_service_requirements")
    if isinstance(runtime, dict) and runtime.get("runtime_scope") != RUNTIME_SCOPE:
        diagnostics.append("handoff.runtime_scope_mismatch")


def validate_canonical_handoff(
    manifest: dict[str, Any],
    handoff: dict[str, Any],
    inventory: ArchiveInventory,
    input_root: Path,
    *,
    expected_operation: str | None = None,
) -> HandoffValidation:
    """Validate physical and semantic v1.1 authorities without mutating them."""
    diagnostics: list[str] = []
    operation = handoff.get("operation")
    if (
        manifest.get("package_schema_version") != 1
        or manifest.get("package_kind") != "normalized-workbench-handoff"
        or manifest.get("handoff_contract") != HANDOFF_CONTRACT
        or handoff.get("schema") != HANDOFF_SCHEMA
    ):
        diagnostics.append("handoff.contract_mismatch")
    if operation not in _OPERATIONS or manifest.get("operation") != operation or (
        expected_operation is not None and operation != expected_operation
    ):
        diagnostics.append("handoff.operation_mismatch")
    if manifest.get("runtime_scope") != RUNTIME_SCOPE:
        diagnostics.append("handoff.runtime_scope_mismatch")
    approval = handoff.get("approval")
    specification = handoff.get("approved_specification")
    if not isinstance(approval, dict) or approval.get("state") != "approved":
        diagnostics.append("approval.not_approved")
    if not isinstance(specification, dict) or specification.get("state") != "approved":
        diagnostics.append("approval.specification_not_approved")
    decisions = handoff.get("unresolved_owner_decisions")
    if not isinstance(decisions, list):
        diagnostics.append("owner_decisions.invalid")
    else:
        for index, item in enumerate(decisions):
            if not isinstance(item, dict) or not all(
                isinstance(item.get(key), str) and bool(item[key].strip())
                for key in ("decision_id", "owner", "summary", "impact")
            ) or type(item.get("blocking")) is not bool:
                diagnostics.append(f"owner_decisions.invalid:{index}")
            elif item.get("blocking") is True:
                diagnostics.append(f"owner_decisions.blocking:{item.get('decision_id', index)}")

    _validate_semantic_fields(handoff, diagnostics)

    artifacts, declared_paths = _validate_physical_manifest(manifest, inventory, Path(input_root), diagnostics)
    canonical = manifest.get("canonical_handoff")
    if isinstance(canonical, dict):
        actual = canonical_json_bytes(handoff)
        if canonical.get("sha256") != sha256(actual).hexdigest() or canonical.get("size") != len(actual):
            diagnostics.append("package.canonical_handoff_mismatch")
    _validate_requirements(handoff, artifacts, declared_paths, Path(input_root), operation, diagnostics)
    _validate_update_fields(handoff, operation, diagnostics)
    unique = tuple(sorted(set(diagnostics)))
    return HandoffValidation("PASS" if not unique else "FAIL", unique)
