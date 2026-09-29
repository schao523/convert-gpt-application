#!/usr/bin/env python3
"""Audit Plugin Builder's deny-by-default public text boundary."""

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
PUBLIC_DOCS = {
    "docs/application-invariants.md",
    "docs/runtime-compatibility.md",
}
PREFIXES = {"scripts", "skills"}
MANIFEST_FILE = ".codex-plugin/plugin.json"
FORBIDDEN_NAMES = {
    ".env",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "conversion.json",
    "conversion.local.json",
}
FORBIDDEN_SUFFIXES = {
    ".bin",
    ".db",
    ".docx",
    ".faiss",
    ".gif",
    ".index",
    ".jpeg",
    ".jpg",
    ".model",
    ".npy",
    ".npz",
    ".onnx",
    ".pdf",
    ".png",
    ".pt",
    ".pth",
    ".safetensors",
    ".sqlite",
    ".sqlite3",
    ".webp",
    ".zip",
}
TEXT_SUFFIXES = {"", ".json", ".md", ".py", ".txt", ".yaml", ".yml"}
WINDOWS_USER_PATH = re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE)
UNIX_USER_PATH = re.compile(r"/(?:Users|home)/[^/\s]+/")
SECRET = re.compile(
    r"(?:BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|AWS_SECRET_ACCESS_KEY\s*=|"
    r"GH_TOKEN\s*=|(?:api[_-]?key|token|password)\s*[:=]\s*['\"]?[^\s'\"]{12,}|"
    r"(?:ghp_|sk-)[A-Za-z0-9_-]{20,})",
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
    return (
        raw in ROOT_FILES
        or raw in PUBLIC_DOCS
        or raw == MANIFEST_FILE
        or bool(relative.parts and relative.parts[0] in PREFIXES)
    )


def _audit(root: Path, *, reject_outside: bool) -> list[str]:
    root = Path(root).resolve()
    errors: set[str] = set()
    for candidate in root.rglob("*"):
        relative_path = candidate.relative_to(root)
        relative = relative_path.as_posix()
        if _is_link(candidate):
            errors.add(f"link_forbidden: {relative}")
        if not candidate.is_file():
            continue
        allowed = _allowed(relative_path)
        if not allowed:
            if reject_outside:
                errors.add(f"outside_allowlist: {relative}")
            continue
        if any(part in FORBIDDEN_NAMES for part in relative_path.parts):
            errors.add(f"forbidden_name: {relative}")
        suffix = candidate.suffix.lower()
        if suffix == ".pyc" or "__pycache__" in relative_path.parts:
            errors.add(f"cache_artifact: {relative}")
        if suffix in FORBIDDEN_SUFFIXES:
            errors.add(f"unsafe_suffix: {relative}")
        if suffix not in TEXT_SUFFIXES:
            errors.add(f"non_text_file: {relative}")
            continue
        try:
            text = candidate.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.add(f"non_utf8_text: {relative}")
            continue
        if WINDOWS_USER_PATH.search(text) or UNIX_USER_PATH.search(text):
            errors.add(f"private_path: {relative}")
        if SECRET.search(text):
            errors.add(f"secret_pattern: {relative}")
        if _scaffold_marker() in text:
            errors.add(f"scaffold_marker: {relative}")
        if suffix == ".md":
            for raw_target in MARKDOWN_LINK.findall(text):
                target = raw_target.split("#", 1)[0].split(maxsplit=1)[0].strip("<>")
                if not target:
                    continue
                resolved = (candidate.parent / target).resolve()
                try:
                    resolved.relative_to(root)
                except ValueError:
                    errors.add(f"broken_markdown_link: {relative} -> {raw_target}")
                    continue
                if not resolved.exists():
                    errors.add(f"broken_markdown_link: {relative} -> {raw_target}")
    return sorted(errors)


def audit_tree(root: Path) -> list[str]:
    """Strictly audit a finished public artifact tree."""

    return _audit(root, reject_outside=True)


def audit_public_source(root: Path) -> list[str]:
    """Audit allowlisted files while ignoring non-public development inputs."""

    return _audit(root, reject_outside=False)


def audit_distribution(stage: Path, _contract: object) -> list[str]:
    """Package-builder hook with the stable product-audit signature."""

    return audit_tree(stage)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--source", action="store_true")
    options = parser.parse_args()
    audit = audit_public_source if options.source else audit_tree
    errors = audit(options.root)
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
