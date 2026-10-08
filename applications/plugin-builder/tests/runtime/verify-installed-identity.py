#!/usr/bin/env python3
"""Diagnose exact installed bytes versus one observed host-manifest variant.

An observed variant is not proof of installer normalization or runtime behavior.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile


MANIFEST = ".codex-plugin/plugin.json"


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _observed_variant(source: bytes, installed: bytes) -> bool:
    try:
        before = json.loads(source, object_pairs_hook=_unique_object)
        after = json.loads(installed, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return False
    if not isinstance(before, dict) or not isinstance(after, dict):
        return False
    if before.get("skills") != "./skills/" or "keywords" in before:
        return False
    expected = dict(before, skills="./skills", keywords=[])
    return after == expected


def _safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(path.parts) and not path.is_absolute() and all(
        part not in {"", ".", ".."} and ":" not in part and "\\" not in part
        for part in path.parts
    )


def reconcile(reviewed_zip: Path, installed_root: Path) -> dict[str, object]:
    reviewed_zip = Path(reviewed_zip)
    installed_root = Path(installed_root)
    if not reviewed_zip.is_file() or not installed_root.is_dir():
        raise ValueError("reviewed ZIP and installed directory are required")
    with zipfile.ZipFile(reviewed_zip) as archive:
        members = [item.filename for item in archive.infolist() if not item.is_dir()]
        if len(members) != len(set(members)) or not all(_safe_member(name) for name in members):
            raise ValueError("reviewed ZIP contains duplicate or unsafe member names")
        source = {name: archive.read(name) for name in members}
    installed: dict[str, bytes] = {}
    for path in installed_root.rglob("*"):
        if path.is_symlink():
            raise ValueError("installed tree contains a symlink")
        if path.is_file():
            installed[path.relative_to(installed_root).as_posix()] = path.read_bytes()
    missing = sorted(source.keys() - installed.keys())
    extra = sorted(installed.keys() - source.keys())
    changed = sorted(name for name in source.keys() & installed.keys() if source[name] != installed[name])
    other = [name for name in changed if name != MANIFEST]
    observed_variant = (
        not missing and not extra and not other and changed == [MANIFEST]
        and _observed_variant(source[MANIFEST], installed[MANIFEST])
    ) if MANIFEST in source and MANIFEST in installed else False
    exact = MANIFEST in source and MANIFEST in installed and not missing and not extra and not changed
    return {
        "schema": "plugin-builder-installed-identity-diagnostic-v1",
        "status": "PASS" if exact else "NOT VERIFIED" if observed_variant else "BLOCKED",
        "installed_byte_identity": "PASS" if exact else "FAIL",
        "manifest_reconciliation": "EXACT" if exact else "OBSERVED_VARIANT_ONLY" if observed_variant else "REJECTED",
        "normalization_cause": "NOT APPLICABLE" if exact else "NOT VERIFIED",
        "installed_runtime_behavior": "NOT VERIFIED",
        "reviewed_zip_sha256": _digest(reviewed_zip.read_bytes()),
        "reviewed_manifest_sha256": _digest(source[MANIFEST]) if MANIFEST in source else None,
        "installed_manifest_sha256": _digest(installed[MANIFEST]) if MANIFEST in installed else None,
        "reviewed_member_count": len(source),
        "installed_member_count": len(installed),
        "missing_members": missing,
        "extra_members": extra,
        "other_member_mismatches": other,
        "errors": ["reviewed.manifest_missing"] if MANIFEST not in source else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-zip", type=Path, required=True)
    parser.add_argument("--installed-root", type=Path, required=True)
    options = parser.parse_args()
    try:
        result = reconcile(options.reviewed_zip, options.installed_root)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        result = {"schema": "plugin-builder-installed-identity-diagnostic-v1", "status": "BLOCKED", "error": str(error)}
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["status"] != "BLOCKED" else 1


if __name__ == "__main__":
    sys.exit(main())
