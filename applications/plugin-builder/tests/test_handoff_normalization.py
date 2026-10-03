from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile


TESTS = Path(__file__).parent
FIXTURE = TESTS / "fixtures" / "design-package-legacy"
SCRIPTS = TESTS.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from plugin_builder_core.handoff_normalization import (
    classify_handoff_profile,
    normalize_handoff_archive,
)
from plugin_builder_core.bootstrap import plugin_authoring


class HandoffNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def archive(self, source: Path, name: str = "source.zip") -> Path:
        destination = self.root / name
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as output:
            for path in sorted(source.rglob("*")):
                if path.is_file():
                    output.write(path, path.relative_to(source).as_posix())
        return destination

    def legacy_source(self, mutate=None) -> Path:
        source = self.root / f"source-{len(list(self.root.glob('source-*')))}"
        shutil.copytree(FIXTURE, source)
        manifest_path = source / "workbench_handoff_manifest.json"
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if mutate is not None:
            mutate(payload, source)
        manifest_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="ascii")
        return self.archive(source, f"{source.name}.zip")

    def normalize(self, archive: Path, name: str = "normalized"):
        return normalize_handoff_archive(archive, self.root / name, self.root / f"{name}.zip")

    def test_canonical_v1_profile_is_detected(self) -> None:
        canonical = TESTS / "fixtures" / "design-package-create"
        archive = self.archive(canonical, "canonical.zip")
        extracted = self.root / "canonical"
        inventory = plugin_authoring.extract_archive(archive, extracted)
        self.assertEqual(classify_handoff_profile(inventory, extracted).profile, "CANONICAL_V1")

    def test_legacy_workbench_v1_profile_is_detected_from_structure_and_fields(self) -> None:
        archive = self.legacy_source()
        extracted = self.root / "legacy"
        inventory = plugin_authoring.extract_archive(archive, extracted)
        self.assertEqual(classify_handoff_profile(inventory, extracted).profile, "LEGACY_WORKBENCH_V1")

    def test_unknown_profile_blocks(self) -> None:
        source = self.root / "unknown"
        source.mkdir()
        (source / "APPROVED.md").write_text("approved", encoding="utf-8")
        outcome = self.normalize(self.archive(source, "unknown.zip"))
        self.assertEqual(outcome.status, "BLOCKED")
        self.assertEqual(outcome.profile, "UNKNOWN")

    def test_multiple_authoritative_specs_are_ambiguous(self) -> None:
        def mutate(payload, source):
            duplicate = dict(payload["included_artifacts"][0])
            duplicate["artifact_id"] = "SPEC-OTHER"
            payload["included_artifacts"].append(duplicate)
        outcome = self.normalize(self.legacy_source(mutate))
        self.assertEqual((outcome.status, outcome.profile), ("BLOCKED", "AMBIGUOUS"))

    def test_legacy_profile_maps_exact_fields_and_expands_directory_artifact(self) -> None:
        outcome = self.normalize(self.legacy_source())
        self.assertEqual(outcome.status, "PASS", outcome.diagnostics)
        manifest = json.loads((self.root / "normalized/package-manifest.json").read_text(encoding="utf-8"))
        handoff = json.loads((self.root / "normalized/workbench-handoff.json").read_text(encoding="utf-8"))
        self.assertEqual((manifest["application"], manifest["spec_version"]), ("Sample Application", "v1.1"))
        expanded = next(item for item in manifest["artifacts"] if item["file"] == "professional_knowledge/reference.md")
        self.assertEqual(expanded["id"], "KNOWLEDGE-v1.1/reference.md")
        self.assertNotIn("requirements", expanded)
        self.assertEqual(handoff["approval"]["state"], "approved")

    def test_missing_approval_evidence_remains_pending(self) -> None:
        outcome = self.normalize(self.legacy_source(lambda payload, source: payload.__setitem__("approval_evidence", "")))
        self.assertEqual(outcome.status, "BLOCKED")
        self.assertFalse((self.root / "normalized").exists())

    def test_blocking_owner_decision_prevents_approval(self) -> None:
        def mutate(payload, source):
            payload["unresolved_owner_decisions"] = [{"decision_id": "D1", "blocking": True, "owner": "owner", "summary": "Choose", "impact": "scope"}]
        outcome = self.normalize(self.legacy_source(mutate))
        self.assertEqual(outcome.status, "BLOCKED")

    def test_malformed_authority_metadata_never_establishes_approval(self) -> None:
        mutations = (
            lambda payload, source: payload["included_artifacts"][0].__setitem__("artifact_id", ""),
            lambda payload, source: payload["included_artifacts"][0].__setitem__("provenance", ""),
            lambda payload, source: payload["included_artifacts"][0].__setitem__("state", "draft"),
            lambda payload, source: payload["included_artifacts"][0].__setitem__("version", 11),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                outcome = self.normalize(self.legacy_source(mutate), f"bad-authority-{index}")
                self.assertEqual(outcome.status, "BLOCKED")
                self.assertTrue(any("artifact_" in item for item in outcome.diagnostics))

    def test_malformed_owner_decisions_never_default_to_non_blocking(self) -> None:
        malformed = ("not-a-list", ["not-an-object"], [{"decision_id": "D1", "blocking": "false"}])
        for index, decisions in enumerate(malformed):
            with self.subTest(index=index):
                outcome = self.normalize(
                    self.legacy_source(lambda payload, source, value=decisions: payload.__setitem__("unresolved_owner_decisions", value)),
                    f"bad-decisions-{index}",
                )
                self.assertEqual(outcome.status, "BLOCKED")
                self.assertTrue(any("owner_decision" in item for item in outcome.diagnostics))

    def test_filename_approved_does_not_establish_approval(self) -> None:
        outcome = self.normalize(self.legacy_source(lambda payload, source: payload.__setitem__("specification_state", "draft")))
        self.assertEqual(outcome.status, "BLOCKED")

    def test_confirmed_by_is_a_role_not_a_fabricated_person(self) -> None:
        self.assertEqual(self.normalize(self.legacy_source()).status, "PASS")
        handoff = json.loads((self.root / "normalized/workbench-handoff.json").read_text(encoding="utf-8"))
        self.assertEqual(handoff["approval"]["confirmed_by"], "decision owner recorded by legacy handoff")

    def test_original_members_are_byte_identical_after_normalization(self) -> None:
        archive = self.legacy_source()
        source_hash = archive.read_bytes()
        original = plugin_authoring.inventory_archive(archive)
        self.assertIn(self.normalize(archive).status, {"PASS", "BLOCKED"})
        normalized = plugin_authoring.inventory_archive(self.root / "normalized.zip")
        by_path = {item.path: item.sha256 for item in normalized.members}
        self.assertTrue(all(
            by_path[item.path] == item.sha256
            for item in original.members
            if item.path != "workbench_handoff_manifest.json"
        ))
        self.assertEqual(archive.read_bytes(), source_hash)

    def test_canonical_filename_collision_blocks_without_overwrite(self) -> None:
        def mutate(payload, source):
            (source / "package-manifest.json").write_text("owner bytes", encoding="utf-8")
        archive = self.legacy_source(mutate)
        before = archive.read_bytes()
        outcome = self.normalize(archive)
        self.assertEqual(outcome.status, "BLOCKED")
        self.assertFalse((self.root / "normalized").exists())
        self.assertEqual(archive.read_bytes(), before)

    def test_empty_or_escaping_declared_prefix_blocks(self) -> None:
        for path in ("", "../escape/"):
            with self.subTest(path=path):
                def mutate(payload, source, value=path):
                    payload["included_artifacts"][1]["path"] = value
                outcome = self.normalize(self.legacy_source(mutate), f"bad-{len(list(self.root.glob('bad-*')))}")
                self.assertEqual(outcome.status, "BLOCKED")

    def test_repeated_normalization_is_byte_identical(self) -> None:
        archive = self.legacy_source()
        first = self.normalize(archive, "first")
        second = self.normalize(archive, "second")
        self.assertEqual((first.status, first.output_archive_sha256), (second.status, second.output_archive_sha256))
        self.assertEqual((self.root / "first.zip").read_bytes(), (self.root / "second.zip").read_bytes())


if __name__ == "__main__":
    unittest.main()
