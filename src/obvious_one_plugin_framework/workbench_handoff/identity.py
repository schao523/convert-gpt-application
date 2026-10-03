"""Baseline plugin identity for Workbench update handoffs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from typing import Any

from ..plugin_authoring import (
    PluginAuthoringError,
    extract_archive,
    inventory_archive,
    locate_plugin_archive_root,
)


@dataclass(frozen=True)
class BaselineIdentity:
    plugin_id: str
    version: str
    archive_sha256: str
    envelope_profile: str


def _read_manifest(root: Path) -> dict[str, Any]:
    path = root / "plugin.json"
    if not path.is_file():
        path = root / ".codex-plugin" / "plugin.json"
    try:
        value = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PluginAuthoringError("baseline_manifest_invalid") from error
    if not isinstance(value, dict):
        raise PluginAuthoringError("baseline_manifest_invalid")
    return value


def baseline_identity_from_archive(path: Path) -> BaselineIdentity:
    """Read logical identity while retaining the exact supplied archive digest."""
    archive = Path(path)
    inventory = inventory_archive(archive)
    with tempfile.TemporaryDirectory(prefix="workbench-baseline-") as name:
        extracted = Path(name)
        extract_archive(archive, extracted)
        located = locate_plugin_archive_root(extracted)
        manifest = _read_manifest(located.path)
    plugin_id = manifest.get("name")
    version = manifest.get("version")
    if not isinstance(plugin_id, str) or not plugin_id or not isinstance(version, str) or not version:
        raise PluginAuthoringError("baseline_identity_invalid")
    return BaselineIdentity(plugin_id, version, inventory.archive_sha256, located.profile)


def validate_update_baseline(
    handoff: dict[str, Any], baseline: BaselineIdentity | None
) -> tuple[str, ...]:
    """Compare the declared update baseline with the separately supplied archive."""
    declared = handoff.get("baseline")
    if not isinstance(declared, dict) or baseline is None:
        return ("baseline.required_for_update",)
    diagnostics: list[str] = []
    if declared.get("plugin_id") != baseline.plugin_id or declared.get("version") != baseline.version:
        diagnostics.append("baseline.identity_mismatch")
    if declared.get("archive_sha256") != baseline.archive_sha256:
        diagnostics.append("baseline.archive_sha256_mismatch")
    return tuple(sorted(diagnostics))
