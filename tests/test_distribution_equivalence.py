from pathlib import Path
import tempfile
import unittest

from scripts.verify_extraction import compare_trees


class DistributionEquivalenceTests(unittest.TestCase):
    def test_compare_trees_reports_sorted_differences(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = root / "expected"
            actual = root / "actual"
            expected.mkdir()
            actual.mkdir()
            (expected / "same.txt").write_text("same", encoding="utf-8")
            (actual / "same.txt").write_text("same", encoding="utf-8")
            (expected / "changed.txt").write_text("old", encoding="utf-8")
            (actual / "changed.txt").write_text("new", encoding="utf-8")
            (expected / "missing.txt").write_text("missing", encoding="utf-8")
            (actual / "unexpected.txt").write_text("unexpected", encoding="utf-8")
            self.assertEqual(
                compare_trees(expected, actual, excluded=set()),
                {
                    "missing": ["missing.txt"],
                    "unexpected": ["unexpected.txt"],
                    "digest_mismatch": ["changed.txt"],
                },
            )


if __name__ == "__main__":
    unittest.main()
