from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework import plugin_authoring
from obvious_one_plugin_framework.plugin_onboarding import OnboardingError
from obvious_one_plugin_framework.plugin_onboarding.repair import (
    repair_delegated_reference_archive,
)
from obvious_one_plugin_framework.plugin_onboarding.repair_contract import (
    load_repair_contract,
)
from tests.framework.plugin_onboarding_fixtures import (
    canonical_bytes,
    write_legacy_repair_fixture,
)


class DelegatedReferenceRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fixture = write_legacy_repair_fixture(self.root / "fixture")
        self.contract_path = self.root / "repair.json"
        self.contract_path.write_bytes(canonical_bytes(self.fixture.contract_payload))
        self.contract = load_repair_contract(self.contract_path)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def build(self, name: str):
        output = self.root / name
        return repair_delegated_reference_archive(
            self.fixture.archive,
            self.contract,
            output / "sample-plugin-1.0.2.zip",
            output / "package-metadata.json",
        )

    def extract(self, archive: Path, name: str) -> Path:
        target = self.root / name
        plugin_authoring.extract_archive(archive, target)
        return target

    def test_repair_changes_only_approved_files_and_closes_handoffs(self) -> None:
        result = self.build("first")
        repaired = self.extract(result.archive, "repaired")
        self.assertEqual((repaired / "README.md").read_bytes(), b"untouched bytes\r\n")
        self.assertFalse((repaired / "PLUGIN-BUILDER-MANIFEST.json").exists())
        self.assertEqual(
            (repaired / "docs/provenance/source-PLUGIN-BUILDER-MANIFEST.json").read_bytes(),
            self.fixture.source_manifest,
        )
        for manifest in ("plugin.json", ".codex-plugin/plugin.json"):
            self.assertEqual(
                json.loads((repaired / manifest).read_text(encoding="utf-8"))["version"],
                "1.0.2",
            )
        for skill in self.contract.non_owner_skills:
            skill_root = repaired / "skills" / skill
            profile = json.loads(
                (skill_root / "assets/reference-profile.json").read_text(encoding="utf-8")
            )
            self.assertEqual(profile["schema"], "skill-reference-profile-v2")
            self.assertEqual(len(profile["delegated_references"]), 2)
            index = json.loads(
                (skill_root / "assets/knowledge-index.json").read_text(encoding="utf-8")
            )
            self.assertEqual(index["assets"], [])
            skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("## Delegated reference handoff", skill_text)
            self.assertNotIn("](assets/reference-material/RM-04", skill_text)
        owner = repaired / "skills" / self.contract.owner_skill
        for reference in self.contract.references:
            expected = owner.joinpath(*reference.owner_relative_path.split("/"))
            self.assertEqual(sha256(expected.read_bytes()).hexdigest(), reference.sha256)
            duplicates = [
                path
                for path in repaired.rglob(Path(reference.owner_relative_path).name)
                if path != expected
            ]
            self.assertEqual(duplicates, [])
        self.assertTrue((repaired / "WORKBENCH-REPAIR-MANIFEST.json").is_file())
        self.assertEqual(plugin_authoring.validate_plugin_tree(repaired), ())

    def test_metadata_is_workbench_owned_and_runtime_remains_not_verified(self) -> None:
        result = self.build("metadata")
        payload = json.loads(result.metadata.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "workbench-repaired-plugin-v1")
        self.assertEqual(payload["input_profile"], "PLUGIN_BUILDER_CANDIDATE_V1")
        self.assertEqual(payload["source_archive_sha256"], self.contract.source_archive_sha256)
        self.assertEqual(payload["archive_sha256"], result.archive_sha256)
        self.assertEqual(set(payload["evidence_states"].values()), {"NOT VERIFIED"})
        self.assertNotIn("candidate_sha256", payload)
        self.assertNotIn("verification_sha256", payload)

    def test_two_clean_builds_are_byte_identical(self) -> None:
        first = self.build("first")
        second = self.build("second")
        self.assertEqual(first.archive.read_bytes(), second.archive.read_bytes())
        self.assertEqual(first.metadata.read_bytes(), second.metadata.read_bytes())
        self.assertEqual(first.archive_sha256, second.archive_sha256)

    def test_wrong_source_digest_fails_without_partial_output(self) -> None:
        payload = dict(self.fixture.contract_payload)
        payload["source_archive_sha256"] = "f" * 64
        contract_path = self.root / "wrong.json"
        contract_path.write_bytes(canonical_bytes(payload))
        output = self.root / "blocked" / "candidate.zip"
        metadata = self.root / "blocked" / "metadata.json"
        with self.assertRaises(OnboardingError) as caught:
            repair_delegated_reference_archive(
                self.fixture.archive,
                load_repair_contract(contract_path),
                output,
                metadata,
            )
        self.assertEqual(caught.exception.code, "onboarding.repair.source_digest_mismatch")
        self.assertFalse(output.exists())
        self.assertFalse(metadata.exists())


if __name__ == "__main__":
    unittest.main()
