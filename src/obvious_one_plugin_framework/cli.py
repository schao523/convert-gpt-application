"""Command-line interface for generic Obvious One plugin distribution work."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .content_policy import ContentPolicyError
from .contract import ContractError, load_contract
from .contract_migration import write_migration_proposal
from .index_reuse import IndexReuseError, check_index_reuse, derive_index
from .package_builder import PackageAuditError, build_package, verify_package
from .release_assets import AssetBuildError, build_asset_groups, write_remote_manifest
from .results import ArtifactRecord, Diagnostic, MutationRecord, OperationResult, result_json


BLOCKING_CODES = frozenset({
    "legacy_contract_read_only",
    "unclassified_files",
    "ambiguous_file_classification",
    "rights_unresolved",
    "migration_decisions_required",
    "reembedding_required",
})


class _CliArgumentError(ValueError):
    pass


class _ResultArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _CliArgumentError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _ResultArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("build-package", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--contract", required=True, type=Path)
        command.add_argument("--output", required=True, type=Path)
        command.add_argument("--json", action="store_true")
    validate = commands.add_parser("validate-contract")
    validate.add_argument("--contract", required=True, type=Path)
    validate.add_argument("--json", action="store_true")
    migrate = commands.add_parser("migrate-contract")
    migrate.add_argument("--contract", required=True, type=Path)
    migrate.add_argument("--output", required=True, type=Path)
    migrate.add_argument("--json", action="store_true")
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


def emit_result(result: OperationResult) -> None:
    """Emit exactly one ASCII-safe result document."""

    sys.stdout.write(result_json(result))


def main(argv: list[str] | None = None) -> int:
    raw_arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        arguments = _parser().parse_args(raw_arguments)
    except _CliArgumentError:
        emit_result(_failure("cli", "FAIL", "invalid_cli_arguments"))
        return 2

    operation = arguments.command
    try:
        result = _dispatch(arguments)
    except ContractError as exc:
        result = _typed_failure(operation, exc.code)
    except ContentPolicyError as exc:
        result = _typed_failure(operation, exc.code)
    except (PackageAuditError, AssetBuildError, IndexReuseError) as exc:
        result = _typed_failure(operation, exc.code)
    except OSError:
        emit_result(_failure(operation, "FAIL", "io_failure"))
        return 4

    emit_result(result)
    if result.status == "PASS":
        return 0
    if result.status == "BLOCKED":
        return 2
    return 3


def _dispatch(arguments: argparse.Namespace) -> OperationResult:
    operation = arguments.command
    if operation == "validate-contract":
        contract = load_contract(arguments.contract)
        return OperationResult(
            operation=operation,
            status="PASS",
            code="contract_valid",
            evidence={
                "plugin_id": contract.plugin_id,
                "schema_version": contract.schema_version,
                "version": contract.version,
            },
        )
    if operation == "migrate-contract":
        return write_migration_proposal(arguments.contract, arguments.output)
    if operation in {"build-package", "verify"}:
        contract = load_contract(arguments.contract)
        existed = arguments.output.exists()
        built = build_package(contract, arguments.output) if operation == "build-package" else verify_package(contract, arguments.output)
        mutations = () if operation == "verify" else (
            MutationRecord(arguments.output.name, "replace" if existed else "create"),
        )
        return OperationResult(
            operation=operation,
            status="PASS",
            code="package_built" if operation == "build-package" else "package_verified",
            artifacts=(ArtifactRecord(arguments.output.name, "plugin_directory", built.content_sha256, built.total_bytes),),
            mutations=mutations,
            evidence={
                "content_sha256": built.content_sha256,
                "file_count": built.file_count,
                "plugin_id": contract.plugin_id,
                "total_bytes": built.total_bytes,
            },
        )
    if operation == "build-assets":
        contract = load_contract(arguments.contract)
        records = build_asset_groups(contract, arguments.output)
        mutations = [MutationRecord(record.name, "create") for record in records]
        artifacts = [ArtifactRecord(record.name, "asset_archive", record.sha256, record.size) for record in records]
        if arguments.manifest is not None:
            write_remote_manifest(contract, records, arguments.manifest)
            mutations.append(MutationRecord(arguments.manifest.name, "create"))
        return OperationResult(
            operation=operation,
            status="PASS",
            code="assets_built",
            artifacts=tuple(artifacts),
            mutations=tuple(mutations),
            evidence={"asset_count": len(records), "plugin_id": contract.plugin_id},
        )
    if operation == "check-index-reuse":
        report = check_index_reuse(arguments.source_manifest, arguments.target_manifest, arguments.source_index)
        if not report.eligible:
            return OperationResult(
                operation=operation,
                status="BLOCKED",
                code="reembedding_required",
                diagnostics=tuple(Diagnostic("index_identity_mismatch", item, "immutable identity differs") for item in report.mismatches),
            )
        return OperationResult(operation, "PASS", "index_reuse_eligible", evidence={"eligible": True, "mismatches": []})
    record = derive_index(arguments.source_index, arguments.destination, arguments.source_manifest, arguments.target_manifest)
    return OperationResult(
        operation=operation,
        status="PASS",
        code="index_derived",
        artifacts=(ArtifactRecord(arguments.destination.name, "vector_index", record.sha256, record.path.stat().st_size),),
        mutations=(MutationRecord(arguments.destination.name, "replace"),),
        evidence={
            "app_id": record.app_id,
            "item_count": record.item_count,
            "namespace": record.namespace,
            "vector_identity_sha256": record.vector_identity_sha256,
        },
    )


def _typed_failure(operation: str, code: str) -> OperationResult:
    return _failure(operation, "BLOCKED" if code in BLOCKING_CODES else "FAIL", code)


def _failure(operation: str, status: str, code: str) -> OperationResult:
    return OperationResult(
        operation=operation,
        status=status,
        code=code,
        diagnostics=(Diagnostic(code, None, "operation did not complete"),),
    )


if __name__ == "__main__":
    raise SystemExit(main())
