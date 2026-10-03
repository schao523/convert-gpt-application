from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from obvious_one_plugin_framework.contract import load_contract
from obvious_one_plugin_framework.package_builder import build_package, verify_package
from obvious_one_plugin_framework.release_assets import build_asset_groups


ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = ROOT.parents[1] / ".tmp" / "plugin-builder-distribution-tests"
PUBLIC_DOCS = {
    "docs/application-invariants.md",
    "docs/runtime-compatibility.md",
}
ROOT_PUBLIC_FILES = {
    "plugin.json",
    ".codex-plugin/plugin.json",
    "README.md",
    "DISTRIBUTION.md",
    "LICENSE",
    "PRIVACY.md",
    "SECURITY.md",
    "THIRD_PARTY_CONTENT.md",
    "THIRD_PARTY_NOTICES.md",
}
INTERNAL_PATHS = {
    "conversion.json",
    "docs/phase-one-scope.json",
    "docs/source-decisions.md",
    "docs/source-inventory.json",
}


def load_audit():
    path = ROOT / "scripts" / "distribution_audit.py"
    spec = importlib.util.spec_from_file_location("plugin_builder_distribution_audit", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load audit module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)

    def test_contract_is_disabled_text_only_and_explicit(self) -> None:
        raw = json.loads(
            (ROOT / "openclaw" / "distribution.json").read_text(encoding="utf-8")
        )
        contract = load_contract(ROOT / "openclaw" / "distribution.json")

        self.assertEqual(contract.schema_version, 3)
        self.assertIsNone(contract.rag)
        self.assertTrue(contract.publication.github_marketplace.enabled)
        self.assertFalse(contract.publication.clawhub.enabled)
        self.assertEqual(raw["version"], "0.1.3")
        self.assertEqual(raw["release_repository"], "schao523/obvious-one-plugins")
        self.assertEqual(
            contract.audit_hook,
            "scripts/distribution_audit.py:audit_distribution",
        )
        self.assertEqual(set(raw["include_files"]), ROOT_PUBLIC_FILES | PUBLIC_DOCS)
        self.assertEqual(set(raw["include_prefixes"]), {"scripts", "skills"})
        self.assertNotIn("docs", raw["include_prefixes"])
        self.assertEqual(len(contract.content_rules), 1)
        rule = raw["content_rules"][0]
        self.assertEqual(rule["classification"], "text")
        self.assertEqual(set(rule["paths"]), ROOT_PUBLIC_FILES | PUBLIC_DOCS)
        self.assertEqual(set(rule["prefixes"]), {"scripts", "skills"})

    def test_source_boundary_ignores_internal_inputs_but_built_tree_rejects_them(self) -> None:
        audit = load_audit()
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
            root = Path(temp)
            (root / "README.md").write_text("Public documentation.\n", encoding="utf-8")
            for relative in INTERNAL_PATHS | {"docs/approved-design/source.md", "tests/test_private.py"}:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("internal\n", encoding="utf-8")

            self.assertEqual(audit.audit_public_source(root), [])
            errors = audit.audit_tree(root)
            for relative in INTERNAL_PATHS | {"docs/approved-design/source.md", "tests/test_private.py"}:
                self.assertTrue(any(relative in error for error in errors), relative)

    def test_audit_rejects_each_unsafe_public_content_class(self) -> None:
        audit = load_audit()
        cases = {
            "secret": ("scripts/leak.py", 'token = "ghp_abcdefghijklmnopqrstuvwxyz123456"\n', "secret_pattern"),
            "private path": ("scripts/path.txt", "C:\\Users\\Someone\\private.txt\n", "private_path"),
            "binary attachment": ("skills/example/source.pdf", b"%PDF-1.7", "unsafe_suffix"),
            "broken link": ("README.md", "[missing](docs/not-present.md)\n", "broken_markdown_link"),
            "scaffold": ("README.md", "[TODO: replace this]\n", "scaffold_marker"),
        }
        for label, (relative, content, code) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
                root = Path(temp)
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(content, bytes):
                    path.write_bytes(content)
                else:
                    path.write_text(content, encoding="utf-8")
                errors = audit.audit_tree(root)
                self.assertTrue(any(code in error for error in errors), errors)

    def test_audit_rejects_symbolic_links_when_supported(self) -> None:
        audit = load_audit()
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
            root = Path(temp)
            target = root / "target.txt"
            target.write_text("target\n", encoding="utf-8")
            link = root / "README.md"
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symbolic links unavailable: {exc}")
            errors = audit.audit_tree(root)
            self.assertTrue(any("link_forbidden" in error for error in errors), errors)

    def test_windows_reparse_points_are_classified_as_links(self) -> None:
        audit = load_audit()
        candidate = mock.Mock()
        candidate.is_symlink.return_value = False
        candidate.stat.return_value.st_file_attributes = 0x400
        with mock.patch.object(audit.os, "name", "nt"):
            self.assertTrue(audit._is_link(candidate))

    def test_framework_package_is_deterministic_allowlisted_and_asset_free(self) -> None:
        contract = load_contract(ROOT / "openclaw" / "distribution.json")
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
            output = Path(temp)
            one = build_package(contract, output / "one")
            two = build_package(contract, output / "two")
            self.assertEqual(one.content_sha256, two.content_sha256)
            self.assertEqual(verify_package(contract, one.output), one)
            self.assertEqual(load_audit().audit_tree(one.output), [])
            self.assertEqual(build_asset_groups(contract, output / "assets"), ())
            members = {
                path.relative_to(one.output).as_posix()
                for path in one.output.rglob("*")
                if path.is_file()
            }

        self.assertTrue(ROOT_PUBLIC_FILES | PUBLIC_DOCS <= members)
        self.assertIn("package.json", members)
        self.assertIn("CONTENT-MANIFEST.json", members)
        for internal in INTERNAL_PATHS:
            self.assertNotIn(internal, members)
        self.assertFalse(any(path.startswith("tests/") for path in members))
        self.assertFalse(any(path.startswith("docs/approved-design/") for path in members))
        self.assertFalse(any("__pycache__" in path for path in members))
        self.assertFalse(any(Path(path).suffix.lower() in {".pdf", ".docx", ".zip", ".png"} for path in members))


if __name__ == "__main__":
    unittest.main()
