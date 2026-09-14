"""Reusable build and runtime support for Obvious One plugin distributions."""

from .contract import (
    AssetGroup,
    ContractError,
    DistributionContract,
    RagProfile,
    load_contract,
    validate_contract,
)
from .verification import (
    ALLOWED_PLACEHOLDERS,
    RESULT_STATES,
    ApplicationConfig,
    ApplicationVerificationProfile,
    CodexBuildProfile,
    ExpansionContext,
    GateResult,
    MarketplaceProfile,
    ProvenanceInventoryRule,
    ProvenanceProfile,
    VerificationCommand,
    VerificationConfigError,
    aggregate_state,
    discover_applications,
    expand_argv,
    load_application_config,
    resolve_within,
    select_applications,
)
from .provenance import (
    ProvenanceError,
    build_provenance,
    inventory_source,
    validate_provenance,
)

__all__ = [
    "AssetGroup",
    "ContractError",
    "DistributionContract",
    "RagProfile",
    "load_contract",
    "validate_contract",
    "ALLOWED_PLACEHOLDERS",
    "RESULT_STATES",
    "ApplicationConfig",
    "ApplicationVerificationProfile",
    "CodexBuildProfile",
    "ExpansionContext",
    "GateResult",
    "MarketplaceProfile",
    "ProvenanceInventoryRule",
    "ProvenanceProfile",
    "VerificationCommand",
    "VerificationConfigError",
    "aggregate_state",
    "discover_applications",
    "expand_argv",
    "load_application_config",
    "resolve_within",
    "select_applications",
    "ProvenanceError",
    "build_provenance",
    "inventory_source",
    "validate_provenance",
]

__version__ = "0.1.0"
