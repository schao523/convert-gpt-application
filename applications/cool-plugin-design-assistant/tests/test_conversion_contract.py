import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ConversionContractTests(unittest.TestCase):
    def test_identity_inventory_and_invariants_are_complete(self) -> None:
        required = (
            ROOT / "conversion.json",
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
        self.assertEqual(manifest["version"], "1.0.0")
        self.assertEqual(len(inventory["source_inventory"]), 16)
        self.assertFalse(
            any(":\\Users\\" in item["path"] for item in inventory["source_inventory"])
        )
        for number in range(1, 16):
            self.assertIn(f"INV-{number:03d}", invariants)


if __name__ == "__main__":
    unittest.main()
