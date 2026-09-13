from contextlib import closing
import hashlib
from html.parser import HTMLParser
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
from review_mutations import ReviewMutator  # noqa: E402
from review_server import ReviewApplication  # noqa: E402
from review_sources import SourceRegistry  # noqa: E402
from review_store import ReviewStore  # noqa: E402


class HtmlProbe(HTMLParser):
    def __init__(self):
        super().__init__()
        self.landmarks = set()
        self.control_ids = set()
        self.button_ids = set()
        self.label_targets = set()
        self.iframe_titles = []
        self.live_regions = []

    @property
    def labels_for_controls(self):
        return bool(self.control_ids) and self.control_ids <= self.label_targets

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in {"header", "nav", "main", "aside"}:
            self.landmarks.add(tag)
        if tag in {"input", "select", "textarea"} and values.get("id"):
            self.control_ids.add(values["id"])
        if tag == "button" and values.get("id"):
            self.button_ids.add(values["id"])
        if tag == "label" and values.get("for"):
            self.label_targets.add(values["for"])
        if tag == "iframe":
            self.iframe_titles.append(values.get("title"))
        if values.get("aria-live"):
            self.live_regions.append(values["aria-live"])


class ReviewWebTests(unittest.TestCase):
    def setUp(self):
        self.root = RUNTIME / "review-web"
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir()
        database = self.root / "cuv.sqlite3"
        initialize_database(database)
        source = self.root / "new.pdf"
        source.write_bytes(b"%PDF synthetic")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        with closing(sqlite3.connect(database)) as connection:
            with connection:
                insert_verses(connection, (
                    VerseRecord(40, 5, 1, "合成一。", "new.pdf", 7, 99.0, True),
                    VerseRecord(40, 5, 3, "合成三。", "new.pdf", 7, 80.0, False),
                ))
                connection.execute(
                    "INSERT INTO metadata(key,value) VALUES (?,?)",
                    ("source_sha256:new.pdf", digest),
                )
            sources = SourceRegistry.from_database(connection, (source,))
        assets = SCRIPTS / "review_web"
        self.application = ReviewApplication(
            ReviewStore(database), ReviewMutator(database, self.root, "session", {"new.pdf"}),
            sources, assets, token="test-token", origin="http://127.0.0.1:1234",
        )

    def tearDown(self):
        if self.root.exists():
            shutil.rmtree(self.root)

    def fetch(self, path):
        return self.application.dispatch("GET", path, {}, b"")

    def test_index_is_served_with_security_headers_and_accessible_landmarks(self):
        response = self.fetch("/?token=test-token")
        headers = dict(response.headers)
        self.assertEqual(response.status, 200)
        self.assertEqual(
            headers["Content-Security-Policy"],
            "default-src 'self'; frame-src 'self'; object-src 'self'",
        )
        document = HtmlProbe()
        document.feed(response.body.decode("utf-8"))
        self.assertEqual(document.landmarks, {"header", "nav", "main", "aside"})
        self.assertTrue(document.labels_for_controls)
        self.assertEqual(document.iframe_titles, ["聖經來源 PDF 頁面"])
        self.assertIn("polite", document.live_regions)
        self.assertIn("rag-metadata-sync", document.button_ids)

    def test_index_injects_tokenized_asset_urls_without_inline_script(self):
        response = self.fetch("/?token=test-token")
        markup = response.body.decode("utf-8")
        self.assertIn("/review_web/styles.css?token=test-token", markup)
        self.assertIn("/review_web/app.js?token=test-token", markup)
        self.assertNotIn("<script>", markup)

    def test_assets_are_token_protected_and_have_expected_mime_types(self):
        self.assertEqual(self.fetch("/review_web/app.js").status, 403)
        response = self.fetch("/review_web/app.js?token=test-token")
        self.assertEqual(dict(response.headers)["Content-Type"], "text/javascript; charset=utf-8")
        self.assertGreater(len(response.body), 100)

    def test_automatic_favicon_request_is_empty_and_does_not_need_session_token(self):
        response = self.fetch("/favicon.ico")
        self.assertEqual(response.status, 204)
        self.assertEqual(response.body, b"")

    def test_summary_exposes_stale_and_backup_states_without_private_paths(self):
        initial = self.fetch("/api/summary?token=test-token")
        import json
        payload = json.loads(initial.body)
        self.assertEqual(payload["review"], {
            "backup_created": False, "rag_index_state": "current", "rag_index_stale_at": None,
            "rag_metadata_sync": {"available": False, "reason": "not_configured"},
        })
        snapshot = self.application.store.get_verse(40, 5, 3)
        edit = {**snapshot.as_dict(), "text": "人工核對。", "verified": True}
        self.application.dispatch(
            "POST", "/api/verses/update?token=test-token",
            {"Origin": self.application.origin, "X-Review-Token": "test-token"},
            json.dumps({"expected": snapshot.as_dict(), "replacement": edit}).encode("utf-8"),
        )
        updated = json.loads(self.fetch("/api/summary?token=test-token").body)
        self.assertTrue(updated["review"]["backup_created"])
        self.assertEqual(updated["review"]["rag_index_state"], "stale")
        self.assertNotIn(str(self.root), json.dumps(updated))


if __name__ == "__main__":
    unittest.main()
