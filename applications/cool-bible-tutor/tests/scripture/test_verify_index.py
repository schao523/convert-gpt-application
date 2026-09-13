from contextlib import closing
import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).parents[2] / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
sys.path.insert(0, str(SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture" / "verify-index"
RUNTIME.mkdir(parents=True, exist_ok=True)

from corpus_db import VerseRecord, initialize_database, insert_verses  # noqa: E402
from verify_cuv_index import (  # noqa: E402
    ApprovedGapManifest,
    calculate_corpus_structure_sha256,
    resolve_verification_sources,
    sha256_file,
    verify_database,
)


class CorpusVerificationTests(unittest.TestCase):
    def setUp(self):
        self.database = RUNTIME / "verify.sqlite3"
        self.database.unlink(missing_ok=True)

    def tearDown(self):
        self.database.unlink(missing_ok=True)
        for path in RUNTIME.glob("*.pdf"):
            path.unlink()

    def create(self, records, mode="fixture"):
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, records)
                connection.execute(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES ('corpus_mode', ?)",
                    (mode,),
                )

    def codes(self, report):
        return {issue.code for issue in report.issues}

    def approved_manifest(self, gaps, row_count):
        return ApprovedGapManifest(
            source_sha256={},
            database_sha256=sha256_file(self.database),
            corpus_structure_sha256=calculate_corpus_structure_sha256(self.database),
            row_count=row_count,
            gaps=tuple(gaps),
        )

    def test_exact_manifest_gap_is_attested_not_warned(self):
        records = [
            VerseRecord(
                book_id, 1, verse, f"第{book_id}卷第{verse}節。",
                "fixture.pdf", book_id, 99.0, True,
            )
            for book_id in range(1, 67)
            for verse in ((1, 3) if book_id == 1 else (1,))
        ]
        self.create(records, mode="production_candidate")

        report = verify_database(
            self.database, [], self.approved_manifest(["1 1:2"], row_count=67)
        )

        self.assertEqual(report.approved_source_gaps, ("1 1:2",))
        self.assertNotIn("verse_gap", self.codes(report))
        self.assertTrue(report.production_ready)

    def test_changed_or_extra_gap_remains_a_warning(self):
        records = [
            VerseRecord(
                book_id, 1, verse, f"第{book_id}卷第{verse}節。",
                "fixture.pdf", book_id, 99.0, True,
            )
            for book_id in range(1, 67)
            for verse in ((1, 3) if book_id == 1 else (1,))
        ]
        self.create(records, mode="production_candidate")
        manifest = self.approved_manifest(["1 1:2"], row_count=67)
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, [
                    VerseRecord(1, 2, 1, "第二章第一節。", "fixture.pdf", 1, 99.0, True),
                    VerseRecord(1, 2, 3, "第二章第三節。", "fixture.pdf", 1, 99.0, True),
                ])

        report = verify_database(self.database, [], manifest)

        self.assertEqual(report.approved_source_gaps, ())
        self.assertIn("verse_gap", self.codes(report))
        self.assertFalse(report.production_ready)

    def test_fixture_is_clean_but_never_production_ready(self):
        self.create([VerseRecord(40, 1, 1, "合成文字。", "fixture.pdf", 1, 99.0, True)])
        report = verify_database(self.database, [])
        self.assertEqual(self.codes(report), {"fixture_mode"})
        self.assertEqual(report.exit_status, 1)
        self.assertFalse(report.production_ready)

    def test_structural_and_confidence_issue_codes(self):
        self.create([
            VerseRecord(40, 1, 1, "", "fixture.pdf", 0, 101.0, False),
            VerseRecord(40, 1, 3, "合成。", "fixture.pdf", 2, 20.0, False),
        ], mode="production_candidate")
        report = verify_database(self.database, [])
        self.assertTrue({
            "empty_text", "invalid_source_page", "invalid_confidence", "unverified",
            "low_confidence", "verse_gap", "missing_book",
        }.issubset(self.codes(report)))
        self.assertEqual(report.exit_status, 2)

    def test_source_hash_mismatch_is_error(self):
        source = RUNTIME / "source.pdf"
        source.write_bytes(b"current-source")
        self.create([VerseRecord(1, 1, 1, "合成。", source.name, 1, 99.0, True)])
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                    ("source_sha256:" + source.name, "0" * 64),
                )
        report = verify_database(self.database, [source])
        self.assertIn("source_hash_mismatch", self.codes(report))
        self.assertEqual(report.exit_status, 2)

    def test_complete_synthetic_structure_can_be_production_ready(self):
        self.create([
            VerseRecord(book_id, 1, 1, f"第{book_id}卷合成文字。", "fixture.pdf", book_id, 99.0, True)
            for book_id in range(1, 67)
        ], mode="production_candidate")
        report = verify_database(self.database, [])
        self.assertEqual(report.issues, ())
        self.assertEqual(report.exit_status, 0)
        self.assertTrue(report.production_ready)

    def test_empty_source_list_uses_bundled_pair(self):
        old_source = RUNTIME / "old.pdf"
        new_source = RUNTIME / "new.pdf"
        with patch(
            "verify_cuv_index.resolve_bundled_sources",
            return_value=(old_source, new_source),
        ):
            self.assertEqual(
                resolve_verification_sources([]),
                (old_source, new_source),
            )

    def test_explicit_verification_sources_are_preserved(self):
        source = RUNTIME / "explicit.pdf"
        with patch("verify_cuv_index.resolve_bundled_sources") as bundled:
            self.assertEqual(resolve_verification_sources([source]), (source.resolve(),))
        bundled.assert_not_called()


if __name__ == "__main__":
    unittest.main()
