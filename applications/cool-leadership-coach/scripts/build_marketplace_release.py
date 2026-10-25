"""Build the approved Codex release from the pinned Workbench derivative."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile

from obvious_one_plugin_framework import plugin_authoring


PLUGIN_ID = "cool-leadership-coach"
VERSION = "1.0.0"


def verify_source(application: Path) -> None:
    imported = application / "imported-plugin"
    inventory = json.loads((application / "docs/imported-package-inventory.json").read_text(encoding="utf-8"))
    if inventory["plugin_id"] != PLUGIN_ID or plugin_authoring.tree_sha256(imported) != inventory["content_tree_sha256"]:
        raise ValueError("imported_plugin_tree_mismatch")
    if [member.__dict__ for member in plugin_authoring.tree_manifest(imported)] != inventory["members"]:
        raise ValueError("imported_plugin_member_mismatch")
    for relative in ("plugin.json", ".codex-plugin/plugin.json"):
        manifest = json.loads((imported / relative).read_text(encoding="utf-8"))
        if (manifest.get("name"), manifest.get("version"), manifest.get("author", {}).get("name")) != (
            PLUGIN_ID, VERSION, "Shen-Chang Chao"
        ):
            raise ValueError("imported_plugin_identity_mismatch")
    if plugin_authoring.validate_plugin_tree(imported):
        raise ValueError("imported_plugin_structure_invalid")


def build(application: Path, destination: Path) -> Path:
    application = application.resolve()
    destination = destination.resolve()
    verify_source(application)
    license_path = application / "LICENSE"
    if not license_path.is_file():
        raise ValueError("license_missing")
    target = destination / "plugins" / PLUGIN_ID
    if target.exists():
        raise ValueError("marketplace_target_exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".leadership-release-", dir=target.parent) as name:
        staged = Path(name) / PLUGIN_ID
        shutil.copytree(application / "imported-plugin", staged)
        shutil.copyfile(license_path, staged / "LICENSE")
        if plugin_authoring.tree_sha256(staged) == plugin_authoring.tree_sha256(application / "imported-plugin"):
            raise ValueError("license_not_included")
        staged.rename(target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    if args.version != VERSION:
        raise ValueError("version_mismatch")
    print(json.dumps({"status": "PASS", "target": str(build(args.source, args.destination))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
