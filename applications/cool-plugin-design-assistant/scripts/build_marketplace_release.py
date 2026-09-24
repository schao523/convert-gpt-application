#!/usr/bin/env python3
"""Build a deterministic, allowlisted Codex marketplace plugin tree."""

from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
from typing import NamedTuple


PLUGIN_ID = "cool-plugin-design-assistant"
MARKER = ".obvious-one-marketplace"
ROOT_FILES = {
    "README.md",
    "DISTRIBUTION.md",
    "LICENSE",
    "PRIVACY.md",
    "SECURITY.md",
    "THIRD_PARTY_CONTENT.md",
    "THIRD_PARTY_NOTICES.md",
}
PREFIXES = {".codex-plugin", "docs", "scripts", "skills"}
EXCLUDED_PATHS = {"docs/marketplace-approved-delta.json"}


class ReleaseReport(NamedTuple):
    version: str
    paths: tuple[str, ...]
    sha256: dict[str, str]
    total_bytes: int


def _digest(path: Path) -> str:
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _remove_tree(path: Path) -> None:
    if not path.exists():
        return

    def retry(function, value, _error):
        os.chmod(value, stat.S_IWRITE)
        function(value)

    shutil.rmtree(path, onerror=retry)


def _load_audit(source: Path):
    path = source / "scripts" / "distribution_audit.py"
    spec = importlib.util.spec_from_file_location("assistant_distribution_audit", path)
    if spec is None or spec.loader is None:
        raise ValueError("distribution audit cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.audit_tree


def _public_files(source: Path) -> list[Path]:
    files: list[Path] = []
    for candidate in source.rglob("*"):
        relative = candidate.relative_to(source)
        if candidate.is_symlink():
            raise ValueError(f"release source contains link: {relative.as_posix()}")
        if not candidate.is_file():
            continue
        raw = relative.as_posix()
        if raw in EXCLUDED_PATHS:
            continue
        if raw in ROOT_FILES or relative.parts[0] in PREFIXES:
            if "__pycache__" not in relative.parts and candidate.suffix.lower() != ".pyc":
                files.append(candidate)
    return sorted(files, key=lambda item: item.relative_to(source).as_posix())


def build_release(source: Path, destination: Path, version: str) -> ReleaseReport:
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    manifest = json.loads(
        (source / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    if manifest.get("name") != PLUGIN_ID or manifest.get("version") != version:
        raise ValueError("plugin identity or version mismatch")

    destination.mkdir(parents=True, exist_ok=True)
    marker = destination / MARKER
    if any(destination.iterdir()) and not marker.is_file():
        raise ValueError("refusing nonempty destination without marketplace marker")
    marker.write_text("Obvious One marketplace staging\n", encoding="utf-8", newline="\n")

    staging = destination / f".{PLUGIN_ID}.staging"
    target = destination / "plugins" / PLUGIN_ID
    _remove_tree(staging)
    staging.mkdir(parents=True)
    for candidate in _public_files(source):
        relative = candidate.relative_to(source)
        output = staging / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(candidate, output)

    errors = _load_audit(source)(staging)
    if errors:
        _remove_tree(staging)
        raise ValueError("distribution audit failed: " + "; ".join(errors))

    target.parent.mkdir(parents=True, exist_ok=True)
    backup = destination / f".{PLUGIN_ID}.previous"
    _remove_tree(backup)
    if target.exists():
        os.replace(target, backup)
    try:
        os.replace(staging, target)
    except Exception:
        if backup.exists() and not target.exists():
            os.replace(backup, target)
        raise
    _remove_tree(backup)

    prefix = Path("plugins") / PLUGIN_ID
    paths = tuple(
        (prefix / item.relative_to(target)).as_posix()
        for item in sorted(
            target.rglob("*"), key=lambda path: path.relative_to(target).as_posix()
        )
        if item.is_file()
    )
    digests = {path: _digest(destination / path) for path in paths}
    report = ReleaseReport(
        version,
        paths,
        digests,
        sum((destination / path).stat().st_size for path in paths),
    )
    release_manifest = {
        "schema_version": 1,
        "plugin_id": PLUGIN_ID,
        "version": version,
        "total_bytes": report.total_bytes,
        "files": [{"path": path, "sha256": digests[path]} for path in paths],
    }
    temporary = destination / ".release-manifest.json.tmp"
    temporary.write_text(
        json.dumps(release_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, destination / ".release-manifest.json")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--version", required=True)
    options = parser.parse_args()
    report = build_release(options.source, options.destination, options.version)
    print(json.dumps(report._asdict(), ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
