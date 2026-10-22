"""Transactional materialization of reviewed Plugin Builder ZIP proposals."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Mapping

from .. import plugin_authoring
from ..contract import load_contract
from ..results import ArtifactRecord, MutationRecord, OperationResult, result_json
from ..verification import load_application_config_path
from .contract import (
    LegacyPluginBuilderAdoption,
    OnboardingError,
    PackageMetadata,
    PortableContentManifestAdoption,
    WorkbenchRepairMetadata,
    load_plugin_builder_adoption,
    load_onboarding_metadata,
    load_publication_decisions,
)
from .inspection import (
    inspect_legacy_plugin_builder_package,
    inspect_portable_content_manifest_package,
    inspect_plugin_builder_package,
    inspect_workbench_repaired_package,
)
from .proposal import build_onboarding_proposal
from .templates import canonical_json_bytes, render_application_files


_MARKER = ".obvious-one-plugin-onboarding"
_ALLOWED_REPOSITORY_OUTPUT_ROOTS = frozenset({".tmp", "dist"})


def _write_files(root: Path, files: Mapping[str, bytes]) -> None:
    for relative, content in sorted(files.items()):
        target = root.joinpath(*relative.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def _preflight_output(output: Path) -> None:
    if not output.exists():
        return
    if not output.is_dir():
        raise OnboardingError("onboarding.output_collision", "FAIL")
    if not any(output.iterdir()):
        return
    marker = output / _MARKER
    if not marker.is_file():
        raise OnboardingError("onboarding.output_collision", "FAIL")
    try:
        payload = json.loads(marker.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OnboardingError("onboarding.output_collision", "FAIL") from exc
    if set(payload) != {"schema", "proposal_sha256"} or payload.get("schema") != "plugin-onboarding-output-v1":
        raise OnboardingError("onboarding.output_collision", "FAIL")


def _validate_output_boundary(
    output: Path,
    repository: Path,
    inputs: tuple[Path, ...],
) -> None:
    destination = output.resolve()
    repository_root = repository.resolve()
    for supplied in inputs:
        candidate = supplied.resolve()
        if candidate == destination or candidate.is_relative_to(destination) or destination.is_relative_to(candidate):
            raise OnboardingError("onboarding.output_input_overlap", "FAIL")
    if repository_root == destination or repository_root.is_relative_to(destination):
        raise OnboardingError("onboarding.output_protected", "FAIL")
    if destination.is_relative_to(repository_root):
        relative = destination.relative_to(repository_root)
        if not relative.parts or relative.parts[0] not in _ALLOWED_REPOSITORY_OUTPUT_ROOTS:
            raise OnboardingError("onboarding.output_protected", "FAIL")


def _publish_output(stage: Path, output: Path, temporary_root: Path) -> None:
    """Replace a missing or owned output while restoring it on publish failure."""

    backup = temporary_root / "previous"
    had_output = output.exists()
    if had_output:
        os.replace(output, backup)
    try:
        if had_output:
            _preflight_output(backup)
        os.replace(stage, output)
    except BaseException:
        if had_output and backup.exists() and not output.exists():
            os.replace(backup, output)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def _validate_stage(
    application: Path,
    imported: Path,
    *,
    strict_plugin_tree: bool = True,
) -> None:
    if strict_plugin_tree:
        issues = plugin_authoring.validate_plugin_tree(imported)
        if issues:
            raise OnboardingError(
                "onboarding.materialize.imported_plugin_invalid", "FAIL", issues[0].code
            )
    contract = load_contract(application / "openclaw" / "distribution.json")
    if contract.schema_version != 3:
        raise OnboardingError("onboarding.materialize.contract_invalid", "FAIL")
    adopted = application.parent / contract.plugin_id
    if adopted.exists():
        raise OnboardingError("onboarding.materialize.validation_collision", "FAIL")
    application.rename(adopted)
    try:
        config = load_application_config_path(
            adopted / "conversion.json", adopted.parent
        )
        if config.plugin_id != contract.plugin_id or config.version != contract.version:
            raise OnboardingError("onboarding.materialize.config_invalid", "FAIL")
    finally:
        adopted.rename(application)


def prepare_plugin_zip_marketplace(
    archive: Path,
    package_metadata: Path | None,
    publication_decisions: Path,
    repository: Path,
    output: Path,
    *,
    legacy_adoption: Path | None = None,
    evidence: Path | None = None,
) -> OperationResult:
    """Create one deterministic, unapproved marketplace-registration proposal."""

    if (package_metadata is None) == (legacy_adoption is None):
        raise OnboardingError("onboarding.authority_selection_invalid", "FAIL")
    if legacy_adoption is not None and evidence is not None:
        raise OnboardingError(
            "onboarding.legacy_runtime_evidence_unsupported", "FAIL"
        )
    archive_path = Path(archive).resolve()
    metadata_path = (
        Path(package_metadata).resolve() if package_metadata is not None else None
    )
    adoption_path = (
        Path(legacy_adoption).resolve() if legacy_adoption is not None else None
    )
    decisions_path = Path(publication_decisions).resolve()
    repository_path = Path(repository).resolve()
    evidence_path = Path(evidence).resolve() if evidence is not None else None
    destination = Path(output).resolve()
    _validate_output_boundary(
        destination,
        repository_path,
        tuple(
            path
            for path in (
                archive_path,
                metadata_path,
                adoption_path,
                decisions_path,
                evidence_path,
            )
            if path is not None
        ),
    )
    _preflight_output(destination)
    decisions = load_publication_decisions(decisions_path)
    metadata: PackageMetadata | WorkbenchRepairMetadata | None
    adoption: LegacyPluginBuilderAdoption | PortableContentManifestAdoption | None
    if adoption_path is not None:
        metadata = None
        adoption = load_plugin_builder_adoption(adoption_path)
        if isinstance(adoption, PortableContentManifestAdoption):
            inspection = inspect_portable_content_manifest_package(
                archive_path, adoption
            )
        else:
            inspection = inspect_legacy_plugin_builder_package(archive_path, adoption)
    else:
        adoption = None
        assert metadata_path is not None
        metadata = load_onboarding_metadata(metadata_path)
        if isinstance(metadata, PackageMetadata):
            inspection = inspect_plugin_builder_package(
                archive_path, metadata, evidence=evidence_path
            )
        else:
            if evidence_path is not None:
                raise OnboardingError(
                    "onboarding.repair_runtime_evidence_unsupported", "FAIL"
                )
            inspection = inspect_workbench_repaired_package(archive_path, metadata)
    proposal = build_onboarding_proposal(inspection, decisions, repository_path)

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}-onboarding-", dir=destination.parent)
    )
    stage = temporary_root / "stage"
    extracted = temporary_root / "extracted"
    stage.mkdir()
    try:
        plugin_authoring.extract_archive(archive_path, extracted)
        located = plugin_authoring.locate_plugin_archive_root(extracted)
        expected_profile = (
            "PORTABLE_SINGLE_DIRECTORY"
            if isinstance(metadata, PackageMetadata)
            or isinstance(adoption, PortableContentManifestAdoption)
            else "LEGACY_FLAT"
        )
        if located.profile != expected_profile:
            raise OnboardingError("onboarding.materialize.envelope_profile_mismatch", "FAIL")
        if plugin_authoring.tree_sha256(located.path) != inspection.content_tree_sha256:
            raise OnboardingError("onboarding.materialize.candidate_identity_mismatch", "FAIL")

        imported_files = {
            path.relative_to(located.path).as_posix(): path.read_bytes()
            for path in sorted(located.path.rglob("*"))
            if path.is_file()
        }
        application = stage / "application"
        imported = application / "imported-plugin"
        _write_files(imported, imported_files)
        _write_files(application, render_application_files(inspection, decisions, imported_files))
        (stage / "onboarding-proposal.json").write_text(
            proposal.proposal_json(), encoding="ascii", newline="\n"
        )
        (stage / "catalog-entry.json").write_bytes(canonical_json_bytes(proposal.catalog_entry))
        (stage / _MARKER).write_bytes(
            canonical_json_bytes(
                {
                    "schema": "plugin-onboarding-output-v1",
                    "proposal_sha256": proposal.proposal_sha256,
                }
            )
        )
        _validate_stage(
            application,
            imported,
            strict_plugin_tree=adoption is None,
        )

        proposal_bytes = (stage / "onboarding-proposal.json").read_bytes()
        result_evidence: dict[str, object] = {
            "proposal_sha256": proposal.proposal_sha256,
            "archive_sha256": inspection.archive_sha256,
            "content_tree_sha256": inspection.content_tree_sha256,
            "runtime_evidence_states": dict(inspection.evidence_states),
        }
        if inspection.candidate_sha256 is not None:
            result_evidence["candidate_sha256"] = inspection.candidate_sha256
        if inspection.verification_sha256 is not None:
            result_evidence["verification_sha256"] = inspection.verification_sha256
        if inspection.adoption_identity_sha256 is not None:
            result_evidence["adoption_identity_sha256"] = (
                inspection.adoption_identity_sha256
            )
        result = OperationResult(
            operation="prepare-plugin-zip-marketplace",
            status="PASS",
            code="onboarding.proposal_materialized",
            artifacts=(
                ArtifactRecord(
                    path="onboarding-proposal.json",
                    kind="plugin-onboarding-proposal",
                    sha256=sha256(proposal_bytes).hexdigest(),
                    size=len(proposal_bytes),
                ),
            ),
            mutations=(MutationRecord(path=".", action="write-proposal"),),
            evidence=result_evidence,
        )
        (stage / "onboarding-result.json").write_text(
            result_json(result), encoding="ascii", newline="\n"
        )
        _publish_output(stage, destination, temporary_root)
        return result
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root)
