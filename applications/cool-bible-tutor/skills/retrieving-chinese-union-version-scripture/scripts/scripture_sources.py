"""Resolve approved bundled Scripture PDFs and authorized external overrides."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


BUNDLED_SOURCES = (
    (
        "Bible 舊約聖經和合本.pdf",
        "2740A6F824F96374CB127D78C3D646B489963898DACC252B842D9A8894A91125",
    ),
    (
        "Bible 新約聖經和合本.pdf",
        "4F0F9EF4C4A78B83F918C74E8F368A7E0EAE515C17866C7767C310CA75786490",
    ),
)


class SourceValidationError(ValueError):
    """Raised when a bundled Scripture source is missing or modified."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def bundled_scripture_dir(script_path: Path | None = None) -> Path:
    script = Path(script_path) if script_path is not None else Path(__file__)
    return script.resolve().parents[3] / "assets" / "scripture"


def validate_source(path: Path, expected_sha256: str) -> Path:
    source = Path(path).resolve()
    if not source.is_file():
        raise SourceValidationError(f"Bundled Scripture source is missing: {source.name}")
    if _sha256(source) != expected_sha256.upper():
        raise SourceValidationError(f"Bundled Scripture source SHA-256 mismatch: {source.name}")
    return source


def resolve_bundled_sources(script_path: Path | None = None) -> tuple[Path, Path]:
    directory = bundled_scripture_dir(script_path)
    sources = tuple(
        validate_source(directory / filename, expected_sha256)
        for filename, expected_sha256 in BUNDLED_SOURCES
    )
    return sources[0], sources[1]


def resolve_source_paths(
    explicit=(), environ=None, script_path: Path | None = None
) -> tuple[Path, ...]:
    values = tuple(Path(value).expanduser().resolve() for value in explicit)
    if values:
        return values
    environment = os.environ if environ is None else environ
    configured = environment.get("COOL_BIBLE_TUTOR_SOURCE_PDFS", "")
    values = tuple(
        Path(value).expanduser().resolve()
        for value in configured.split(os.pathsep)
        if value.strip()
    )
    if values:
        return values
    return resolve_bundled_sources(script_path)
