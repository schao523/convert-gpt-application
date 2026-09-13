import importlib.util
from pathlib import Path
import shutil
import unittest


PLUGIN = Path(__file__).parents[1]
MODULE = PLUGIN / "scripts" / "build_marketplace_release.py"
spec = importlib.util.spec_from_file_location("marketplace_release", MODULE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class MarketplaceReleaseTests(unittest.TestCase):
    def setUp(self):
        self.destination = PLUGIN.parent / ".marketplace-release-test"
        if self.destination.exists():
            shutil.rmtree(self.destination)

    def tearDown(self):
        if self.destination.exists():
            shutil.rmtree(self.destination)

    def test_release_contains_public_runtime_assets_but_no_private_state(self):
        report = module.build_release(PLUGIN, self.destination, "2.4.6")
        self.assertIn(
            "plugins/cool-bible-tutor/assets/scripture/cuv.sqlite3", report.paths
        )
        self.assertIn(
            "plugins/cool-bible-tutor/assets/rag/cuv-rag-index.sqlite3", report.paths
        )
        self.assertIn(
            "plugins/cool-bible-tutor/vendor/rag-runtime/runtime-lock.json", report.paths
        )
        self.assertIn(
            "plugins/cool-bible-tutor/vendor/obvious-one-runtime/obvious_one_runtime/setup.py",
            report.paths,
        )
        self.assertIn(
            "plugins/cool-bible-tutor/assets/openclaw/remote-assets.json", report.paths
        )
        serialized = "\n".join(report.paths)
        self.assertNotIn(".local-data", serialized)
        self.assertNotIn("__pycache__", serialized)
        self.assertNotIn("tests/test_openclaw_release.py", serialized)
        self.assertNotIn("tests/test_vendored_runtime.py", serialized)
        self.assertNotIn("tools/obvious_one_plugin_framework", serialized)
        self.assertTrue((self.destination / ".obvious-one-marketplace").is_file())
        self.assertTrue(all(len(digest) == 64 for digest in report.sha256.values()))

    def test_builder_refuses_unmarked_nonempty_destination(self):
        self.destination.mkdir(parents=True)
        (self.destination / "unrelated.txt").write_text("owner data", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "nonempty destination"):
            module.build_release(PLUGIN, self.destination, "2.4.6")
        self.assertEqual(
            (self.destination / "unrelated.txt").read_text(encoding="utf-8"),
            "owner data",
        )


if __name__ == "__main__":
    unittest.main()
