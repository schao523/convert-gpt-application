from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from obvious_one_plugin_framework import plugin_authoring
from obvious_one_plugin_framework.contract import load_contract
from obvious_one_plugin_framework.plugin_onboarding.contract import OnboardingError
from obvious_one_plugin_framework.plugin_onboarding.materialize import (
    prepare_plugin_zip_marketplace,
)
from obvious_one_plugin_framework.plugin_onboarding import materialize as onboarding_materialize
from obvious_one_plugin_framework.verification import load_application_config_path
from tests.framework.plugin_onboarding_fixtures import (
    write_plugin_builder_fixture,
    write_publication_decisions,
)


REPOSITORY = Path(__file__).resolve().parents[2]


class PluginOnboardingMaterializeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fixture = write_plugin_builder_fixture(self.root / "package")
        self.decisions = write_publication_decisions(self.root / "decisions.json")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def prepare(self, output: Path, *, fixture=None, decisions: Path | None = None):
        selected = fixture or self.fixture
        return prepare_plugin_zip_marketplace(
            selected.archive,
            selected.metadata,
            decisions or self.decisions,
            REPOSITORY,
            output,
        )

    def test_materialization_writes_exact_specified_tree_and_relative_result_paths(self) -> None:
        output = self.root / "proposal"
        result = self.prepare(output)
        expected = {
            ".obvious-one-plugin-onboarding",
            "onboarding-result.json",
            "onboarding-proposal.json",
            "catalog-entry.json",
            "application/conversion.json",
            "application/plugin.json",
            "application/.codex-plugin/plugin.json",
            "application/DISTRIBUTION.md",
            "application/LICENSE",
            "application/PRIVACY.md",
            "application/SECURITY.md",
            "application/THIRD_PARTY_CONTENT.md",
            "application/THIRD_PARTY_NOTICES.md",
            "application/docs/application-invariants.md",
            "application/docs/imported-package-inventory.json",
            "application/docs/publication-decisions.json",
            "application/docs/runtime-compatibility.md",
            "application/docs/source-decisions.md",
            "application/openclaw/distribution.json",
            "application/scripts/build_marketplace_release.py",
            "application/scripts/distribution_audit.py",
            "application/tests/test_imported_package.py",
            "application/tests/test_marketplace_release.py",
        }
        actual = {
            path.relative_to(output).as_posix()
            for path in output.rglob("*")
            if path.is_file()
        }
        imported = {
            f"application/imported-plugin/{path.relative_to(self.fixture.candidate).as_posix()}"
            for path in self.fixture.candidate.rglob("*")
            if path.is_file()
        }
        self.assertEqual(actual, expected | imported)
        self.assertEqual(result.status, "PASS")
        self.assertTrue(all(not Path(item.path).is_absolute() for item in result.artifacts))
        self.assertTrue(all(not Path(item.path).is_absolute() for item in result.mutations))

    def test_imported_plugin_bytes_equal_archive_candidate_members(self) -> None:
        output = self.root / "exact"
        self.prepare(output)
        imported = output / "application" / "imported-plugin"
        self.assertEqual(plugin_authoring.tree_manifest(imported), plugin_authoring.tree_manifest(self.fixture.candidate))
        for source in self.fixture.candidate.rglob("*"):
            if source.is_file():
                self.assertEqual(
                    (imported / source.relative_to(self.fixture.candidate)).read_bytes(),
                    source.read_bytes(),
                )

    def test_two_independent_outputs_have_identical_files_and_tree_identity(self) -> None:
        first = self.root / "first"
        second = self.root / "second"
        first_result = self.prepare(first)
        second_result = self.prepare(second)
        self.assertEqual(plugin_authoring.tree_sha256(first), plugin_authoring.tree_sha256(second))
        self.assertEqual(first_result.evidence, second_result.evidence)

    def test_generated_manifest_pair_and_arbitrary_skills_validate(self) -> None:
        files = self.fixture.candidate_files
        files.update(
            {
                f"skills/skill-{index}/SKILL.md": (
                    "---\n"
                    f"name: skill-{index}\n"
                    f"description: Execute bounded sample workflow {index}.\n"
                    "---\n"
                ).encode("utf-8")
                for index in range(1, 8)
            }
        )
        fixture = write_plugin_builder_fixture(self.root / "many-skills", files=files)
        output = self.root / "many-skills-proposal"
        self.prepare(output, fixture=fixture)
        imported = output / "application" / "imported-plugin"
        self.assertEqual(plugin_authoring.validate_plugin_tree(imported), ())
        adopted = self.root / "adopted" / "applications" / "sample-plugin"
        adopted.parent.mkdir(parents=True)
        shutil.copytree(output / "application", adopted)
        self.assertEqual(
            load_application_config_path(
                adopted / "conversion.json", self.root / "adopted"
            ).plugin_id,
            "sample-plugin",
        )

    def test_mixed_text_and_binary_files_have_complete_v3_content_rules(self) -> None:
        files = self.fixture.candidate_files
        files.update({"assets/blob.bin": b"\x00\xff\x10", "notes.txt": b"public text\n"})
        fixture = write_plugin_builder_fixture(self.root / "mixed", files=files)
        output = self.root / "mixed-proposal"
        self.prepare(output, fixture=fixture)
        contract = load_contract(output / "application" / "openclaw" / "distribution.json")
        classifications = {
            path: rule.classification
            for rule in contract.content_rules
            for path in rule.paths
        }
        self.assertEqual(classifications["imported-plugin/assets/blob.bin"], "binary")
        self.assertEqual(classifications["imported-plugin/notes.txt"], "text")
        selected = set(contract.include_files)
        classified = set(classifications)
        self.assertEqual(selected, classified)

    def test_generated_mit_and_third_party_documents_follow_owner_decisions(self) -> None:
        files = self.fixture.candidate_files
        files["THIRD_PARTY_NOTICES.md"] = b"# Notices\n\nExample dependency.\n"
        fixture = write_plugin_builder_fixture(self.root / "notices", files=files)
        decisions = write_publication_decisions(
            self.root / "notices-decisions.json",
            overrides={"third_party_content": "INCLUDED_WITH_PLUGIN_NOTICES"},
        )
        output = self.root / "notices-proposal"
        self.prepare(output, fixture=fixture, decisions=decisions)
        self.assertIn("2026 Example Developer", (output / "application" / "LICENSE").read_text(encoding="utf-8"))
        self.assertEqual(
            (output / "application" / "THIRD_PARTY_NOTICES.md").read_bytes(),
            files["THIRD_PARTY_NOTICES.md"],
        )
        self.assertIn("INCLUDED_WITH_PLUGIN_NOTICES", (output / "application" / "THIRD_PARTY_CONTENT.md").read_text(encoding="utf-8"))

    def test_unmarked_nonempty_output_collision_preserves_all_inputs(self) -> None:
        output = self.root / "collision"
        output.mkdir()
        sentinel = output / "keep.txt"
        sentinel.write_bytes(b"keep\r\n")
        archive_before = self.fixture.archive.read_bytes()
        repository_before = plugin_authoring.tree_sha256(REPOSITORY)
        with self.assertRaises(OnboardingError) as caught:
            self.prepare(output)
        self.assertEqual(caught.exception.code, "onboarding.output_collision")
        self.assertEqual(sentinel.read_bytes(), b"keep\r\n")
        self.assertEqual(self.fixture.archive.read_bytes(), archive_before)
        self.assertEqual(plugin_authoring.tree_sha256(REPOSITORY), repository_before)

    def test_owned_replacement_is_transactional_and_failure_preserves_previous_tree(self) -> None:
        output = self.root / "owned"
        self.prepare(output)
        before = plugin_authoring.tree_sha256(output)
        with patch(
            "obvious_one_plugin_framework.plugin_onboarding.materialize._publish_output",
            side_effect=OSError("injected replacement failure"),
        ):
            with self.assertRaises(OSError):
                self.prepare(output)
        self.assertEqual(plugin_authoring.tree_sha256(output), before)

    def test_output_swapped_after_preflight_is_not_overwritten(self) -> None:
        output = self.root / "swapped"
        original_validate = onboarding_materialize._validate_stage

        def swap_after_validation(application: Path, imported: Path) -> None:
            original_validate(application, imported)
            output.mkdir()
            (output / "intruder.txt").write_bytes(b"preserve\r\n")

        with patch(
            "obvious_one_plugin_framework.plugin_onboarding.materialize._validate_stage",
            side_effect=swap_after_validation,
        ):
            with self.assertRaises(OnboardingError) as caught:
                self.prepare(output)

        self.assertEqual(caught.exception.code, "onboarding.output_collision")
        self.assertEqual((output / "intruder.txt").read_bytes(), b"preserve\r\n")
        self.assertEqual(
            {path.name for path in output.iterdir()},
            {"intruder.txt"},
        )

    def test_owned_output_can_be_replaced_and_missing_output_is_created(self) -> None:
        output = self.root / "replaceable"
        self.assertFalse(output.exists())
        first = self.prepare(output)
        first_tree = plugin_authoring.tree_sha256(output)
        second = self.prepare(output)
        self.assertEqual(first_tree, plugin_authoring.tree_sha256(output))
        self.assertEqual(first.evidence, second.evidence)


if __name__ == "__main__":
    unittest.main()
