from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import unittest
from unittest.mock import patch


SCRIPTS = (
    Path(__file__).parents[2]
    / "skills"
    / "retrieving-chinese-union-version-scripture"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture"
RUNTIME.mkdir(exist_ok=True)

from corpus_db import VerseRecord, initialize_database, insert_verses  # noqa: E402
from rag_metadata_sync import (  # noqa: E402
    RagMetadataSyncIneligible,
    RagMetadataSyncUnavailable,
    RagMetadataSynchronizer,
)
from rag_vector_lock import VectorFileLock  # noqa: E402


class RagMetadataSyncTests(unittest.TestCase):
    @staticmethod
    def structure_hash(*keys):
        digest = hashlib.sha256()
        for book_id, chapter, verse in keys:
            digest.update(f"{book_id}:{chapter}:{verse}\n".encode("ascii"))
        return digest.hexdigest()

    @staticmethod
    def identity_hash(*identities):
        return hashlib.sha256(json.dumps(
            sorted(identities), ensure_ascii=False, separators=(",", ":"),
        ).encode("utf-8")).hexdigest()

    def setUp(self):
        self.root = RUNTIME / "rag-metadata-sync"
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir()
        self.database = self.root / "cuv.sqlite3"
        self.vector = self.root / "rag-vectors.json"
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, (
                    VerseRecord(40, 5, 1, "合成一。", "new.pdf", 7, 100.0, True),
                    VerseRecord(40, 5, 2, "合成二。", "new.pdf", 7, 100.0, False),
                ))
                connection.executemany(
                    "INSERT INTO metadata(key, value) VALUES (?, ?)",
                    (
                        ("source_sha256:new.pdf", "source-digest"),
                        ("rag_index_state", "stale"),
                        ("rag_index_stale_at", "2026-08-24T00:00:00Z"),
                        ("rag_vector_item_count", "1"),
                        (
                            "rag_corpus_structure_sha256",
                            self.structure_hash((40, 5, 1), (40, 5, 2)),
                        ),
                        (
                            "rag_vector_identity_sha256",
                            self.identity_hash(("cuv:40:5", "cuv:40:5::0", 0)),
                        ),
                    ),
                )
        self.vector.write_text(json.dumps({"items": [self.vector_item()]}), encoding="utf-8")
        self.environ = {
            "RAG_VECTOR_STORE_BACKEND": "json",
            "RAG_VECTOR_STORE_PATH": str(self.vector),
        }

    def tearDown(self):
        if self.root.exists():
            shutil.rmtree(self.root)

    @staticmethod
    def vector_item():
        return {
            "doc_id": "cuv:40:5",
            "chunk_id": "cuv:40:5::0",
            "text": "5:1 合成一。\n5:2 合成二。",
            "section_path": "太5:1-2",
            "order": 0,
            "language": "zh",
            "embedding_model": "bge-large-zh",
            "namespace": "cool-bible-tutor:zh:bge-large-zh",
            "embedding": [0.25, -0.5, 0.75],
            "metadata": {
                "app_id": "cool-bible-tutor",
                "corpus": "cuv-private",
                "book_id": "40",
                "book_name": "馬太福音",
                "chapter": "5",
                "canonical_reference": "太5:1-2",
                "start_verse": "1",
                "end_verse": "2",
                "verified_all": "true",
                "unverified_count": "0",
                "source_files": "new.pdf",
                "source_pages": "7",
                "source_hashes": "new.pdf=source-digest",
            },
            "hash": "synthetic-content-hash",
        }

    def synchronizer(self, environ=None):
        return RagMetadataSynchronizer(
            self.database,
            environ=self.environ if environ is None else environ,
        )

    def read_vector_item(self):
        return json.loads(self.vector.read_text(encoding="utf-8"))["items"][0]

    def test_sync_derives_trust_metadata_without_changing_content_or_embeddings(self):
        before = self.read_vector_item()

        result = self.synchronizer().synchronize()

        after = self.read_vector_item()
        self.assertEqual(after["metadata"]["verified_all"], "false")
        self.assertEqual(after["metadata"]["unverified_count"], "1")
        self.assertEqual(after["text"], before["text"])
        self.assertEqual(after["embedding"], before["embedding"])
        self.assertEqual(after["hash"], before["hash"])
        self.assertEqual(result["targeted_items"], 1)
        self.assertEqual(result["changed_items"], 1)
        self.assertTrue(result["content_unchanged"])
        self.assertTrue(result["embeddings_unchanged"])
        backup = self.vector.with_name(result["backup_name"])
        self.assertTrue(backup.is_file())
        self.assertEqual(json.loads(backup.read_text(encoding="utf-8"))["items"][0], before)
        with closing(sqlite3.connect(self.database)) as connection:
            metadata = dict(connection.execute(
                "SELECT key, value FROM metadata WHERE key LIKE 'rag_%'"
            ))
        self.assertNotIn("rag_index_state", metadata)
        self.assertEqual(metadata["rag_metadata_sync_method"], "metadata_only_reuse_embeddings")

    def test_sync_rejects_changed_verse_text_without_touching_vector_or_stale_state(self):
        before = self.vector.read_bytes()
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "UPDATE verses SET text = '已修改。' WHERE book_id = 40 AND chapter = 5 AND verse = 2"
                )

        with self.assertRaisesRegex(RagMetadataSyncIneligible, "text or provenance"):
            self.synchronizer().synchronize()

        self.assertEqual(self.vector.read_bytes(), before)
        self.assertEqual(list(self.root.glob("rag-vectors.before-metadata-sync-*.json")), [])
        with closing(sqlite3.connect(self.database)) as connection:
            state = connection.execute(
                "SELECT value FROM metadata WHERE key = 'rag_index_state'"
            ).fetchone()[0]
        self.assertEqual(state, "stale")

    def test_sync_rejects_changed_source_hash(self):
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "UPDATE metadata SET value = 'different' WHERE key = 'source_sha256:new.pdf'"
                )

        with self.assertRaisesRegex(RagMetadataSyncIneligible, "text or provenance"):
            self.synchronizer().synchronize()

    def test_sync_rejects_inserted_verse_missing_from_existing_chunks(self):
        before = self.vector.read_bytes()
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, (
                    VerseRecord(40, 5, 3, "新增三。", "new.pdf", 7, 100.0, True),
                ))

        with self.assertRaisesRegex(RagMetadataSyncIneligible, "structure"):
            self.synchronizer().synchronize()

        self.assertEqual(self.vector.read_bytes(), before)
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute(
                "SELECT value FROM metadata WHERE key = 'rag_index_state'"
            ).fetchone()[0], "stale")

    def test_sync_rejects_vector_item_count_mismatch_or_missing_baseline(self):
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "UPDATE metadata SET value = '2' WHERE key = 'rag_vector_item_count'"
                )
        with self.assertRaisesRegex(RagMetadataSyncIneligible, "item count"):
            self.synchronizer().synchronize()

        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "DELETE FROM metadata WHERE key IN "
                    "('rag_vector_item_count', 'rag_corpus_structure_sha256', "
                    "'rag_vector_identity_sha256')"
                )
        with self.assertRaisesRegex(RagMetadataSyncIneligible, "full ingestion"):
            self.synchronizer().synchronize()

    def test_sync_requires_stale_state(self):
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "DELETE FROM metadata WHERE key IN ('rag_index_state', 'rag_index_stale_at')"
                )
        with self.assertRaisesRegex(RagMetadataSyncIneligible, "not marked stale"):
            self.synchronizer().synchronize()

    def test_sync_rejects_changed_chunk_identity(self):
        payload = json.loads(self.vector.read_text(encoding="utf-8"))
        payload["items"][0]["chunk_id"] = "cuv:40:5::999"
        self.vector.write_text(json.dumps(payload), encoding="utf-8")

        with self.assertRaisesRegex(RagMetadataSyncIneligible, "identity"):
            self.synchronizer().synchronize()

    def test_sync_refuses_when_project_json_writer_holds_lock(self):
        with VectorFileLock(self.vector):
            synchronizer = RagMetadataSynchronizer(
                self.database, environ=self.environ, lock_timeout=0.01,
            )
            with self.assertRaisesRegex(RagMetadataSyncUnavailable, "busy"):
                synchronizer.synchronize()

    def test_sync_detects_vector_change_after_backup_before_replace(self):
        original_copy = shutil.copy2

        def copy_then_change(source, destination):
            result = original_copy(source, destination)
            self.vector.write_bytes(self.vector.read_bytes() + b" ")
            return result

        with patch("rag_metadata_sync.shutil.copy2", side_effect=copy_then_change):
            with self.assertRaisesRegex(RagMetadataSyncIneligible, "changed during validation"):
                self.synchronizer().synchronize()

        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute(
                "SELECT value FROM metadata WHERE key = 'rag_index_state'"
            ).fetchone()[0], "stale")

    def test_post_write_failure_restores_original_vector_atomically(self):
        before = self.vector.read_bytes()
        payload = json.loads(before)
        with patch.object(
            RagMetadataSynchronizer,
            "_load_payload",
            side_effect=(payload, RagMetadataSyncIneligible("verify failure")),
        ):
            with self.assertRaisesRegex(RagMetadataSyncIneligible, "verify failure"):
                self.synchronizer().synchronize()
        self.assertEqual(self.vector.read_bytes(), before)

    def test_sync_rejects_unsupported_or_missing_vector_store(self):
        with self.assertRaisesRegex(RagMetadataSyncUnavailable, "JSON"):
            self.synchronizer({"RAG_VECTOR_STORE_BACKEND": "pgvector"}).synchronize()
        with self.assertRaisesRegex(RagMetadataSyncUnavailable, "not available"):
            self.synchronizer({
                "RAG_VECTOR_STORE_BACKEND": "json",
                "RAG_VECTOR_STORE_PATH": str(self.root / "missing.json"),
            }).synchronize()


if __name__ == "__main__":
    unittest.main()
