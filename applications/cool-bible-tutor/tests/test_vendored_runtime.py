from __future__ import annotations

from pathlib import Path
import unittest


PLUGIN = Path(__file__).resolve().parents[1]
REPOSITORY = PLUGIN.parents[1]
TEMPLATE = REPOSITORY / "src/obvious_one_plugin_framework/templates/runtime/obvious_one_runtime"
VENDORED = PLUGIN / "vendor/obvious-one-runtime/obvious_one_runtime"


class VendoredRuntimeTests(unittest.TestCase):
    def test_vendored_bootstrap_matches_framework_template(self) -> None:
        expected = {
            path.relative_to(TEMPLATE).as_posix(): path.read_bytes()
            for path in TEMPLATE.rglob("*.py")
        }
        actual = {
            path.relative_to(VENDORED).as_posix(): path.read_bytes()
            for path in VENDORED.rglob("*.py")
        }
        self.assertEqual(actual, expected)
        self.assertIn("setup.py", actual)
        self.assertIn("adapters.py", actual)


if __name__ == "__main__":
    unittest.main()
