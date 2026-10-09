from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

from obvious_one_plugin_framework import plugin_authoring
from obvious_one_plugin_framework.marketplace import (
    MarketplaceError,
    load_preparation_catalog,
    prepare_marketplace,
    verify_marketplace,
)
from obvious_one_plugin_framework.plugin_onboarding import prepare_plugin_zip_marketplace
from tests.framework.plugin_onboarding_fixtures import (
    canonical_bytes,
    write_plugin_builder_fixture,
    write_publication_decisions,
)


WORKBENCH = Path(__file__).resolve().parents[2]


class PluginOnboardingMarketplaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.fixture = write_plugin_builder_fixture(self.root / "package")
        self.decisions = write_publication_decisions(self.root / "decisions.json")
        self.proposal = self.root / "proposal"
        prepare_plugin_zip_marketplace(
            self.fixture.archive,
            self.fixture.metadata,
            self.decisions,
            WORKBENCH,
            self.proposal,
        )
        self.repository = self.root / "repository"
        application = self.repository / "applications" / "sample-plugin"
        application.parent.mkdir(parents=True)
        shutil.copytree(self.proposal / "application", application)
        catalog_entry = json.loads((self.proposal / "catalog-entry.json").read_text(encoding="ascii"))
        catalog_path = self.repository / "marketplaces" / "obvious-one.json"
        catalog_path.parent.mkdir(parents=True)
        catalog_path.write_bytes(
            canonical_bytes(
                {
                    "schema_version": 2,
                    "marketplace_id": "obvious-one",
                    "applications": [catalog_entry],
                }
            )
        )
        self.catalog_path = catalog_path
        self.baseline = self.root / "marketplace-baseline"
        self.baseline.mkdir()

    def git(self, root: Path, *arguments: str) -> None:
        subprocess.run(
            ["git", *arguments], cwd=root, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def test_owner_adopted_registration_passes_unchanged_marketplace_pipeline(self) -> None:
        catalog = load_preparation_catalog(self.catalog_path, self.repository)
        application = self.repository / "applications" / "sample-plugin"
        for test in ("test_imported_package.py", "test_marketplace_release.py"):
            completed = subprocess.run(
                [sys.executable, "-B", str(application / "tests" / test)],
                cwd=application,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout)

        first = self.root / "marketplace-first"
        second = self.root / "marketplace-second"
        baseline_before = plugin_authoring.tree_sha256(self.baseline)
        repository_before = plugin_authoring.tree_sha256(self.repository)
        first_result = prepare_marketplace(catalog, self.baseline, first)
        second_result = prepare_marketplace(catalog, self.baseline, second)
        self.assertEqual(first_result.status, "PASS")
        self.assertEqual(first_result.artifacts[0].sha256, second_result.artifacts[0].sha256)
        self.assertEqual(plugin_authoring.tree_sha256(first), plugin_authoring.tree_sha256(second))
        self.assertEqual(plugin_authoring.tree_sha256(self.baseline), baseline_before)
        self.assertEqual(plugin_authoring.tree_sha256(self.repository), repository_before)
        filesystem_verification = verify_marketplace(catalog, first)
        verifier_probe = subprocess.run(
            [
                sys.executable,
                "-B",
                str(first / "tools" / "verify_marketplace.py"),
                "--registry",
                str(first / ".obvious-one-validation.json"),
                "--plugin",
                "sample-plugin",
                "--json",
            ],
            cwd=first,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(
            filesystem_verification.status,
            "PASS",
            (filesystem_verification.evidence, verifier_probe.stdout),
        )
        self.assertTrue((first / "plugins/sample-plugin/.codex-plugin/plugin.json").is_file())
        self.assertFalse((first / "openclaw/sample-plugin").exists())

        self.git(first, "init")
        self.git(first, "config", "user.email", "tests@example.invalid")
        self.git(first, "config", "user.name", "Framework Tests")
        self.git(first, "config", "core.autocrlf", "false")
        self.git(first, "add", ".")
        self.git(first, "commit", "-m", "onboarded plugin")
        verified = verify_marketplace(
            catalog, first, check_index=True, commit="HEAD", fresh_checkout=True
        )
        self.assertEqual(verified.status, "PASS")
        self.assertEqual(
            verified.evidence["gates"],
            {"filesystem": "PASS", "index": "PASS", "commit": "PASS", "fresh_checkout": "PASS"},
        )

    def test_imported_crlf_utf8_and_binary_bytes_survive_onboarding_and_codex_build(self) -> None:
        files = self.fixture.candidate_files
        files.update(
            {
                "notes/windows.txt": b"first\r\nsecond\r\n",
                "notes/unicode.txt": "完整保留\n".encode("utf-8"),
                "assets/blob.bin": b"\x00\xff\x10\x80",
            }
        )
        fixture = write_plugin_builder_fixture(self.root / "bytes", files=files)
        proposal = self.root / "bytes-proposal"
        prepare_plugin_zip_marketplace(
            fixture.archive, fixture.metadata, self.decisions, WORKBENCH, proposal
        )
        imported = proposal / "application" / "imported-plugin"
        for relative, content in files.items():
            self.assertEqual(imported.joinpath(*relative.split("/")).read_bytes(), content)
        built_root = self.root / "direct-build"
        completed = subprocess.run(
            [
                sys.executable, "-B",
                str(proposal / "application/scripts/build_marketplace_release.py"),
                "--source", str(proposal / "application"),
                "--destination", str(built_root),
                "--version", "1.2.3",
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        built = built_root / "plugins" / "sample-plugin"
        self.assertEqual(plugin_authoring.tree_manifest(built), plugin_authoring.tree_manifest(fixture.candidate))

    def test_codex_build_rejects_any_imported_tree_drift_before_replacement(self) -> None:
        application = self.proposal / "application"
        imported_skill = (
            application
            / "imported-plugin"
            / "skills"
            / "sample"
            / "SKILL.md"
        )
        imported_skill.write_bytes(imported_skill.read_bytes() + b"\nchanged\n")
        built_root = self.root / "drifted-build"

        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(application / "scripts" / "build_marketplace_release.py"),
                "--source",
                str(application),
                "--destination",
                str(built_root),
                "--version",
                "1.2.3",
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("imported_plugin_tree_mismatch", completed.stdout)
        self.assertFalse((built_root / "plugins" / "sample-plugin").exists())

    def test_not_applicable_openclaw_collision_fails_without_mutation(self) -> None:
        stale = self.baseline / "openclaw" / "sample-plugin"
        stale.mkdir(parents=True)
        (stale / "keep.bin").write_bytes(b"keep")
        runtime_catalog = self.baseline / ".claude-plugin" / "marketplace.json"
        runtime_catalog.parent.mkdir(parents=True)
        runtime_catalog.write_bytes(
            canonical_bytes(
                {
                    "plugins": [
                        {
                            "name": "sample-plugin",
                            "version": "1.2.2",
                            "source": "./openclaw/sample-plugin",
                        }
                    ]
                }
            )
        )
        baseline_before = plugin_authoring.tree_sha256(self.baseline)
        catalog = load_preparation_catalog(self.catalog_path, self.repository)
        with self.assertRaises(MarketplaceError) as caught:
            prepare_marketplace(catalog, self.baseline, self.root / "blocked")
        self.assertEqual(caught.exception.code, "not_applicable_target_already_published")
        self.assertEqual(plugin_authoring.tree_sha256(self.baseline), baseline_before)
        self.assertFalse((self.root / "blocked").exists())

    @unittest.skipUnless(os.name == "nt", "Windows read-only directory semantics")
    def test_readonly_baseline_is_not_mutated(self) -> None:
        keep = self.baseline / "unchanged"
        keep.mkdir()
        (keep / "keep.txt").write_bytes(b"keep\r\n")
        keep.chmod(stat.S_IREAD)
        self.addCleanup(keep.chmod, stat.S_IREAD | stat.S_IWRITE)
        before = (keep / "keep.txt").read_bytes()
        catalog = load_preparation_catalog(self.catalog_path, self.repository)
        result = prepare_marketplace(catalog, self.baseline, self.root / "readonly-stage")
        self.assertEqual(result.status, "PASS")
        self.assertEqual((keep / "keep.txt").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
