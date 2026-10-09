"""Public contracts for Plugin Builder ZIP onboarding."""

from .contract import (
    CandidateMember,
    OnboardingError,
    PackageMember,
    PackageMetadata,
    PublicationDecisions,
    load_package_metadata,
    load_publication_decisions,
)
from .materialize import prepare_plugin_zip_marketplace
from .repair_contract import (
    DelegatedReferenceRepair,
    RepairReference,
    load_repair_contract,
)
from .repair import RepairResult, repair_delegated_reference_archive

__all__ = [
    "CandidateMember",
    "OnboardingError",
    "PackageMember",
    "PackageMetadata",
    "PublicationDecisions",
    "load_package_metadata",
    "load_publication_decisions",
    "prepare_plugin_zip_marketplace",
    "DelegatedReferenceRepair",
    "RepairReference",
    "RepairResult",
    "load_repair_contract",
    "repair_delegated_reference_archive",
]
