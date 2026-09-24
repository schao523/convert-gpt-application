#!/usr/bin/env python3
"""Audit Cool Plugin Design Assistant distributable text trees."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re


ROOT_FILES = {
    "README.md",
    "DISTRIBUTION.md",
    "LICENSE",
    "PRIVACY.md",
    "SECURITY.md",
    "THIRD_PARTY_CONTENT.md",
    "THIRD_PARTY_NOTICES.md",
    "package.json",
    "CONTENT-MANIFEST.json",
}
PREFIXES = {".codex-plugin", "docs", "scripts", "skills"}
EXCLUDED_PATHS = {"docs/marketplace-approved-delta.json"}
FORBIDDEN_NAMES = {
    ".env",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "conversion.json",
    "conversion.local.json",
    "CONTENT-MANIFEST.json.tmp",
    ".release-manifest.json.tmp",
}
FORBIDDEN_SUFFIXES = {
    ".db",
    ".sqlite",
    ".sqlite3",
    ".faiss",
    ".index",
    ".npy",
    ".npz",
    ".onnx",
    ".pt",
    ".pth",
    ".safetensors",
    ".model",
    ".bin",
    ".docx",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
}
TEXT_SUFFIXES = {"", ".md", ".json", ".yaml", ".yml", ".py", ".txt"}
WINDOWS_USER_PATH = re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE)
UNIX_USER_PATH = re.compile(r"/(?:Users|home)/[^/\s]+/")
SECRET = re.compile(
    r"(?:BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|AWS_SECRET_ACCESS_KEY\s*=|"
    r"GH_TOKEN\s*=|(?:api[_-]?key|token|password)\s*[:=]\s*['\"]?[^\s'\"]{12,}|"
    r"sk-[A-Za-z0-9]{20,})",
    re.IGNORECASE,
)
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\((?!https?://|mailto:|#)([^)]+)\)")


def _scaffold_marker() -> str:
    return "[" + "TODO:"


def _is_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    if os.name == "nt":
        return bool(path.stat(follow_symlinks=False).st_file_attributes & 0x400)
    return False


def _allowed(relative: Path) -> bool:
    raw = relative.as_posix()
    if raw in EXCLUDED_PATHS:
        return False
    return raw in ROOT_FILES or bool(relative.parts and relative.parts[0] in PREFIXES)


def _audit(root: Path, reject_outside: bool) -> list[str]:
    root = Path(root).resolve()
    errors: set[str] = set()
    for candidate in root.rglob("*"):
        relative_path = candidate.relative_to(root)
        relative = relative_path.as_posix()
        if _is_link(candidate):
            errors.add(f"link forbidden: {relative}")
        if not candidate.is_file():
            continue
        if reject_outside and any(part in FORBIDDEN_NAMES for part in relative_path.parts):
            errors.add(f"forbidden file: {relative}")
        suffix = candidate.suffix.lower()
        if reject_outside and suffix in FORBIDDEN_SUFFIXES:
            errors.add(f"forbidden source or runtime asset: {relative}")
        if not _allowed(relative_path):
            if reject_outside:
                errors.add(f"file outside allowlist: {relative}")
            continue
        if any(part in FORBIDDEN_NAMES for part in relative_path.parts):
            errors.add(f"forbidden file: {relative}")
        if suffix == ".pyc" or "__pycache__" in relative_path.parts:
            errors.add(f"Python cache artifact: {relative}")
        if suffix in FORBIDDEN_SUFFIXES:
            errors.add(f"forbidden source or runtime asset: {relative}")
        if suffix not in TEXT_SUFFIXES:
            errors.add(f"non-text file forbidden: {relative}")
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
        if suffix == ".md":
            for raw in MARKDOWN_LINK.findall(text):
                target = raw.split("#", 1)[0].split(maxsplit=1)[0].strip("<>")
                if target and not (candidate.parent / target).resolve().exists():
                    errors.add(f"broken Markdown link: {relative} -> {raw}")
    return sorted(errors)


def audit_tree(root: Path) -> list[str]:
    """Strictly audit a finished public artifact tree."""

    return _audit(root, reject_outside=True)


def audit_public_source(root: Path) -> list[str]:
    """Audit only allowlisted files in a development product root."""

    return _audit(root, reject_outside=False)


def audit_distribution(stage: Path, _contract: object) -> list[str]:
    """Package-builder hook with the stable product-audit signature."""

    return audit_tree(stage)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--source", action="store_true")
    options = parser.parse_args()
    function = audit_public_source if options.source else audit_tree
    errors = function(options.root)
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
