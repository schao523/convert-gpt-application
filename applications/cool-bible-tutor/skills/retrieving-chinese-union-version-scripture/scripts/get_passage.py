import argparse
from contextlib import closing
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
import sys

from corpus_db import fetch_passage, open_corpus_read_only, resolve_database
from references import parse_reference


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Retrieve a passage from a private CUV index")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser


def _json_payload(passage):
    return {
        "canonical_reference": passage.canonical_reference,
        "trust_status": "verified" if passage.verified else "unverified",
        "confidence_threshold": passage.confidence_threshold,
        "verses": [asdict(record) for record in passage.records],
    }


def _print_text(passage) -> None:
    status = "已核實" if passage.verified else "未核實：不可當作精確引文"
    print(f"{passage.canonical_reference} [{status}]")
    for record in passage.records:
        print(f"{record.chapter}:{record.verse} {record.text}")
        print(
            f"  來源：{record.source_file}，頁 {record.source_page}，"
            f"OCR 信心 {record.ocr_confidence:.1f}"
        )


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        request = parse_reference(arguments.reference)
    except ValueError as error:
        print(f"無效經文引用：{error}", file=sys.stderr)
        return 2

    database = resolve_database(arguments.data_dir)
    if not database.is_file():
        print(
            "找不到私有和合本索引。請以 build_cuv_index.py --data-dir <目錄> "
            "從內附來源建立索引，或貼上要查考的經文。",
            file=sys.stderr,
        )
        return 2
    try:
        with closing(open_corpus_read_only(database)) as connection:
            passage = fetch_passage(connection, request)
    except (sqlite3.Error, LookupError) as error:
        print(f"無法取得經文：{error}", file=sys.stderr)
        return 2

    if arguments.format == "json":
        print(json.dumps(_json_payload(passage), ensure_ascii=False, indent=2))
    else:
        _print_text(passage)
    return 0 if passage.verified else 3


if __name__ == "__main__":
    raise SystemExit(main())
