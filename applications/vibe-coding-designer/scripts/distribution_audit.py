#!/usr/bin/env python3
"""Audit Vibe Coding Designer distributable trees."""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import re


FORBIDDEN_NAMES = {
    ".env", ".git", "__pycache__", "conversion.json", "conversion.local.json",
    "CONTENT-MANIFEST.json.tmp", ".release-manifest.json.tmp",
}
FORBIDDEN_SUFFIXES = {
    ".db", ".sqlite", ".sqlite3", ".faiss", ".onnx", ".pt", ".pth",
    ".safetensors", ".docx", ".pdf",
}
TEXT_SUFFIXES = {"", ".md", ".json", ".yaml", ".yml", ".py", ".txt"}
WINDOWS_USER_PATH = re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE)
UNIX_USER_PATH = re.compile(r"/(?:Users|home)/[^/\s]+/")
SECRET = re.compile(
    r"(?:BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|AWS_SECRET_ACCESS_KEY\s*=|GH_TOKEN\s*=|sk-[A-Za-z0-9]{20,})"
)
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\((?!https?://|#)([^)]+)\)")


def _scaffold_marker() -> str:
    return "[" + "TODO:"


def digest(path: Path) -> str:
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def audit_tree(root: Path) -> list[str]:
    root = Path(root).resolve()
    errors: set[str] = set()
    for candidate in root.rglob("*"):
        relative = candidate.relative_to(root).as_posix()
        if candidate.is_symlink():
            errors.add(f"link forbidden: {relative}")
        if candidate.name in FORBIDDEN_NAMES:
            errors.add(f"forbidden file: {relative}")
        if not candidate.is_file():
            continue
        if candidate.suffix.lower() == ".pyc":
            errors.add(f"Python cache artifact: {relative}")
        if candidate.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.add(f"forbidden source or runtime asset: {relative}")
        if candidate.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = candidate.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.add(f"non-UTF-8 text file: {relative}")
            continue
        if WINDOWS_USER_PATH.search(text):
            errors.add(f"absolute Windows user path: {relative}")
        if UNIX_USER_PATH.search(text):
            errors.add(f"absolute Unix user path: {relative}")
        if SECRET.search(text):
            errors.add(f"secret pattern: {relative}")
        if _scaffold_marker() in text:
            errors.add(f"scaffold marker: {relative}")
        if candidate.suffix.lower() == ".md":
            for raw in MARKDOWN_LINK.findall(text):
                target = raw.split("#", 1)[0]
                if target and not (candidate.parent / target).resolve().exists():
                    errors.add(f"broken Markdown link: {relative} -> {raw}")
    return sorted(errors)


def audit_distribution(stage: Path, _contract: object) -> list[str]:
    """Package-builder hook with the stable product-audit signature."""

    return audit_tree(stage)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    options = parser.parse_args()
    errors = audit_tree(options.root)
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
