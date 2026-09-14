"""Write redacted, reproducible provenance for one configured application."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from obvious_one_plugin_framework.provenance import (  # noqa: E402
    ProvenanceError,
    build_provenance,
)
from obvious_one_plugin_framework.verification import (  # noqa: E402
    ApplicationConfig,
    VerificationConfigError,
    discover_applications,
    select_applications,
)


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


def resolve_output(
    config: ApplicationConfig,
    repository_root: Path,
    override: Path | None,
) -> Path:
    repository = Path(repository_root).resolve()
    destination = config.source_inventory.resolve() if override is None else Path(override).resolve()
    if not destination.is_relative_to(repository):
        raise ProvenanceError("output_path_escape")
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--application", required=True)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--marketplace", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    options = build_parser().parse_args(arguments)
    try:
        configs = discover_applications(ROOT)
        config = select_applications(
            configs,
            application_id=options.application,
            select_all=False,
        )[0]
        destination = resolve_output(config, ROOT, options.output)
        payload = build_provenance(
            config,
            options.source.resolve(),
            options.marketplace.resolve(),
        )
        write_atomic(destination, payload)
    except (OSError, ProvenanceError, VerificationConfigError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print(output_report(destination))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
