import contextlib
from contextlib import closing
import io
import json
import os
import shutil
import sqlite3
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPTS = Path(__file__).parents[2] / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
sys.path.insert(0, str(SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture" / "ingest-rag"
RUNTIME.mkdir(parents=True, exist_ok=True)

from corpus_db import VerseRecord, initialize_database, insert_verses  # noqa: E402
from ingest_bible_rag import ingest_database, main  # noqa: E402
from rag_runtime import AdapterRuntimeError  # noqa: E402
from rag_vector_lock import VectorFileBusyError, VectorFileLock  # noqa: E402


class IngestBibleRagTests(unittest.TestCase):
    def setUp(self):
        self.data_dir = RUNTIME / "corpus"
        self.data_dir.mkdir(exist_ok=True)
        self.database = self.data_dir / "cuv.sqlite3"
        self.database.unlink(missing_ok=True)
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, (
                    VerseRecord(40, 5, 3, "合成甲。", "synthetic.pdf", 7, 99.0, True),
                    VerseRecord(40, 5, 4, "合成乙。", "synthetic.pdf", 8, 75.0, False),
                    VerseRecord(40, 6, 1, "合成丙。", "synthetic.pdf", 9, 99.0, True),
                ))
                connection.execute(
                    "INSERT INTO metadata(key, value) VALUES (?, ?)",
                    ("source_sha256:synthetic.pdf", "abc"),
                )

    def tearDown(self):
        if self.data_dir.exists():
            shutil.rmtree(self.data_dir)

    def mark_stale(self):
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "INSERT OR REPLACE INTO metadata(key,value) VALUES ('rag_index_state','stale')"
                )
                connection.execute(
                    "INSERT OR REPLACE INTO metadata(key,value) "
                    "VALUES ('rag_index_stale_at','2026-08-22T00:00:00Z')"
                )

    def metadata(self, key):
        with closing(sqlite3.connect(self.database)) as connection:
            row = connection.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
        return None if row is None else row[0]

    @staticmethod
    def api(process_files=None):
        return SimpleNamespace(
            ProcessConfig=lambda **values: values,
            process_files=process_files or (lambda documents, config: []),
        )

    def call_main(self, *arguments, loader=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        selected_loader = loader or (lambda: self.api())
        with patch.dict(os.environ, {}, clear=True):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = main(list(arguments), rag_api_loader=selected_loader)
        return code, json.loads(stdout.getvalue()), stderr.getvalue()

    def test_ingestion_uses_fixed_app_id_and_process_configuration(self):
        seen = {}

        def process_files(documents, config):
            seen.update(documents=documents, config=config)
            return [
                SimpleNamespace(
                    doc_id="cuv:40:5",
                    inserted=1,
                    skipped_too_short_count=2,
                    skipped_boilerplate_count=3,
                    skipped_near_dup_count=4,
                )
            ]

        with patch.dict(os.environ, {"RAG_VECTOR_STORE_BACKEND": "in_memory"}, clear=True):
            payload = ingest_database(self.database, self.api(process_files), book_id=40, chapter=5)

        self.assertEqual(seen["documents"][0]["doc_id"], "cuv:40:5")
        self.assertEqual(seen["documents"][0]["blocks"][0]["metadata"]["app_id"], "cool-bible-tutor")
        self.assertEqual(seen["config"], {"min_chunk_length": 1, "section_token_threshold": 10000})
        self.assertEqual(payload, {
            "status": "ok",
            "app_id": "cool-bible-tutor",
            "documents": 1,
            "inserted_chunks": 1,
            "skipped": {"too_short": 2, "boilerplate": 3, "near_duplicate": 4},
            "source_hashes": {"synthetic.pdf": "abc"},
            "vector_backend": "in_memory",
        })

    def test_json_ingestion_holds_the_project_vector_lock(self):
        vector = RUNTIME / "lock-test-vectors.json"
        self.addCleanup(lambda: Path(str(vector) + ".lock").unlink(missing_ok=True))
        saw_busy = []

        def process_files(documents, config):
            try:
                with VectorFileLock(vector, timeout=0.01):
                    pass
            except VectorFileBusyError:
                saw_busy.append(True)
            return []

        with patch.dict(os.environ, {
            "RAG_VECTOR_STORE_BACKEND": "json",
            "RAG_VECTOR_STORE_PATH": str(vector),
        }, clear=True):
            ingest_database(self.database, self.api(process_files), book_id=40, chapter=5)

        self.assertEqual(saw_busy, [True])

    def test_json_full_ingestion_records_actual_vector_count_not_insert_result(self):
        vector = RUNTIME / "actual-count-vectors.json"
        self.addCleanup(vector.unlink, missing_ok=True)
        self.addCleanup(lambda: Path(str(vector) + ".lock").unlink(missing_ok=True))

        def process_files(documents, config):
            vector.write_text(json.dumps({"items": [
                {"doc_id": "cuv:40:5", "chunk_id": "cuv:40:5::0", "order": 0,
                 "metadata": {"app_id": "cool-bible-tutor"}},
                {"doc_id": "cuv:40:6", "chunk_id": "cuv:40:6::1", "order": 1,
                 "metadata": {"app_id": "cool-bible-tutor"}},
                {"doc_id": "other", "chunk_id": "other::0", "order": 0,
                 "metadata": {"app_id": "another-app"}},
            ]}), encoding="utf-8")
            return [SimpleNamespace(
                doc_id="cuv:40:5", inserted=0, skipped_too_short_count=0,
                skipped_boilerplate_count=0, skipped_near_dup_count=0,
            )]

        with patch.dict(os.environ, {
            "RAG_VECTOR_STORE_BACKEND": "json",
            "RAG_VECTOR_STORE_PATH": str(vector),
        }, clear=True):
            payload = ingest_database(self.database, self.api(process_files))

        self.assertEqual(payload["inserted_chunks"], 0)
        self.assertEqual(self.metadata("rag_vector_item_count"), "2")
        self.assertIsNotNone(self.metadata("rag_vector_identity_sha256"))

    def test_json_full_ingestion_keeps_stale_when_no_cuv_vectors_are_produced(self):
        vector = RUNTIME / "empty-vectors.json"
        self.addCleanup(vector.unlink, missing_ok=True)
        self.addCleanup(lambda: Path(str(vector) + ".lock").unlink(missing_ok=True))
        self.mark_stale()

        def process_files(documents, config):
            vector.write_text('{"items": []}', encoding="utf-8")
            return []

        with patch.dict(os.environ, {
            "RAG_VECTOR_STORE_BACKEND": "json",
            "RAG_VECTOR_STORE_PATH": str(vector),
        }, clear=True):
            with self.assertRaisesRegex(AdapterRuntimeError, "no CUV chunks"):
                ingest_database(self.database, self.api(process_files))

        self.assertEqual(self.metadata("rag_index_state"), "stale")

    def test_full_ingestion_keeps_stale_when_corpus_changes_during_processing(self):
        def process_files(documents, config):
            with closing(sqlite3.connect(self.database)) as connection:
                with connection:
                    connection.execute(
                        "UPDATE verses SET verified = 1 - verified "
                        "WHERE book_id = 40 AND chapter = 5 AND verse = 4"
                    )
            return []

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(AdapterRuntimeError, "changed during RAG ingestion"):
                ingest_database(self.database, self.api(process_files))

        self.assertEqual(self.metadata("rag_index_state"), "stale")

    def test_cli_returns_json_exit_two_for_missing_database(self):
        missing = RUNTIME / "missing"
        code, payload, stderr = self.call_main("--data-dir", str(missing))
        self.assertEqual(code, 2)
        self.assertEqual(payload["error"]["code"], "missing_corpus")
        self.assertEqual(stderr, "")

    def test_cli_requires_book_when_chapter_is_selected(self):
        code, payload, _ = self.call_main(
            "--data-dir", str(self.data_dir), "--chapter", "5"
        )
        self.assertEqual(code, 2)
        self.assertEqual(payload["error"]["code"], "invalid_request")

    def test_cli_resolves_book_and_emits_success_as_json(self):
        seen = {}

        def process_files(documents, config):
            seen["doc_ids"] = [document["doc_id"] for document in documents]
            return [SimpleNamespace(
                doc_id="cuv:40:5", inserted=1, skipped_too_short_count=0,
                skipped_boilerplate_count=0, skipped_near_dup_count=0,
            )]

        code, payload, stderr = self.call_main(
            "--data-dir", str(self.data_dir), "--book", "馬太福音", "--chapter", "5",
            loader=lambda: self.api(process_files),
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["documents"], 1)
        self.assertEqual(seen["doc_ids"], ["cuv:40:5"])
        self.assertEqual(stderr, "")
        self.assertNotIn("合成甲", json.dumps(payload, ensure_ascii=False))

    def test_cli_maps_external_rag_failure_to_exit_four(self):
        def fail_process_files(documents, config):
            raise RuntimeError("vector store offline")

        code, payload, _ = self.call_main(
            "--data-dir", str(self.data_dir),
            loader=lambda: self.api(fail_process_files),
        )
        self.assertEqual(code, 4)
        self.assertEqual(payload["error"]["code"], "rag_unavailable")

    def test_only_successful_full_ingestion_clears_stale_marker(self):
        self.mark_stale()
        with patch.dict(os.environ, {}, clear=True):
            ingest_database(self.database, self.api(), book_id=40, chapter=5)
            self.assertEqual(self.metadata("rag_index_state"), "stale")
            ingest_database(self.database, self.api())
        self.assertIsNone(self.metadata("rag_index_state"))
        self.assertIsNone(self.metadata("rag_index_stale_at"))
        self.assertIsNone(self.metadata("rag_vector_item_count"))
        self.assertIsNone(self.metadata("rag_corpus_structure_sha256"))

    def test_external_failure_leaves_both_stale_markers_unchanged(self):
        self.mark_stale()

        def fail_process_files(documents, config):
            raise RuntimeError("vector store offline")

        code, payload, _ = self.call_main(
            "--data-dir", str(self.data_dir), loader=lambda: self.api(fail_process_files),
        )
        self.assertEqual((code, payload["error"]["code"]), (4, "rag_unavailable"))
        self.assertEqual(self.metadata("rag_index_state"), "stale")
        self.assertEqual(self.metadata("rag_index_stale_at"), "2026-08-22T00:00:00Z")

    def test_cli_maps_loader_runtime_failure_to_exit_four(self):
        code, payload, _ = self.call_main(
            "--data-dir", str(self.data_dir),
            loader=lambda: (_ for _ in ()).throw(AdapterRuntimeError("missing runtime")),
        )
        self.assertEqual(code, 4)
        self.assertEqual(payload["error"]["code"], "rag_unavailable")


if __name__ == "__main__":
    unittest.main()
