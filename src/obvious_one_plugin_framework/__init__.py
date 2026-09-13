"""Reusable build and runtime support for Obvious One plugin distributions."""

from .contract import (
    AssetGroup,
    ContractError,
    DistributionContract,
    RagProfile,
    load_contract,
    validate_contract,
)

__all__ = [
    "AssetGroup",
    "ContractError",
    "DistributionContract",
    "RagProfile",
    "load_contract",
    "validate_contract",
]

__version__ = "0.1.0"
