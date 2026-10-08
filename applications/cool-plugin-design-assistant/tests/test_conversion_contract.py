import json
from pathlib import Path
import unittest

from obvious_one_plugin_framework.plugin_authoring import validate_manifest_pair


ROOT = Path(__file__).resolve().parents[1]


class ConversionContractTests(unittest.TestCase):
    def test_identity_inventory_and_invariants_are_complete(self) -> None:
        required = (
            ROOT / "conversion.json",
            ROOT / "plugin.json",
            ROOT / ".codex-plugin/plugin.json",
            ROOT / "docs/source-inventory.json",
            ROOT / "docs/application-invariants.md",
        )
        for path in required:
            self.assertTrue(path.is_file(), path.relative_to(ROOT).as_posix())

        config = json.loads((ROOT / "conversion.json").read_text(encoding="utf-8"))
        manifest = json.loads(
            (ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
        )
        portable = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        inventory = json.loads(
            (ROOT / "docs/source-inventory.json").read_text(encoding="utf-8")
        )
        invariants = (ROOT / "docs/application-invariants.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(config["schema_version"], 2)
        self.assertEqual(config["application_id"], "cool-plugin-design-assistant")
        self.assertEqual(manifest["name"], "cool-plugin-design-assistant")
        self.assertEqual(
            manifest["interface"]["displayName"], "Cool Plugin Design Assistant"
        )
        self.assertEqual(manifest["version"], "1.0.2")
        self.assertEqual(
            portable["$schema"],
            "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        )
        self.assertEqual(
            (portable["name"], portable["version"]),
            (manifest["name"], manifest["version"]),
        )
        self.assertEqual(
            portable["extensions"]["com.openai"]["interface"],
            manifest["interface"],
        )
        self.assertEqual(validate_manifest_pair(ROOT), ())
        distribution = json.loads(
            (ROOT / "openclaw/distribution.json").read_text(encoding="utf-8")
        )
        self.assertEqual(distribution["version"], "1.0.2")
        self.assertEqual(len(inventory["source_inventory"]), 16)
        self.assertFalse(
            any(":\\Users\\" in item["path"] for item in inventory["source_inventory"])
        )
        for number in range(1, 16):
            self.assertIn(f"INV-{number:03d}", invariants)

    def test_handoff_delivery_contract_is_digest_bound_and_reopened(self) -> None:
        distribution = (ROOT / "DISTRIBUTION.md").read_text(encoding="utf-8")
        for invariant in (
            "FINAL_ZIP_SHA256",
            "REOPEN_CANONICAL_VALIDATION",
            "ONE_SEMANTIC_AUTHORITY",
        ):
            self.assertIn(invariant, distribution)


if __name__ == "__main__":
    unittest.main()
