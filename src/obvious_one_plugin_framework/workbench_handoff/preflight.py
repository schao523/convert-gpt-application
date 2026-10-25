"""Deterministic read-only Source Handoff ZIP preflight."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Any

from ..plugin_authoring import PluginAuthoringError, extract_archive, inventory_archive
from .contract import HANDOFF_CONTRACT, RUNTIME_SCOPE
from .profiles import classify_handoff_profile
from .source_contract import SOURCE_PROFILES, analyze_source_handoff


SUPPORTED_INPUT_PROFILES = (
    "COOL_DESIGN_ASSISTANT_DELTA_V1", "COOL_DESIGN_ASSISTANT_FULL_V1",
    "LEGACY_WORKBENCH_V1", "CANONICAL_V1", "WORKBENCH_HANDOFF_V1_1",
)
_CHECKS = tuple(f"PF{i:02d}" for i in range(1, 11))


@dataclass(frozen=True)
class SourcePreflightOutcome:
    status: str
    profile: str
    diagnostics: tuple[str, ...]
    report: dict[str, Any]


def _check_for(code: str) -> str:
    if code.startswith("profile.") or code.startswith("source.profile"):
        return "PF01" if code.startswith("profile.") else "PF09"
    if code.startswith("archive_"):
        return "PF08"
    if code.startswith("requirements."):
        return "PF04" if "binding" in code or "index" in code else "PF03"
    if code.startswith("approval.") or code.startswith("normalization.authoritative"):
        return "PF05"
    if code.startswith("owner_decisions.") or code.startswith("rights."):
        return "PF07"
    if code.startswith("reference."):
        return "PF06"
    if code.startswith("package.declared_member_mismatch"):
        return "PF08"
    return "PF02"


def _corrective_action(code: str) -> str:
    key = code.partition(":")[0]
    if key.startswith("profile.") or key == "source.profile_not_v11_eligible":
        return "Supply one supported full or delta Source Handoff authority for the v1.1 target."
    if key.startswith("archive_"):
        return "Repackage the source with safe, unique relative ZIP members and retry."
    if key.startswith("requirements."):
        return "Correct the exact requirement record and its declared artifact binding."
    if key.startswith("approval.") or key.startswith("normalization.authoritative"):
        return "Provide one unambiguous approved specification version and matching owner approval evidence."
    if key.startswith("owner_decisions.") or key.startswith("rights."):
        return "Resolve the blocking owner or rights decision and record its authority in the source manifest."
    if key.startswith("reference."):
        return "Correct the declared reference inventory and usage map."
    if key.startswith("package."):
        return "Correct the manifest declaration or packaged artifact bytes and retry."
    return "Correct the declared source evidence and run preflight again."


def _report(status: str, profile: str, codes: tuple[str, ...], digest: str | None,
            *, completed_checks: frozenset[str] = frozenset()) -> dict[str, Any]:
    by_check = {check: [] for check in _CHECKS}
    for code in codes:
        by_check[_check_for(code)].append(code)
    checks = [
        {"id": check, "status": "BLOCKED" if by_check[check] else ("PASS" if check in completed_checks else "NOT VERIFIED"),
         "diagnostics": by_check[check]}
        for check in _CHECKS
    ]
    diagnostics = []
    for code in codes:
        location = code.partition(":")[2] or None
        diagnostics.append({
            "check_id": _check_for(code), "status": status if status != "PASS" else "BLOCKED",
            "severity": "ERROR", "location": location,
            "requirement_id": location if code.startswith("requirements.") else None,
            "code": code, "explanation": code.partition(":")[0].replace(".", " ").replace("_", " "),
            "corrective_action": _corrective_action(code),
        })
    return {
        "operation": "preflight-source-handoff", "status": status,
        "input_profile": profile, "target_output_profile": HANDOFF_CONTRACT,
        "source_archive_sha256": digest, "normalization_ready": status == "PASS",
        "supported_input_profiles": list(SUPPORTED_INPUT_PROFILES),
        "checks": checks, "diagnostics": diagnostics, "errors": list(codes),
    }


def preflight_handoff_archive(source: Path, *, runtime_scope: str = RUNTIME_SCOPE) -> SourcePreflightOutcome:
    """Inspect source bytes without creating a canonical package or changing the source."""
    try:
        inventory = inventory_archive(Path(source))
    except PluginAuthoringError as exc:
        codes = (exc.code,)
        return SourcePreflightOutcome("BLOCKED", "UNKNOWN", codes, _report("BLOCKED", "UNKNOWN", codes, None))
    with tempfile.TemporaryDirectory(prefix="source-handoff-preflight-") as temporary:
        root = Path(temporary) / "source"
        try:
            extract_archive(Path(source), root)
        except PluginAuthoringError as exc:
            codes = (exc.code,)
            return SourcePreflightOutcome("BLOCKED", "UNKNOWN", codes, _report("BLOCKED", "UNKNOWN", codes, inventory.archive_sha256))
        classified = classify_handoff_profile(root)
        if classified.profile in {"UNKNOWN", "AMBIGUOUS"}:
            codes = classified.diagnostics
        elif classified.profile not in SOURCE_PROFILES:
            codes = ("source.profile_not_v11_eligible",)
        else:
            codes = analyze_source_handoff(root, classified.profile, runtime_scope=runtime_scope).diagnostics
    status = "BLOCKED" if codes else "PASS"
    completed = frozenset(_CHECKS) if classified.profile in SOURCE_PROFILES else frozenset({"PF01"})
    return SourcePreflightOutcome(status, classified.profile, codes, _report(
        status, classified.profile, codes, inventory.archive_sha256, completed_checks=completed,
    ))


__all__ = ["SUPPORTED_INPUT_PROFILES", "SourcePreflightOutcome", "preflight_handoff_archive"]
