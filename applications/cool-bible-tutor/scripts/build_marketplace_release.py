"""Build an allowlisted, auditable Obvious One marketplace tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
from typing import NamedTuple


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from distribution_audit import (  # noqa: E402
    FORBIDDEN_SUFFIXES,
    PUBLIC_CORPUS_PATH,
    PUBLIC_RAG_INDEX,
    audit_tree,
)


MARKER = ".obvious-one-marketplace"
PLUGIN_ID = "cool-bible-tutor"
MAX_FILE_BYTES = 100 * 1024 * 1024
PUBLIC_ROOT_FILES = {
    ".gitattributes", "README.md", "DISTRIBUTION.md", "THIRD_PARTY_CONTENT.md",
    "THIRD_PARTY_NOTICES.md", "PRIVACY.md", "SECURITY.md", "LICENSE",
}
PUBLIC_PREFIXES = {
    ".codex-plugin", "assets", "docs", "scripts", "skills", "tests", "vendor",
}
REPOSITORY_ONLY_PATHS = {
    "tests/test_openclaw_release.py",
    "tests/test_vendored_runtime.py",
}


class ReleaseReport(NamedTuple):
    version: str
    paths: tuple[str, ...]
    sha256: dict[str, str]
    total_bytes: int


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _public_source_files(source: Path) -> list[Path]:
    files: list[Path] = []
    for candidate in source.rglob("*"):
        relative = candidate.relative_to(source)
        if candidate.is_symlink():
            raise ValueError(f"release source contains symlink: {relative.as_posix()}")
        if not candidate.is_file():
            continue
        if relative.parts[0] not in PUBLIC_PREFIXES and relative.as_posix() not in PUBLIC_ROOT_FILES:
            continue
        if relative.as_posix() in REPOSITORY_ONLY_PATHS:
            continue
        if candidate.stat().st_size >= MAX_FILE_BYTES:
            raise ValueError(f"release file is at or above 100 MiB: {relative.as_posix()}")
        suffix = candidate.suffix.lower()
        if suffix in FORBIDDEN_SUFFIXES and relative.as_posix() not in {
            PUBLIC_CORPUS_PATH, PUBLIC_RAG_INDEX,
        }:
            raise ValueError(f"undeclared database, vector, or model file: {relative.as_posix()}")
        files.append(candidate)
    return sorted(files, key=lambda item: item.relative_to(source).as_posix())


def _prepare_destination(destination: Path) -> None:
    if destination.exists():
        entries = list(destination.iterdir())
        if entries and not (destination / MARKER).is_file():
            raise ValueError("refusing nonempty destination without marketplace marker")
    else:
        destination.mkdir(parents=True)
    (destination / MARKER).write_text("明明可知 Obvious One marketplace\n", encoding="utf-8")


def _remove_tree(path: Path) -> None:
    def clear_readonly_and_retry(function, value, _error):
        os.chmod(value, stat.S_IWRITE)
        function(value)
    shutil.rmtree(path, onerror=clear_readonly_and_retry)


def build_release(source: Path, destination: Path, version: str) -> ReleaseReport:
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if not source.is_dir():
        raise ValueError("plugin source directory is missing")
    errors = audit_tree(source)
    if errors:
        raise ValueError("source distribution audit failed: " + "; ".join(errors))
    plugin_manifest = json.loads(
        (source / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    if plugin_manifest.get("name") != PLUGIN_ID or plugin_manifest.get("version") != version:
        raise ValueError("plugin identity or version does not match release request")
    _prepare_destination(destination)

    staging = destination / f".{PLUGIN_ID}.staging"
    target = destination / "plugins" / PLUGIN_ID
    if staging.exists():
        _remove_tree(staging)
    staging.mkdir(parents=True)
    source_files = _public_source_files(source)
    for candidate in source_files:
        relative = candidate.relative_to(source)
        output = staging / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate, output)

    errors = audit_tree(staging)
    if errors:
        _remove_tree(staging)
        raise ValueError("staged distribution audit failed: " + "; ".join(errors))
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = destination / f".{PLUGIN_ID}.previous"
    if backup.exists():
        _remove_tree(backup)
    if target.exists():
        os.replace(target, backup)
    try:
        os.replace(staging, target)
    except Exception:
        if backup.exists() and not target.exists():
            os.replace(backup, target)
        raise
    if backup.exists():
        _remove_tree(backup)

    prefix = Path("plugins") / PLUGIN_ID
    paths = tuple((prefix / path.relative_to(source)).as_posix() for path in source_files)
    digests = {
        relative: _digest(destination / relative)
        for relative in paths
    }
    report = ReleaseReport(
        version=version,
        paths=paths,
        sha256=digests,
        total_bytes=sum((destination / relative).stat().st_size for relative in paths),
    )
    manifest = {
        "schema_version": 1,
        "plugin_id": PLUGIN_ID,
        "version": version,
        "total_bytes": report.total_bytes,
        "files": [{"path": path, "sha256": digests[path]} for path in paths],
    }
    temporary = destination / ".release-manifest.json.tmp"
    temporary.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, destination / ".release-manifest.json")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    report = build_release(args.source, args.destination, args.version)
    print(json.dumps(report._asdict(), ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
