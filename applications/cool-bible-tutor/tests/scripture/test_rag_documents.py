from contextlib import closing
import json
import sqlite3
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[2] / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
sys.path.insert(0, str(SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture"
RUNTIME.mkdir(exist_ok=True)

from corpus_db import VerseRecord, initialize_database, insert_verses  # noqa: E402
from rag_documents import build_rag_documents, read_corpus  # noqa: E402


class RagDocumentTests(unittest.TestCase):
    def record(self, book, chapter, verse, *, verified=False, page=1, source="synthetic.pdf"):
        return VerseRecord(book, chapter, verse, f"合成經文{verse}。", source, page, 99.0, verified)

    def test_windows_overlap_without_crossing_a_gap_or_chapter(self):
        records = tuple(self.record(40, 5, verse) for verse in (1, 2, 3, 4, 5, 6, 8, 9))
        records += (self.record(40, 6, 1),)

        documents = build_rag_documents(records, {"synthetic.pdf": "abc"})

        references = [
            block["metadata"]["canonical_reference"]
            for document in documents
            for block in document["blocks"]
        ]
        self.assertEqual(references, ["太5:1-5", "太5:4-6", "太5:8-9", "太6:1"])
        self.assertEqual([document["doc_id"] for document in documents], ["cuv:40:5", "cuv:40:6"])

    def test_metadata_is_deterministic_and_counts_unverified_rows(self):
        records = (
            self.record(40, 5, 3, verified=True, page=7, source="b.pdf"),
            self.record(40, 5, 4, verified=False, page=8, source="a.pdf"),
        )

        block = build_rag_documents(records, {"a.pdf": "aaa", "b.pdf": "bbb"})[0]["blocks"][0]

        self.assertEqual(block["metadata"], {
            "app_id": "cool-bible-tutor",
            "corpus": "cuv-private",
            "book_id": "40",
            "book_name": "馬太福音",
            "chapter": "5",
            "canonical_reference": "太5:3-4",
            "start_verse": "3",
            "end_verse": "4",
            "verified_all": "false",
            "unverified_count": "1",
            "source_files": "a.pdf,b.pdf",
            "source_pages": "7,8",
            "source_hashes": "a.pdf=aaa;b.pdf=bbb",
        })
        self.assertEqual(block["section_path"], "太5:3-4")
        self.assertEqual(block["text"], "5:3 合成經文3。\n5:4 合成經文4。")
        self.assertNotIn("D:\\", json.dumps(block, ensure_ascii=False))

    def test_rejects_invalid_window_settings_book_ids_and_missing_hashes(self):
        record = self.record(40, 5, 1)
        for window_size, overlap in ((0, 0), (5, -1), (5, 5)):
            with self.subTest(window_size=window_size, overlap=overlap):
                with self.assertRaises(ValueError):
                    build_rag_documents((record,), {"synthetic.pdf": "abc"}, window_size, overlap)
        with self.assertRaisesRegex(ValueError, "unknown book id"):
            build_rag_documents((self.record(67, 1, 1),), {"synthetic.pdf": "abc"})
        with self.assertRaisesRegex(ValueError, "source hash"):
            build_rag_documents((record,), {})
        with self.assertRaisesRegex(ValueError, "synthetic.pdf"):
            build_rag_documents((record,), {"other.pdf": "abc"})

    def test_read_corpus_filters_rows_and_returns_source_hashes(self):
        database = RUNTIME / "rag-documents.sqlite3"
        database.unlink(missing_ok=True)
        self.addCleanup(database.unlink, missing_ok=True)
        initialize_database(database)
        with closing(sqlite3.connect(database)) as connection:
            with connection:
                insert_verses(connection, (self.record(40, 5, 1), self.record(40, 6, 1)))
                connection.execute(
                    "INSERT INTO metadata(key, value) VALUES (?, ?)",
                    ("source_sha256:synthetic.pdf", "abc"),
                )
            hashes, records = read_corpus(connection, book_id=40, chapter=5)

        self.assertEqual(hashes, {"synthetic.pdf": "abc"})
        self.assertEqual([(record.chapter, record.verse) for record in records], [(5, 1)])

    def test_read_corpus_rejects_chapter_without_book(self):
        with closing(sqlite3.connect(":memory:")) as connection:
            with self.assertRaisesRegex(ValueError, "chapter requires book"):
                read_corpus(connection, chapter=5)


if __name__ == "__main__":
    unittest.main()
