"""Portable Agent Plugins manifests and legacy Codex compatibility overlays."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from .archive import PluginAuthoringError


PORTABLE_PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"

_COMMON_KEYS = (
    "author",
    "description",
    "homepage",
    "keywords",
    "license",
    "name",
    "repository",
    "version",
)
_INTERFACE_KEYS = (
    "capabilities",
    "category",
    "defaultPrompt",
    "developerName",
    "displayName",
    "iconLarge",
    "iconSmall",
    "longDescription",
    "shortDescription",
)
_OVERLAY_KEYS = set(_COMMON_KEYS) | {"interface", "skills"}


@dataclass(frozen=True)
class ManifestPairIdentity:
    portable_sha256: str
    overlay_sha256: str


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        return (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")
    except (TypeError, ValueError) as error:
        raise PluginAuthoringError("manifest_json_invalid") from error


def _mapping(value: object, code: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise PluginAuthoringError(code)
    return dict(value)


def _portable_interface(payload: Mapping[str, Any]) -> dict[str, Any]:
    extensions = _mapping(payload.get("extensions"), "portable_extensions_invalid")
    openai = _mapping(extensions.get("com.openai"), "portable_openai_extension_invalid")
    return _mapping(openai.get("interface"), "portable_interface_invalid")


def portable_manifest_from_legacy(payload: Mapping[str, Any]) -> dict[str, Any]:
    legacy = _mapping(payload, "legacy_manifest_invalid")
    interface = _mapping(legacy.get("interface"), "legacy_interface_invalid")
    for unsupported in ("apps", "mcpServers"):
        value = legacy.get(unsupported)
        if value not in (None, {}, []):
            raise PluginAuthoringError("legacy_manifest_dependency_requires_adapter", unsupported)
    portable: dict[str, Any] = {"$schema": PORTABLE_PLUGIN_SCHEMA}
    for key in _COMMON_KEYS:
        if key in legacy:
            portable[key] = deepcopy(legacy[key])
    portable["extensions"] = {"com.openai": {"interface": deepcopy(interface)}}
    return portable


def legacy_overlay_from_portable(payload: Mapping[str, Any]) -> dict[str, Any]:
    portable = _mapping(payload, "portable_manifest_invalid")
    interface = _portable_interface(portable)
    overlay: dict[str, Any] = {}
    for key in _COMMON_KEYS:
        if key in portable:
            overlay[key] = deepcopy(portable[key])
    overlay["skills"] = "./skills/"
    overlay["interface"] = deepcopy(interface)
    return overlay


def manifest_pair_mismatches(
    portable: Mapping[str, Any],
    overlay: Mapping[str, Any],
) -> tuple[str, ...]:
    mismatches: set[str] = set()
    for key in set(overlay) - _OVERLAY_KEYS:
        mismatches.add(f"overlay.{key}")
    try:
        interface = _portable_interface(portable)
    except PluginAuthoringError:
        return ("portable.interface",)
    legacy_interface = overlay.get("interface")
    if not isinstance(legacy_interface, Mapping):
        return ("overlay.interface",)
    for key in set(legacy_interface) - set(_INTERFACE_KEYS):
        mismatches.add(f"overlay.interface.{key}")
    for key in ("name", "version", "description", "author"):
        if portable.get(key) != overlay.get(key):
            mismatches.add(key)
    if overlay.get("skills") != "./skills/":
        mismatches.add("skills")
    for key in _INTERFACE_KEYS:
        if interface.get(key) != legacy_interface.get(key):
            mismatches.add(f"interface.{key}")
    return tuple(sorted(mismatches))


def _read_json(path: Path, code: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PluginAuthoringError(code, path.name) from error
    return _mapping(payload, code)


def _write_transactionally(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
            temporary_name = output.name
        os.replace(temporary_name, path)
        temporary_name = None
    except OSError as error:
        raise PluginAuthoringError("manifest_write_failed", path.name) from error
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def materialize_manifest_pair(root: Path) -> ManifestPairIdentity:
    plugin_root = Path(root)
    portable_path = plugin_root / "plugin.json"
    overlay_path = plugin_root / ".codex-plugin" / "plugin.json"
    portable_exists = portable_path.is_file()
    overlay_exists = overlay_path.is_file()
    if not portable_exists and not overlay_exists:
        raise PluginAuthoringError("manifest_pair_missing")

    portable = _read_json(portable_path, "portable_manifest_invalid") if portable_exists else None
    overlay = _read_json(overlay_path, "compatibility_overlay_invalid") if overlay_exists else None
    if portable is None:
        assert overlay is not None
        portable = portable_manifest_from_legacy(overlay)
        _write_transactionally(portable_path, _canonical_bytes(portable))
    elif overlay is None:
        overlay = legacy_overlay_from_portable(portable)
        _write_transactionally(overlay_path, _canonical_bytes(overlay))
    else:
        mismatches = manifest_pair_mismatches(portable, overlay)
        if mismatches:
            raise PluginAuthoringError("manifest_pair_mismatch", ",".join(mismatches))

    portable_bytes = portable_path.read_bytes()
    overlay_bytes = overlay_path.read_bytes()
    return ManifestPairIdentity(
        portable_sha256=sha256(portable_bytes).hexdigest(),
        overlay_sha256=sha256(overlay_bytes).hexdigest(),
    )
