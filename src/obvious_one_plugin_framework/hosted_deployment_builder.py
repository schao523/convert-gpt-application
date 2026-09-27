"""Deterministic, transactional hosted deployment artifact construction."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
from typing import Mapping
from uuid import uuid4
import zipfile

from .content_policy import canonical_content_bytes
from .hosted_deployment_contract import HostedDeploymentContract, HostedDeploymentError
from .hosted_deployment_planner import HostedDeploymentValidation, validate_hosted_deployment


_FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_REPORT_NAMES = (
    "deployment-manifest.json",
    "validation-report.json",
    "deployment-report.json",
)


@dataclass(frozen=True)
class HostedDeploymentBuild:
    output: Path
    archive_path: Path
    archive_sha256: str
    artifact_sha256: str
    member_count: int
    total_bytes: int


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _digest(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _file_digest(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _member_bytes(validation: HostedDeploymentValidation) -> Mapping[str, bytes]:
    return {
        path: canonical_content_bytes(validation.source_paths[path], validation.content_policies[path])
        for path in validation.archive_paths
    }


def _write_zip(path: Path, members: Mapping[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, _FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, members[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def _core_artifact_hash(stage: Path, archive_name: str) -> str:
    digest = sha256()
    for name in sorted((archive_name, "deployment-manifest.json", "validation-report.json")):
        payload = (stage / name).read_bytes()
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(sha256(payload).digest())
    return digest.hexdigest()


def _write_reports(
    stage: Path,
    validation: HostedDeploymentValidation,
    members: Mapping[str, bytes],
    archive_sha256: str,
) -> str:
    contract = validation.contract
    manifest = {
        "application_id": contract.application_id,
        "archive": contract.archive_name,
        "archive_sha256": archive_sha256,
        "manifest_schema": "hosted-deployment-manifest-v1",
        "member_count": len(members),
        "members": [
            {
                "canonicalization": validation.content_policies[path].canonicalization,
                "classification": validation.content_policies[path].classification,
                "path": path,
                "sha256": _digest(members[path]),
                "size": len(members[path]),
            }
            for path in sorted(members)
        ],
        "operation": contract.operation,
        "package_name": contract.package_name,
        "total_bytes": sum(len(value) for value in members.values()),
        "version": contract.target_version,
    }
    (stage / "deployment-manifest.json").write_bytes(_json_bytes(manifest))

    capabilities = {
        capability.capability_id: {
            "hosted_execution": validation.hosted_capabilities[capability.capability_id],
            "local_execution": validation.local_capabilities[capability.capability_id],
            "package_static": "STATICALLY VERIFIED",
        }
        for capability in sorted(contract.capabilities, key=lambda item: item.capability_id)
    }
    validation_report = {
        "application_id": contract.application_id,
        "capabilities": capabilities,
        "channels": {
            "declared": dict(sorted(validation.declared_channels.items())),
            "generated": dict(sorted(validation.generated_channels.items())),
        },
        "code": "hosted_deployment_validated",
        "expected_skills": list(contract.expected_skills),
        "gates": {
            "capability_contracts": "PASS",
            "complete_archive_mapping": "PASS",
            "content_policy": "PASS",
            "identity_and_version": "PASS",
            "skill_discovery": "PASS",
        },
        "report_schema": "hosted-validation-report-v1",
        "status": "PASS",
    }
    (stage / "validation-report.json").write_bytes(_json_bytes(validation_report))
    artifact_sha256 = _core_artifact_hash(stage, contract.archive_name)

    instruction = (
        "Upload this complete ZIP as a new version of the existing hosted plugin."
        if contract.operation == "OPENAI_HOSTED_UPDATE"
        else "Upload this complete ZIP to create a new hosted plugin."
    )
    deployment_report = {
        "application_id": contract.application_id,
        "archive_sha256": archive_sha256,
        "artifact_sha256": artifact_sha256,
        "code": "hosted_deployment_built",
        "installation_status": "NOT VERIFIED",
        "instruction": instruction,
        "marketplace_status": "NOT_PERFORMED",
        "operation": contract.operation,
        "package_name": contract.package_name,
        "public_submission_status": "NOT_PERFORMED",
        "report_schema": "hosted-deployment-report-v1",
        "status": "PASS",
        "target_version": contract.target_version,
        "upload_status": "NOT_PERFORMED",
    }
    (stage / "deployment-report.json").write_bytes(_json_bytes(deployment_report))
    return artifact_sha256


def _audit_stage(
    stage: Path,
    validation: HostedDeploymentValidation,
    artifact_sha256: str,
) -> HostedDeploymentBuild:
    contract = validation.contract
    expected_files = {contract.archive_name, *_REPORT_NAMES}
    actual_files = {path.name for path in stage.iterdir() if path.is_file()}
    if actual_files != expected_files:
        raise HostedDeploymentError("hosted_artifact_set_mismatch")
    archive_path = stage / contract.archive_name
    archive_sha256 = _file_digest(archive_path)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            if [item.filename for item in infos] != list(validation.archive_paths):
                raise HostedDeploymentError("complete_archive_mismatch")
            if any(item.date_time != _FIXED_TIMESTAMP for item in infos):
                raise HostedDeploymentError("archive_metadata_mismatch")
        for name in _REPORT_NAMES:
            json.loads((stage / name).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        raise HostedDeploymentError("hosted_artifact_audit_failed") from exc
    report = json.loads((stage / "deployment-report.json").read_text(encoding="utf-8"))
    if report.get("archive_sha256") != archive_sha256 or report.get("artifact_sha256") != artifact_sha256:
        raise HostedDeploymentError("hosted_report_hash_mismatch")
    if _core_artifact_hash(stage, contract.archive_name) != artifact_sha256:
        raise HostedDeploymentError("hosted_artifact_hash_mismatch")
    return HostedDeploymentBuild(
        output=stage,
        archive_path=archive_path,
        archive_sha256=archive_sha256,
        artifact_sha256=artifact_sha256,
        member_count=len(validation.archive_paths),
        total_bytes=sum((stage / contract.archive_name).stat().st_size for _ in (0,)),
    )


def _remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_file() or path.is_symlink():
        path.unlink()
        return

    def retry(function, value, _error) -> None:
        os.chmod(value, stat.S_IWRITE)
        function(value)

    shutil.rmtree(path, onerror=retry)


def _replace_directory_transactionally(stage: Path, output: Path) -> None:
    backup = output.with_name(f".{output.name}.previous-{uuid4().hex}")
    moved_previous = False
    try:
        if output.exists():
            os.replace(output, backup)
            moved_previous = True
        os.replace(stage, output)
    except BaseException:
        if moved_previous and backup.exists() and not output.exists():
            os.replace(backup, output)
        raise
    else:
        if moved_previous:
            _remove_path(backup)


def build_hosted_deployment(
    contract: HostedDeploymentContract,
    output: Path,
) -> HostedDeploymentBuild:
    validation = validate_hosted_deployment(contract)
    destination = Path(output).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{destination.name}.stage-", dir=destination.parent))
    try:
        members = _member_bytes(validation)
        archive_path = stage / contract.archive_name
        _write_zip(archive_path, members)
        archive_sha256 = _file_digest(archive_path)
        artifact_sha256 = _write_reports(stage, validation, members, archive_sha256)
        built = _audit_stage(stage, validation, artifact_sha256)
        _replace_directory_transactionally(stage, destination)
        return replace(
            built,
            output=destination,
            archive_path=destination / contract.archive_name,
            total_bytes=sum(len(value) for value in members.values()),
        )
    except BaseException:
        _remove_path(stage)
        raise
