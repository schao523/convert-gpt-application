from __future__ import annotations

import json
from pathlib import Path
import unittest


class ImportedPackageTests(unittest.TestCase):
    def test_manifest_pair_identity(self) -> None:
        root = Path(__file__).resolve().parents[1] / "imported-plugin"
        identities = []
        for relative in ("plugin.json", ".codex-plugin/plugin.json"):
            payload = json.loads((root / relative).read_text(encoding="utf-8"))
            identities.append((payload["name"], payload["version"]))
        self.assertEqual(identities, [('sermon-coach', '1.0.3')] * 2)


if __name__ == "__main__":
    unittest.main()
