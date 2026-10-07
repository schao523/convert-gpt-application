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


def bundled_tool_v2() -> dict:
    payload = bundled_tool()
    payload.update({
        "schema": "plugin-builder-application-tool-v2",
        "capability_ids": ["normalize-content"],
        "operation": {
            "id": "normalize-input",
            "protocol": "MCP_TOOL_CALL",
            "input_schema_sha256": "59dd9138acc693310fce4722159a02240f995b2be524301ba57548a1aa7b10fa",
            "output_schema_sha256": "59dd9138acc693310fce4722159a02240f995b2be524301ba57548a1aa7b10fa",
            "side_effect_class": "NONE",
            "idempotent": True,
            "capability_ids": ["normalize-content"],
        },
        "dependencies": [{
            "id": "mcp-service",
            "type": "SERVICE",
            "provider": "REMOTE_SERVICE",
            "version": None,
            "sha256": None,
            "runtime_targets": ["ChatGPT Work Local/Desktop", "Codex"],
            "setup_owner": "SERVICE_OPERATOR",
            "required": True,
            "absence_policy": "BLOCK",
        }],
        "permissions": [
            {
                "id": "network",
                "target_runtime": "Codex",
                "grant_source": "OWNER",
                "required": True,
                "purpose": "Reach the approved MCP service.",
                "verification": "Observe the installed tool call.",
            },
            {
                "id": "network",
                "target_runtime": "ChatGPT Work Local/Desktop",
                "grant_source": "OWNER",
                "required": True,
                "purpose": "Reach the approved MCP service.",
                "verification": "Observe the installed tool call.",
            },
        ],
        "fallback": {
            "policy": "BLOCK",
            "trigger_conditions": ["The approved MCP service is unavailable."],
            "alternative_operation_id": None,
            "preserved_requirement_ids": [],
            "degraded_requirement_ids": ["RQ1"],
        },
        "mcp": {
            "server_id": "normalizer",
            "config_file": "mcp.json",
            "transport": "streamable-http",
            "permission_scopes": ["normalize:execute"],
            "authentication": "NOT_REQUIRED",
            "setup": "SERVICE_OPERATOR",
            "service_boundary": "Normalize approved content.",
            "url": "https://example.com/mcp",
        },
        "realizations": [
            {
                "target_runtime": target,
                "mechanism": "MCP_REMOTE_HTTPS",
                "adapter_id": "mcp-streamable-http",
                "adapter_version": "1",
                "exposed_capability": "normalize-input",
                "operation_id": "normalize-input",
                "transport": "MCP_STREAMABLE_HTTP",
                "execution_location": "REMOTE_SERVICE",
                "dependency_ids": ["mcp-service"],
                "permission_ids": ["network"],
                "setup_requirements": ["Configure the approved HTTPS MCP endpoint."],
                "setup_owner": "SERVICE_OPERATOR",
                "feasibility_state": "FEASIBLE_WITH_SETUP",
                "evidence_policy": "DEFERRED_ALLOWED",
            }
            for target in ("ChatGPT Work Local/Desktop", "Codex")
        ],
    })
    return payload


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

    def test_v2_contract_binds_operation_dependencies_permissions_and_realizations(self) -> None:
        self.assertEqual(self.codes(bundled_tool_v2()), set())

        invalid = bundled_tool_v2()
        invalid["operation"]["input_schema_sha256"] = "0" * 64
        invalid["operation"]["capability_ids"] = ["other-capability"]
        invalid["realizations"][0]["dependency_ids"] = ["missing"]
        invalid["realizations"][0]["permission_ids"] = ["missing"]
        self.assertEqual(
            self.codes(invalid),
            {
                "tool.normalize-input.operation_capability_mismatch",
                "tool.normalize-input.operation_input_schema_mismatch",
                "realization.ChatGPT Work Local/Desktop.dependency_unknown:missing",
                "realization.ChatGPT Work Local/Desktop.permission_unknown:missing",
            },
        )

    def test_v2_requires_exactly_one_realization_per_runtime_target(self) -> None:
        invalid = bundled_tool_v2()
        invalid["realizations"] = [invalid["realizations"][0], copy.deepcopy(invalid["realizations"][0])]
        self.assertEqual(
            self.codes(invalid),
            {
                "tool.normalize-input.realization_duplicate:ChatGPT Work Local/Desktop",
                "tool.normalize-input.realization_missing:Codex",
            },
        )

    def test_v2_rejects_unsafe_endpoint_credentials_and_invalid_structured_fallback(self) -> None:
        invalid = bundled_tool_v2()
        invalid["mcp"]["url"] = "http://user:secret@localhost:3000/mcp"
        invalid["fallback"]["alternative_operation_id"] = "other-operation"
        self.assertEqual(
            self.codes(invalid),
            {
                "tool.normalize-input.credential_material_forbidden",
                "tool.normalize-input.fallback_alternative_forbidden",
                "tool.normalize-input.mcp_url_invalid",
            },
        )

    def test_v2_uses_the_locked_operation_dependency_and_permission_enums(self) -> None:
        invalid = bundled_tool_v2()
        invalid["operation"]["protocol"] = "DIRECT_ARGV"
        invalid["operation"]["side_effect_class"] = "EXTERNAL_MUTATION"
        invalid["dependencies"][0]["type"] = "PYTHON"
        invalid["dependencies"][0]["provider"] = "USER_DEVICE"
        invalid["dependencies"][0]["absence_policy"] = "OMIT_OPTIONAL"
        invalid["permissions"][0]["grant_source"] = "SERVICE_OPERATOR"
        self.assertEqual(
            self.codes(invalid),
            {
                "tool.normalize-input.dependency_absence_policy_invalid:mcp-service",
                "tool.normalize-input.dependency_provider_invalid:mcp-service",
                "tool.normalize-input.dependency_type_invalid:mcp-service",
                "tool.normalize-input.operation_protocol_invalid",
                "tool.normalize-input.operation_side_effect_class_invalid",
                "tool.normalize-input.permission_grant_source_invalid:network",
            },
        )

    def test_v2_permission_ids_accept_registered_scoped_vocabulary(self) -> None:
        payload = bundled_tool_v2()
        for permission in payload["permissions"]:
            permission["id"] = "runtime:native"
        for realization in payload["realizations"]:
            realization["permission_ids"] = ["runtime:native"]
        self.assertEqual(self.codes(payload), set())

    def test_v1_contract_remains_unchanged(self) -> None:
        result = validate_application_tool_contract(bundled_tool())
        self.assertEqual(result.errors, ())
        self.assertEqual(result.blockers, ())


if __name__ == "__main__":
    unittest.main()
