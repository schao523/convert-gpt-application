import json
from pathlib import Path, PurePosixPath
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKAGE_SHA256 = "8edde15b6bd0e658990c3a354b85ea90b93bfa1c17216c7b11928f8284c3f497"
NORMALIZED_PACKAGE_SHA256 = "953747ad9f92d05dc29a049359fa06227fc2f8cc8590242cd4d1f09e17f82b21"


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class ConversionContractTests(unittest.TestCase):
    def test_identity_scope_and_provenance_are_explicit(self) -> None:
        config = load_json("conversion.json")
        manifest = load_json(".codex-plugin/plugin.json")
        scope = load_json("docs/phase-one-scope.json")
        inventory = load_json("docs/source-inventory.json")
        runtime = (ROOT / "docs/runtime-compatibility.md").read_text(encoding="utf-8")

        self.assertEqual(config["schema_version"], 2)
        self.assertEqual(config["application_id"], "plugin-builder")
        self.assertEqual(config["plugin_id"], "plugin-builder")
        self.assertEqual(manifest["name"], "plugin-builder")
        self.assertEqual(manifest["version"], "0.1.0")

        self.assertEqual(scope["scope"], "OPENAI_ONLY_PHASE_ONE")
        self.assertEqual(scope["source_package_sha256"], SOURCE_PACKAGE_SHA256)
        self.assertEqual(scope["normalized_package_sha256"], NORMALIZED_PACKAGE_SHA256)
        self.assertEqual(
            set(scope["target_runtimes"]),
            {"ChatGPT Work Local/Desktop", "Codex"},
        )
        self.assertGreaterEqual(set(scope["excluded_runtimes"]), {"OpenClaw", "Claude"})
        self.assertEqual(scope["publication_state"], "NOT_PERFORMED")
        self.assertEqual(scope["release_state"], "NOT_PERFORMED")

        serialized_inventory = json.dumps(inventory, ensure_ascii=False)
        self.assertNotRegex(serialized_inventory, re.compile(r"[A-Za-z]:[\\/]"))
        self.assertNotIn("/Users/", serialized_inventory)
        self.assertNotIn("\\Users\\", serialized_inventory)
        for item in inventory["source_inventory"]:
            path = PurePosixPath(item["path"])
            self.assertFalse(path.is_absolute(), item["path"])
            self.assertNotIn("..", path.parts, item["path"])

        self.assertIn("| OpenClaw | NOT APPLICABLE |", runtime)
        self.assertIn("| Codex | RUNTIME VERIFIED |", runtime)
        self.assertIn("| ChatGPT Work Local/Desktop | RUNTIME VERIFIED |", runtime)


if __name__ == "__main__":
    unittest.main()
