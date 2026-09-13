"""Resolve shared dependency caches and isolated plugin data roots."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class RuntimePaths:
    shared_root: Path
    runtime_dir: Path
    model_dir: Path
    plugin_root: Path
    indexes_dir: Path
    source_assets_dir: Path
    authoring_dir: Path
    downloads_dir: Path


def resolve_runtime_paths(
    plugin_id: str,
    runtime_lock_digest: str,
    model_digest: str,
    data_root: Path,
) -> RuntimePaths:
    if not _ID.fullmatch(plugin_id):
        raise ValueError("invalid_plugin_id")
    if not _DIGEST.fullmatch(runtime_lock_digest):
        raise ValueError("invalid_runtime_lock_digest")
    if not _DIGEST.fullmatch(model_digest):
        raise ValueError("invalid_model_digest")
    root = Path(data_root).resolve()
    shared = root / "shared-rag"
    plugin = root / "plugins" / plugin_id
    return RuntimePaths(
        shared_root=shared,
        runtime_dir=shared / "runtimes" / runtime_lock_digest,
        model_dir=shared / "models" / model_digest,
        plugin_root=plugin,
        indexes_dir=plugin / "indexes",
        source_assets_dir=plugin / "source-assets",
        authoring_dir=plugin / "authoring-data",
        downloads_dir=plugin / "downloads",
    )
