from dataclasses import dataclass
import re
import unicodedata

from book_names import Book, aliases_by_longest_prefix


@dataclass(frozen=True, order=True)
class VerseRef:
    book_id: int
    chapter: int
    verse: int


@dataclass(frozen=True)
class ReferenceRequest:
    book: Book
    start_chapter: int
    start_verse: int | None
    end_chapter: int
    end_verse: int | None

    @property
    def is_whole_chapter(self) -> bool:
        return self.start_verse is None


_CHAPTER = re.compile(r"^(\d+)$")
_VERSE_RANGE = re.compile(r"^(\d+):(\d+)(?:-(?:(\d+):)?(\d+))?$")


def _normalize_reference(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = normalized.replace("：", ":").replace("－", "-")
    normalized = normalized.replace("–", "-").replace("—", "-")
    return "".join(character for character in normalized if not character.isspace())


def _positive(value: str, label: str) -> int:
    number = int(value)
    if number <= 0:
        raise ValueError(f"{label} must be positive")
    return number


def parse_reference(value: str) -> ReferenceRequest:
    normalized = _normalize_reference(value)
    if not normalized:
        raise ValueError("Bible reference is empty")

    book = None
    remainder = ""
    for alias, candidate in aliases_by_longest_prefix():
        if normalized.startswith(alias):
            book = candidate
            remainder = normalized[len(alias):]
            break
    if book is None or not remainder:
        raise ValueError(f"Bible reference is missing a recognized book or location: {value!r}")

    chapter_match = _CHAPTER.fullmatch(remainder)
    if chapter_match:
        chapter = _positive(chapter_match.group(1), "chapter")
        return ReferenceRequest(book, chapter, None, chapter, None)

    range_match = _VERSE_RANGE.fullmatch(remainder)
    if not range_match:
        raise ValueError(f"Invalid Bible reference syntax: {value!r}")

    start_chapter = _positive(range_match.group(1), "chapter")
    start_verse = _positive(range_match.group(2), "verse")
    if range_match.group(4) is None:
        end_chapter, end_verse = start_chapter, start_verse
    else:
        end_chapter = _positive(range_match.group(3), "chapter") if range_match.group(3) else start_chapter
        end_verse = _positive(range_match.group(4), "verse")

    if (end_chapter, end_verse) < (start_chapter, start_verse):
        raise ValueError("Bible reference range is reversed")
    return ReferenceRequest(book, start_chapter, start_verse, end_chapter, end_verse)
