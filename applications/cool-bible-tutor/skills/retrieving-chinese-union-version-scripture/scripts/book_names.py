from dataclasses import dataclass
from typing import Sequence
import unicodedata


@dataclass(frozen=True)
class Book:
    id: int
    testament: str
    canonical_zh: str
    abbreviation_zh: str
    english: str
    aliases: Sequence[str]


_BOOK_ROWS = (
    ("創世記", "創", "Genesis", ("Gen",)),
    ("出埃及記", "出", "Exodus", ("Exod", "Ex")),
    ("利未記", "利", "Leviticus", ("Lev",)),
    ("民數記", "民", "Numbers", ("Num",)),
    ("申命記", "申", "Deuteronomy", ("Deut",)),
    ("約書亞記", "書", "Joshua", ("Josh",)),
    ("士師記", "士", "Judges", ("Judg",)),
    ("路得記", "得", "Ruth", ()),
    ("撒母耳記上", "撒上", "1 Samuel", ("I Samuel", "1Sam")),
    ("撒母耳記下", "撒下", "2 Samuel", ("II Samuel", "2Sam")),
    ("列王紀上", "王上", "1 Kings", ("I Kings", "1Kgs")),
    ("列王紀下", "王下", "2 Kings", ("II Kings", "2Kgs")),
    ("歷代志上", "代上", "1 Chronicles", ("I Chronicles", "1Chr")),
    ("歷代志下", "代下", "2 Chronicles", ("II Chronicles", "2Chr")),
    ("以斯拉記", "拉", "Ezra", ()),
    ("尼希米記", "尼", "Nehemiah", ("Neh",)),
    ("以斯帖記", "斯", "Esther", ("Esth",)),
    ("約伯記", "伯", "Job", ()),
    ("詩篇", "詩", "Psalms", ("Psalm", "Ps")),
    ("箴言", "箴", "Proverbs", ("Prov",)),
    ("傳道書", "傳", "Ecclesiastes", ("Eccl",)),
    ("雅歌", "歌", "Song of Solomon", ("Song of Songs", "Song")),
    ("以賽亞書", "賽", "Isaiah", ("Isa",)),
    ("耶利米書", "耶", "Jeremiah", ("Jer",)),
    ("耶利米哀歌", "哀", "Lamentations", ("Lam",)),
    ("以西結書", "結", "Ezekiel", ("Ezek",)),
    ("但以理書", "但", "Daniel", ("Dan",)),
    ("何西阿書", "何", "Hosea", ("Hos",)),
    ("約珥書", "珥", "Joel", ()),
    ("阿摩司書", "摩", "Amos", ()),
    ("俄巴底亞書", "俄", "Obadiah", ("Obad",)),
    ("約拿書", "拿", "Jonah", ()),
    ("彌迦書", "彌", "Micah", ("Mic",)),
    ("那鴻書", "鴻", "Nahum", ("Nah",)),
    ("哈巴谷書", "哈", "Habakkuk", ("Hab",)),
    ("西番雅書", "番", "Zephaniah", ("Zeph",)),
    ("哈該書", "該", "Haggai", ("Hag",)),
    ("撒迦利亞書", "亞", "Zechariah", ("Zech",)),
    ("瑪拉基書", "瑪", "Malachi", ("Mal",)),
    ("馬太福音", "太", "Matthew", ("Matt",)),
    ("馬可福音", "可", "Mark", ("Mk",)),
    ("路加福音", "路", "Luke", ("Lk",)),
    ("約翰福音", "約", "John", ("Jn",)),
    ("使徒行傳", "徒", "Acts", ()),
    ("羅馬書", "羅", "Romans", ("Rom",)),
    ("哥林多前書", "林前", "1 Corinthians", ("I Corinthians", "1Cor")),
    ("哥林多後書", "林後", "2 Corinthians", ("II Corinthians", "2Cor")),
    ("加拉太書", "加", "Galatians", ("Gal",)),
    ("以弗所書", "弗", "Ephesians", ("Eph",)),
    ("腓立比書", "腓", "Philippians", ("Phil",)),
    ("歌羅西書", "西", "Colossians", ("Col",)),
    ("帖撒羅尼迦前書", "帖前", "1 Thessalonians", ("I Thessalonians", "1Thess")),
    ("帖撒羅尼迦後書", "帖後", "2 Thessalonians", ("II Thessalonians", "2Thess")),
    ("提摩太前書", "提前", "1 Timothy", ("I Timothy", "1Tim")),
    ("提摩太後書", "提後", "2 Timothy", ("II Timothy", "2Tim")),
    ("提多書", "多", "Titus", ()),
    ("腓利門書", "門", "Philemon", ("Phlm",)),
    ("希伯來書", "來", "Hebrews", ("Heb",)),
    ("雅各書", "雅", "James", ("Jas",)),
    ("彼得前書", "彼前", "1 Peter", ("I Peter", "1Pet")),
    ("彼得後書", "彼後", "2 Peter", ("II Peter", "2Pet")),
    ("約翰一書", "約一", "1 John", ("I John", "1Jn")),
    ("約翰二書", "約二", "2 John", ("II John", "2Jn")),
    ("約翰三書", "約三", "3 John", ("III John", "3Jn")),
    ("猶大書", "猶", "Jude", ()),
    ("啟示錄", "啟", "Revelation", ("Rev",)),
)


BOOKS = tuple(
    Book(
        id=index,
        testament="OT" if index <= 39 else "NT",
        canonical_zh=row[0],
        abbreviation_zh=row[1],
        english=row[2],
        aliases=tuple(row[3]),
    )
    for index, row in enumerate(_BOOK_ROWS, start=1)
)


def normalize_book_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


_ALIAS_MAP: dict[str, Book] = {}
for _book in BOOKS:
    for _alias in (_book.canonical_zh, _book.abbreviation_zh, _book.english, *_book.aliases):
        _key = normalize_book_name(_alias)
        if _key in _ALIAS_MAP and _ALIAS_MAP[_key] != _book:
            raise RuntimeError(f"Ambiguous Bible book alias: {_alias}")
        _ALIAS_MAP[_key] = _book


def resolve_book(value: str) -> Book:
    key = normalize_book_name(value)
    try:
        return _ALIAS_MAP[key]
    except KeyError as error:
        raise ValueError(f"Unknown or ambiguous Bible book: {value!r}") from error


def aliases_by_longest_prefix() -> tuple[tuple[str, Book], ...]:
    return tuple(sorted(_ALIAS_MAP.items(), key=lambda item: len(item[0]), reverse=True))
