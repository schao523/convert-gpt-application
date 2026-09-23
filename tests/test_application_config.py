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

    def test_real_marketplace_mappings_and_command_targets_are_explicit(self) -> None:
        configs = {item.plugin_id: item for item in discover_applications(ROOT)}
        vibe = configs["vibe-coding-designer"]
        cool = configs["cool-bible-tutor"]

        self.assertIsNotNone(vibe.verification.marketplace)
        self.assertEqual(vibe.verification.marketplace.codex_path, "plugins/{plugin_id}")
        self.assertEqual(vibe.verification.marketplace.openclaw_path, "openclaw/{plugin_id}")
        self.assertTrue(vibe.verification.marketplace.approved_delta.is_file())
        vibe_targets = {
            item.command_id: item.marketplace_targets
            for item in vibe.verification.commands
        }
        self.assertEqual(vibe_targets["runtime-status"], ("codex", "openclaw"))
        self.assertEqual(vibe_targets["design-validator"], ())
        self.assertEqual(vibe_targets["workflow-validator"], ())

        cool_targets = {
            item.command_id: item.marketplace_targets
            for item in cool.verification.commands
        }
        self.assertEqual(cool_targets["distribution-audit"], ("codex", "openclaw"))
        self.assertEqual(cool_targets["runtime-status"], ("codex", "openclaw"))
        self.assertEqual(cool_targets["exact-passage"], ("openclaw",))


if __name__ == "__main__":
    unittest.main()
