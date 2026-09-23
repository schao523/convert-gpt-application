from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.contract import load_contract
from obvious_one_plugin_framework.package_builder import build_package, verify_package
from obvious_one_plugin_framework.release_assets import build_asset_groups


ROOT = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def test_distribution_is_schema_v3_with_complete_redistribution_rules(self) -> None:
        contract = load_contract(ROOT / "openclaw" / "distribution.json")

        self.assertEqual(contract.schema_version, 3)
        self.assertEqual(len(contract.content_rules), 1)
        rule = contract.content_rules[0]
        self.assertEqual(rule.classification, "text")
        self.assertEqual(rule.redistribution.status, "approved")
        self.assertEqual(rule.redistribution.provenance, "docs/source-decisions.md")
        self.assertTrue(contract.publication.github_marketplace.enabled)
        self.assertFalse(contract.publication.clawhub.enabled)
        self.assertIsNone(contract.publication.clawhub.family)
        self.assertIsNone(contract.publication.clawhub.native_manifest)
        with tempfile.TemporaryDirectory() as temp:
            result = build_package(contract, Path(temp) / "vibe")
            self.assertEqual(verify_package(contract, result.output), result)

    def test_no_rag_openclaw_build_is_deterministic_and_verified(self) -> None:
        contract = load_contract(ROOT / "openclaw" / "distribution.json")
        self.assertIsNone(contract.rag)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            one = build_package(contract, output / "one")
            two = build_package(contract, output / "two")
            self.assertEqual(one.content_sha256, two.content_sha256)
            self.assertEqual(build_asset_groups(contract, output / "assets"), ())
            self.assertEqual(verify_package(contract, one.output), one)

    def test_distribution_contract_excludes_product_tests_and_local_state(self) -> None:
        raw = json.loads(
            (ROOT / "openclaw" / "distribution.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("tests", raw["include_prefixes"])
        self.assertNotIn("conversion.local.json", raw["include_files"])
        self.assertNotIn("conversion.json", raw["include_files"])
        self.assertIn("docs/marketplace-approved-delta.json", raw["exclude_paths"])
        self.assertIsNone(raw["rag"])


if __name__ == "__main__":
    unittest.main()
