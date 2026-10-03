from pathlib import Path
import subprocess
import unittest

from obvious_one_plugin_framework.marketplace import load_preparation_catalog
from obvious_one_plugin_framework.verification import discover_applications


ROOT = Path(__file__).resolve().parents[1]
class ApplicationConfigTests(unittest.TestCase):
    def test_design_assistant_remains_dual_runtime(self) -> None:
        catalog = load_preparation_catalog(
            ROOT / "marketplaces" / "obvious-one.json", ROOT
        )
        assistant = next(
            entry
            for entry in catalog.applications
            if entry.application.plugin_id == "cool-plugin-design-assistant"
        )

        self.assertEqual(assistant.target("codex").mode, "build")
        self.assertEqual(assistant.target("codex").destination, "plugins/cool-plugin-design-assistant")
        self.assertEqual(assistant.target("openclaw").mode, "build")
        self.assertEqual(
            assistant.target("openclaw").destination,
            "openclaw/cool-plugin-design-assistant",
        )

    def test_all_cataloged_target_destinations_match_application_identity(self) -> None:
        catalog = load_preparation_catalog(
            ROOT / "marketplaces" / "obvious-one.json", ROOT
        )

        self.assertEqual(catalog.schema_version, 2)
        for entry in catalog.applications:
            plugin_id = entry.application.plugin_id
            for target_name, target in entry.applicable_targets():
                prefix = "plugins" if target_name == "codex" else "openclaw"
                self.assertEqual(target.destination, f"{prefix}/{plugin_id}")

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
        assistant = configs["cool-plugin-design-assistant"]

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
        self.assertEqual(cool_targets["distribution-audit"], ("codex",))
        self.assertEqual(cool_targets["runtime-status"], ("codex",))
        self.assertEqual(cool_targets["exact-passage"], ("openclaw",))

        self.assertIsNotNone(assistant.verification.marketplace)
        self.assertEqual(
            assistant.verification.marketplace.codex_path,
            "plugins/{plugin_id}",
        )
        self.assertEqual(
            assistant.verification.marketplace.openclaw_path,
            "openclaw/{plugin_id}",
        )
        self.assertTrue(assistant.verification.marketplace.approved_delta.is_file())
        assistant_targets = {
            item.command_id: item.marketplace_targets
            for item in assistant.verification.commands
        }
        self.assertEqual(len(assistant_targets), 6)
        self.assertTrue(
            all(targets == ("codex", "openclaw") for targets in assistant_targets.values())
        )
        assistant_fixture_args = {
            argument
            for command in assistant.verification.commands
            for argument in command.argv
            if "fixtures/" in argument.replace("\\", "/")
        }
        self.assertTrue(assistant_fixture_args)
        self.assertTrue(
            all(
                argument.startswith("{application_root}/docs/validation-fixtures/")
                for argument in assistant_fixture_args
            )
        )
        for argument in assistant_fixture_args:
            relative = argument.removeprefix("{application_root}/")
            self.assertTrue(
                (assistant.root / Path(relative)).is_file(),
                relative,
            )

    def test_plugin_builder_phase_one_configuration_is_explicit(self) -> None:
        configs = {item.plugin_id: item for item in discover_applications(ROOT)}
        builder = configs["plugin-builder"]

        self.assertEqual(builder.version, "0.1.3")
        self.assertIsNone(builder.verification.marketplace)
        self.assertEqual(
            {
                command.command_id: command.marketplace_targets
                for command in builder.verification.commands
            },
            {
                "runtime-status": ("codex",),
                "session-validator": (),
                "create-smoke": (),
                "update-smoke": (),
                "bundled-local-tool-smoke": (),
            },
        )


if __name__ == "__main__":
    unittest.main()
