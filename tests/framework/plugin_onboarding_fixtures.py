from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping
import zipfile

from obvious_one_plugin_framework import plugin_authoring


PORTABLE_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True)
        + "\n"
    ).encode("ascii")


@dataclass(frozen=True)
class PluginBuilderFixture:
    root: Path
    candidate: Path
    archive: Path
    metadata: Path
    metadata_payload: Mapping[str, object]

    @property
    def candidate_files(self) -> dict[str, bytes]:
        return {
            path.relative_to(self.candidate).as_posix(): path.read_bytes()
            for path in sorted(self.candidate.rglob("*"))
            if path.is_file() and path.name != "PLUGIN-BUILDER-MANIFEST.json"
        }


@dataclass(frozen=True)
class LegacyRepairFixture:
    root: Path
    candidate: Path
    archive: Path
    source_manifest: bytes
    contract_payload: Mapping[str, object]


def write_legacy_repair_fixture(root: Path) -> LegacyRepairFixture:
    fixture_root = Path(root)
    fixture_root.mkdir(parents=True, exist_ok=True)
    candidate = fixture_root / "legacy-candidate"
    candidate.mkdir()
    interface = {
        "displayName": "Sample Plugin",
        "shortDescription": "Portable sample",
        "longDescription": "A portable sample plugin for repair tests.",
        "developerName": "Example Developer",
        "category": "Education",
        "capabilities": ["Interactive", "Read"],
        "defaultPrompt": "Help me use this plugin.",
    }
    files: dict[str, bytes] = {
        "plugin.json": canonical_bytes(
            {
                "$schema": PORTABLE_SCHEMA,
                "name": "sample-plugin",
                "version": "1.0.1",
                "description": "A portable sample plugin.",
                "author": {"name": "Example Developer"},
                "extensions": {"com.openai": {"interface": interface}},
            }
        ),
        ".codex-plugin/plugin.json": canonical_bytes(
            {
                "name": "sample-plugin",
                "version": "1.0.1",
                "description": "A portable sample plugin.",
                "author": {"name": "Example Developer"},
                "skills": "./skills/",
                "interface": interface,
            }
        ),
        "README.md": b"untouched bytes\r\n",
    }
    owner = "guiding-biblical-study"
    non_owners = ("guiding-parenting-sessions", "supporting-parent-reflection")
    references = {
        "RM-04A": ("reference-material/RM-04A_Bible_OT.pdf", b"OT-PDF\n"),
        "RM-04B": ("reference-material/RM-04B_Bible_NT.pdf", b"NT-PDF\n"),
    }
    owner_links = "\n".join(
        f"- [{reference_id}](assets/{relative})"
        for reference_id, (relative, _) in references.items()
    )
    files[f"skills/{owner}/SKILL.md"] = (
        "---\n"
        f"name: {owner}\n"
        "description: Own exact Scripture verification and formal Bible study.\n"
        "---\n\n"
        f"{owner_links}\n"
    ).encode("utf-8")
    owner_assets = []
    for reference_id, (relative, content) in references.items():
        files[f"skills/{owner}/assets/{relative}"] = content
        owner_assets.append({"id": reference_id, "file": relative})
    files[f"skills/{owner}/assets/knowledge-index.json"] = canonical_bytes(
        {"assets": owner_assets}
    )
    files[f"skills/{owner}/assets/reference-profile.json"] = canonical_bytes(
        {
            "schema": "skill-reference-profile-v1",
            "skill": owner,
            "major_intents": ["Bible study"],
            "required": [],
            "conditional": [],
            "optional": [],
            "prohibited_substitutions": ["Do not fabricate exact Scripture."],
            "fallback": "Disclose unavailable authority.",
        }
    )
    for skill in non_owners:
        stale_links = "\n".join(
            f"- [{reference_id}](assets/{relative})"
            for reference_id, (relative, _) in references.items()
        )
        files[f"skills/{skill}/SKILL.md"] = (
            "---\n"
            f"name: {skill}\n"
            "description: Route a sample parent workflow.\n"
            "---\n\n"
            "Keep this ordinary behavior byte-stable where possible.\n\n"
            f"{stale_links}\n"
        ).encode("utf-8")
        files[f"skills/{skill}/assets/knowledge-index.json"] = canonical_bytes(
            {
                "assets": [
                    {"id": reference_id, "file": relative}
                    for reference_id, (relative, _) in references.items()
                ]
            }
        )
        files[f"skills/{skill}/assets/reference-profile.json"] = canonical_bytes(
            {
                "schema": "skill-reference-profile-v1",
                "skill": skill,
                "major_intents": ["Parenting"],
                "required": [],
                "conditional": [
                    f"assets/{relative}" for relative, _ in references.values()
                ],
                "optional": [],
                "prohibited_substitutions": ["Do not fabricate exact Scripture."],
                "fallback": "Disclose unavailable authority.",
            }
        )
    for relative, content in files.items():
        destination = candidate.joinpath(*relative.split("/"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    source_manifest = canonical_bytes(
        {
            "schema": "plugin-builder-candidate-manifest-v1",
            "candidate_version": "1.0.1",
            "w1_state": "APPROVED",
            "w2_state": "APPROVED",
            "expected_members": sorted([*files, "PLUGIN-BUILDER-MANIFEST.json"]),
        }
    )
    (candidate / "PLUGIN-BUILDER-MANIFEST.json").write_bytes(source_manifest)
    archive = fixture_root / "legacy-plugin.zip"
    archive_sha256 = plugin_authoring.write_deterministic_zip(candidate, archive)
    contract_payload: dict[str, object] = {
        "schema": "plugin-delegated-reference-repair-v1",
        "plugin_id": "sample-plugin",
        "source_version": "1.0.1",
        "target_version": "1.0.2",
        "source_archive_sha256": archive_sha256,
        "owner_skill": owner,
        "non_owner_skills": list(non_owners),
        "references": [
            {
                "reference_id": reference_id,
                "owner_relative_path": f"assets/{relative}",
                "sha256": sha256(content).hexdigest(),
            }
            for reference_id, (relative, content) in references.items()
        ],
        "source_manifest_path": "PLUGIN-BUILDER-MANIFEST.json",
        "approval_record": {
            "decision": "APPROVED",
            "confirmed_by": "Plugin Owner",
            "recorded_at": "2026-10-09T12:00:00+08:00",
        },
    }
    return LegacyRepairFixture(
        fixture_root,
        candidate,
        archive,
        source_manifest,
        contract_payload,
    )


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
    tool_bindings: list[dict[str, object]] | None = None,
    tool_contracts: list[dict[str, object]] | None = None,
) -> PluginBuilderFixture:
    fixture_root = Path(root)
    fixture_root.mkdir(parents=True, exist_ok=True)
    candidate = fixture_root / "candidate"
    candidate.mkdir()
    for relative, content in (dict(files) if files is not None else _default_files()).items():
        destination = candidate.joinpath(*relative.split("/"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    bindings = list(tool_bindings or [])
    contracts = list(tool_contracts or [])
    manifest_path = candidate / "PLUGIN-BUILDER-MANIFEST.json"
    if not manifest_path.exists():
        content_members = [
            asdict(member) for member in plugin_authoring.tree_manifest(candidate)
        ]
        candidate_manifest: dict[str, object] = {
            "schema": (
                "plugin-builder-candidate-manifest-v3"
                if schema == "plugin-builder-package-v3"
                else "plugin-builder-candidate-manifest-v2"
            ),
            "operation": "create",
            "plan_sha256": "7" * 64,
            "tools_sha256": sha256(canonical_bytes([])).hexdigest(),
            "preflight_evidence_sha256": sha256(
                canonical_bytes(
                    {
                        "manifest_profile": "PORTABLE_WITH_OPENAI_COMPATIBILITY",
                        "state": "PASS",
                    }
                )
            ).hexdigest(),
            "file_roles": {},
            "manifest_profile": "PORTABLE_WITH_OPENAI_COMPATIBILITY",
            "manifest_profile_sha256": "9" * 64,
            "content_tree_sha256": plugin_authoring.tree_sha256(candidate),
            "expected_members": sorted(
                [item["path"] for item in content_members]
                + ["PLUGIN-BUILDER-MANIFEST.json"]
            ),
            "members": content_members,
            "tool_bindings": bindings,
            "tool_contracts": contracts,
        }
        if schema == "plugin-builder-package-v3":
            candidate_manifest.update(
                {
                    "capabilities_sha256": "3" * 64,
                    "realizations_sha256": "4" * 64,
                    "adapter_registry_sha256": "5" * 64,
                    "generated_runtime_configuration_sha256": "6" * 64,
                }
            )
        manifest_path.write_bytes(canonical_bytes(candidate_manifest))

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
        "tool_bindings": bindings,
        "tool_contracts_sha256": sha256(canonical_bytes(contracts)).hexdigest(),
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


def write_runtime_evidence_bundle(
    path: Path,
    fixture: PluginBuilderFixture,
    *,
    overrides: Mapping[str, object] | None = None,
) -> Path:
    metadata = fixture.metadata_payload
    result: dict[str, object] = {
        "schema": "plugin-onboarding-runtime-observations-v1",
        "plugin_id": "sample-plugin",
        "version": "1.2.3",
        "zip_sha256": metadata["archive_sha256"],
        "member_manifest_sha256": metadata["member_manifest_sha256"],
        "candidate_sha256": metadata["candidate_sha256"],
        "verification_sha256": metadata["verification_sha256"],
        "plan_sha256": "7" * 64,
        "session_sha256": "a" * 64,
        "operation_identities": [],
        "evidence_states": {
            "installation": "NOT VERIFIED",
            "skill_invocation": "NOT VERIFIED",
            "capability_discovery": "NOT VERIFIED",
            "operation_execution": "NOT VERIFIED",
            "result_delivery": "NOT VERIFIED",
            "conversation": "NOT VERIFIED",
        },
    }
    if overrides:
        result.update(overrides)
    result_bytes = canonical_bytes(result)
    result_digest = sha256(result_bytes).hexdigest()
    index = {
        "schema": "plugin-builder-runtime-evidence-index-v1",
        "result": {
            "path": f"results/{result_digest}.json",
            "sha256": result_digest,
            "size": len(result_bytes),
        },
        "evidence": [],
    }
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("evidence-index.json", canonical_bytes(index))
        archive.writestr(f"results/{result_digest}.json", result_bytes)
    return destination


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
