from __future__ import annotations

import re
import sys
from pathlib import Path
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from plugin_builder_core.runtime_adapters import (
    adapter_registry,
    adapter_registry_sha256,
    validate_realization_against_registry,
)


def realization(**changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "target_runtime": "Codex",
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


class RuntimeAdapterRegistryTests(unittest.TestCase):
    def test_registry_is_immutable_canonically_ordered_and_digest_stable(self) -> None:
        first = adapter_registry()
        second = adapter_registry()
        self.assertEqual(first, second)
        self.assertIsInstance(first, tuple)
        identities = [(item.adapter_id, item.adapter_version) for item in first]
        self.assertEqual(identities, sorted(identities))
        self.assertEqual(
            identities,
            [
                ("direct-local", "1"),
                ("mcp-streamable-http", "1"),
                ("runtime-native", "1"),
                ("unsupported", "1"),
            ],
        )
        digest = adapter_registry_sha256()
        self.assertEqual(digest, adapter_registry_sha256())
        self.assertRegex(digest, re.compile(r"^[0-9a-f]{64}$"))
        self.assertEqual(digest, "e4e4d98d51fc35b531fe5664c6d95dbb172477daaac8fb52ab697ea431138973")

    def test_streamable_http_support_is_exactly_target_and_channel_aware(self) -> None:
        definition = next(item for item in adapter_registry() if item.adapter_id == "mcp-streamable-http")
        self.assertEqual(definition.endpoint_policy, "HTTPS_ONLY")
        self.assertEqual(definition.installation_channels, ("OPENAI_PORTABLE_PLUGIN",))
        self.assertEqual(definition.verification_channels, ("PLUGIN_BUILDER_LOCAL_TEST",))
        for target in ("ChatGPT Work Local/Desktop", "Codex"):
            with self.subTest(target=target):
                errors, blockers = validate_realization_against_registry(
                    realization(target_runtime=target),
                    installation_channel="OPENAI_PORTABLE_PLUGIN",
                )
                self.assertEqual(errors, ())
                self.assertEqual(blockers, ())

    def test_unknown_adapter_version_mechanism_and_target_fail_closed(self) -> None:
        cases = (
            (
                realization(adapter_id="missing"),
                ("adapter.unknown:missing",),
            ),
            (
                realization(adapter_version="2"),
                ("adapter.mcp-streamable-http.version_unsupported:2",),
            ),
            (
                realization(mechanism="DIRECT_LOCAL"),
                ("adapter.mcp-streamable-http.mechanism_mismatch",),
            ),
            (
                realization(target_runtime="OpenClaw"),
                ("adapter.mcp-streamable-http.target_unsupported:OpenClaw",),
            ),
        )
        for payload, expected in cases:
            with self.subTest(expected=expected):
                errors, blockers = validate_realization_against_registry(
                    payload,
                    installation_channel="OPENAI_PORTABLE_PLUGIN",
                )
                self.assertEqual(errors, expected)
                self.assertEqual(blockers, ())

    def test_test_harness_cannot_be_confused_with_installed_support(self) -> None:
        errors, blockers = validate_realization_against_registry(
            realization(),
            installation_channel="PLUGIN_BUILDER_LOCAL_TEST",
        )
        self.assertEqual(errors, ())
        self.assertEqual(
            blockers,
            ("adapter.mcp-streamable-http.verification_channel_not_installed",),
        )

    def test_direct_local_and_runtime_native_are_conservative_until_channel_proven(self) -> None:
        cases = (
            realization(
                mechanism="DIRECT_LOCAL",
                adapter_id="direct-local",
                transport="DIRECT_ARGV",
                execution_location="USER_DEVICE",
            ),
            realization(
                mechanism="RUNTIME_NATIVE",
                adapter_id="runtime-native",
                transport="RUNTIME_API",
                execution_location="RUNTIME_HOST",
            ),
        )
        for payload in cases:
            with self.subTest(adapter=payload["adapter_id"]):
                errors, blockers = validate_realization_against_registry(
                    payload,
                    installation_channel="OPENAI_PORTABLE_PLUGIN",
                )
                self.assertEqual(errors, ())
                self.assertEqual(
                    blockers,
                    (f"adapter.{payload['adapter_id']}.channel_unsupported:OPENAI_PORTABLE_PLUGIN",),
                )

    def test_local_process_is_not_inferred_from_local_test_capability(self) -> None:
        errors, blockers = validate_realization_against_registry(
            realization(
                mechanism="MCP_LOCAL_PROCESS",
                adapter_id="mcp-local-process",
                transport="MCP_STREAMABLE_HTTP",
                execution_location="USER_DEVICE",
            ),
            installation_channel="PLUGIN_BUILDER_LOCAL_TEST",
        )
        self.assertEqual(errors, ("adapter.unknown:mcp-local-process",))
        self.assertEqual(blockers, ())


if __name__ == "__main__":
    unittest.main()
