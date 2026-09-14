from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

from obvious_one_plugin_framework.verification import GateResult, VerificationConfigError
from scripts.verify_extraction import (
    ApplicationResult,
    VerificationReport,
    build_parser,
    main,
    verify,
)


FIXTURES = Path(__file__).parent / "fixtures" / "verification"


def _fixture_repository(root: Path) -> Path:
    repository = root / "repository"
    applications = repository / "applications"
    applications.mkdir(parents=True)
    for application_id in ("plugin-alpha", "plugin-beta"):
        shutil.copytree(FIXTURES / application_id, applications / application_id)
    docs = repository / "docs"
    docs.mkdir()
    (docs / "source.json").write_text('{"files": []}\n', encoding="utf-8")
    (docs / "delta.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "marketplace_commit": "0" * 40,
                "codex": {"missing": [], "unexpected": [], "digest_mismatch": []},
                "openclaw": {"missing": [], "unexpected": [], "digest_mismatch": []},
            }
        ),
        encoding="utf-8",
    )
    return repository


class VerifierSelectionAndAggregationTests(unittest.TestCase):
    def test_parser_defaults_to_all_and_supports_explicit_selection(self) -> None:
        default = build_parser().parse_args([])
        self.assertFalse(default.all)
        self.assertIsNone(default.application)

        selected = build_parser().parse_args(["--application", "plugin-alpha"])
        self.assertEqual(selected.application, "plugin-alpha")

        with self.assertRaises(SystemExit):
            build_parser().parse_args(["--all", "--application", "plugin-alpha"])

    def test_verify_continues_with_later_application_after_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = _fixture_repository(Path(temp))
            calls: list[str] = []

            def application_result(config, context):
                calls.append(config.application_id)
                state = "FAIL" if config.application_id == "plugin-alpha" else "PASS"
                return ApplicationResult(
                    application_id=config.application_id,
                    state=state,
                    gates=(GateResult("product-tests", state, state.lower()),),
                    artifacts={},
                )

            with patch(
                "scripts.verify_extraction.run_shared_gates",
                return_value=[GateResult("shared", "PASS", "passed")],
            ), patch(
                "scripts.verify_extraction.run_application",
                side_effect=application_result,
            ):
                report = verify(repository_root=repository, select_all=True)

            self.assertEqual(calls, ["plugin-alpha", "plugin-beta"])
            self.assertEqual(report.state, "FAIL")
            self.assertEqual(
                [result.state for result in report.applications], ["FAIL", "PASS"]
            )
            payload = json.loads(report.report_path.read_text(encoding="utf-8"))
            self.assertEqual([item["application_id"] for item in payload["applications"]], calls)
            self.assertNotIn(str(repository), report.report_path.read_text(encoding="utf-8"))

    def test_failed_shared_gate_prevents_product_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = _fixture_repository(Path(temp))
            application_runner = Mock()
            with patch(
                "scripts.verify_extraction.run_shared_gates",
                return_value=[GateResult("shared", "FAIL", "failed")],
            ), patch("scripts.verify_extraction.run_application", application_runner):
                report = verify(repository_root=repository, select_all=True)

            application_runner.assert_not_called()
            self.assertEqual(report.state, "FAIL")
            self.assertEqual(
                [result.state for result in report.applications],
                ["NOT VERIFIED", "NOT VERIFIED"],
            )

    def test_provenance_override_requires_one_application(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = _fixture_repository(Path(temp))
            provenance = repository / "docs" / "source.json"
            with self.assertRaisesRegex(VerificationConfigError, "one application"):
                verify(
                    repository_root=repository,
                    select_all=True,
                    provenance_override=provenance,
                )


class VerifierCliTests(unittest.TestCase):
    def test_main_preserves_legacy_marketplace_and_provenance_arguments(self) -> None:
        report = VerificationReport(
            state="PASS",
            diagnostics=Path(".tmp/verification/run-test"),
            report_path=Path(".tmp/verification/run-test/report.json"),
            shared_gates=(),
            applications=(),
        )
        with patch("scripts.verify_extraction.verify", return_value=report) as invoked:
            code = main(
                [
                    "--marketplace",
                    "marketplace",
                    "--provenance",
                    "docs/source.json",
                ]
            )

        self.assertEqual(code, 0)
        self.assertEqual(invoked.call_args.kwargs["marketplace"], Path("marketplace").resolve())
        self.assertEqual(
            invoked.call_args.kwargs["provenance_override"],
            Path("docs/source.json").resolve(),
        )

    def test_main_returns_nonzero_for_unknown_application(self) -> None:
        with patch(
            "scripts.verify_extraction.verify",
            side_effect=VerificationConfigError("unknown application: missing"),
        ):
            self.assertEqual(main(["--application", "missing"]), 1)


if __name__ == "__main__":
    unittest.main()
