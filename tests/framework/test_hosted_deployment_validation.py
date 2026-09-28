from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from obvious_one_plugin_framework.hosted_deployment_contract import (
    HostedDeploymentError,
    load_hosted_deployment_contract,
)
from obvious_one_plugin_framework.hosted_deployment_planner import validate_hosted_deployment


FIXTURE = Path(__file__).parent / "fixtures" / "hosted-deployment" / "application"


class HostedDeploymentValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "hosted-fixture"
        shutil.copytree(FIXTURE, self.root)
        self.contract_path = self.root / "hosted-openai" / "deployment.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def payload(self) -> dict:
        return json.loads(self.contract_path.read_text(encoding="utf-8"))

    def write(self, payload: dict) -> None:
        self.contract_path.write_text(json.dumps(payload), encoding="utf-8")

    def add_exact_retrieval_capability(self) -> None:
        tool = self.root / "scripts" / "retrieve.py"
        tool.parent.mkdir()
        tool.write_text("print('fixture')\n", encoding="utf-8")
        distribution_path = self.root / "openclaw" / "distribution.json"
        distribution = json.loads(distribution_path.read_text(encoding="utf-8"))
        distribution["include_files"].append("scripts/retrieve.py")
        distribution["content_rules"][0]["paths"].append("scripts/retrieve.py")
        distribution_path.write_text(json.dumps(distribution), encoding="utf-8")
        payload = self.payload()
        payload["content"]["canonical_mappings"].append({
            "id": "retrieval-tool", "source_kind": "canonical_application",
            "source": "scripts/retrieve.py", "target": "scripts/retrieve.py",
            "copy_mode": "copy_file", "classification": "text",
            "redistribution_reference": "approved-text"
        })
        payload["validation"]["capabilities"] = [{
            "id": "exact-retrieval", "requirement": "required",
            "provider_kind": "packaged_executable", "artifact_paths": ["scripts/retrieve.py"],
            "local_verification_test": "fixture-test",
            "hosted_verification": "required_after_install", "on_unavailable": "block", "fallback": None
        }]
        self.write(payload)

    def test_valid_complete_mapping_has_exact_member_set(self) -> None:
        self.add_exact_retrieval_capability()
        validation = validate_hosted_deployment(load_hosted_deployment_contract(self.contract_path))
        self.assertEqual(validation.archive_paths, (
            ".codex-plugin/plugin.json", "plugin.json", "scripts/retrieve.py", "skills/demo/SKILL.md"
        ))
        self.assertEqual(validation.hosted_capabilities["exact-retrieval"], "NOT VERIFIED")
        self.assertEqual(validation.local_capabilities["exact-retrieval"], "NOT VERIFIED")

    def test_adapter_cannot_duplicate_canonical_skill(self) -> None:
        router = self.root / "hosted-openai" / "adapter" / "skills" / "example" / "SKILL.md"
        router.parent.mkdir(parents=True)
        router.write_text("duplicate", encoding="utf-8")
        payload = self.payload()
        payload["content"]["adapter_mappings"].append({
            "id": "duplicate-skill", "source_kind": "hosted_adapter",
            "source": "adapter/skills/example/SKILL.md", "target": "skills/example/SKILL.md",
            "copy_mode": "copy_file", "classification": "text",
            "redistribution_reference": "../docs/source-decisions.md"
        })
        self.write(payload)
        with self.assertRaisesRegex(HostedDeploymentError, "adapter_duplicates_canonical_content"):
            validate_hosted_deployment(load_hosted_deployment_contract(self.contract_path))

    def test_local_build_cannot_mark_external_channel_current(self) -> None:
        validation = validate_hosted_deployment(load_hosted_deployment_contract(self.contract_path))
        self.assertEqual(validation.generated_channels["openai_hosted"], "PENDING_ACTION")
        self.assertEqual(validation.generated_channels["obvious_one"], validation.declared_channels["obvious_one"])
        self.assertEqual(validation.generated_channels["openai_public"], "UNPUBLISHED")

    def test_manifests_must_be_present_and_match_identity_and_version(self) -> None:
        payload = self.payload()
        payload["content"]["adapter_mappings"] = payload["content"]["adapter_mappings"][1:]
        self.write(payload)
        with self.assertRaisesRegex(HostedDeploymentError, "portable_manifest_missing"):
            validate_hosted_deployment(load_hosted_deployment_contract(self.contract_path))

        payload = json.loads((FIXTURE / "hosted-openai" / "deployment.json").read_text(encoding="utf-8"))
        manifest = self.root / "hosted-openai" / "adapter" / "plugin.json"
        content = json.loads(manifest.read_text(encoding="utf-8"))
        content["version"] = "9.9.9"
        manifest.write_text(json.dumps(content), encoding="utf-8")
        self.write(payload)
        with self.assertRaisesRegex(HostedDeploymentError, "hosted_manifest_identity_mismatch"):
            validate_hosted_deployment(load_hosted_deployment_contract(self.contract_path))

    def test_expected_skill_closure_and_explicit_policy_are_enforced(self) -> None:
        payload = self.payload()
        payload["validation"]["expected_skills"] = ["demo", "missing"]
        self.write(payload)
        with self.assertRaisesRegex(HostedDeploymentError, "expected_skill_mismatch"):
            validate_hosted_deployment(load_hosted_deployment_contract(self.contract_path))

        payload["validation"]["expected_skills"] = ["demo"]
        payload["validation"]["explicit_only_skills"] = ["demo"]
        self.write(payload)
        with self.assertRaisesRegex(HostedDeploymentError, "explicit_only_policy_missing"):
            validate_hosted_deployment(load_hosted_deployment_contract(self.contract_path))

    def test_fallback_artifacts_forbidden_names_and_size_limit_are_enforced(self) -> None:
        payload = self.payload()
        payload["validation"]["capabilities"] = [{
            "id": "optional-adapter", "requirement": "optional", "provider_kind": "external_adapter",
            "artifact_paths": [], "local_verification_test": None,
            "hosted_verification": "required_after_install", "on_unavailable": "use_declared_fallback",
            "fallback": {"description": "Use bundled data", "artifact_paths": ["missing.json"], "approval_reference": "../docs/source-decisions.md"}
        }]
        self.write(payload)
        with self.assertRaisesRegex(HostedDeploymentError, "fallback_artifact_missing"):
            validate_hosted_deployment(load_hosted_deployment_contract(self.contract_path))

        payload = self.payload()
        payload["validation"]["capabilities"] = []
        payload["content"]["adapter_mappings"][0]["target"] = ".env"
        self.write(payload)
        with self.assertRaisesRegex(HostedDeploymentError, "forbidden_archive_path"):
            validate_hosted_deployment(load_hosted_deployment_contract(self.contract_path))

        payload = self.payload()
        payload["content"]["adapter_mappings"][0]["target"] = "plugin.json"
        payload["target"]["max_archive_bytes"] = 1
        self.write(payload)
        with self.assertRaisesRegex(HostedDeploymentError, "hosted_archive_size_limit"):
            validate_hosted_deployment(load_hosted_deployment_contract(self.contract_path))


if __name__ == "__main__":
    unittest.main()
