from contextlib import closing
import sqlite3
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[2] / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
sys.path.insert(0, str(SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture"
RUNTIME.mkdir(exist_ok=True)

from corpus_db import VerseRecord, initialize_database, insert_verses  # noqa: E402
from review_store import ReviewFilters, ReviewStore  # noqa: E402


class ReviewStoreReadTests(unittest.TestCase):
    def setUp(self):
        self.database = RUNTIME / "review-read.sqlite3"
        self.database.unlink(missing_ok=True)
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, (
                    VerseRecord(40, 5, 1, "合成一。", "new.pdf", 7, 99.0, True),
                    VerseRecord(40, 5, 3, "合成三。", "new.pdf", 7, 80.0, False),
                    VerseRecord(40, 5, 4, "合成四。", "new.pdf", 8, 99.0, False),
                ))

    def tearDown(self):
        self.database.unlink(missing_ok=True)

    def test_summary_and_gap_queue_derive_live_counts(self):
        store = ReviewStore(self.database)
        self.assertEqual(store.summary()["verse_count"], 3)
        self.assertEqual(store.summary()["gap_count"], 1)
        self.assertEqual(store.summary()["unverified_count"], 2)
        item = store.list_gaps(ReviewFilters(), limit=10)["items"][0]
        self.assertEqual(item["missing_references"], ["馬太福音 5:2"])
        self.assertEqual(item["previous"]["verse"], 1)
        self.assertEqual(item["next"]["verse"], 3)

    def test_unverified_queue_groups_by_exact_source_page(self):
        items = ReviewStore(self.database).list_unverified_pages(ReviewFilters(), limit=10)["items"]
        self.assertEqual([(item["source_page"], item["row_count"]) for item in items], [(7, 1), (8, 1)])
        self.assertEqual(items[0]["low_confidence_count"], 1)

    def test_empty_corpus_has_empty_live_queues(self):
        empty = RUNTIME / "review-empty.sqlite3"
        empty.unlink(missing_ok=True)
        self.addCleanup(empty.unlink, missing_ok=True)
        initialize_database(empty)
        store = ReviewStore(empty)
        self.assertEqual(store.summary(), {
            "verse_count": 0, "gap_count": 0, "unverified_count": 0,
        })
        self.assertEqual(store.list_gaps(ReviewFilters())["items"], [])
        self.assertEqual(store.list_unverified_pages(ReviewFilters())["items"], [])

    def test_invalid_filters_and_pagination_are_rejected(self):
        store = ReviewStore(self.database)
        invalid = (
            ReviewFilters(testament="both"),
            ReviewFilters(book_id=0),
            ReviewFilters(book_id=67),
            ReviewFilters(chapter=0),
            ReviewFilters(source_page=-1),
        )
        for filters in invalid:
            with self.subTest(filters=filters):
                with self.assertRaises(ValueError):
                    store.list_unverified_pages(filters)
        for offset, limit in ((-1, 10), (0, 0), (0, 101)):
            with self.subTest(offset=offset, limit=limit):
                with self.assertRaises(ValueError):
                    store.list_gaps(ReviewFilters(), offset=offset, limit=limit)

    def test_gap_pagination_is_stable_and_expands_multi_verse_intervals(self):
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, (
                    VerseRecord(40, 6, 1, "六一。", "new.pdf", 9, 99.0, True),
                    VerseRecord(40, 6, 3, "六三。", "new.pdf", 9, 99.0, True),
                    VerseRecord(40, 7, 1, "七一。", "new.pdf", 10, 99.0, True),
                    VerseRecord(40, 7, 4, "七四。", "new.pdf", 10, 99.0, True),
                ))
        store = ReviewStore(self.database)
        page = store.list_gaps(ReviewFilters(book_id=40), offset=2, limit=1)
        self.assertEqual(page["total"], 3)
        self.assertEqual(page["items"][0]["missing_references"], ["馬太福音 7:2", "馬太福音 7:3"])

    def test_testament_filter_keeps_only_the_selected_canon_partition(self):
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, (
                    VerseRecord(1, 1, 1, "舊一。", "old.pdf", 2, 99.0, True),
                    VerseRecord(1, 1, 3, "舊三。", "old.pdf", 2, 70.0, False),
                ))
        store = ReviewStore(self.database)
        old_gaps = store.list_gaps(ReviewFilters(testament="OT"))["items"]
        old_pages = store.list_unverified_pages(ReviewFilters(testament="OT"))["items"]
        self.assertEqual(old_gaps[0]["missing_references"], ["創世記 1:2"])
        self.assertEqual([(item["source_file"], item["source_page"]) for item in old_pages], [("old.pdf", 2)])

    def test_lookup_and_page_snapshots_include_verified_context_rows(self):
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, (
                    VerseRecord(40, 5, 5, "合成五。", "new.pdf", 7, 99.0, True),
                ))
        store = ReviewStore(self.database)
        snapshot = store.get_verse(40, 5, 5)
        self.assertEqual(snapshot.as_dict()["reference"], "馬太福音 5:5")
        self.assertEqual([row.verse for row in store.page_snapshots("new.pdf", 7)], [1, 3, 5])
        with self.assertRaises(LookupError):
            store.get_verse(40, 5, 2)


if __name__ == "__main__":
    unittest.main()
