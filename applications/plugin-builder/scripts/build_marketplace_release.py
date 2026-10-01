#!/usr/bin/env python3
"""Build a deterministic local Codex artifact without publishing it."""

from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
from tempfile import TemporaryDirectory
from typing import NamedTuple


PLUGIN_ID = "plugin-builder"
MARKER = ".plugin-builder-release-root"
ROOT_FILES = {
    "plugin.json",
    "README.md",
    "DISTRIBUTION.md",
    "LICENSE",
    "PRIVACY.md",
    "SECURITY.md",
    "THIRD_PARTY_CONTENT.md",
    "THIRD_PARTY_NOTICES.md",
}
PUBLIC_DOCS = {
    "docs/application-invariants.md",
    "docs/runtime-compatibility.md",
}
PREFIXES = {"scripts", "skills"}
MANIFEST_FILES = {"plugin.json", ".codex-plugin/plugin.json"}
VENDOR_PACKAGE = Path("scripts/vendor/obvious_one_plugin_framework/plugin_authoring")


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


def _remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        def retry(function, value, _error):
            os.chmod(value, stat.S_IWRITE)
            function(value)

        shutil.rmtree(path, onerror=retry)
    else:
        path.unlink()


def _load_audit(source: Path):
    path = source / "scripts" / "distribution_audit.py"
    spec = importlib.util.spec_from_file_location("plugin_builder_distribution_audit", path)
    if spec is None or spec.loader is None:
        raise ValueError("distribution audit cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        or raw in MANIFEST_FILES
        or bool(relative.parts and relative.parts[0] in PREFIXES)
    )


def _public_files(source: Path) -> tuple[Path, ...]:
    selected: list[Path] = []
    for candidate in source.rglob("*"):
        relative = candidate.relative_to(source)
        if _is_link(candidate):
            raise ValueError(f"release source contains link: {relative.as_posix()}")
        if not candidate.is_file() or not _allowed(relative):
            continue
        if "__pycache__" in relative.parts or candidate.suffix.lower() == ".pyc":
            continue
        selected.append(candidate)
    return tuple(sorted(selected, key=lambda item: item.relative_to(source).as_posix()))


def _release_data(plugin: Path, version: str) -> tuple[ReleaseReport, dict[str, object]]:
    prefix = Path("plugins") / PLUGIN_ID
    paths = tuple(
        (prefix / item.relative_to(plugin)).as_posix()
        for item in sorted(plugin.rglob("*"), key=lambda path: path.relative_to(plugin).as_posix())
        if item.is_file()
    )
    digests = {path: _digest(plugin.parents[1] / path) for path in paths}
    report = ReleaseReport(
        version=version,
        paths=paths,
        sha256=digests,
        total_bytes=sum((plugin.parents[1] / path).stat().st_size for path in paths),
    )
    manifest: dict[str, object] = {
        "schema_version": 1,
        "plugin_id": PLUGIN_ID,
        "version": version,
        "total_bytes": report.total_bytes,
        "files": [{"path": path, "sha256": digests[path]} for path in paths],
    }
    return report, manifest


def _install_transactionally(staged_plugin: Path, staged_manifest: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    marker = destination / MARKER
    marker.write_text("Plugin Builder local release staging\n", encoding="utf-8", newline="\n")
    target = destination / "plugins" / PLUGIN_ID
    release_manifest = destination / ".release-manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)

    backup_plugin = staged_plugin.parent / ".previous-plugin"
    backup_manifest = staged_plugin.parent / ".previous-release-manifest.json"
    plugin_backed_up = False
    manifest_backed_up = False
    plugin_installed = False
    manifest_installed = False
    try:
        if target.exists():
            os.replace(target, backup_plugin)
            plugin_backed_up = True
        if release_manifest.exists():
            os.replace(release_manifest, backup_manifest)
            manifest_backed_up = True
        os.replace(staged_plugin, target)
        plugin_installed = True
        os.replace(staged_manifest, release_manifest)
        manifest_installed = True
    except Exception:
        if plugin_installed:
            _remove_path(target)
        if manifest_installed:
            _remove_path(release_manifest)
        if plugin_backed_up:
            os.replace(backup_plugin, target)
        if manifest_backed_up:
            os.replace(backup_manifest, release_manifest)
        raise


def build_release(source: Path, destination: Path, version: str) -> ReleaseReport:
    """Build and transactionally install one marker-protected local artifact."""

    source = Path(source).resolve()
    destination = Path(destination).resolve()
    portable = json.loads((source / "plugin.json").read_text(encoding="utf-8"))
    manifest = json.loads((source / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    if (
        portable.get("name") != PLUGIN_ID or portable.get("version") != version
        or manifest.get("name") != PLUGIN_ID or manifest.get("version") != version
        or portable.get("extensions", {}).get("com.openai", {}).get("interface") != manifest.get("interface")
    ):
        raise ValueError("plugin identity or version mismatch")

    rights_evidence = source / "docs" / "source-decisions.md"
    try:
        rights_text = rights_evidence.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError("rights and provenance evidence missing") from exc
    if not rights_text.strip():
        raise ValueError("rights and provenance evidence missing")

    audit = _load_audit(source)
    source_errors = audit.audit_public_source(source)
    if source_errors:
        raise ValueError("release source audit failed: " + "; ".join(source_errors))

    if destination.exists() and any(destination.iterdir()) and not (destination / MARKER).is_file():
        raise ValueError("refusing nonempty destination without Plugin Builder release marker")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=f".{PLUGIN_ID}-release-", dir=destination.parent) as temporary:
        stage_root = Path(temporary)
        staged_plugin = stage_root / "plugins" / PLUGIN_ID
        staged_plugin.mkdir(parents=True)
        for candidate in _public_files(source):
            relative = candidate.relative_to(source)
            output = staged_plugin / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(candidate, output)

        repository = source.parents[1]
        framework_package = repository / "src" / "obvious_one_plugin_framework" / "plugin_authoring"
        if not framework_package.is_dir():
            package_spec = importlib.util.find_spec("obvious_one_plugin_framework.plugin_authoring")
            if package_spec is not None and package_spec.submodule_search_locations:
                framework_package = Path(next(iter(package_spec.submodule_search_locations)))
        if not framework_package.is_dir():
            raise ValueError("plugin authoring runtime is unavailable")
        vendor_parent = staged_plugin / "scripts/vendor/obvious_one_plugin_framework"
        vendor_parent.mkdir(parents=True, exist_ok=True)
        (vendor_parent / "__init__.py").write_text(
            '"""Vendored standalone runtime namespace."""\n', encoding="utf-8", newline="\n"
        )
        vendor_package = staged_plugin / VENDOR_PACKAGE
        vendor_package.mkdir(parents=True, exist_ok=True)
        for candidate in sorted(framework_package.glob("*.py"), key=lambda path: path.name):
            shutil.copyfile(candidate, vendor_package / candidate.name)

        errors = audit.audit_tree(staged_plugin)
        if errors:
            raise ValueError("distribution audit failed: " + "; ".join(errors))

        report, release_manifest = _release_data(staged_plugin, version)
        staged_manifest = stage_root / ".release-manifest.json"
        staged_manifest.write_text(
            json.dumps(release_manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        _install_transactionally(staged_plugin, staged_manifest, destination)
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
