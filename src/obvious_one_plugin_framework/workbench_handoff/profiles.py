"""Exact, fail-closed recognizers for supported Workbench handoff envelopes."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .contract import HANDOFF_CONTRACT, HANDOFF_SCHEMA


_LEGACY_WORKBENCH_FIELDS = {
    "application_name",
    "specification_state",
    "approval_evidence",
    "gate_result",
    "specification_version",
    "included_artifacts",
}
_DESIGN_ASSISTANT_FIELDS = {
    "application",
    "spec_version",
    "gate",
    "approval_evidence",
    "artifacts",
    "unresolved_owner_decisions",
    "exclusions",
    "reserved_workbench_decisions",
    "readiness_note",
}


@dataclass(frozen=True)
class HandoffProfile:
    profile: str
    diagnostics: tuple[str, ...] = ()


def _load_object(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def classify_handoff_profile(root: Path) -> HandoffProfile:
    """Classify one extracted package without choosing among competing authorities."""
    package_root = Path(root)
    manifest = _load_object(package_root / "package-manifest.json")
    handoff = _load_object(package_root / "workbench-handoff.json")
    legacy = _load_object(package_root / "workbench_handoff_manifest.json")
    full = _load_object(package_root / "handoff_manifest.json")
    delta = _load_object(package_root / "delta_handoff_manifest.json")

    authorities: list[str] = []
    canonical_pair = (
        manifest is not None
        and handoff is not None
        and manifest.get("package_schema_version") == 1
        and manifest.get("package_kind") == "normalized-workbench-handoff"
    )
    if canonical_pair:
        if manifest.get("handoff_contract") == HANDOFF_CONTRACT and handoff.get("schema") == HANDOFF_SCHEMA:
            authorities.append("WORKBENCH_HANDOFF_V1_1")
        else:
            authorities.append("CANONICAL_V1")
    if legacy is not None and _LEGACY_WORKBENCH_FIELDS.issubset(legacy):
        authorities.append("LEGACY_WORKBENCH_V1")
    if full is not None and _DESIGN_ASSISTANT_FIELDS.issubset(full):
        authorities.append("COOL_DESIGN_ASSISTANT_FULL_V1")
    if delta is not None and _DESIGN_ASSISTANT_FIELDS.issubset(delta):
        authorities.append("COOL_DESIGN_ASSISTANT_DELTA_V1")

    if len(authorities) > 1:
        return HandoffProfile("AMBIGUOUS", ("profile.multiple_authorities",))
    if not authorities:
        return HandoffProfile("UNKNOWN", ("profile.unrecognized",))
    return HandoffProfile(authorities[0])


__all__ = ["HandoffProfile", "classify_handoff_profile"]
