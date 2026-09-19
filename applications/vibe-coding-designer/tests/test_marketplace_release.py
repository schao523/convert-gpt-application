from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class MarketplaceReleaseTests(unittest.TestCase):
    def test_codex_release_is_deterministic_and_allowlisted(self) -> None:
        release = load_script("build_marketplace_release.py")
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "marketplace"
            first = release.build_release(ROOT, destination, "1.0.0")
            second = release.build_release(ROOT, destination, "1.0.0")
            self.assertEqual(first.sha256, second.sha256)
            self.assertEqual(first.paths, second.paths)
            plugin = destination / "plugins" / "vibe-coding-designer"
            self.assertTrue((plugin / ".codex-plugin/plugin.json").is_file())
            self.assertTrue((plugin / "skills/guiding-vibe-design-sessions/SKILL.md").is_file())
            self.assertFalse((plugin / "tests").exists())
            self.assertFalse((plugin / "conversion.json").exists())
            self.assertFalse((plugin / "openclaw").exists())

    def test_distribution_audit_rejects_secrets_and_user_paths(self) -> None:
        audit = load_script("distribution_audit.py")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "safe.md").write_text("safe\n", encoding="utf-8")
            self.assertEqual(audit.audit_tree(root), [])
            (root / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
            (root / "leak.md").write_text(
                "C:\\Users\\someone\\private\\source.md\n", encoding="utf-8"
            )
            errors = audit.audit_tree(root)
            self.assertIn("forbidden file: .env", errors)
            self.assertIn("absolute Windows user path: leak.md", errors)


if __name__ == "__main__":
    unittest.main()
