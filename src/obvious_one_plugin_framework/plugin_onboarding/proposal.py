"""Publication-only audit and deterministic onboarding proposals."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Mapping

from ..marketplace import MarketplaceError, load_preparation_catalog
from .contract import OnboardingError, PublicationDecisions
from .inspection import OnboardingInspection


_GENERATED_APPLICATION_FILES = (
    "conversion.json",
    "plugin.json",
    ".codex-plugin/plugin.json",
    "DISTRIBUTION.md",
    "LICENSE",
    "PRIVACY.md",
    "SECURITY.md",
    "THIRD_PARTY_CONTENT.md",
    "THIRD_PARTY_NOTICES.md",
    "docs/application-invariants.md",
    "docs/imported-package-inventory.json",
    "docs/publication-decisions.json",
    "docs/runtime-compatibility.md",
    "docs/source-decisions.md",
    "openclaw/distribution.json",
    "scripts/build_marketplace_release.py",
    "scripts/distribution_audit.py",
    "tests/test_imported_package.py",
    "tests/test_marketplace_release.py",
)


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("ascii")


def _freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class OnboardingProposal:
    schema: str
    proposal_sha256: str
    plugin_id: str
    version: str
    application_path: str
    catalog_entry: Mapping[str, object]
    generated_files: tuple[str, ...]
    publication_decisions: Mapping[str, object]
    builder_evidence: Mapping[str, object]
    runtime_evidence_states: Mapping[str, str]
    diagnostics: tuple[str, ...] = ()

    def proposal_payload(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "proposal_sha256": self.proposal_sha256,
            "plugin_id": self.plugin_id,
            "version": self.version,
            "application_path": self.application_path,
            "catalog_entry": _thaw(self.catalog_entry),
            "generated_files": list(self.generated_files),
            "publication_decisions": _thaw(self.publication_decisions),
            "builder_evidence": _thaw(self.builder_evidence),
            "runtime_evidence_states": _thaw(self.runtime_evidence_states),
            "diagnostics": list(self.diagnostics),
        }

    def proposal_json(self) -> str:
        return _canonical_bytes(self.proposal_payload()).decode("ascii")


def _error(code: str, *, blocked: bool = False, detail: str = "") -> OnboardingError:
    prefix = "onboarding." if code.startswith("existing_") else "onboarding.proposal."
    return OnboardingError(prefix + code, "BLOCKED" if blocked else "FAIL", detail)


def _decision_payload(decisions: PublicationDecisions) -> dict[str, object]:
    return {
        **decisions.identity_payload(),
        "decision_recorded_at": decisions.decision_recorded_at,
    }


def _audit_decisions(
    inspection: OnboardingInspection,
    decisions: PublicationDecisions,
) -> None:
    for field in (
        "redistribution_approved",
        "third_party_content_reviewed",
        "public_marketplace_approved",
    ):
        if getattr(decisions, field) is not True:
            raise OnboardingError(
                f"onboarding.decisions.{field}_required", "BLOCKED"
            )
    if decisions.license != "MIT":
        raise OnboardingError("onboarding.decisions.unsupported_license", "FAIL")
    if decisions.target_runtime != "CODEX":
        raise OnboardingError("onboarding.decisions.invalid_target_runtime", "FAIL")
    if decisions.marketplace_id != "obvious-one":
        raise OnboardingError("onboarding.decisions.invalid_marketplace_id", "FAIL")
    if decisions.plugin_id != inspection.plugin_id:
        raise _error("plugin_identity_mismatch")
    if decisions.version != inspection.version:
        raise _error("version_mismatch")
    if decisions.author != inspection.manifest_identity.get("author"):
        raise _error("author_mismatch")
    expected_destination = f"plugins/{inspection.plugin_id}"
    destination = decisions.codex_destination
    if (
        destination != expected_destination
        or "\\" in destination
        or PurePosixPath(destination).is_absolute()
        or PureWindowsPath(destination).is_absolute()
        or any(part in {"", ".", ".."} for part in PurePosixPath(destination).parts)
    ):
        raise _error("destination_invalid")
    if decisions.third_party_content == "INCLUDED_WITH_PLUGIN_NOTICES":
        notice = next(
            (
                member
                for member in inspection.members
                if member.path == f"{inspection.plugin_id}/THIRD_PARTY_NOTICES.md"
            ),
            None,
        )
        if notice is None or notice.size <= 0:
            raise _error("third_party_notices_required")


def _audit_declared_content(inspection: OnboardingInspection) -> None:
    if inspection.diagnostics:
        raise _error("secret_finding", detail=inspection.diagnostics[0])
    declared_files: set[str] = set()
    dependencies_declared = False
    mcp_declared = False
    for contract in inspection.tool_contracts:
        files = contract.get("files")
        if isinstance(files, (list, tuple)):
            declared_files.update(item for item in files if isinstance(item, str))
        dependencies = contract.get("dependencies")
        dependencies_declared = dependencies_declared or bool(dependencies)
        mcp_declared = mcp_declared or contract.get("implementation_kind") == "MCP_ADAPTER"
    undeclared_executable = sorted(set(inspection.executable_files) - declared_files)
    if undeclared_executable:
        raise _error("undeclared_executable", detail=undeclared_executable[0])
    if inspection.dependency_files and not dependencies_declared:
        raise _error("undeclared_dependency", detail=inspection.dependency_files[0])
    if inspection.mcp_files and not mcp_declared:
        raise _error("undeclared_external_service", detail=inspection.mcp_files[0])
    remote_markers = (
        "remote-assets.json",
        "remote_asset",
        "/corpus/",
        "/corpora/",
        "/vector-index/",
    )
    for member in inspection.members:
        folded = f"/{member.path.casefold()}"
        if any(marker in folded for marker in remote_markers):
            raise _error("undeclared_remote_asset", detail=member.path)


def _load_catalog(repository: Path):
    catalog_path = repository / "marketplaces" / "obvious-one.json"
    try:
        catalog = load_preparation_catalog(catalog_path, repository)
    except MarketplaceError as exc:
        raise _error("repository_catalog_invalid", detail=exc.code) from exc
    if catalog.schema_version != 2 or catalog.marketplace_id != "obvious-one":
        raise _error("repository_catalog_invalid")
    return catalog


def _audit_repository(
    inspection: OnboardingInspection,
    decisions: PublicationDecisions,
    repository: Path,
) -> None:
    root = Path(repository)
    if not root.is_dir():
        raise _error("repository_invalid")
    application = root / "applications" / inspection.plugin_id
    if application.exists():
        raise _error("existing_plugin_requires_update_design", blocked=True)
    catalog = _load_catalog(root)
    proposed = PurePosixPath(decisions.codex_destination)
    for entry in catalog.applications:
        if entry.application.plugin_id == inspection.plugin_id:
            raise _error("existing_plugin_requires_update_design", blocked=True)
        for _, target in entry.applicable_targets():
            if target.destination is None:
                continue
            existing = PurePosixPath(target.destination)
            proposed_parts = tuple(part.casefold() for part in proposed.parts)
            existing_parts = tuple(part.casefold() for part in existing.parts)
            if (
                proposed_parts[: len(existing_parts)] == existing_parts
                or existing_parts[: len(proposed_parts)] == proposed_parts
            ):
                raise _error("existing_plugin_requires_update_design", blocked=True)


def _identity_payload(
    inspection: OnboardingInspection,
    decisions: PublicationDecisions,
    application_path: str,
    catalog_entry: Mapping[str, object],
    generated_files: tuple[str, ...],
    builder_evidence: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema": "plugin-onboarding-proposal-v1",
        "plugin_id": inspection.plugin_id,
        "version": inspection.version,
        "application_path": application_path,
        "catalog_entry": _thaw(catalog_entry),
        "generated_files": list(generated_files),
        "publication_decisions": decisions.identity_payload(),
        "builder_evidence": _thaw(builder_evidence),
        "runtime_evidence_states": _thaw(inspection.evidence_states),
        "diagnostics": [],
    }


def build_onboarding_proposal(
    inspection: OnboardingInspection,
    decisions: PublicationDecisions,
    repository: Path,
) -> OnboardingProposal:
    """Compile a deterministic, unapproved Workbench registration proposal."""

    _audit_decisions(inspection, decisions)
    _audit_declared_content(inspection)
    _audit_repository(inspection, decisions, Path(repository))
    application_path = f"applications/{inspection.plugin_id}"
    catalog_entry = {
        "application_config": f"{application_path}/conversion.json",
        "distribution_contract": f"{application_path}/openclaw/distribution.json",
        "targets": {
            "codex": {
                "mode": "build",
                "destination": decisions.codex_destination,
            },
            "openclaw": {"mode": "not_applicable"},
        },
    }
    imported_files = tuple(
        f"imported-plugin/{member.path.removeprefix(f'{inspection.plugin_id}/')}"
        for member in inspection.members
    )
    generated_files = tuple(sorted((*_GENERATED_APPLICATION_FILES, *imported_files)))
    builder_evidence = {
        "package_state": inspection.package_state,
        "archive_sha256": inspection.archive_sha256,
        "member_manifest_sha256": inspection.member_manifest_sha256,
        "candidate_sha256": inspection.candidate_sha256,
        "verification_sha256": inspection.verification_sha256,
        "manifest_profile": inspection.manifest_profile,
        "runtime_realization_state": inspection.runtime_realization_state,
        "evidence_bundle_state": inspection.evidence_bundle_state,
    }
    identity_payload = _identity_payload(
        inspection,
        decisions,
        application_path,
        catalog_entry,
        generated_files,
        builder_evidence,
    )
    proposal_sha256 = sha256(_canonical_bytes(identity_payload)).hexdigest()
    return OnboardingProposal(
        schema="plugin-onboarding-proposal-v1",
        proposal_sha256=proposal_sha256,
        plugin_id=inspection.plugin_id,
        version=inspection.version,
        application_path=application_path,
        catalog_entry=_freeze(catalog_entry),  # type: ignore[arg-type]
        generated_files=generated_files,
        publication_decisions=_freeze(_decision_payload(decisions)),  # type: ignore[arg-type]
        builder_evidence=_freeze(builder_evidence),  # type: ignore[arg-type]
        runtime_evidence_states=_freeze(dict(inspection.evidence_states)),  # type: ignore[arg-type]
    )
