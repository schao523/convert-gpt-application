from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.contract import ContractError
from obvious_one_plugin_framework.contract_migration import (
    build_migration_proposal,
    write_migration_proposal,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures"
LEGACY = FIXTURES / "plugin-alpha" / "distribution.json"


class ContractMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_legacy_migration_writes_unresolved_proposal_not_valid_contract(self) -> None:
        destination = self.root / "proposal.json"

        result = write_migration_proposal(LEGACY, destination)
        payload = json.loads(destination.read_text(encoding="utf-8"))

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.code, "migration_decisions_required")
        self.assertEqual(payload["proposal_schema_version"], 1)
        self.assertEqual(payload["target_schema_version"], 3)
        self.assertEqual(payload["contract_draft"]["schema_version"], 3)
        self.assertIsNone(payload["contract_draft"]["publication"]["github_marketplace"]["enabled"])
        self.assertTrue(payload["diagnostics"])
        self.assertTrue(
            all(rule["classification"] is None for rule in payload["contract_draft"]["content_rules"])
        )

    def test_migration_refuses_existing_destination(self) -> None:
        destination = self.root / "proposal.json"
        destination.write_text("keep", encoding="utf-8")

        with self.assertRaisesRegex(ContractError, "migration_destination_exists"):
            write_migration_proposal(LEGACY, destination)

        self.assertEqual(destination.read_text(encoding="utf-8"), "keep")

    def test_proposal_is_deterministic_and_contains_no_private_source_path(self) -> None:
        first = self.root / "first" / "proposal.json"
        second = self.root / "second" / "proposal.json"
        first.parent.mkdir()
        second.parent.mkdir()

        write_migration_proposal(LEGACY, first)
        write_migration_proposal(LEGACY, second)

        self.assertEqual(first.read_bytes(), second.read_bytes())
        encoded = first.read_text(encoding="utf-8")
        self.assertNotIn(str(LEGACY.parent), encoded)
        self.assertTrue(encoded.endswith("\n"))

    def test_proposal_reports_each_selected_file_and_safe_candidates(self) -> None:
        proposal = build_migration_proposal(LEGACY)

        file_diagnostics = [
            item for item in proposal.diagnostics if item.code == "classification_required"
        ]
        self.assertEqual(
            [item.path for item in file_diagnostics],
            [".codex-plugin/plugin.json", "README.md"],
        )
        for diagnostic in file_diagnostics:
            self.assertEqual(
                diagnostic.candidates,
                ("text", "binary", "exclude", "external_asset", "private_local"),
            )


if __name__ == "__main__":
    unittest.main()
