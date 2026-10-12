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
    runtime_plugins = {"codex": codex, "openclaw": openclaw}
    for target_name, actual in runtime_plugins.items():
        expected = {
            plugin_id
            for plugin_id, entry in planned.items()
            if entry.target(target_name).mode != "not_applicable"
        }
        missing = sorted(expected - set(actual))
        if missing:
            raise MarketplaceError(
                "runtime_catalog_missing_entry",
                f"{target_name}:{missing[0]}",
            )
        unexpected = sorted(set(actual) - expected)
        if unexpected:
            raise MarketplaceError(
                "runtime_catalog_unexpected_entry",
                f"{target_name}:{unexpected[0]}",
            )

    plugins: list[dict[str, object]] = []
    for plugin_id in sorted(planned):
        entry = planned[plugin_id]
        targets: dict[str, dict[str, object]] = {}
        for target_name in ("codex", "openclaw"):
            target = entry.target(target_name)
            if target.mode == "not_applicable":
                targets[target_name] = {"state": "NOT APPLICABLE"}
                continue
            if target.destination is None:
                raise MarketplaceError("runtime_catalog_target_mismatch", f"{plugin_id}:{target_name}")
            if target_name == "codex":
                if codex[plugin_id] != target.destination:
                    raise MarketplaceError("runtime_catalog_target_mismatch", f"{plugin_id}:codex")
            else:
                openclaw_path, version = openclaw[plugin_id]
                if openclaw_path != target.destination or version != entry.application.version:
                    raise MarketplaceError("runtime_catalog_target_mismatch", f"{plugin_id}:openclaw")
            targets[target_name] = {
                "state": "STATICALLY VERIFIED",
                "mode": target.mode,
                "path": target.destination,
            }
        commands = []
        for command in entry.application.verification.commands:
            for target in command.marketplace_targets:
                if entry.target(target).mode == "not_applicable":
                    raise MarketplaceError(
                        "marketplace_command_target_not_applicable",
                        f"{plugin_id}:{command.command_id}:{target}",
                    )
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
            "targets": targets,
            "commands": commands,
            "clawhub": clawhub,
        })
    return {
        "schema_version": 2,
        "marketplace_id": preparation_catalog.marketplace_id,
        "plugins": plugins,
    }


def render_marketplace_verifier() -> str:
    """Load the standalone verifier from installed package resources."""

    resource = files("obvious_one_plugin_framework").joinpath(
        "templates/marketplace/verify_marketplace.py.template"
    )
    return resource.read_text(encoding="utf-8")


def render_marketplace_selector() -> str:
    """Load the standalone affected-plugin selector from package resources."""

    resource = files("obvious_one_plugin_framework").joinpath(
        "templates/marketplace/select_marketplace_plugins.py.template"
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
        raise MarketplaceError("runtime_catalog_target_mismatch", "codex plugins")
    result: dict[str, str] = {}
    for item in records:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise MarketplaceError("runtime_catalog_target_mismatch", "codex entry")
        source = item.get("source")
        if not isinstance(source, dict) or not isinstance(source.get("path"), str):
            raise MarketplaceError("runtime_catalog_target_mismatch", str(item.get("name")))
        plugin_id = item["name"]
        if plugin_id in result:
            raise MarketplaceError("runtime_catalog_target_mismatch", "duplicate codex entry")
        result[plugin_id] = _catalog_path(source["path"])
    return result


def _openclaw_plugins(catalog: Mapping[str, object]) -> dict[str, tuple[str, str]]:
    records = catalog.get("plugins")
    if not isinstance(records, list):
        raise MarketplaceError("runtime_catalog_target_mismatch", "openclaw plugins")
    result: dict[str, tuple[str, str]] = {}
    for item in records:
        if not isinstance(item, dict) or not all(isinstance(item.get(key), str) for key in ("name", "version", "source")):
            raise MarketplaceError("runtime_catalog_target_mismatch", "openclaw entry")
        plugin_id = item["name"]
        if plugin_id in result:
            raise MarketplaceError("runtime_catalog_target_mismatch", "duplicate openclaw entry")
        result[plugin_id] = (_catalog_path(item["source"]), item["version"])
    return result


def _catalog_path(value: str) -> str:
    return value[2:] if value.startswith("./") else value


_LEGACY_WORKFLOW_V1 = """name: Validate marketplace

on:
  pull_request:
  push:
    branches: [main]
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


_WORKFLOW = """name: Validate marketplace

on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  matrix:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.selection.outputs.matrix }}
      selection_mode: ${{ steps.selection.outputs.selection_mode }}
      selection_status: ${{ steps.selection.outputs.selection_status }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - id: selection
        shell: python
        env:
          EVENT_NAME: ${{ github.event_name }}
          PR_BASE_SHA: ${{ github.event.pull_request.base.sha }}
          PR_HEAD_SHA: ${{ github.event.pull_request.head.sha }}
          PUSH_BEFORE_SHA: ${{ github.event.before }}
          PUSH_HEAD_SHA: ${{ github.sha }}
        run: |
          import json, os, subprocess, sys
          command = [
              sys.executable, '-B', 'tools/select_marketplace_plugins.py',
              '--registry', '.obvious-one-validation.json',
          ]
          event = os.environ.get('EVENT_NAME', '')
          if event == 'workflow_dispatch':
              command.extend(['--all', 'workflow_dispatch'])
          else:
              if event == 'pull_request':
                  base = os.environ.get('PR_BASE_SHA', '')
                  head = os.environ.get('PR_HEAD_SHA', '')
              else:
                  base = os.environ.get('PUSH_BEFORE_SHA', '')
                  head = os.environ.get('PUSH_HEAD_SHA', '')
              command.extend(['--base', base, '--head', head])
          completed = subprocess.run(
              command,
              stdin=subprocess.DEVNULL,
              stdout=subprocess.PIPE,
              stderr=subprocess.PIPE,
              text=True,
              encoding='utf-8',
              errors='replace',
              check=False,
          )
          matrix = {'plugin': []}
          mode = 'INVALID'
          status = 'FAIL'
          try:
              payload = json.loads(completed.stdout)
              evidence = payload.get('evidence', {})
              candidate = evidence.get('matrix')
              selected = candidate.get('plugin') if isinstance(candidate, dict) else None
              candidate_mode = evidence.get('selection_mode')
              valid_plugins = (
                  isinstance(selected, list)
                  and selected == sorted(set(selected))
                  and all(isinstance(item, str) and item for item in selected)
              )
              if (
                  payload.get('result_schema_version') == 1
                  and payload.get('operation') == 'select-marketplace-plugins'
                  and payload.get('status') in {'PASS', 'FAIL'}
                  and candidate_mode in {'AFFECTED', 'ALL', 'NONE'}
                  and valid_plugins
              ):
                  matrix = {'plugin': selected}
                  mode = candidate_mode
                  status = payload['status']
          except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
              pass
          with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
              stream.write('matrix=' + json.dumps(matrix, separators=(',', ':')) + '\\n')
              stream.write(f'selection_mode={mode}\\n')
              stream.write(f'selection_status={status}\\n')
          if completed.returncode != 0 or status != 'PASS':
              raise SystemExit(1)
  validate:
    needs: matrix
    if: needs.matrix.outputs.selection_status == 'PASS' && needs.matrix.outputs.selection_mode != 'NONE'
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
    needs: [matrix, validate]
    runs-on: ubuntu-latest
    steps:
      - shell: python
        env:
          MATRIX_RESULT: ${{ needs.matrix.result }}
          VALIDATION_RESULT: ${{ needs.validate.result }}
          SELECTION_MODE: ${{ needs.matrix.outputs.selection_mode }}
          SELECTION_STATUS: ${{ needs.matrix.outputs.selection_status }}
        run: |
          import os, sys
          matrix = os.environ.get('MATRIX_RESULT')
          validation = os.environ.get('VALIDATION_RESULT')
          mode = os.environ.get('SELECTION_MODE')
          status = os.environ.get('SELECTION_STATUS')
          accepted = (
              matrix == 'success'
              and status == 'PASS'
              and (
                  (mode == 'NONE' and validation == 'skipped')
                  or (mode != 'NONE' and validation == 'success')
              )
          )
          sys.exit(0 if accepted else 1)
"""
