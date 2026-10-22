from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework import plugin_authoring
from obvious_one_plugin_framework.plugin_onboarding import (
    PortableContentManifestAdoption,
    inspect_portable_content_manifest_package,
    load_portable_content_manifest_adoption,
)
from obvious_one_plugin_framework.plugin_onboarding.materialize import (
    prepare_plugin_zip_marketplace,
)
from tests.framework.plugin_onboarding_fixtures import (
    canonical_bytes,
    write_publication_decisions,
)


REPOSITORY = Path(__file__).resolve().parents[2]


class PortableContentManifestOnboardingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_fixture(
        self, name: str = "fixture"
    ) -> tuple[Path, Path, Path, dict[str, object]]:
        plugin_id = "sample-plugin"
        fixture_root = self.root / name
        fixture_root.mkdir()
        candidate = fixture_root / "candidate"
        (candidate / ".codex-plugin").mkdir(parents=True)
        (candidate / "skills" / "sample").mkdir(parents=True)
        interface = {
            "displayName": "Sample Plugin",
            "shortDescription": "Portable sample",
            "longDescription": "A portable sample plugin for compatibility tests.",
            "developerName": "Example Developer",
            "category": "Education",
            "capabilities": ["Interactive", "Read"],
            "defaultPrompt": "Help me use this plugin.",
        }
        (candidate / "plugin.json").write_bytes(
            canonical_bytes(
                {
                    "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                    "name": plugin_id,
                    "version": "1.0.1",
                    "description": "A portable sample plugin.",
                    "author": {"name": "Example Developer"},
                    "extensions": {"com.openai": {"interface": interface}},
                }
            )
        )
        (candidate / ".codex-plugin" / "plugin.json").write_bytes(
            canonical_bytes(
                {
                    "name": plugin_id,
                    "version": "1.0.1",
                    "description": "A portable sample plugin.",
                    "author": {"name": "Example Developer"},
                    "skills": "./skills/",
                    "interface": interface,
                }
            )
        )
        (candidate / "skills" / "sample" / "SKILL.md").write_text(
            "---\nname: sample\ndescription: Exercise a sample workflow.\n---\n\nReturn a sample result.\n",
            encoding="utf-8",
            newline="\n",
        )
        payload_members = [
            asdict(member) for member in plugin_authoring.tree_manifest(candidate)
        ]
        content_manifest = {
            "plugin_id": plugin_id,
            "version": "1.0.1",
            "source_handoff_contract": "WORKBENCH_HANDOFF_V1_1",
            "approved_spec": "approved-spec.md",
            "applied_delta": "approved-delta.md",
            "skills": ["sample"],
            "files": payload_members,
        }
        content_manifest_path = candidate / "content-manifest.json"
        content_manifest_path.write_bytes(canonical_bytes(content_manifest))
        archive = fixture_root / "sample-plugin.zip"
        archive_sha256 = plugin_authoring.write_deterministic_zip(
            candidate, archive, prefix=plugin_id
        )
        inventory = plugin_authoring.inventory_archive(archive)
        members = [asdict(member) for member in inventory.members]
        adoption_payload: dict[str, object] = {
            "schema": "workbench-portable-content-manifest-adoption-v1",
            "input_profile": "PLUGIN_BUILDER_PORTABLE_CONTENT_MANIFEST_V1",
            "plugin_id": plugin_id,
            "version": "1.0.1",
            "archive_sha256": archive_sha256,
            "member_manifest_sha256": sha256(canonical_bytes(members)).hexdigest(),
            "members": members,
            "content_tree_sha256": plugin_authoring.tree_sha256(candidate),
            "content_manifest_path": "content-manifest.json",
            "content_manifest_sha256": sha256(
                content_manifest_path.read_bytes()
            ).hexdigest(),
            "executable_files": [],
            "dependency_files": [],
            "adoption_approved": True,
            "confirmed_by": "Plugin Owner",
            "decision_recorded_at": "2026-10-22T22:00:00+08:00",
            "purpose": "OBVIOUS_ONE_CODEX_MARKETPLACE_ONBOARDING",
        }
        adoption = fixture_root / "adoption.json"
        adoption.write_bytes(canonical_bytes(adoption_payload))
        return candidate, archive, adoption, adoption_payload

    def rebuild_fixture(
        self,
        candidate: Path,
        archive: Path,
        adoption: Path,
        *,
        refresh_content_members: bool = True,
    ) -> None:
        manifest_path = candidate / "content-manifest.json"
        if refresh_content_members:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"] = [
                asdict(member)
                for member in plugin_authoring.tree_manifest(candidate)
                if member.path != "content-manifest.json"
            ]
            manifest_path.write_bytes(canonical_bytes(manifest))
        archive_sha256 = plugin_authoring.write_deterministic_zip(
            candidate, archive, prefix="sample-plugin"
        )
        inventory = plugin_authoring.inventory_archive(archive)
        members = [asdict(member) for member in inventory.members]
        authority = json.loads(adoption.read_text(encoding="utf-8"))
        authority.update(
            {
                "archive_sha256": archive_sha256,
                "member_manifest_sha256": sha256(canonical_bytes(members)).hexdigest(),
                "members": members,
                "content_tree_sha256": plugin_authoring.tree_sha256(candidate),
                "content_manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
            }
        )
        adoption.write_bytes(canonical_bytes(authority))

    def test_exact_wrapped_content_manifest_package_is_statically_verified(self) -> None:
        _, archive, adoption_path, adoption_payload = self.write_fixture()

        adoption = load_portable_content_manifest_adoption(adoption_path)
        inspection = inspect_portable_content_manifest_package(archive, adoption)

        self.assertIsInstance(adoption, PortableContentManifestAdoption)
        self.assertEqual(
            inspection.input_profile,
            "PLUGIN_BUILDER_PORTABLE_CONTENT_MANIFEST_V1",
        )
        self.assertEqual(inspection.package_state, "STATICALLY VERIFIED")
        self.assertEqual(inspection.archive_sha256, adoption_payload["archive_sha256"])
        self.assertEqual(set(inspection.evidence_states.values()), {"NOT VERIFIED"})
        self.assertEqual(inspection.runtime_realization_state, "NOT VERIFIED")
        self.assertEqual(inspection.approved_executable_files, ())
        self.assertEqual(inspection.approved_dependency_files, ())
        self.assertEqual(
            inspection.producer_claims["source_handoff_contract"],
            "WORKBENCH_HANDOFF_V1_1",
        )

    def test_exact_wrapped_package_materializes_without_changing_imported_bytes(self) -> None:
        _, archive, adoption_path, _ = self.write_fixture()
        decisions = write_publication_decisions(
            self.root / "decisions.json",
            overrides={"version": "1.0.1"},
        )
        output = self.root / "proposal"

        result = prepare_plugin_zip_marketplace(
            archive,
            None,
            decisions,
            REPOSITORY,
            output,
            legacy_adoption=adoption_path,
        )

        self.assertEqual(result.status, "PASS")
        imported = output / "application" / "imported-plugin"
        with tempfile.TemporaryDirectory() as extraction:
            extracted = Path(extraction)
            plugin_authoring.extract_archive(archive, extracted)
            original = extracted / "sample-plugin"
            self.assertEqual(
                plugin_authoring.tree_manifest(imported),
                plugin_authoring.tree_manifest(original),
            )
        proposal = json.loads(
            (output / "onboarding-proposal.json").read_text(encoding="ascii")
        )
        self.assertEqual(
            proposal["builder_evidence"]["input_profile"],
            "PLUGIN_BUILDER_PORTABLE_CONTENT_MANIFEST_V1",
        )

    def test_changed_archive_bytes_are_rejected_by_exact_adoption(self) -> None:
        candidate, archive, adoption_path, _ = self.write_fixture()
        (candidate / "skills" / "sample" / "SKILL.md").write_bytes(b"changed\n")
        plugin_authoring.write_deterministic_zip(
            candidate, archive, prefix="sample-plugin"
        )

        with self.assertRaisesRegex(Exception, "archive_sha256_mismatch"):
            inspect_portable_content_manifest_package(
                archive, load_portable_content_manifest_adoption(adoption_path)
            )

    def test_incomplete_content_manifest_is_rejected_after_outer_rebinding(self) -> None:
        candidate, archive, adoption_path, _ = self.write_fixture()
        manifest_path = candidate / "content-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"] = manifest["files"][1:]
        manifest_path.write_bytes(canonical_bytes(manifest))
        self.rebuild_fixture(
            candidate,
            archive,
            adoption_path,
            refresh_content_members=False,
        )

        with self.assertRaisesRegex(Exception, "content_manifest_members_mismatch"):
            inspect_portable_content_manifest_package(
                archive, load_portable_content_manifest_adoption(adoption_path)
            )

    def test_mixed_authority_is_rejected(self) -> None:
        candidate, archive, adoption_path, _ = self.write_fixture()
        (candidate / "PLUGIN-BUILDER-MANIFEST.json").write_bytes(b"{}\n")
        self.rebuild_fixture(candidate, archive, adoption_path)

        with self.assertRaisesRegex(Exception, "authority_ambiguous"):
            inspect_portable_content_manifest_package(
                archive, load_portable_content_manifest_adoption(adoption_path)
            )

    def test_secret_and_undeclared_executable_are_rejected(self) -> None:
        for name, content, expected in (
            ("secret.md", b"api_key=not-a-real-key\n", "credential_material_forbidden"),
            ("helper.py", b"print('sample')\n", "executable_files_mismatch"),
        ):
            with self.subTest(name=name):
                candidate, archive, adoption_path, _ = self.write_fixture(name)
                (candidate / name).write_bytes(content)
                self.rebuild_fixture(candidate, archive, adoption_path)
                with self.assertRaisesRegex(Exception, expected):
                    inspect_portable_content_manifest_package(
                        archive,
                        load_portable_content_manifest_adoption(adoption_path),
                    )

    def test_historical_reference_link_omissions_are_recorded_not_rewritten(self) -> None:
        candidate, archive, adoption_path, _ = self.write_fixture()
        reference = candidate / "skills" / "sample" / "references" / "guide.md"
        reference.parent.mkdir()
        reference.write_text("# Guide\n", encoding="utf-8", newline="\n")
        self.rebuild_fixture(candidate, archive, adoption_path)

        inspection = inspect_portable_content_manifest_package(
            archive, load_portable_content_manifest_adoption(adoption_path)
        )

        self.assertEqual(inspection.package_state, "STATICALLY VERIFIED")
        self.assertEqual(
            inspection.producer_claims["structural_validation_issues"],
            (
                {
                    "code": "professional_reference_unlinked",
                    "path": "skills/sample/references/guide.md",
                    "detail": "",
                },
            ),
        )


if __name__ == "__main__":
    unittest.main()
