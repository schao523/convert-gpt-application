from contextlib import closing, redirect_stderr
import hashlib
import io
import json
import shutil
import sqlite3
import sys
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from pathlib import Path


SCRIPTS = Path(__file__).parents[2] / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
sys.path.insert(0, str(SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture"
RUNTIME.mkdir(exist_ok=True)

from corpus_db import VerseRecord, initialize_database, insert_verses  # noqa: E402
from review_mutations import ReviewMutator  # noqa: E402
from review_cuv_index import build_application, build_parser, resolve_source_paths  # noqa: E402
from review_server import ReviewApplication, serve  # noqa: E402
from review_sources import SourceRegistry  # noqa: E402
from review_store import ReviewStore  # noqa: E402
from rag_metadata_sync import RagMetadataSynchronizer  # noqa: E402


class ReviewServerTests(unittest.TestCase):
    def setUp(self):
        self.root = RUNTIME / "review-server"
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir()
        self.database = self.root / "cuv.sqlite3"
        initialize_database(self.database)
        self.source = self.root / "new.pdf"
        self.source.write_bytes(b"%PDF-1.4 synthetic")
        self.assets = self.root / "assets"
        self.assets.mkdir()
        (self.assets / "index.html").write_text("<!doctype html><main>review</main>", encoding="utf-8")
        (self.assets / "app.js").write_text("window.reviewReady = true;", encoding="utf-8")
        digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                insert_verses(connection, (
                    VerseRecord(40, 5, 1, "合成一。", "new.pdf", 7, 99.0, True),
                    VerseRecord(40, 5, 3, "合成三。", "new.pdf", 7, 80.0, False),
                ))
                connection.execute(
                    "INSERT INTO metadata(key,value) VALUES (?,?)",
                    ("source_sha256:new.pdf", digest),
                )
            registry = SourceRegistry.from_database(connection, (self.source,))
        self.store = ReviewStore(self.database)
        self.mutator = ReviewMutator(self.database, self.root, "session", {"new.pdf"})
        self.application = ReviewApplication(
            self.store, self.mutator, registry, self.assets,
            token="test-token", origin="http://127.0.0.1:4321",
        )
        snapshot = self.store.get_verse(40, 5, 3)
        self.valid_update = {
            "expected": snapshot.as_dict(),
            "replacement": {**snapshot.as_dict(), "text": "人工校訂。", "verified": True},
            "note": "checked PDF",
        }

    def tearDown(self):
        if self.root.exists():
            shutil.rmtree(self.root)

    def dispatch(self, method, path, body=b"", headers=None):
        response = self.application.dispatch(method, path, headers or {}, body)
        payload = json.loads(response.body) if response.body else None
        return response.status, payload

    def test_requests_require_the_session_token(self):
        status, _ = self.dispatch("GET", "/api/summary")
        self.assertEqual(status, 403)
        status, payload = self.dispatch("GET", "/api/summary?token=test-token")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")

    def test_mutation_requires_same_origin_and_header_token(self):
        body = json.dumps(self.valid_update).encode("utf-8")
        status, payload = self.dispatch(
            "POST", "/api/verses/update?token=test-token", body=body,
            headers={"X-Review-Token": "test-token", "Origin": "https://attacker.invalid"},
        )
        self.assertEqual(status, 403)
        self.assertEqual(payload["error"]["code"], "forbidden")

    def test_rag_metadata_sync_requires_confirmation_and_uses_secured_mutation_route(self):
        vector = self.root / "rag-vectors.json"
        vector.write_text(json.dumps({"items": [{
            "doc_id": "cuv:40:5", "chunk_id": "cuv:40:5::0",
            "text": "5:1 合成一。", "section_path": "太5:1", "order": 0,
            "language": "zh", "embedding_model": "bge-large-zh",
            "namespace": "cool-bible-tutor:zh:bge-large-zh", "embedding": [0.5],
            "metadata": {
                "app_id": "cool-bible-tutor", "book_id": "40", "chapter": "5",
                "start_verse": "1", "end_verse": "1", "verified_all": "false",
                "unverified_count": "1", "source_files": "new.pdf",
                "source_pages": "7", "source_hashes": "new.pdf=" + hashlib.sha256(
                    self.source.read_bytes()
                ).hexdigest(),
            },
            "hash": "fixture-hash",
        }]}), encoding="utf-8")
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES ('rag_index_state', 'stale')"
                )
                connection.executemany(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                    (
                        ("rag_vector_item_count", "1"),
                        (
                            "rag_corpus_structure_sha256",
                            hashlib.sha256(b"40:5:1\n40:5:3\n").hexdigest(),
                        ),
                        (
                            "rag_vector_identity_sha256",
                            hashlib.sha256(json.dumps(
                                [["cuv:40:5", "cuv:40:5::0", 0]],
                                separators=(",", ":"),
                            ).encode("utf-8")).hexdigest(),
                        ),
                    ),
                )
        self.application.rag_sync = RagMetadataSynchronizer(
            self.database,
            environ={
                "RAG_VECTOR_STORE_BACKEND": "json",
                "RAG_VECTOR_STORE_PATH": str(vector),
            },
        )
        headers = {"X-Review-Token": "test-token", "Origin": self.application.origin}

        status, payload = self.dispatch(
            "POST", "/api/rag/metadata-sync?token=test-token", b"{}", headers,
        )
        self.assertEqual((status, payload["error"]["code"]), (422, "validation_error"))

        body = json.dumps({"confirmation": "同步 RAG 核實資料"}).encode("utf-8")
        status, payload = self.dispatch(
            "POST", "/api/rag/metadata-sync?token=test-token", body,
            {"X-Review-Token": "test-token", "Origin": "https://attacker.invalid"},
        )
        self.assertEqual((status, payload["error"]["code"]), (403, "forbidden"))

        status, payload = self.dispatch(
            "POST", "/api/rag/metadata-sync?token=test-token", body, headers,
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["result"]["targeted_items"], 1)
        self.assertTrue(payload["result"]["embeddings_unchanged"])

    def start_server(self):
        server = serve(self.application, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def stop():
            server.shutdown()
            thread.join(2)
            server.server_close()
        self.addCleanup(stop)
        return f"http://127.0.0.1:{server.server_address[1]}"

    def http(self, base, method, path, body=None, headers=None):
        request = Request(base + path, data=body, method=method, headers=headers or {})
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as error:
            response = error
        try:
            content = response.read()
            return response.status, dict(response.headers), content
        finally:
            response.close()

    def test_real_server_serves_summary_pagination_pdf_ranges_and_assets(self):
        base = self.start_server()
        status, headers, content = self.http(base, "GET", "/api/summary?token=test-token")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(content)["summary"]["verse_count"], 2)
        self.assertNotIn("Access-Control-Allow-Origin", headers)

        status, _, content = self.http(
            base, "GET", "/api/issues?kind=gap&offset=0&limit=1&token=test-token"
        )
        issues = json.loads(content)["result"]
        self.assertEqual((status, issues["total"], len(issues["items"])), (200, 1, 1))

        source_id = self.application.sources.public_sources()[0]["id"]
        status, headers, content = self.http(
            base, "GET", f"/source/{source_id}.pdf?token=test-token",
            headers={"Range": "bytes=5-9"},
        )
        self.assertEqual((status, content), (206, b"1.4 s"))
        self.assertEqual(headers["Content-Range"], "bytes 5-9/18")
        status, headers, content = self.http(
            base, "GET", f"/source/{source_id}.pdf?token=test-token",
            headers={"Range": "bytes=999-1000"},
        )
        self.assertEqual((status, headers["Content-Range"], content), (416, "bytes */18", b""))

        status, headers, content = self.http(base, "GET", "/review_web/app.js?token=test-token")
        self.assertEqual((status, headers["Content-Type"]), (200, "text/javascript; charset=utf-8"))
        self.assertIn(b"reviewReady", content)

    def test_real_server_blocks_missing_token_and_accepts_same_origin_update(self):
        base = self.start_server()
        status, _, content = self.http(base, "GET", "/api/summary")
        self.assertEqual((status, json.loads(content)["error"]["code"]), (403, "forbidden"))

        body = json.dumps(self.valid_update).encode("utf-8")
        status, _, content = self.http(
            base, "POST", "/api/verses/update?token=test-token", body=body,
            headers={
                "Content-Type": "application/json", "X-Review-Token": "test-token",
                "Origin": base,
            },
        )
        payload = json.loads(content)
        self.assertEqual((status, payload["verse"]["text"]), (200, "人工校訂。"))
        self.assertEqual(self.store.get_verse(40, 5, 3).text, "人工校訂。")

    def test_dispatch_maps_malformed_validation_conflict_and_missing_errors(self):
        headers = {"X-Review-Token": "test-token", "Origin": self.application.origin}
        status, payload = self.dispatch(
            "POST", "/api/verses/update?token=test-token", b"{", headers,
        )
        self.assertEqual((status, payload["error"]["code"]), (400, "invalid_json"))

        invalid = json.dumps({**self.valid_update, "replacement": {
            **self.valid_update["replacement"], "text": "",
        }}).encode("utf-8")
        status, payload = self.dispatch(
            "POST", "/api/verses/update?token=test-token", invalid, headers,
        )
        self.assertEqual((status, payload["error"]["code"]), (422, "validation_error"))

        expected = self.store.get_verse(40, 5, 3)
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "UPDATE verses SET text='concurrent' WHERE book_id=40 AND chapter=5 AND verse=3"
                )
        conflict = json.dumps({
            "expected": expected.as_dict(),
            "replacement": {**expected.as_dict(), "text": "stale"},
        }).encode("utf-8")
        status, payload = self.dispatch(
            "POST", "/api/verses/update?token=test-token", conflict, headers,
        )
        self.assertEqual((status, payload["error"]["code"]), (409, "conflict"))

        status, payload = self.dispatch("GET", "/api/not-here?token=test-token")
        self.assertEqual((status, payload["error"]["code"]), (404, "not_found"))

    def test_issue_ids_resolve_review_items_and_history(self):
        status, payload = self.dispatch(
            "GET", "/api/issues?kind=unverified&token=test-token"
        )
        issue = payload["result"]["items"][0]
        self.assertEqual(status, 200)
        self.assertEqual(set(issue) - {"id"}, {
            "source_file", "source_page", "row_count", "low_confidence_count",
        })
        status, payload = self.dispatch(
            "GET", f"/api/review-item?kind=unverified&id={issue['id']}&token=test-token"
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            [verse["reference"] for verse in payload["item"]["verses"]],
            ["馬太福音 5:1", "馬太福音 5:3"],
        )
        self.assertEqual(payload["item"]["source"]["filename"], "new.pdf")

        headers = {"X-Review-Token": "test-token", "Origin": self.application.origin}
        self.dispatch(
            "POST", "/api/verses/update?token=test-token",
            json.dumps(self.valid_update).encode("utf-8"), headers,
        )
        status, payload = self.dispatch("GET", "/api/history?token=test-token")
        self.assertEqual((status, payload["history"][0]["action"]), (200, "update_verse"))

    def test_all_mutation_routes_apply_to_synthetic_rows(self):
        headers = {"X-Review-Token": "test-token", "Origin": self.application.origin}
        missing = {
            "book_id": 40, "chapter": 5, "verse": 2, "text": "人工補入。",
            "source_file": "new.pdf", "source_page": 7,
            "ocr_confidence": 100.0, "verified": True,
        }
        status, payload = self.dispatch(
            "POST", "/api/verses/insert?token=test-token",
            json.dumps({"replacement": missing}).encode("utf-8"), headers,
        )
        self.assertEqual((status, payload["verse"]["verse"]), (201, 2))

        expected = self.store.get_verse(40, 5, 2)
        status, payload = self.dispatch(
            "POST", "/api/verses/verification?token=test-token",
            json.dumps({"expected": [expected.as_dict()], "verified": False}).encode("utf-8"),
            headers,
        )
        self.assertEqual((status, payload["verses"][0]["verified"]), (200, False))

        page = self.store.page_snapshots("new.pdf", 7)
        status, payload = self.dispatch(
            "POST", "/api/pages/verify?token=test-token",
            json.dumps({"expected": [row.as_dict() for row in page]}).encode("utf-8"), headers,
        )
        self.assertEqual(status, 200)
        self.assertTrue(all(row["verified"] for row in payload["verses"]))

    def test_unknown_source_id_is_missing_not_a_validation_error(self):
        status, payload = self.dispatch(
            "GET", "/source/not-a-real-id.pdf?token=test-token"
        )
        self.assertEqual((status, payload["error"]["code"]), (404, "not_found"))

    def test_backup_failure_response_never_exposes_private_paths(self):
        (self.root / "backups").write_text("blocked", encoding="utf-8")
        headers = {"X-Review-Token": "test-token", "Origin": self.application.origin}
        status, payload = self.dispatch(
            "POST", "/api/verses/update?token=test-token",
            json.dumps(self.valid_update).encode("utf-8"), headers,
        )
        self.assertEqual((status, payload["error"]["code"]), (500, "backup_failed"))
        self.assertEqual(payload["error"]["message"], "無法建立核對前備份；語料未被修改。")
        self.assertNotIn("review-server", json.dumps(payload))

    def test_launcher_has_no_host_override_and_builds_from_validated_private_inputs(self):
        parser = build_parser()
        args = parser.parse_args([
            "--data-dir", str(self.root), "--source-pdf", str(self.source),
            "--port", "0", "--no-open",
        ])
        self.assertFalse(hasattr(args, "host"))
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(["--host", "0.0.0.0"])
        application = build_application(
            self.root, (self.source,), token="launcher-token", session_id="launcher-session",
            assets=self.assets,
        )
        self.assertEqual(application.store.summary()["verse_count"], 2)
        self.assertEqual(application.token, "launcher-token")

    def test_source_paths_use_explicit_values_before_environment(self):
        alternate = self.root / "alternate.pdf"
        self.assertEqual(
            resolve_source_paths((self.source,), {"COOL_BIBLE_TUTOR_SOURCE_PDFS": str(alternate)}),
            (self.source.resolve(),),
        )
        self.assertEqual(
            resolve_source_paths((), {"COOL_BIBLE_TUTOR_SOURCE_PDFS": str(self.source)}),
            (self.source.resolve(),),
        )

    def test_source_paths_fall_back_to_bundled_pair(self):
        alternate = self.root / "alternate.pdf"
        with patch(
            "review_cuv_index.resolve_bundled_sources",
            return_value=(self.source, alternate),
        ):
            self.assertEqual(resolve_source_paths((), {}), (self.source, alternate))


if __name__ == "__main__":
    unittest.main()
