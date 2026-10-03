"""Portable Workbench handoff contract and identity primitives."""

from .contract import (
    HANDOFF_CONTRACT,
    HANDOFF_SCHEMA,
    RUNTIME_SCOPE,
    HandoffValidation,
    canonical_json_bytes,
    validate_canonical_handoff,
)
from .identity import BaselineIdentity, baseline_identity_from_archive, validate_update_baseline
from .normalization import ADAPTER_VERSION, HandoffNormalizationOutcome, normalize_handoff_archive
from .profiles import HandoffProfile, classify_handoff_profile

__all__ = [
    "HANDOFF_CONTRACT",
    "HANDOFF_SCHEMA",
    "RUNTIME_SCOPE",
    "HandoffValidation",
    "BaselineIdentity",
    "canonical_json_bytes",
    "validate_canonical_handoff",
    "baseline_identity_from_archive",
    "validate_update_baseline",
    "ADAPTER_VERSION",
    "HandoffProfile",
    "HandoffNormalizationOutcome",
    "classify_handoff_profile",
    "normalize_handoff_archive",
]
