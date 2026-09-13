from contextlib import closing
import io
import json
import sqlite3
import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).parents[2]
SKILL_SCRIPTS = (
    PLUGIN_ROOT / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
)
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(SKILL_SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture" / "freeze-public-corpus"
RUNTIME.mkdir(parents=True, exist_ok=True)

from corpus_db import VerseRecord, initialize_database, insert_verses  # noqa: E402
from freeze_public_corpus import freeze_public_corpus, main as freeze_main  # noqa: E402
from verify_cuv_index import (  # noqa: E402
    calculate_corpus_structure_sha256,
    sha256_file,
)


class PublicCorpusFreezerTests(unittest.TestCase):
    def setUp(self):
        self.source = RUNTIME / "authoring.sqlite3"
        self.destination = RUNTIME / "cuv.sqlite3"
        self.gap_manifest = RUNTIME / "approved-gaps.json"
        for path in (self.source, self.destination, self.gap_manifest):
            path.unlink(missing_ok=True)

    def tearDown(self):
        for path in RUNTIME.iterdir():
            if path.is_file():
                path.unlink()

    def create_source(self):
        initialize_database(self.source)
        records = [
            VerseRecord(
                book_id, 1, verse, f"第{book_id}卷第{verse}節。",
                "fixture.pdf", book_id, 99.0, True,
            )
            for book_id in range(1, 67)
            for verse in ((1, 3) if book_id == 1 else (1,))
        ]
        with closing(sqlite3.connect(self.source)) as connection:
            with connection:
                insert_verses(connection, records)
                connection.executemany(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                    (
                        ("corpus_mode", "production_candidate"),
                        ("rag_private_path", "C:/private/vector.json"),
                        ("source_sha256:Bible 測試.pdf", "a" * 64),
                    ),
                )
        self.write_manifest(database_sha256=sha256_file(self.source))

    def write_manifest(self, database_sha256):
        payload = {
            "schema_version": 1,
            "attestation": "synthetic test attestation",
            "source_sha256": {"Bible 測試.pdf": "a" * 64},
            "authoring_database_sha256": database_sha256,
            "database_sha256": database_sha256,
            "corpus_structure_sha256": calculate_corpus_structure_sha256(self.source),
            "row_count": 67,
            "gaps": ["1 1:2"],
        }
        self.gap_manifest.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def test_freezer_copies_only_public_tables_and_metadata(self):
        self.create_source()

        result = freeze_public_corpus(
            self.source, self.destination, self.gap_manifest
        )

        with closing(sqlite3.connect(self.destination)) as connection:
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            metadata = dict(connection.execute("SELECT key, value FROM metadata"))
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        self.assertEqual(tables, {"metadata", "verses"})
        self.assertNotIn("rag_private_path", metadata)
        self.assertEqual(metadata["corpus_mode"], "public_runtime")
        self.assertEqual(result["row_count"], 67)
        self.assertEqual(integrity, "ok")
        finalized = json.loads(self.gap_manifest.read_text(encoding="utf-8"))
        self.assertEqual(finalized["database_sha256"], sha256_file(self.destination))

    def test_freezer_rejects_non_production_ready_input(self):
        self.create_source()
        self.write_manifest(database_sha256="0" * 64)

        with self.assertRaisesRegex(ValueError, "production-ready"):
            freeze_public_corpus(self.source, self.destination, self.gap_manifest)

        self.assertFalse(self.destination.exists())

    def test_freezer_rejects_private_authoring_tables(self):
        self.create_source()
        with closing(sqlite3.connect(self.source)) as connection:
            with connection:
                connection.execute("CREATE TABLE review_history(id INTEGER PRIMARY KEY)")

        with self.assertRaisesRegex(ValueError, "forbidden authoring tables"):
            freeze_public_corpus(self.source, self.destination, self.gap_manifest)

    def test_freezer_can_repeat_after_manifest_is_bound_to_runtime_database(self):
        self.create_source()
        first = freeze_public_corpus(self.source, self.destination, self.gap_manifest)
        second_destination = RUNTIME / "cuv-second.sqlite3"

        second = freeze_public_corpus(
            self.source, second_destination, self.gap_manifest
        )

        self.assertEqual(first["database_sha256"], second["database_sha256"])
        self.assertEqual(
            sha256_file(self.destination), sha256_file(second_destination)
        )

    def test_cli_json_is_safe_on_a_legacy_windows_console(self):
        self.create_source()
        manifest = RUNTIME / "runtime-manifest.json"
        bytes_output = io.BytesIO()
        output = io.TextIOWrapper(bytes_output, encoding="cp1252")

        code = freeze_main(
            [
                str(self.source),
                "--gap-manifest", str(self.gap_manifest),
                "--output", str(self.destination),
                "--manifest", str(manifest),
            ],
            stdout=output,
        )
        output.flush()
        output.detach()

        self.assertEqual(code, 0)
        report = json.loads(bytes_output.getvalue().decode("cp1252"))
        self.assertIn("Bible", " ".join(report["source_sha256"]))


if __name__ == "__main__":
    unittest.main()
