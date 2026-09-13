import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).parents[2] / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
sys.path.insert(0, str(SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture"

from ocr_adapter import OcrPage, extract_pdf_pages, ocr_page, render_page  # noqa: E402


class OcrAdapterTests(unittest.TestCase):
    @patch("ocr_adapter.subprocess.run")
    def test_embedded_pdf_text_is_split_into_provenance_pages(self, run):
        run.return_value = subprocess.CompletedProcess(
            [], 0, "太 1:1 合成甲。\n\f太 1:2 合成乙。\n\f", ""
        )
        pages = extract_pdf_pages(Path("source.pdf"), executable="pdftotext")
        self.assertEqual([page.page_number for page in pages], [1, 2])
        self.assertEqual(pages[1].lines[0].text, "太 1:2 合成乙。")
        self.assertEqual(pages[1].lines[0].confidence, 100.0)
        command = run.call_args.args[0]
        self.assertIsInstance(command, list)
        self.assertIn("-layout", command)
        self.assertNotEqual(run.call_args.kwargs.get("shell"), True)

    @patch("ocr_adapter.subprocess.run")
    def test_render_uses_argument_array_without_shell(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, "", "")
        render_page(Path("source.pdf"), 7, RUNTIME / "page-7.png", dpi=300, executable="pdftoppm")
        args, kwargs = run.call_args
        self.assertIsInstance(args[0], list)
        self.assertIn("source.pdf", args[0])
        self.assertIn("7", args[0])
        self.assertNotEqual(kwargs.get("shell"), True)
        self.assertEqual(kwargs.get("encoding"), "utf-8")
        self.assertEqual(kwargs.get("errors"), "replace")

    @patch("ocr_adapter.subprocess.run")
    def test_ocr_parses_tsv_lines_and_confidence(self, run):
        run.return_value = subprocess.CompletedProcess(
            [], 0,
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
            "5\t1\t1\t1\t1\t1\t0\t0\t1\t1\t96\t太\n"
            "5\t1\t1\t1\t1\t2\t0\t0\t1\t1\t94\t1:1\n"
            "5\t1\t1\t1\t1\t3\t0\t0\t1\t1\t92\t合成。\n",
            "",
        )
        result = ocr_page(
            Path("page.png"), page_number=4, executable="tesseract",
            tessdata_dir=Path("private-tessdata"),
        )
        self.assertIsInstance(result, OcrPage)
        self.assertEqual(result.lines[0].text, "太1:1合成。")
        self.assertEqual(result.lines[0].confidence, 94.0)
        self.assertIn("--tessdata-dir", run.call_args.args[0])
        self.assertIn("private-tessdata", run.call_args.args[0])
        self.assertIn("tessedit_create_tsv=1", run.call_args.args[0])
        self.assertNotEqual(run.call_args.kwargs.get("shell"), True)
        self.assertEqual(run.call_args.kwargs.get("encoding"), "utf-8")


if __name__ == "__main__":
    unittest.main()
