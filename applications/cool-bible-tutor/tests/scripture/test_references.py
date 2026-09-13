import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[2] / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from book_names import BOOKS, resolve_book  # noqa: E402
from references import parse_reference  # noqa: E402


class BookNameTests(unittest.TestCase):
    def test_all_sixty_six_books_have_stable_ids(self):
        self.assertEqual(len(BOOKS), 66)
        self.assertEqual([book.id for book in BOOKS], list(range(1, 67)))
        self.assertEqual(resolve_book("創").canonical_zh, "創世記")
        self.assertEqual(resolve_book("mAtThEw").canonical_zh, "馬太福音")
        self.assertEqual(resolve_book("約").canonical_zh, "約翰福音")
        self.assertEqual(resolve_book("約一").canonical_zh, "約翰一書")
        self.assertEqual(resolve_book("約二").canonical_zh, "約翰二書")
        self.assertEqual(resolve_book("約三").canonical_zh, "約翰三書")


class ReferenceParserTests(unittest.TestCase):
    def assert_ref(self, text, book, start_chapter, start_verse, end_chapter, end_verse):
        parsed = parse_reference(text)
        self.assertEqual(parsed.book.canonical_zh, book)
        self.assertEqual(
            (parsed.start_chapter, parsed.start_verse, parsed.end_chapter, parsed.end_verse),
            (start_chapter, start_verse, end_chapter, end_verse),
        )

    def test_chinese_english_ranges_and_whole_chapter(self):
        cases = (
            ("創世記 1:1", "創世記", 1, 1, 1, 1),
            ("創 1:1-3", "創世記", 1, 1, 1, 3),
            ("太5:3", "馬太福音", 5, 3, 5, 3),
            ("Matthew 5:3", "馬太福音", 5, 3, 5, 3),
            ("約 3:16-18", "約翰福音", 3, 16, 3, 18),
            ("約 3:16-4:2", "約翰福音", 3, 16, 4, 2),
            ("詩篇 23", "詩篇", 23, None, 23, None),
            ("  約翰福音　3：16－18  ", "約翰福音", 3, 16, 3, 18),
        )
        for case in cases:
            with self.subTest(case=case[0]):
                self.assert_ref(*case)

    def test_invalid_references_are_rejected(self):
        for value in (
            "1:1", "未知書 1:1", "創 0:1", "創 1:0", "創 -1:1",
            "創 2:3-1:1", "創 2:3-2", "約翰 1:1",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_reference(value)


if __name__ == "__main__":
    unittest.main()
