"""Transactional optional-RAG setup used by generated plugin packages."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import uuid

from .cache import ensure_cached_object
from .paths import RuntimePaths, resolve_runtime_paths
from .remote_assets import (
    RemoteAssetGroup,
    RemoteMemberRecord,
    SetupError,
    download_verified,
    extract_verified,
    verify_file,
)
from .status import RAG_READY, RuntimeStatus


@dataclass(frozen=True)
class BootstrapConfig:
    plugin_id: str
    app_id: str
    namespace: str
    data_root: Path
    runtime_lock_digest: str
    model_digest: str
    asset_groups: tuple[RemoteAssetGroup, ...]
    required_free_bytes: int = 6_000_000_000


def _remove_tree(path: Path) -> None:
    if not path.exists():
        return
    def retry(function, value, _error):
        os.chmod(value, stat.S_IWRITE)
        function(value)
    shutil.rmtree(path, onexc=retry)


def _missing_populator(_stage: Path) -> None:
    raise SetupError("dependency_installer_required")


def _missing_verifier(_path: Path) -> None:
    raise SetupError("dependency_verifier_required")


def _default_fetch(group: RemoteAssetGroup, destination: Path) -> Path:
    return download_verified(group.url, destination, group.size, group.sha256)


def _validate_subdir(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or any(part in {"", "."} for part in path.parts):
        raise SetupError("asset_path_escape", value)
    return path.as_posix()


def _activate_assets(stage: Path, paths: RuntimePaths, subdirs: tuple[str, ...]) -> None:
    backups: list[tuple[Path, Path]] = []
    activated: list[Path] = []
    try:
        for subdir in subdirs:
            source = stage / subdir
            target = paths.plugin_root / subdir
            backup = paths.plugin_root / f".{subdir}.previous"
            _remove_tree(backup)
            if target.exists():
                os.replace(target, backup)
                backups.append((target, backup))
            os.replace(source, target)
            activated.append(target)
    except Exception:
        for target in reversed(activated):
            _remove_tree(target)
        for target, backup in reversed(backups):
            if backup.exists():
                os.replace(backup, target)
        raise
    for _target, backup in backups:
        _remove_tree(backup)


def setup_rag(
    config: BootstrapConfig,
    accept_downloads: bool,
    repair: bool = False,
    *,
    runtime_populate: Callable[[Path], None] = _missing_populator,
    runtime_verify: Callable[[Path], None] = _missing_verifier,
    model_populate: Callable[[Path], None] = _missing_populator,
    model_verify: Callable[[Path], None] = _missing_verifier,
    asset_fetch: Callable[[RemoteAssetGroup, Path], Path] = _default_fetch,
    smoke_test: Callable[[Path], None] = lambda _path: None,
) -> RuntimeStatus:
    del repair
    if not accept_downloads:
        raise SetupError("downloads_not_accepted")
    if not config.namespace.startswith(config.app_id + ":"):
        raise SetupError("namespace_owner_mismatch")
    paths = resolve_runtime_paths(
        config.plugin_id,
        config.runtime_lock_digest,
        config.model_digest,
        config.data_root,
    )
    paths.plugin_root.parent.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(paths.plugin_root.parent).free
    if free < config.required_free_bytes:
        raise SetupError("insufficient_disk_space", str(free))
    runtime_dir = ensure_cached_object(
        paths.runtime_dir, config.runtime_lock_digest, runtime_populate, runtime_verify
    )
    model_dir = ensure_cached_object(
        paths.model_dir, config.model_digest, model_populate, model_verify
    )
    paths.plugin_root.mkdir(parents=True, exist_ok=True)
    paths.downloads_dir.mkdir(parents=True, exist_ok=True)
    stage = paths.plugin_root / f".setup-{uuid.uuid4().hex}"
    stage.mkdir()
    try:
        subdirs: list[str] = []
        for group in config.asset_groups:
            subdir = _validate_subdir(group.install_subdir)
            if subdir in subdirs:
                raise SetupError("duplicate_asset_destination", subdir)
            subdirs.append(subdir)
            archive = paths.downloads_dir / f"{group.name}.zip"
            fetched = asset_fetch(group, archive)
            verify_file(fetched, group.size, group.sha256)
            expected = {member.path: member for member in group.members}
            extract_verified(fetched, stage / subdir, expected)
        try:
            smoke_test(stage)
        except Exception as exc:
            raise SetupError("smoke_test_failed", str(exc)) from exc
        _activate_assets(stage, paths, tuple(subdirs))
        payload = {
            "schema_version": 2,
            "plugin_id": config.plugin_id,
            "app_id": config.app_id,
            "namespace": config.namespace,
            "runtime_lock_digest": config.runtime_lock_digest,
            "runtime_dir": str(runtime_dir),
            "model_digest": config.model_digest,
            "model_dir": str(model_dir),
            "index_dir": str(paths.indexes_dir),
            "source_assets_dir": str(paths.source_assets_dir),
            "asset_groups": [asdict(group) for group in config.asset_groups],
        }
        temporary = paths.plugin_root / ".config.json.tmp"
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        config_path = paths.plugin_root / "config.json"
        os.replace(temporary, config_path)
        return RuntimeStatus(
            RAG_READY,
            {"runtime": "ready", "model": "ready", "assets": "ready"},
            config_path,
        )
    finally:
        _remove_tree(stage)


__all__ = [
    "BootstrapConfig",
    "RemoteAssetGroup",
    "RemoteMemberRecord",
    "RuntimeStatus",
    "SetupError",
    "setup_rag",
]
