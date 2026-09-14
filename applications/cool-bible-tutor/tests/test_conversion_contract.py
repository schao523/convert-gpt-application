from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest

from obvious_one_plugin_framework.provenance import validate_provenance
from obvious_one_plugin_framework.verification import load_application_config


APPLICATION = Path(__file__).resolve().parents[1]
ROOT = APPLICATION.parents[1]


class CoolBibleTutorConversionContractTests(unittest.TestCase):
    def test_conversion_preserves_application_owned_identity_and_commands(self) -> None:
        config = load_application_config(APPLICATION, ROOT)

        self.assertEqual(config.application_id, "cool-bible-tutor")
        self.assertEqual(config.plugin_id, "cool-bible-tutor")
        self.assertEqual(config.version, "2.4.6")
        self.assertEqual(
            [command.command_id for command in config.verification.commands],
            ["distribution-audit", "exact-passage", "runtime-status"],
        )
        self.assertEqual(config.marketplace_repository, "schao523/obvious-one-plugins")
        self.assertEqual(config.provenance.source_repository, "cool-bible-tutor-gpt-source")
        self.assertEqual(
            config.provenance.incorporated_branches,
            ("feature/generic-openclaw-framework", "codex/openclaw-compat-evaluation"),
        )

    def test_checked_in_provenance_matches_application_contract(self) -> None:
        config = load_application_config(APPLICATION, ROOT)
        payload = json.loads(config.source_inventory.read_text(encoding="utf-8"))

        validate_provenance(payload, config)

    def test_local_source_configuration_is_ignored_and_untracked(self) -> None:
        relative = "applications/cool-bible-tutor/conversion.local.json"
        ignored = subprocess.run(
            ["git", "check-ignore", relative],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(ignored.returncode, 0, ignored.stderr)
        tracked = subprocess.check_output(["git", "ls-files", relative], cwd=ROOT, text=True)
        self.assertEqual(tracked, "")

    def test_generic_templates_do_not_contain_reference_application_identity(self) -> None:
        forbidden = ("cool-bible-tutor", "2.4.6", "John 3:16", "約 3:16")
        templates = ROOT / "templates"
        for path in templates.rglob("*.template"):
            content = path.read_text(encoding="utf-8")
            for value in forbidden:
                self.assertNotIn(value, content, path.as_posix())


if __name__ == "__main__":
    unittest.main()
