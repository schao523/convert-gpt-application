"""Public contracts for Plugin Builder ZIP onboarding."""

from .contract import (
    CandidateMember,
    LegacyPluginBuilderAdoption,
    OnboardingError,
    PackageMember,
    PackageMetadata,
    WorkbenchRepairMetadata,
    PublicationDecisions,
    load_package_metadata,
    load_legacy_plugin_builder_adoption,
    load_onboarding_metadata,
    load_publication_decisions,
)
from .materialize import prepare_plugin_zip_marketplace
from .inspection import inspect_legacy_plugin_builder_package
from .repair_contract import (
    DelegatedReferenceRepair,
    RepairReference,
    load_repair_contract,
)
from .repair import RepairResult, repair_delegated_reference_archive

__all__ = [
    "CandidateMember",
    "LegacyPluginBuilderAdoption",
    "OnboardingError",
    "PackageMember",
    "PackageMetadata",
    "WorkbenchRepairMetadata",
    "PublicationDecisions",
    "load_package_metadata",
    "load_legacy_plugin_builder_adoption",
    "load_onboarding_metadata",
    "load_publication_decisions",
    "prepare_plugin_zip_marketplace",
    "inspect_legacy_plugin_builder_package",
    "DelegatedReferenceRepair",
    "RepairReference",
    "RepairResult",
    "load_repair_contract",
    "repair_delegated_reference_archive",
]
