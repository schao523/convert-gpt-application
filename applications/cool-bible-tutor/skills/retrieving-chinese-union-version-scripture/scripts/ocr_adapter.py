from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class OcrLine:
    text: str
    confidence: float


@dataclass(frozen=True)
class OcrPage:
    page_number: int
    lines: tuple[OcrLine, ...]


def extract_pdf_pages(
    pdf: Path,
    executable: str = "pdftotext",
) -> tuple[OcrPage, ...]:
    command = [
        executable, "-layout", "-enc", "UTF-8", str(pdf), "-",
    ]
    result = subprocess.run(
        command, check=True, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    raw_pages = result.stdout.split("\f")
    if raw_pages and not raw_pages[-1].strip():
        raw_pages.pop()
    return tuple(
        OcrPage(
            page_number,
            tuple(OcrLine(line.strip(), 100.0) for line in raw.splitlines() if line.strip()),
        )
        for page_number, raw in enumerate(raw_pages, start=1)
    )


def render_page(
    pdf: Path,
    page: int,
    output_png: Path,
    dpi: int = 300,
    executable: str = "pdftoppm",
) -> None:
    output_png = Path(output_png)
    output_png.parent.mkdir(parents=True, exist_ok=True)
    command = [
        executable, "-f", str(page), "-l", str(page), "-r", str(dpi),
        "-png", "-singlefile", str(pdf), str(output_png.with_suffix("")),
    ]
    subprocess.run(
        command, check=True, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def ocr_page(
    image: Path,
    page_number: int,
    language: str = "chi_tra",
    executable: str = "tesseract",
    tessdata_dir: Path | None = None,
) -> OcrPage:
    command = [executable, str(image), "stdout"]
    if tessdata_dir is not None:
        command.extend(["--tessdata-dir", str(tessdata_dir)])
    command.extend(["-l", language, "-c", "tessedit_create_tsv=1"])
    result = subprocess.run(
        command, check=True, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    rows = result.stdout.splitlines()
    if not rows:
        return OcrPage(page_number, ())
    header_index = next(
        (index for index, row in enumerate(rows) if row.startswith("level\tpage_num\t")),
        None,
    )
    if header_index is None:
        raise RuntimeError("Tesseract did not return TSV output")
    rows = rows[header_index:]
    headers = rows[0].split("\t")
    columns = {name: index for index, name in enumerate(headers)}
    groups: dict[tuple[str, str, str, str], list[tuple[str, float]]] = {}
    for row in rows[1:]:
        fields = row.split("\t")
        if len(fields) < len(headers):
            continue
        text = fields[columns["text"]].strip()
        if not text:
            continue
        try:
            confidence = float(fields[columns["conf"]])
        except ValueError:
            continue
        key = tuple(fields[columns[name]] for name in ("page_num", "block_num", "par_num", "line_num"))
        groups.setdefault(key, []).append((text, confidence))
    lines = []
    for words in groups.values():
        text = "".join(word for word, _ in words)
        valid = [confidence for _, confidence in words if confidence >= 0]
        confidence = sum(valid) / len(valid) if valid else 0.0
        lines.append(OcrLine(text, round(confidence, 2)))
    return OcrPage(page_number, tuple(lines))
