from contextlib import closing
import hashlib
import json
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
from review_sources import SourceRegistry, SourceValidationError  # noqa: E402


class SourceRegistryTests(unittest.TestCase):
    def setUp(self):
        self.root = RUNTIME / "review-sources"
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir()
        self.database = self.root / "cuv.sqlite3"
        initialize_database(self.database)
        self.connection = sqlite3.connect(self.database)
        with self.connection:
            insert_verses(self.connection, (
                VerseRecord(40, 5, 1, "合成。", "Bible-new.pdf", 1, 99.0, True),
            ))
        self.source = self.root / "Bible-new.pdf"
        self.source.write_bytes(b"%PDF-1.4 synthetic")

    def tearDown(self):
        self.connection.close()
        if self.root.exists():
            shutil.rmtree(self.root)

    def register_hash(self, source=None, digest=None):
        source = source or self.source
        digest = digest or hashlib.sha256(source.read_bytes()).hexdigest()
        with self.connection:
            self.connection.execute(
                "INSERT OR REPLACE INTO metadata(key,value) VALUES (?,?)",
                (f"source_sha256:{source.name}", digest),
            )

    def test_only_hash_matching_database_sources_receive_opaque_ids(self):
        self.register_hash()
        registry = SourceRegistry.from_database(self.connection, (self.source,))
        public = registry.public_sources()[0]
        self.assertEqual(set(public), {"id", "filename", "size"})
        self.assertNotIn(str(self.root), json.dumps(public))
        result = registry.read_slice(public["id"], "bytes=5-9")
        self.assertEqual(result.status, 206)
        self.assertEqual(result.content, b"1.4 s")

    def test_hash_mismatch_is_rejected(self):
        self.register_hash(digest="0" * 64)
        with self.assertRaises(SourceValidationError):
            SourceRegistry.from_database(self.connection, (self.source,))

    def test_full_open_ended_suffix_and_unsatisfiable_ranges(self):
        self.register_hash()
        registry = SourceRegistry.from_database(self.connection, (self.source,))
        source_id = registry.public_sources()[0]["id"]
        full = registry.read_slice(source_id)
        self.assertEqual((full.status, full.content), (200, b"%PDF-1.4 synthetic"))
        self.assertEqual(registry.read_slice(source_id, "bytes=5-").content, b"1.4 synthetic")
        self.assertEqual(registry.read_slice(source_id, "bytes=-4").content, b"etic")
        unsatisfiable = registry.read_slice(source_id, "bytes=999-1000")
        self.assertEqual((unsatisfiable.status, unsatisfiable.total, unsatisfiable.content), (416, 18, b""))

    def test_multiple_and_malformed_ranges_are_rejected(self):
        self.register_hash()
        registry = SourceRegistry.from_database(self.connection, (self.source,))
        source_id = registry.public_sources()[0]["id"]
        for header in ("bytes=0-1,3-4", "bytes=word", "items=0-1", "bytes=-"):
            with self.subTest(header=header):
                with self.assertRaises(SourceValidationError):
                    registry.read_slice(source_id, header)

    def test_duplicate_basenames_are_rejected(self):
        self.register_hash()
        alternate_dir = self.root / "alternate"
        alternate_dir.mkdir()
        alternate = alternate_dir / self.source.name
        alternate.write_bytes(self.source.read_bytes())
        with self.assertRaises(SourceValidationError):
            SourceRegistry.from_database(self.connection, (self.source, alternate))

    def test_missing_corpus_source_and_unknown_opaque_id_are_rejected(self):
        self.register_hash()
        with self.assertRaises(SourceValidationError):
            SourceRegistry.from_database(self.connection, ())
        registry = SourceRegistry.from_database(self.connection, (self.source,))
        with self.assertRaises(SourceValidationError):
            registry.get("../../Bible-new.pdf")

    def test_url_metacharacters_remain_only_in_public_metadata_not_source_ids(self):
        unusual = self.root / "Bible #+%.pdf"
        unusual.write_bytes(b"%PDF unusual")
        with self.connection:
            self.connection.execute(
                "UPDATE verses SET source_file=?", (unusual.name,)
            )
        self.register_hash(unusual)
        registry = SourceRegistry.from_database(self.connection, (unusual,))
        public = registry.public_sources()[0]
        self.assertEqual(public["filename"], unusual.name)
        self.assertNotIn("#", public["id"])
        self.assertNotIn("%", public["id"])
        self.assertEqual(registry.get(public["id"]).path, unusual.resolve())


if __name__ == "__main__":
    unittest.main()
