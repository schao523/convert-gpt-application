import contextlib
from contextlib import closing
from dataclasses import dataclass
import io
import json
import os
import sqlite3
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPTS = Path(__file__).parents[2] / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
sys.path.insert(0, str(SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture" / "discover-rag"
RUNTIME.mkdir(parents=True, exist_ok=True)

from book_names import resolve_book  # noqa: E402
from corpus_db import VerseRecord, initialize_database, insert_verses  # noqa: E402
from discover_bible_references import discover_references, main  # noqa: E402
import rag_runtime  # noqa: E402


@dataclass
class FakeChunk:
    doc_id: str
    chunk_id: str
    text: str
    section_path: str
    order: int
    language: str
    embedding_model: str
    namespace: str
    embedding: list[float]
    metadata: dict
    hash: str


@dataclass
class FakeCandidate:
    chunk: FakeChunk
    score: float
    source: str


def candidate(reference, text, *, source="hybrid", source_hashes="synthetic.pdf=abc",
              app_id="cool-bible-tutor", namespace="cool-bible-tutor:zh:bge-large-zh"):
    return FakeCandidate(
        chunk=FakeChunk(
            doc_id="cuv:40:5", chunk_id=f"chunk:{reference}", text=text,
            section_path=reference, order=0, language="zh", embedding_model="bge-large-zh",
            namespace=namespace, embedding=[0.1],
            metadata={
                "app_id": app_id, "corpus": "cuv-private",
                "book_id": "40", "book_name": "馬太福音", "chapter": "5",
                "canonical_reference": reference, "start_verse": "3", "end_verse": "4",
                "verified_all": "true", "unverified_count": "0",
                "source_files": "synthetic.pdf", "source_pages": "7,8",
                "source_hashes": source_hashes,
            },
            hash="hash",
        ),
        score=0.75,
        source=source,
    )


class DiscoverBibleReferencesTests(unittest.TestCase):
    def setUp(self):
        self.data_dir = RUNTIME / "corpus"
        self.data_dir.mkdir(exist_ok=True)
        self.database = self.data_dir / "cuv.sqlite3"
        self.database.unlink(missing_ok=True)
        initialize_database(self.database)
        self.connection = sqlite3.connect(self.database)
        with self.connection:
            insert_verses(self.connection, (
                VerseRecord(1, 1, 1, "未核合成。", "synthetic.pdf", 1, 70.0, False),
                VerseRecord(40, 5, 3, "合成甲。", "synthetic.pdf", 7, 99.0, True),
                VerseRecord(40, 5, 4, "合成乙。", "synthetic.pdf", 8, 99.0, True),
                VerseRecord(40, 6, 1, "合成丙。", "synthetic.pdf", 9, 99.0, True),
            ))
            self.connection.execute(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                ("source_sha256:synthetic.pdf", "abc"),
            )

    def tearDown(self):
        self.connection.close()
        self.database.unlink(missing_ok=True)

    @staticmethod
    def api_for(*candidates, seen=None, failure=None):
        def retrieve_data(query, top_k, filters, config):
            if failure:
                raise failure
            if seen is not None:
                seen.update(query=query, top_k=top_k, filters=filters, config=config)
            return SimpleNamespace(
                query=query,
                results=list(candidates),
                debug={"embedding_backend": "hash", "private": "do not expose"},
            )
        return SimpleNamespace(default_retrieval_config=object(), retrieve_data=retrieve_data)

    def call_main(self, *arguments, loader):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, {}, clear=True):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = main(list(arguments), rag_api_loader=loader)
        return code, json.loads(stdout.getvalue()), stderr.getvalue()

    def test_discovery_returns_ranked_references_without_chunk_text_or_scores(self):
        seen = {}
        api = self.api_for(
            candidate("太5:3-4", "secret chunk text", source="hybrid"),
            candidate("太5:3-4", "duplicate text", source="semantic"),
            candidate("創1:1", "unverified text", source="lexical"),
            candidate("not-a-reference", "bad text", source="semantic"),
            seen=seen,
        )

        payload = discover_references("恩典", 5, self.connection, api)

        self.assertEqual(seen["filters"], {"app_id": "cool-bible-tutor"})
        self.assertEqual(seen["top_k"], 15)
        self.assertEqual(
            [item["reference"] for item in payload["candidates"]],
            ["馬太福音 5:3-4", "創世記 1:1"],
        )
        self.assertEqual(
            [item["trust_status"] for item in payload["candidates"]],
            ["verified", "unverified"],
        )
        serialized = json.dumps(payload, ensure_ascii=False)
        for forbidden in ("secret chunk text", "duplicate text", "unverified text", "0.75", "private"):
            self.assertNotIn(forbidden, serialized)
        self.assertEqual(payload["diagnostics"], {
            "retrieved_count": 4,
            "returned_count": 2,
            "invalid_reference_count": 1,
            "duplicate_reference_count": 1,
        })

    def test_discovery_rejects_cross_plugin_results(self):
        api = self.api_for(candidate(
            "太5:3", "foreign", app_id="another-plugin", namespace="another-plugin:docs"
        ))
        with self.assertRaisesRegex(Exception, "cross_plugin_result"):
            discover_references("恩典", 1, self.connection, api)

    def test_partial_range_is_missing_and_changed_hash_is_stale(self):
        payload = discover_references(
            "缺節", 3, self.connection,
            self.api_for(candidate("太5:3-5", "partial", source_hashes="synthetic.pdf=old")),
        )
        item = payload["candidates"][0]
        self.assertEqual(item["trust_status"], "missing")
        self.assertEqual(item["rag_index_status"], "stale")
        self.assertEqual(item["source_pages"], [7, 8])

    def test_current_hash_compares_only_sources_named_by_candidate(self):
        with self.connection:
            self.connection.execute(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                ("source_sha256:other.pdf", "def"),
            )
        payload = discover_references(
            "饒恕", 1, self.connection, self.api_for(candidate("太5:3", "candidate")),
        )
        self.assertEqual(payload["candidates"][0]["rag_index_status"], "current")

    def test_global_stale_marker_overrides_matching_source_hash(self):
        with self.connection:
            self.connection.execute(
                "INSERT OR REPLACE INTO metadata(key,value) VALUES ('rag_index_state','stale')"
            )
        payload = discover_references(
            "恩典", 1, self.connection, self.api_for(candidate("太5:3", "hidden")),
        )
        self.assertEqual(payload["candidates"][0]["rag_index_status"], "stale")

    def test_whole_chapter_and_cross_chapter_candidates_are_never_complete(self):
        payload = discover_references(
            "範圍", 2, self.connection,
            self.api_for(candidate("太5", "chapter"), candidate("太5:3-6:1", "cross chapter")),
        )
        self.assertEqual(
            [item["trust_status"] for item in payload["candidates"]],
            ["missing", "missing"],
        )

    def test_book_filter_is_exact_metadata_and_top_k_is_clamped(self):
        seen = {}
        discover_references("愛", 500, self.connection, self.api_for(seen=seen), resolve_book("太"))
        self.assertEqual(seen["top_k"], 150)
        self.assertEqual(seen["filters"], {"app_id": "cool-bible-tutor", "book_id": "40"})

    def test_cli_emits_reference_only_json(self):
        code, payload, stderr = self.call_main(
            "--query", "恩典", "--data-dir", str(self.data_dir),
            loader=lambda: self.api_for(candidate("太5:3", "hidden scripture")),
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["candidates"][0]["reference"], "馬太福音 5:3")
        self.assertNotIn("hidden scripture", json.dumps(payload, ensure_ascii=False))
        self.assertEqual(stderr, "")

    def test_cli_json_is_safe_on_a_legacy_windows_console(self):
        bytes_output = io.BytesIO()
        output = io.TextIOWrapper(bytes_output, encoding="cp1252")
        with patch.dict(os.environ, {}, clear=True):
            with contextlib.redirect_stdout(output):
                code = main(
                    ["--query", "恩典", "--data-dir", str(self.data_dir)],
                    rag_api_loader=lambda: self.api_for(candidate("太5:3", "hidden")),
                )
        output.flush()
        output.detach()

        self.assertEqual(code, 0)
        payload = json.loads(bytes_output.getvalue().decode("cp1252"))
        self.assertEqual(payload["candidates"][0]["reference"], "馬太福音 5:3")

    def test_cli_returns_exit_four_when_retrieval_fails(self):
        code, payload, _ = self.call_main(
            "--query", "恩典", "--data-dir", str(self.data_dir),
            loader=lambda: self.api_for(failure=RuntimeError("vector store offline")),
        )
        self.assertEqual(code, 4)
        self.assertEqual(payload["error"]["code"], "rag_unavailable")

    def test_discovery_without_managed_runtime_returns_setup_guidance(self):
        stdout = io.StringIO()
        app_data = RUNTIME / "missing-managed-runtime"
        with patch.dict(os.environ, {"LOCALAPPDATA": str(app_data)}, clear=True):
            with contextlib.redirect_stdout(stdout):
                code = main(["--query", "神的愛", "--data-dir", str(self.data_dir)])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(code, 4)
        self.assertEqual(payload["status"], "setup_required")
        self.assertIn("setup-rag", payload["next_command"])
        self.assertNotIn("verse_text", payload)

    def test_linux_discovery_honors_launcher_localappdata_override(self):
        app_data = RUNTIME / "linux-local-app-data"
        report = SimpleNamespace(status="rag_setup_required")
        with (
            patch.object(rag_runtime.sys, "platform", "linux"),
            patch("rag_setup.RuntimePaths.for_user", return_value=object()) as resolver,
            patch("rag_setup.bundled_runtime_assets", return_value=object()),
            patch("rag_setup.inspect_rag_setup", return_value=report),
        ):
            _, actual = rag_runtime.managed_runtime_environment(
                {"LOCALAPPDATA": str(app_data)}
            )

        resolver.assert_called_once_with(app_data)
        self.assertIs(actual, report)


if __name__ == "__main__":
    unittest.main()
