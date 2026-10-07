from __future__ import annotations

import copy
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from plugin_builder_core.implementation_plan import canonical_bytes, compile_plan
from plugin_builder_core.inspection import inspect_design_package


def proposal_v2() -> dict:
    payload = json.loads((FIXTURES / "plan-create.json").read_text(encoding="utf-8"))
    payload["schema"] = "plugin-builder-plan-proposal-v2"
    payload["capabilities"] = [
        {
            "schema": "plugin-builder-capability-v1",
            "id": "normalize-content",
            "requirement_ids": ["RQ1"],
            "skill_bindings": ["answering-structured-requests"],
            "realization_need": "TOOL_REQUIRED",
            "tool_id": "normalize-input",
            "runtime_targets": ["ChatGPT Work Local/Desktop", "Codex"],
            "evidence_targets": ["STRUCTURE", "OPERATION", "INSTALLED_REALIZATION", "BEHAVIOR"],
        },
        {
            "schema": "plugin-builder-capability-v1",
            "id": "traceability-review",
            "requirement_ids": ["AC1"],
            "skill_bindings": ["checking-traceability"],
            "realization_need": "SKILL_ONLY",
            "tool_id": None,
            "runtime_targets": ["ChatGPT Work Local/Desktop", "Codex"],
            "evidence_targets": ["STRUCTURE", "BEHAVIOR"],
        },
    ]
    tool = payload["tools"][0]
    tool["schema"] = "plugin-builder-application-tool-v2"
    tool["capability_ids"] = ["normalize-content"]
    tool["operation"] = {
        "id": "normalize-input",
        "protocol": "MCP_TOOL_CALL",
        "input_schema_sha256": sha256(canonical_bytes(tool["input_schema"])).hexdigest(),
        "output_schema_sha256": sha256(canonical_bytes(tool["output_schema"])).hexdigest(),
        "side_effect_class": "NONE",
        "idempotent": True,
        "capability_ids": ["normalize-content"],
    }
    tool["dependencies"] = [
        {
            "id": "normalizer-service",
            "type": "SERVICE",
            "provider": "REMOTE_SERVICE",
            "version": None,
            "sha256": None,
            "runtime_targets": ["ChatGPT Work Local/Desktop", "Codex"],
            "setup_owner": "SERVICE_OPERATOR",
            "required": True,
            "absence_policy": "BLOCK",
        }
    ]
    tool["permissions"] = [
        {
            "id": "network",
            "target_runtime": target,
            "grant_source": "OWNER",
            "required": True,
            "purpose": "Reach the approved normalization service.",
            "verification": "Observe installed Skill-to-tool evidence.",
        }
        for target in ("ChatGPT Work Local/Desktop", "Codex")
    ]
    tool["fallback"] = {
        "policy": "BLOCK",
        "trigger_conditions": ["The approved service is unavailable."],
        "alternative_operation_id": None,
        "preserved_requirement_ids": [],
        "degraded_requirement_ids": ["RQ1"],
    }
    tool["mcp"] = {
        "server_id": "normalizer",
        "config_file": "mcp.json",
        "transport": "streamable-http",
        "permission_scopes": ["normalize:execute"],
        "authentication": "NOT_REQUIRED",
        "setup": "SERVICE_OPERATOR",
        "service_boundary": "Normalize approved structured content.",
        "url": "https://example.com/mcp",
    }
    tool["realizations"] = [
        {
            "target_runtime": target,
            "mechanism": "MCP_REMOTE_HTTPS",
            "adapter_id": "mcp-streamable-http",
            "adapter_version": "1",
            "exposed_capability": "normalize-input",
            "operation_id": "normalize-input",
            "transport": "MCP_STREAMABLE_HTTP",
            "execution_location": "REMOTE_SERVICE",
            "dependency_ids": ["normalizer-service"],
            "permission_ids": ["network"],
            "setup_requirements": ["Configure the approved HTTPS MCP endpoint."],
            "setup_owner": "SERVICE_OPERATOR",
            "feasibility_state": "FEASIBLE_WITH_SETUP",
            "evidence_policy": "DEFERRED_ALLOWED",
        }
        for target in ("ChatGPT Work Local/Desktop", "Codex")
    ]
    return payload


class RuntimeFeasibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        package = self.root / "design.zip"
        with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            fixture = FIXTURES / "design-package-create"
            for path in sorted(fixture.iterdir(), key=lambda item: item.name):
                archive.write(path, path.name)
        self.workspace = self.root / "workspace"
        inspected = inspect_design_package(package, self.workspace, "create")
        self.assertEqual(inspected.status, "PASS")
        self.inspection = self.workspace / "inspection.json"
        self.output = self.workspace / "implementation-plan.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def compile(self, payload: dict):
        return compile_plan(self.inspection, payload, self.output)

    def test_v2_closure_is_deterministic_and_hashes_every_runtime_boundary(self) -> None:
        first = self.compile(proposal_v2())
        first_bytes = self.output.read_bytes()
        second = self.compile(proposal_v2())
        self.assertEqual(first.status, "PASS")
        self.assertEqual(second, first)
        self.assertEqual(self.output.read_bytes(), first_bytes)
        for digest in (
            first.plan_sha256,
            first.tools_sha256,
            first.capabilities_sha256,
            first.realizations_sha256,
            first.adapter_registry_sha256,
        ):
            self.assertRegex(str(digest), r"^[0-9a-f]{64}$")
        plan = json.loads(first_bytes)
        self.assertEqual(
            [item["id"] for item in plan["capabilities"]],
            ["normalize-content", "traceability-review"],
        )

    def test_capability_tool_skill_and_requirement_closure_fails_exactly(self) -> None:
        payload = proposal_v2()
        payload["capabilities"][0]["tool_id"] = "missing-tool"
        payload["tools"][0]["capability_ids"] = ["missing-capability"]
        payload["tools"][0]["operation"]["capability_ids"] = ["missing-capability"]
        outcome = self.compile(payload)
        self.assertEqual(outcome.status, "FAIL")
        self.assertIn("capability.normalize-content.tool_unknown:missing-tool", outcome.errors)
        self.assertIn("tool.normalize-input.capability_unknown:missing-capability", outcome.errors)
        self.assertFalse(self.output.exists())

    def test_required_unverified_unsupported_and_blocked_paths_stop_before_w1(self) -> None:
        for state in ("NOT VERIFIED", "UNSUPPORTED", "BLOCKED"):
            with self.subTest(state=state):
                payload = proposal_v2()
                realization = payload["tools"][0]["realizations"][0]
                realization["feasibility_state"] = state
                if state == "UNSUPPORTED":
                    realization.update(
                        mechanism="UNSUPPORTED",
                        adapter_id="unsupported",
                        transport="NONE",
                        execution_location="RUNTIME_HOST",
                        dependency_ids=[],
                        permission_ids=[],
                        setup_requirements=[],
                        setup_owner="RUNTIME",
                    )
                outcome = self.compile(payload)
                self.assertEqual(outcome.status, "BLOCKED")
                self.assertIn(
                    f"capability.normalize-content.runtime_infeasible:ChatGPT Work Local/Desktop:{state}",
                    outcome.blockers,
                )
                self.assertTrue(self.output.is_file())
                self.assertFalse((self.workspace / "candidate").exists())

    def test_feasible_with_setup_requires_complete_setup_contract(self) -> None:
        payload = proposal_v2()
        payload["tools"][0]["realizations"][0]["setup_requirements"] = []
        outcome = self.compile(payload)
        self.assertEqual(outcome.status, "FAIL")
        self.assertIn(
            "realization.ChatGPT Work Local/Desktop.setup_requirements_required",
            outcome.errors,
        )

    def test_optional_omission_and_behavior_preserving_alternative_are_executable(self) -> None:
        optional = proposal_v2()
        optional_tool = optional["tools"][0]
        optional_tool["required"] = False
        optional_tool["fallback"]["policy"] = "OMIT_OPTIONAL"
        unavailable = optional_tool["realizations"][0]
        unavailable.update(
            mechanism="UNSUPPORTED",
            adapter_id="unsupported",
            transport="NONE",
            execution_location="RUNTIME_HOST",
            dependency_ids=[],
            permission_ids=[],
            setup_requirements=[],
            setup_owner="RUNTIME",
            feasibility_state="UNSUPPORTED",
        )
        self.assertEqual(self.compile(optional).status, "PASS")

        alternative = proposal_v2()
        primary = alternative["tools"][0]
        unavailable = primary["realizations"][0]
        unavailable.update(
            mechanism="UNSUPPORTED",
            adapter_id="unsupported",
            transport="NONE",
            execution_location="RUNTIME_HOST",
            dependency_ids=[],
            permission_ids=[],
            setup_requirements=[],
            setup_owner="RUNTIME",
            feasibility_state="UNSUPPORTED",
        )
        fallback_tool = copy.deepcopy(primary)
        fallback_tool["id"] = "normalize-input-fallback"
        fallback_tool["operation"]["id"] = "normalize-input-fallback"
        for item in fallback_tool["realizations"]:
            item["operation_id"] = "normalize-input-fallback"
            item["exposed_capability"] = "normalize-input-fallback"
            item.update(
                mechanism="MCP_REMOTE_HTTPS",
                adapter_id="mcp-streamable-http",
                transport="MCP_STREAMABLE_HTTP",
                execution_location="REMOTE_SERVICE",
                dependency_ids=["normalizer-service"],
                permission_ids=["network"],
                setup_requirements=["Configure the approved HTTPS MCP endpoint."],
                setup_owner="SERVICE_OPERATOR",
                feasibility_state="FEASIBLE_WITH_SETUP",
            )
        primary["fallback"].update(
            policy="ALTERNATIVE",
            alternative_operation_id="normalize-input-fallback",
            preserved_requirement_ids=["RQ1"],
            degraded_requirement_ids=[],
        )
        alternative["tools"].append(fallback_tool)
        self.assertEqual(self.compile(alternative).status, "PASS")

        primary["fallback"]["degraded_requirement_ids"] = ["RQ1"]
        degraded = self.compile(alternative)
        self.assertEqual(degraded.status, "BLOCKED")
        self.assertIn(
            "capability.normalize-content.fallback_design_approval_required:ChatGPT Work Local/Desktop",
            degraded.blockers,
        )

    def test_new_v1_proposal_is_blocked_without_mutating_existing_plan(self) -> None:
        sentinel = b"approved legacy plan bytes\n"
        self.output.write_bytes(sentinel)
        legacy = json.loads((FIXTURES / "plan-create-v1-legacy.json").read_text(encoding="utf-8"))
        outcome = self.compile(legacy)
        self.assertEqual(outcome.status, "BLOCKED")
        self.assertEqual(outcome.blockers, ("plan.proposal_v2_required",))
        self.assertEqual(self.output.read_bytes(), sentinel)


if __name__ == "__main__":
    unittest.main()
