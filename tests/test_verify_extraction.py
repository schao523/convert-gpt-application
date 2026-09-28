from __future__ import annotations

import json
import contextlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import scripts.verify_extraction as verifier

from obvious_one_plugin_framework.verification import GateResult, VerificationConfigError
from scripts.verify_extraction import (
    ApplicationResult,
    RunContext,
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
    for application_id in ("plugin-alpha", "plugin-beta"):
        (docs / f"{application_id}-source.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "application_id": application_id,
                    "plugin_id": application_id,
                    "source_repository": f"{application_id}-source",
                    "source_commit": "1" * 40,
                    "marketplace_repository": "example/plugins",
                    "marketplace_commit": "0" * 40,
                    "incorporated_branches": [],
                    "source_inventory": [],
                }
            ),
            encoding="utf-8",
        )
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
    def context(self, repository: Path) -> RunContext:
        return RunContext(
            repository_root=repository,
            diagnostics=repository / ".tmp" / "verification",
            python=sys.executable,
            command_runner=lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "", ""),
        )

    def add_hosted_contract(
        self,
        repository: Path,
        application_id: str,
        *,
        operation: str = "OPENAI_HOSTED_CREATE",
        include_identity: bool = False,
    ) -> Path:
        application = repository / "applications" / application_id
        docs = application / "docs"
        docs.mkdir(exist_ok=True)
        shutil.copy2(repository / "docs" / f"{application_id}-source.json", docs / "source-inventory.json")
        shutil.copy2(repository / "docs" / "delta.json", docs / "delta.json")
        conversion_path = application / "conversion.json"
        conversion = json.loads(conversion_path.read_text(encoding="utf-8"))
        conversion["source_inventory"] = "docs/source-inventory.json"
        conversion["verification"]["marketplace"]["approved_delta"] = "docs/delta.json"
        conversion_path.write_text(json.dumps(conversion), encoding="utf-8")

        hosted = application / "hosted-openai"
        adapter = hosted / "adapter"
        (adapter / ".codex-plugin").mkdir(parents=True)
        for target in (adapter / "plugin.json", adapter / ".codex-plugin" / "plugin.json"):
            target.write_text(json.dumps({
                "name": application_id,
                "version": "1.1.0",
                "description": "Fixture hosted plugin",
            }), encoding="utf-8")
        (hosted / "lineage-decision.json").write_text(json.dumps({
            "schema_version": 1,
            "application_id": application_id,
            "status": "approved",
            "canonical_source": "canonical_converted_application",
            "evidence_reference": "../docs/rights.md",
        }), encoding="utf-8")
        identity_reference = None
        if include_identity:
            identity_reference = "hosted-identity.json"
            (hosted / identity_reference).write_text(json.dumps({
                "schema_version": 1,
                "application_id": application_id,
                "package_name": application_id,
                "last_confirmed_version": "1.0.0",
                "last_confirmed_archive_sha256": "1" * 64,
                "origin": "prior_verified_deployment",
                "deployment_confirmation": {
                    "status": "owner_confirmed",
                    "recorded_at": "2026-09-25T00:00:00Z",
                    "evidence_reference": "../docs/rights.md",
                },
            }), encoding="utf-8")
        contract = {
            "schema_version": 1,
            "application_id": application_id,
            "operation": operation,
            "lineage": {
                "source_inventory": "../docs/source-inventory.json",
                "canonical_distribution_contract": "../openclaw/distribution.json",
                "hosted_lineage_decision": "lineage-decision.json",
            },
            "identity": {"package_name": application_id, "record": identity_reference},
            "target": {
                "version": "1.1.0",
                "archive_name": f"{application_id}-1.1.0.zip",
                "portable_manifest": "adapter/plugin.json",
                "legacy_manifest": "adapter/.codex-plugin/plugin.json",
                "max_archive_bytes": 1000000,
            },
            "content": {
                "canonical_mappings": [{
                    "id": "demo", "source_kind": "canonical_application",
                    "source": "skills/demo", "target": "skills/demo",
                    "copy_mode": "copy_tree", "classification": "text",
                    "redistribution_reference": "fixture-text",
                }],
                "adapter_mappings": [
                    {
                        "id": "portable", "source_kind": "hosted_adapter",
                        "source": "adapter/plugin.json", "target": "plugin.json",
                        "copy_mode": "copy_file", "classification": "text",
                        "redistribution_reference": "../docs/rights.md",
                    },
                    {
                        "id": "legacy", "source_kind": "hosted_adapter",
                        "source": "adapter/.codex-plugin/plugin.json",
                        "target": ".codex-plugin/plugin.json", "copy_mode": "copy_file",
                        "classification": "text", "redistribution_reference": "../docs/rights.md",
                    },
                ],
            },
            "validation": {
                "expected_skills": ["demo"], "explicit_only_skills": [],
                "required_application_tests": ["smoke"], "capabilities": [],
            },
            "channels": {
                "openai_hosted": {"status": "UNPUBLISHED", "evidence": "fixture declaration"},
                "obvious_one": {"status": "UNPUBLISHED", "evidence": "fixture declaration"},
                "openai_public": {"status": "UNPUBLISHED", "evidence": "fixture declaration"},
            },
        }
        path = hosted / "deployment.json"
        path.write_text(json.dumps(contract), encoding="utf-8")
        return path

    def test_hosted_gate_runs_only_for_application_that_owns_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = _fixture_repository(Path(temp))
            self.add_hosted_contract(repository, "plugin-alpha")
            alpha, beta = verifier.discover_applications(repository)
            with patch(
                "scripts.verify_extraction._hosted_deployment_gate",
                return_value=GateResult("hosted-deployment", "PASS", "verified"),
            ) as hosted:
                alpha_result = verifier.run_application(alpha, self.context(repository))
                beta_result = verifier.run_application(beta, self.context(repository))
            self.assertEqual(hosted.call_count, 1)
            self.assertIn("hosted-deployment", [gate.gate_id for gate in alpha_result.gates])
            self.assertNotIn("hosted-deployment", [gate.gate_id for gate in beta_result.gates])

    def test_local_hosted_gate_does_not_report_external_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = _fixture_repository(Path(temp))
            self.add_hosted_contract(repository, "plugin-alpha")
            config = verifier.discover_applications(repository)[0]
            gate = verifier._hosted_deployment_gate(config, self.context(repository))
        self.assertEqual(gate.data["upload"], "NOT_PERFORMED")
        self.assertEqual(gate.data["installation"], "NOT VERIFIED")
        self.assertEqual(gate.data["marketplace"], "NOT_PERFORMED")
        self.assertEqual(gate.data["public_submission"], "NOT_PERFORMED")

    def test_create_needs_no_identity_but_update_requires_one(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = _fixture_repository(Path(temp))
            create = self.add_hosted_contract(repository, "plugin-alpha")
            config = verifier.discover_applications(repository)[0]
            self.assertEqual(
                verifier._hosted_deployment_gate(config, self.context(repository)).state,
                "PASS",
            )
            payload = json.loads(create.read_text(encoding="utf-8"))
            payload["operation"] = "OPENAI_HOSTED_UPDATE"
            create.write_text(json.dumps(payload), encoding="utf-8")
            gate = verifier._hosted_deployment_gate(config, self.context(repository))
            self.assertEqual(gate.state, "NOT VERIFIED")
            self.assertIn("identity", gate.detail)

    def test_hosted_failure_for_one_application_does_not_add_gate_to_another(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = _fixture_repository(Path(temp))
            self.add_hosted_contract(repository, "plugin-alpha")
            alpha, beta = verifier.discover_applications(repository)
            with patch(
                "scripts.verify_extraction._hosted_deployment_gate",
                return_value=GateResult("hosted-deployment", "FAIL", "failed"),
            ):
                alpha_result = verifier.run_application(alpha, self.context(repository))
                beta_result = verifier.run_application(beta, self.context(repository))
            self.assertEqual(alpha_result.state, "FAIL")
            self.assertNotIn("hosted-deployment", [gate.gate_id for gate in beta_result.gates])

    def test_shared_gates_do_not_execute_application_provenance_tests(self) -> None:
        commands: list[list[str]] = []

        def runner(command, **kwargs):
            commands.append(command)
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            context = RunContext(
                repository_root=root,
                diagnostics=root / ".tmp" / "verification",
                python=sys.executable,
                command_runner=runner,
            )
            verifier.run_shared_gates(context)

        flattened = "\n".join(" ".join(command) for command in commands)
        self.assertNotIn("tests.test_provenance", flattened)

    def test_application_provenance_is_an_application_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = _fixture_repository(Path(temp))
            config = verifier.discover_applications(repository)[0]
            payload = {
                "schema_version": 2,
                "application_id": config.application_id,
                "plugin_id": config.plugin_id,
                "source_repository": config.provenance.source_repository,
                "source_commit": "1" * 40,
                "marketplace_repository": config.marketplace_repository,
                "marketplace_commit": "2" * 40,
                "incorporated_branches": list(config.provenance.incorporated_branches),
                "source_inventory": [],
            }
            config.source_inventory.write_text(json.dumps(payload), encoding="utf-8")
            context = RunContext(
                repository_root=repository,
                diagnostics=repository / ".tmp" / "verification",
                python=sys.executable,
            )

            gate = verifier._provenance_gate(config, context)

            self.assertEqual(gate.gate_id, "provenance")
            self.assertEqual(gate.state, "PASS")

    def test_parser_defaults_to_all_and_supports_explicit_selection(self) -> None:
        default = build_parser().parse_args([])
        self.assertFalse(default.all)
        self.assertIsNone(default.application)

        selected = build_parser().parse_args(["--application", "plugin-alpha"])
        self.assertEqual(selected.application, "plugin-alpha")

        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
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
        with patch("scripts.verify_extraction.verify", return_value=report) as invoked, contextlib.redirect_stdout(io.StringIO()):
            code = main([
                "--marketplace", "marketplace",
                "--provenance", "docs/source.json",
            ])

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
        ), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--application", "missing"]), 1)


if __name__ == "__main__":
    unittest.main()
