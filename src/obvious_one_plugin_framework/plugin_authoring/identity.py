"""Portable filesystem-tree identities and deterministic ZIP output."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import zipfile

from .archive import PluginAuthoringError, _CHUNK_SIZE, _is_link_or_reparse


@dataclass(frozen=True)
class TreeMember:
    path: str
    size: int
    sha256: str


def _stream_hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        while chunk := source.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def tree_manifest(root: Path) -> tuple[TreeMember, ...]:
    tree = Path(root)
    if not tree.is_dir() or _is_link_or_reparse(tree):
        raise PluginAuthoringError("tree_missing")
    members: list[TreeMember] = []
    seen: dict[str, str] = {}
    for directory, names, files in os.walk(tree, topdown=True, followlinks=False):
        directory_path = Path(directory)
        for name in sorted(names):
            child = directory_path / name
            if _is_link_or_reparse(child):
                raise PluginAuthoringError("tree_link_member", child.relative_to(tree).as_posix())
        for name in sorted(files):
            child = directory_path / name
            relative = child.relative_to(tree).as_posix()
            if _is_link_or_reparse(child) or not child.is_file():
                raise PluginAuthoringError("tree_link_member", relative)
            folded = relative.casefold()
            if folded in seen:
                raise PluginAuthoringError("tree_casefold_collision", relative)
            seen[folded] = relative
            members.append(TreeMember(relative, child.stat().st_size, _stream_hash(child)))
    return tuple(sorted(members, key=lambda member: member.path))


def tree_sha256(root: Path) -> str:
    payload = [asdict(member) for member in tree_manifest(root)]
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    return sha256(encoded).hexdigest()


def write_deterministic_zip(root: Path, destination: Path) -> str:
    tree = Path(root).absolute()
    output = Path(destination).absolute()
    try:
        output.relative_to(tree)
    except ValueError:
        pass
    else:
        raise PluginAuthoringError("zip_destination_inside_tree")
    manifest = tree_manifest(tree)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
        temporary_path = Path(temporary_name)
        with zipfile.ZipFile(temporary_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for member in manifest:
                info = zipfile.ZipInfo(member.path, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                with (tree / Path(member.path)).open("rb") as source, archive.open(info, "w") as target:
                    shutil.copyfileobj(source, target, length=_CHUNK_SIZE)
        digest = _stream_hash(temporary_path)
        os.replace(temporary_path, output)
        temporary_name = None
        return digest
    except OSError as exc:
        raise PluginAuthoringError("zip_write_failed") from exc
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
