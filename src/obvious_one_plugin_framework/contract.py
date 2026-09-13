"""Strict declarative contracts for generated OpenClaw plugin editions."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping


_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_ROOT_KEYS = {
    "schema_version", "plugin_id", "package_name", "family", "version",
    "source_root", "include_files", "include_prefixes", "exclude_paths",
    "max_total_bytes", "release_repository", "release_tag_template",
    "readme_overlay", "audit_hook", "rag",
}
_RAG_KEYS = {
    "app_id", "namespace", "runtime_lock", "runtime_lock_digest",
    "model_manifest", "model_digest", "index_manifest", "asset_groups",
}
_ASSET_KEYS = {"name", "archive_name", "source_paths", "install_subdir"}


class ContractError(ValueError):
    """Raised when a distribution contract violates a stable rule."""

    def __init__(self, code: str, detail: str = "") -> None:
        message = code if not detail else f"{code}: {detail}"
        super().__init__(message)
        self.code = code


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
    rag: RagProfile
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
    _only_keys(raw, _ROOT_KEYS, "contract")
    rag_raw = _mapping(raw["rag"], "rag")
    _only_keys(rag_raw, _RAG_KEYS, "rag")
    groups_raw = rag_raw["asset_groups"]
    if not isinstance(groups_raw, list) or not groups_raw:
        raise ContractError("invalid_asset_groups", "at least one group is required")
    groups: list[AssetGroup] = []
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
    family = _text(raw["family"], "family")
    if family != "bundle-plugin":
        raise ContractError("invalid_family", family)
    include_files = _path_list(raw["include_files"], "include_files")
    if "openclaw.plugin.json" in include_files:
        raise ContractError("native_marker_forbidden", "openclaw.plugin.json")
    max_total_bytes = raw["max_total_bytes"]
    if not isinstance(max_total_bytes, int) or max_total_bytes <= 0:
        raise ContractError("invalid_size_limit", "max_total_bytes")
    contract = DistributionContract(
        schema_version=int(raw["schema_version"]),
        plugin_id=_text(raw["plugin_id"], "plugin_id"),
        package_name=_text(raw["package_name"], "package_name"),
        family=family,
        version=_text(raw["version"], "version"),
        source_root=_source_root(raw["source_root"], contract_path),
        include_files=include_files,
        include_prefixes=_path_list(raw["include_prefixes"], "include_prefixes"),
        exclude_paths=_path_list(raw["exclude_paths"], "exclude_paths"),
        max_total_bytes=max_total_bytes,
        release_repository=_text(raw["release_repository"], "release_repository"),
        release_tag_template=_text(raw["release_tag_template"], "release_tag_template"),
        readme_overlay=_optional_text(raw["readme_overlay"], "readme_overlay"),
        audit_hook=_optional_text(raw["audit_hook"], "audit_hook"),
        rag=RagProfile(
            app_id=app_id,
            namespace=namespace,
            runtime_lock=_relative(rag_raw["runtime_lock"], "rag.runtime_lock"),
            runtime_lock_digest=_digest(rag_raw["runtime_lock_digest"], "rag.runtime_lock_digest"),
            model_manifest=_relative(rag_raw["model_manifest"], "rag.model_manifest"),
            model_digest=_digest(rag_raw["model_digest"], "rag.model_digest"),
            index_manifest=_relative(rag_raw["index_manifest"], "rag.index_manifest"),
            asset_groups=tuple(groups),
        ),
        contract_path=contract_path,
    )
    validate_contract(contract, contract.source_root)
    return contract


def validate_contract(contract: DistributionContract, source_root: Path) -> None:
    if contract.schema_version != 1:
        raise ContractError("unsupported_schema", str(contract.schema_version))
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
