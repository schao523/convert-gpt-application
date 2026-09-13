from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import unittest


PLUGIN_ROOT = Path(__file__).parents[2]
INDEX = PLUGIN_ROOT / "assets" / "rag" / "cuv-rag-index.sqlite3"
INDEX_MANIFEST = PLUGIN_ROOT / "assets" / "rag" / "cuv-rag-runtime-manifest.json"
MODEL_MANIFEST = PLUGIN_ROOT / "assets" / "rag" / "bge-large-zh-v1.5-model-manifest.json"
CORPUS_MANIFEST = PLUGIN_ROOT / "assets" / "scripture" / "cuv-runtime-manifest.json"
APP_ID = "cool-bible-tutor"
NAMESPACE = "cool-bible-tutor:zh:bge-large-zh"

GOLDEN = {
    "神的愛與救恩": {
        "semantic_ids": [
            "cuv:49:2::9347", "cuv:46:16::9206", "cuv:62:4::9787",
            "cuv:19:116::5062", "cuv:19:116::5061", "cuv:19:86::4894",
            "cuv:62:4::9788", "cuv:19:85::4888", "cuv:19:106::5018",
            "cuv:32:2::7193", "cuv:19:85::4887", "cuv:19:136::5178",
            "cuv:19:40::4663", "cuv:14:6::3639", "cuv:19:18::4545",
            "cuv:62:3::9781", "cuv:19:118::5076", "cuv:19:36::4633",
            "cuv:23:12::5715", "cuv:19:33::4614",
        ],
        "references": [
            "弗2:4-8", "創1:1-5", "林前16:22-24", "創1:4-8", "約一4:10-14",
            "創1:7-11", "詩116:4-8", "詩116:1-5", "詩86:13-17", "約一4:13-17",
        ],
    },
    "饒恕得罪我們的人": {
        "semantic_ids": [
            "cuv:11:8::2905", "cuv:42:17::8189", "cuv:41:11::7870",
            "cuv:27:9::7016", "cuv:14:6::3633", "cuv:27:9::7017",
            "cuv:11:8::2900", "cuv:49:4::9369", "cuv:19:44::4676",
            "cuv:47:2::9217", "cuv:25:3::6506", "cuv:19:32::4605",
            "cuv:40:5::7416", "cuv:47:2::9216", "cuv:40:18::7575",
            "cuv:23:43::5911", "cuv:41:11::7869", "cuv:40:6::7424",
            "cuv:24:18::6190", "cuv:42:12::8130",
        ],
        "references": [
            "王上8:46-50", "創1:1-5", "路17:1-5", "創1:4-8", "可11:25-29",
            "創1:7-11", "但9:4-8", "代下6:22-26", "但9:7-11", "王上8:31-35",
        ],
    },
    "苦難中的盼望": {
        "semantic_ids": [
            "cuv:25:3::6499", "cuv:18:30::4359", "cuv:47:1::9209",
            "cuv:47:1::9208", "cuv:30:5::7157", "cuv:45:8::8992",
            "cuv:19:31::4599", "cuv:19:88::4897", "cuv:18:30::4358",
            "cuv:19:33::4614", "cuv:18:5::4159", "cuv:18:17::4261",
            "cuv:19:102::4963", "cuv:23:26::5792", "cuv:19:142::5199",
            "cuv:19:107::5021", "cuv:18:6::4169", "cuv:60:5::9742",
            "cuv:45:5::8963", "cuv:19:107::5024",
        ],
        "references": [
            "哀3:19-23", "創1:1-5", "伯30:25-29", "創1:4-8", "林後1:7-11",
            "創1:7-11", "林後1:4-8", "摩5:16-20", "羅8:22-26", "詩31:7-11",
        ],
    },
    "禱告與信心": {
        "semantic_ids": [
            "cuv:59:5::9709", "cuv:57:1::9574", "cuv:52:3::9464",
            "cuv:52:5::9480", "cuv:41:11::7869", "cuv:52:3::9465",
            "cuv:50:4::9417", "cuv:52:5::9477", "cuv:45:15::9050",
            "cuv:53:3::9490", "cuv:52:1::9453", "cuv:45:1::8928",
            "cuv:40:6::7422", "cuv:11:8::2899", "cuv:45:1::8929",
            "cuv:59:5::9710", "cuv:45:8::8993", "cuv:53:1::9483",
            "cuv:19:86::4891", "cuv:58:13::9674",
        ],
        "references": [
            "雅5:13-17", "創1:1-5", "門1:4-8", "創1:4-8", "帖前3:7-11",
            "創1:7-11", "帖前5:25-28", "可11:22-26", "帖前3:10-13", "腓4:4-8",
        ],
    },
    "照顧貧窮與弱勢": {
        "semantic_ids": [
            "cuv:2:22::686", "cuv:59:2::9687", "cuv:20:14::5361",
            "cuv:19:41::4664", "cuv:59:2::9686", "cuv:47:8::9253",
            "cuv:47:8::9252", "cuv:20:22::5436", "cuv:2:22::687",
            "cuv:20:29::5505", "cuv:54:5::9521", "cuv:18:31::4366",
            "cuv:20:13::5354", "cuv:43:12::8491", "cuv:20:14::5365",
            "cuv:47:9::9260", "cuv:5:15::1712", "cuv:18:24::4314",
            "cuv:59:2::9690", "cuv:20:13::5348",
        ],
        "references": [
            "出22:22-26", "創1:1-5", "雅2:4-8", "創1:4-8", "箴14:19-23",
            "創1:7-11", "詩41:1-5", "雅2:1-5", "林後8:10-14", "林後8:7-11",
        ],
    },
}


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class PublicRagIndexTests(unittest.TestCase):
    def test_index_is_manifest_bound_compact_and_structurally_valid(self):
        manifest = json.loads(INDEX_MANIFEST.read_text(encoding="utf-8"))
        corpus = json.loads(CORPUS_MANIFEST.read_text(encoding="utf-8"))
        model = json.loads(MODEL_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(sha256_file(INDEX), manifest["index_sha256"])
        self.assertLess(INDEX.stat().st_size, 100 * 1024 * 1024)
        self.assertEqual(manifest["item_count"], 9942)
        self.assertEqual(manifest["dimensions"], 1024)
        self.assertEqual(manifest["corpus_database_sha256"], corpus["database_sha256"])
        self.assertEqual(
            manifest["corpus_structure_sha256"], corpus["corpus_structure_sha256"]
        )
        self.assertEqual(manifest["model_revision"], model["revision"])
        self.assertEqual(manifest["model_files"], model["files"])

        uri = INDEX.resolve().as_uri() + "?mode=ro&immutable=1"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            metadata = dict(connection.execute("SELECT key, value FROM index_metadata"))
            count, app_count, dimensions = connection.execute(
                "SELECT COUNT(*), COUNT(DISTINCT app_id), MIN(length(embedding)) FROM chunks"
            ).fetchone()
            source_order = connection.execute(
                "SELECT MIN(source_order), MAX(source_order), COUNT(DISTINCT source_order) FROM chunks"
            ).fetchone()
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        self.assertEqual(tables, {"index_metadata", "chunks"})
        self.assertEqual((count, app_count, dimensions), (9942, 1, 4096))
        self.assertEqual(source_order, (0, 9941, 9942))
        self.assertEqual(metadata["vector_identity_sha256"], manifest["vector_identity_sha256"])
        self.assertEqual(integrity, "ok")

    def test_index_contains_no_private_paths_or_metadata_keys(self):
        uri = INDEX.resolve().as_uri() + "?mode=ro&immutable=1"
        forbidden_fragments = (
            "C:/Users/", "C:\\Users\\", "/Users/", "/home/", "OneDrive",
            "Dropbox (Personal)", "source_path", "review_history", "authoring-data",
        )
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            rows = connection.execute("SELECT text, metadata_json FROM chunks").fetchall()
            apps = connection.execute("SELECT DISTINCT app_id FROM chunks").fetchall()
        self.assertEqual(apps, [(APP_ID,)])
        serialized = "\n".join(value for row in rows for value in row if value)
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, serialized)

    def test_index_rejects_sql_writes(self):
        uri = INDEX.resolve().as_uri() + "?mode=ro&immutable=1"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("DELETE FROM chunks")

    def test_golden_contract_names_existing_chunks(self):
        expected_ids = {
            chunk_id
            for contract in GOLDEN.values()
            for chunk_id in contract["semantic_ids"]
        }
        placeholders = ",".join("?" for _ in expected_ids)
        uri = INDEX.resolve().as_uri() + "?mode=ro&immutable=1"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            actual_ids = {
                row[0] for row in connection.execute(
                    f"SELECT chunk_id FROM chunks WHERE chunk_id IN ({placeholders})",
                    sorted(expected_ids),
                )
            }
        self.assertEqual(actual_ids, expected_ids)
        self.assertTrue(all(len(contract["semantic_ids"]) == 20 for contract in GOLDEN.values()))
        self.assertTrue(all(len(contract["references"]) == 10 for contract in GOLDEN.values()))

    @unittest.skipUnless(
        os.environ.get("COOL_BIBLE_TUTOR_RELEASE_RAG_PARITY") == "1",
        "release-only gate requires the private authoring JSON and pinned local model",
    )
    def test_release_json_and_sqlite_rankings_match_goldens(self):
        rag_root = Path(os.environ["COOL_BIBLE_TUTOR_RAG_ROOT"]).resolve()
        json_path = Path(os.environ["RAG_VECTOR_STORE_PATH"]).resolve()
        sys.path.insert(0, str(rag_root))
        os.environ["RAG_EMBEDDING_BACKEND"] = "local"
        from rag_subsystem.config import DEFAULT_RETRIEVAL_CONFIG
        from rag_subsystem.embedding import embed_text
        from rag_subsystem.retrieval_data import retrieve_data
        from rag_subsystem.vector_store.json_file_store import JsonFileVectorStore
        from rag_subsystem.vector_store.sqlite_readonly_store import SqliteReadonlyVectorStore

        json_store = JsonFileVectorStore(str(json_path))
        sqlite_store = SqliteReadonlyVectorStore(str(INDEX))
        for query, contract in GOLDEN.items():
            embedding = embed_text(query, "bge-large-zh")
            json_ids = [
                chunk.chunk_id for chunk, _score in json_store.semantic_search(
                    embedding, NAMESPACE, 20, app_id=APP_ID
                )
            ]
            sqlite_ids = [
                chunk.chunk_id for chunk, _score in sqlite_store.semantic_search(
                    embedding, NAMESPACE, 20, app_id=APP_ID
                )
            ]
            self.assertEqual(json_ids, contract["semantic_ids"])
            self.assertEqual(sqlite_ids, contract["semantic_ids"])
            json_result = retrieve_data(
                query, 10, {"app_id": APP_ID}, DEFAULT_RETRIEVAL_CONFIG, json_store
            )
            sqlite_result = retrieve_data(
                query, 10, {"app_id": APP_ID}, DEFAULT_RETRIEVAL_CONFIG, sqlite_store
            )
            self.assertEqual(
                [item.chunk.metadata["canonical_reference"] for item in json_result.results],
                contract["references"],
            )
            self.assertEqual(
                [item.chunk.metadata["canonical_reference"] for item in sqlite_result.results],
                contract["references"],
            )


if __name__ == "__main__":
    unittest.main()
