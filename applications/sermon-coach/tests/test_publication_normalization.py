from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework import plugin_authoring


APPLICATION = Path(__file__).resolve().parents[1]
SCRIPT = APPLICATION / "scripts" / "build_publication_release.py"


def _canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def _load_launcher():
    spec = importlib.util.spec_from_file_location("sermon_coach_release", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("release launcher could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_fixture(root: Path) -> tuple[Path, Path, dict[str, bytes]]:
    candidate = root / "candidate"
    (candidate / ".codex-plugin").mkdir(parents=True)
    (candidate / "skills" / "reviewing-sermon-evidence").mkdir(parents=True)
    (candidate / "references" / "source-materials").mkdir(parents=True)
    (candidate / "docs").mkdir(parents=True)
    (candidate / "scripts").mkdir(parents=True)
    interface = {
        "displayName": "講章優化教練",
        "shortDescription": "Sermon review",
        "longDescription": "Review sermons with supplied references.",
        "developerName": "SC",
        "category": "education",
        "capabilities": ["interactive", "reference-grounded"],
        "defaultPrompt": "Review this sermon.",
    }
    compatibility_manifest = {
        "name": "sermon-coach",
        "version": "1.0.3",
        "description": "Sermon review fixture",
        "author": {"name": "SC"},
        "skills": "./skills/",
        "interface": interface,
    }
    portable_manifest = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "sermon-coach",
        "version": "1.0.3",
        "description": "Sermon review fixture",
        "author": {"name": "SC"},
        "extensions": {"com.openai": {"interface": interface}},
    }
    (candidate / ".codex-plugin" / "plugin.json").write_bytes(_canonical(compatibility_manifest))
    (candidate / "plugin.json").write_bytes(_canonical(portable_manifest))
    (candidate / "skills" / "reviewing-sermon-evidence" / "SKILL.md").write_text(
        "---\nname: reviewing-sermon-evidence\ndescription: Review sermon evidence.\n---\n\n# Review\n\n[Invariants](../../docs/application-invariants.md)\n",
        encoding="utf-8",
        newline="\n",
    )
    invariant = candidate / "docs" / "application-invariants.md"
    invariant.write_bytes(b"approved invariant bytes\n")
    reference = candidate / "references" / "source-materials" / "approved-reference.md"
    reference.write_bytes(b"approved source bytes\n")
    validator_script = candidate / "scripts" / "validate.py"
    validator_script.write_bytes(b"print('offline validation')\n")
    before = {member.path: (candidate / member.path).read_bytes() for member in plugin_authoring.tree_manifest(candidate)}
    members = [asdict(member) for member in plugin_authoring.tree_manifest(candidate)]
    producer = {
        "schema": "plugin-builder-manifest-v1.0.3-runtime-native-reference-access",
        "content_tree_sha256": plugin_authoring.tree_sha256(candidate),
        "expected_members": sorted([*before, "PLUGIN-BUILDER-MANIFEST.json"]),
        "members": members,
        "plan_sha256": "1" * 64,
        "tools_sha256": "2" * 64,
        "tool_bindings": [],
        "tool_contracts": [
            {
                "schema": "producer-specific-offline-tool-v1",
                "id": "package-validator",
                "implementation_kind": "BUNDLED_LOCAL",
                "required": False,
                "skill_bindings": [],
                "files": ["scripts/validate.py"],
            }
        ],
    }
    producer_bytes = _canonical(producer)
    (candidate / "PLUGIN-BUILDER-MANIFEST.json").write_bytes(producer_bytes)
    source = root / "source.zip"
    source_sha256 = plugin_authoring.write_deterministic_zip(candidate, source)
    contract = {
        "schema": "sermon-coach-publication-normalization-v1",
        "plugin_id": "sermon-coach",
        "version": "1.0.3",
        "source_archive_sha256": source_sha256,
        "source_manifest_schema": producer["schema"],
        "source_content_tree_sha256_claim": producer["content_tree_sha256"],
        "source_content_tree_sha256_recomputed": producer["content_tree_sha256"],
        "source_content_tree_disposition": "SUPERSEDED_BY_EXACT_MEMBER_CLOSURE",
        "skill_local_document_bindings": {
            "skills": ["reviewing-sermon-evidence"],
            "documents": [
                {
                    "path": "docs/application-invariants.md",
                    "sha256": sha256(invariant.read_bytes()).hexdigest(),
                }
            ],
        },
        "license": "MIT",
        "copyright_year": 2026,
        "copyright_holder": "SC",
        "approval_record": {
            "decision": "APPROVED",
            "confirmed_by": "decision-owner",
            "recorded_at": "2026-10-11",
        },
        "third_party_sources": [
            {
                "reference_id": "RM-TEST",
                "path": "references/source-materials/approved-reference.md",
                "sha256": sha256(reference.read_bytes()).hexdigest(),
                "rights_basis": "Owner-approved inclusion and redistribution.",
            }
        ],
    }
    contract_path = root / "contract.json"
    contract_path.write_bytes(_canonical(contract))
    before["PLUGIN-BUILDER-MANIFEST.json"] = producer_bytes
    return source, contract_path, before


class SermonCoachPublicationNormalizationTests(unittest.TestCase):
    def test_approved_contract_records_exact_source_and_rights(self) -> None:
        launcher = _load_launcher()

        contract = launcher._load_contract(launcher.CONTRACT_PATH)

        self.assertEqual(
            contract["source_archive_sha256"],
            "cf425863ede9d205944373b26c1c7f0435d2cc66c8ac6e949afca67939e62c90",
        )
        self.assertEqual(contract["plugin_id"], "sermon-coach")
        self.assertEqual(contract["version"], "1.0.3")
        self.assertEqual(contract["license"], "MIT")
        self.assertEqual(contract["copyright_holder"], "SC")
        self.assertEqual(len(contract["third_party_sources"]), 6)
        self.assertEqual(
            {item["reference_id"] for item in contract["third_party_sources"]},
            {"RM-01", "RM-02", "RM-03", "RM-04-SOURCE", "RM-05", "RM-06"},
        )

    def test_build_preserves_plugin_bytes_and_adds_publication_controls(self) -> None:
        launcher = _load_launcher()
        with tempfile.TemporaryDirectory(prefix="sermon-publication-") as name:
            root = Path(name)
            source, contract, before = _write_fixture(root)

            result = launcher.build_publication_release(source, root / "output", contract)

            extracted = root / "extracted"
            plugin_authoring.extract_archive(result.archive, extracted)
            self.assertFalse((extracted / "PLUGIN-BUILDER-MANIFEST.json").exists())
            self.assertEqual(
                (extracted / "docs/provenance/source-PLUGIN-BUILDER-MANIFEST.json").read_bytes(),
                before["PLUGIN-BUILDER-MANIFEST.json"],
            )
            for relative, expected in before.items():
                if relative in {
                    "PLUGIN-BUILDER-MANIFEST.json",
                    "skills/reviewing-sermon-evidence/SKILL.md",
                }:
                    continue
                self.assertEqual((extracted / relative).read_bytes(), expected, relative)
            repaired_skill = (
                extracted / "skills" / "reviewing-sermon-evidence" / "SKILL.md"
            ).read_text(encoding="utf-8")
            self.assertIn("assets/docs/application-invariants.md", repaired_skill)
            self.assertNotIn("../../docs/application-invariants.md", repaired_skill)
            self.assertEqual(
                (
                    extracted
                    / "skills"
                    / "reviewing-sermon-evidence"
                    / "assets"
                    / "docs"
                    / "application-invariants.md"
                ).read_bytes(),
                before["docs/application-invariants.md"],
            )
            self.assertIn("MIT License", (extracted / "LICENSE").read_text(encoding="utf-8"))
            notice = (extracted / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
            self.assertIn("RM-TEST", notice)
            self.assertIn("approved-reference.md", notice)
            self.assertTrue((extracted / "WORKBENCH-REPAIR-MANIFEST.json").is_file())
            metadata = json.loads(result.metadata.read_text(encoding="utf-8"))
            self.assertEqual(metadata["schema"], "workbench-repaired-plugin-v2")
            self.assertEqual(metadata["input_profile"], "PLUGIN_BUILDER_VERSIONED_LEGACY_V1")
            self.assertEqual(set(metadata["evidence_states"].values()), {"NOT VERIFIED"})
            self.assertEqual(metadata["tool_bindings"], [])
            self.assertEqual(
                metadata["offline_validators"][0],
                {
                    "id": "package-validator",
                    "files": ["scripts/validate.py"],
                    "runtime_role": "OFFLINE_PACKAGE_VALIDATION_ONLY",
                    "required": False,
                    "installed_runtime_callable": False,
                    "source_contract_sha256": sha256(
                        _canonical(
                            {
                                "schema": "producer-specific-offline-tool-v1",
                                "id": "package-validator",
                                "implementation_kind": "BUNDLED_LOCAL",
                                "required": False,
                                "skill_bindings": [],
                                "files": ["scripts/validate.py"],
                            }
                        )
                    ).hexdigest(),
                },
            )
            repair = json.loads(
                (extracted / "WORKBENCH-REPAIR-MANIFEST.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                repair["offline_validators"],
                metadata["offline_validators"],
            )

    def test_two_clean_builds_are_byte_identical(self) -> None:
        launcher = _load_launcher()
        with tempfile.TemporaryDirectory(prefix="sermon-publication-repeat-") as name:
            root = Path(name)
            source, contract, _ = _write_fixture(root)

            first = launcher.build_publication_release(source, root / "first", contract)
            second = launcher.build_publication_release(source, root / "second", contract)

            self.assertEqual(first.archive.read_bytes(), second.archive.read_bytes())
            self.assertEqual(first.metadata.read_bytes(), second.metadata.read_bytes())

    def test_source_member_records_are_order_independent_but_hash_bound(self) -> None:
        launcher = _load_launcher()
        with tempfile.TemporaryDirectory(prefix="sermon-publication-order-") as name:
            root = Path(name)
            source, contract_path, _ = _write_fixture(root)
            extracted = root / "reordered"
            plugin_authoring.extract_archive(source, extracted)
            manifest_path = extracted / "PLUGIN-BUILDER-MANIFEST.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["members"] = list(reversed(manifest["members"]))
            manifest["expected_members"] = list(reversed(manifest["expected_members"]))
            manifest_path.write_bytes(_canonical(manifest))
            reordered_source = root / "reordered.zip"
            reordered_digest = plugin_authoring.write_deterministic_zip(extracted, reordered_source)
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["source_archive_sha256"] = reordered_digest
            reordered_contract = root / "reordered-contract.json"
            reordered_contract.write_bytes(_canonical(contract))

            result = launcher.build_publication_release(
                reordered_source,
                root / "output",
                reordered_contract,
            )

            self.assertTrue(result.archive.is_file())

    def test_stale_tree_claim_requires_exact_claim_and_recomputed_bindings(self) -> None:
        launcher = _load_launcher()
        with tempfile.TemporaryDirectory(prefix="sermon-publication-tree-claim-") as name:
            root = Path(name)
            source, contract_path, _ = _write_fixture(root)
            extracted = root / "stale"
            plugin_authoring.extract_archive(source, extracted)
            manifest_path = extracted / "PLUGIN-BUILDER-MANIFEST.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["content_tree_sha256"] = "a" * 64
            manifest_path.write_bytes(_canonical(manifest))
            stale_source = root / "stale.zip"
            stale_digest = plugin_authoring.write_deterministic_zip(extracted, stale_source)
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["source_archive_sha256"] = stale_digest
            contract["source_content_tree_sha256_claim"] = "a" * 64
            stale_contract = root / "stale-contract.json"
            stale_contract.write_bytes(_canonical(contract))

            result = launcher.build_publication_release(
                stale_source,
                root / "output",
                stale_contract,
            )

            self.assertTrue(result.archive.is_file())


if __name__ == "__main__":
    unittest.main()
