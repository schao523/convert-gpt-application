from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest


TESTS = Path(__file__).parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from test_create_candidate import PLAN_FIXTURE, prepared_workspace, read_result, run_cli
import test_update_candidate as update_tests


def _tool_script(proposal: dict, text: str) -> None:
    recipe = next(item for item in proposal["files"] if item["path"] == "tools/normalize.py")
    recipe["inline_text"] = text
    recipe["source_sha256"] = sha256(text.encode("utf-8")).hexdigest()


class CandidateVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _workspace(self, mutate=None) -> Path:
        workspace = prepared_workspace(self.root, mutate=mutate)
        built = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(built.returncode, 0, built.stdout)
        return workspace

    def _verify(self, workspace: Path):
        return run_cli("verify", "--session", str(workspace / "session.json"), "--json")

    def _report(self, workspace: Path) -> dict:
        return json.loads((workspace / "verification-report.json").read_text(encoding="utf-8"))

    def test_verify_reports_plugin_skill_reference_tool_and_distribution_checks(self) -> None:
        workspace = self._workspace()
        completed = self._verify(workspace)
        self.assertEqual(completed.returncode, 0, completed.stdout)
        checks = {item["kind"]: item for item in self._report(workspace)["checks"]}
        for kind in ("PLUGIN_STRUCTURE", "SKILL_STRUCTURE", "REFERENCE_CLOSURE", "DISTRIBUTION_SAFETY", "EXACT_MEMBERS", "TOOL_BINDING"):
            self.assertEqual(checks[kind]["state"], "PASS")

    def test_local_tool_executes_with_declared_fixture_and_direct_argv(self) -> None:
        workspace = self._workspace()
        self.assertEqual(self._verify(workspace).returncode, 0)
        evidence = self._report(workspace)["tools"][0]
        self.assertEqual(evidence["state"], "PASS")
        self.assertTrue(evidence["executed"])
        self.assertEqual(evidence["argv"], ["{python}", "tools/normalize.py", "--self-test"])
        self.assertRegex(evidence["fixture_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(evidence["stdout_sha256"], r"^[0-9a-f]{64}$")

    def test_verification_binds_preflight_quality_profile_and_command_evidence(self) -> None:
        workspace = self._workspace()
        self.assertEqual(self._verify(workspace).returncode, 0)
        report = self._report(workspace)
        plan = json.loads((workspace / "implementation-plan.json").read_text(encoding="utf-8"))
        self.assertEqual(report["schema"], "plugin-builder-verification-report-v2")
        self.assertEqual(report["preflight_evidence"], plan["preflight_evidence"])
        self.assertEqual(report["tools"][0]["declared_argv"], ["{python}", "tools/normalize.py", "--self-test"])
        self.assertEqual(report["tools"][0]["adapter"], "CURRENT_PYTHON")
        self.assertEqual(
            set(report["evidence_states"]),
            {"structural_validation", "installation", "tool_execution", "reference_consultation", "conversation"},
        )

    def test_runtime_native_and_mcp_tool_evidence_is_runtime_specific(self) -> None:
        from plugin_builder_core.tool_verification import verify_application_tool

        tool = json.loads(PLAN_FIXTURE.read_text(encoding="utf-8"))["tools"][0]
        tool.update({"implementation_kind": "RUNTIME_NATIVE", "files": [], "execution": None, "fixtures": None, "runtime_capability": {"name": "desktop-picker", "runtimes": tool["runtime_targets"]}, "fallback": {"policy": "OPTIONAL", "description": "manual fallback"}})
        native = verify_application_tool(tool, self.root)
        self.assertEqual(native["state"], "NOT VERIFIED")
        self.assertIn("runtime_capability_unavailable", native["diagnostics"])
        tool.update({"implementation_kind": "MCP_ADAPTER", "permissions": ["workspace:read", "network"], "runtime_capability": None, "mcp": {"server_id": "fixture", "config_file": "mcp.json", "transport": "stdio", "permission_scopes": ["read"], "authentication": "USER_CONFIGURED", "setup": "OWNER_CONFIGURED", "service_boundary": "external"}})
        mcp = verify_application_tool(tool, self.root)
        self.assertEqual(mcp["state"], "NOT VERIFIED")
        self.assertIn("mcp_runtime_evidence_required", mcp["diagnostics"])

    def test_tool_failure_maps_to_owning_requirements_and_blocks_when_required(self) -> None:
        workspace = self._workspace(lambda p: _tool_script(p, "raise SystemExit(7)\n"))
        completed = self._verify(workspace)
        self.assertEqual(completed.returncode, 2)
        report = self._report(workspace)
        self.assertEqual(report["tools"][0]["state"], "FAIL")
        requirement = next(item for item in report["requirements"] if item["id"] == "RQ1")
        self.assertEqual(requirement["state"], "FAIL")

    def test_network_or_auth_tool_is_not_executed_without_explicit_runtime_authorization(self) -> None:
        def mutate(proposal):
            proposal["tools"][0]["permissions"].append("network")
            proposal["tools"][0]["configuration"]["authentication"] = "USER_CONFIGURED"
        workspace = self._workspace(mutate)
        completed = self._verify(workspace)
        self.assertEqual(completed.returncode, 2)
        tool = self._report(workspace)["tools"][0]
        self.assertEqual(tool["state"], "NOT VERIFIED")
        self.assertFalse(tool["executed"])
        self.assertIn("runtime_authorization_required", tool["diagnostics"])

    def test_required_failure_blocks_w2_and_preserves_diagnostics(self) -> None:
        workspace = self._workspace(lambda p: _tool_script(p, "raise SystemExit(9)\n"))
        self.assertEqual(self._verify(workspace).returncode, 2)
        report_before = (workspace / "verification-report.json").read_bytes()
        approved = run_cli("approve-w2", "--session", str(workspace / "session.json"), "--confirmed-by", "owner", "--evidence", "reviewed", "--json")
        self.assertEqual(approved.returncode, 2)
        self.assertIn("w2.required_failure", read_result(approved)["errors"])
        self.assertEqual((workspace / "verification-report.json").read_bytes(), report_before)

    def test_unavailable_literal_command_fails_preflight(self) -> None:
        def mutate(proposal):
            check = next(item for item in proposal["checks"] if item["id"] == "normalize-self-test")
            check["argv"] = ["definitely-missing-executable"]
            proposal["tools"][0]["verification"]["argv"] = ["definitely-missing-executable"]
        with self.assertRaises(AssertionError) as raised:
            prepared_workspace(self.root, mutate=mutate)
        self.assertIn(
            "plan.preflight.command_unresolved:normalize-input:verification:executable_unavailable",
            str(raised.exception),
        )

    def test_verification_covers_every_required_requirement(self) -> None:
        workspace = self._workspace()
        self.assertEqual(self._verify(workspace).returncode, 0)
        report = self._report(workspace)
        self.assertEqual({item["id"] for item in report["requirements"]}, {"AC1", "RQ1"})
        self.assertTrue(all(item["state"] == "PASS" for item in report["requirements"] if item["required"]))

    def test_update_verification_proves_preserved_members_and_tools(self) -> None:
        helper = update_tests.UpdateCandidateTests()
        helper.root = self.root
        workspace = helper._prepare()
        built = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(built.returncode, 0, built.stdout)
        self.assertEqual(self._verify(workspace).returncode, 0)
        report = self._report(workspace)
        update = next(item for item in report["checks"] if item["kind"] == "UPDATE_PRESERVATION")
        self.assertEqual(update["state"], "PASS")
        self.assertIn("owner-notes.txt", update["evidence"]["preserved_members"])
        self.assertEqual(report["tools"][0]["state"], "PASS")

    def test_candidate_change_invalidates_report_and_w2(self) -> None:
        workspace = self._workspace()
        self.assertEqual(self._verify(workspace).returncode, 0)
        (workspace / "candidate/tools/normalize.py").write_text("tampered\n", encoding="utf-8")
        approved = run_cli("approve-w2", "--session", str(workspace / "session.json"), "--confirmed-by", "owner", "--evidence", "reviewed", "--json")
        self.assertEqual(approved.returncode, 2)
        self.assertIn("w2.candidate_sha256_mismatch", read_result(approved)["errors"])
        session = json.loads((workspace / "session.json").read_text(encoding="utf-8"))
        self.assertIsNone(session["w2"])


if __name__ == "__main__":
    unittest.main()
