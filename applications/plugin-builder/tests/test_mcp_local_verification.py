from __future__ import annotations

import copy
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock


TESTS = Path(__file__).parent
SCRIPTS = TESTS.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from plugin_builder_core.mcp_local_verification import _invalid_input, verify_local_mcp_realization


FIXTURE = TESTS / "fixtures" / "mcp_server_fixture.py"


def tool(mode: str = "normal") -> dict:
    argv = ["{python}", "tools/server.py", "--host", "127.0.0.1", "--port", "{port}"]
    if mode != "normal":
        argv += ["--mode", mode]
    return {
        "schema": "plugin-builder-application-tool-v2",
        "id": "normalize-input",
        "implementation_kind": "MCP_ADAPTER",
        "files": ["tools/server.py"],
        "dependencies": [{
            "id": "python-runtime", "type": "EXECUTABLE",
            "provider": "RUNTIME_PROVIDED", "version": None, "sha256": None,
            "runtime_targets": ["ChatGPT Work Local/Desktop", "Codex"],
            "setup_owner": "RUNTIME", "required": True, "absence_policy": "BLOCK",
        }],
        "operation": {"id": "normalize-input"},
        "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        "verification": {"kind": "MCP_CONTRACT", "argv": argv, "network": True},
        "execution": {"timeout_seconds": 2},
        "fixtures": {"input": {"text": " A "}, "output": {"normalized": "A"}},
        "realizations": [{
            "target_runtime": target, "adapter_id": "mcp-streamable-http",
            "operation_id": "normalize-input", "exposed_capability": "normalize-input",
        } for target in ("ChatGPT Work Local/Desktop", "Codex")],
    }


class McpLocalVerificationTests(unittest.TestCase):
    def test_negative_call_is_derived_from_declared_schema_not_sample_field_name(self) -> None:
        self.assertEqual(
            _invalid_input({"input_schema": {"type": "object", "required": ["count"], "properties": {"count": {"type": "integer"}}}}, {"count": 3}),
            {},
        )
        self.assertEqual(
            _invalid_input({"input_schema": {"type": "object", "properties": {"label": {"type": "string"}}}}, {"label": "ok"}),
            {"label": 7},
        )
        self.assertIsNone(_invalid_input({"input_schema": {"type": "object"}}, {"anything": 3}))

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "tools").mkdir()
        shutil.copyfile(FIXTURE, self.root / "tools/server.py")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_initialize_discovery_valid_invalid_and_structured_call_pass(self) -> None:
        with mock.patch.dict(os.environ, {"MCP_TEST_LEAK": "must-not-leak"}):
            result = verify_local_mcp_realization(tool(), self.root, allow_loopback=True)
        self.assertEqual(result["state"], "PASS", result)
        self.assertEqual(result["environment"], "BUILD_HOST_LOCAL_MCP")
        self.assertTrue(result["executed"])
        self.assertTrue(result["network_contacted"])
        self.assertEqual(result["process_cleanup"], "PASS")
        for field in ("input_sha256", "output_sha256", "transcript_sha256"):
            self.assertRegex(result[field], r"^[0-9a-f]{64}$")
        self.assertNotIn(" A ", json.dumps(result))
        self.assertNotIn("normalized", json.dumps(result))
        self.assertEqual(result["operation_execution"]["state"], "PASS")
        for realization in result["realizations"]:
            self.assertEqual(realization["state"], "NOT VERIFIED")
            self.assertEqual(realization["layers"]["operation_execution"], "STATICALLY VERIFIED")
            self.assertEqual(realization["layers"]["skill_invocation"], "NOT VERIFIED")
            self.assertEqual(realization["layers"]["result_delivery"], "NOT VERIFIED")
            self.assertEqual(realization["layers"]["skill_behavior"], "NOT VERIFIED")

    def test_loopback_authorization_host_file_and_dependency_fail_closed(self) -> None:
        self.assertEqual(
            verify_local_mcp_realization(tool(), self.root)["diagnostics"],
            ["mcp_local.loopback_not_authorized"],
        )
        external = tool()
        external["verification"]["argv"][4] = "0.0.0.0"
        self.assertIn(
            "mcp_local.external_host_forbidden",
            verify_local_mcp_realization(external, self.root, allow_loopback=True)["diagnostics"],
        )
        undeclared = tool()
        undeclared["files"] = []
        self.assertIn(
            "mcp_local.server_file_undeclared:tools/server.py",
            verify_local_mcp_realization(undeclared, self.root, allow_loopback=True)["diagnostics"],
        )
        dependency = tool()
        dependency["dependencies"] = []
        self.assertIn(
            "mcp_local.dependency_undeclared",
            verify_local_mcp_realization(dependency, self.root, allow_loopback=True)["diagnostics"],
        )

    def test_protocol_and_lifecycle_failures_are_bounded_and_cleaned_up(self) -> None:
        for mode, expected in (
            ("startup-fail", "mcp_local.startup_failed"),
            ("premature-exit", "mcp_local.premature_exit"),
            ("hang", "mcp_local.request_timeout"),
            ("malformed", "mcp_local.response_invalid"),
            ("wrong-tool", "mcp_local.tool_not_advertised:normalize-input"),
        ):
            with self.subTest(mode=mode):
                result = verify_local_mcp_realization(tool(mode), self.root, allow_loopback=True)
                self.assertEqual(result["state"], "FAIL")
                self.assertIn(expected, result["diagnostics"])
                self.assertEqual(result["process_cleanup"], "PASS")

    def test_repeated_success_has_deterministic_operation_digests(self) -> None:
        first = verify_local_mcp_realization(tool(), self.root, allow_loopback=True)
        second = verify_local_mcp_realization(copy.deepcopy(tool()), self.root, allow_loopback=True)
        self.assertEqual(first["input_sha256"], second["input_sha256"])
        self.assertEqual(first["output_sha256"], second["output_sha256"])
        self.assertEqual(first["transcript_sha256"], second["transcript_sha256"])


if __name__ == "__main__":
    unittest.main()
