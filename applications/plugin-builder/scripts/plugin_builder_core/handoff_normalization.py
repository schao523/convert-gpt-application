"""Deterministic compatibility normalization for approved Workbench handoffs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any

from .bootstrap import plugin_authoring
from .implementation_plan import canonical_bytes


ADAPTER_VERSION = "plugin-builder-0.1.1"
_CANONICAL_FILES = {"package-manifest.json", "workbench-handoff.json"}
_LEGACY_REQUIRED = {
    "application_name", "specification_state", "approval_evidence", "gate_result",
    "specification_version", "included_artifacts",
}


@dataclass(frozen=True)
class HandoffProfile:
    profile: str
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class HandoffNormalizationOutcome:
    status: str
    profile: str
    diagnostics: tuple[str, ...]
    report: dict[str, Any]
    source_archive_sha256: str | None = None
    output_archive_sha256: str | None = None
    output_tree_sha256: str | None = None


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _role(value: object) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value).casefold()).strip("_")
    if normalized in {"authoritative_specification", "approved_specification"}:
        return "approved_specification"
    if "reference" in normalized or "knowledge" in normalized or "resource" in normalized:
        return "required_reference_material"
    return normalized


def _authoritative(legacy: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = legacy.get("included_artifacts")
    if not isinstance(artifacts, list):
        return []
    return [item for item in artifacts if isinstance(item, dict) and _role(item.get("relation")) == "approved_specification"]


def classify_handoff_profile(inventory, extracted_root: Path) -> HandoffProfile:
    root = Path(extracted_root)
    canonical_manifest = _load_json(root / "package-manifest.json")
    canonical_handoff = _load_json(root / "workbench-handoff.json")
    legacy = _load_json(root / "workbench_handoff_manifest.json")
    canonical = (
        canonical_manifest is not None
        and canonical_handoff is not None
        and canonical_manifest.get("package_schema_version") == 1
        and canonical_manifest.get("package_kind") == "normalized-workbench-handoff"
    )
    recognized_legacy = legacy is not None and _LEGACY_REQUIRED.issubset(legacy)
    if canonical:
        return HandoffProfile("CANONICAL_V1")
    if recognized_legacy:
        authorities = _authoritative(legacy)
        if len(authorities) > 1:
            return HandoffProfile("AMBIGUOUS", ("profile.multiple_authoritative_specifications",))
        return HandoffProfile("LEGACY_WORKBENCH_V1")
    return HandoffProfile("UNKNOWN", ("profile.unrecognized",))


def _safe_declared_path(value: object) -> tuple[str, bool] | None:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        return None
    prefix = value.endswith("/")
    trimmed = value[:-1] if prefix else value
    path = PurePosixPath(trimmed)
    if not trimmed or any(part in {"", ".", ".."} for part in path.parts) or ":" in path.parts[0]:
        return None
    return path.as_posix(), prefix


def _artifact_records(legacy: dict[str, Any], inventory) -> tuple[list[dict[str, Any]], list[str]]:
    by_path = {item.path: item for item in inventory.members}
    records: list[dict[str, Any]] = []
    diagnostics: list[str] = []
    artifacts = legacy.get("included_artifacts")
    if not isinstance(artifacts, list):
        return [], ["legacy.included_artifacts_invalid"]
    seen: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            diagnostics.append("legacy.artifact_invalid")
            continue
        identifier = artifact.get("artifact_id")
        provenance = artifact.get("provenance")
        state = artifact.get("state")
        version = artifact.get("version")
        if not isinstance(identifier, str) or not identifier.strip():
            diagnostics.append("legacy.artifact_id_invalid")
        if not isinstance(provenance, str) or not provenance.strip():
            diagnostics.append(f"legacy.artifact_provenance_invalid:{identifier or ''}")
        if not isinstance(state, str) or not state.strip():
            diagnostics.append(f"legacy.artifact_state_invalid:{identifier or ''}")
        if not isinstance(version, str) or not version.strip():
            diagnostics.append(f"legacy.artifact_version_invalid:{identifier or ''}")
        role = _role(artifact.get("relation"))
        if not role:
            diagnostics.append(f"legacy.artifact_relation_invalid:{identifier or ''}")
        declared = _safe_declared_path(artifact.get("path"))
        if declared is None:
            diagnostics.append(f"legacy.artifact_path_invalid:{artifact.get('artifact_id', '')}")
            continue
        path, prefix = declared
        matches = (
            sorted((item for name, item in by_path.items() if name.startswith(f"{path}/")), key=lambda item: item.path)
            if prefix else ([by_path[path]] if path in by_path else [])
        )
        if not matches:
            diagnostics.append(f"legacy.artifact_missing:{path}")
            continue
        for member in matches:
            folded = member.path.casefold()
            if folded in seen:
                diagnostics.append(f"legacy.artifact_collision:{member.path}")
                continue
            seen.add(folded)
            relative = member.path[len(path) + 1:] if prefix else ""
            record: dict[str, Any] = {
                "file": member.path,
                "id": identifier if not relative else f"{identifier}/{relative}",
                "provenance": provenance,
                "role": role,
                "sha256": member.sha256,
                "size": member.size,
                "state": state,
                "version": version,
            }
            if "requirements" in artifact:
                record["requirements"] = artifact["requirements"]
            records.append(record)
    return records, diagnostics


def _publish_outputs(
    stage: Path,
    destination: Path,
    temporary: Path,
    staged_zip: Path | None,
    zip_destination: Path | None,
) -> None:
    backup = temporary / "previous-output"
    backup_zip = temporary / "previous-output.zip"
    moved = moved_zip = published = False
    try:
        if destination.exists():
            os.replace(destination, backup)
            moved = True
        if zip_destination is not None and zip_destination.exists():
            os.replace(zip_destination, backup_zip)
            moved_zip = True
        os.replace(stage, destination)
        published = True
        if staged_zip is not None and zip_destination is not None:
            os.replace(staged_zip, zip_destination)
    except OSError:
        if published and destination.exists():
            os.replace(destination, temporary / "failed-output")
        if moved and backup.exists() and not destination.exists():
            os.replace(backup, destination)
        if moved_zip and backup_zip.exists() and zip_destination is not None and not zip_destination.exists():
            os.replace(backup_zip, zip_destination)
        raise


def normalize_handoff_archive(
    source: Path,
    destination_root: Path,
    normalized_zip: Path | None = None,
    runtime_scope: str = "OPENAI_ONLY_PHASE_ONE",
) -> HandoffNormalizationOutcome:
    source_path = Path(source)
    destination = Path(destination_root).absolute()
    try:
        inventory = plugin_authoring.inventory_archive(source_path)
    except plugin_authoring.PluginAuthoringError as error:
        report = {"schema": "plugin-builder-handoff-normalization-v1", "status": "FAIL", "diagnostics": [error.code]}
        return HandoffNormalizationOutcome("FAIL", "UNKNOWN", (error.code,), report)
    source_hash = inventory.archive_sha256
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=f".{destination.name}.normalize-") as temporary_name:
        temporary = Path(temporary_name)
        raw = temporary / "raw"
        plugin_authoring.extract_archive(source_path, raw)
        classified = classify_handoff_profile(inventory, raw)
        if classified.profile in {"UNKNOWN", "AMBIGUOUS"}:
            report = {
                "schema": "plugin-builder-handoff-normalization-v1", "status": "BLOCKED",
                "profile": classified.profile, "source_archive_sha256": source_hash,
                "diagnostics": list(classified.diagnostics),
            }
            return HandoffNormalizationOutcome("BLOCKED", classified.profile, classified.diagnostics, report, source_hash)

        diagnostics: list[str] = []
        unresolved: list[str] = []
        if classified.profile == "LEGACY_WORKBENCH_V1":
            collisions = sorted(_CANONICAL_FILES & {item.path for item in inventory.members})
            if collisions:
                diagnostics.extend(f"normalization.canonical_collision:{item}" for item in collisions)
                report = {
                    "schema": "plugin-builder-handoff-normalization-v1", "status": "BLOCKED",
                    "profile": classified.profile, "source_archive_sha256": source_hash,
                    "diagnostics": diagnostics,
                }
                return HandoffNormalizationOutcome("BLOCKED", classified.profile, tuple(diagnostics), report, source_hash)
            legacy = _load_json(raw / "workbench_handoff_manifest.json") or {}
            records, record_diagnostics = _artifact_records(legacy, inventory)
            diagnostics.extend(record_diagnostics)
            authorities = [item for item in records if item["role"] == "approved_specification"]
            if len(authorities) != 1:
                diagnostics.append("normalization.authoritative_specification_required")
            else:
                if authorities[0].get("state") != "approved":
                    diagnostics.append("legacy.artifact_authority_state_invalid")
                if authorities[0].get("version") != legacy.get("specification_version"):
                    diagnostics.append("legacy.artifact_authority_version_mismatch")
            decisions = legacy.get("unresolved_owner_decisions", [])
            normalized_decisions = []
            if not isinstance(decisions, list):
                diagnostics.append("legacy.owner_decisions_invalid")
            else:
                for item in decisions:
                    valid = (
                        isinstance(item, dict)
                        and set(item) == {"blocking", "decision_id", "impact", "owner", "summary"}
                        and type(item.get("blocking")) is bool
                        and all(isinstance(item.get(key), str) and item[key].strip() for key in ("decision_id", "impact", "owner", "summary"))
                    )
                    if not valid:
                        diagnostics.append("legacy.owner_decision_invalid")
                        continue
                    normalized_decisions.append({key: item[key] for key in ("blocking", "decision_id", "impact", "owner", "summary")})
            approval_evidence = legacy.get("approval_evidence")
            approved = (
                legacy.get("specification_state") == "approved"
                and isinstance(approval_evidence, str) and bool(approval_evidence.strip())
                and isinstance(legacy.get("gate_result"), str) and legacy["gate_result"].startswith("APPROVED")
                and len(authorities) == 1
                and authorities[0].get("version") == legacy.get("specification_version")
                and authorities[0].get("state") == "approved"
                and not any(item["blocking"] for item in normalized_decisions)
                and not diagnostics
            )
            if not approved:
                unresolved.append("approval")
            authority = authorities[0] if len(authorities) == 1 else {
                "file": "", "id": "", "version": legacy.get("specification_version", "")
            }
            field_provenance = {
                "approval.confirmed_by": "MECHANICALLY_DERIVED",
                "approval.evidence": "COPIED" if approval_evidence else "UNRESOLVED",
                "approval.specification_version": "COPIED",
                "approval.state": "MECHANICALLY_DERIVED",
                "approved_specification": "COPIED",
                "unresolved_owner_decisions": "COPIED",
            }
            handoff = {
                "approval": {
                    "confirmed_by": "decision owner recorded by legacy handoff",
                    "evidence": approval_evidence if isinstance(approval_evidence, str) else "",
                    "specification_version": legacy.get("specification_version", ""),
                    "state": "approved" if approved else "pending",
                },
                "approved_specification": {
                    "file": authority.get("file", ""), "id": authority.get("id", ""),
                    "state": legacy.get("specification_state", ""), "version": authority.get("version", ""),
                },
                "field_provenance": field_provenance,
                "source_archive_sha256": source_hash,
                "source_profile": classified.profile,
                "unresolved_owner_decisions": normalized_decisions,
            }
            handoff_bytes = canonical_bytes(handoff)
            (raw / "workbench-handoff.json").write_bytes(handoff_bytes)
            represented = {item["file"] for item in records}
            supporting = [
                asdict(item) | {"file": item.path}
                for item in inventory.members
                if item.path not in represented and item.path not in _CANONICAL_FILES
            ]
            for item in supporting:
                item.pop("path", None)
            manifest = {
                "application": legacy.get("application_name", ""),
                "artifacts": records,
                "canonical_handoff": {
                    "file": "workbench-handoff.json", "sha256": sha256(handoff_bytes).hexdigest(),
                    "size": len(handoff_bytes),
                },
                "gate": legacy.get("gate_result", ""),
                "normalization": {
                    "adapter_version": ADAPTER_VERSION,
                    "field_provenance": {
                        "application": "COPIED", "artifacts.role": "MECHANICALLY_DERIVED",
                        "artifacts.sha256": "MECHANICALLY_DERIVED", "gate": "COPIED",
                        "runtime_scope": "OWNER_SUPPLIED", "source_archive_sha256": "MECHANICALLY_DERIVED",
                        "spec_version": "COPIED",
                    },
                    "profile": classified.profile,
                },
                "package_kind": "normalized-workbench-handoff",
                "package_schema_version": 1,
                "runtime_scope": runtime_scope,
                "source_archive_sha256": source_hash,
                "spec_version": legacy.get("specification_version", ""),
                "supporting_files": supporting,
            }
            (raw / "package-manifest.json").write_bytes(canonical_bytes(manifest))

        output_tree_hash = plugin_authoring.tree_sha256(raw)
        staged_zip = temporary / "normalized.zip"
        output_archive_hash = plugin_authoring.write_deterministic_zip(raw, staged_zip) if normalized_zip is not None else None
        status = "PASS" if not diagnostics and not unresolved else "BLOCKED"
        report = {
            "schema": "plugin-builder-handoff-normalization-v1",
            "status": status,
            "profile": classified.profile,
            "adapter_version": ADAPTER_VERSION,
            "runtime_scope": runtime_scope,
            "source_archive_sha256": source_hash,
            "output_archive_sha256": output_archive_hash,
            "output_tree_sha256": output_tree_hash,
            "unresolved_fields": sorted(unresolved),
            "diagnostics": sorted(set(diagnostics)),
        }
        zip_destination = Path(normalized_zip).absolute() if normalized_zip is not None else None
        if normalized_zip is not None:
            assert zip_destination is not None
            zip_destination.parent.mkdir(parents=True, exist_ok=True)
        _publish_outputs(
            raw, destination, temporary,
            staged_zip if normalized_zip is not None else None,
            zip_destination,
        )
        return HandoffNormalizationOutcome(
            status, classified.profile, tuple(sorted(set(diagnostics))), report,
            source_hash, output_archive_hash, output_tree_hash,
        )
