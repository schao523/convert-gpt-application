"""Command-line interface for generic Obvious One plugin distribution work."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from .contract import ContractError, load_contract
from .index_reuse import IndexReuseError, check_index_reuse, derive_index
from .package_builder import PackageAuditError, build_package, verify_package
from .release_assets import AssetBuildError, build_asset_groups, write_remote_manifest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("build-package", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--contract", required=True, type=Path)
        command.add_argument("--output", required=True, type=Path)
        command.add_argument("--json", action="store_true")
    assets = commands.add_parser("build-assets")
    assets.add_argument("--contract", required=True, type=Path)
    assets.add_argument("--output", required=True, type=Path)
    assets.add_argument("--manifest", type=Path)
    assets.add_argument("--json", action="store_true")
    check = commands.add_parser("check-index-reuse")
    check.add_argument("--source-manifest", required=True, type=Path)
    check.add_argument("--target-manifest", required=True, type=Path)
    check.add_argument("--source-index", required=True, type=Path)
    check.add_argument("--json", action="store_true")
    derive = commands.add_parser("derive-index")
    derive.add_argument("--source-manifest", required=True, type=Path)
    derive.add_argument("--target-manifest", required=True, type=Path)
    derive.add_argument("--source-index", required=True, type=Path)
    derive.add_argument("--destination", required=True, type=Path)
    derive.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True, default=str))


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command in {"build-package", "verify"}:
            contract = load_contract(arguments.contract)
            result = (
                build_package(contract, arguments.output)
                if arguments.command == "build-package"
                else verify_package(contract, arguments.output)
            )
            _emit({
                "status": "ok",
                "plugin_id": contract.plugin_id,
                "output": str(result.output),
                "file_count": result.file_count,
                "total_bytes": result.total_bytes,
                "content_sha256": result.content_sha256,
            })
            return 0
        if arguments.command == "build-assets":
            contract = load_contract(arguments.contract)
            records = build_asset_groups(contract, arguments.output)
            if arguments.manifest is not None:
                write_remote_manifest(contract, records, arguments.manifest)
            _emit({
                "status": "ok",
                "plugin_id": contract.plugin_id,
                "asset_count": len(records),
                "assets": [asdict(record) for record in records],
            })
            return 0
        if arguments.command == "check-index-reuse":
            report = check_index_reuse(
                arguments.source_manifest, arguments.target_manifest,
                arguments.source_index,
            )
            if not report.eligible:
                _emit({"status": "error", "error": "reembedding_required", "mismatches": report.mismatches})
                return 3
            _emit({"status": "ok", "eligible": True, "mismatches": []})
            return 0
        record = derive_index(
            arguments.source_index, arguments.destination,
            arguments.source_manifest, arguments.target_manifest,
        )
        _emit({"status": "ok", **asdict(record)})
        return 0
    except ContractError as exc:
        _emit({"status": "error", "error": exc.code, "message": str(exc)})
        return 2
    except (PackageAuditError, AssetBuildError, IndexReuseError) as exc:
        _emit({"status": "error", "error": exc.code, "message": str(exc)})
        return 3
    except OSError as exc:
        _emit({"status": "error", "error": "io_failure", "message": str(exc)})
        return 4


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
