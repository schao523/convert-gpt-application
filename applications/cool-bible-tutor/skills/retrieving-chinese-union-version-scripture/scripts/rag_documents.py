from collections import defaultdict
from collections.abc import Mapping, Sequence
import hashlib
import json
import sqlite3

from book_names import BOOKS
from corpus_db import VerseRecord


APP_ID = "cool-bible-tutor"


def corpus_structure_sha256(records: Sequence[VerseRecord]) -> str:
    digest = hashlib.sha256()
    for record in sorted(records, key=lambda item: (item.book_id, item.chapter, item.verse)):
        digest.update(f"{record.book_id}:{record.chapter}:{record.verse}\n".encode("ascii"))
    return digest.hexdigest()


def corpus_fingerprint(
    records: Sequence[VerseRecord], source_hashes: Mapping[str, str]
) -> str:
    digest = hashlib.sha256()
    for record in sorted(records, key=lambda item: (item.book_id, item.chapter, item.verse)):
        digest.update(json.dumps(
            (
                record.book_id, record.chapter, record.verse, record.text,
                record.source_file, record.source_page, record.ocr_confidence,
                bool(record.verified),
            ),
            ensure_ascii=False, separators=(",", ":"),
        ).encode("utf-8"))
        digest.update(b"\n")
    for filename, source_digest in sorted(source_hashes.items()):
        digest.update(filename.encode("utf-8"))
        digest.update(b"=")
        digest.update(source_digest.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def read_corpus(
    connection: sqlite3.Connection,
    book_id: int | None = None,
    chapter: int | None = None,
) -> tuple[dict[str, str], tuple[VerseRecord, ...]]:
    if chapter is not None and book_id is None:
        raise ValueError("chapter requires book_id")

    metadata = dict(connection.execute("SELECT key, value FROM metadata"))
    sql = (
        "SELECT book_id, chapter, verse, text, source_file, source_page, "
        "ocr_confidence, verified FROM verses"
    )
    clauses: list[str] = []
    parameters: list[int] = []
    if book_id is not None:
        clauses.append("book_id = ?")
        parameters.append(book_id)
    if chapter is not None:
        clauses.append("chapter = ?")
        parameters.append(chapter)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY book_id, chapter, verse"

    rows = connection.execute(sql, parameters).fetchall()
    records = tuple(VerseRecord(*row[:-1], bool(row[-1])) for row in rows)
    source_hashes = {
        key.split(":", 1)[1]: value
        for key, value in metadata.items()
        if key.startswith("source_sha256:")
    }
    return source_hashes, records


def build_rag_documents(
    records: Sequence[VerseRecord],
    source_hashes: Mapping[str, str],
    window_size: int = 5,
    overlap: int = 2,
) -> list[dict]:
    if window_size <= 0 or overlap < 0 or overlap >= window_size:
        raise ValueError("window_size must be positive and overlap must be smaller")
    if not source_hashes:
        raise ValueError("source hashes are required")

    chapters: dict[tuple[int, int], list[VerseRecord]] = defaultdict(list)
    for record in sorted(records, key=lambda item: (item.book_id, item.chapter, item.verse)):
        chapters[(record.book_id, record.chapter)].append(record)

    documents: list[dict] = []
    step = window_size - overlap
    for (book_id, chapter), chapter_records in sorted(chapters.items()):
        if not 1 <= book_id <= len(BOOKS):
            raise ValueError(f"unknown book id: {book_id}")
        book = BOOKS[book_id - 1]

        runs: list[list[VerseRecord]] = []
        current: list[VerseRecord] = []
        for record in chapter_records:
            if current and record.verse != current[-1].verse + 1:
                runs.append(current)
                current = []
            current.append(record)
        if current:
            runs.append(current)

        blocks: list[dict] = []
        for run in runs:
            start = 0
            while start < len(run):
                window = run[start:start + window_size]
                first, last = window[0], window[-1]
                reference = f"{book.abbreviation_zh}{chapter}:{first.verse}"
                if first.verse != last.verse:
                    reference += f"-{last.verse}"
                files = sorted({record.source_file for record in window})
                missing_hashes = [name for name in files if name not in source_hashes]
                if missing_hashes:
                    raise ValueError(f"missing source hash for {', '.join(missing_hashes)}")
                metadata = {
                    "app_id": APP_ID,
                    "corpus": "cuv-private",
                    "book_id": str(book_id),
                    "book_name": book.canonical_zh,
                    "chapter": str(chapter),
                    "canonical_reference": reference,
                    "start_verse": str(first.verse),
                    "end_verse": str(last.verse),
                    "verified_all": str(all(record.verified for record in window)).lower(),
                    "unverified_count": str(sum(not record.verified for record in window)),
                    "source_files": ",".join(files),
                    "source_pages": ",".join(
                        str(page) for page in sorted({record.source_page for record in window})
                    ),
                    "source_hashes": ";".join(
                        f"{name}={source_hashes[name]}" for name in files
                    ),
                }
                blocks.append({
                    "type": "text",
                    "text": "\n".join(
                        f"{record.chapter}:{record.verse} {record.text}" for record in window
                    ),
                    "section_path": reference,
                    "metadata": metadata,
                })
                if start + window_size >= len(run):
                    break
                start += step

        documents.append({"doc_id": f"cuv:{book_id}:{chapter}", "blocks": blocks})
    return documents
