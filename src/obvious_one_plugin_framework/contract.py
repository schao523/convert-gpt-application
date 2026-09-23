"""Strict declarative contracts for generated OpenClaw plugin editions."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Literal, Mapping


_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_LEGACY_ROOT_KEYS = {
    "schema_version", "plugin_id", "package_name", "family", "version",
    "source_root", "include_files", "include_prefixes", "exclude_paths",
    "max_total_bytes", "release_repository", "release_tag_template",
    "readme_overlay", "audit_hook", "rag",
}
_V3_ROOT_KEYS = _LEGACY_ROOT_KEYS | {"content_rules", "publication"}
_RAG_KEYS = {
    "app_id", "namespace", "runtime_lock", "runtime_lock_digest",
    "model_manifest", "model_digest", "index_manifest", "asset_groups",
}
_ASSET_KEYS = {"name", "archive_name", "source_paths", "install_subdir"}
_CONTENT_RULE_KEYS = {"id", "paths", "prefixes", "classification", "redistribution"}
_REDISTRIBUTION_KEYS = {"status", "provenance"}
_PUBLICATION_KEYS = {"github_marketplace", "clawhub"}
_GITHUB_MARKETPLACE_KEYS = {"enabled"}
_CLAWHUB_KEYS = {"enabled", "family", "native_manifest"}
_SUPPORTED_CLAWHUB_FAMILIES = frozenset({"native-plugin"})


class ContractError(ValueError):
    """Raised when a distribution contract violates a stable rule."""

    def __init__(self, code: str, detail: str = "") -> None:
        message = code if not detail else f"{code}: {detail}"
        super().__init__(message)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class AssetGroup:
    name: str
    archive_name: str
    source_paths: tuple[str, ...]
    install_subdir: str


@dataclass(frozen=True)
class RagProfile:
    app_id: str
    namespace: str
    runtime_lock: str
    runtime_lock_digest: str
    model_manifest: str
    model_digest: str
    index_manifest: str
    asset_groups: tuple[AssetGroup, ...]


@dataclass(frozen=True)
class RedistributionEvidence:
    status: str
    provenance: str


@dataclass(frozen=True)
class ContentRule:
    rule_id: str
    paths: tuple[str, ...]
    prefixes: tuple[str, ...]
    classification: Literal["text", "binary"]
    redistribution: RedistributionEvidence


@dataclass(frozen=True)
class PublicationTarget:
    enabled: bool
    family: str | None = None
    native_manifest: str | None = None


@dataclass(frozen=True)
class PublicationProfile:
    github_marketplace: PublicationTarget
    clawhub: PublicationTarget


@dataclass(frozen=True)
class DistributionContract:
    schema_version: int
    plugin_id: str
    package_name: str
    family: str
    version: str
    source_root: Path
    include_files: tuple[str, ...]
    include_prefixes: tuple[str, ...]
    exclude_paths: tuple[str, ...]
    max_total_bytes: int
    release_repository: str
    release_tag_template: str
    readme_overlay: str | None
    audit_hook: str | None
    rag: RagProfile | None
    content_rules: tuple[ContentRule, ...]
    publication: PublicationProfile | None
    contract_path: Path


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("invalid_type", f"{label} must be an object")
    return value


def _only_keys(value: Mapping[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ContractError("unknown_key", f"{label}.{unknown[0]}")
    missing = sorted(allowed - set(value))
    if missing:
        raise ContractError("missing_key", f"{label}.{missing[0]}")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError("invalid_text", label)
    return value


def _optional_text(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _text(value, label)


def _boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ContractError("invalid_type", f"{label} must be a boolean")
    return value


def _relative(value: Any, label: str, *, allow_dot: bool = False) -> str:
    text = _text(value, label).replace("\\", "/")
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or (not allow_dot and text in {"", "."}):
        raise ContractError("asset_path_escape", label)
    if any(part in {"", "."} for part in path.parts):
        raise ContractError("invalid_path", label)
    return path.as_posix()


def _path_list(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ContractError("invalid_type", f"{label} must be a list")
    normalized = tuple(_relative(item, label) for item in value)
    if len(normalized) != len(set(normalized)):
        raise ContractError("duplicate_path", label)
    return normalized


def _source_root(value: Any, contract_path: Path) -> Path:
    text = _text(value, "source_root").replace("\\", "/")
    relative = PurePosixPath(text)
    if relative.is_absolute() or text not in {"..", "."} and ".." in relative.parts:
        raise ContractError("source_root_escape", text)
    if text == "..":
        return contract_path.parent.parent.resolve()
    if any(part in {"", "."} for part in relative.parts) and text != ".":
        raise ContractError("invalid_path", "source_root")
    return (contract_path.parent / relative.as_posix()).resolve()


def _digest(value: Any, label: str) -> str:
    text = _text(value, label).lower()
    if not _DIGEST.fullmatch(text):
        raise ContractError("invalid_digest", label)
    return text


def load_contract(path: Path) -> DistributionContract:
    contract_path = Path(path).resolve()
    try:
        raw = _mapping(json.loads(contract_path.read_text(encoding="utf-8")), "contract")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("invalid_json", str(path)) from exc
    schema_version = raw.get("schema_version")
    if not isinstance(schema_version, int) or isinstance(schema_version, bool):
        raise ContractError("unsupported_schema", str(schema_version))
    if schema_version in (1, 2):
        _only_keys(raw, _LEGACY_ROOT_KEYS, "contract")
    elif schema_version == 3:
        _only_keys(raw, _V3_ROOT_KEYS, "contract")
    else:
        raise ContractError("unsupported_schema", str(schema_version))
    groups: list[AssetGroup] = []
    rag_profile = None
    if raw["rag"] is not None:
        rag_raw = _mapping(raw["rag"], "rag")
        _only_keys(rag_raw, _RAG_KEYS, "rag")
        groups_raw = rag_raw["asset_groups"]
        if not isinstance(groups_raw, list) or not groups_raw:
            raise ContractError("invalid_asset_groups", "at least one group is required")
        for index, item in enumerate(groups_raw):
            group = _mapping(item, f"rag.asset_groups[{index}]")
            _only_keys(group, _ASSET_KEYS, f"rag.asset_groups[{index}]")
            archive = _relative(group["archive_name"], "archive_name")
            if "/" in archive or "{version}" not in archive:
                raise ContractError("invalid_archive_name", archive)
            groups.append(AssetGroup(
                name=_text(group["name"], "asset_group.name"),
                archive_name=archive,
                source_paths=_path_list(group["source_paths"], "asset_group.source_paths"),
                install_subdir=_relative(group["install_subdir"], "asset_group.install_subdir"),
            ))
        if len({group.name for group in groups}) != len(groups):
            raise ContractError("duplicate_asset_group", "name")
        if len({group.install_subdir for group in groups}) != len(groups):
            raise ContractError("duplicate_asset_destination", "install_subdir")
        app_id = _text(rag_raw["app_id"], "rag.app_id")
        namespace = _text(rag_raw["namespace"], "rag.namespace")
        if not namespace.startswith(app_id + ":"):
            raise ContractError("namespace_owner_mismatch", namespace)
        rag_profile = RagProfile(
            app_id=app_id,
            namespace=namespace,
            runtime_lock=_relative(rag_raw["runtime_lock"], "rag.runtime_lock"),
            runtime_lock_digest=_digest(rag_raw["runtime_lock_digest"], "rag.runtime_lock_digest"),
            model_manifest=_relative(rag_raw["model_manifest"], "rag.model_manifest"),
            model_digest=_digest(rag_raw["model_digest"], "rag.model_digest"),
            index_manifest=_relative(rag_raw["index_manifest"], "rag.index_manifest"),
            asset_groups=tuple(groups),
        )
    family = _text(raw["family"], "family")
    if family != "bundle-plugin":
        raise ContractError("invalid_family", family)
    include_files = _path_list(raw["include_files"], "include_files")
    if "openclaw.plugin.json" in include_files:
        raise ContractError("native_marker_forbidden", "openclaw.plugin.json")
    max_total_bytes = raw["max_total_bytes"]
    if not isinstance(max_total_bytes, int) or max_total_bytes <= 0:
        raise ContractError("invalid_size_limit", "max_total_bytes")
    content_rules: tuple[ContentRule, ...] = ()
    publication = None
    source_root = _source_root(raw["source_root"], contract_path)
    plugin_id = _text(raw["plugin_id"], "plugin_id")
    package_name = _text(raw["package_name"], "package_name")
    version = _text(raw["version"], "version")
    if schema_version == 3:
        content_rules = _parse_content_rules(raw["content_rules"], source_root)
        publication = _parse_publication(
            raw["publication"],
            source_root,
            plugin_id=plugin_id,
            package_name=package_name,
            version=version,
        )

    contract = DistributionContract(
        schema_version=schema_version,
        plugin_id=plugin_id,
        package_name=package_name,
        family=family,
        version=version,
        source_root=source_root,
        include_files=include_files,
        include_prefixes=_path_list(raw["include_prefixes"], "include_prefixes"),
        exclude_paths=_path_list(raw["exclude_paths"], "exclude_paths"),
        max_total_bytes=max_total_bytes,
        release_repository=_text(raw["release_repository"], "release_repository"),
        release_tag_template=_text(raw["release_tag_template"], "release_tag_template"),
        readme_overlay=_optional_text(raw["readme_overlay"], "readme_overlay"),
        audit_hook=_optional_text(raw["audit_hook"], "audit_hook"),
        rag=rag_profile,
        content_rules=content_rules,
        publication=publication,
        contract_path=contract_path,
    )
    validate_contract(contract, contract.source_root)
    return contract


def validate_contract(contract: DistributionContract, source_root: Path) -> None:
    if contract.schema_version not in (1, 2, 3):
        raise ContractError("unsupported_schema", str(contract.schema_version))
    if contract.schema_version == 1 and contract.rag is None:
        raise ContractError("missing_rag", "schema_version 1 requires rag")
    if not source_root.is_dir():
        raise ContractError("source_root_missing", str(source_root))
    manifest_path = source_root / ".codex-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("plugin_manifest_invalid", str(manifest_path)) from exc
    if manifest.get("name") != contract.plugin_id or manifest.get("version") != contract.version:
        raise ContractError("plugin_identity_mismatch", contract.plugin_id)
    excluded = set(contract.exclude_paths)
    included = set(contract.include_files)
    overlap = sorted(excluded & included)
    if overlap:
        raise ContractError("include_exclude_overlap", overlap[0])
    if "{version}" not in contract.release_tag_template:
        raise ContractError("invalid_release_tag_template", contract.release_tag_template)


def require_buildable_contract(contract: DistributionContract) -> None:
    """Reject legacy contracts for every operation that creates new bytes."""

    if contract.schema_version != 3:
        raise ContractError("legacy_contract_read_only", str(contract.schema_version))


def _parse_content_rules(value: Any, source_root: Path) -> tuple[ContentRule, ...]:
    if not isinstance(value, list) or not value:
        raise ContractError("invalid_content_rules", "at least one rule is required")
    rules: list[ContentRule] = []
    for index, item in enumerate(value):
        label = f"content_rules[{index}]"
        raw = _mapping(item, label)
        _only_keys(raw, _CONTENT_RULE_KEYS, label)
        paths = _path_list(raw["paths"], f"{label}.paths")
        prefixes = _path_list(raw["prefixes"], f"{label}.prefixes")
        if not paths and not prefixes:
            raise ContractError("empty_rule_selector", label)
        classification = _text(raw["classification"], f"{label}.classification")
        if classification not in {"text", "binary"}:
            raise ContractError("invalid_content_classification", classification)
        redistribution_raw = _mapping(raw["redistribution"], f"{label}.redistribution")
        _only_keys(redistribution_raw, _REDISTRIBUTION_KEYS, f"{label}.redistribution")
        status = _text(redistribution_raw["status"], f"{label}.redistribution.status")
        if status != "approved":
            raise ContractError("rights_unresolved", label)
        provenance = _relative(
            redistribution_raw["provenance"],
            f"{label}.redistribution.provenance",
        )
        if not (source_root / provenance).is_file():
            raise ContractError("rights_unresolved", provenance)
        rules.append(
            ContentRule(
                rule_id=_text(raw["id"], f"{label}.id"),
                paths=paths,
                prefixes=prefixes,
                classification=classification,
                redistribution=RedistributionEvidence(status=status, provenance=provenance),
            )
        )
    if len({rule.rule_id for rule in rules}) != len(rules):
        raise ContractError("duplicate_content_rule", "id")
    return tuple(rules)


def _parse_publication(
    value: Any,
    source_root: Path,
    *,
    plugin_id: str,
    package_name: str,
    version: str,
) -> PublicationProfile:
    raw = _mapping(value, "publication")
    _only_keys(raw, _PUBLICATION_KEYS, "publication")

    github_raw = _mapping(raw["github_marketplace"], "publication.github_marketplace")
    _only_keys(github_raw, _GITHUB_MARKETPLACE_KEYS, "publication.github_marketplace")
    github = PublicationTarget(
        enabled=_boolean(github_raw["enabled"], "publication.github_marketplace.enabled")
    )

    clawhub_raw = _mapping(raw["clawhub"], "publication.clawhub")
    _only_keys(clawhub_raw, _CLAWHUB_KEYS, "publication.clawhub")
    enabled = _boolean(clawhub_raw["enabled"], "publication.clawhub.enabled")
    family = _optional_text(clawhub_raw["family"], "publication.clawhub.family")
    native_manifest_raw = clawhub_raw["native_manifest"]
    if not enabled:
        if family is not None or native_manifest_raw is not None:
            raise ContractError("clawhub_disabled_fields", "family and native_manifest must be null")
        clawhub = PublicationTarget(enabled=False)
    else:
        if family not in _SUPPORTED_CLAWHUB_FAMILIES:
            raise ContractError("clawhub_family_unsupported", str(family))
        if native_manifest_raw is None:
            raise ContractError("clawhub_native_manifest_required")
        native_manifest = _relative(
            native_manifest_raw,
            "publication.clawhub.native_manifest",
        )
        if not (source_root / native_manifest).is_file():
            raise ContractError("clawhub_native_manifest_missing", native_manifest)
        _validate_native_clawhub_manifest(
            source_root,
            native_manifest,
            plugin_id=plugin_id,
            package_name=package_name,
            version=version,
        )
        clawhub = PublicationTarget(
            enabled=True,
            family=family,
            native_manifest=native_manifest,
        )
    return PublicationProfile(github_marketplace=github, clawhub=clawhub)


def _validate_native_clawhub_manifest(
    source_root: Path,
    native_manifest: str,
    *,
    plugin_id: str,
    package_name: str,
    version: str,
) -> None:
    if native_manifest != "openclaw.plugin.json":
        raise ContractError("clawhub_native_manifest_invalid", native_manifest)
    try:
        manifest = json.loads((source_root / native_manifest).read_text(encoding="utf-8"))
        package = json.loads((source_root / "package.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("clawhub_native_manifest_invalid", native_manifest) from exc
    if not isinstance(manifest, dict) or manifest.get("id") != plugin_id:
        raise ContractError("clawhub_native_manifest_invalid", native_manifest)
    schema = manifest.get("configSchema")
    if not isinstance(schema, dict) or schema.get("type") != "object":
        raise ContractError("clawhub_native_manifest_invalid", native_manifest)
    if not isinstance(package, dict) or package.get("name") != package_name or package.get("version") != version:
        raise ContractError("clawhub_native_manifest_invalid", "package.json")
    openclaw = package.get("openclaw")
    extensions = openclaw.get("extensions") if isinstance(openclaw, dict) else None
    if not isinstance(extensions, list) or not extensions or not all(isinstance(item, str) for item in extensions):
        raise ContractError("clawhub_native_manifest_invalid", "package.json")
    for item in extensions:
        normalized = item[2:] if item.startswith("./") else item
        relative = _relative(normalized, "package.json.openclaw.extensions")
        extension = (source_root / relative).resolve()
        if not extension.is_relative_to(source_root.resolve()) or not extension.is_file():
            raise ContractError("clawhub_native_manifest_invalid", relative)
