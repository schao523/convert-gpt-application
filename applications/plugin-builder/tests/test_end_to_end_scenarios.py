from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TESTS = Path(__file__).parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from test_create_candidate import prepared_workspace, read_result, run_cli
import test_update_candidate as update_tests


def _failing_tool(proposal: dict) -> None:
    recipe = next(item for item in proposal["files"] if item["path"] == "tools/normalize.py")
    recipe["inline_text"] = "raise SystemExit(23)\n"
    recipe["source_sha256"] = sha256(recipe["inline_text"].encode()).hexdigest()


def _runtime_native_optional(proposal: dict) -> None:
    tool = proposal["tools"][0]
    skill = next(item for item in proposal["files"] if item["path"] == "skills/answering-structured-requests/SKILL.md")
    skill["inline_text"] += "\nThe optional runtime-exposed capability is `desktop-picker`; use it only when available.\n"
    skill["source_sha256"] = sha256(skill["inline_text"].encode("utf-8")).hexdigest()
    tool.update({
        "required": False, "implementation_kind": "RUNTIME_NATIVE", "files": [],
        "execution": None, "fixtures": None, "mcp": None,
        "runtime_capability": {"name": "desktop-picker", "runtimes": tool["runtime_targets"]},
        "dependencies": [{
            "id": "desktop-picker-runtime", "type": "RUNTIME_CAPABILITY",
            "provider": "RUNTIME_PROVIDED", "version": None, "sha256": None,
            "runtime_targets": tool["runtime_targets"], "setup_owner": "RUNTIME",
            "required": False, "absence_policy": "FALLBACK",
        }],
        "permissions": [{
            "id": "runtime:native", "target_runtime": target,
            "grant_source": "RUNTIME", "required": False,
            "purpose": "Use the runtime-provided desktop picker.",
            "verification": "Observe installed runtime capability discovery.",
        } for target in tool["runtime_targets"]],
        "fallback": {
            "policy": "OMIT_OPTIONAL",
            "trigger_conditions": ["The runtime-native picker is unavailable."],
            "alternative_operation_id": None,
            "preserved_requirement_ids": [],
            "degraded_requirement_ids": ["RQ1"],
        },
        "verification": {"kind": "RUNTIME_CAPABILITY", "argv": [], "network": False},
        "realizations": [{
            "target_runtime": target, "mechanism": "RUNTIME_NATIVE",
            "adapter_id": "runtime-native", "adapter_version": "1",
            "exposed_capability": "desktop-picker", "operation_id": "normalize-input",
            "transport": "RUNTIME_API", "execution_location": "RUNTIME_HOST",
            "dependency_ids": ["desktop-picker-runtime"],
            "permission_ids": ["runtime:native"], "setup_requirements": [],
            "setup_owner": "RUNTIME", "feasibility_state": "NOT VERIFIED",
            "evidence_policy": "DEFERRED_ALLOWED",
        } for target in tool["runtime_targets"]],
    })
    tool["operation"]["protocol"] = "RUNTIME_API"
    proposal["files"] = [item for item in proposal["files"] if item["path"] != "tools/normalize.py"]
    proposal["expected_members"].remove("tools/normalize.py")
    proposal["expected_members"] = [
        item for item in proposal["expected_members"]
        if item not in {"mcp.json", ".mcp.json"}
    ]
    proposal["checks"] = [item for item in proposal["checks"] if item["id"] != "normalize-self-test"]
    requirement = next(item for item in proposal["requirements"] if item["id"] == "RQ1")
    requirement["implementation_paths"] = [item for item in requirement["implementation_paths"] if item != "tools/normalize.py"]
    requirement["evidence_targets"] = [item for item in requirement["evidence_targets"] if item != "normalize-self-test"]


def _mcp_optional(proposal: dict) -> None:
    tool = proposal["tools"][0]
    proposal["files"] = [item for item in proposal["files"] if item["path"] != "tools/normalize.py"]
    proposal["expected_members"].remove("tools/normalize.py")
    proposal["checks"] = [item for item in proposal["checks"] if item["id"] != "normalize-self-test"]
    requirement = next(item for item in proposal["requirements"] if item["id"] == "RQ1")
    requirement["implementation_paths"] = [item for item in requirement["implementation_paths"] if item != "tools/normalize.py"]
    requirement["implementation_paths"].append("mcp.json")
    requirement["evidence_targets"] = [item for item in requirement["evidence_targets"] if item != "normalize-self-test"]
    tool.update({
        "required": False, "implementation_kind": "MCP_ADAPTER", "files": [],
        "execution": None, "fixtures": None, "runtime_capability": None,
        "configuration": {"authentication": "USER_CONFIGURED", "setup": "OWNER_CONFIGURED"},
        "fallback": {
            "policy": "OMIT_OPTIONAL",
            "trigger_conditions": ["The external enrichment service is unavailable."],
            "alternative_operation_id": None,
            "preserved_requirement_ids": [],
            "degraded_requirement_ids": ["RQ1"],
        },
    })
    tool["mcp"].update({"server_id": "example", "service_boundary": "external example"})


class EndToEndScenarios(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_t8_local_mcp_operation_does_not_upgrade_installed_realizations(self) -> None:
        from plugin_builder_core.tool_verification import verify_application_tool

        script = TESTS / "runtime" / "prepare-runtime-scenarios.py"
        output = self.root / "scenario-inputs"
        completed = subprocess.run(
            [sys.executable, "-B", str(script), "--base-plan", str(TESTS / "fixtures/plan-create.json"), "--output", str(output)],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        t8 = json.loads((output / "t8-local-mcp-plan.json").read_text(encoding="utf-8"))
        workspace = prepared_workspace(self.root, mutate=lambda proposal: (proposal.clear(), proposal.update(t8)))
        self.assertEqual(run_cli("build", "--session", str(workspace / "session.json"), "--json").returncode, 0)
        result = verify_application_tool(t8["tools"][0], workspace / "candidate", allow_loopback=True)
        self.assertEqual(result["state"], "PASS", result)
        self.assertEqual(result["environment"], "BUILD_HOST_LOCAL_MCP")
        self.assertTrue(all(item["state"] == "NOT VERIFIED" for item in result["realizations"]))
        verified = run_cli("verify", "--session", str(workspace / "session.json"), "--allow-loopback", "--json")
        self.assertEqual(verified.returncode, 0, verified.stdout)
        report = json.loads((workspace / "verification-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["tools"][0]["state"], "PASS")
        self.assertEqual(report["tools"][0]["environment"], "BUILD_HOST_LOCAL_MCP")
        self.assertTrue(all(item["state"] == "NOT VERIFIED" for item in report["tools"][0]["realizations"]))

    def test_t1_behavior_only_design_reaches_w1_without_candidate(self) -> None:
        workspace = prepared_workspace(self.root, approve=False)
        session = json.loads((workspace / "session.json").read_text(encoding="utf-8"))
        self.assertEqual(session["stage"], "W1")
        self.assertIsNone(session["candidate"])
        self.assertFalse((workspace / "candidate").exists())

    def test_t2_create_with_bundled_local_tool_reaches_verified_deterministic_zip(self) -> None:
        workspace = prepared_workspace(self.root)
        for command in (("build",), ("verify",)):
            self.assertEqual(run_cli(*command, "--session", str(workspace / "session.json"), "--json").returncode, 0)
        self.assertEqual(run_cli("approve-w2", "--session", str(workspace / "session.json"), "--confirmed-by", "owner", "--evidence", "reviewed", "--json").returncode, 0)
        first = run_cli("package", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(first.returncode, 0, first.stdout)
        payload = (workspace / "dist/sample-plugin.zip").read_bytes()
        self.assertEqual(run_cli("package", "--session", str(workspace / "session.json"), "--json").returncode, 0)
        self.assertEqual((workspace / "dist/sample-plugin.zip").read_bytes(), payload)

    def test_t3_missing_conflicting_or_unresolved_tool_behavior_waits_for_new_approval(self) -> None:
        def mutate(proposal):
            proposal["tools"][0]["implementation_kind"] = "UNRESOLVED"
            proposal["tools"][0]["files"] = []
            proposal["tools"][0]["execution"] = None
            proposal["tools"][0]["fixtures"] = None
        with self.assertRaises(AssertionError) as failure:
            prepared_workspace(self.root, mutate=mutate)
        self.assertIn("unresolved_required", str(failure.exception))

    def test_t4_unexplained_update_content_and_tools_wait_and_survive(self) -> None:
        helper = update_tests.UpdateCandidateTests()
        helper.root = self.root
        workspace = helper._prepare(keep_unrelated=False)
        blocked = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(run_cli("resolve-update", "--session", str(workspace / "session.json"), "--member", "owner-notes.txt", "--decision", "keep", "--evidence", "owner keeps it", "--json").returncode, 0)
        self.assertEqual(run_cli("build", "--session", str(workspace / "session.json"), "--json").returncode, 0)
        self.assertEqual((workspace / "candidate/owner-notes.txt").read_bytes(), (workspace / "baseline/owner-notes.txt").read_bytes())
        self.assertEqual((workspace / "candidate/tools/normalize.py").read_bytes(), (workspace / "baseline/tools/normalize.py").read_bytes())

    def test_t5_required_tool_or_other_failure_never_emits_zip(self) -> None:
        workspace = prepared_workspace(self.root, mutate=_failing_tool)
        self.assertEqual(run_cli("build", "--session", str(workspace / "session.json"), "--json").returncode, 0)
        self.assertEqual(run_cli("verify", "--session", str(workspace / "session.json"), "--json").returncode, 2)
        self.assertEqual(run_cli("package", "--session", str(workspace / "session.json"), "--json").returncode, 2)
        self.assertFalse((workspace / "dist/sample-plugin.zip").exists())

    def test_t6_environment_limited_runtime_native_or_mcp_check_remains_not_verified_through_w2(self) -> None:
        workspace = prepared_workspace(self.root, mutate=_runtime_native_optional)
        self.assertEqual(run_cli("build", "--session", str(workspace / "session.json"), "--json").returncode, 0)
        verified = run_cli("verify", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(verified.returncode, 0, verified.stdout)
        report = json.loads((workspace / "verification-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["tools"][0]["state"], "NOT VERIFIED")
        approved = run_cli("approve-w2", "--session", str(workspace / "session.json"), "--confirmed-by", "owner", "--evidence", "accepted documented optional limitation", "--json")
        self.assertEqual(approved.returncode, 0, approved.stdout)
        self.assertEqual(json.loads((workspace / "verification-report.json").read_text(encoding="utf-8"))["tools"][0]["state"], "NOT VERIFIED")

    def test_external_adapter_is_planned_built_bound_and_reported_without_credentials_or_false_runtime_pass(self) -> None:
        workspace = prepared_workspace(self.root, mutate=_mcp_optional)
        self.assertEqual(run_cli("build", "--session", str(workspace / "session.json"), "--json").returncode, 0)
        run_cli("verify", "--session", str(workspace / "session.json"), "--json")
        report = json.loads((workspace / "verification-report.json").read_text(encoding="utf-8"))
        tool = report["tools"][0]
        self.assertEqual(tool["implementation_kind"], "MCP_ADAPTER")
        self.assertEqual(tool["state"], "NOT VERIFIED")
        self.assertFalse(tool["executed"])
        candidate_text = "\n".join(path.read_text(encoding="utf-8") for path in (workspace / "candidate").rglob("*") if path.is_file())
        self.assertNotRegex(candidate_text.casefold(), r"api[_-]?key|password|secret")

    def test_pause_resume_and_cancel_are_thin_session_operations(self) -> None:
        workspace = prepared_workspace(self.root, approve=False)
        session = workspace / "session.json"
        self.assertEqual(run_cli("pause", "--session", str(session), "--json").returncode, 0)
        self.assertEqual(json.loads(session.read_text(encoding="utf-8"))["stage"], "H1")
        self.assertEqual(run_cli("resume", "--session", str(session), "--json").returncode, 0)
        self.assertEqual(json.loads(session.read_text(encoding="utf-8"))["stage"], "W1")
        self.assertEqual(run_cli("cancel", "--session", str(session), "--json").returncode, 0)
        self.assertEqual(json.loads(session.read_text(encoding="utf-8"))["stage"], "E2")


if __name__ == "__main__":
    unittest.main()
