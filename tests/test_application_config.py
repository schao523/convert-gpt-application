from pathlib import Path
import json
import subprocess
import unittest

from obvious_one_plugin_framework.verification import load_application_config


ROOT = Path(__file__).resolve().parents[1]
APPLICATION = ROOT / "applications" / "cool-bible-tutor"


class ApplicationConfigTests(unittest.TestCase):
    def test_cool_bible_tutor_conversion_paths_resolve(self) -> None:
        path = APPLICATION / "conversion.json"
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 2)
        self.assertEqual(data["application_id"], "cool-bible-tutor")
        self.assertEqual(data["plugin_id"], "cool-bible-tutor")
        for key in ("coverage_matrix", "distribution_contract"):
            self.assertTrue((APPLICATION / data[key]).is_file(), key)
        self.assertTrue((APPLICATION / data["source_inventory"]).is_file())

        config = load_application_config(APPLICATION, ROOT)
        self.assertEqual(
            [command.command_id for command in config.verification.commands],
            ["distribution-audit", "exact-passage", "runtime-status"],
        )
        self.assertEqual(config.version, "2.4.6")

    def test_local_source_configuration_is_ignored_and_untracked(self) -> None:
        relative = "applications/cool-bible-tutor/conversion.local.json"
        ignored = subprocess.run(
            ["git", "check-ignore", relative],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(ignored.returncode, 0, ignored.stderr)
        tracked = subprocess.check_output(
            ["git", "ls-files", relative],
            cwd=ROOT,
            text=True,
        )
        self.assertEqual(tracked, "")


if __name__ == "__main__":
    unittest.main()
