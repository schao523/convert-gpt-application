"""Safe, portable ZIP inventory and extraction primitives."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import unicodedata
import zipfile


_SUPPORTED_COMPRESSION = frozenset({zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED})
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")
_CHUNK_SIZE = 1024 * 1024
_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


class PluginAuthoringError(ValueError):
    """A stable plugin-authoring failure with path-independent identity."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(code if not detail else f"{code}: {detail}")


@dataclass(frozen=True)
class ArchiveLimits:
    max_members: int = 4096
    max_member_bytes: int = 64 * 1024 * 1024
    max_total_bytes: int = 256 * 1024 * 1024
    max_compression_ratio: int = 1000

    def __post_init__(self) -> None:
        values = (
            self.max_members,
            self.max_member_bytes,
            self.max_total_bytes,
            self.max_compression_ratio,
        )
        if any(value <= 0 for value in values):
            raise ValueError("invalid_archive_limits")


@dataclass(frozen=True)
class ArchiveMember:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ArchiveInventory:
    archive_sha256: str
    members: tuple[ArchiveMember, ...]
    total_bytes: int


@dataclass(frozen=True)
class LocatedPluginRoot:
    path: Path
    profile: str


def _has_plugin_manifest(root: Path) -> bool:
    return (root / "plugin.json").is_file() or (root / ".codex-plugin" / "plugin.json").is_file()


def locate_plugin_archive_root(extracted_root: Path) -> LocatedPluginRoot:
    """Locate one unambiguous logical plugin root after safe extraction."""
    root = Path(extracted_root)
    if not root.is_dir() or _is_link_or_reparse(root):
        raise PluginAuthoringError("plugin_archive_root_missing")
    flat = _has_plugin_manifest(root)
    children = sorted((item for item in root.iterdir() if item.is_dir()), key=lambda item: item.name)
    wrapped = [
        item for item in children
        if item.name != ".codex-plugin" and _has_plugin_manifest(item)
    ]
    if flat:
        if wrapped:
            raise PluginAuthoringError("plugin_archive_root_ambiguous")
        return LocatedPluginRoot(root, "LEGACY_FLAT")
    top_level = list(root.iterdir())
    if len(top_level) == 1 and len(wrapped) == 1 and top_level[0] == wrapped[0]:
        return LocatedPluginRoot(wrapped[0], "PORTABLE_SINGLE_DIRECTORY")
    if len(wrapped) > 1 or top_level:
        raise PluginAuthoringError("plugin_archive_root_ambiguous")
    raise PluginAuthoringError("plugin_archive_root_missing")


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        while chunk := source.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _normal_member_name(raw_name: str) -> str:
    if not raw_name or "\x00" in raw_name:
        raise PluginAuthoringError("archive_path_escape")
    name = raw_name.replace("\\", "/")
    if name.startswith(("/", "//")) or _WINDOWS_DRIVE.match(name):
        raise PluginAuthoringError("archive_path_escape", raw_name)
    trimmed = name[:-1] if name.endswith("/") else name
    path = PurePosixPath(trimmed)
    if not trimmed or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise PluginAuthoringError("archive_path_escape", raw_name)
    if any(":" in part for part in path.parts):
        raise PluginAuthoringError("archive_path_escape", raw_name)
    return path.as_posix()


def _portable_parts(name: str) -> tuple[str, ...]:
    result = []
    for part in PurePosixPath(name).parts:
        normalized = unicodedata.normalize("NFC", part).rstrip(" .")
        if not normalized or normalized.split(".", 1)[0].upper() in _WINDOWS_RESERVED:
            raise PluginAuthoringError("archive_portable_name_invalid", name)
        result.append(normalized.casefold())
    return tuple(result)


def _is_link(info: zipfile.ZipInfo) -> bool:
    unix_mode = (info.external_attr >> 16) & 0xFFFF
    if info.create_system == 3 and stat.S_IFMT(unix_mode) == stat.S_IFLNK:
        return True
    return bool((info.external_attr & 0xFFFF) & 0x0400)


def _is_link_or_reparse(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or bool(attributes & reparse_flag)


def _validated_infos(
    archive: zipfile.ZipFile,
    limits: ArchiveLimits,
) -> list[tuple[str, zipfile.ZipInfo]]:
    infos = archive.infolist()
    if len(infos) > limits.max_members:
        raise PluginAuthoringError("archive_member_limit")
    normalized: dict[str, tuple[str, zipfile.ZipInfo]] = {}
    portable_names: dict[tuple[str, ...], str] = {}
    portable_files: set[tuple[str, ...]] = set()
    portable_prefixes: dict[tuple[str, ...], tuple[str, ...]] = {}
    file_paths: set[str] = set()
    directory_paths: set[str] = set()
    total = 0
    for info in infos:
        raw_name = info.orig_filename
        name = _normal_member_name(raw_name)
        existing = normalized.get(name)
        if existing is not None:
            code = "archive_alias_collision" if existing[0] != raw_name else "archive_duplicate_member"
            raise PluginAuthoringError(code, name)
        portable = _portable_parts(name)
        raw_parts = PurePosixPath(name).parts
        if portable in portable_names:
            raise PluginAuthoringError("archive_casefold_collision", name)
        for index in range(1, len(portable) + 1):
            logical_prefix = portable[:index]
            raw_prefix = raw_parts[:index]
            prior = portable_prefixes.get(logical_prefix)
            if prior is not None and prior != raw_prefix:
                raise PluginAuthoringError("archive_casefold_collision", name)
            portable_prefixes[logical_prefix] = raw_prefix
        for existing in portable_files:
            if portable[:len(existing)] == existing or (not info.is_dir() and existing[:len(portable)] == portable):
                raise PluginAuthoringError("archive_path_collision", name)
        normalized[name] = (raw_name, info)
        portable_names[portable] = name
        if not info.is_dir():
            portable_files.add(portable)
        if info.flag_bits & 0x1:
            raise PluginAuthoringError("archive_encrypted_member", name)
        if _is_link(info):
            raise PluginAuthoringError("archive_link_member", name)
        if info.compress_type not in _SUPPORTED_COMPRESSION:
            raise PluginAuthoringError("archive_compression_unsupported", name)
        if info.file_size > limits.max_member_bytes:
            raise PluginAuthoringError("archive_member_too_large", name)
        if info.file_size and info.file_size > max(info.compress_size, 1) * limits.max_compression_ratio:
            raise PluginAuthoringError("archive_compression_ratio", name)
        if info.is_dir():
            directory_paths.add(name)
            continue
        file_paths.add(name)
        total += info.file_size
        if total > limits.max_total_bytes:
            raise PluginAuthoringError("archive_expansion_limit")
    for file_path in file_paths:
        parts = PurePosixPath(file_path).parts
        if any("/".join(parts[:index]) in file_paths for index in range(1, len(parts))):
            raise PluginAuthoringError("archive_path_collision", file_path)
        if file_path in directory_paths:
            raise PluginAuthoringError("archive_path_collision", file_path)
    return sorted(
        ((name, value[1]) for name, value in normalized.items() if not value[1].is_dir()),
        key=lambda item: item[0],
    )


def _stream_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo, target=None) -> tuple[str, int]:
    digest = sha256()
    actual_size = 0
    try:
        with archive.open(info, "r") as source:
            while chunk := source.read(_CHUNK_SIZE):
                digest.update(chunk)
                actual_size += len(chunk)
                if target is not None:
                    target.write(chunk)
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise PluginAuthoringError("archive_member_read_failed", info.filename) from exc
    if actual_size != info.file_size:
        raise PluginAuthoringError("archive_member_size_mismatch", info.filename)
    return digest.hexdigest(), actual_size


def inventory_archive(path: Path, limits: ArchiveLimits = ArchiveLimits()) -> ArchiveInventory:
    archive_path = Path(path)
    if not archive_path.is_file() or _is_link_or_reparse(archive_path):
        raise PluginAuthoringError("archive_missing")
    archive_digest = _hash_file(archive_path)
    try:
        archive = zipfile.ZipFile(archive_path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise PluginAuthoringError("archive_invalid") from exc
    with archive:
        infos = _validated_infos(archive, limits)
        members = tuple(
            ArchiveMember(name, info.file_size, _stream_member(archive, info)[0])
            for name, info in infos
        )
    return ArchiveInventory(archive_digest, members, sum(member.size for member in members))


def _check_existing_components(path: Path) -> None:
    absolute = path.absolute()
    parts = absolute.parts
    current = Path(parts[0])
    for part in parts[1:]:
        current /= part
        if current.exists() or _is_link_or_reparse(current):
            if _is_link_or_reparse(current):
                raise PluginAuthoringError("destination_link_component", current.name)


def _replace_directory(stage: Path, destination: Path, backup: Path) -> None:
    moved_existing = False
    try:
        if destination.exists():
            os.replace(destination, backup)
            moved_existing = True
        os.replace(stage, destination)
    except OSError as exc:
        if moved_existing and backup.exists() and not destination.exists():
            os.replace(backup, destination)
        raise PluginAuthoringError("destination_replace_failed") from exc


def extract_archive(
    path: Path,
    destination: Path,
    limits: ArchiveLimits = ArchiveLimits(),
) -> ArchiveInventory:
    inventory = inventory_archive(path, limits)
    destination_path = Path(destination).absolute()
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    _check_existing_components(destination_path)
    try:
        archive = zipfile.ZipFile(Path(path))
    except (OSError, zipfile.BadZipFile) as exc:
        raise PluginAuthoringError("archive_invalid") from exc
    with tempfile.TemporaryDirectory(
        dir=destination_path.parent,
        prefix=f".{destination_path.name}.extract-",
    ) as temporary_name:
        temporary = Path(temporary_name)
        stage = temporary / "payload"
        backup = temporary / "previous"
        stage.mkdir()
        with archive:
            infos = _validated_infos(archive, limits)
            for name, info in infos:
                output = stage.joinpath(*PurePosixPath(name).parts)
                output.parent.mkdir(parents=True, exist_ok=True)
                with output.open("xb") as target:
                    digest, actual_size = _stream_member(archive, info, target)
                expected = next(member for member in inventory.members if member.path == name)
                if digest != expected.sha256 or actual_size != expected.size:
                    raise PluginAuthoringError("archive_changed_during_extract", name)
        _replace_directory(stage, destination_path, backup)
    return inventory
