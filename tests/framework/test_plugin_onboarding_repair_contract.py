from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.plugin_onboarding import OnboardingError
from obvious_one_plugin_framework.plugin_onboarding.repair_contract import (
    load_repair_contract,
)
from tests.framework.plugin_onboarding_fixtures import (
    canonical_bytes,
    write_legacy_repair_fixture,
)


class RepairContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fixture = write_legacy_repair_fixture(self.root / "fixture")
        self.contract = self.root / "repair.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def load(self, payload: dict[str, object] | None = None):
        self.contract.write_bytes(
            canonical_bytes(payload or dict(self.fixture.contract_payload))
        )
        return load_repair_contract(self.contract)

    def assert_code(self, payload: dict[str, object], code: str) -> None:
        with self.assertRaises(OnboardingError) as caught:
            self.load(payload)
        self.assertEqual(caught.exception.code, code)

    def test_valid_contract_loads_to_frozen_exact_values(self) -> None:
        loaded = self.load()
        self.assertEqual(
            (loaded.plugin_id, loaded.source_version, loaded.target_version),
            ("sample-plugin", "1.0.1", "1.0.2"),
        )
        self.assertEqual(loaded.owner_skill, "guiding-biblical-study")
        self.assertEqual(len(loaded.references), 2)
        with self.assertRaises(AttributeError):
            loaded.plugin_id = "changed"  # type: ignore[misc]

    def test_v2_public_domain_notice_is_strict_and_frozen(self) -> None:
        payload = copy.deepcopy(self.fixture.contract_payload)
        payload["schema"] = "plugin-delegated-reference-repair-v2"
        payload["third_party_notice"] = {
            "classification": "PUBLIC_DOMAIN",
            "redistribution_approved": True,
            "confirmed_by": "Plugin Owner",
            "recorded_at": "2026-10-10",
        }

        loaded = self.load(payload)

        self.assertEqual(loaded.schema, "plugin-delegated-reference-repair-v2")
        self.assertEqual(loaded.third_party_notice.classification, "PUBLIC_DOMAIN")
        self.assertTrue(loaded.third_party_notice.redistribution_approved)
        with self.assertRaises(AttributeError):
            loaded.third_party_notice.confirmed_by = "changed"  # type: ignore[misc]

    def test_v2_notice_rejects_missing_unknown_or_unapproved_values(self) -> None:
        base = copy.deepcopy(self.fixture.contract_payload)
        base["schema"] = "plugin-delegated-reference-repair-v2"
        base["third_party_notice"] = {
            "classification": "PUBLIC_DOMAIN",
            "redistribution_approved": True,
            "confirmed_by": "Plugin Owner",
            "recorded_at": "2026-10-10",
        }
        cases = []
        missing = copy.deepcopy(base)
        missing.pop("third_party_notice")
        cases.append((missing, "missing_key"))
        unknown = copy.deepcopy(base)
        unknown["third_party_notice"]["extra"] = True  # type: ignore[index]
        cases.append((unknown, "invalid_third_party_notice"))
        wrong_classification = copy.deepcopy(base)
        wrong_classification["third_party_notice"]["classification"] = "UNKNOWN"  # type: ignore[index]
        cases.append((wrong_classification, "invalid_third_party_notice"))
        unapproved = copy.deepcopy(base)
        unapproved["third_party_notice"]["redistribution_approved"] = False  # type: ignore[index]
        cases.append((unapproved, "redistribution_approval_required"))
        for payload, suffix in cases:
            with self.subTest(suffix=suffix):
                self.assert_code(payload, f"onboarding.repair_contract.{suffix}")

    def test_unknown_missing_and_absent_approval_fail_closed(self) -> None:
        base = dict(self.fixture.contract_payload)
        unknown = copy.deepcopy(base)
        unknown["surprise"] = True
        self.assert_code(unknown, "onboarding.repair_contract.unknown_key")
        missing = copy.deepcopy(base)
        missing.pop("target_version")
        self.assert_code(missing, "onboarding.repair_contract.missing_key")
        approval = copy.deepcopy(base)
        approval["approval_record"] = {}
        self.assert_code(approval, "onboarding.repair_contract.approval_required")

    def test_identity_paths_versions_and_digests_are_strict(self) -> None:
        base = dict(self.fixture.contract_payload)
        cases = (
            ("plugin_id", "Bad ID", "invalid_plugin_id"),
            ("source_version", "one", "invalid_source_version"),
            ("target_version", "two", "invalid_target_version"),
            ("source_archive_sha256", "A" * 64, "invalid_digest"),
            ("source_manifest_path", "../manifest.json", "invalid_path"),
        )
        for field, value, suffix in cases:
            with self.subTest(field=field):
                payload = copy.deepcopy(base)
                payload[field] = value
                self.assert_code(payload, f"onboarding.repair_contract.{suffix}")
        payload = copy.deepcopy(base)
        payload["references"][0]["owner_relative_path"] = "../RM-04A.pdf"  # type: ignore[index]
        self.assert_code(payload, "onboarding.repair_contract.invalid_path")

    def test_duplicate_or_contradictory_ownership_is_rejected(self) -> None:
        base = dict(self.fixture.contract_payload)
        duplicate_skill = copy.deepcopy(base)
        duplicate_skill["non_owner_skills"].append(  # type: ignore[union-attr]
            duplicate_skill["non_owner_skills"][0]  # type: ignore[index]
        )
        self.assert_code(
            duplicate_skill, "onboarding.repair_contract.duplicate_non_owner_skill"
        )
        owner_in_list = copy.deepcopy(base)
        owner_in_list["non_owner_skills"].append(owner_in_list["owner_skill"])  # type: ignore[union-attr]
        self.assert_code(
            owner_in_list, "onboarding.repair_contract.owner_is_non_owner"
        )
        duplicate_reference = copy.deepcopy(base)
        duplicate_reference["references"].append(  # type: ignore[union-attr]
            copy.deepcopy(duplicate_reference["references"][0])  # type: ignore[index]
        )
        self.assert_code(
            duplicate_reference, "onboarding.repair_contract.duplicate_reference"
        )


if __name__ == "__main__":
    unittest.main()
