#!/usr/bin/env python3
"""Build the approved Growing with Children 1.0.2 repaired derivative."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from obvious_one_plugin_framework.plugin_onboarding import (
    OnboardingError,
    RepairResult,
    load_repair_contract,
    repair_delegated_reference_archive,
)


APPLICATION_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = APPLICATION_ROOT / "repair" / "delegated-reference-repair-v1.json"
OPERATION = "build-growing-with-children-repair"


def build_repaired_release(source: Path, output_root: Path) -> RepairResult:
    """Build one deterministic repair below an explicit caller-owned root."""

    contract = load_repair_contract(CONTRACT_PATH)
    output = Path(output_root)
    archive = output / f"{contract.plugin_id}-{contract.target_version}.zip"
    metadata = output / "package-metadata.json"
    return repair_delegated_reference_archive(Path(source), contract, archive, metadata)


def _payload(status: str, *, errors: list[str], result: RepairResult | None = None) -> dict[str, object]:
    value: dict[str, object] = {
        "result_schema_version": 1,
        "operation": OPERATION,
        "status": status,
        "errors": sorted(set(errors)),
    }
    if result is not None:
        value["artifacts"] = [
            {"path": result.archive.name, "sha256": result.archive_sha256},
            {"path": result.metadata.name, "sha256": _sha256(result.metadata)},
        ]
        value["source_archive_sha256"] = result.source_archive_sha256
        value["member_manifest_sha256"] = result.member_manifest_sha256
    return value


def _sha256(path: Path) -> str:
    from hashlib import sha256

    digest = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    options = parser.parse_args(argv)
    try:
        result = build_repaired_release(options.source, options.output)
        payload = _payload("PASS", errors=[], result=result)
        exit_code = 0
    except OnboardingError as exc:
        payload = _payload("FAIL", errors=[exc.code])
        exit_code = 3
    except (OSError, ValueError):
        payload = _payload("FAIL", errors=["product.repair.unexpected_failure"])
        exit_code = 4
    rendered = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)
    print(rendered if options.json else rendered)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
