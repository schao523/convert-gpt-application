from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


class ImportedPackageTests(unittest.TestCase):
    def test_imported_tree_is_checked_out_byte_exact(self) -> None:
        repository = Path(__file__).resolve().parents[3]
        relatives = (
            "applications/sermon-coach/LICENSE",
            "applications/sermon-coach/imported-plugin/README.md",
        )
        result = subprocess.run(
            ["git", "check-attr", "text", "--", *relatives],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            result.stdout.splitlines(),
            [f"{relative}: text: unset" for relative in relatives],
        )

    def test_manifest_pair_identity(self) -> None:
        root = Path(__file__).resolve().parents[1] / "imported-plugin"
        identities = []
        for relative in ("plugin.json", ".codex-plugin/plugin.json"):
            payload = json.loads((root / relative).read_text(encoding="utf-8"))
            identities.append((payload["name"], payload["version"]))
        self.assertEqual(identities, [('sermon-coach', '1.0.3')] * 2)


if __name__ == "__main__":
    unittest.main()
