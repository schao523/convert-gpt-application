from __future__ import annotations

import json
from pathlib import Path
import unittest

from obvious_one_plugin_framework.plugin_onboarding import load_repair_contract


APPLICATION = Path(__file__).resolve().parents[1]


class GrowingWithChildrenRepairContractTests(unittest.TestCase):
    def test_owner_approved_product_contract_is_exact(self) -> None:
        conversion = json.loads((APPLICATION / "conversion.json").read_text(encoding="utf-8"))
        contract = load_repair_contract(
            APPLICATION / "repair" / "delegated-reference-repair-v1.json"
        )

        self.assertEqual(conversion["schema_version"], 2)
        self.assertEqual(conversion["application_id"], "growing-with-children")
        self.assertEqual(conversion["plugin_id"], "growing-with-children")
        self.assertEqual(conversion["marketplace_repository"], "schao523/obvious-one-plugins")
        self.assertTrue(
            all(
                command.get("marketplace_targets", []) in ([], ["codex"])
                for command in conversion["verification"]["commands"]
            )
        )

        self.assertEqual(contract.plugin_id, "growing-with-children")
        self.assertEqual(contract.source_version, "1.0.1")
        self.assertEqual(contract.target_version, "1.0.2")
        self.assertEqual(
            contract.source_archive_sha256,
            "e20ab7f970565dde1d2bfa8529d82da12366dfbed6a6672aed9dc51eedb6d1f1",
        )
        self.assertEqual(contract.owner_skill, "guiding-biblical-study")
        self.assertEqual(
            contract.non_owner_skills,
            (
                "coaching-parenting-and-sensitive-conversations",
                "designing-family-devotions",
                "guiding-parenting-sessions",
                "supporting-parent-reflection",
            ),
        )
        self.assertEqual(
            {item.reference_id: (item.owner_relative_path, item.sha256) for item in contract.references},
            {
                "RM-04A": (
                    "assets/reference-material/RM-04A_Bible_舊約聖經和合本_PUBLIC_DOMAIN.pdf",
                    "2740a6f824f96374cb127d78c3d646b489963898dacc252b842d9a8894a91125",
                ),
                "RM-04B": (
                    "assets/reference-material/RM-04B_Bible_新約聖經和合本_PUBLIC_DOMAIN.pdf",
                    "4f0f9ef4c4a78b83f918c74e8f368a7e0eae515c17866c7767c310ca75786490",
                ),
            },
        )
        self.assertEqual(contract.approval_record["decision"], "APPROVED")
        self.assertEqual(contract.approval_record["confirmed_by"], "decision-owner")
        self.assertEqual(contract.schema, "plugin-delegated-reference-repair-v2")
        self.assertEqual(contract.third_party_notice.classification, "PUBLIC_DOMAIN")
        self.assertTrue(contract.third_party_notice.redistribution_approved)
        self.assertEqual(contract.third_party_notice.confirmed_by, "SC")

    def test_source_decision_preserves_behavior_and_codex_only_scope(self) -> None:
        decisions = (APPLICATION / "docs" / "source-decisions.md").read_text(encoding="utf-8")

        self.assertIn("five-skill architecture", decisions)
        self.assertIn("approved behavior", decisions)
        self.assertIn("Codex", decisions)
        self.assertIn("OpenClaw", decisions)
        self.assertIn("NOT VERIFIED", decisions)


if __name__ == "__main__":
    unittest.main()
