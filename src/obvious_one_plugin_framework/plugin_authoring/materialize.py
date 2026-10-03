"""Transactional exact-file materialization for approved plugin recipes."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from typing import Any, Iterable, Mapping

from .archive import PluginAuthoringError, _is_link_or_reparse
from .identity import TreeMember, tree_manifest


_RESERVED = frozenset({"PLUGIN-BUILDER-MANIFEST.json", "PLUGIN-BUILDER-CHANGES.json"})
_CLASSIFICATIONS = {
    "inline_text": "generated_text",
    "inline_json": "generated_json",
    "source_path": "approved_source",
}


def _safe_path(value: object, code: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        raise PluginAuthoringError(code)
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts) or ":" in parts[0]:
        raise PluginAuthoringError(code, value)
    path = PurePosixPath(value)
    if path.as_posix() != value:
        raise PluginAuthoringError(code, value)
    return value


def _payload(recipe: Mapping[str, Any], source_root: Path) -> bytes:
    origins = [key for key in _CLASSIFICATIONS if key in recipe]
    if len(origins) != 1:
        raise PluginAuthoringError("materialize_origin_invalid", str(recipe.get("path", "")))
    origin = origins[0]
    if recipe.get("classification") != _CLASSIFICATIONS[origin]:
        raise PluginAuthoringError("materialize_classification_invalid", str(recipe.get("path", "")))
    redistribution = recipe.get("redistribution")
    if (
        not isinstance(redistribution, dict)
        or set(redistribution) != {"state", "evidence"}
        or redistribution.get("state") != "APPROVED"
        or not isinstance(redistribution.get("evidence"), str)
        or not redistribution["evidence"]
    ):
        raise PluginAuthoringError("materialize_redistribution_unapproved", str(recipe.get("path", "")))
    if origin == "inline_text":
        value = recipe[origin]
        if not isinstance(value, str):
            raise PluginAuthoringError("materialize_inline_text_invalid")
        payload = value.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    elif origin == "inline_json":
        try:
            payload = (json.dumps(recipe[origin], ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")
        except (TypeError, ValueError) as error:
            raise PluginAuthoringError("materialize_inline_json_invalid") from error
    else:
        relative = _safe_path(recipe[origin], "materialize_source_escape")
        source = source_root.joinpath(*PurePosixPath(relative).parts)
        try:
            source.relative_to(source_root)
        except ValueError as error:
            raise PluginAuthoringError("materialize_source_escape", relative) from error
        current = source_root
        for part in PurePosixPath(relative).parts:
            current /= part
            if _is_link_or_reparse(current):
                raise PluginAuthoringError("materialize_source_link", relative)
        if not source.is_file():
            raise PluginAuthoringError("materialize_source_missing", relative)
        try:
            payload = source.read_bytes()
        except OSError as error:
            raise PluginAuthoringError("materialize_source_unreadable", relative) from error
    expected = recipe.get("source_sha256")
    if not isinstance(expected, str) or sha256(payload).hexdigest() != expected:
        raise PluginAuthoringError("materialize_source_hash_mismatch", str(recipe.get("path", "")))
    return payload


def _replace(stage: Path, destination: Path, temporary: Path) -> None:
    backup = temporary / "previous"
    moved = False
    try:
        if destination.exists():
            os.replace(destination, backup)
            moved = True
        os.replace(stage, destination)
    except OSError as error:
        if moved and backup.exists() and not destination.exists():
            os.replace(backup, destination)
        raise PluginAuthoringError("materialize_replace_failed") from error


def materialize_files(
    recipes: Iterable[Mapping[str, Any]],
    source_root: Path,
    destination: Path,
) -> tuple[TreeMember, ...]:
    sources = Path(source_root).absolute()
    if not sources.is_dir() or _is_link_or_reparse(sources):
        raise PluginAuthoringError("materialize_source_root_invalid")
    normalized: list[tuple[str, bytes]] = []
    seen: dict[str, str] = {}
    paths: set[str] = set()
    for recipe in recipes:
        if not isinstance(recipe, Mapping):
            raise PluginAuthoringError("materialize_recipe_invalid")
        path = _safe_path(recipe.get("path"), "materialize_path_invalid")
        if path in _RESERVED:
            raise PluginAuthoringError("materialize_reserved_path", path)
        folded = path.casefold()
        if folded in seen:
            raise PluginAuthoringError("materialize_path_collision", path)
        parts = PurePosixPath(path).parts
        if any("/".join(parts[:index]) in paths for index in range(1, len(parts))):
            raise PluginAuthoringError("materialize_path_collision", path)
        seen[folded] = path
        paths.add(path)
        normalized.append((path, _payload(recipe, sources)))
    for path in paths:
        prefix = f"{path}/"
        if any(other.startswith(prefix) for other in paths):
            raise PluginAuthoringError("materialize_path_collision", path)

    output = Path(destination).absolute()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=f".{output.name}.materialize-") as name:
        temporary = Path(name)
        stage = temporary / "candidate"
        stage.mkdir()
        for path, payload in sorted(normalized):
            target = stage.joinpath(*PurePosixPath(path).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        _replace(stage, output, temporary)
    return tree_manifest(output)


def overlay_files(
    baseline: Path,
    recipes: Iterable[Mapping[str, Any]],
    source_root: Path,
    destination: Path,
    *,
    remove: Iterable[str] = (),
) -> tuple[TreeMember, ...]:
    """Copy a validated baseline byte-for-byte, then apply an approved delta."""

    baseline_root = Path(baseline).absolute()
    if not baseline_root.is_dir() or _is_link_or_reparse(baseline_root):
        raise PluginAuthoringError("overlay_baseline_invalid")
    output = Path(destination).absolute()
    output.parent.mkdir(parents=True, exist_ok=True)
    recipe_list = list(recipes)
    removals = sorted({_safe_path(path, "overlay_remove_path_invalid") for path in remove})
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=f".{output.name}.overlay-") as name:
        temporary = Path(name)
        stage = temporary / "candidate"
        shutil.copytree(baseline_root, stage, copy_function=shutil.copy2)
        delta = temporary / "delta"
        materialize_files(recipe_list, Path(source_root), delta)
        for member in tree_manifest(delta):
            source = delta.joinpath(*PurePosixPath(member.path).parts)
            target = stage.joinpath(*PurePosixPath(member.path).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        for path in removals:
            target = stage.joinpath(*PurePosixPath(path).parts)
            if target.is_dir():
                raise PluginAuthoringError("overlay_remove_not_file", path)
            target.unlink(missing_ok=True)
        _replace(stage, output, temporary)
    return tree_manifest(output)
