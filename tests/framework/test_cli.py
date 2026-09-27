from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from obvious_one_plugin_framework.cli import main
from obvious_one_plugin_framework.verification import VerificationConfigError
from tests.framework import test_marketplace as marketplace_fixture


FIXTURES = Path(__file__).resolve().parent / "fixtures"
LEGACY = FIXTURES / "plugin-alpha" / "distribution.json"
V3 = FIXTURES / "plugin-v3" / "distribution.json"
HOSTED_FIXTURE = FIXTURES / "hosted-deployment" / "application"


class FrameworkCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)
        self.hosted_application = self.output / "hosted-fixture"
        shutil.copytree(HOSTED_FIXTURE, self.hosted_application)
        self.hosted_contract = self.hosted_application / "hosted-openai" / "deployment.json"

    def invoke(self, *arguments: str) -> tuple[int, dict[str, object]]:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(list(arguments))
        return code, json.loads(stdout.getvalue())

    def test_cli_builds_schema_v3_fixture(self) -> None:
        name = "plugin-v3"
        code, payload = self.invoke(
            "build-package",
            "--contract", str(FIXTURES / name / "distribution.json"),
            "--output", str(self.output / name),
            "--json",
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["code"], "package_built")
        self.assertEqual(payload["evidence"]["plugin_id"], name)
        self.assertTrue((self.output / name / "CONTENT-MANIFEST.json").is_file())

    def test_cli_builds_assets_and_manifest(self) -> None:
        manifest = self.output / "remote-assets.json"
        code, payload = self.invoke(
            "build-assets",
            "--contract", str(FIXTURES / "plugin-v3/distribution.json"),
            "--output", str(self.output / "assets"),
            "--manifest", str(manifest),
            "--json",
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["evidence"]["asset_count"], 1)
        self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["plugin_id"], "plugin-v3")

    def test_cli_json_is_safe_on_legacy_windows_console(self) -> None:
        bytes_output = io.BytesIO()
        output = io.TextIOWrapper(bytes_output, encoding="cp1252")
        with contextlib.redirect_stdout(output):
            code = main([
                "build-assets",
                "--contract", str(FIXTURES / "plugin-v3/distribution.json"),
                "--output", str(self.output / "legacy-assets"),
                "--json",
            ])
        output.flush()
        output.detach()
        self.assertEqual(code, 0)
        payload = json.loads(bytes_output.getvalue().decode("cp1252"))
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["evidence"]["asset_count"], 1)

    def test_cli_reports_blocked_legacy_build(self) -> None:
        target = self.output / "legacy"

        code, payload = self.invoke(
            "build-package", "--contract", str(LEGACY), "--output", str(target)
        )

        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "BLOCKED")
        self.assertEqual(payload["code"], "legacy_contract_read_only")
        self.assertEqual(payload["mutations"], [])
        self.assertFalse(target.exists())

    def test_validate_contract_requires_no_interaction(self) -> None:
        with patch("builtins.input", side_effect=AssertionError("interactive input forbidden")):
            code, payload = self.invoke("validate-contract", "--contract", str(V3))

        self.assertEqual((code, payload["status"]), (0, "PASS"))
        self.assertEqual(payload["code"], "contract_valid")

    def test_validate_contract_blocks_unclassified_selected_file(self) -> None:
        root = self.output / "unclassified"
        shutil.copytree(FIXTURES / "plugin-v3", root)
        contract_path = root / "distribution.json"
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
        raw["content_rules"] = [raw["content_rules"][0]]
        contract_path.write_text(json.dumps(raw), encoding="utf-8")

        code, payload = self.invoke("validate-contract", "--contract", str(contract_path))

        self.assertEqual((code, payload["status"], payload["code"]), (2, "BLOCKED", "unclassified_files"))
        self.assertEqual(payload["diagnostics"][0]["path"], "assets/logo.bin")
        self.assertIn("binary", payload["diagnostics"][0]["candidates"])

    def test_missing_rights_evidence_is_blocked_with_actionable_path(self) -> None:
        root = self.output / "rights"
        shutil.copytree(FIXTURES / "plugin-v3", root)
        contract_path = root / "distribution.json"
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
        raw["content_rules"][0]["redistribution"]["provenance"] = "docs/missing-rights.md"
        contract_path.write_text(json.dumps(raw), encoding="utf-8")

        code, payload = self.invoke("validate-contract", "--contract", str(contract_path))

        self.assertEqual((code, payload["status"], payload["code"]), (2, "BLOCKED", "rights_unresolved"))
        self.assertEqual(payload["diagnostics"][0]["path"], "docs/missing-rights.md")
        self.assertIn("exclude", payload["diagnostics"][0]["candidates"])

    def test_timeout_is_a_single_machine_readable_failure(self) -> None:
        with patch(
            "obvious_one_plugin_framework.cli._dispatch",
            side_effect=subprocess.TimeoutExpired(["tool"], 1),
        ):
            code, payload = self.invoke("validate-contract", "--contract", str(V3))

        self.assertEqual(code, 4)
        self.assertEqual((payload["status"], payload["code"]), ("FAIL", "operation_timeout"))
        self.assertEqual(len(payload["diagnostics"]), 1)

    def test_verification_config_error_never_exposes_absolute_path_as_code(self) -> None:
        with patch(
            "obvious_one_plugin_framework.cli._dispatch",
            side_effect=VerificationConfigError(
                "/private/work/app/conversion.json: plugin_id: invalid"
            ),
        ):
            code, payload = self.invoke("validate-contract", "--contract", str(V3))

        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["code"], "invalid_verification_config")
        self.assertEqual(payload["diagnostics"][0]["path"], None)
        self.assertNotIn("/private/", json.dumps(payload))

    def test_parser_error_is_a_single_result_document(self) -> None:
        code, payload = self.invoke("build-package", "--contract", str(V3))

        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["code"], "invalid_cli_arguments")

    def test_hosted_create_build_emits_one_ascii_safe_result(self) -> None:
        target = self.output / "hosted"
        code, payload = self.invoke(
            "build-hosted-deployment",
            "--contract", str(self.hosted_contract),
            "--output", str(target),
            "--json",
        )
        self.assertEqual((code, payload["status"], payload["code"]), (0, "PASS", "hosted_deployment_built"))
        json.dumps(payload, ensure_ascii=True).encode("cp1252")
        self.assertEqual(payload["evidence"]["upload_status"], "NOT_PERFORMED")
        self.assertEqual(payload["evidence"]["installation_status"], "NOT VERIFIED")
        self.assertTrue((target / "gpt-hosted-fixture-1.1.0.zip").is_file())
        self.assertTrue(all(not Path(item["path"]).is_absolute() for item in payload["artifacts"]))

    def test_hosted_verify_keeps_local_hosted_and_channel_evidence_separate(self) -> None:
        target = self.output / "hosted"
        self.invoke(
            "build-hosted-deployment", "--contract", str(self.hosted_contract),
            "--output", str(target),
        )
        code, payload = self.invoke(
            "verify-hosted-deployment", "--contract", str(self.hosted_contract),
            "--artifact", str(target), "--json",
        )
        self.assertEqual((code, payload["status"], payload["code"]), (0, "PASS", "hosted_deployment_verified"))
        self.assertEqual(payload["evidence"]["channels"]["openai_hosted"], "PENDING_ACTION")
        self.assertEqual(payload["evidence"]["upload_status"], "NOT_PERFORMED")
        self.assertEqual(payload["evidence"]["installation_status"], "NOT VERIFIED")

    def test_identity_proposal_is_blocked_but_written_without_interaction(self) -> None:
        archive = self.output / "hosted.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("plugin.json", json.dumps({
                "name": "gpt-hosted-fixture", "version": "1.0.0"
            }))
        proposal = self.output / "identity-proposal.json"
        with patch("builtins.input", side_effect=AssertionError("interactive input forbidden")):
            code, payload = self.invoke(
                "import-hosted-identity",
                "--application", str(self.hosted_application / "conversion.json"),
                "--archive", str(archive),
                "--output", str(proposal),
                "--json",
            )
        self.assertEqual((code, payload["status"]), (2, "BLOCKED"))
        self.assertEqual(payload["code"], "hosted_identity_approval_required")
        self.assertTrue(proposal.is_file())

    def test_hosted_plan_blocking_and_proposal_collision_are_stable(self) -> None:
        proposal = self.output / "deployment-proposal.json"
        code, payload = self.invoke(
            "plan-hosted-deployment",
            "--application", str(self.hosted_application / "conversion.json"),
            "--operation", "OPENAI_HOSTED_UPDATE",
            "--output", str(proposal),
            "--json",
        )
        self.assertEqual((code, payload["status"], payload["code"]), (
            2, "BLOCKED", "hosted_deployment_decisions_required"
        ))
        self.assertTrue(proposal.is_file())
        before = proposal.read_bytes()
        code, payload = self.invoke(
            "plan-hosted-deployment",
            "--application", str(self.hosted_application / "conversion.json"),
            "--operation", "OPENAI_HOSTED_UPDATE",
            "--output", str(proposal),
        )
        self.assertEqual((code, payload["status"], payload["code"]), (
            3, "FAIL", "hosted_deployment_proposal_exists"
        ))
        self.assertEqual(proposal.read_bytes(), before)

    def test_hosted_archive_safety_failure_is_one_safe_result(self) -> None:
        archive = self.output / "unsafe.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("../escape.json", "{}")
        code, payload = self.invoke(
            "import-hosted-identity",
            "--application", str(self.hosted_application / "conversion.json"),
            "--archive", str(archive),
            "--output", str(self.output / "proposal.json"),
        )
        self.assertEqual((code, payload["status"]), (3, "FAIL"))
        self.assertEqual(payload["code"], "archive_path_escape")
        self.assertNotIn(str(self.output), json.dumps(payload))

    def test_hosted_validate_and_parser_failures_are_stable(self) -> None:
        code, payload = self.invoke(
            "validate-hosted-deployment", "--contract", str(self.hosted_contract), "--json"
        )
        self.assertEqual((code, payload["status"], payload["code"]), (
            0, "PASS", "hosted_deployment_validated"
        ))
        code, payload = self.invoke("verify-hosted-deployment", "--contract", str(self.hosted_contract))
        self.assertEqual((code, payload["status"], payload["code"]), (
            2, "FAIL", "invalid_cli_arguments"
        ))

    def test_invalid_json_is_fail_with_stable_exit_code(self) -> None:
        invalid = self.output / "invalid.json"
        invalid.write_text("not json", encoding="utf-8")

        code, payload = self.invoke("validate-contract", "--contract", str(invalid))

        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["code"], "invalid_json")

    def test_migration_destination_collision_is_fail_and_preserves_file(self) -> None:
        destination = self.output / "proposal.json"
        destination.write_text("keep", encoding="utf-8")

        code, payload = self.invoke(
            "migrate-contract",
            "--contract", str(LEGACY),
            "--output", str(destination),
        )

        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["code"], "migration_destination_exists")
        self.assertEqual(destination.read_text(encoding="utf-8"), "keep")

    def test_migration_returns_blocked_result_and_writes_proposal(self) -> None:
        destination = self.output / "proposal.json"

        code, payload = self.invoke(
            "migrate-contract",
            "--contract", str(LEGACY),
            "--output", str(destination),
        )

        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "BLOCKED")
        self.assertEqual(payload["code"], "migration_decisions_required")
        self.assertTrue(destination.is_file())

    def test_prepare_marketplace_cli_stages_exact_delta_without_baseline_mutation(self) -> None:
        fixture = self.marketplace_fixture()
        (fixture.baseline / ".gitattributes").write_text(
            "/docs/** text\n", encoding="utf-8", newline="\n"
        )
        baseline_before = fixture._tree(fixture.baseline)

        code, payload = self.invoke(
            "prepare-marketplace",
            "--catalog", str(fixture.catalog_path),
            "--marketplace", str(fixture.baseline),
            "--output", str(fixture.output),
            "--json",
        )

        self.assertEqual((code, payload["status"]), (0, "PASS"))
        self.assertTrue(payload["artifacts"])
        self.assertTrue(payload["mutations"])
        self.assertEqual(fixture._tree(fixture.baseline), baseline_before)
        changed = [item["path"] for item in payload["mutations"]]
        self.assertEqual(changed, sorted(changed))
        self.assertIn(".obvious-one-validation.json", changed)
        attributes = (fixture.output / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("/docs/** text\n", attributes)
        self.assertIn("/plugins/modern/** -text whitespace=cr-at-eol\n", attributes)

    def test_verify_marketplace_cli_supports_all_git_evidence_modes(self) -> None:
        fixture = self.marketplace_fixture()
        prepared, _ = self.invoke(
            "prepare-marketplace",
            "--catalog", str(fixture.catalog_path),
            "--marketplace", str(fixture.baseline),
            "--output", str(fixture.output),
        )
        self.assertEqual(prepared, 0)
        self.git(fixture.output, "init")
        self.git(fixture.output, "config", "user.email", "tests@example.invalid")
        self.git(fixture.output, "config", "user.name", "Framework Tests")
        self.git(fixture.output, "config", "core.autocrlf", "true")
        self.git(fixture.output, "add", ".")
        self.git(fixture.output, "commit", "-m", "fixture")

        cases = (
            ((), "filesystem"),
            (("--index",), "index"),
            (("--commit", "HEAD"), "commit"),
            (("--fresh-checkout",), "fresh_checkout"),
        )
        for options, gate in cases:
            with self.subTest(gate=gate):
                code, payload = self.invoke(
                    "verify-marketplace",
                    "--catalog", str(fixture.catalog_path),
                    "--marketplace", str(fixture.output),
                    *options,
                    "--json",
                )
                self.assertEqual((code, payload["status"]), (0, "PASS"), payload)
                self.assertEqual(payload["evidence"]["gates"]["filesystem"], "PASS")
                self.assertEqual(payload["evidence"]["gates"][gate], "PASS")

    def test_verify_marketplace_git_modes_are_mutually_exclusive(self) -> None:
        code, payload = self.invoke(
            "verify-marketplace",
            "--catalog", str(V3),
            "--marketplace", str(self.output),
            "--index",
            "--commit", "HEAD",
        )

        self.assertEqual(code, 2)
        self.assertEqual(payload["code"], "invalid_cli_arguments")

    def marketplace_fixture(self):
        fixture = marketplace_fixture.MarketplaceTests(
            "test_build_requires_v3_and_verify_existing_accepts_legacy"
        )
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        return fixture

    @staticmethod
    def git(root: Path, *arguments: str) -> None:
        completed = subprocess.run(
            ["git", *arguments], cwd=root, capture_output=True, text=True, check=False
        )
        if completed.returncode:
            raise AssertionError(completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
