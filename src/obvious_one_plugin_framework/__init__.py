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
    MarketplaceProfile,
    VerificationCommand,
    VerificationConfigError,
    discover_applications,
    load_application_config,
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
    "MarketplaceProfile",
    "VerificationCommand",
    "VerificationConfigError",
    "discover_applications",
    "load_application_config",
]

__version__ = "0.1.0"
