from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path
import sqlite3

from book_names import BOOKS
from corpus_db import DEFAULT_CONFIDENCE_THRESHOLD


@dataclass(frozen=True)
class VerseSnapshot:
    book_id: int
    chapter: int
    verse: int
    text: str
    source_file: str
    source_page: int
    ocr_confidence: float
    verified: bool

    def as_dict(self) -> dict:
        values = asdict(self)
        values["book_name"] = BOOKS[self.book_id - 1].canonical_zh
        values["reference"] = f"{values['book_name']} {self.chapter}:{self.verse}"
        return values


@dataclass(frozen=True)
class ReviewFilters:
    testament: str | None = None
    book_id: int | None = None
    chapter: int | None = None
    source_page: int | None = None


class ReviewStore:
    def __init__(self, database: Path):
        self.database = Path(database).resolve()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _page(offset: int, limit: int) -> tuple[int, int]:
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("offset must be a non-negative integer")
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        return offset, limit

    @staticmethod
    def _threshold(connection: sqlite3.Connection) -> float:
        row = connection.execute(
            "SELECT value FROM metadata WHERE key = 'confidence_threshold'"
        ).fetchone()
        return float(row[0]) if row else DEFAULT_CONFIDENCE_THRESHOLD

    @staticmethod
    def _snapshot(row: sqlite3.Row, prefix: str = "") -> VerseSnapshot:
        return VerseSnapshot(
            book_id=row[f"{prefix}book_id"],
            chapter=row[f"{prefix}chapter"],
            verse=row[f"{prefix}verse"],
            text=row[f"{prefix}text"],
            source_file=row[f"{prefix}source_file"],
            source_page=row[f"{prefix}source_page"],
            ocr_confidence=float(row[f"{prefix}ocr_confidence"]),
            verified=bool(row[f"{prefix}verified"]),
        )

    def summary(self) -> dict:
        with closing(self._connect()) as connection:
            threshold = self._threshold(connection)
            verse_count = connection.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
            unverified_count = connection.execute(
                "SELECT COUNT(*) FROM verses WHERE verified = 0 OR ocr_confidence < ?",
                (threshold,),
            ).fetchone()[0]
            gap_count = connection.execute(
                """
                WITH ordered AS (
                    SELECT verse,
                           LAG(verse) OVER (
                               PARTITION BY book_id, chapter ORDER BY verse
                           ) AS previous_verse
                    FROM verses
                )
                SELECT COUNT(*) FROM ordered
                WHERE previous_verse IS NOT NULL AND verse != previous_verse + 1
                """
            ).fetchone()[0]
        return {
            "verse_count": verse_count,
            "gap_count": gap_count,
            "unverified_count": unverified_count,
        }

    def review_state(self) -> dict:
        with closing(self._connect()) as connection:
            metadata = dict(connection.execute(
                "SELECT key, value FROM metadata WHERE key IN ('rag_index_state', 'rag_index_stale_at')"
            ))
        return {
            "rag_index_state": metadata.get("rag_index_state", "current"),
            "rag_index_stale_at": metadata.get("rag_index_stale_at"),
        }

    def list_gaps(self, filters: ReviewFilters, offset: int = 0, limit: int = 50) -> dict:
        offset, limit = self._page(offset, limit)
        conditions, parameters = self._filter_conditions(filters)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            WITH filtered AS (
                SELECT * FROM verses {where}
            ), ordered AS (
                SELECT *,
                       LAG(verse) OVER (PARTITION BY book_id, chapter ORDER BY verse) AS previous_verse,
                       LAG(text) OVER (PARTITION BY book_id, chapter ORDER BY verse) AS previous_text,
                       LAG(source_file) OVER (PARTITION BY book_id, chapter ORDER BY verse) AS previous_source_file,
                       LAG(source_page) OVER (PARTITION BY book_id, chapter ORDER BY verse) AS previous_source_page,
                       LAG(ocr_confidence) OVER (PARTITION BY book_id, chapter ORDER BY verse) AS previous_ocr_confidence,
                       LAG(verified) OVER (PARTITION BY book_id, chapter ORDER BY verse) AS previous_verified
                FROM filtered
            )
            SELECT * FROM ordered
            WHERE previous_verse IS NOT NULL AND verse != previous_verse + 1
            ORDER BY book_id, chapter, verse
        """
        with closing(self._connect()) as connection:
            rows = connection.execute(query, parameters).fetchall()
        selected = rows[offset:offset + limit]
        items = []
        for row in selected:
            book_name = BOOKS[row["book_id"] - 1].canonical_zh
            previous = VerseSnapshot(
                row["book_id"], row["chapter"], row["previous_verse"], row["previous_text"],
                row["previous_source_file"], row["previous_source_page"],
                float(row["previous_ocr_confidence"]), bool(row["previous_verified"]),
            )
            following = self._snapshot(row)
            items.append({
                "missing_references": [
                    f"{book_name} {row['chapter']}:{verse}"
                    for verse in range(row["previous_verse"] + 1, row["verse"])
                ],
                "previous": previous.as_dict(),
                "next": following.as_dict(),
            })
        return {"items": items, "total": len(rows), "offset": offset, "limit": limit}

    def list_unverified_pages(
        self, filters: ReviewFilters, offset: int = 0, limit: int = 50
    ) -> dict:
        offset, limit = self._page(offset, limit)
        conditions, parameters = self._filter_conditions(filters)
        with closing(self._connect()) as connection:
            threshold = self._threshold(connection)
            conditions.append("(verified = 0 OR ocr_confidence < ?)")
            parameters.append(threshold)
            where = "WHERE " + " AND ".join(conditions)
            rows = connection.execute(
                f"""
                SELECT source_file, source_page, COUNT(*) AS row_count,
                       SUM(CASE WHEN ocr_confidence < ? THEN 1 ELSE 0 END) AS low_confidence_count,
                       MIN(book_id) AS first_book_id, MIN(chapter) AS first_chapter,
                       MIN(verse) AS first_verse
                FROM verses {where}
                GROUP BY source_file, source_page
                ORDER BY first_book_id, first_chapter, first_verse, source_file, source_page
                """,
                [threshold, *parameters],
            ).fetchall()
        items = [
            {
                "source_file": row["source_file"],
                "source_page": row["source_page"],
                "row_count": row["row_count"],
                "low_confidence_count": row["low_confidence_count"],
            }
            for row in rows[offset:offset + limit]
        ]
        return {"items": items, "total": len(rows), "offset": offset, "limit": limit}

    def get_verse(self, book_id: int, chapter: int, verse: int) -> VerseSnapshot:
        self._validate_reference(book_id, chapter, verse)
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT book_id, chapter, verse, text, source_file, source_page,
                       ocr_confidence, verified
                FROM verses WHERE book_id = ? AND chapter = ? AND verse = ?
                """,
                (book_id, chapter, verse),
            ).fetchone()
        if row is None:
            raise LookupError(f"Verse is not indexed: {book_id} {chapter}:{verse}")
        return self._snapshot(row)

    def page_snapshots(self, source_file: str, source_page: int) -> tuple[VerseSnapshot, ...]:
        if not isinstance(source_file, str) or not source_file.strip():
            raise ValueError("source_file must not be blank")
        if not isinstance(source_page, int) or source_page <= 0:
            raise ValueError("source_page must be a positive integer")
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT book_id, chapter, verse, text, source_file, source_page,
                       ocr_confidence, verified
                FROM verses WHERE source_file = ? AND source_page = ?
                ORDER BY book_id, chapter, verse
                """,
                (source_file, source_page),
            ).fetchall()
        return tuple(self._snapshot(row) for row in rows)

    @staticmethod
    def _validate_reference(book_id: int, chapter: int, verse: int) -> None:
        if not isinstance(book_id, int) or not 1 <= book_id <= len(BOOKS):
            raise ValueError("book_id must be between 1 and 66")
        for name, value in (("chapter", chapter), ("verse", verse)):
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

    @staticmethod
    def _filter_conditions(filters: ReviewFilters) -> tuple[list[str], list[int]]:
        conditions: list[str] = []
        parameters: list[int] = []
        if filters.testament is not None:
            if filters.testament not in {"OT", "NT"}:
                raise ValueError("testament must be OT or NT")
            conditions.append("book_id <= 39" if filters.testament == "OT" else "book_id >= 40")
        if filters.book_id is not None:
            if not isinstance(filters.book_id, int) or not 1 <= filters.book_id <= len(BOOKS):
                raise ValueError("book_id must be between 1 and 66")
            conditions.append("book_id = ?")
            parameters.append(filters.book_id)
        for name, value in (("chapter", filters.chapter), ("source_page", filters.source_page)):
            if value is not None:
                if not isinstance(value, int) or value <= 0:
                    raise ValueError(f"{name} must be a positive integer")
                conditions.append(f"{name} = ?")
                parameters.append(value)
        return conditions, parameters
