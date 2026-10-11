from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from obvious_one_plugin_framework.plugin_onboarding import load_repair_contract
from obvious_one_plugin_framework.verification import load_application_config


ROOT = Path(__file__).resolve().parents[1]
APPLICATION = ROOT / "applications" / "growing-with-children"


class DelegatedReferenceRepairRepositoryContractTests(unittest.TestCase):
    def test_generic_legacy_inspection_command_is_executable(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "obvious_one_plugin_framework.cli",
                "inspect-plugin-zip",
                "--help",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--archive", completed.stdout)
        self.assertIn("--output", completed.stdout)
        self.assertIn("--json", completed.stdout)

    def test_product_repair_command_and_configuration_are_executable(self) -> None:
        launcher = APPLICATION / "scripts" / "build_repaired_release.py"
        completed = subprocess.run(
            [sys.executable, "-B", str(launcher), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--source", completed.stdout)
        self.assertIn("--output", completed.stdout)
        self.assertIn("--json", completed.stdout)
        config = load_application_config(APPLICATION, ROOT)
        contract = load_repair_contract(
            APPLICATION / "repair" / "delegated-reference-repair-v1.json"
        )
        self.assertEqual(config.plugin_id, contract.plugin_id)
        self.assertEqual(config.version, contract.target_version)
        self.assertEqual(
            [command.marketplace_targets for command in config.verification.commands],
            [()],
        )

    def test_repair_recipe_never_embeds_a_machine_specific_source_path(self) -> None:
        conversion = json.loads((APPLICATION / "conversion.json").read_text(encoding="utf-8"))
        self.assertEqual(conversion["source_location"], "conversion.local.json")
        repair = (APPLICATION / "repair" / "delegated-reference-repair-v1.json").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("D:\\", repair)
        self.assertNotIn("C:\\", repair)

    def test_public_domain_notice_repair_contract_is_documented(self) -> None:
        command_reference = (ROOT / "docs" / "PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("plugin-delegated-reference-repair-v2", command_reference)
        self.assertIn("THIRD_PARTY_NOTICES.md", command_reference)
        self.assertIn("PUBLIC_DOMAIN", command_reference)


if __name__ == "__main__":
    unittest.main()
