import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess

from book_names import resolve_book
from corpus_db import DATABASE_NAME, VerseRecord, initialize_database, insert_verses
from ocr_adapter import OcrPage, extract_pdf_pages, ocr_page, render_page
from scripture_sources import SourceValidationError, resolve_bundled_sources


STATE_NAME = "build-state.json"
BUILDING_DATABASE_NAME = ".cuv-building.sqlite3"
_VERSE_LINE = re.compile(r"^(.+?)\s*(\d+)\s*[:：]\s*(\d+)\s*(.+)$")
_PAGE_NUMBER = re.compile(r"^-?\s*\d+\s*-?$")


def resolve_testament_sources(
    old_testament: Path | None, new_testament: Path | None
) -> tuple[Path, Path]:
    if old_testament is None and new_testament is None:
        return resolve_bundled_sources()
    if old_testament is None or new_testament is None:
        raise ValueError("--old-testament and --new-testament must be supplied together")
    return Path(old_testament).resolve(), Path(new_testament).resolve()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pdf_page_count(pdf: Path, executable: str = "pdfinfo") -> int:
    result = subprocess.run(
        [executable, str(pdf)], check=True, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not determine PDF page count: {pdf}")
    return int(match.group(1))


def _is_page_furniture(text: str) -> bool:
    return bool(
        _PAGE_NUMBER.fullmatch(text)
        or "國際聖經協會" in text
        or ("全書" in text and "和合本" in text)
        or text.startswith(("http://", "https://"))
    )


def parse_pages(pages: tuple[OcrPage, ...], source_pdf: Path) -> list[VerseRecord]:
    pending: list[dict] = []
    for page in pages:
        for line in page.lines:
            text = line.text.strip()
            if not text or _is_page_furniture(text):
                continue
            match = _VERSE_LINE.match(text)
            if match:
                try:
                    book = resolve_book(match.group(1).strip())
                except ValueError:
                    match = None
            if match:
                pending.append(
                    {
                        "book_id": book.id,
                        "chapter": int(match.group(2)),
                        "verse": int(match.group(3)),
                        "parts": [match.group(4).strip()],
                        "confidences": [line.confidence],
                        "source_page": page.page_number,
                    }
                )
            elif pending:
                pending[-1]["parts"].append(text)
                pending[-1]["confidences"].append(line.confidence)

    records = []
    for item in pending:
        confidences = item["confidences"]
        records.append(
            VerseRecord(
                item["book_id"], item["chapter"], item["verse"],
                "".join(item["parts"]), Path(source_pdf).name, item["source_page"],
                round(sum(confidences) / len(confidences), 2), False,
            )
        )
    return records


def parse_ocr_lines(page: OcrPage, source_pdf: Path) -> list[VerseRecord]:
    return parse_pages((page,), source_pdf)


def _load_or_reset_state(data_dir: Path, sources: dict[str, str]) -> dict:
    state_path = data_dir / STATE_NAME
    building = data_dir / BUILDING_DATABASE_NAME
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("sources") == sources and building.is_file():
            return state
    state_path.unlink(missing_ok=True)
    building.unlink(missing_ok=True)
    state = {"sources": sources, "completed": {"old": [], "new": []}}
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def _save_state(path: Path, state: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def build_index(
    old_testament: Path,
    new_testament: Path,
    data_dir: Path,
    *,
    pdftoppm: str = "pdftoppm",
    pdftotext: str = "pdftotext",
    pdfinfo: str = "pdfinfo",
    tesseract: str = "tesseract",
    language: str = "chi_tra",
    tessdata_dir: Path | None = None,
    scratch_dir: Path | None = None,
    dpi: int = 300,
) -> Path:
    old_testament = Path(old_testament).resolve()
    new_testament = Path(new_testament).resolve()
    data_dir = Path(data_dir).resolve()
    scratch_dir = Path(scratch_dir).resolve() if scratch_dir is not None else data_dir
    for source in (old_testament, new_testament):
        if not source.is_file():
            raise FileNotFoundError(source)
    data_dir.mkdir(parents=True, exist_ok=True)
    scratch_dir.mkdir(parents=True, exist_ok=True)
    sources = {"old": sha256_file(old_testament), "new": sha256_file(new_testament)}
    state = _load_or_reset_state(data_dir, sources)
    state_path = data_dir / STATE_NAME
    building = data_dir / BUILDING_DATABASE_NAME
    target = data_dir / DATABASE_NAME
    if not building.is_file():
        initialize_database(building)

    try:
        for label, source in (("old", old_testament), ("new", new_testament)):
            count = pdf_page_count(source, executable=pdfinfo)
            completed = set(state["completed"][label])
            if len(completed) < count:
                try:
                    embedded_pages = extract_pdf_pages(source, executable=pdftotext)
                except (OSError, subprocess.SubprocessError):
                    embedded_pages = ()
                embedded_records = parse_pages(embedded_pages, source) if embedded_pages else []
                if embedded_records:
                    first_book, last_book = (1, 39) if label == "old" else (40, 66)
                    with closing(sqlite3.connect(building)) as connection:
                        with connection:
                            connection.execute(
                                "DELETE FROM verses WHERE book_id BETWEEN ? AND ?",
                                (first_book, last_book),
                            )
                            insert_verses(connection, embedded_records)
                    state["completed"][label] = list(range(1, count + 1))
                    _save_state(state_path, state)
                    continue
            for page_number in range(1, count + 1):
                if page_number in completed:
                    continue
                image = scratch_dir / f"page-{label}-{page_number}.png"
                try:
                    render_page(source, page_number, image, dpi=dpi, executable=pdftoppm)
                    page = ocr_page(
                        image, page_number=page_number, language=language,
                        executable=tesseract, tessdata_dir=tessdata_dir,
                    )
                    records = parse_ocr_lines(page, source)
                    with closing(sqlite3.connect(building)) as connection:
                        with connection:
                            insert_verses(connection, records)
                    state["completed"][label].append(page_number)
                    _save_state(state_path, state)
                finally:
                    image.unlink(missing_ok=True)

        with closing(sqlite3.connect(building)) as connection:
            with connection:
                connection.executemany(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                    (
                        ("old_testament_sha256", sources["old"]),
                        ("new_testament_sha256", sources["new"]),
                        (f"source_sha256:{old_testament.name}", sources["old"]),
                        (f"source_sha256:{new_testament.name}", sources["new"]),
                        ("corpus_mode", "production_candidate"),
                    ),
                )
                count = connection.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
        if count == 0:
            raise RuntimeError("OCR completed but no verse-labelled text was parsed")
        os.replace(building, target)
        state_path.unlink(missing_ok=True)
        return target
    except Exception:
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a private CUV SQLite index")
    parser.add_argument("--old-testament", type=Path)
    parser.add_argument("--new-testament", type=Path)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--pdftoppm", default="pdftoppm")
    parser.add_argument("--pdftotext", default="pdftotext")
    parser.add_argument("--pdfinfo", default="pdfinfo")
    parser.add_argument("--tesseract", default="tesseract")
    parser.add_argument("--language", default="chi_tra")
    parser.add_argument("--tessdata-dir", type=Path)
    parser.add_argument("--scratch-dir", type=Path)
    parser.add_argument("--dpi", type=int, default=300)
    arguments = parser.parse_args(argv)
    try:
        old_testament, new_testament = resolve_testament_sources(
            arguments.old_testament, arguments.new_testament
        )
    except (SourceValidationError, ValueError) as error:
        parser.error(str(error))
    result = build_index(
        old_testament, new_testament, arguments.data_dir,
        pdftoppm=arguments.pdftoppm, pdfinfo=arguments.pdfinfo,
        pdftotext=arguments.pdftotext,
        tesseract=arguments.tesseract, language=arguments.language, dpi=arguments.dpi,
        tessdata_dir=arguments.tessdata_dir,
        scratch_dir=arguments.scratch_dir,
    )
    print(f"Build completed: {result.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
