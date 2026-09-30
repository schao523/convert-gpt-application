from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

TESTS = Path(__file__).parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from test_create_candidate import (
    prepared_workspace,
    read_result,
    run_cli,
)


class CandidateApplicationToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def build(self, mutate=None):
        workspace = prepared_workspace(self.root, mutate=mutate)
        completed = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        return workspace, completed

    def test_tool_contract_is_bound_to_owning_skill_and_requirement(self) -> None:
        workspace, completed = self.build()
        self.assertEqual(completed.returncode, 0, completed.stdout)
        manifest = json.loads((workspace / "candidate/PLUGIN-BUILDER-MANIFEST.json").read_text(encoding="utf-8"))
        binding = manifest["tool_bindings"][0]
        self.assertEqual(binding["tool_id"], "normalize-input")
        self.assertEqual(binding["skills"], ["answering-structured-requests"])
        self.assertEqual(binding["requirements"], ["RQ1"])
        self.assertEqual(binding["files"], ["tools/normalize.py"])

    def test_framework_adapter_bundles_only_approved_portable_modules(self) -> None:
        def mutate(proposal: dict) -> None:
            tool = proposal["tools"][0]
            tool["implementation_kind"] = "FRAMEWORK_ADAPTER"
            tool["adapter"] = {
                "source": "obvious_one_plugin_framework.plugin_authoring.validation",
                "portable_files": ["tools/normalize.py"],
                "provenance": {"version": "0.1.0", "sha256": "a" * 64},
            }
        workspace, completed = self.build(mutate)
        self.assertEqual(completed.returncode, 0, completed.stdout)
        files = {path.relative_to(workspace / "candidate").as_posix() for path in (workspace / "candidate").rglob("*") if path.is_file()}
        self.assertIn("tools/normalize.py", files)
        self.assertFalse(any(path.startswith("src/") or "__pycache__" in path for path in files))

    def test_mcp_adapter_emits_manifest_without_credentials(self) -> None:
        def mutate(proposal: dict) -> None:
            tool = proposal["tools"][0]
            tool.update({
                "implementation_kind": "MCP_ADAPTER",
                "permissions": ["network"],
                "configuration": {"authentication": "USER_CONFIGURED", "setup": "USER_CONFIGURED"},
                "execution": None,
                "fixtures": None,
                "verification": {"kind": "MCP_CONTRACT", "argv": [], "network": True},
                "mcp": {
                    "server_id": "records", "config_file": "tools/normalize.py", "transport": "stdio",
                    "permission_scopes": ["records:read"], "authentication": "USER_CONFIGURED",
                    "setup": "USER_CONFIGURED", "service_boundary": "Read user-selected records."
                },
            })
        workspace, completed = self.build(mutate)
        self.assertEqual(completed.returncode, 0, completed.stdout)
        serialized = (workspace / "candidate/PLUGIN-BUILDER-MANIFEST.json").read_text(encoding="utf-8")
        self.assertIn('"implementation_kind": "MCP_ADAPTER"', serialized)
        self.assertNotIn("secret", serialized.casefold())
        self.assertNotIn("token", serialized.casefold())

    def test_required_runtime_native_capability_without_fallback_blocks_build(self) -> None:
        def mutate(proposal: dict) -> None:
            tool = proposal["tools"][0]
            tool.update({
                "implementation_kind": "RUNTIME_NATIVE",
                "files": [], "execution": None, "fixtures": None,
                "runtime_capability": {"name": "web_search", "runtimes": ["ChatGPT Work Local/Desktop", "Codex"]},
                "redistribution": {"state": "NOT_APPLICABLE", "evidence": "runtime supplied"},
                "verification": {"kind": "RUNTIME_CAPABILITY", "argv": [], "network": False},
            })
        workspace, completed = self.build(mutate)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("tool.normalize-input.runtime_capability_unavailable", read_result(completed)["errors"])
        self.assertFalse((workspace / "candidate").exists())


if __name__ == "__main__":
    unittest.main()
