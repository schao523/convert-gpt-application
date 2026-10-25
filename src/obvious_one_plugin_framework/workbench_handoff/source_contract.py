"""Read-only checks for the Design Assistant source envelopes accepted by normalization."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from typing import Any

from .contract import SEMANTIC_FIELD_TYPES


SOURCE_PROFILES = frozenset({"COOL_DESIGN_ASSISTANT_FULL_V1", "COOL_DESIGN_ASSISTANT_DELTA_V1"})
ROLE_BY_ID_PREFIX = {
    "SPEC": "approved_specification",
    "DS": "approved_design_statement",
    "BW": "workflow_definitions_and_instruction_modules",
    "RM": "reference_material_inventory_evaluation_and_usage_map",
    "INV": "application_invariants_and_hitl_checkpoints",
    "TEST": "acceptance_criteria_and_representative_scenarios",
    "DEC": "rights_and_redistribution_decisions",
}
ARTIFACT_ROLES = frozenset(ROLE_BY_ID_PREFIX.values())
APPROVED_GATES = frozenset({"APPROVED", "READY FOR WORKBENCH", "APPROVED WITH NONBLOCKING DECISIONS"})
REQUIRED_FIELDS = frozenset({
    "application", "spec_version", "gate", "approval_evidence", "artifacts",
    "unresolved_owner_decisions", "exclusions", "reserved_workbench_decisions", "readiness_note",
})


@dataclass(frozen=True)
class SourceContractAnalysis:
    profile: str
    diagnostics: tuple[str, ...]
    manifest: dict[str, Any] | None


def _safe_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        return None
    path = PurePosixPath(value)
    if path.as_posix() != value or any(part in {".", "..", ""} for part in value.split("/")) or ":" in path.parts[0]:
        return None
    return value


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def artifact_role(row: dict[str, Any]) -> str:
    """Resolve the existing explicit-role or legacy ID-prefix convention."""
    explicit = row.get("role")
    if isinstance(explicit, str) and explicit:
        return explicit
    return ROLE_BY_ID_PREFIX.get(str(row.get("id", "")).partition("-")[0], "")


def analyze_source_handoff(root: Path, profile: str, *, runtime_scope: str) -> SourceContractAnalysis:
    """Check one extracted full/delta source package without changing its files."""
    if profile not in SOURCE_PROFILES:
        return SourceContractAnalysis(profile, ("source.profile_not_v11_eligible",), None)
    name = "handoff_manifest.json" if profile == "COOL_DESIGN_ASSISTANT_FULL_V1" else "delta_handoff_manifest.json"
    try:
        manifest = json.loads((root / name).read_bytes().decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return SourceContractAnalysis(profile, ("package.manifest_invalid",), None)
    if not isinstance(manifest, dict):
        return SourceContractAnalysis(profile, ("package.manifest_invalid",), None)

    errors: list[str] = []
    if not REQUIRED_FIELDS.issubset(manifest):
        errors.append("package.manifest_invalid")
    for field in ("application", "spec_version", "readiness_note"):
        if not _nonempty(manifest.get(field)):
            errors.append(f"package.{field}_invalid")
    if not _nonempty(manifest.get("approval_evidence")) or manifest.get("gate") not in APPROVED_GATES:
        errors.append("approval.not_approved")
    if "approval" in manifest:
        approval = manifest["approval"]
        if not isinstance(approval, dict) or approval.get("state") != "approved" or (
            "evidence" in approval and approval["evidence"] != manifest.get("approval_evidence")
        ) or ("specification_version" in approval and approval["specification_version"] != manifest.get("spec_version")):
            errors.append("approval.conflicting_authority")
    if "reference_material_inventory_evaluation_and_usage_map" in manifest and not isinstance(
        manifest["reference_material_inventory_evaluation_and_usage_map"], list
    ):
        errors.append("reference.usage_map_invalid")
    if "rights_and_redistribution_decisions" in manifest and not isinstance(
        manifest["rights_and_redistribution_decisions"], dict
    ):
        errors.append("rights.decision_invalid")
    for field, expected_type in SEMANTIC_FIELD_TYPES.items():
        if field in manifest and not isinstance(manifest[field], expected_type):
            errors.append(f"handoff.semantic_field_invalid:{field}")
    if not isinstance(manifest.get("exclusions"), list) or not isinstance(manifest.get("reserved_workbench_decisions"), list):
        errors.append("package.manifest_invalid")
    if runtime_scope != "OPENAI_ONLY_PHASE_ONE":
        errors.append("handoff.runtime_scope_mismatch")

    records = manifest.get("requirements")
    if not isinstance(records, list) or not records:
        errors.append("requirements.explicit_records_required")
        records = []
    by_id: dict[str, dict[str, Any]] = {}
    artifact_members: set[str] = set()
    bindings: dict[str, set[str]] = {}
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("package.manifest_invalid")
        artifacts = []
    authority_count = 0
    for index, row in enumerate(artifacts):
        if not isinstance(row, dict):
            errors.append(f"package.artifact_invalid:{index}")
            continue
        path = _safe_path(row.get("file"))
        if path is None:
            errors.append(f"package.declared_path_invalid:{index}")
            continue
        if path in artifact_members:
            errors.append(f"package.declared_member_duplicate:{path}")
        artifact_members.add(path)
        source = root / path
        if not source.is_file():
            errors.append(f"package.declared_member_missing:{path}")
            continue
        content = source.read_bytes()
        if "sha256" in row and row["sha256"] != sha256(content).hexdigest():
            errors.append(f"package.declared_member_mismatch:{path}")
        if "size" in row and row["size"] != len(content):
            errors.append(f"package.declared_member_mismatch:{path}")
        for field in ("id", "version", "state", "provenance"):
            if not _nonempty(row.get(field)):
                errors.append(f"package.artifact_{field}_invalid:{path}")
        role = artifact_role(row)
        if role not in ARTIFACT_ROLES:
            errors.append(f"package.artifact_role_invalid:{path}")
        if role == "approved_specification":
            authority_count += 1
            if row.get("state") != "approved":
                errors.append("approval.specification_not_approved")
            if row.get("version") != manifest.get("spec_version"):
                errors.append("approval.specification_version_mismatch")
        ids = row.get("requirements")
        if not isinstance(ids, list) or any(not _nonempty(value) for value in ids):
            errors.append(f"requirements.artifact_index_invalid:{path}")
        else:
            for identifier in ids:
                bindings.setdefault(identifier, set()).add(path)
    if authority_count != 1:
        errors.append("normalization.authoritative_specification_required")

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"requirements.record_invalid:{index}")
            continue
        identifier = record.get("id")
        if not _nonempty(identifier) or identifier.strip() != identifier:
            errors.append(f"requirements.id_invalid:{index}")
            continue
        if identifier in by_id:
            errors.append(f"requirements.duplicate_id:{identifier}")
        by_id[identifier] = record
        source = record.get("source")
        member = _safe_path(source.partition("#")[0]) if isinstance(source, str) else None
        if member is None:
            errors.append(f"requirements.source_invalid:{identifier}")
        elif member not in artifact_members or not (root / member).is_file():
            errors.append(f"requirements.source_missing:{identifier}")
        elif member not in bindings.get(identifier, set()):
            errors.append(f"requirements.source_artifact_binding_missing:{identifier}")
        verbatim = record.get("verbatim")
        if not _nonempty(verbatim):
            errors.append(f"requirements.text_invalid:{identifier}")
        elif member and (root / member).is_file():
            try:
                if verbatim not in (root / member).read_bytes().decode("utf-8"):
                    errors.append(f"requirements.text_mismatch:{identifier}")
            except UnicodeError:
                errors.append(f"requirements.source_unreadable:{identifier}")
        if profile == "COOL_DESIGN_ASSISTANT_DELTA_V1" and record.get("change") not in {"add", "modify", "remove", "preserve"}:
            errors.append(f"requirements.change_required:{identifier}")
        elif profile == "COOL_DESIGN_ASSISTANT_FULL_V1" and "change" in record:
            errors.append(f"requirements.change_forbidden:{identifier}")
    for identifier in sorted(by_id):
        if identifier not in bindings:
            errors.append(f"requirements.artifact_binding_missing:{identifier}")
    for identifier in sorted(set(bindings) - set(by_id)):
        errors.append(f"requirements.artifact_binding_unknown:{identifier}")

    decisions = manifest.get("unresolved_owner_decisions")
    if not isinstance(decisions, list):
        errors.append("owner_decisions.invalid")
    else:
        for index, item in enumerate(decisions):
            if not isinstance(item, dict) or any(not _nonempty(item.get(key)) for key in ("decision_id", "owner", "summary", "impact")) or type(item.get("blocking")) is not bool:
                errors.append(f"owner_decisions.invalid:{index}")
            elif item["blocking"]:
                errors.append(f"owner_decisions.blocking:{item['decision_id']}")

    if profile == "COOL_DESIGN_ASSISTANT_DELTA_V1":
        baseline = manifest.get("baseline")
        preservation = manifest.get("baseline_preservation")
        if not isinstance(baseline, dict) or any(not _nonempty(baseline.get(key)) for key in ("plugin_id", "version", "archive_sha256")):
            errors.append("baseline.required_for_update")
        elif len(baseline["archive_sha256"]) != 64 or any(
            character not in "0123456789abcdef" for character in baseline["archive_sha256"]
        ):
            errors.append("baseline.archive_sha256_invalid")
        if not isinstance(preservation, dict) or any(preservation.get(key) is not True for key in ("preserve_unaffected_members", "removal_requires_requirement", "identity_must_match")):
            errors.append("baseline.preservation_required")

    represented = artifact_members | {name, "README.md"}
    for path in sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()):
        if path not in represented:
            errors.append(f"package.undeclared_member:{path}")
    return SourceContractAnalysis(profile, tuple(sorted(set(errors))), manifest)


__all__ = ["SOURCE_PROFILES", "SourceContractAnalysis", "analyze_source_handoff", "artifact_role"]
