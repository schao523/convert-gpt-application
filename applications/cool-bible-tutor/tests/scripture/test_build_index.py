import sqlite3
from contextlib import closing
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).parents[2] / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
sys.path.insert(0, str(SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture" / "build-index"
RUNTIME.mkdir(parents=True, exist_ok=True)
FIXTURE = Path(__file__).parents[1] / "fixtures" / "scripture" / "synthetic-page.txt"

from build_cuv_index import (  # noqa: E402
    build_index,
    parse_ocr_lines,
    parse_pages,
    resolve_testament_sources,
)
from ocr_adapter import OcrLine, OcrPage  # noqa: E402


class OcrVerseParserTests(unittest.TestCase):
    def test_wrapped_lines_preserve_text_page_and_confidence(self):
        lines = FIXTURE.read_text(encoding="utf-8").splitlines()
        page = OcrPage(9, tuple(OcrLine(text, 95.0 - index) for index, text in enumerate(lines)))
        records = parse_ocr_lines(page, Path("synthetic.pdf"))
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].text, "這是合成測試文字，也是同一節的續行。")
        self.assertEqual(records[0].source_page, 9)
        self.assertEqual(records[0].source_file, "synthetic.pdf")
        self.assertEqual(records[0].ocr_confidence, 94.5)
        self.assertFalse(records[0].verified)

    def test_compact_ocr_reference_is_accepted(self):
        page = OcrPage(3, (OcrLine("太1:1無空格合成文字。", 98.0),))
        records = parse_ocr_lines(page, Path("synthetic.pdf"))
        self.assertEqual(records[0].text, "無空格合成文字。")

    def test_page_leading_continuation_joins_previous_verse(self):
        pages = (
            OcrPage(1, (OcrLine("太1:1第一行，", 100.0),)),
            OcrPage(2, (OcrLine("跨頁續行。", 100.0), OcrLine("太1:2第二節。", 100.0))),
        )
        records = parse_pages(pages, Path("synthetic.pdf"))
        self.assertEqual(records[0].text, "第一行，跨頁續行。")
        self.assertEqual(records[0].source_page, 1)


class AtomicBuildTests(unittest.TestCase):
    def setUp(self):
        for path in RUNTIME.glob("*"):
            if path.is_file():
                path.unlink()
        self.old_pdf = RUNTIME / "old.pdf"
        self.new_pdf = RUNTIME / "new.pdf"
        self.old_pdf.write_bytes(b"synthetic-old")
        self.new_pdf.write_bytes(b"synthetic-new")

    def tearDown(self):
        for path in RUNTIME.glob("*"):
            if path.is_file():
                path.unlink()

    @patch("build_cuv_index.extract_pdf_pages")
    @patch("build_cuv_index.ocr_page")
    @patch("build_cuv_index.render_page")
    @patch("build_cuv_index.pdf_page_count", return_value=1)
    def test_success_prefers_embedded_text_and_creates_queryable_database(self, _, render, ocr, extract):
        extract.side_effect = [
            (OcrPage(1, (OcrLine("創 1:1 合成索引文字。", 100.0),)),),
            (OcrPage(1, (OcrLine("太 1:1 合成索引文字。", 100.0),)),),
        ]
        scratch = RUNTIME / "scratch"
        result = build_index(self.old_pdf, self.new_pdf, RUNTIME, scratch_dir=scratch)
        self.assertEqual(result, RUNTIME / "cuv.sqlite3")
        with closing(sqlite3.connect(result)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM verses").fetchone()[0], 2)
        self.assertFalse((RUNTIME / "build-state.json").exists())
        render.assert_not_called()
        ocr.assert_not_called()

    @patch("build_cuv_index.ocr_page", side_effect=RuntimeError("synthetic OCR failure"))
    @patch("build_cuv_index.render_page")
    @patch("build_cuv_index.extract_pdf_pages", return_value=())
    @patch("build_cuv_index.pdf_page_count", return_value=1)
    def test_failure_preserves_state_and_does_not_replace_existing_database(self, *_):
        target = RUNTIME / "cuv.sqlite3"
        target.write_bytes(b"existing-index")
        with self.assertRaises(RuntimeError):
            build_index(self.old_pdf, self.new_pdf, RUNTIME)
        self.assertEqual(target.read_bytes(), b"existing-index")
        self.assertTrue((RUNTIME / "build-state.json").is_file())
        self.assertFalse(any(RUNTIME.glob("page-*.png")))

    def test_missing_testament_arguments_use_bundled_pair(self):
        with patch(
            "build_cuv_index.resolve_bundled_sources",
            return_value=(self.old_pdf, self.new_pdf),
        ):
            self.assertEqual(
                resolve_testament_sources(None, None),
                (self.old_pdf, self.new_pdf),
            )

    def test_testament_sources_reject_partial_override(self):
        with self.assertRaisesRegex(ValueError, "together"):
            resolve_testament_sources(self.old_pdf, None)

    def test_explicit_testament_pair_is_preserved(self):
        with patch("build_cuv_index.resolve_bundled_sources") as bundled:
            self.assertEqual(
                resolve_testament_sources(self.old_pdf, self.new_pdf),
                (self.old_pdf.resolve(), self.new_pdf.resolve()),
            )
        bundled.assert_not_called()


if __name__ == "__main__":
    unittest.main()
