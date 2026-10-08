from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC = ROOT / "tests/runtime/verify-installed-identity.py"


class InstalledIdentityDiagnosticTests(unittest.TestCase):
    def test_observed_manifest_variant_never_becomes_byte_identity_pass(self) -> None:
        self.assertTrue(DIAGNOSTIC.is_file())
        spec = importlib.util.spec_from_file_location("installed_identity_diagnostic", DIAGNOSTIC)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reviewed = root / "reviewed.zip"
            installed = root / "installed"
            installed.mkdir()
            source_manifest = {
                "name": "plugin-builder", "version": "1.0.1", "skills": "./skills/",
                "interface": {"displayName": "Plugin Builder"},
            }
            source_bytes = (json.dumps(source_manifest, separators=(",", ":")) + "\n").encode()
            with zipfile.ZipFile(reviewed, "w") as archive:
                archive.writestr(".codex-plugin/plugin.json", source_bytes)
                archive.writestr("skills/example/SKILL.md", b"# Example\n")
            (installed / ".codex-plugin").mkdir()
            (installed / "skills/example").mkdir(parents=True)
            (installed / "skills/example/SKILL.md").write_bytes(b"# Example\n")

            (installed / ".codex-plugin/plugin.json").write_bytes(source_bytes)
            exact = module.reconcile(reviewed, installed)
            self.assertEqual(exact["status"], "PASS")
            self.assertEqual(exact["installed_byte_identity"], "PASS")

            observed = dict(source_manifest, skills="./skills", keywords=[])
            (installed / ".codex-plugin/plugin.json").write_text(
                json.dumps(observed, indent=2) + "\n", encoding="utf-8"
            )
            variant = module.reconcile(reviewed, installed)
            self.assertEqual(variant["status"], "NOT VERIFIED")
            self.assertEqual(variant["installed_byte_identity"], "FAIL")
            self.assertEqual(variant["manifest_reconciliation"], "OBSERVED_VARIANT_ONLY")
            self.assertEqual(variant["normalization_cause"], "NOT VERIFIED")
            self.assertEqual(variant["other_member_mismatches"], [])

            observed["interface"]["displayName"] = "Different Plugin"
            (installed / ".codex-plugin/plugin.json").write_text(
                json.dumps(observed) + "\n", encoding="utf-8"
            )
            changed_behavior = module.reconcile(reviewed, installed)
            self.assertEqual(changed_behavior["status"], "BLOCKED")

            (installed / ".codex-plugin/plugin.json").write_bytes(source_bytes)
            (installed / "skills/example/SKILL.md").write_bytes(b"# Changed\n")
            changed_skill = module.reconcile(reviewed, installed)
            self.assertEqual(changed_skill["status"], "BLOCKED")
            self.assertEqual(changed_skill["other_member_mismatches"], ["skills/example/SKILL.md"])

            (installed / "skills/example/SKILL.md").write_bytes(b"# Example\n")
            (installed / "unexpected.txt").write_text("extra", encoding="utf-8")
            extra_member = module.reconcile(reviewed, installed)
            self.assertEqual(extra_member["status"], "BLOCKED")
            self.assertEqual(extra_member["extra_members"], ["unexpected.txt"])

    def test_missing_codex_manifest_cannot_pass_even_with_exact_members(self) -> None:
        self.assertTrue(DIAGNOSTIC.is_file())
        spec = importlib.util.spec_from_file_location("installed_identity_no_manifest", DIAGNOSTIC)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reviewed = root / "reviewed.zip"
            installed = root / "installed"
            installed.mkdir()
            with zipfile.ZipFile(reviewed, "w") as archive:
                archive.writestr("skills/example/SKILL.md", b"# Example\n")
            (installed / "skills/example").mkdir(parents=True)
            (installed / "skills/example/SKILL.md").write_bytes(b"# Example\n")
            self.assertEqual(module.reconcile(reviewed, installed)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
