"""Generate a self-contained marketplace validation registry and workflow."""

from __future__ import annotations

from importlib.resources import files
import json
from pathlib import Path
import re
from typing import Mapping

from .marketplace import MarketplaceError, PreparationCatalog


_PLACEHOLDER = re.compile(r"\{([^{}]+)\}")


def build_validation_registry(
    codex_catalog: Mapping[str, object] | Path,
    openclaw_catalog: Mapping[str, object] | Path,
    preparation_catalog: PreparationCatalog,
) -> dict[str, object]:
    """Cross-check runtime catalogs and build the portable verifier registry."""

    codex = _codex_plugins(_load_mapping(codex_catalog))
    openclaw = _openclaw_plugins(_load_mapping(openclaw_catalog))
    planned = {entry.application.plugin_id: entry for entry in preparation_catalog.applications}
    if set(codex) != set(openclaw) or set(codex) != set(planned):
        raise MarketplaceError("runtime_catalog_mismatch", "plugin identities")

    plugins: list[dict[str, object]] = []
    for plugin_id in sorted(planned):
        entry = planned[plugin_id]
        if codex[plugin_id] != entry.codex_destination:
            raise MarketplaceError("runtime_catalog_mismatch", plugin_id)
        openclaw_path, version = openclaw[plugin_id]
        if openclaw_path != entry.openclaw_destination or version != entry.application.version:
            raise MarketplaceError("runtime_catalog_mismatch", plugin_id)
        commands = []
        for command in entry.application.verification.commands:
            for target in command.marketplace_targets:
                argv = tuple(argument.replace("{application_root}", "{artifact_root}") for argument in command.argv)
                placeholders = {name for argument in argv for name in _PLACEHOLDER.findall(argument)}
                if not placeholders <= {"python", "artifact_root"}:
                    raise MarketplaceError("marketplace_command_placeholder", command.command_id)
                commands.append({
                    "id": f"{command.command_id}-{target}",
                    "artifact": target,
                    "argv": list(argv),
                })
        publication = entry.contract.publication
        if publication is None or not publication.clawhub.enabled:
            clawhub = {"state": "NOT APPLICABLE"}
        elif publication.clawhub.native_manifest is None:
            raise MarketplaceError("clawhub_native_manifest_required", plugin_id)
        else:
            clawhub = {
                "state": "CONFIGURED",
                "family": publication.clawhub.family,
                "native_manifest": publication.clawhub.native_manifest,
            }
        plugins.append({
            "plugin_id": plugin_id,
            "version": entry.application.version,
            "mode": entry.mode,
            "codex_path": entry.codex_destination,
            "openclaw_path": entry.openclaw_destination,
            "commands": commands,
            "clawhub": clawhub,
        })
    return {
        "schema_version": 1,
        "marketplace_id": preparation_catalog.marketplace_id,
        "plugins": plugins,
    }


def render_marketplace_verifier() -> str:
    """Load the standalone verifier from installed package resources."""

    resource = files("obvious_one_plugin_framework").joinpath(
        "templates/marketplace/verify_marketplace.py.template"
    )
    return resource.read_text(encoding="utf-8")


def render_validation_workflow() -> str:
    """Render plugin-neutral cross-platform GitHub Actions validation."""

    return _WORKFLOW


def _load_mapping(value: Mapping[str, object] | Path) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    try:
        loaded = json.loads(Path(value).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MarketplaceError("runtime_catalog_invalid") from exc
    if not isinstance(loaded, dict):
        raise MarketplaceError("runtime_catalog_invalid")
    return loaded


def _codex_plugins(catalog: Mapping[str, object]) -> dict[str, str]:
    records = catalog.get("plugins")
    if not isinstance(records, list):
        raise MarketplaceError("runtime_catalog_mismatch", "codex plugins")
    result: dict[str, str] = {}
    for item in records:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise MarketplaceError("runtime_catalog_mismatch", "codex entry")
        source = item.get("source")
        if not isinstance(source, dict) or not isinstance(source.get("path"), str):
            raise MarketplaceError("runtime_catalog_mismatch", str(item.get("name")))
        plugin_id = item["name"]
        if plugin_id in result:
            raise MarketplaceError("runtime_catalog_mismatch", "duplicate codex entry")
        result[plugin_id] = _catalog_path(source["path"])
    return result


def _openclaw_plugins(catalog: Mapping[str, object]) -> dict[str, tuple[str, str]]:
    records = catalog.get("plugins")
    if not isinstance(records, list):
        raise MarketplaceError("runtime_catalog_mismatch", "openclaw plugins")
    result: dict[str, tuple[str, str]] = {}
    for item in records:
        if not isinstance(item, dict) or not all(isinstance(item.get(key), str) for key in ("name", "version", "source")):
            raise MarketplaceError("runtime_catalog_mismatch", "openclaw entry")
        plugin_id = item["name"]
        if plugin_id in result:
            raise MarketplaceError("runtime_catalog_mismatch", "duplicate openclaw entry")
        result[plugin_id] = (_catalog_path(item["source"]), item["version"])
    return result


def _catalog_path(value: str) -> str:
    return value[2:] if value.startswith("./") else value


_WORKFLOW = """name: Validate marketplace

on:
  push:
  pull_request:
  workflow_dispatch:

jobs:
  matrix:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.registry.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
      - id: registry
        shell: python
        run: |
          import json, os
          data = json.load(open('.obvious-one-validation.json', encoding='utf-8'))
          matrix = json.dumps({'plugin': [item['plugin_id'] for item in data['plugins']]}, separators=(',', ':'))
          with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
              stream.write(f'matrix={matrix}\\n')
  validate:
    needs: matrix
    strategy:
      fail-fast: false
      matrix:
        plugin: ${{ fromJson(needs.matrix.outputs.matrix).plugin }}
        os: [windows-latest, ubuntu-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python -B tools/verify_marketplace.py --registry .obvious-one-validation.json --plugin "${{ matrix.plugin }}" --json
  aggregate:
    if: always()
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - run: test "${{ needs.validate.result }}" = success
"""
