import contextlib
from contextlib import closing
import io
import json
import os
import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).parents[2] / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
sys.path.insert(0, str(SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture"
RUNTIME.mkdir(exist_ok=True)

from corpus_db import VerseRecord, initialize_database, insert_verses  # noqa: E402
from get_passage import main  # noqa: E402


class PassageCliTests(unittest.TestCase):
    def setUp(self):
        self.data_dir = RUNTIME / "passage-cli"
        self.data_dir.mkdir(exist_ok=True)
        self.database = self.data_dir / "cuv.sqlite3"
        self.database.unlink(missing_ok=True)

    def tearDown(self):
        self.database.unlink(missing_ok=True)

    def call_main(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(list(arguments))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_missing_database_returns_setup_guidance(self):
        code, _, stderr = self.call_main("--reference", "太 5:3", "--data-dir", str(self.data_dir))
        self.assertEqual(code, 2)
        self.assertIn("build_cuv_index.py --data-dir", stderr)
        self.assertNotIn("--old-testament", stderr)

    def test_json_contains_ordered_provenance(self):
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, [
                    VerseRecord(40, 5, 3, "合成甲。", "synthetic.pdf", 7, 99.0, True),
                    VerseRecord(40, 5, 4, "合成乙。", "synthetic.pdf", 8, 99.0, True),
                ])
        code, stdout, _ = self.call_main(
            "--reference", "太 5:3-4", "--data-dir", str(self.data_dir), "--format", "json"
        )
        payload = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(payload["canonical_reference"], "馬太福音 5:3-4")
        self.assertEqual([item["verse"] for item in payload["verses"]], [3, 4])
        self.assertEqual(payload["verses"][0]["source_page"], 7)
        self.assertEqual(payload["trust_status"], "verified")

    def test_unverified_result_is_labeled_and_exits_three(self):
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, [
                    VerseRecord(40, 5, 3, "待核合成文字。", "synthetic.pdf", 7, 42.0, False),
                ])
        code, stdout, _ = self.call_main(
            "--reference", "太 5:3", "--data-dir", str(self.data_dir), "--format", "text"
        )
        self.assertEqual(code, 3)
        self.assertIn("未核實", stdout)
        self.assertIn("synthetic.pdf", stdout)

    def test_no_data_dir_retrieves_from_bundled_verified_corpus(self):
        with patch.dict(os.environ, {}, clear=True):
            code, stdout, stderr = self.call_main(
                "--reference", "約 3:16", "--format", "json"
            )

        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(payload["canonical_reference"], "約翰福音 3:16")
        self.assertEqual(payload["trust_status"], "verified")
        self.assertEqual(len(payload["verses"]), 1)
        self.assertEqual(payload["verses"][0]["source_file"], "Bible 新約聖經和合本.pdf")


if __name__ == "__main__":
    unittest.main()
