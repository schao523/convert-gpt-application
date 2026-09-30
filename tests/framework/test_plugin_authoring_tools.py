from __future__ import annotations

import copy
import unittest

from obvious_one_plugin_framework.plugin_authoring import validate_application_tool_contract


def bundled_tool() -> dict:
    return {
        "schema": "plugin-builder-application-tool-v1",
        "id": "normalize-input",
        "required": True,
        "implementation_kind": "BUNDLED_LOCAL",
        "requirement_ids": ["RQ1"],
        "skill_bindings": ["answering-requests"],
        "files": ["tools/normalize.py"],
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "side_effects": [],
        "permissions": ["workspace:read"],
        "runtime_targets": ["ChatGPT Work Local/Desktop", "Codex"],
        "dependencies": [],
        "configuration": {"authentication": "NOT_REQUIRED", "setup": "BUNDLED"},
        "fallback": {"policy": "BLOCK", "description": "Required behavior."},
        "verification": {"kind": "PYTHON_ARGV", "argv": ["python", "tools/normalize.py", "--self-test"], "network": False},
        "redistribution": {"state": "APPROVED", "evidence": "generated locally"},
        "execution": {"argv": ["python", "tools/normalize.py"], "clean_environment": True, "timeout_seconds": 30},
        "fixtures": {"input": {"text": " A "}, "output": {"normalized": "A"}},
        "runtime_capability": None,
        "adapter": None,
        "mcp": None,
    }


class ApplicationToolContractTests(unittest.TestCase):
    def codes(self, payload: dict) -> set[str]:
        result = validate_application_tool_contract(payload)
        return set(result.errors) | set(result.blockers)

    def test_bundled_local_tool_requires_safe_files_and_direct_skill_binding(self) -> None:
        self.assertEqual(self.codes(bundled_tool()), set())
        invalid = bundled_tool()
        invalid["files"] = ["../escape.py"]
        invalid["skill_bindings"] = []
        self.assertEqual(
            self.codes(invalid),
            {"tool.normalize-input.files_invalid", "tool.normalize-input.skill_binding_required"},
        )

    def test_runtime_native_tool_requires_declared_runtime_capability(self) -> None:
        payload = bundled_tool()
        payload.update({
            "id": "runtime-search",
            "implementation_kind": "RUNTIME_NATIVE",
            "files": [],
            "execution": None,
            "fixtures": None,
            "runtime_capability": {"name": "web_search", "runtimes": ["ChatGPT Work Local/Desktop", "Codex"]},
            "verification": {"kind": "RUNTIME_CAPABILITY", "argv": [], "network": False},
            "redistribution": {"state": "NOT_APPLICABLE", "evidence": "runtime supplied"},
        })
        self.assertEqual(self.codes(payload), set())
        payload["runtime_capability"] = None
        self.assertIn("tool.runtime-search.runtime_capability_required", self.codes(payload))

    def test_framework_adapter_records_portable_source_and_provenance(self) -> None:
        payload = bundled_tool()
        payload.update({
            "id": "framework-validator",
            "implementation_kind": "FRAMEWORK_ADAPTER",
            "files": ["tools/framework_validator.py"],
            "execution": {"argv": ["python", "tools/framework_validator.py"], "clean_environment": True, "timeout_seconds": 30},
            "adapter": {
                "source": "obvious_one_plugin_framework.plugin_authoring.validation",
                "portable_files": ["tools/framework_validator.py"],
                "provenance": {"version": "0.1.0", "sha256": "a" * 64},
            },
        })
        self.assertEqual(self.codes(payload), set())
        payload["adapter"]["provenance"].pop("sha256")
        self.assertIn("tool.framework-validator.adapter_provenance_invalid", self.codes(payload))

    def test_mcp_adapter_requires_config_permissions_auth_and_service_contract(self) -> None:
        payload = bundled_tool()
        payload.update({
            "id": "records-service",
            "implementation_kind": "MCP_ADAPTER",
            "files": ["mcp/records.json"],
            "permissions": ["network"],
            "configuration": {"authentication": "USER_CONFIGURED", "setup": "USER_CONFIGURED"},
            "execution": None,
            "fixtures": None,
            "mcp": {
                "server_id": "records",
                "config_file": "mcp/records.json",
                "transport": "stdio",
                "permission_scopes": ["records:read"],
                "authentication": "USER_CONFIGURED",
                "setup": "USER_CONFIGURED",
                "service_boundary": "Read records selected by the user.",
            },
            "verification": {"kind": "MCP_CONTRACT", "argv": [], "network": True},
        })
        self.assertEqual(self.codes(payload), set())
        payload["mcp"].pop("service_boundary")
        payload["permissions"] = []
        self.assertEqual(
            self.codes(payload),
            {"tool.records-service.mcp_contract_invalid", "tool.records-service.network_permission_required"},
        )

    def test_unresolved_required_tool_is_blocking(self) -> None:
        payload = bundled_tool()
        payload.update({
            "implementation_kind": "UNRESOLVED",
            "files": [], "execution": None, "fixtures": None,
            "runtime_capability": None, "adapter": None, "mcp": None,
            "redistribution": {"state": "UNRESOLVED", "evidence": "owner decision required"},
        })
        result = validate_application_tool_contract(payload)
        self.assertEqual(result.errors, ())
        self.assertEqual(result.blockers, ("tool.normalize-input.unresolved_required",))

    def test_tool_contract_rejects_credentials_shell_commands_and_unknown_permissions(self) -> None:
        payload = bundled_tool()
        payload["configuration"]["token"] = "secret-value"
        payload["execution"]["argv"] = ["python", "tools/normalize.py && whoami"]
        payload["permissions"] = ["workspace:read", "admin:all"]
        self.assertEqual(
            self.codes(payload),
            {
                "tool.normalize-input.configuration_invalid",
                "tool.normalize-input.credential_material_forbidden",
                "tool.normalize-input.execution_shell_forbidden",
                "tool.normalize-input.permissions_invalid",
            },
        )


if __name__ == "__main__":
    unittest.main()
