from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.plugin_authoring import (
    PluginAuthoringError,
    legacy_overlay_from_portable,
    materialize_manifest_pair,
    portable_manifest_from_legacy,
    validate_manifest_pair,
    validate_portable_manifest,
)


PORTABLE_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"


class PluginAuthoringManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "sample-plugin"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_json(self, relative: str, payload: object) -> Path:
        path = self.root / Path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    @staticmethod
    def codes(issues) -> set[str]:
        return {issue.code for issue in issues}

    def portable(self, *, default_prompt: object = "Help me use this plugin.") -> dict[str, object]:
        return {
            "$schema": PORTABLE_SCHEMA,
            "name": "sample-plugin",
            "version": "1.2.3",
            "description": "A portable sample plugin.",
            "author": {"name": "Example Developer"},
            "extensions": {
                "com.openai": {
                    "interface": {
                        "displayName": "Sample Plugin",
                        "shortDescription": "Portable sample",
                        "longDescription": "A portable sample plugin used to exercise the authoring contract.",
                        "developerName": "Example Developer",
                        "category": "Productivity",
                        "capabilities": ["Interactive", "Read"],
                        "defaultPrompt": default_prompt,
                    }
                }
            },
        }

    def legacy(self, *, default_prompt: object = "Help me use this plugin.") -> dict[str, object]:
        return {
            "name": "sample-plugin",
            "version": "1.2.3",
            "description": "A portable sample plugin.",
            "author": {"name": "Example Developer"},
            "skills": "./skills/",
            "interface": {
                "displayName": "Sample Plugin",
                "shortDescription": "Portable sample",
                "longDescription": "A portable sample plugin used to exercise the authoring contract.",
                "developerName": "Example Developer",
                "category": "Productivity",
                "capabilities": ["Interactive", "Read"],
                "defaultPrompt": default_prompt,
            },
        }

    def test_portable_manifest_requires_agent_plugins_schema_and_openai_extension(self) -> None:
        payload = self.portable()
        del payload["$schema"]
        payload["extensions"] = {}
        self.write_json("plugin.json", payload)

        issues = validate_portable_manifest(self.root)

        self.assertEqual(
            self.codes(issues),
            {"portable_manifest_schema_invalid", "portable_openai_extension_missing"},
        )
        self.assertTrue(all(issue.path == "plugin.json" for issue in issues))

    def test_portable_manifest_rejects_legacy_root_keys(self) -> None:
        payload = self.portable()
        payload.update({"skills": "./skills/", "interface": {}, "mcpServers": {}, "apps": []})
        self.write_json("plugin.json", payload)

        issues = validate_portable_manifest(self.root)

        forbidden = sorted(issue.detail for issue in issues if issue.code == "portable_manifest_forbidden_key")
        self.assertEqual(forbidden, ["apps", "interface", "mcpServers", "skills"])

    def test_short_description_is_at_most_thirty_characters(self) -> None:
        payload = self.portable()
        payload["extensions"]["com.openai"]["interface"]["shortDescription"] = "x" * 31  # type: ignore[index]
        self.write_json("plugin.json", payload)

        issues = validate_portable_manifest(self.root)

        self.assertIn("portable_short_description_too_long", self.codes(issues))

    def test_portable_discovery_uses_fixed_skills_and_mcp_locations(self) -> None:
        payload = self.portable()
        self.write_json("plugin.json", payload)
        (self.root / "skills/demo").mkdir(parents=True)
        (self.root / "skills/demo/SKILL.md").write_text(
            "---\nname: demo\ndescription: Demonstrate the supported workflow.\n---\n",
            encoding="utf-8",
        )
        self.write_json("mcp.json", {"mcpServers": {}})

        self.assertEqual(validate_portable_manifest(self.root), ())
        self.assertNotIn("skills", payload)
        self.assertNotIn("mcpServers", payload)

    def test_legacy_manifest_converts_to_portable_without_losing_identity(self) -> None:
        converted = portable_manifest_from_legacy(self.legacy())

        self.assertEqual(converted, self.portable())
        self.assertNotIn("skills", converted)
        self.assertNotIn("interface", converted)

    def test_portable_manifest_generates_legacy_overlay(self) -> None:
        self.assertEqual(legacy_overlay_from_portable(self.portable()), self.legacy())

    def test_manifest_pair_rejects_identity_presentation_and_prompt_order_drift(self) -> None:
        portable = self.portable(default_prompt=["First", "Second"])
        legacy = self.legacy(default_prompt=["Second", "First"])
        legacy["version"] = "1.2.4"
        legacy["interface"]["displayName"] = "Different Name"  # type: ignore[index]
        self.write_json("plugin.json", portable)
        self.write_json(".codex-plugin/plugin.json", legacy)

        issues = validate_manifest_pair(self.root)

        mismatches = sorted(issue.detail for issue in issues if issue.code == "manifest_pair_mismatch")
        self.assertEqual(mismatches, ["interface.defaultPrompt", "interface.displayName", "version"])

    def test_materialize_manifest_pair_is_deterministic(self) -> None:
        self.write_json(".codex-plugin/plugin.json", self.legacy(default_prompt=["First", "Second"]))

        first = materialize_manifest_pair(self.root)
        first_bytes = (self.root / "plugin.json").read_bytes()
        second = materialize_manifest_pair(self.root)

        self.assertEqual(first, second)
        self.assertEqual((self.root / "plugin.json").read_bytes(), first_bytes)
        self.assertTrue(first_bytes.endswith(b"\n"))
        self.assertEqual(validate_manifest_pair(self.root), ())

        changed = self.legacy(default_prompt=["Second", "First"])
        self.write_json(".codex-plugin/plugin.json", changed)
        with self.assertRaisesRegex(PluginAuthoringError, "manifest_pair_mismatch"):
            materialize_manifest_pair(self.root)


if __name__ == "__main__":
    unittest.main()
