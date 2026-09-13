from dataclasses import dataclass
import hashlib
import hmac
from pathlib import Path
import re
import secrets
import sqlite3


class SourceValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SourceDocument:
    id: str
    filename: str
    path: Path
    size: int
    sha256: str


@dataclass(frozen=True)
class PdfSlice:
    status: int
    start: int
    end: int
    total: int
    content: bytes


class SourceRegistry:
    def __init__(self, documents):
        self._documents = {document.id: document for document in documents}

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @classmethod
    def from_database(
        cls, connection: sqlite3.Connection, paths
    ) -> "SourceRegistry":
        resolved = tuple(Path(path).expanduser().resolve() for path in paths)
        by_name: dict[str, Path] = {}
        for path in resolved:
            if path.name in by_name:
                raise SourceValidationError(f"Duplicate source filename: {path.name}")
            by_name[path.name] = path

        required = {
            row[0] for row in connection.execute(
                "SELECT DISTINCT source_file FROM verses ORDER BY source_file"
            )
        }
        missing = sorted(required - set(by_name))
        extra = sorted(set(by_name) - required)
        if missing:
            raise SourceValidationError(f"Missing corpus source: {missing[0]}")
        if extra:
            raise SourceValidationError(f"Source is not referenced by the corpus: {extra[0]}")

        documents = []
        for filename in sorted(required):
            path = by_name[filename]
            if not path.is_file() or path.suffix.casefold() != ".pdf":
                raise SourceValidationError(f"Source PDF does not exist: {filename}")
            row = connection.execute(
                "SELECT value FROM metadata WHERE key=?",
                (f"source_sha256:{filename}",),
            ).fetchone()
            if row is None:
                raise SourceValidationError(f"Missing stored source hash: {filename}")
            actual = cls._sha256(path)
            if not hmac.compare_digest(str(row[0]).casefold(), actual):
                raise SourceValidationError(f"Source hash mismatch: {filename}")
            documents.append(SourceDocument(
                id=secrets.token_urlsafe(18), filename=filename, path=path,
                size=path.stat().st_size, sha256=actual,
            ))
        return cls(documents)

    def public_sources(self) -> tuple[dict, ...]:
        return tuple(
            {"id": item.id, "filename": item.filename, "size": item.size}
            for item in sorted(self._documents.values(), key=lambda document: document.filename)
        )

    def get(self, source_id: str) -> SourceDocument:
        try:
            return self._documents[source_id]
        except KeyError as error:
            raise SourceValidationError("Unknown source document") from error

    def read_slice(self, source_id: str, range_header: str | None = None) -> PdfSlice:
        document = self.get(source_id)
        total = document.size
        if range_header is None:
            content = document.path.read_bytes()
            return PdfSlice(200, 0, max(total - 1, 0), total, content)

        match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
        if match is None or not any(match.groups()) or "," in range_header:
            raise SourceValidationError("Only one valid byte range is supported")
        first, last = match.groups()
        if total == 0:
            return PdfSlice(416, 0, 0, total, b"")
        if first:
            start = int(first)
            end = int(last) if last else total - 1
            if start >= total or end < start:
                return PdfSlice(416, 0, 0, total, b"")
            end = min(end, total - 1)
        else:
            suffix = int(last)
            if suffix <= 0:
                return PdfSlice(416, 0, 0, total, b"")
            start = max(total - suffix, 0)
            end = total - 1
        with document.path.open("rb") as stream:
            stream.seek(start)
            content = stream.read(end - start + 1)
        return PdfSlice(206, start, end, total, content)
