from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Callable, Iterable

from book_names import BOOKS
from review_store import VerseSnapshot


class ReviewValidationError(ValueError):
    pass


class ReviewConflictError(RuntimeError):
    pass


class BackupError(RuntimeError):
    pass


@dataclass(frozen=True)
class VerseEdit:
    book_id: int
    chapter: int
    verse: int
    text: str
    source_file: str
    source_page: int
    ocr_confidence: float
    verified: bool

    @classmethod
    def from_snapshot(cls, snapshot: VerseSnapshot, **changes) -> "VerseEdit":
        values = asdict(snapshot)
        values.update(changes)
        return cls(**values)

    def as_snapshot(self) -> VerseSnapshot:
        return VerseSnapshot(**asdict(self))


class ReviewMutator:
    def __init__(self, database, data_dir, session_id, allowed_sources):
        self.database = Path(database).resolve()
        self.data_dir = Path(data_dir).resolve()
        self.history_database = self.data_dir / "cuv-review-history.sqlite3"
        self.session_id = str(session_id)
        self.allowed_sources = frozenset(str(source) for source in allowed_sources)
        self._backup_path: Path | None = None

    @property
    def backup_created(self) -> bool:
        return self._backup_path is not None and self._backup_path.is_file()

    @staticmethod
    def _utc_stamp() -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")

    @staticmethod
    def _utc_iso() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _ensure_backup(self) -> Path:
        if self._backup_path is not None:
            return self._backup_path
        backup_dir = (self.data_dir / "backups").resolve()
        if self.data_dir != backup_dir and self.data_dir not in backup_dir.parents:
            raise BackupError("Backup directory escaped the private data directory")
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            target = backup_dir / f"cuv-before-review-{self._utc_stamp()}.sqlite3"
            with closing(sqlite3.connect(self.database)) as source:
                with closing(sqlite3.connect(target)) as destination:
                    source.backup(destination)
        except (OSError, sqlite3.Error) as error:
            raise BackupError(f"Could not create corpus backup: {error}") from error
        self._backup_path = target
        return target

    def _validate_edit(self, edit: VerseEdit) -> None:
        if not isinstance(edit.book_id, int) or not 1 <= edit.book_id <= len(BOOKS):
            raise ReviewValidationError("book_id must be between 1 and 66")
        for name, value in (("chapter", edit.chapter), ("verse", edit.verse), ("source_page", edit.source_page)):
            if not isinstance(value, int) or value <= 0:
                raise ReviewValidationError(f"{name} must be a positive integer")
        if not isinstance(edit.text, str) or not edit.text.strip():
            raise ReviewValidationError("text must not be blank")
        if edit.source_file not in self.allowed_sources:
            raise ReviewValidationError("source_file is not registered for this review session")
        if not isinstance(edit.ocr_confidence, (int, float)) or not 0 <= edit.ocr_confidence <= 100:
            raise ReviewValidationError("ocr_confidence must be between 0 and 100")
        if not isinstance(edit.verified, bool):
            raise ReviewValidationError("verified must be boolean")

    @staticmethod
    def _expected_values(snapshot: VerseSnapshot) -> tuple:
        return (
            snapshot.book_id, snapshot.chapter, snapshot.verse, snapshot.text,
            snapshot.source_file, snapshot.source_page, snapshot.ocr_confidence,
            int(snapshot.verified),
        )

    def _initialize_history(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS review_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                session_id TEXT NOT NULL,
                status TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT NOT NULL,
                before_json TEXT NOT NULL,
                after_json TEXT NOT NULL,
                note TEXT NOT NULL
            )
            """
        )

    def _prepare_history(self, action: str, before, after, note: str) -> int:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.history_database)) as connection:
            with connection:
                self._initialize_history(connection)
                cursor = connection.execute(
                    """
                    INSERT INTO review_history(
                        timestamp_utc, session_id, status, action, target,
                        before_json, after_json, note
                    ) VALUES (?, ?, 'prepared', ?, ?, ?, ?, ?)
                    """,
                    (
                        self._utc_iso(), self.session_id, action,
                        json.dumps(self._targets(after), ensure_ascii=False, sort_keys=True),
                        json.dumps(before, ensure_ascii=False, sort_keys=True),
                        json.dumps(after, ensure_ascii=False, sort_keys=True), str(note),
                    ),
                )
                return int(cursor.lastrowid)

    @staticmethod
    def _targets(payload) -> list[dict]:
        rows = payload if isinstance(payload, list) else [payload]
        return [
            {key: row[key] for key in ("book_id", "chapter", "verse")}
            for row in rows
        ]

    def _commit_history(self, history_id: int) -> None:
        with closing(sqlite3.connect(self.history_database)) as connection:
            with connection:
                connection.execute(
                    "UPDATE review_history SET status='committed' WHERE id=?",
                    (history_id,),
                )

    def _write(
        self,
        action: str,
        before: list[dict],
        after: list[dict],
        note: str,
        operation: Callable[[sqlite3.Connection], None],
    ) -> None:
        self._ensure_backup()
        history_id = self._prepare_history(action, before, after, note)
        with closing(sqlite3.connect(self.database)) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                operation(connection)
                now = self._utc_iso()
                connection.executemany(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                    (("rag_index_state", "stale"), ("rag_index_stale_at", now)),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        self._commit_history(history_id)

    def update_verse(
        self, expected: VerseSnapshot, replacement: VerseEdit, note: str = ""
    ) -> VerseSnapshot:
        self._validate_edit(replacement)
        if (expected.book_id, expected.chapter, expected.verse) != (
            replacement.book_id, replacement.chapter, replacement.verse
        ):
            raise ReviewValidationError("An update cannot change the verse key")

        def operation(connection: sqlite3.Connection) -> None:
            cursor = connection.execute(
                """
                UPDATE verses
                SET text=?, source_file=?, source_page=?, ocr_confidence=?, verified=?
                WHERE book_id=? AND chapter=? AND verse=? AND text=?
                  AND source_file=? AND source_page=? AND ocr_confidence=? AND verified=?
                """,
                (
                    replacement.text, replacement.source_file, replacement.source_page,
                    replacement.ocr_confidence, int(replacement.verified),
                    *self._expected_values(expected),
                ),
            )
            if cursor.rowcount != 1:
                raise ReviewConflictError("The verse changed after it was loaded")

        self._write(
            "update_verse", [expected.as_dict()], [replacement.as_snapshot().as_dict()], note, operation
        )
        return replacement.as_snapshot()

    def set_verification(
        self, expected_rows: Iterable[VerseSnapshot], verified: bool, note: str = ""
    ) -> tuple[VerseSnapshot, ...]:
        if not isinstance(verified, bool):
            raise ReviewValidationError("verified must be boolean")
        expected = tuple(expected_rows)
        if not expected:
            raise ReviewValidationError("At least one verse is required")
        replacements = tuple(VerseEdit.from_snapshot(row, verified=verified) for row in expected)
        for replacement in replacements:
            self._validate_edit(replacement)

        def operation(connection: sqlite3.Connection) -> None:
            for row in expected:
                cursor = connection.execute(
                    """
                    UPDATE verses SET verified=?
                    WHERE book_id=? AND chapter=? AND verse=? AND text=?
                      AND source_file=? AND source_page=? AND ocr_confidence=? AND verified=?
                    """,
                    (int(verified), *self._expected_values(row)),
                )
                if cursor.rowcount != 1:
                    raise ReviewConflictError("A verse changed after it was loaded")

        self._write(
            "set_verification", [row.as_dict() for row in expected],
            [row.as_snapshot().as_dict() for row in replacements], note, operation,
        )
        return tuple(row.as_snapshot() for row in replacements)

    def insert_verse(self, replacement: VerseEdit, note: str = "") -> VerseSnapshot:
        self._validate_edit(replacement)
        if replacement.verified is not True:
            raise ReviewValidationError("Inserted verses require explicit human verification")

        def operation(connection: sqlite3.Connection) -> None:
            try:
                connection.execute(
                    """
                    INSERT INTO verses(
                        book_id, chapter, verse, text, source_file, source_page,
                        ocr_confidence, verified
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        replacement.book_id, replacement.chapter, replacement.verse,
                        replacement.text, replacement.source_file, replacement.source_page,
                        replacement.ocr_confidence, int(replacement.verified),
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise ReviewConflictError("The verse key is already indexed") from error

        after = replacement.as_snapshot()
        self._write("insert_verse", [], [after.as_dict()], note, operation)
        return after

    def verify_page(
        self, expected_rows: Iterable[VerseSnapshot], note: str = ""
    ) -> tuple[VerseSnapshot, ...]:
        expected = tuple(expected_rows)
        if not expected:
            raise ReviewValidationError("A non-empty source page is required")
        page_keys = {(row.source_file, row.source_page) for row in expected}
        if len(page_keys) != 1:
            raise ReviewValidationError("All expected verses must belong to one source page")
        source_file, source_page = next(iter(page_keys))
        if source_file not in self.allowed_sources:
            raise ReviewValidationError("source_file is not registered for this review session")
        replacements = tuple(VerseEdit.from_snapshot(row, verified=True) for row in expected)

        def operation(connection: sqlite3.Connection) -> None:
            rows = connection.execute(
                """
                SELECT book_id, chapter, verse, text, source_file, source_page,
                       ocr_confidence, verified
                FROM verses WHERE source_file=? AND source_page=?
                ORDER BY book_id, chapter, verse
                """,
                (source_file, source_page),
            ).fetchall()
            current = tuple(
                VerseSnapshot(*row[:-1], bool(row[-1])) for row in rows
            )
            if current != expected:
                raise ReviewConflictError("The source page changed after it was loaded")
            cursor = connection.execute(
                "UPDATE verses SET verified=1 WHERE source_file=? AND source_page=?",
                (source_file, source_page),
            )
            if cursor.rowcount != len(expected):
                raise ReviewConflictError("The complete source page could not be verified")

        self._write(
            "verify_page", [row.as_dict() for row in expected],
            [row.as_snapshot().as_dict() for row in replacements], note, operation,
        )
        return tuple(row.as_snapshot() for row in replacements)

    def history(self, limit: int = 100, offset: int = 0) -> list[dict]:
        if not self.history_database.exists():
            return []
        if not isinstance(limit, int) or not 1 <= limit <= 1000 or not isinstance(offset, int) or offset < 0:
            raise ReviewValidationError("Invalid history pagination")
        with closing(sqlite3.connect(self.history_database)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT * FROM review_history ORDER BY id LIMIT ? OFFSET ?", (limit, offset)
            ).fetchall()
        return [dict(row) for row in rows]
