from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
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
from obvious_one_plugin_framework.provenance import inventory_source
from obvious_one_plugin_framework.verification import load_application_config_path
from scripts.verify_extraction import RunContext, _provenance_gate
from tests.framework.plugin_onboarding_fixtures import (
    canonical_bytes,
    rebuild_legacy_plugin_builder_fixture,
    write_legacy_plugin_builder_fixture,
    write_legacy_repair_fixture,
    write_plugin_builder_fixture,
    write_publication_decisions,
)


REPOSITORY = Path(__file__).resolve().parents[2]


class PluginOnboardingMaterializeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fixture = write_plugin_builder_fixture(self.root / "package")
        self.legacy_fixture = write_legacy_plugin_builder_fixture(self.root / "legacy-package")
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

    def prepare_legacy(
        self,
        output: Path,
        *,
        fixture=None,
        decisions: Path | None = None,
        evidence: Path | None = None,
    ):
        selected = fixture or self.legacy_fixture
        return prepare_plugin_zip_marketplace(
            selected.archive,
            None,
            decisions or self.decisions,
            REPOSITORY,
            output,
            legacy_adoption=selected.adoption,
            evidence=evidence,
        )

    def test_materialization_writes_exact_specified_tree_and_relative_result_paths(self) -> None:
        output = self.root / "proposal"
        result = self.prepare(output)
        expected = {
            ".obvious-one-plugin-onboarding",
            "onboarding-result.json",
            "onboarding-proposal.json",
            "catalog-entry.json",
            "application/.gitattributes",
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
        self.assertEqual(
            (output / "application" / ".gitattributes").read_bytes(),
            b"imported-plugin/** -text -whitespace\n",
        )
        self.assertEqual(result.status, "PASS")
        self.assertTrue(all(not Path(item.path).is_absolute() for item in result.artifacts))
        self.assertTrue(all(not Path(item.path).is_absolute() for item in result.mutations))

    def test_workbench_repaired_flat_archive_materializes_without_builder_evidence(self) -> None:
        from obvious_one_plugin_framework.plugin_onboarding import (
            load_repair_contract,
            repair_delegated_reference_archive,
        )

        legacy = write_legacy_repair_fixture(self.root / "legacy")
        contract_path = self.root / "repair.json"
        contract_path.write_bytes(canonical_bytes(legacy.contract_payload))
        repaired = repair_delegated_reference_archive(
            legacy.archive,
            load_repair_contract(contract_path),
            self.root / "repaired.zip",
            self.root / "repaired-metadata.json",
        )
        decisions = write_publication_decisions(
            self.root / "repair-decisions.json",
            overrides={"version": "1.0.2"},
        )
        output = self.root / "repaired-proposal"
        result = prepare_plugin_zip_marketplace(
            repaired.archive,
            repaired.metadata,
            decisions,
            REPOSITORY,
            output,
        )
        self.assertEqual(result.status, "PASS")
        proposal = json.loads((output / "onboarding-proposal.json").read_text(encoding="ascii"))
        evidence = proposal["builder_evidence"]
        self.assertEqual(evidence["input_profile"], "WORKBENCH_REPAIRED_PLUGIN_V1")
        self.assertNotIn("candidate_sha256", evidence)
        self.assertNotIn("verification_sha256", evidence)

    def test_legacy_adoption_materializes_exact_flat_archive_bytes(self) -> None:
        output = self.root / "legacy-proposal"

        result = self.prepare_legacy(output)

        self.assertEqual(result.status, "PASS")
        imported = output / "application" / "imported-plugin"
        self.assertEqual(
            plugin_authoring.tree_manifest(imported),
            plugin_authoring.tree_manifest(self.legacy_fixture.candidate),
        )
        proposal = json.loads(
            (output / "onboarding-proposal.json").read_text(encoding="ascii")
        )
        evidence = proposal["builder_evidence"]
        self.assertEqual(
            evidence["input_profile"],
            "PLUGIN_BUILDER_DETERMINISTIC_CONTENT_V2",
        )
        self.assertRegex(evidence["adoption_identity_sha256"], r"^[0-9a-f]{64}$")
        self.assertNotIn("candidate_sha256", evidence)
        self.assertNotIn("verification_sha256", evidence)

    def test_generated_imported_test_detects_changed_legacy_member_bytes(self) -> None:
        output = self.root / "legacy-generated-test"
        self.prepare_legacy(output)
        application = output / "application"
        generated_test = application / "tests" / "test_imported_package.py"

        passing = subprocess.run(
            [sys.executable, "-B", str(generated_test)],
            cwd=application,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(passing.returncode, 0, passing.stdout + passing.stderr)

        helper = application / "imported-plugin" / "scripts" / "helper.py"
        helper.write_bytes(helper.read_bytes() + b"# changed\n")
        changed = subprocess.run(
            [sys.executable, "-B", str(generated_test)],
            cwd=application,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(changed.returncode, 0, changed.stdout + changed.stderr)

    def test_legacy_outputs_are_deterministic_and_allow_historical_portable_omissions(self) -> None:
        fixture = write_legacy_plugin_builder_fixture(self.root / "legacy-omissions")
        portable_path = fixture.candidate / "plugin.json"
        portable = json.loads(portable_path.read_text(encoding="utf-8"))
        interface = portable["extensions"]["com.openai"]["interface"]
        for field in ("longDescription", "developerName", "category", "capabilities"):
            interface.pop(field)
        portable_path.write_bytes(canonical_bytes(portable))
        fixture = rebuild_legacy_plugin_builder_fixture(fixture)
        first = self.root / "legacy-first"
        second = self.root / "legacy-second"

        first_result = self.prepare_legacy(first, fixture=fixture)
        second_result = self.prepare_legacy(second, fixture=fixture)

        self.assertEqual(plugin_authoring.tree_sha256(first), plugin_authoring.tree_sha256(second))
        self.assertEqual(first_result.evidence, second_result.evidence)

    def test_legacy_authority_selection_and_runtime_evidence_fail_before_output(self) -> None:
        cases = (
            (
                lambda output: prepare_plugin_zip_marketplace(
                    self.legacy_fixture.archive,
                    None,
                    self.decisions,
                    REPOSITORY,
                    output,
                ),
                "onboarding.authority_selection_invalid",
            ),
            (
                lambda output: prepare_plugin_zip_marketplace(
                    self.fixture.archive,
                    self.fixture.metadata,
                    self.decisions,
                    REPOSITORY,
                    output,
                    legacy_adoption=self.legacy_fixture.adoption,
                ),
                "onboarding.authority_selection_invalid",
            ),
            (
                lambda output: self.prepare_legacy(
                    output,
                    evidence=self.root / "unsupported-evidence.zip",
                ),
                "onboarding.legacy_runtime_evidence_unsupported",
            ),
        )
        for index, (operation, code) in enumerate(cases):
            with self.subTest(code=code):
                output = self.root / f"legacy-authority-{index}"
                with self.assertRaises(OnboardingError) as caught:
                    operation(output)
                self.assertEqual(caught.exception.code, code)
                self.assertFalse(output.exists())

    def test_legacy_archive_change_after_approval_and_overlay_collision_fail_closed(self) -> None:
        changed = write_legacy_plugin_builder_fixture(self.root / "legacy-changed")
        changed.archive.write_bytes(changed.archive.read_bytes() + b"changed")
        with self.assertRaises(OnboardingError) as caught:
            self.prepare_legacy(self.root / "legacy-changed-output", fixture=changed)
        self.assertEqual(caught.exception.code, "onboarding.inspection.archive_sha256_mismatch")

        collision = write_legacy_plugin_builder_fixture(self.root / "legacy-collision")
        (collision.candidate / "LICENSE").write_bytes(b"source license\n")
        collision = rebuild_legacy_plugin_builder_fixture(collision)
        with self.assertRaises(OnboardingError) as caught:
            self.prepare_legacy(self.root / "legacy-collision-output", fixture=collision)
        self.assertEqual(caught.exception.code, "onboarding.proposal.overlay_collision")

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
        config = load_application_config_path(
            adopted / "conversion.json", self.root / "adopted"
        )
        self.assertEqual(config.plugin_id, "sample-plugin")
        inventory = inventory_source(adopted, config.provenance.inventory_rules)
        self.assertIn(
            "imported-plugin/skills/sample/SKILL.md",
            {item["path"] for item in inventory},
        )

    def test_generated_imported_inventory_passes_repository_provenance_gate(self) -> None:
        output = self.root / "provenance-proposal"
        self.prepare(output)
        adopted = self.root / "provenance-repository" / "applications" / "sample-plugin"
        adopted.parent.mkdir(parents=True)
        shutil.copytree(output / "application", adopted)
        config = load_application_config_path(
            adopted / "conversion.json",
            self.root / "provenance-repository",
        )
        context = RunContext(
            repository_root=self.root / "provenance-repository",
            diagnostics=self.root / "provenance-diagnostics",
            python="python",
        )

        gate = _provenance_gate(config, context)

        self.assertEqual((gate.state, gate.detail), ("PASS", "application provenance is valid"))

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

        def swap_after_validation(
            application: Path,
            imported: Path,
            *,
            strict_plugin_tree: bool = True,
        ) -> None:
            original_validate(
                application,
                imported,
                strict_plugin_tree=strict_plugin_tree,
            )
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

    def test_output_containing_an_input_is_rejected_without_deleting_it(self) -> None:
        output = self.root / "owned-input"
        self.prepare(output)
        nested_metadata = output / "input-package-metadata.json"
        nested_metadata.write_bytes(self.fixture.metadata.read_bytes())

        with self.assertRaises(OnboardingError) as caught:
            prepare_plugin_zip_marketplace(
                self.fixture.archive,
                nested_metadata,
                self.decisions,
                REPOSITORY,
                output,
            )

        self.assertEqual(caught.exception.code, "onboarding.output_input_overlap")
        self.assertTrue(nested_metadata.is_file())

    def test_output_below_a_protected_repository_path_is_rejected(self) -> None:
        repository = self.root / "repository"
        repository.mkdir()
        output = repository / "applications" / "sample-plugin"

        with self.assertRaises(OnboardingError) as caught:
            prepare_plugin_zip_marketplace(
                self.fixture.archive,
                self.fixture.metadata,
                self.decisions,
                repository,
                output,
            )

        self.assertEqual(caught.exception.code, "onboarding.output_protected")
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
