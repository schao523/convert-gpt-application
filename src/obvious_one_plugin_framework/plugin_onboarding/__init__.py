"""Public contracts for Plugin Builder ZIP onboarding."""

from .contract import (
    CandidateMember,
    LegacyPluginBuilderAdoption,
    PortableContentManifestAdoption,
    OnboardingError,
    PackageMember,
    PackageMetadata,
    WorkbenchRepairMetadata,
    PublicationDecisions,
    load_package_metadata,
    load_legacy_plugin_builder_adoption,
    load_plugin_builder_adoption,
    load_portable_content_manifest_adoption,
    load_onboarding_metadata,
    load_publication_decisions,
)
from .materialize import prepare_plugin_zip_marketplace
from .inspection import (
    inspect_legacy_plugin_builder_package,
    inspect_portable_content_manifest_package,
)
from .repair_contract import (
    DelegatedReferenceRepair,
    RepairReference,
    load_repair_contract,
)
from .repair import RepairResult, repair_delegated_reference_archive

__all__ = [
    "CandidateMember",
    "LegacyPluginBuilderAdoption",
    "PortableContentManifestAdoption",
    "OnboardingError",
    "PackageMember",
    "PackageMetadata",
    "WorkbenchRepairMetadata",
    "PublicationDecisions",
    "load_package_metadata",
    "load_legacy_plugin_builder_adoption",
    "load_plugin_builder_adoption",
    "load_portable_content_manifest_adoption",
    "load_onboarding_metadata",
    "load_publication_decisions",
    "prepare_plugin_zip_marketplace",
    "inspect_legacy_plugin_builder_package",
    "inspect_portable_content_manifest_package",
    "DelegatedReferenceRepair",
    "RepairReference",
    "RepairResult",
    "load_repair_contract",
    "repair_delegated_reference_archive",
]
