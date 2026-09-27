from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from obvious_one_plugin_framework.hosted_deployment_planner import plan_hosted_deployment


FIXTURE = Path(__file__).parent / "fixtures" / "hosted-deployment" / "application"


class HostedDeploymentPlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "hosted-fixture"
        shutil.copytree(FIXTURE, self.root)
        self.application = self.root / "conversion.json"
        self.output = Path(self.temporary.name) / "proposal.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def diagnostic_codes(self, result) -> list[str]:
        return [item.code for item in result.diagnostics]

    def distribution(self) -> tuple[Path, dict]:
        path = self.root / "openclaw" / "distribution.json"
        return path, json.loads(path.read_text(encoding="utf-8"))

    def test_create_plan_requires_no_identity_or_marketplace(self) -> None:
        result = plan_hosted_deployment(self.application, "OPENAI_HOSTED_CREATE", self.output)
        proposal = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(result.code, "hosted_deployment_decisions_required")
        self.assertNotIn("hosted_identity", proposal["required_inputs"])
        self.assertNotIn("marketplace", proposal["required_inputs"])
        self.assertEqual(proposal["operation"], "OPENAI_HOSTED_CREATE")

    def test_update_plan_reports_missing_identity_decision(self) -> None:
        result = plan_hosted_deployment(self.application, "OPENAI_HOSTED_UPDATE", self.output)
        self.assertEqual(result.status, "BLOCKED")
        self.assertIn("hosted_identity_required", self.diagnostic_codes(result))

    def test_proposal_is_deterministic_and_does_not_mutate_approved_contract(self) -> None:
        contract = self.root / "hosted-openai" / "deployment.json"
        before = contract.read_bytes()
        first = plan_hosted_deployment(self.application, "OPENAI_HOSTED_CREATE", self.output)
        second_output = Path(self.temporary.name) / "proposal-two.json"
        second = plan_hosted_deployment(self.application, "OPENAI_HOSTED_CREATE", second_output)
        self.assertEqual(self.output.read_bytes(), second_output.read_bytes())
        self.assertEqual(first.evidence, second.evidence)
        self.assertEqual(contract.read_bytes(), before)

    def test_existing_destination_is_preserved(self) -> None:
        self.output.write_text("keep", encoding="utf-8")
        result = plan_hosted_deployment(self.application, "OPENAI_HOSTED_CREATE", self.output)
        self.assertEqual(result.code, "hosted_deployment_proposal_exists")
        self.assertEqual(self.output.read_text(encoding="utf-8"), "keep")

    def test_unclassified_and_ambiguous_canonical_files_are_reported(self) -> None:
        path, payload = self.distribution()
        (self.root / "UNCLASSIFIED.txt").write_text("content", encoding="utf-8")
        payload["include_files"].append("UNCLASSIFIED.txt")
        path.write_text(json.dumps(payload), encoding="utf-8")
        result = plan_hosted_deployment(self.application, "OPENAI_HOSTED_CREATE", self.output)
        self.assertIn("unclassified_files", self.diagnostic_codes(result))

        self.output.unlink()
        payload["content_rules"].append({
            "id": "overlap", "paths": [], "prefixes": ["skills"], "classification": "text",
            "redistribution": {"status": "approved", "provenance": "docs/source-decisions.md"}
        })
        path.write_text(json.dumps(payload), encoding="utf-8")
        result = plan_hosted_deployment(self.application, "OPENAI_HOSTED_CREATE", self.output)
        self.assertIn("ambiguous_file_classification", self.diagnostic_codes(result))

    def test_adapter_rights_and_portable_duplication_remain_unresolved(self) -> None:
        duplicate = self.root / "hosted-openai" / "adapter" / "skills" / "demo" / "SKILL.md"
        duplicate.parent.mkdir(parents=True)
        duplicate.write_text("duplicate", encoding="utf-8")
        result = plan_hosted_deployment(self.application, "OPENAI_HOSTED_CREATE", self.output)
        codes = self.diagnostic_codes(result)
        self.assertIn("adapter_rights_unresolved", codes)
        self.assertIn("adapter_duplicates_canonical_content", codes)


if __name__ == "__main__":
    unittest.main()
