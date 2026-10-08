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
from plugin_builder_core.bootstrap import plugin_authoring
from plugin_builder_core.verification import _effective_tool_states


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
        self.assertEqual(report["schema"], "plugin-builder-verification-report-v3")
        self.assertEqual(report["preflight_evidence"], plan["preflight_evidence"])
        self.assertEqual(report["tools"][0]["declared_argv"], ["{python}", "tools/normalize.py", "--self-test"])
        self.assertEqual(report["tools"][0]["adapter"], "CURRENT_PYTHON")
        self.assertEqual(report["tools"][0]["operation_execution"]["state"], "PASS")
        self.assertEqual(len(report["runtime_realizations"]), 2)
        self.assertTrue(all(item["state"] == "NOT VERIFIED" for item in report["runtime_realizations"]))
        self.assertEqual(
            set(report["evidence_states"]),
            {"structural_validation", "installation", "tool_execution", "reference_consultation", "conversation"},
        )

    def test_required_installed_realization_blocks_w2_but_deferred_remains_visible(self) -> None:
        def require_installed(proposal: dict) -> None:
            proposal["tools"][0]["realizations"][0]["evidence_policy"] = "REQUIRED_BEFORE_W2"

        workspace = self._workspace(mutate=require_installed)
        verified = self._verify(workspace)
        self.assertEqual(verified.returncode, 2, verified.stdout)
        report = self._report(workspace)
        self.assertEqual(report["tools"][0]["operation_execution"]["state"], "PASS")
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(
            [item["evidence_policy"] for item in report["runtime_realizations"]],
            ["REQUIRED_BEFORE_W2", "DEFERRED_ALLOWED"],
        )
        approved = run_cli("approve-w2", "--session", str(workspace / "session.json"), "--confirmed-by", "owner", "--evidence", "reviewed", "--json")
        self.assertEqual(approved.returncode, 2, approved.stdout)
        self.assertFalse((workspace / "dist/sample-plugin.zip").exists())

    def test_changed_generated_endpoint_is_rejected_even_if_candidate_hash_is_rebound(self) -> None:
        workspace = self._workspace()
        candidate = workspace / "candidate"
        mcp_path = candidate / "mcp.json"
        mcp_path.write_bytes(mcp_path.read_bytes().replace(b"example.com", b"unapproved.example"))
        session_path = workspace / "session.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))
        session["candidate"]["sha256"] = plugin_authoring.tree_sha256(candidate)
        session_path.write_text(json.dumps(session, sort_keys=True), encoding="utf-8")
        verified = self._verify(workspace)
        self.assertEqual(verified.returncode, 2, verified.stdout)
        self.assertIn("verify.runtime_identity_invalid:runtime_configuration_mismatch:mcp.portable_projection_mismatch", verified.stdout)

    def test_changed_tool_binding_is_rejected_even_if_candidate_hash_is_rebound(self) -> None:
        workspace = self._workspace()
        candidate = workspace / "candidate"
        manifest_path = candidate / "PLUGIN-BUILDER-MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["tool_bindings"][0]["permissions"] = []
        manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
        session_path = workspace / "session.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))
        session["candidate"]["sha256"] = plugin_authoring.tree_sha256(candidate)
        session_path.write_text(json.dumps(session, sort_keys=True), encoding="utf-8")
        verified = self._verify(workspace)
        self.assertEqual(verified.returncode, 2, verified.stdout)
        self.assertIn("verify.tool_bindings_mismatch", verified.stdout)

    def test_approved_behavior_preserving_alternative_satisfies_primary_requirement(self) -> None:
        contracts = [
            {"id": "primary", "operation": {"id": "primary-op"}, "requirement_ids": ["RQ1"],
             "fallback": {"policy": "ALTERNATIVE", "alternative_operation_id": "alternative-op", "preserved_requirement_ids": ["RQ1"], "degraded_requirement_ids": []}},
            {"id": "alternative", "operation": {"id": "alternative-op"}, "requirement_ids": ["RQ1"], "fallback": {"policy": "BLOCK"}},
        ]
        results = [
            {"tool_id": "primary", "state": "NOT VERIFIED"},
            {"tool_id": "alternative", "state": "PASS"},
        ]
        effective, activations = _effective_tool_states(contracts, results)
        self.assertEqual(effective["primary"], "PASS")
        self.assertEqual(activations, [{"tool_id": "primary", "alternative_tool_id": "alternative", "operation_id": "alternative-op", "preserved_requirement_ids": ["RQ1"]}])

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

    def test_authorized_local_mcp_pass_does_not_upgrade_installed_realizations(self) -> None:
        from plugin_builder_core.tool_verification import verify_application_tool
        from test_mcp_local_verification import tool as local_mcp_tool

        candidate = self.root / "candidate"
        (candidate / "tools").mkdir(parents=True)
        source = TESTS / "fixtures" / "mcp_server_fixture.py"
        (candidate / "tools/server.py").write_bytes(source.read_bytes())
        evidence = verify_application_tool(local_mcp_tool(), candidate, allow_loopback=True)
        self.assertEqual(evidence["state"], "PASS")
        self.assertEqual(evidence["environment"], "BUILD_HOST_LOCAL_MCP")
        self.assertTrue(all(item["state"] == "NOT VERIFIED" for item in evidence["realizations"]))

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
