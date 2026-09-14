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
    VerificationCommand,
    VerificationConfigError,
    aggregate_state,
    discover_applications,
    expand_argv,
    load_application_config,
    resolve_within,
    select_applications,
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
    "VerificationCommand",
    "VerificationConfigError",
    "aggregate_state",
    "discover_applications",
    "expand_argv",
    "load_application_config",
    "resolve_within",
    "select_applications",
]

__version__ = "0.1.0"
