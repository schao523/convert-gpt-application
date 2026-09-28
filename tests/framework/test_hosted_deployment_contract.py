from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from obvious_one_plugin_framework.hosted_deployment_contract import (
    HostedDeploymentError,
    load_hosted_deployment_contract,
    load_hosted_identity,
)


FIXTURE = Path(__file__).parent / "fixtures" / "hosted-deployment" / "application"


class HostedDeploymentContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "hosted-fixture"
        shutil.copytree(FIXTURE, self.root)
        self.contract_path = self.root / "hosted-openai" / "deployment.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def read_contract(self) -> dict:
        return json.loads(self.contract_path.read_text(encoding="utf-8"))

    def write_contract(self, payload: dict) -> Path:
        self.contract_path.write_text(json.dumps(payload), encoding="utf-8")
        return self.contract_path

    def update_contract(self, *, target_version: str = "1.1.0", identity_file: str = "hosted-identity.json") -> Path:
        payload = self.read_contract()
        payload["operation"] = "OPENAI_HOSTED_UPDATE"
        payload["identity"]["record"] = identity_file
        payload["target"]["version"] = target_version
        return self.write_contract(payload)

    def test_create_requires_no_identity_record(self) -> None:
        contract = load_hosted_deployment_contract(self.contract_path)
        self.assertEqual(contract.operation, "OPENAI_HOSTED_CREATE")
        self.assertIsNone(contract.identity_record)

    def test_update_loads_confirmed_identity_and_newer_version(self) -> None:
        contract = load_hosted_deployment_contract(self.update_contract())
        self.assertEqual(contract.identity_record.package_name, "gpt-hosted-fixture")
        self.assertEqual(contract.target_version, "1.1.0")

    def test_update_requires_newer_version(self) -> None:
        with self.assertRaisesRegex(HostedDeploymentError, "hosted_version_not_advanced"):
            load_hosted_deployment_contract(self.update_contract(target_version="1.0.0"))

    def test_identity_proposal_cannot_be_used_as_identity_record(self) -> None:
        proposal = self.root / "hosted-openai" / "hosted-identity-proposal.json"
        proposal.write_text(json.dumps({"proposal_schema": "hosted-identity-proposal-v1"}), encoding="utf-8")
        with self.assertRaisesRegex(HostedDeploymentError, "hosted_identity_unapproved"):
            load_hosted_deployment_contract(self.update_contract(identity_file=proposal.name))

    def test_create_rejects_identity_record(self) -> None:
        payload = self.read_contract()
        payload["identity"]["record"] = "hosted-identity.json"
        with self.assertRaisesRegex(HostedDeploymentError, "hosted_identity_forbidden"):
            load_hosted_deployment_contract(self.write_contract(payload))

    def test_update_requires_matching_package_name(self) -> None:
        payload = self.read_contract()
        payload["identity"]["package_name"] = "another-package"
        self.write_contract(payload)
        with self.assertRaisesRegex(HostedDeploymentError, "hosted_package_name_mismatch"):
            load_hosted_deployment_contract(self.update_contract())

    def test_required_capability_cannot_use_fallback(self) -> None:
        payload = self.read_contract()
        payload["validation"]["capabilities"] = [{
            "id": "runner",
            "requirement": "required",
            "provider_kind": "packaged_executable",
            "artifact_paths": ["scripts/run.py"],
            "local_verification_test": "fixture-test",
            "hosted_verification": "required_after_install",
            "on_unavailable": "use_declared_fallback",
            "fallback": {
                "description": "Do less",
                "artifact_paths": [],
                "approval_reference": "../docs/source-decisions.md"
            }
        }]
        with self.assertRaisesRegex(HostedDeploymentError, "invalid_required_capability_policy"):
            load_hosted_deployment_contract(self.write_contract(payload))

    def test_packaged_executable_requires_artifact(self) -> None:
        payload = self.read_contract()
        payload["validation"]["capabilities"] = [{
            "id": "runner", "requirement": "required", "provider_kind": "packaged_executable",
            "artifact_paths": [], "local_verification_test": "fixture-test",
            "hosted_verification": "required_after_install", "on_unavailable": "block", "fallback": None
        }]
        with self.assertRaisesRegex(HostedDeploymentError, "required_capability_artifact_missing"):
            load_hosted_deployment_contract(self.write_contract(payload))

    def test_optional_fallback_policy_requires_fallback(self) -> None:
        payload = self.read_contract()
        payload["validation"]["capabilities"] = [{
            "id": "adapter", "requirement": "optional", "provider_kind": "external_adapter",
            "artifact_paths": [], "local_verification_test": None,
            "hosted_verification": "required_after_install", "on_unavailable": "use_declared_fallback", "fallback": None
        }]
        with self.assertRaisesRegex(HostedDeploymentError, "capability_decision_required"):
            load_hosted_deployment_contract(self.write_contract(payload))

    def test_local_verification_test_must_be_declared(self) -> None:
        payload = self.read_contract()
        payload["validation"]["required_application_tests"] = ["missing-test"]
        with self.assertRaisesRegex(HostedDeploymentError, "unknown_application_test"):
            load_hosted_deployment_contract(self.write_contract(payload))

    def test_duplicate_mapping_ids_and_casefold_targets_are_rejected(self) -> None:
        payload = self.read_contract()
        duplicate = dict(payload["content"]["adapter_mappings"][0])
        duplicate["target"] = "PLUGIN.JSON"
        payload["content"]["adapter_mappings"].append(duplicate)
        with self.assertRaisesRegex(HostedDeploymentError, "duplicate_mapping_id"):
            load_hosted_deployment_contract(self.write_contract(payload))
        duplicate["id"] = "portable-manifest-copy"
        with self.assertRaisesRegex(HostedDeploymentError, "target_path_collision"):
            load_hosted_deployment_contract(self.write_contract(payload))

    def test_unknown_keys_are_rejected_at_nested_levels(self) -> None:
        mutations = [
            ([], "unexpected"),
            (["lineage"], "unexpected"),
            (["identity"], "unexpected"),
            (["target"], "unexpected"),
            (["content"], "unexpected"),
            (["validation"], "unexpected"),
            (["channels", "openai_hosted"], "unexpected"),
            (["content", "canonical_mappings", 0], "unexpected"),
        ]
        for path, key in mutations:
            with self.subTest(path=path):
                payload = self.read_contract()
                current = payload
                for part in path:
                    current = current[part]
                current[key] = True
                with self.assertRaisesRegex(HostedDeploymentError, "unknown_key"):
                    load_hosted_deployment_contract(self.write_contract(payload))

    def test_invalid_operation_semver_provider_and_channel_status_are_rejected(self) -> None:
        payload = self.read_contract()
        payload["operation"] = "UPSERT"
        with self.assertRaisesRegex(HostedDeploymentError, "invalid_operation"):
            load_hosted_deployment_contract(self.write_contract(payload))
        payload = self.read_contract()
        payload["operation"] = "OPENAI_HOSTED_CREATE"
        payload["target"]["version"] = "version-one"
        with self.assertRaisesRegex(HostedDeploymentError, "invalid_semver"):
            load_hosted_deployment_contract(self.write_contract(payload))
        payload["target"]["version"] = "1.1.0-01"
        with self.assertRaisesRegex(HostedDeploymentError, "invalid_semver"):
            load_hosted_deployment_contract(self.write_contract(payload))
        payload = self.read_contract()
        payload["target"]["version"] = "1.1.0"
        payload["channels"]["openai_hosted"]["status"] = "READY"
        with self.assertRaisesRegex(HostedDeploymentError, "invalid_channel_status"):
            load_hosted_deployment_contract(self.write_contract(payload))
        payload["channels"]["openai_hosted"]["status"] = "UNPUBLISHED"
        payload["validation"]["capabilities"] = [{
            "id": "memory", "requirement": "optional", "provider_kind": "model_memory",
            "artifact_paths": [], "local_verification_test": None,
            "hosted_verification": "required_after_install", "on_unavailable": "block", "fallback": None
        }]
        with self.assertRaisesRegex(HostedDeploymentError, "invalid_capability_provider"):
            load_hosted_deployment_contract(self.write_contract(payload))

    def test_absolute_escaping_and_windows_alias_paths_are_rejected(self) -> None:
        for value in ("/absolute", "../escape", "C:/private", "folder\\alias"):
            with self.subTest(value=value):
                payload = self.read_contract()
                payload["content"]["canonical_mappings"][0]["target"] = value
                with self.assertRaisesRegex(HostedDeploymentError, "invalid_relative_path"):
                    load_hosted_deployment_contract(self.write_contract(payload))

    def test_channel_state_requires_evidence(self) -> None:
        payload = self.read_contract()
        payload["channels"]["openai_hosted"]["evidence"] = ""
        with self.assertRaisesRegex(HostedDeploymentError, "channel_evidence_required"):
            load_hosted_deployment_contract(self.write_contract(payload))

    def test_identity_rejects_sensitive_fields(self) -> None:
        identity_path = self.root / "hosted-openai" / "hosted-identity.json"
        payload = json.loads(identity_path.read_text(encoding="utf-8"))
        payload["workspace_id"] = "private-workspace"
        identity_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(HostedDeploymentError, "sensitive_identity_field"):
            load_hosted_identity(identity_path)


if __name__ == "__main__":
    unittest.main()
