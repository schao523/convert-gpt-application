from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from obvious_one_plugin_framework.contract import load_contract
from obvious_one_plugin_framework.package_builder import (
    PackageAuditError,
    build_package,
    verify_package,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class PackageBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)

    def contract(self, name: str = "plugin-alpha"):
        return load_contract(FIXTURES / name / "distribution.json")

    def test_builder_vendors_bootstrap_into_each_plugin(self) -> None:
        for name in ("plugin-alpha", "plugin-beta"):
            result = build_package(self.contract(name), self.output / name)
            bootstrap = (
                result.output
                / "vendor/obvious-one-runtime/obvious_one_runtime/status.py"
            )
            self.assertTrue(bootstrap.is_file())
            self.assertTrue((result.output / ".codex-plugin/plugin.json").is_file())
            self.assertFalse((result.output / "openclaw.plugin.json").exists())

    def test_repeat_build_has_identical_content_identity(self) -> None:
        one = build_package(self.contract(), self.output / "one")
        two = build_package(self.contract(), self.output / "two")
        self.assertEqual(one.content_sha256, two.content_sha256)
        self.assertEqual(
            (one.output / "CONTENT-MANIFEST.json").read_bytes(),
            (two.output / "CONTENT-MANIFEST.json").read_bytes(),
        )
        self.assertEqual(verify_package(self.contract(), one.output), one)

    def test_failed_audit_preserves_previous_output(self) -> None:
        contract = self.contract()
        target = self.output / "alpha"
        before = build_package(contract, target)
        source = self.output / "unsafe-source"
        shutil.copytree(contract.source_root, source)
        (source / "unsafe").mkdir()
        (source / "unsafe/.env").write_text("TOKEN=secret", encoding="utf-8")
        unsafe = replace(contract, source_root=source, include_prefixes=("unsafe",))
        with self.assertRaisesRegex(PackageAuditError, "forbidden_file"):
            build_package(unsafe, target)
        self.assertEqual(verify_package(contract, target).content_sha256, before.content_sha256)

    def test_package_json_uses_bundle_identity(self) -> None:
        result = build_package(self.contract(), self.output / "alpha")
        package = json.loads((result.output / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["name"], "@obvious-one/plugin-alpha")
        self.assertEqual(package["version"], "1.0.0")
        self.assertEqual(package["openclaw"]["family"], "bundle-plugin")
        self.assertNotIn("main", package)

    def test_declared_product_audit_hook_is_enforced(self) -> None:
        contract = self.contract()
        source = self.output / "hook-source"
        shutil.copytree(contract.source_root, source)
        (source / "audit_hook.py").write_text(
            "def audit(stage, contract):\n    raise ValueError('hook_seen')\n",
            encoding="utf-8",
        )
        hooked = replace(
            contract,
            source_root=source,
            audit_hook="audit_hook.py:audit",
        )
        with self.assertRaisesRegex(PackageAuditError, "product_audit_failed.*hook_seen"):
            build_package(hooked, self.output / "hooked")


if __name__ == "__main__":
    unittest.main()
