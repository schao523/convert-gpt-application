from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping

from obvious_one_plugin_framework import plugin_authoring


PORTABLE_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("ascii")


@dataclass(frozen=True)
class PluginBuilderFixture:
    root: Path
    candidate: Path
    archive: Path
    metadata: Path
    metadata_payload: Mapping[str, object]


def _default_files() -> dict[str, bytes]:
    interface = {
        "displayName": "Sample Plugin",
        "shortDescription": "Portable sample",
        "longDescription": "A portable sample plugin for onboarding tests.",
        "developerName": "Example Developer",
        "category": "Productivity",
        "capabilities": ["Interactive", "Read"],
        "defaultPrompt": "Help me use this plugin.",
    }
    portable = {
        "$schema": PORTABLE_SCHEMA,
        "name": "sample-plugin",
        "version": "1.2.3",
        "description": "A portable sample plugin.",
        "author": {"name": "Example Developer"},
        "extensions": {"com.openai": {"interface": interface}},
    }
    compatibility = {
        "name": "sample-plugin",
        "version": "1.2.3",
        "description": "A portable sample plugin.",
        "author": {"name": "Example Developer"},
        "skills": "./skills/",
        "interface": interface,
    }
    return {
        "plugin.json": canonical_bytes(portable),
        ".codex-plugin/plugin.json": canonical_bytes(compatibility),
        "skills/sample/SKILL.md": (
            "---\n"
            "name: sample\n"
            "description: Exercise a deterministic onboarding workflow.\n"
            "---\n\n"
            "Return a concise sample result.\n"
        ).encode("utf-8"),
    }


def write_plugin_builder_fixture(
    root: Path,
    *,
    schema: str = "plugin-builder-package-v3",
    files: Mapping[str, bytes] | None = None,
) -> PluginBuilderFixture:
    fixture_root = Path(root)
    fixture_root.mkdir(parents=True, exist_ok=True)
    candidate = fixture_root / "candidate"
    candidate.mkdir()
    for relative, content in (dict(files) if files is not None else _default_files()).items():
        destination = candidate.joinpath(*relative.split("/"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    archive = fixture_root / "sample-plugin.zip"
    archive_sha256 = plugin_authoring.write_deterministic_zip(
        candidate, archive, prefix="sample-plugin"
    )
    inventory = plugin_authoring.inventory_archive(archive)
    members = [asdict(member) for member in inventory.members]
    candidate_members = [asdict(member) for member in plugin_authoring.tree_manifest(candidate)]
    preflight_evidence = {
        "manifest_profile": "PORTABLE_WITH_OPENAI_COMPATIBILITY",
        "state": "PASS",
    }
    payload: dict[str, object] = {
        "schema": schema,
        "plugin_id": "sample-plugin",
        "archive_sha256": archive_sha256,
        "candidate_sha256": plugin_authoring.tree_sha256(candidate),
        "verification_sha256": "2" * 64,
        "member_manifest_sha256": sha256(canonical_bytes(members)).hexdigest(),
        "members": members,
        "candidate_members": candidate_members,
        "envelope_profile": "PORTABLE_SINGLE_DIRECTORY",
        "preflight_evidence": preflight_evidence,
        "manifest_profile": "PORTABLE_WITH_OPENAI_COMPATIBILITY",
        "command_evidence": [],
        "fallback_activations": [],
        "evidence_states": {
            "package_structure": "PASS",
            "installed_skill_invocation": "NOT VERIFIED",
        },
        "tool_bindings": [],
        "tool_contracts_sha256": sha256(canonical_bytes([])).hexdigest(),
        "extracted_validation": {"state": "PASS", "diagnostics": []},
        "safety_validation": {"state": "PASS", "diagnostics": []},
    }
    if schema == "plugin-builder-package-v3":
        payload.update(
            {
                "capabilities_sha256": "3" * 64,
                "realizations_sha256": "4" * 64,
                "adapter_registry_sha256": "5" * 64,
                "generated_runtime_configuration_sha256": "6" * 64,
                "runtime_realizations": [],
                "runtime_realization_state": "NOT VERIFIED",
            }
        )
    metadata = fixture_root / "package-metadata.json"
    metadata.write_bytes(canonical_bytes(payload))
    return PluginBuilderFixture(fixture_root, candidate, archive, metadata, payload)


def write_publication_decisions(
    path: Path,
    *,
    overrides: Mapping[str, object] | None = None,
) -> Path:
    payload: dict[str, object] = {
        "schema": "plugin-publication-decisions-v1",
        "plugin_id": "sample-plugin",
        "version": "1.2.3",
        "author": "Example Developer",
        "license": "MIT",
        "copyright_year": 2026,
        "redistribution_approved": True,
        "third_party_content_reviewed": True,
        "third_party_content": "NONE",
        "public_marketplace_approved": True,
        "target_runtime": "CODEX",
        "marketplace_id": "obvious-one",
        "codex_destination": "plugins/sample-plugin",
        "confirmed_by": "Plugin Owner",
        "decision_recorded_at": "2026-10-09T10:30:00+08:00",
    }
    if overrides:
        payload.update(overrides)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(canonical_bytes(payload))
    return destination
