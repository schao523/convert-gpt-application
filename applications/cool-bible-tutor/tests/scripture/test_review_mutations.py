from contextlib import closing
import shutil
import sqlite3
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[2] / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
sys.path.insert(0, str(SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture"
RUNTIME.mkdir(exist_ok=True)

from corpus_db import VerseRecord, initialize_database, insert_verses  # noqa: E402
from review_mutations import (  # noqa: E402
    BackupError, ReviewConflictError, ReviewMutator, ReviewValidationError, VerseEdit,
)
from review_store import ReviewStore  # noqa: E402


class ReviewMutationTests(unittest.TestCase):
    def setUp(self):
        self.data_dir = RUNTIME / "review-mutations"
        if self.data_dir.exists():
            shutil.rmtree(self.data_dir)
        self.data_dir.mkdir()
        self.database = self.data_dir / "cuv.sqlite3"
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, (
                    VerseRecord(40, 5, 1, "合成一。", "new.pdf", 7, 99.0, True),
                    VerseRecord(40, 5, 3, "合成三。", "new.pdf", 7, 80.0, False),
                    VerseRecord(40, 5, 4, "合成四。", "new.pdf", 8, 99.0, False),
                ))
        self.store = ReviewStore(self.database)
        self.mutator = ReviewMutator(
            self.database, self.data_dir, "session-test", {"new.pdf", "old.pdf"}
        )

    def tearDown(self):
        if self.data_dir.exists():
            shutil.rmtree(self.data_dir)

    def test_first_mutation_creates_one_backup_audit_and_stale_marker(self):
        expected = self.store.get_verse(40, 5, 3)
        replacement = VerseEdit(40, 5, 3, "人工核對文字。", "new.pdf", 7, 100.0, True)

        updated = self.mutator.update_verse(expected, replacement, note="checked PDF")
        self.mutator.set_verification((updated,), False, note="second action")

        backups = list((self.data_dir / "backups").glob("cuv-before-review-*.sqlite3"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(self.store.get_verse(40, 5, 3).text, "人工核對文字。")
        with closing(sqlite3.connect(self.database)) as connection:
            metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        self.assertEqual(metadata["rag_index_state"], "stale")
        self.assertEqual([item["status"] for item in self.mutator.history()], ["committed", "committed"])

    def test_stale_expected_snapshot_raises_conflict_without_overwrite(self):
        expected = self.store.get_verse(40, 5, 3)
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "UPDATE verses SET text = '另一工作階段' WHERE book_id=40 AND chapter=5 AND verse=3"
                )
        with self.assertRaises(ReviewConflictError):
            self.mutator.update_verse(
                expected, VerseEdit.from_snapshot(expected, text="舊分頁文字")
            )
        self.assertEqual(self.store.get_verse(40, 5, 3).text, "另一工作階段")

    def test_insert_requires_valid_allowlisted_explicitly_verified_content(self):
        invalid = (
            VerseEdit(40, 5, 2, "", "new.pdf", 7, 100.0, True),
            VerseEdit(40, 5, 2, "人工補入。", "other.pdf", 7, 100.0, True),
            VerseEdit(40, 5, 2, "人工補入。", "new.pdf", 7, 101.0, True),
            VerseEdit(40, 5, 2, "人工補入。", "new.pdf", 7, 100.0, False),
        )
        for replacement in invalid:
            with self.subTest(replacement=replacement):
                with self.assertRaises(ReviewValidationError):
                    self.mutator.insert_verse(replacement)
        self.assertFalse((self.data_dir / "backups").exists())
        with self.assertRaises(LookupError):
            self.store.get_verse(40, 5, 2)

        inserted = self.mutator.insert_verse(
            VerseEdit(40, 5, 2, "人工補入。", "new.pdf", 7, 100.0, True),
            note="compared with page 7",
        )
        self.assertEqual(inserted.text, "人工補入。")
        with self.assertRaises(ReviewConflictError):
            self.mutator.insert_verse(VerseEdit.from_snapshot(inserted))

    def test_verify_page_updates_only_an_unchanged_complete_page(self):
        expected = self.store.page_snapshots("new.pdf", 7)
        updated = self.mutator.verify_page(expected, note="reviewed page 7")
        self.assertEqual([row.verified for row in updated], [True, True])
        self.assertTrue(all(row.verified for row in self.store.page_snapshots("new.pdf", 7)))

    def test_verify_page_rejects_a_hidden_new_row_without_partial_update(self):
        expected = self.store.page_snapshots("new.pdf", 7)
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, (
                    VerseRecord(40, 5, 5, "新增列。", "new.pdf", 7, 99.0, False),
                ))
        with self.assertRaises(ReviewConflictError):
            self.mutator.verify_page(expected)
        self.assertFalse(self.store.get_verse(40, 5, 3).verified)
        self.assertFalse(self.store.get_verse(40, 5, 5).verified)

    def test_verify_page_rejects_changed_row_without_partial_update(self):
        expected = self.store.page_snapshots("new.pdf", 7)
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "UPDATE verses SET text='別的分頁已修改' WHERE book_id=40 AND chapter=5 AND verse=1"
                )
        with self.assertRaises(ReviewConflictError):
            self.mutator.verify_page(expected)
        self.assertEqual(self.store.get_verse(40, 5, 1).text, "別的分頁已修改")
        self.assertFalse(self.store.get_verse(40, 5, 3).verified)

    def test_backup_failure_blocks_history_and_corpus_writes(self):
        (self.data_dir / "backups").write_text("not a directory", encoding="utf-8")
        expected = self.store.get_verse(40, 5, 3)
        with self.assertRaises(BackupError):
            self.mutator.update_verse(
                expected, VerseEdit.from_snapshot(expected, text="不可寫入")
            )
        self.assertEqual(self.store.get_verse(40, 5, 3).text, "合成三。")
        self.assertEqual(self.mutator.history(), [])

    def test_history_preparation_failure_blocks_corpus_write(self):
        self.mutator.history_database.mkdir()
        expected = self.store.get_verse(40, 5, 3)
        with self.assertRaises(sqlite3.Error):
            self.mutator.update_verse(
                expected, VerseEdit.from_snapshot(expected, text="不可寫入")
            )
        self.assertEqual(self.store.get_verse(40, 5, 3).text, "合成三。")

    def test_corpus_failure_preserves_prepared_history_without_changing_row(self):
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "CREATE TRIGGER reject_review BEFORE UPDATE ON verses "
                    "BEGIN SELECT RAISE(ABORT, 'synthetic write failure'); END"
                )
        expected = self.store.get_verse(40, 5, 3)
        with self.assertRaises(sqlite3.IntegrityError):
            self.mutator.update_verse(
                expected, VerseEdit.from_snapshot(expected, text="不可寫入")
            )
        self.assertEqual(self.store.get_verse(40, 5, 3).text, "合成三。")
        self.assertEqual([item["status"] for item in self.mutator.history()], ["prepared"])


if __name__ == "__main__":
    unittest.main()
