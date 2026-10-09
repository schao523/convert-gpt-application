from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.plugin_onboarding.contract import (
    OnboardingError,
    WorkbenchRepairMetadata,
    load_onboarding_metadata,
    load_package_metadata,
    load_publication_decisions,
)
from tests.framework.plugin_onboarding_fixtures import (
    canonical_bytes,
    write_plugin_builder_fixture,
    write_legacy_repair_fixture,
    write_publication_decisions,
)


class PluginOnboardingContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def assert_error(
        self,
        callable_,
        *,
        code: str,
        status: str = "FAIL",
    ) -> OnboardingError:
        with self.assertRaises(OnboardingError) as caught:
            callable_()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(caught.exception.status, status)
        return caught.exception

    def rewrite(self, path: Path, mutate) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        mutate(payload)
        path.write_bytes(canonical_bytes(payload))

    def test_v2_and_v3_metadata_parse_to_typed_exact_contracts(self) -> None:
        for schema in ("plugin-builder-package-v2", "plugin-builder-package-v3"):
            with self.subTest(schema=schema):
                fixture = write_plugin_builder_fixture(self.root / schema, schema=schema)

                metadata = load_package_metadata(fixture.metadata)

                self.assertEqual(metadata.schema, schema)
                self.assertEqual(metadata.plugin_id, "sample-plugin")
                self.assertEqual(metadata.envelope_profile, "PORTABLE_SINGLE_DIRECTORY")
                self.assertEqual(metadata.archive_sha256, fixture.metadata_payload["archive_sha256"])
                self.assertEqual(
                    metadata.members[0].path,
                    "sample-plugin/.codex-plugin/plugin.json",
                )
                self.assertGreater(metadata.members[0].size, 0)
                self.assertEqual(metadata.candidate_members[0].path, ".codex-plugin/plugin.json")
                self.assertIsInstance(metadata.members, tuple)
                self.assertEqual(
                    metadata.capabilities_sha256,
                    "3" * 64 if schema.endswith("v3") else None,
                )

    def test_workbench_repair_metadata_is_separate_from_builder_evidence(self) -> None:
        fixture = write_legacy_repair_fixture(self.root / "legacy")
        contract_path = self.root / "repair.json"
        contract_path.write_bytes(canonical_bytes(fixture.contract_payload))
        from obvious_one_plugin_framework.plugin_onboarding import (
            load_repair_contract,
            repair_delegated_reference_archive,
        )

        result = repair_delegated_reference_archive(
            fixture.archive,
            load_repair_contract(contract_path),
            self.root / "repaired.zip",
            self.root / "repaired-metadata.json",
        )
        metadata = load_onboarding_metadata(result.metadata)
        self.assertIsInstance(metadata, WorkbenchRepairMetadata)
        self.assertEqual(metadata.input_profile, "PLUGIN_BUILDER_CANDIDATE_V1")
        self.assertEqual(metadata.archive_sha256, result.archive_sha256)
        self.assertEqual(set(metadata.evidence_states.values()), {"NOT VERIFIED"})
        self.assertFalse(hasattr(metadata, "candidate_sha256"))
        self.assertFalse(hasattr(metadata, "verification_sha256"))

    def test_unknown_missing_and_wrong_typed_metadata_fields_fail_closed(self) -> None:
        cases = (
            (lambda value: value.update({"surprise": True}), "onboarding.metadata.unknown_key"),
            (lambda value: value.pop("archive_sha256"), "onboarding.metadata.missing_key"),
            (lambda value: value.update({"members": "wrong"}), "onboarding.metadata.invalid_type"),
            (lambda value: value.update({"archive_sha256": "A" * 64}), "onboarding.metadata.invalid_digest"),
        )
        for index, (mutate, code) in enumerate(cases):
            with self.subTest(code=code):
                fixture = write_plugin_builder_fixture(self.root / f"case-{index}")
                self.rewrite(fixture.metadata, mutate)
                self.assert_error(lambda: load_package_metadata(fixture.metadata), code=code)

    def test_publication_decisions_require_exact_codex_obvious_one_values(self) -> None:
        path = write_publication_decisions(self.root / "decisions.json")

        decisions = load_publication_decisions(path)

        self.assertEqual(decisions.schema, "plugin-publication-decisions-v1")
        self.assertEqual(decisions.target_runtime, "CODEX")
        self.assertEqual(decisions.marketplace_id, "obvious-one")
        self.assertEqual(decisions.codex_destination, "plugins/sample-plugin")
        identity = decisions.identity_payload()
        self.assertNotIn("decision_recorded_at", identity)
        self.assertEqual(identity["confirmed_by"], "Plugin Owner")

        invalid_values = {
            "target_runtime": "OPENCLAW",
            "marketplace_id": "another-market",
            "codex_destination": "plugins/other-plugin",
        }
        for field, value in invalid_values.items():
            with self.subTest(field=field):
                candidate = write_publication_decisions(
                    self.root / f"invalid-{field}.json", overrides={field: value}
                )
                self.assert_error(
                    lambda candidate=candidate: load_publication_decisions(candidate),
                    code=f"onboarding.decisions.invalid_{field}",
                )

    def test_missing_or_false_owner_authority_is_blocked(self) -> None:
        for field in (
            "redistribution_approved",
            "third_party_content_reviewed",
            "public_marketplace_approved",
        ):
            with self.subTest(field=field, state="false"):
                path = write_publication_decisions(
                    self.root / f"false-{field}.json", overrides={field: False}
                )
                self.assert_error(
                    lambda path=path: load_publication_decisions(path),
                    code=f"onboarding.decisions.{field}_required",
                    status="BLOCKED",
                )
            with self.subTest(field=field, state="missing"):
                path = write_publication_decisions(self.root / f"missing-{field}.json")
                self.rewrite(path, lambda value, field=field: value.pop(field))
                self.assert_error(
                    lambda path=path: load_publication_decisions(path),
                    code=f"onboarding.decisions.{field}_required",
                    status="BLOCKED",
                )

    def test_mit_author_year_and_third_party_notice_states_are_strict(self) -> None:
        cases = (
            ({"license": "Apache-2.0"}, "onboarding.decisions.unsupported_license"),
            ({"author": ""}, "onboarding.decisions.invalid_author"),
            ({"copyright_year": True}, "onboarding.decisions.invalid_copyright_year"),
            ({"copyright_year": 999}, "onboarding.decisions.invalid_copyright_year"),
            ({"third_party_content": "UNKNOWN"}, "onboarding.decisions.invalid_third_party_content"),
        )
        for index, (overrides, code) in enumerate(cases):
            with self.subTest(code=code):
                path = write_publication_decisions(
                    self.root / f"strict-{index}.json", overrides=overrides
                )
                self.assert_error(lambda path=path: load_publication_decisions(path), code=code)

        included = write_publication_decisions(
            self.root / "included.json",
            overrides={"third_party_content": "INCLUDED_WITH_PLUGIN_NOTICES"},
        )
        self.assertEqual(
            load_publication_decisions(included).third_party_content,
            "INCLUDED_WITH_PLUGIN_NOTICES",
        )

    def test_contract_diagnostics_do_not_expose_absolute_paths(self) -> None:
        metadata = self.root / "private-owner-name" / "package-metadata.json"
        metadata.parent.mkdir()
        metadata.write_text("not json", encoding="utf-8")
        decisions = self.root / "private-owner-name" / "decisions.json"
        decisions.write_text("[]", encoding="utf-8")

        for loader, path, code in (
            (load_package_metadata, metadata, "onboarding.metadata.invalid_json"),
            (load_publication_decisions, decisions, "onboarding.decisions.invalid_type"),
        ):
            with self.subTest(loader=loader.__name__):
                error = self.assert_error(lambda loader=loader, path=path: loader(path), code=code)
                self.assertNotIn(str(self.root), str(error))
                self.assertNotIn("private-owner-name", error.detail)


if __name__ == "__main__":
    unittest.main()
