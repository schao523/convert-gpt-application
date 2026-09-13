from pathlib import Path
import json
import re
import unittest

from scripts import write_extraction_provenance as provenance


ROOT = Path(__file__).resolve().parents[1]


class ProvenanceTests(unittest.TestCase):
    def test_output_report_is_safe_on_a_legacy_windows_console(self) -> None:
        self.assertTrue(hasattr(provenance, "output_report"))
        report = provenance.output_report(Path("C:/資料/source-extraction.json"))
        report.encode("cp1252")
        self.assertEqual(
            json.loads(report)["output"],
            "C:\\資料\\source-extraction.json",
        )

    def test_provenance_has_commits_and_no_private_absolute_path(self) -> None:
        path = ROOT / "docs/provenance/source-extraction.json"
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertRegex(data["source_commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(data["marketplace_commit"], r"^[0-9a-f]{40}$")
        self.assertIn(
            "codex/openclaw-compat-evaluation",
            data["incorporated_branches"],
        )
        serialized = json.dumps(data, ensure_ascii=False)
        self.assertIsNone(re.search(r"[A-Za-z]:\\Users\\", serialized))

    def test_source_inventory_contains_hashes_not_file_contents(self) -> None:
        path = ROOT / "docs/provenance/source-extraction.json"
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertGreater(len(data["source_inventory"]), 0)
        for item in data["source_inventory"]:
            self.assertRegex(item["sha256"], r"^[0-9a-f]{64}$")
            self.assertIn(
                item["classification"],
                {"source-only", "public-product-asset"},
            )
            self.assertNotIn("absolute_path", item)


if __name__ == "__main__":
    unittest.main()
