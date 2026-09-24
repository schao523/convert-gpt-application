from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.contract import load_contract
from obvious_one_plugin_framework.package_builder import build_package, verify_package
from obvious_one_plugin_framework.release_assets import build_asset_groups


ROOT = Path(__file__).resolve().parents[1]


def load_audit():
    path = ROOT / "scripts" / "distribution_audit.py"
    spec = importlib.util.spec_from_file_location("assistant_distribution_audit", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DistributionTests(unittest.TestCase):
    def test_distribution_is_schema_v3_text_only_and_clawhub_disabled(self) -> None:
        contract = load_contract(ROOT / "openclaw" / "distribution.json")
        self.assertEqual(contract.schema_version, 3)
        self.assertIsNone(contract.rag)
        self.assertTrue(contract.publication.github_marketplace.enabled)
        self.assertFalse(contract.publication.clawhub.enabled)
        self.assertIsNone(contract.publication.clawhub.family)
        self.assertIsNone(contract.publication.clawhub.native_manifest)
        self.assertEqual(
            contract.audit_hook,
            "scripts/distribution_audit.py:audit_distribution",
        )
        self.assertEqual(len(contract.content_rules), 1)
        self.assertEqual(contract.content_rules[0].classification, "text")

    def test_public_artifacts_exclude_tests_conversion_and_raw_sources(self) -> None:
        raw = json.loads(
            (ROOT / "openclaw" / "distribution.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("tests", raw["include_prefixes"])
        self.assertNotIn("conversion.json", raw["include_files"])
        self.assertIn("docs/marketplace-approved-delta.json", raw["exclude_paths"])
        with tempfile.TemporaryDirectory() as temp:
            contract = load_contract(ROOT / "openclaw" / "distribution.json")
            result = build_package(contract, Path(temp) / "bundle")
            public_files = [path for path in result.output.rglob("*") if path.is_file()]
            self.assertEqual(verify_package(contract, result.output), result)
            self.assertEqual(load_audit().audit_tree(result.output), [])
        self.assertFalse(
            any(path.suffix.lower() in {".pdf", ".docx", ".png"} for path in public_files)
        )

    def test_no_rag_build_is_deterministic_and_has_no_remote_assets(self) -> None:
        contract = load_contract(ROOT / "openclaw" / "distribution.json")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            one = build_package(contract, output / "one")
            two = build_package(contract, output / "two")
            self.assertEqual(one.content_sha256, two.content_sha256)
            self.assertEqual(build_asset_groups(contract, output / "assets"), ())


if __name__ == "__main__":
    unittest.main()
