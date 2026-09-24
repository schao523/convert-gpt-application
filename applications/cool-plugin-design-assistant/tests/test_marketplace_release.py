from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from obvious_one_plugin_framework.marketplace import load_preparation_catalog


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class MarketplaceReleaseTests(unittest.TestCase):
    def test_obvious_one_catalog_registers_this_application_and_preserves_existing_modes(self) -> None:
        catalog = load_preparation_catalog(
            REPOSITORY / "marketplaces" / "obvious-one.json", REPOSITORY
        )
        modes = {
            entry.application.plugin_id: entry.mode for entry in catalog.applications
        }
        self.assertEqual(modes["cool-bible-tutor"], "verify_existing")
        self.assertEqual(modes["vibe-coding-designer"], "build")
        self.assertEqual(modes["cool-plugin-design-assistant"], "build")

    def test_codex_release_is_deterministic_and_allowlisted(self) -> None:
        release = load_script("build_marketplace_release.py")
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "marketplace"
            first = release.build_release(ROOT, destination, "1.0.0")
            second = release.build_release(ROOT, destination, "1.0.0")
            self.assertEqual(first.sha256, second.sha256)
            self.assertEqual(first.paths, second.paths)
            plugin = destination / "plugins" / "cool-plugin-design-assistant"
            self.assertTrue((plugin / ".codex-plugin/plugin.json").is_file())
            self.assertTrue(
                (plugin / "skills/guiding-ai-application-design-sessions/SKILL.md").is_file()
            )
            self.assertFalse((plugin / "tests").exists())
            self.assertFalse((plugin / "conversion.json").exists())
            self.assertFalse((plugin / "openclaw").exists())
            self.assertFalse(
                (plugin / "docs/marketplace-approved-delta.json").exists()
            )

    def test_codex_release_requires_rights_evidence_before_destination_mutation(self) -> None:
        release = load_script("build_marketplace_release.py")
        with tempfile.TemporaryDirectory() as temp:
            copied_source = Path(temp) / "source"
            shutil.copytree(ROOT, copied_source)
            (copied_source / "docs" / "source-decisions.md").unlink()
            destination = Path(temp) / "marketplace"
            with self.assertRaisesRegex(ValueError, "rights and provenance evidence missing"):
                release.build_release(copied_source, destination, "1.0.0")
            self.assertFalse(destination.exists())

    def test_codex_release_detects_windows_reparse_points(self) -> None:
        release = load_script("build_marketplace_release.py")
        candidate = mock.Mock()
        candidate.is_symlink.return_value = False
        candidate.stat.return_value.st_file_attributes = 0x400
        with mock.patch.object(release.os, "name", "nt"):
            self.assertTrue(release._is_link(candidate))

    def test_distribution_audit_rejects_secrets_paths_assets_and_non_allowlisted_files(
        self,
    ) -> None:
        audit = load_script("distribution_audit.py")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("safe\n", encoding="utf-8")
            self.assertEqual(audit.audit_tree(root), [])
            (root / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
            (root / "leak.md").write_text(
                "C:\\Users\\someone\\private\\source.md\n", encoding="utf-8"
            )
            (root / "raw.pdf").write_bytes(b"not-public")
            (root / "tests").mkdir()
            (root / "tests" / "private.md").write_text("private\n", encoding="utf-8")
            errors = audit.audit_tree(root)
            self.assertIn("forbidden file: .env", errors)
            self.assertIn("file outside allowlist: leak.md", errors)
            self.assertIn("forbidden source or runtime asset: raw.pdf", errors)
            self.assertIn("file outside allowlist: tests/private.md", errors)


if __name__ == "__main__":
    unittest.main()
