from __future__ import annotations

from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from obvious_one_plugin_framework.index_reuse import (
    IndexReuseError,
    check_index_reuse,
    derive_index,
)


class IndexReuseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source_index = self.root / "source.sqlite3"
        self.source_manifest = self.root / "source.json"
        self.target_manifest = self.root / "target.json"
        self._create_index()
        self._write_manifest(self.source_manifest, "plugin-alpha", "plugin-alpha:docs")
        self._write_manifest(self.target_manifest, "plugin-beta", "plugin-beta:docs")

    def _create_index(self) -> None:
        connection = sqlite3.connect(self.source_index)
        connection.executescript("""
            CREATE TABLE chunks(
                chunk_id TEXT PRIMARY KEY,
                app_id TEXT NOT NULL,
                namespace TEXT NOT NULL,
                text TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                embedding BLOB NOT NULL,
                metadata_json TEXT NOT NULL
            );
            CREATE TABLE index_metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        rows = [
            ("doc::0", "first text", bytes(range(8))),
            ("doc::1", "second text", bytes(range(8, 16))),
        ]
        for chunk_id, text, vector in rows:
            connection.execute(
                "INSERT INTO chunks VALUES (?,?,?,?,?,?,?)",
                (chunk_id, "plugin-alpha", "plugin-alpha:docs", text,
                 sha256(text.encode()).hexdigest(), vector,
                 json.dumps({"app_id": "plugin-alpha", "namespace": "plugin-alpha:docs"})),
            )
        connection.executemany(
            "INSERT INTO index_metadata VALUES (?,?)",
            (("app_id", "plugin-alpha"), ("namespace", "plugin-alpha:docs"),
             ("vector_identity_sha256", "old-identity")),
        )
        connection.commit()
        connection.close()

    def _manifest(self, app_id: str, namespace: str) -> dict[str, object]:
        texts = ["first text", "second text"]
        return {
            "schema_version": 1,
            "app_id": app_id,
            "namespace": namespace,
            "source_files": {"source.pdf": "1" * 64},
            "corpus_structure_sha256": "2" * 64,
            "chunks": [
                {"chunk_id": f"doc::{index}", "order": index,
                 "text_sha256": sha256(text.encode()).hexdigest(),
                 "content_hash": sha256(text.encode()).hexdigest()}
                for index, text in enumerate(texts)
            ],
            "chunker": {"id": "paragraph-v1", "config_sha256": "3" * 64},
            "model": {"id": "example/model", "revision": "revision-1",
                      "dimensions": 2, "normalize": true_value()},
            "vector": {"schema": "sqlite-chunks-v1", "serialization": "float32-le"}
        }

    def _write_manifest(self, path: Path, app_id: str, namespace: str) -> None:
        path.write_text(json.dumps(self._manifest(app_id, namespace)), encoding="utf-8")

    def test_identical_embedding_inputs_are_eligible(self) -> None:
        report = check_index_reuse(self.source_manifest, self.target_manifest, self.source_index)
        self.assertTrue(report.eligible)
        self.assertEqual(report.mismatches, ())

    def test_text_or_model_change_requires_reembedding(self) -> None:
        target = self._manifest("plugin-beta", "plugin-beta:docs")
        target["chunks"][0]["text_sha256"] = "f" * 64
        target["model"]["revision"] = "revision-2"
        self.target_manifest.write_text(json.dumps(target), encoding="utf-8")
        report = check_index_reuse(self.source_manifest, self.target_manifest, self.source_index)
        self.assertFalse(report.eligible)
        self.assertEqual(report.mismatches, ("chunks", "model.revision"))

    def test_derivation_rebinds_identity_but_preserves_vector_blobs(self) -> None:
        before = sha256(self.source_index.read_bytes()).hexdigest()
        destination = self.root / "beta.sqlite3"
        record = derive_index(
            self.source_index, destination, self.source_manifest, self.target_manifest
        )
        self.assertEqual(self._vectors(self.source_index), self._vectors(destination))
        with closing(sqlite3.connect(destination)) as connection:
            self.assertEqual(
                {row[0] for row in connection.execute("SELECT DISTINCT app_id FROM chunks")},
                {"plugin-beta"},
            )
            self.assertEqual(
                {row[0] for row in connection.execute("SELECT DISTINCT namespace FROM chunks")},
                {"plugin-beta:docs"},
            )
            metadata_text = "\n".join(row[0] for row in connection.execute("SELECT metadata_json FROM chunks"))
            self.assertNotIn("plugin-alpha", metadata_text)
        self.assertEqual(sha256(self.source_index.read_bytes()).hexdigest(), before)
        self.assertNotEqual(record.sha256, before)
        self.assertEqual(record.app_id, "plugin-beta")

    def test_ineligible_derivation_leaves_no_destination(self) -> None:
        target = self._manifest("plugin-beta", "plugin-beta:docs")
        target["model"]["dimensions"] = 3
        self.target_manifest.write_text(json.dumps(target), encoding="utf-8")
        destination = self.root / "refused.sqlite3"
        with self.assertRaisesRegex(IndexReuseError, "reembedding_required"):
            derive_index(self.source_index, destination, self.source_manifest, self.target_manifest)
        self.assertFalse(destination.exists())

    @staticmethod
    def _vectors(path: Path) -> list[bytes]:
        with closing(sqlite3.connect(path)) as connection:
            return [row[0] for row in connection.execute("SELECT embedding FROM chunks ORDER BY chunk_id")]


def true_value() -> bool:
    return True


if __name__ == "__main__":
    unittest.main()
