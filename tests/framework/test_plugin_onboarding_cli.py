from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from obvious_one_plugin_framework.cli import main
from tests.framework.plugin_onboarding_fixtures import (
    write_legacy_adoption,
    write_legacy_plugin_builder_fixture,
    write_legacy_repair_fixture,
    write_plugin_builder_fixture,
    write_publication_decisions,
)


REPOSITORY = Path(__file__).resolve().parents[2]


class PluginOnboardingCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.fixture = write_plugin_builder_fixture(self.root / "package")
        self.legacy_fixture = write_legacy_plugin_builder_fixture(
            self.root / "legacy-package"
        )
        self.decisions = write_publication_decisions(self.root / "decisions.json")
        self.output = self.root / "proposal"

    def invoke(self, *extra: str) -> tuple[int, str, dict[str, object]]:
        arguments = [
            "prepare-plugin-zip-marketplace",
            "--archive", str(self.fixture.archive),
            "--package-metadata", str(self.fixture.metadata),
            "--publication-decisions", str(self.decisions),
            "--repository", str(REPOSITORY),
            "--output", str(self.output),
            *extra,
        ]
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = main(arguments)
        text = stream.getvalue()
        return code, text, json.loads(text)

    def invoke_legacy(self, *extra: str) -> tuple[int, str, dict[str, object]]:
        arguments = [
            "prepare-plugin-zip-marketplace",
            "--archive", str(self.legacy_fixture.archive),
            "--legacy-adoption", str(self.legacy_fixture.adoption),
            "--publication-decisions", str(self.decisions),
            "--repository", str(REPOSITORY),
            "--output", str(self.output),
            *extra,
        ]
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = main(arguments)
        text = stream.getvalue()
        return code, text, json.loads(text)

    def test_cli_success_emits_one_ascii_safe_pass_result(self) -> None:
        code, text, payload = self.invoke("--json")
        self.assertEqual((code, payload["status"], payload["code"]), (0, "PASS", "onboarding.proposal_materialized"))
        self.assertTrue(text.isascii())
        self.assertEqual(text.count('"result_schema_version"'), 1)
        self.assertTrue((self.output / "onboarding-result.json").is_file())

    def test_legacy_cli_success_emits_one_ascii_safe_pass_result(self) -> None:
        code, text, payload = self.invoke_legacy("--json")
        self.assertEqual(
            (code, payload["status"], payload["code"]),
            (0, "PASS", "onboarding.proposal_materialized"),
        )
        self.assertTrue(text.isascii())
        self.assertEqual(text.count('"result_schema_version"'), 1)
        self.assertRegex(
            payload["evidence"]["adoption_identity_sha256"], r"^[0-9a-f]{64}$"
        )

    def test_cli_requires_exactly_one_authority_option(self) -> None:
        common = [
            "prepare-plugin-zip-marketplace",
            "--archive", str(self.fixture.archive),
            "--publication-decisions", str(self.decisions),
            "--repository", str(REPOSITORY),
            "--output", str(self.output),
        ]
        for authority in (
            [],
            [
                "--package-metadata", str(self.fixture.metadata),
                "--legacy-adoption", str(self.legacy_fixture.adoption),
            ],
        ):
            with self.subTest(authority=authority):
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream):
                    code = main([*common, *authority])
                payload = json.loads(stream.getvalue())
                self.assertEqual(
                    (code, payload["status"], payload["code"]),
                    (2, "FAIL", "invalid_cli_arguments"),
                )
                self.assertFalse(self.output.exists())

    def test_legacy_runtime_evidence_is_rejected_before_output(self) -> None:
        code, _, payload = self.invoke_legacy(
            "--evidence", str(self.root / "unsupported-evidence.zip")
        )
        self.assertEqual(
            (code, payload["status"], payload["code"]),
            (3, "FAIL", "onboarding.legacy_runtime_evidence_unsupported"),
        )
        self.assertFalse(self.output.exists())

    def test_legacy_false_approval_is_blocked_exit_two(self) -> None:
        self.legacy_fixture = type(self.legacy_fixture)(
            self.legacy_fixture.root,
            self.legacy_fixture.candidate,
            self.legacy_fixture.archive,
            write_legacy_adoption(
                self.root / "false-adoption.json",
                self.legacy_fixture,
                overrides={"adoption_approved": False},
            ),
            self.legacy_fixture.adoption_payload,
        )
        code, _, payload = self.invoke_legacy()
        self.assertEqual(
            (code, payload["status"], payload["code"]),
            (2, "BLOCKED", "onboarding.legacy_adoption.adoption_approval_required"),
        )
        self.assertFalse(self.output.exists())

    def test_legacy_tampered_archive_is_fail_exit_three(self) -> None:
        self.legacy_fixture.archive.write_bytes(
            self.legacy_fixture.archive.read_bytes() + b"tampered"
        )
        code, _, payload = self.invoke_legacy()
        self.assertEqual(
            (code, payload["status"], payload["code"]),
            (3, "FAIL", "onboarding.inspection.archive_sha256_mismatch"),
        )
        self.assertFalse(self.output.exists())

    def test_legacy_unicode_paths_and_preexisting_output_fail_closed(self) -> None:
        self.legacy_fixture = write_legacy_plugin_builder_fixture(
            self.root / "歷史套件"
        )
        code, text, payload = self.invoke_legacy()
        self.assertEqual((code, payload["status"]), (0, "PASS"))
        self.assertNotIn(str(self.root), text)

        self.output = self.root / "preexisting-output"
        self.output.mkdir()
        (self.output / "owner-file.txt").write_bytes(b"preserve\n")
        code, _, payload = self.invoke_legacy()
        self.assertEqual(
            (code, payload["status"], payload["code"]),
            (3, "FAIL", "onboarding.output_collision"),
        )
        self.assertEqual(
            (self.output / "owner-file.txt").read_bytes(), b"preserve\n"
        )

    def test_inspect_legacy_zip_writes_observation_without_mutation(self) -> None:
        legacy = write_legacy_repair_fixture(self.root / "legacy")
        report = self.root / "inspection.json"
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = main(
                [
                    "inspect-plugin-zip",
                    "--archive", str(legacy.archive),
                    "--output", str(report),
                    "--json",
                ]
            )
        payload = json.loads(stream.getvalue())
        self.assertEqual((code, payload["status"]), (0, "PASS"))
        observation = json.loads(report.read_text(encoding="ascii"))
        self.assertEqual(observation["input_profile"], "PLUGIN_BUILDER_CANDIDATE_V1")
        self.assertEqual(set(observation["evidence_states"].values()), {"NOT VERIFIED"})
        self.assertFalse(self.output.exists())

    def test_cli_missing_authority_is_blocked_exit_two(self) -> None:
        payload = json.loads(self.decisions.read_text(encoding="utf-8"))
        payload["public_marketplace_approved"] = False
        self.decisions.write_text(json.dumps(payload), encoding="utf-8")
        code, _, result = self.invoke()
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "onboarding.decisions.public_marketplace_approved_required")
        self.assertFalse(self.output.exists())

    def test_cli_tampering_is_fail_exit_three(self) -> None:
        self.fixture.archive.write_bytes(self.fixture.archive.read_bytes() + b"tampered")
        code, _, result = self.invoke()
        self.assertEqual((code, result["status"]), (3, "FAIL"))
        self.assertEqual(result["code"], "onboarding.inspection.archive_sha256_mismatch")
        self.assertFalse(self.output.exists())

    def test_cli_io_failure_is_exit_four(self) -> None:
        with patch(
            "obvious_one_plugin_framework.cli.prepare_plugin_zip_marketplace",
            side_effect=OSError("private machine path"),
        ):
            code, text, result = self.invoke()
        self.assertEqual((code, result["status"], result["code"]), (4, "FAIL", "io_failure"))
        self.assertNotIn("private machine path", text)

    def test_cli_invalid_arguments_create_no_output(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = main(["prepare-plugin-zip-marketplace", "--output", str(self.output)])
        result = json.loads(stream.getvalue())
        self.assertEqual((code, result["status"], result["code"]), (2, "FAIL", "invalid_cli_arguments"))
        self.assertFalse(self.output.exists())

    def test_cli_unicode_inputs_do_not_leak_absolute_paths(self) -> None:
        unicode_root = self.root / "測試輸入"
        fixture = write_plugin_builder_fixture(unicode_root / "套件")
        decisions = write_publication_decisions(unicode_root / "決定.json")
        self.fixture = fixture
        self.decisions = decisions
        code, text, result = self.invoke()
        self.assertEqual((code, result["status"]), (0, "PASS"))
        self.assertNotIn(str(self.root), text)

    def test_cli_never_mutates_repository_or_marketplace(self) -> None:
        catalog = REPOSITORY / "marketplaces" / "obvious-one.json"
        catalog_before = catalog.read_bytes()
        applications_before = tuple(sorted(path.name for path in (REPOSITORY / "applications").iterdir()))
        code, _, result = self.invoke()
        self.assertEqual((code, result["status"]), (0, "PASS"))
        self.assertEqual(catalog.read_bytes(), catalog_before)
        self.assertEqual(
            tuple(sorted(path.name for path in (REPOSITORY / "applications").iterdir())),
            applications_before,
        )


if __name__ == "__main__":
    unittest.main()
