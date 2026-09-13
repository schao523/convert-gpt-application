"""Build-time import surface for package-local adapter contracts."""

from .templates.runtime.obvious_one_runtime.adapters import (
    AdapterContractError,
    DiscoveryRequest,
    IngestionRequest,
    validate_discovery_request,
    validate_discovery_results,
    validate_ingestion_request,
)

__all__ = [
    "AdapterContractError",
    "DiscoveryRequest",
    "IngestionRequest",
    "validate_discovery_request",
    "validate_discovery_results",
    "validate_ingestion_request",
]
