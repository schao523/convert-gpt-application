"""Write redacted, reproducible provenance for a controlled extraction."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess


SOURCE_SUFFIXES = {".pdf", ".docx", ".ppt", ".pptx"}
INCORPORATED_BRANCHES = (
    "feature/generic-openclaw-framework",
    "codex/openclaw-compat-evaluation",
)


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _record(root: Path, path: Path, classification: str) -> dict[str, str]:
    return {
        "classification": classification,
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
    }


def inventory_source(source: Path) -> list[dict[str, str]]:
    source = source.resolve()
    records: list[dict[str, str]] = []
    for path in source.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() in SOURCE_SUFFIXES or path.name.endswith("_guide.md"):
            records.append(_record(source, path, "source-only"))

    product_assets = source / "cool-bible-tutor" / "assets"
    for path in product_assets.rglob("*"):
        if path.is_file() and not path.is_symlink():
            records.append(_record(source, path, "public-product-asset"))
    return sorted(records, key=lambda item: (item["classification"], item["path"]))


def _git_head(repository: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        text=True,
    ).strip()


def build_provenance(
    source_repo: Path,
    marketplace_repo: Path,
) -> dict[str, object]:
    source_repo = source_repo.resolve()
    marketplace_repo = marketplace_repo.resolve()
    return {
        "schema_version": 1,
        "source_repository": "cool-bible-tutor-gpt-source",
        "source_commit": _git_head(source_repo),
        "marketplace_repository": "schao523/obvious-one-plugins",
        "marketplace_commit": _git_head(marketplace_repo),
        "incorporated_branches": list(INCORPORATED_BRANCHES),
        "source_inventory": inventory_source(source_repo),
    }


def write_atomic(destination: Path, payload: dict[str, object]) -> None:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, destination)


def output_report(destination: Path) -> str:
    return json.dumps(
        {"output": str(destination.resolve())},
        ensure_ascii=True,
        sort_keys=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--marketplace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    write_atomic(
        arguments.output,
        build_provenance(arguments.source, arguments.marketplace),
    )
    print(output_report(arguments.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
