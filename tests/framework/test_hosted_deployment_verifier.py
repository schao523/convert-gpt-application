from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
from unittest import mock
import shutil
import tempfile
import unittest
import zipfile

from obvious_one_plugin_framework.hosted_deployment_builder import build_hosted_deployment
from obvious_one_plugin_framework.hosted_deployment_contract import (
    HostedDeploymentError,
    load_hosted_deployment_contract,
)
from obvious_one_plugin_framework.hosted_deployment_planner import validate_hosted_deployment
from obvious_one_plugin_framework.hosted_deployment_verifier import verify_hosted_deployment


FIXTURE = Path(__file__).parent / "fixtures" / "hosted-deployment" / "application"


class HostedDeploymentVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.application = self.base / "hosted-fixture"
        shutil.copytree(FIXTURE, self.application)
        self.contract_path = self.application / "hosted-openai" / "deployment.json"
        self.add_capability()
        self.reload_and_build()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def json_file(self, relative: str) -> dict:
        path = self.application / relative
        return json.loads(path.read_text(encoding="utf-8"))

    def write_json(self, relative: str, value: dict) -> None:
        (self.application / relative).write_text(json.dumps(value), encoding="utf-8")

    def add_mapped_file(self, relative: str, content: bytes, *, classification: str = "text") -> None:
        path = self.application / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        distribution = self.json_file("openclaw/distribution.json")
        distribution["include_files"].append(relative)
        distribution["content_rules"][0]["paths"].append(relative)
        self.write_json("openclaw/distribution.json", distribution)
        deployment = self.json_file("hosted-openai/deployment.json")
        deployment["content"]["canonical_mappings"].append({
            "id": "mapped-" + relative.replace("/", "-"),
            "source_kind": "canonical_application",
            "source": relative,
            "target": relative,
            "copy_mode": "copy_file",
            "classification": classification,
            "redistribution_reference": "approved-text",
        })
        self.write_json("hosted-openai/deployment.json", deployment)

    def add_capability(self, *, local_test: str | None = "fixture-test") -> None:
        self.add_mapped_file("scripts/retrieve.py", b"print('fixture')\n")
        deployment = self.json_file("hosted-openai/deployment.json")
        deployment["validation"]["capabilities"] = [{
            "id": "exact-retrieval",
            "requirement": "required",
            "provider_kind": "packaged_executable",
            "artifact_paths": ["scripts/retrieve.py"],
            "local_verification_test": local_test,
            "hosted_verification": "required_after_install",
            "on_unavailable": "block",
            "fallback": None,
        }]
        self.write_json("hosted-openai/deployment.json", deployment)

    def reload_and_build(self) -> None:
        self.contract = load_hosted_deployment_contract(self.contract_path)
        self.contract_validation = validate_hosted_deployment(self.contract)
        self.artifact = self.base / "artifact"
        build_hosted_deployment(self.contract, self.artifact)

    def tree_bytes(self) -> dict[str, bytes]:
        return {
            path.relative_to(self.artifact).as_posix(): path.read_bytes()
            for path in sorted(self.artifact.rglob("*"), key=lambda item: item.as_posix())
            if path.is_file()
        }

    def rewrite_archive(self, members: dict[str, bytes]) -> None:
        archive_path = self.artifact / self.contract.archive_name
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in sorted(members.items()):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, content)

    def archive_members(self) -> dict[str, bytes]:
        with zipfile.ZipFile(self.artifact / self.contract.archive_name) as archive:
            return {name: archive.read(name) for name in archive.namelist()}

    def test_verifies_complete_archive_and_reports_without_mutation(self) -> None:
        before = self.tree_bytes()
        result = verify_hosted_deployment(self.contract, self.artifact)
        self.assertEqual(result.gates["complete_archive"], "PASS")
        self.assertEqual(result.archive_paths, self.contract_validation.archive_paths)
        self.assertEqual(self.tree_bytes(), before)

    def test_local_capability_pass_never_upgrades_hosted_execution(self) -> None:
        result = verify_hosted_deployment(self.contract, self.artifact)
        evidence = result.capabilities["exact-retrieval"]
        self.assertEqual(evidence.package_static, "STATICALLY VERIFIED")
        self.assertEqual(evidence.local_execution, "STATICALLY VERIFIED")
        self.assertEqual(evidence.hosted_execution, "NOT VERIFIED")

    def test_reports_do_not_claim_external_mutation_or_retention(self) -> None:
        result = verify_hosted_deployment(self.contract, self.artifact)
        self.assertEqual(result.upload_status, "NOT_PERFORMED")
        self.assertEqual(result.installation_status, "NOT VERIFIED")
        self.assertEqual(result.marketplace_status, "NOT_PERFORMED")
        self.assertEqual(result.publication_status, "NOT_PERFORMED")
        serialized = json.dumps(result, default=lambda value: value.__dict__).casefold()
        self.assertNotIn("deleted", serialized)
        self.assertNotIn("retained", serialized)

    def test_rejects_extra_and_missing_members(self) -> None:
        members = self.archive_members()
        members["extra.txt"] = b"extra"
        self.rewrite_archive(members)
        with self.assertRaisesRegex(HostedDeploymentError, "complete_archive_mismatch"):
            verify_hosted_deployment(self.contract, self.artifact)

        self.reload_and_build()
        members = self.archive_members()
        members.pop("skills/demo/SKILL.md")
        self.rewrite_archive(members)
        with self.assertRaisesRegex(HostedDeploymentError, "complete_archive_mismatch"):
            verify_hosted_deployment(self.contract, self.artifact)

    def test_rejects_malformed_zip_and_changed_archive(self) -> None:
        archive = self.artifact / self.contract.archive_name
        archive.write_bytes(b"not a zip")
        with self.assertRaisesRegex(HostedDeploymentError, "hosted_archive_invalid"):
            verify_hosted_deployment(self.contract, self.artifact)

        self.reload_and_build()
        archive.write_bytes(archive.read_bytes() + b"changed")
        with self.assertRaisesRegex(HostedDeploymentError, "hosted_report_hash_mismatch"):
            verify_hosted_deployment(self.contract, self.artifact)

    def test_rejects_report_hash_disagreement_and_identity_mismatch(self) -> None:
        report_path = self.artifact / "deployment-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["artifact_sha256"] = "0" * 64
        report_path.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(HostedDeploymentError, "hosted_report_hash_mismatch"):
            verify_hosted_deployment(self.contract, self.artifact)

        self.reload_and_build()
        manifest_path = self.artifact / "deployment-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["version"] = "9.9.9"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(HostedDeploymentError, "hosted_manifest_identity_mismatch"):
            verify_hosted_deployment(self.contract, self.artifact)

    def test_rejects_broken_reference_and_invalid_json_asset(self) -> None:
        skill = self.application / "skills" / "demo" / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "\n[missing](references/missing.md)\n", encoding="utf-8")
        self.reload_and_build()
        with self.assertRaisesRegex(HostedDeploymentError, "hosted_reference_missing"):
            verify_hosted_deployment(self.contract, self.artifact)

        self.application = self.base / "second" / "hosted-fixture"
        shutil.copytree(FIXTURE, self.application)
        self.contract_path = self.application / "hosted-openai" / "deployment.json"
        self.add_capability()
        self.add_mapped_file("data/index.json", b"{not-json}\n")
        self.reload_and_build()
        with self.assertRaisesRegex(HostedDeploymentError, "hosted_json_invalid"):
            verify_hosted_deployment(self.contract, self.artifact)

    def test_clean_environment_prefixes_are_removed(self) -> None:
        conversion = self.json_file("conversion.json")
        conversion["verification"]["commands"][0] = {
            "id": "fixture-test",
            "argv": ["{python}", "-c", "import os; raise SystemExit('HOSTED_TEST_SECRET' in os.environ)"],
            "clean_environment_prefixes": ["HOSTED_TEST_"],
        }
        self.write_json("conversion.json", conversion)
        self.reload_and_build()
        with mock.patch.dict(os.environ, {"HOSTED_TEST_SECRET": "private"}):
            result = verify_hosted_deployment(self.contract, self.artifact)
        self.assertEqual(result.capabilities["exact-retrieval"].local_execution, "STATICALLY VERIFIED")

    def test_failing_and_timed_out_local_commands_are_rejected(self) -> None:
        conversion = self.json_file("conversion.json")
        conversion["verification"]["commands"][0]["argv"] = ["{python}", "-c", "raise SystemExit(7)"]
        self.write_json("conversion.json", conversion)
        self.reload_and_build()
        with self.assertRaisesRegex(HostedDeploymentError, "capability_local_verification_failed"):
            verify_hosted_deployment(self.contract, self.artifact)

        conversion = self.json_file("conversion.json")
        conversion["verification"]["commands"][0]["argv"] = ["{python}", "-c", "import time; time.sleep(1)"]
        self.write_json("conversion.json", conversion)
        self.reload_and_build()
        with mock.patch("obvious_one_plugin_framework.hosted_deployment_verifier._COMMAND_TIMEOUT_SECONDS", 0.01):
            with self.assertRaisesRegex(HostedDeploymentError, "capability_local_verification_failed"):
                verify_hosted_deployment(self.contract, self.artifact)

    def test_missing_declared_command_is_rejected(self) -> None:
        profile = replace(self.contract.application.verification, commands=())
        application = replace(self.contract.application, verification=profile)
        self.contract = replace(self.contract, application=application)
        with self.assertRaisesRegex(HostedDeploymentError, "capability_local_verification_command_missing"):
            verify_hosted_deployment(self.contract, self.artifact)

    def test_no_local_test_is_not_applicable_and_optional_fallback_is_static(self) -> None:
        deployment = self.json_file("hosted-openai/deployment.json")
        capability = deployment["validation"]["capabilities"][0]
        capability.update({
            "requirement": "optional",
            "local_verification_test": None,
            "on_unavailable": "use_declared_fallback",
            "fallback": {
                "description": "Use the packaged retrieval script manually.",
                "artifact_paths": ["scripts/retrieve.py"],
                "approval_reference": "../docs/source-decisions.md",
            },
        })
        self.write_json("hosted-openai/deployment.json", deployment)
        self.reload_and_build()
        evidence = verify_hosted_deployment(self.contract, self.artifact).capabilities["exact-retrieval"]
        self.assertEqual(evidence.package_static, "STATICALLY VERIFIED")
        self.assertEqual(evidence.local_execution, "NOT APPLICABLE")
        self.assertEqual(evidence.hosted_execution, "NOT VERIFIED")


if __name__ == "__main__":
    unittest.main()
