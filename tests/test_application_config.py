from pathlib import Path
import subprocess
import unittest

from obvious_one_plugin_framework.verification import discover_applications


ROOT = Path(__file__).resolve().parents[1]
class ApplicationConfigTests(unittest.TestCase):
    def test_every_discovered_application_configuration_resolves(self) -> None:
        configs = discover_applications(ROOT)
        self.assertGreater(len(configs), 0)
        for config in configs:
            self.assertTrue(config.coverage_matrix.is_file(), config.application_id)
            self.assertTrue(config.distribution_contract.is_file(), config.application_id)
            self.assertTrue(config.source_inventory.is_file(), config.application_id)

    def test_every_local_source_configuration_is_ignored_and_untracked(self) -> None:
        for config in discover_applications(ROOT):
            relative = config.source_location.relative_to(ROOT).as_posix()
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
