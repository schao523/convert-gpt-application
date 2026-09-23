"""Read-only legacy-contract migration proposals.

Proposals preserve known declarations while leaving every owner decision
explicitly unresolved. They are diagnostics, not buildable contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping

from .contract import ContractError, DistributionContract, load_contract
from .results import ArtifactRecord, Diagnostic, OperationResult


_CLASSIFICATION_CANDIDATES = (
    "text",
    "binary",
    "exclude",
    "external_asset",
    "private_local",
)


@dataclass(frozen=True)
class MigrationProposal:
    proposal_schema_version: int
    target_schema_version: int
    contract_draft: Mapping[str, object]
    diagnostics: tuple[Diagnostic, ...]


def build_migration_proposal(contract_path: Path) -> MigrationProposal:
    """Create a deterministic, intentionally unresolved schema-v3 proposal."""

    contract = load_contract(contract_path)
    if contract.schema_version not in (1, 2):
        raise ContractError("migration_requires_legacy_contract", str(contract.schema_version))
    raw = _load_raw_contract(contract_path)
    selected = _selected_files(contract)

    diagnostics: list[Diagnostic] = [
        Diagnostic(
            "publication_decision_required",
            None,
            "publication targets require an explicit decision-owner approval",
            ("enable_github_marketplace", "disable_github_marketplace"),
        )
    ]
    rules: list[dict[str, object]] = []
    for index, (relative, source) in enumerate(selected, start=1):
        characteristics = _characteristics(source)
        diagnostics.append(
            Diagnostic(
                "classification_required",
                relative,
                "classification required; detected "
                f"size={characteristics['size']}, "
                f"utf8_decodable={str(characteristics['utf8_decodable']).lower()}, "
                f"contains_nul={str(characteristics['contains_nul']).lower()}, "
                f"extension={characteristics['extension']}",
                _CLASSIFICATION_CANDIDATES,
            )
        )
        rules.append(
            {
                "classification": None,
                "id": f"unresolved-{index:04d}",
                "paths": [relative],
                "prefixes": [],
                "redistribution": {"provenance": None, "status": None},
            }
        )

    preserved_keys = (
        "plugin_id",
        "package_name",
        "family",
        "version",
        "source_root",
        "include_files",
        "include_prefixes",
        "exclude_paths",
        "max_total_bytes",
        "release_repository",
        "release_tag_template",
        "readme_overlay",
        "audit_hook",
        "rag",
    )
    draft: dict[str, object] = {key: raw[key] for key in preserved_keys}
    draft.update(
        {
            "schema_version": 3,
            "content_rules": rules,
            "publication": {
                "github_marketplace": {"enabled": None},
                "clawhub": {
                    "enabled": None,
                    "family": None,
                    "native_manifest": None,
                },
            },
        }
    )
    return MigrationProposal(
        proposal_schema_version=1,
        target_schema_version=3,
        contract_draft=draft,
        diagnostics=tuple(diagnostics),
    )


def write_migration_proposal(contract_path: Path, output_path: Path) -> OperationResult:
    """Write a new proposal without replacing any existing destination."""

    destination = Path(output_path)
    if destination.exists():
        raise ContractError("migration_destination_exists", destination.name)
    proposal = build_migration_proposal(contract_path)
    payload = _proposal_payload(proposal)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
    except FileExistsError as exc:
        raise ContractError("migration_destination_exists", destination.name) from exc
    return OperationResult(
        operation="migrate-contract",
        status="BLOCKED",
        code="migration_decisions_required",
        diagnostics=proposal.diagnostics,
        artifacts=(
            ArtifactRecord(
                path=destination.name,
                kind="migration_proposal",
                sha256=_sha256(encoded.encode("utf-8")),
                size=len(encoded.encode("utf-8")),
            ),
        ),
        evidence={"diagnostic_count": len(proposal.diagnostics)},
    )


def _load_raw_contract(path: Path) -> Mapping[str, object]:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("invalid_json", Path(path).name) from exc
    if not isinstance(raw, dict):
        raise ContractError("invalid_type", "contract must be an object")
    return raw


def _selected_files(contract: DistributionContract) -> tuple[tuple[str, Path], ...]:
    selected: dict[str, Path] = {}
    excluded = set(contract.exclude_paths)
    for relative in contract.include_files:
        candidate = contract.source_root / relative
        if not candidate.is_file():
            raise ContractError("included_file_missing", relative)
        selected[relative] = candidate
    for prefix in contract.include_prefixes:
        base = contract.source_root / prefix
        if not base.is_dir():
            raise ContractError("included_prefix_missing", prefix)
        for candidate in base.rglob("*"):
            if not candidate.is_file():
                continue
            relative = candidate.relative_to(contract.source_root).as_posix()
            if relative not in excluded:
                selected[relative] = candidate
    for relative in excluded:
        selected.pop(relative, None)
    return tuple((relative, selected[relative]) for relative in sorted(selected))


def _characteristics(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    try:
        data.decode("utf-8")
        utf8_decodable = True
    except UnicodeDecodeError:
        utf8_decodable = False
    return {
        "contains_nul": b"\x00" in data,
        "extension": path.suffix.lower(),
        "size": len(data),
        "utf8_decodable": utf8_decodable,
    }


def _proposal_payload(proposal: MigrationProposal) -> dict[str, object]:
    return {
        "proposal_schema_version": proposal.proposal_schema_version,
        "target_schema_version": proposal.target_schema_version,
        "contract_draft": proposal.contract_draft,
        "diagnostics": [
            {
                "candidates": list(item.candidates),
                "code": item.code,
                "message": item.message,
                "path": item.path,
            }
            for item in proposal.diagnostics
        ],
    }


def _sha256(data: bytes) -> str:
    from hashlib import sha256

    return sha256(data).hexdigest()
