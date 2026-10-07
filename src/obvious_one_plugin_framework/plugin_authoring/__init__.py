"""Portable primitives for deterministic plugin authoring."""

from .archive import (
    ArchiveInventory,
    ArchiveLimits,
    ArchiveMember,
    LocatedPluginRoot,
    PluginAuthoringError,
    extract_archive,
    inventory_archive,
    locate_plugin_archive_root,
)
from .identity import TreeMember, tree_manifest, tree_sha256, write_deterministic_zip
from .manifests import (
    PORTABLE_PLUGIN_SCHEMA,
    ManifestPairIdentity,
    legacy_overlay_from_portable,
    manifest_pair_mismatches,
    materialize_manifest_pair,
    portable_manifest_from_legacy,
)
from .validation import (
    ValidationIssue,
    validate_manifest_pair,
    validate_plugin_tree,
    validate_portable_manifest,
    validate_reference_closure,
    validate_path_bindings,
    validate_skill_tree,
)
from .tools import ApplicationToolContract, validate_application_tool_contract
from .materialize import materialize_files, overlay_files

__all__ = [
    "ArchiveInventory",
    "ArchiveLimits",
    "ArchiveMember",
    "LocatedPluginRoot",
    "PluginAuthoringError",
    "TreeMember",
    "extract_archive",
    "inventory_archive",
    "locate_plugin_archive_root",
    "tree_manifest",
    "tree_sha256",
    "write_deterministic_zip",
    "PORTABLE_PLUGIN_SCHEMA",
    "ManifestPairIdentity",
    "legacy_overlay_from_portable",
    "manifest_pair_mismatches",
    "materialize_manifest_pair",
    "portable_manifest_from_legacy",
    "ValidationIssue",
    "validate_manifest_pair",
    "validate_plugin_tree",
    "validate_portable_manifest",
    "validate_reference_closure",
    "validate_path_bindings",
    "validate_skill_tree",
    "ApplicationToolContract",
    "validate_application_tool_contract",
    "materialize_files",
    "overlay_files",
]
