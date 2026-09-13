from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import unittest


PLUGIN_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture" / "freeze-public-rag"
RUNTIME.mkdir(parents=True, exist_ok=True)

from freeze_public_rag_index import freeze_rag_index  # noqa: E402


class PublicRagIndexFreezerTests(unittest.TestCase):
    def setUp(self):
        self.source = RUNTIME / "vectors.json"
        self.output = RUNTIME / "index.sqlite3"
        self.corpus_manifest = RUNTIME / "corpus.json"
        self.model_manifest = RUNTIME / "model.json"
        self.corpus_manifest.write_text(json.dumps({
            "schema_version": 1,
            "database_sha256": "a" * 64,
            "corpus_structure_sha256": "b" * 64,
            "row_count": 31008,
        }), encoding="utf-8")
        self.model_manifest.write_text(json.dumps({
            "schema_version": 1,
            "model_id": "BAAI/bge-large-zh-v1.5",
            "revision": "c" * 40,
            "route": "bge-large-zh",
            "dimensions": 4,
            "files": {"config.json": "d" * 64},
        }), encoding="utf-8")

    def tearDown(self):
        for path in RUNTIME.iterdir():
            if path.is_file():
                path.unlink()

    @staticmethod
    def item(chunk_id, embedding=None, app_id="cool-bible-tutor"):
        return {
            "doc_id": "cuv:43:3",
            "chunk_id": chunk_id,
            "text": "3:16 神愛世人。",
            "section_path": "約3:16",
            "order": 0,
            "language": "zh",
            "embedding_model": "bge-large-zh",
            "namespace": "cool-bible-tutor:zh:bge-large-zh",
            "embedding": [0.25, -0.5, 0.75, 1.0] if embedding is None else embedding,
            "metadata": {
                "app_id": app_id,
                "book_id": "43",
                "canonical_reference": "約3:16",
                "source_path": "C:/private/authoring.pdf",
            },
            "hash": f"hash-{chunk_id}",
        }

    def write_source(self, items):
        self.source.write_text(
            json.dumps({"items": items}, ensure_ascii=False), encoding="utf-8"
        )

    def test_converter_filters_app_and_preserves_float32(self):
        self.write_source([
            self.item("cuv:43:3::1"),
            self.item("foreign::0", app_id="another-app"),
            self.item("cuv:43:3::0"),
        ])

        manifest = freeze_rag_index(
            self.source, self.output, self.corpus_manifest, self.model_manifest
        )

        self.assertEqual(manifest["item_count"], 2)
        self.assertEqual(manifest["dimensions"], 4)
        with closing(sqlite3.connect(self.output)) as connection:
            rows = connection.execute(
                "SELECT chunk_id, source_order, app_id, length(embedding), metadata_json "
                "FROM chunks ORDER BY chunk_id"
            ).fetchall()
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        self.assertEqual(
            [(row[0], row[1], row[2], row[3]) for row in rows],
            [
                ("cuv:43:3::0", 1, "cool-bible-tutor", 16),
                ("cuv:43:3::1", 0, "cool-bible-tutor", 16),
            ],
        )
        self.assertEqual(tables, {"index_metadata", "chunks"})
        self.assertNotIn("private", "".join(row[4] for row in rows))

    def test_converter_is_byte_deterministic(self):
        self.write_source([self.item("cuv:43:3::1"), self.item("cuv:43:3::0")])
        second = RUNTIME / "second.sqlite3"

        first_manifest = freeze_rag_index(
            self.source, self.output, self.corpus_manifest, self.model_manifest
        )
        second_manifest = freeze_rag_index(
            self.source, second, self.corpus_manifest, self.model_manifest
        )

        self.assertEqual(first_manifest["index_sha256"], second_manifest["index_sha256"])
        self.assertEqual(
            hashlib.sha256(self.output.read_bytes()).digest(),
            hashlib.sha256(second.read_bytes()).digest(),
        )

    def test_converter_rejects_duplicate_chunk_identity(self):
        self.write_source([self.item("duplicate"), self.item("duplicate")])
        with self.assertRaisesRegex(ValueError, "duplicate chunk identity"):
            freeze_rag_index(
                self.source, self.output, self.corpus_manifest, self.model_manifest
            )

    def test_converter_rejects_dimension_or_model_route_mismatch(self):
        self.write_source([self.item("bad-dimension", embedding=[1.0, 2.0])])
        with self.assertRaisesRegex(ValueError, "dimension"):
            freeze_rag_index(
                self.source, self.output, self.corpus_manifest, self.model_manifest
            )

        self.write_source([self.item("bad-route")])
        model = json.loads(self.model_manifest.read_text(encoding="utf-8"))
        model["route"] = "e5-large"
        self.model_manifest.write_text(json.dumps(model), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "model route"):
            freeze_rag_index(
                self.source, self.output, self.corpus_manifest, self.model_manifest
            )

    def test_production_mode_enforces_release_count_and_dimensions(self):
        self.write_source([self.item("too-few")])
        with self.assertRaisesRegex(ValueError, "production item count|1,024"):
            freeze_rag_index(
                self.source,
                self.output,
                self.corpus_manifest,
                self.model_manifest,
                production=True,
            )


if __name__ == "__main__":
    unittest.main()
