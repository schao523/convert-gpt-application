from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest


TESTS = Path(__file__).parent
SCRIPTS = TESTS.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from plugin_builder_core.mcp_realization import (
    canonical_mcp_bytes,
    project_mcp_configuration,
    validate_mcp_projection,
)


FIXTURE = TESTS / "fixtures" / "plan-create.json"


def proposal() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class McpRealizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def materialize_projection(self, payload: dict) -> None:
        portable, compatibility = project_mcp_configuration(payload)
        if portable is not None:
            (self.root / "mcp.json").write_bytes(canonical_mcp_bytes(portable))
        if compatibility is not None:
            (self.root / ".mcp.json").write_bytes(canonical_mcp_bytes(compatibility))

    def test_projects_portable_and_codex_compatibility_configuration_deterministically(self) -> None:
        payload = proposal()
        first = project_mcp_configuration(payload)
        second = project_mcp_configuration(copy.deepcopy(payload))
        self.assertEqual(first, second)
        portable, compatibility = first
        self.assertEqual(
            portable,
            {
                "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
                "mcpServers": {
                    "normalizer": {
                        "type": "streamable-http",
                        "url": "https://example.com/mcp",
                    }
                },
            },
        )
        self.assertEqual(compatibility, portable)
        self.assertEqual(canonical_mcp_bytes(portable), canonical_mcp_bytes(compatibility))

    def test_skills_only_plan_omits_mcp_files(self) -> None:
        payload = proposal()
        payload["tools"] = []
        payload["expected_members"] = [
            item for item in payload["expected_members"]
            if item not in {"mcp.json", ".mcp.json"}
        ]
        self.assertEqual(project_mcp_configuration(payload), (None, None))
        self.assertEqual(validate_mcp_projection(payload, self.root), ())

    def test_multiple_servers_are_sorted_and_duplicate_server_or_tool_ids_fail(self) -> None:
        payload = proposal()
        second = copy.deepcopy(payload["tools"][0])
        second["id"] = "alpha-tool"
        second["mcp"]["server_id"] = "alpha"
        second["mcp"]["url"] = "https://alpha.example.com/mcp"
        for realization in second["realizations"]:
            realization["exposed_capability"] = "alpha-tool"
        payload["tools"].append(second)
        portable, _ = project_mcp_configuration(payload)
        self.assertEqual(list(portable["mcpServers"]), ["alpha", "normalizer"])

        duplicate_server = copy.deepcopy(payload)
        duplicate_server["tools"][1]["mcp"]["server_id"] = "normalizer"
        self.assertIn(
            "mcp.server_duplicate:normalizer",
            validate_mcp_projection(duplicate_server, self.root),
        )
        duplicate_tool = copy.deepcopy(payload)
        duplicate_tool["tools"][1]["id"] = "normalize-input"
        self.assertIn(
            "mcp.tool_duplicate:normalize-input",
            validate_mcp_projection(duplicate_tool, self.root),
        )

    def test_rejects_unsafe_remote_endpoints_transports_paths_and_credentials(self) -> None:
        cases = (
            ("http://example.com/mcp", "mcp.url_https_required:normalizer"),
            ("https://user:password@example.com/mcp", "mcp.url_credentials_forbidden:normalizer"),
            ("https://example.com/mcp?token=secret", "mcp.url_query_forbidden:normalizer"),
            ("https://localhost:8443/mcp", "mcp.remote_loopback_forbidden:normalizer"),
            ("https://127.0.0.1/mcp", "mcp.remote_loopback_forbidden:normalizer"),
        )
        for url, diagnostic in cases:
            with self.subTest(url=url):
                payload = proposal()
                payload["tools"][0]["mcp"]["url"] = url
                self.assertIn(diagnostic, validate_mcp_projection(payload, self.root))

        payload = proposal()
        payload["tools"][0]["mcp"]["transport"] = "stdio"
        self.assertIn("mcp.transport_unsupported:normalizer", validate_mcp_projection(payload, self.root))
        payload = proposal()
        payload["tools"][0]["mcp"]["config_file"] = "../mcp.json"
        self.assertIn("mcp.config_path_invalid:normalizer", validate_mcp_projection(payload, self.root))
        payload = proposal()
        payload["tools"][0]["mcp"]["authorization"] = "Bearer secret"
        self.assertIn("mcp.credential_material_forbidden:normalizer", validate_mcp_projection(payload, self.root))

    def test_declared_members_and_materialized_bytes_must_match_exact_projection(self) -> None:
        payload = proposal()
        payload["expected_members"] = sorted(set(payload["expected_members"]) | {"mcp.json", ".mcp.json"})
        self.materialize_projection(payload)
        self.assertEqual(validate_mcp_projection(payload, self.root), ())

        (self.root / "mcp.json").write_text("{}\n", encoding="ascii")
        self.assertIn("mcp.portable_projection_mismatch", validate_mcp_projection(payload, self.root))

        undeclared = proposal()
        undeclared["expected_members"] = [
            item for item in undeclared["expected_members"]
            if item not in {"mcp.json", ".mcp.json"}
        ]
        self.materialize_projection(undeclared)
        self.assertIn("mcp.generated_member_undeclared:.mcp.json", validate_mcp_projection(undeclared, self.root))
        self.assertIn("mcp.generated_member_undeclared:mcp.json", validate_mcp_projection(undeclared, self.root))


if __name__ == "__main__":
    unittest.main()
