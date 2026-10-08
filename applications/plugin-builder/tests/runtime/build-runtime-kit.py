#!/usr/bin/env python3
"""Build a deterministic, self-contained T1–T8 owner replay kit."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import zipfile

from obvious_one_plugin_framework.plugin_authoring import write_deterministic_zip
from obvious_one_plugin_framework.workbench_handoff import normalize_handoff_archive


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def build_kit(source: Path, release: Path, plugin_zip: Path, output: Path) -> str:
    source = source.resolve()
    release = release.resolve()
    plugin_zip = plugin_zip.resolve()
    plugin = release / "plugins/plugin-builder"
    if not (release / ".plugin-builder-release-root").is_file() or not plugin.is_dir():
        raise ValueError("reviewed release root is required")
    if not plugin_zip.is_file():
        raise ValueError("reviewed upload ZIP is required")
    release_manifest = release / ".release-manifest.json"
    manifest = json.loads(release_manifest.read_text(encoding="utf-8"))
    expected = {
        item["path"].removeprefix("plugins/plugin-builder/"): item["sha256"]
        for item in manifest["files"]
    }
    with zipfile.ZipFile(plugin_zip) as archive:
        observed = {
            item.filename: sha256(archive.read(item)).hexdigest()
            for item in archive.infolist() if not item.is_dir()
        }
    if observed != expected:
        raise ValueError("upload ZIP does not match reviewed release manifest")
    sample = source / "tests/fixtures/design-package-legacy"
    if not sample.is_dir():
        raise ValueError("sample handoff source is unavailable")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="plugin-builder-runtime-kit-") as temporary:
        stage = Path(temporary) / "kit"
        stage.mkdir()
        shutil.copyfile(plugin_zip, stage / "plugin-builder.zip")
        shutil.copyfile(release_manifest, stage / "release-manifest.json")
        shutil.copytree(plugin / "runtime", stage / "runtime")
        shutil.copyfile(source / "tests/runtime/runtime-result-schema.json", stage / "runtime/runtime-result-schema.json")
        raw = stage / "sample-legacy-handoff-v1.1.zip"
        write_deterministic_zip(sample, raw)
        canonical = stage / "sample-normalized-handoff-v1.1.zip"
        normalized = normalize_handoff_archive(raw, Path(temporary) / "normalized-tree", canonical)
        if normalized.status != "PASS":
            raise ValueError(f"sample normalization failed: {normalized.diagnostics}")
        scenario = stage / "scenario-inputs"
        prepared = subprocess.run(
            [sys.executable, "-B", str(stage / "runtime/prepare-runtime-scenarios.py"),
             "--output", str(scenario)],
            cwd=stage, capture_output=True, text=True, encoding="utf-8", check=False,
        )
        if prepared.returncode != 0 or json.loads(prepared.stdout).get("status") != "PASS":
            raise ValueError(f"scenario preparation failed: {prepared.stderr}")
        files = {
            path.relative_to(stage).as_posix(): digest(path)
            for path in sorted(stage.rglob("*")) if path.is_file()
        }
        identity = {
            "schema": "plugin-builder-runtime-kit-identity-v1",
            "plugin_zip_sha256": files["plugin-builder.zip"],
            "release_manifest_sha256": digest(release_manifest),
            "members": files,
            "installed_runtime_evidence": "NOT VERIFIED",
        }
        (stage / "identity.json").write_text(
            json.dumps(identity, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="ascii", newline="\n",
        )
        return write_deterministic_zip(stage, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--plugin-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    digest_value = build_kit(options.source, options.release, options.plugin_zip, options.output)
    print(json.dumps({"status": "PASS", "sha256": digest_value, "output": str(options.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
