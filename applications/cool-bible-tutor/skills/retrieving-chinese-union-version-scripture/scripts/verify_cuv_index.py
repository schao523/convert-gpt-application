import argparse
from contextlib import closing
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from corpus_db import DEFAULT_CONFIDENCE_THRESHOLD, SCHEMA_VERSION
from scripture_sources import resolve_bundled_sources


@dataclass(frozen=True)
class VerificationIssue:
    code: str
    reference: str | None
    detail: str
    severity: str


@dataclass(frozen=True)
class ApprovedGapManifest:
    source_sha256: dict[str, str]
    database_sha256: str
    corpus_structure_sha256: str
    row_count: int
    gaps: tuple[str, ...]
    authoring_database_sha256: str | None = None


@dataclass(frozen=True)
class VerificationReport:
    issues: tuple[VerificationIssue, ...]
    production_ready: bool
    approved_source_gaps: tuple[str, ...] = ()

    @property
    def exit_status(self) -> int:
        severities = {issue.severity for issue in self.issues}
        if "error" in severities:
            return 2
        if "warning" in severities:
            return 1
        return 0

    @property
    def counts(self) -> dict[str, int]:
        return {
            severity: sum(issue.severity == severity for issue in self.issues)
            for severity in ("error", "warning")
        }


def resolve_verification_sources(source_pdfs: list[Path]) -> tuple[Path, ...]:
    if source_pdfs:
        return tuple(Path(source).expanduser().resolve() for source in source_pdfs)
    return resolve_bundled_sources()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def calculate_corpus_structure_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with closing(sqlite3.connect(Path(path))) as connection:
        rows = connection.execute(
            "SELECT book_id, chapter, verse FROM verses ORDER BY book_id, chapter, verse"
        )
        for book_id, chapter, verse in rows:
            digest.update(f"{book_id}:{chapter}:{verse}\n".encode("ascii"))
    return digest.hexdigest()


def _require_sha256(value: object, field: str) -> str:
    normalized = str(value or "").lower()
    if not re.fullmatch(r"[0-9a-f]{64}", normalized):
        raise ValueError(f"{field} must be a SHA-256 digest")
    return normalized


def _gap_sort_key(reference: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"([1-9]\d*) ([1-9]\d*):([1-9]\d*)", reference)
    if match is None:
        raise ValueError(f"invalid approved gap reference: {reference!r}")
    return tuple(map(int, match.groups()))


def load_approved_gaps(path: Path) -> ApprovedGapManifest:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("invalid approved-gap manifest") from error
    if not isinstance(payload, dict):
        raise ValueError("invalid approved-gap manifest")
    sources = payload.get("source_sha256")
    gaps = payload.get("gaps")
    if not isinstance(sources, dict) or not isinstance(gaps, list):
        raise ValueError("invalid approved-gap manifest")
    normalized_sources = {
        str(name): _require_sha256(digest, f"source_sha256:{name}")
        for name, digest in sources.items()
    }
    normalized_gaps = tuple(str(reference) for reference in gaps)
    sorted_gaps = tuple(sorted(normalized_gaps, key=_gap_sort_key))
    if normalized_gaps != sorted_gaps or len(set(normalized_gaps)) != len(normalized_gaps):
        raise ValueError("approved gaps must be unique and canonically sorted")
    try:
        row_count = int(payload["row_count"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("row_count must be an integer") from error
    if row_count <= 0:
        raise ValueError("row_count must be positive")
    database_sha256 = _require_sha256(payload.get("database_sha256"), "database_sha256")
    authoring_database_sha256 = _require_sha256(
        payload.get("authoring_database_sha256", database_sha256),
        "authoring_database_sha256",
    )
    return ApprovedGapManifest(
        source_sha256=normalized_sources,
        database_sha256=database_sha256,
        corpus_structure_sha256=_require_sha256(
            payload.get("corpus_structure_sha256"), "corpus_structure_sha256"
        ),
        row_count=row_count,
        gaps=normalized_gaps,
        authoring_database_sha256=authoring_database_sha256,
    )


def _manifest_identity_matches(
    manifest: ApprovedGapManifest,
    path: Path,
    metadata: dict[str, str],
    rows: list[tuple],
) -> bool:
    stored_sources = {
        key.split(":", 1)[1]: value.lower()
        for key, value in metadata.items()
        if key.startswith("source_sha256:")
    }
    return (
        sha256_file(path) == manifest.database_sha256
        and len(rows) == manifest.row_count
        and calculate_corpus_structure_sha256(path) == manifest.corpus_structure_sha256
        and stored_sources == manifest.source_sha256
    )


def verify_database(
    path: Path,
    source_pdfs: list[Path],
    approved_gaps: ApprovedGapManifest | None = None,
) -> VerificationReport:
    path = Path(path)
    issues: list[VerificationIssue] = []
    if not path.is_file():
        issue = VerificationIssue("missing_database", None, f"Database not found: {path}", "error")
        return VerificationReport((issue,), False)
    try:
        with closing(sqlite3.connect(path)) as connection:
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            if not {"metadata", "verses"}.issubset(tables):
                issue = VerificationIssue("invalid_schema", None, "Required tables are missing", "error")
                return VerificationReport((issue,), False)
            metadata = dict(connection.execute("SELECT key, value FROM metadata"))
            if metadata.get("schema_version") != SCHEMA_VERSION:
                issues.append(VerificationIssue(
                    "schema_version", None,
                    f"Expected schema {SCHEMA_VERSION}; found {metadata.get('schema_version')!r}", "error",
                ))
            try:
                threshold = float(metadata.get("confidence_threshold", DEFAULT_CONFIDENCE_THRESHOLD))
            except ValueError:
                threshold = DEFAULT_CONFIDENCE_THRESHOLD
                issues.append(VerificationIssue(
                    "invalid_threshold", None, "Confidence threshold is not numeric", "error"
                ))
            rows = connection.execute(
                """SELECT book_id, chapter, verse, text, source_file, source_page,
                          ocr_confidence, verified FROM verses
                   ORDER BY book_id, chapter, verse"""
            ).fetchall()
            duplicate_rows = connection.execute(
                """SELECT book_id, chapter, verse, COUNT(*) FROM verses
                   GROUP BY book_id, chapter, verse HAVING COUNT(*) > 1"""
            ).fetchall()
    except sqlite3.Error as error:
        issue = VerificationIssue("invalid_schema", None, str(error), "error")
        return VerificationReport((issue,), False)

    for book_id, chapter, verse, _ in duplicate_rows:
        issues.append(VerificationIssue(
            "duplicate_verse", f"{book_id} {chapter}:{verse}", "Duplicate verse key", "error"
        ))

    present_books = set()
    previous_by_chapter: dict[tuple[int, int], int] = {}
    gap_issues: list[VerificationIssue] = []
    observed_gaps: list[str] = []
    for book_id, chapter, verse, text, source_file, source_page, confidence, verified in rows:
        reference = f"{book_id} {chapter}:{verse}"
        if not 1 <= book_id <= 66:
            issues.append(VerificationIssue("invalid_book_id", reference, str(book_id), "error"))
        else:
            present_books.add(book_id)
        if chapter <= 0 or verse <= 0:
            issues.append(VerificationIssue("invalid_reference", reference, "Non-positive chapter or verse", "error"))
        if not str(text).strip():
            issues.append(VerificationIssue("empty_text", reference, "Verse text is empty", "error"))
        if source_page <= 0:
            issues.append(VerificationIssue("invalid_source_page", reference, str(source_page), "error"))
        if not 0 <= confidence <= 100:
            issues.append(VerificationIssue("invalid_confidence", reference, str(confidence), "error"))
        elif confidence < threshold:
            issues.append(VerificationIssue("low_confidence", reference, str(confidence), "warning"))
        if verified not in (1, True):
            issues.append(VerificationIssue("unverified", reference, "Verse has not been reviewed", "warning"))
        key = (book_id, chapter)
        previous = previous_by_chapter.get(key)
        if previous is not None and verse != previous + 1:
            missing_verse = previous + 1
            observed_gaps.append(f"{book_id} {chapter}:{missing_verse}")
            gap_issues.append(VerificationIssue(
                "verse_gap", reference, f"Expected verse {missing_verse}", "warning"
            ))
        previous_by_chapter[key] = verse

    mode = metadata.get("corpus_mode", "production_candidate")
    if mode == "fixture":
        issues.append(VerificationIssue(
            "fixture_mode", None, "Fixture corpora are never production-ready", "warning"
        ))
    else:
        for book_id in sorted(set(range(1, 67)) - present_books):
            issues.append(VerificationIssue(
                "missing_book", str(book_id), "Canonical book has no indexed verses", "error"
            ))

    for source in map(Path, source_pdfs):
        if not source.is_file():
            issues.append(VerificationIssue(
                "missing_source", None, f"Source PDF not found: {source}", "error"
            ))
            continue
        expected = metadata.get(f"source_sha256:{source.name}")
        actual = sha256_file(source)
        if expected is None:
            issues.append(VerificationIssue(
                "missing_source_hash", None, source.name, "error"
            ))
        elif expected != actual:
            issues.append(VerificationIssue(
                "source_hash_mismatch", None, source.name, "error"
            ))

    approved_source_gaps: tuple[str, ...] = ()
    if approved_gaps is None:
        issues.extend(gap_issues)
    else:
        manifest_sources_match = all(
            source.is_file()
            and approved_gaps.source_sha256.get(source.name) == sha256_file(source)
            for source in map(Path, source_pdfs)
        )
        exact_gap_set = tuple(observed_gaps) == approved_gaps.gaps
        if (
            exact_gap_set
            and manifest_sources_match
            and _manifest_identity_matches(approved_gaps, path, metadata, rows)
        ):
            approved_source_gaps = tuple(observed_gaps)
        else:
            issues.extend(gap_issues)
            issues.append(VerificationIssue(
                "approved_gap_manifest_mismatch", None,
                "Observed corpus identity or source gaps do not exactly match the approved manifest",
                "warning",
            ))

    issues.sort(key=lambda item: (item.severity != "error", item.code, item.reference or ""))
    production_ready = mode != "fixture" and len(present_books) == 66 and not issues
    return VerificationReport(tuple(issues), production_ready, approved_source_gaps)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a private CUV index")
    parser.add_argument("database", type=Path)
    parser.add_argument("--source-pdf", action="append", type=Path, default=[])
    parser.add_argument("--approved-gaps", type=Path)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args(argv)
    report = verify_database(
        arguments.database,
        list(resolve_verification_sources(arguments.source_pdf)),
        load_approved_gaps(arguments.approved_gaps) if arguments.approved_gaps else None,
    )
    if arguments.json:
        print(json.dumps({
            "production_ready": report.production_ready,
            "counts": report.counts,
            "approved_source_gaps": list(report.approved_source_gaps),
            "issues": [asdict(issue) for issue in report.issues],
        }, ensure_ascii=False, indent=2))
    else:
        for issue in report.issues:
            where = f" [{issue.reference}]" if issue.reference else ""
            print(f"{issue.severity.upper()} {issue.code}{where}: {issue.detail}")
        print(f"production_ready={str(report.production_ready).lower()}")
    return report.exit_status


if __name__ == "__main__":
    raise SystemExit(main())
