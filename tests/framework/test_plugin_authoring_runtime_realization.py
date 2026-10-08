from __future__ import annotations

import unittest

from obvious_one_plugin_framework.plugin_authoring.runtime_realization import (
    validate_runtime_realization,
)


def realization(target: str = "Codex", **changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
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
    payload.update(changes)
    return payload


class RuntimeRealizationContractTests(unittest.TestCase):
    def validate(self, payload: object):
        return validate_runtime_realization(
            payload,
            operation_id="normalize-input",
            runtime_targets={"ChatGPT Work Local/Desktop", "Codex"},
            dependency_ids={"mcp-service"},
            permission_ids={"network"},
        )

    def test_valid_realization_preserves_an_immutable_payload(self) -> None:
        payload = realization()
        result = self.validate(payload)
        self.assertEqual(result.errors, ())
        self.assertEqual(result.blockers, ())
        self.assertEqual(result.target_runtime, "Codex")
        self.assertEqual(result.payload["dependency_ids"], ("mcp-service",))
        payload["dependency_ids"].append("changed")  # type: ignore[union-attr]
        self.assertEqual(result.payload["dependency_ids"], ("mcp-service",))

    def test_exact_shape_and_declared_bindings_are_required(self) -> None:
        payload = realization(
            target_runtime="Unknown",
            operation_id="other-operation",
            dependency_ids=["missing-dependency"],
            permission_ids=["missing-permission"],
            extra=True,
        )
        result = self.validate(payload)
        self.assertEqual(
            result.errors,
            (
                "realization.Unknown.dependency_unknown:missing-dependency",
                "realization.Unknown.invalid_keys",
                "realization.Unknown.operation_mismatch",
                "realization.Unknown.permission_unknown:missing-permission",
                "realization.Unknown.target_runtime_invalid",
            ),
        )

    def test_mechanism_transport_and_execution_location_must_agree(self) -> None:
        result = self.validate(
            realization(
                mechanism="DIRECT_LOCAL",
                transport="MCP_STREAMABLE_HTTP",
                execution_location="REMOTE_SERVICE",
            )
        )
        self.assertEqual(
            result.errors,
            (
                "realization.Codex.execution_location_mismatch",
                "realization.Codex.transport_mismatch",
            ),
        )

    def test_all_approved_mechanisms_have_one_valid_shape(self) -> None:
        cases = (
            realization(),
            realization(
                mechanism="MCP_REGISTERED",
                execution_location="RUNTIME_HOST",
                setup_owner="OWNER",
            ),
            realization(
                mechanism="MCP_LOCAL_PROCESS",
                execution_location="USER_DEVICE",
                setup_owner="OWNER",
            ),
            realization(
                mechanism="DIRECT_LOCAL",
                transport="DIRECT_ARGV",
                execution_location="USER_DEVICE",
                adapter_id="direct-local",
            ),
            realization(
                mechanism="RUNTIME_NATIVE",
                transport="RUNTIME_API",
                execution_location="RUNTIME_HOST",
                adapter_id="runtime-native",
            ),
            realization(
                mechanism="UNSUPPORTED",
                transport="NONE",
                execution_location="RUNTIME_HOST",
                adapter_id="unsupported",
                dependency_ids=[],
                permission_ids=[],
                feasibility_state="UNSUPPORTED",
                setup_requirements=[],
                setup_owner="RUNTIME",
                evidence_policy="DEFERRED_ALLOWED",
            ),
        )
        for item in cases:
            with self.subTest(mechanism=item["mechanism"]):
                self.assertEqual(self.validate(item).errors, ())

    def test_setup_feasibility_and_evidence_policy_are_validated(self) -> None:
        result = self.validate(
            realization(
                setup_requirements=[],
                setup_owner="UNKNOWN",
                feasibility_state="MAYBE",
                evidence_policy="PASS_IF_LOCAL",
            )
        )
        self.assertEqual(
            result.errors,
            (
                "realization.Codex.evidence_policy_invalid",
                "realization.Codex.feasibility_state_invalid",
                "realization.Codex.setup_owner_invalid",
            ),
        )
        missing_setup = self.validate(realization(setup_requirements=[]))
        self.assertEqual(
            missing_setup.errors,
            ("realization.Codex.setup_requirements_required",),
        )

    def test_locked_feasibility_and_evidence_enums_are_exact(self) -> None:
        for state in ("FEASIBLE", "FEASIBLE_WITH_SETUP", "NOT VERIFIED", "BLOCKED"):
            with self.subTest(state=state):
                self.assertEqual(self.validate(realization(feasibility_state=state)).errors, ())
        required = self.validate(realization(evidence_policy="REQUIRED_BEFORE_W2"))
        self.assertEqual(required.errors, ())
        legacy_spelling = self.validate(realization(evidence_policy="REQUIRED_BEFORE_RELEASE"))
        self.assertEqual(
            legacy_spelling.errors,
            ("realization.Codex.evidence_policy_invalid",),
        )


if __name__ == "__main__":
    unittest.main()
