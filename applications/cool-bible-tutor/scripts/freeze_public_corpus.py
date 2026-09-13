"""Freeze a reviewed authoring corpus into the immutable public runtime format."""

from __future__ import annotations

import argparse
from contextlib import closing
from dataclasses import replace
import json
import os
from pathlib import Path
import sqlite3
import sys


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = (
    PLUGIN_ROOT / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
)
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from corpus_db import VerseRecord, initialize_database, insert_verses  # noqa: E402
from verify_cuv_index import (  # noqa: E402
    calculate_corpus_structure_sha256,
    load_approved_gaps,
    sha256_file,
    verify_database,
)


PUBLIC_TABLES = {"metadata", "verses"}
PUBLIC_METADATA_KEYS = {
    "schema_version",
    "confidence_threshold",
    "corpus_mode",
}


def _canonical_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _write_text_atomic(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def sqlite_integrity(connection: sqlite3.Connection) -> None:
    result = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise ValueError(f"SQLite integrity check failed: {result}")


def _source_tables(connection: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def _read_public_data(source: Path) -> tuple[dict[str, str], tuple[VerseRecord, ...]]:
    with closing(sqlite3.connect(source)) as connection:
        sqlite_integrity(connection)
        tables = _source_tables(connection)
        forbidden = tables - PUBLIC_TABLES
        missing = PUBLIC_TABLES - tables
        if forbidden:
            raise ValueError(
                "forbidden authoring tables: " + ", ".join(sorted(forbidden))
            )
        if missing:
            raise ValueError("required public tables are missing: " + ", ".join(sorted(missing)))
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        rows = connection.execute(
            """SELECT book_id, chapter, verse, text, source_file, source_page,
                      ocr_confidence, verified
                 FROM verses ORDER BY book_id, chapter, verse"""
        ).fetchall()
    records = tuple(VerseRecord(*row[:-1], bool(row[-1])) for row in rows)
    public_metadata = {
        key: value
        for key, value in metadata.items()
        if key in PUBLIC_METADATA_KEYS or key.startswith("source_sha256:")
    }
    public_metadata["corpus_mode"] = "public_runtime"
    return public_metadata, records


def freeze_public_corpus(
    source: Path,
    destination: Path,
    gap_manifest: Path,
) -> dict:
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    gap_manifest = Path(gap_manifest).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)

    public_metadata, records = _read_public_data(source)
    approved = load_approved_gaps(gap_manifest)
    source_approved = replace(
        approved,
        database_sha256=approved.authoring_database_sha256 or approved.database_sha256,
    )
    source_report = verify_database(source, [], source_approved)
    if not source_report.production_ready:
        raise ValueError("authoring corpus is not production-ready under the approved-gap manifest")

    destination.parent.mkdir(parents=True, exist_ok=True)
    database_temporary = destination.with_name(destination.name + ".building")
    gap_temporary = gap_manifest.with_name(gap_manifest.name + ".building")
    database_temporary.unlink(missing_ok=True)
    gap_temporary.unlink(missing_ok=True)
    try:
        initialize_database(database_temporary)
        with closing(sqlite3.connect(database_temporary)) as connection:
            with connection:
                insert_verses(connection, records)
                connection.executemany(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                    sorted(public_metadata.items()),
                )
            connection.execute("VACUUM")
            sqlite_integrity(connection)

        raw_gap_manifest = json.loads(gap_manifest.read_text(encoding="utf-8"))
        raw_gap_manifest["database_sha256"] = sha256_file(database_temporary)
        gap_temporary.write_text(
            _canonical_json(raw_gap_manifest), encoding="utf-8"
        )
        finalized_approved = load_approved_gaps(gap_temporary)
        frozen_report = verify_database(database_temporary, [], finalized_approved)
        if not frozen_report.production_ready:
            raise ValueError("frozen corpus did not pass the production-ready verification gate")

        runtime_manifest = {
            "schema_version": 1,
            "corpus_schema_version": public_metadata["schema_version"],
            "row_count": len(records),
            "database_sha256": sha256_file(database_temporary),
            "corpus_structure_sha256": calculate_corpus_structure_sha256(
                database_temporary
            ),
            "source_sha256": finalized_approved.source_sha256,
            "approved_gap_sha256": sha256_file(gap_temporary),
            "approved_source_gaps": len(frozen_report.approved_source_gaps),
            "sqlite_integrity": "ok",
        }
        os.replace(database_temporary, destination)
        os.replace(gap_temporary, gap_manifest)
        return runtime_manifest
    finally:
        database_temporary.unlink(missing_ok=True)
        gap_temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None, stdout=None) -> int:
    parser = argparse.ArgumentParser(description="Freeze the public CUV runtime corpus")
    parser.add_argument("source", type=Path)
    parser.add_argument("--gap-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    arguments = parser.parse_args(argv)
    runtime_manifest = freeze_public_corpus(
        arguments.source, arguments.output, arguments.gap_manifest
    )
    _write_text_atomic(arguments.manifest, _canonical_json(runtime_manifest))
    output = sys.stdout if stdout is None else stdout
    print(json.dumps(runtime_manifest, ensure_ascii=True, sort_keys=True), file=output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
