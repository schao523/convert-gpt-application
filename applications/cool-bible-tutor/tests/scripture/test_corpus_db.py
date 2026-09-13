import os
from contextlib import closing
import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).parents[2] / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
sys.path.insert(0, str(SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture"
RUNTIME.mkdir(exist_ok=True)

from corpus_db import (  # noqa: E402
    BUNDLED_DATABASE,
    VerseRecord,
    fetch_passage,
    initialize_database,
    insert_verses,
    open_corpus_read_only,
    resolve_data_dir,
    resolve_database,
)
from references import parse_reference  # noqa: E402


class CorpusDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.database = RUNTIME / "corpus-test.sqlite3"
        self.database.unlink(missing_ok=True)
        initialize_database(self.database)

    def tearDown(self):
        self.database.unlink(missing_ok=True)

    def test_path_precedence(self):
        explicit = RUNTIME / "explicit"
        environment = RUNTIME / "environment"
        with patch.dict(os.environ, {"COOL_BIBLE_TUTOR_DATA_DIR": str(environment)}):
            self.assertEqual(resolve_data_dir(explicit), explicit.resolve())
            self.assertEqual(resolve_data_dir(None), environment.resolve())
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve_data_dir(None).name, "data")

    def test_database_precedence_is_explicit_then_configured_then_bundled(self):
        explicit = RUNTIME / "explicit"
        configured = RUNTIME / "configured"

        self.assertEqual(resolve_database(explicit, {}), explicit.resolve() / "cuv.sqlite3")
        self.assertEqual(
            resolve_database(
                None, {"COOL_BIBLE_TUTOR_DATA_DIR": str(configured)}
            ),
            configured.resolve() / "cuv.sqlite3",
        )
        self.assertEqual(resolve_database(None, {}), BUNDLED_DATABASE)

    def test_bundled_database_connection_rejects_mutation(self):
        with closing(open_corpus_read_only(BUNDLED_DATABASE)) as connection:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("DELETE FROM verses")

    def test_insert_and_fetch_preserve_canonical_order_and_trust(self):
        records = [
            VerseRecord(40, 5, 4, "合成文字乙。", "synthetic.pdf", 8, 98.0, True),
            VerseRecord(40, 5, 3, "合成文字甲。", "synthetic.pdf", 7, 97.0, True),
        ]
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, records)
            passage = fetch_passage(connection, parse_reference("太 5:3-4"))
        self.assertEqual([record.verse for record in passage.records], [3, 4])
        self.assertEqual(passage.canonical_reference, "馬太福音 5:3-4")
        self.assertTrue(passage.verified)
        self.assertEqual(passage.records[0].source_page, 7)


if __name__ == "__main__":
    unittest.main()
