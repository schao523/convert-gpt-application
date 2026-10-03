"""Compatibility import surface for the shared Workbench handoff runtime."""

from __future__ import annotations

from pathlib import Path

from .bootstrap import workbench_handoff


ADAPTER_VERSION = workbench_handoff.ADAPTER_VERSION
HandoffProfile = workbench_handoff.HandoffProfile
HandoffNormalizationOutcome = workbench_handoff.HandoffNormalizationOutcome
normalize_handoff_archive = workbench_handoff.normalize_handoff_archive


def classify_handoff_profile(inventory_or_root, extracted_root: Path | None = None):
    """Accept the former two-argument surface while delegating to the shared recognizer."""
    root = Path(inventory_or_root) if extracted_root is None else Path(extracted_root)
    return workbench_handoff.classify_handoff_profile(root)


__all__ = [
    "ADAPTER_VERSION",
    "HandoffProfile",
    "HandoffNormalizationOutcome",
    "classify_handoff_profile",
    "normalize_handoff_archive",
]
