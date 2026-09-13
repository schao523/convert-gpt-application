from dataclasses import dataclass
from contextlib import closing
from collections.abc import Mapping
import os
from pathlib import Path
import sqlite3
from typing import Iterable

from references import ReferenceRequest


DATABASE_NAME = "cuv.sqlite3"
SCHEMA_VERSION = "1"
DEFAULT_CONFIDENCE_THRESHOLD = 90.0
PLUGIN_ROOT = Path(__file__).resolve().parents[3]
BUNDLED_DATABASE = PLUGIN_ROOT / "assets" / "scripture" / DATABASE_NAME


@dataclass(frozen=True)
class VerseRecord:
    book_id: int
    chapter: int
    verse: int
    text: str
    source_file: str
    source_page: int
    ocr_confidence: float
    verified: bool


@dataclass(frozen=True)
class Passage:
    request: ReferenceRequest
    records: tuple[VerseRecord, ...]
    confidence_threshold: float

    @property
    def canonical_reference(self) -> str:
        book = self.request.book.canonical_zh
        start_chapter = self.request.start_chapter
        start_verse = self.request.start_verse
        end_chapter = self.request.end_chapter
        end_verse = self.request.end_verse
        if start_verse is None:
            return f"{book} {start_chapter}"
        if (start_chapter, start_verse) == (end_chapter, end_verse):
            return f"{book} {start_chapter}:{start_verse}"
        if start_chapter == end_chapter:
            return f"{book} {start_chapter}:{start_verse}-{end_verse}"
        return f"{book} {start_chapter}:{start_verse}-{end_chapter}:{end_verse}"

    @property
    def verified(self) -> bool:
        return bool(self.records) and all(
            record.verified and record.ocr_confidence >= self.confidence_threshold
            for record in self.records
        )


def resolve_data_dir(explicit: Path | None) -> Path:
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    configured = os.environ.get("COOL_BIBLE_TUTOR_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path(__file__).parents[1] / "data").resolve()


def resolve_database(
    explicit_data_dir: Path | None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    if explicit_data_dir is not None:
        return Path(explicit_data_dir).expanduser().resolve() / DATABASE_NAME
    environment = os.environ if environ is None else environ
    configured = environment.get("COOL_BIBLE_TUTOR_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve() / DATABASE_NAME
    return BUNDLED_DATABASE


def open_corpus_read_only(path: Path) -> sqlite3.Connection:
    uri = Path(path).resolve().as_uri() + "?mode=ro&immutable=1"
    return sqlite3.connect(uri, uri=True)


def initialize_database(path: Path, confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection:
        with connection:
            connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS verses (
                book_id INTEGER NOT NULL,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                text TEXT NOT NULL,
                source_file TEXT NOT NULL,
                source_page INTEGER NOT NULL,
                ocr_confidence REAL NOT NULL,
                verified INTEGER NOT NULL CHECK (verified IN (0, 1)),
                PRIMARY KEY (book_id, chapter, verse)
            );
            """
        )
            connection.executemany(
                "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                (
                    ("schema_version", SCHEMA_VERSION),
                    ("confidence_threshold", str(float(confidence_threshold))),
                ),
            )


def insert_verses(connection: sqlite3.Connection, verses: Iterable[VerseRecord]) -> None:
    connection.executemany(
        """
        INSERT OR REPLACE INTO verses(
            book_id, chapter, verse, text, source_file, source_page,
            ocr_confidence, verified
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            (
                record.book_id, record.chapter, record.verse, record.text,
                record.source_file, record.source_page, record.ocr_confidence,
                int(record.verified),
            )
            for record in verses
        ),
    )


def fetch_passage(connection: sqlite3.Connection, request: ReferenceRequest) -> Passage:
    if request.is_whole_chapter:
        rows = connection.execute(
            """SELECT book_id, chapter, verse, text, source_file, source_page,
                      ocr_confidence, verified
               FROM verses WHERE book_id = ? AND chapter = ?
               ORDER BY chapter, verse""",
            (request.book.id, request.start_chapter),
        ).fetchall()
    else:
        rows = connection.execute(
            """SELECT book_id, chapter, verse, text, source_file, source_page,
                      ocr_confidence, verified
               FROM verses
               WHERE book_id = ?
                 AND (chapter > ? OR (chapter = ? AND verse >= ?))
                 AND (chapter < ? OR (chapter = ? AND verse <= ?))
               ORDER BY chapter, verse""",
            (
                request.book.id,
                request.start_chapter, request.start_chapter, request.start_verse,
                request.end_chapter, request.end_chapter, request.end_verse,
            ),
        ).fetchall()
    if not rows:
        raise LookupError("No indexed verses match the requested reference")
    threshold_row = connection.execute(
        "SELECT value FROM metadata WHERE key = 'confidence_threshold'"
    ).fetchone()
    threshold = float(threshold_row[0]) if threshold_row else DEFAULT_CONFIDENCE_THRESHOLD
    records = tuple(VerseRecord(*row[:-1], bool(row[-1])) for row in rows)
    return Passage(request, records, threshold)
