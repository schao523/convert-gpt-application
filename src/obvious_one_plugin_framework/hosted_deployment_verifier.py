"""Independent verification for complete OpenAI-hosted deployment artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
from typing import Mapping
import zipfile

from .content_policy import canonical_content_bytes
from .hosted_deployment_contract import HostedDeploymentContract, HostedDeploymentError
from .hosted_deployment_planner import validate_hosted_deployment
from .verification import ExpansionContext, VerificationCommand, expand_argv


_COMMAND_TIMEOUT_SECONDS = 30.0
_FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_REPORT_NAMES = (
    "deployment-manifest.json",
    "validation-report.json",
    "deployment-report.json",
)
_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


@dataclass(frozen=True)
class CapabilityEvidence:
    package_static: str
    local_execution: str
    hosted_execution: str


@dataclass(frozen=True)
class HostedDeploymentVerification:
    artifact_sha256: str
    archive_sha256: str
    archive_paths: tuple[str, ...]
    capabilities: Mapping[str, CapabilityEvidence]
    gates: Mapping[str, str]
    upload_status: str
    installation_status: str
    marketplace_status: str
    publication_status: str


def _digest(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _file_digest(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _json_object(path: Path, code: str) -> Mapping[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HostedDeploymentError(code, path.name) from exc
    if not isinstance(value, dict):
        raise HostedDeploymentError(code, path.name)
    return value


def _core_artifact_hash(artifact: Path, archive_name: str) -> str:
    digest = sha256()
    for name in sorted((archive_name, "deployment-manifest.json", "validation-report.json")):
        payload = (artifact / name).read_bytes()
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(sha256(payload).digest())
    return digest.hexdigest()


def _safe_archive_name(info: zipfile.ZipInfo) -> str:
    original = getattr(info, "orig_filename", info.filename)
    if "\\" in original or original.startswith(("/", "\\")):
        raise HostedDeploymentError("hosted_archive_unsafe_path", original)
    candidate = PurePosixPath(original)
    if not original or candidate.is_absolute() or ".." in candidate.parts:
        raise HostedDeploymentError("hosted_archive_unsafe_path", original)
    if any(part in {"", "."} or part.endswith(":") for part in candidate.parts):
        raise HostedDeploymentError("hosted_archive_unsafe_path", original)
    if info.flag_bits & 0x1:
        raise HostedDeploymentError("hosted_archive_encrypted", original)
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise HostedDeploymentError("hosted_archive_link_forbidden", original)
    if info.is_dir():
        raise HostedDeploymentError("hosted_archive_directory_entry", original)
    if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
        raise HostedDeploymentError("hosted_archive_compression_unsupported", original)
    return candidate.as_posix()


def _read_archive(path: Path) -> tuple[tuple[str, ...], Mapping[str, bytes], tuple[zipfile.ZipInfo, ...]]:
    try:
        with zipfile.ZipFile(path) as archive:
            infos = tuple(archive.infolist())
            names = tuple(_safe_archive_name(info) for info in infos)
            if len(names) != len(set(names)) or len(names) != len({name.casefold() for name in names}):
                raise HostedDeploymentError("hosted_archive_duplicate_path")
            members = {name: archive.read(info) for name, info in zip(names, infos)}
    except HostedDeploymentError:
        raise
    except (OSError, RuntimeError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise HostedDeploymentError("hosted_archive_invalid") from exc
    return names, members, infos


def _validate_manifest(
    contract: HostedDeploymentContract,
    manifest: Mapping[str, object],
    members: Mapping[str, bytes],
    archive_sha256: str,
) -> None:
    if (
        manifest.get("manifest_schema") != "hosted-deployment-manifest-v1"
        or manifest.get("application_id") != contract.application_id
        or manifest.get("package_name") != contract.package_name
        or manifest.get("version") != contract.target_version
        or manifest.get("operation") != contract.operation
        or manifest.get("archive") != contract.archive_name
    ):
        raise HostedDeploymentError("hosted_manifest_identity_mismatch")
    if manifest.get("archive_sha256") != archive_sha256:
        raise HostedDeploymentError("hosted_report_hash_mismatch")
    records = manifest.get("members")
    if not isinstance(records, list):
        raise HostedDeploymentError("hosted_manifest_member_mismatch")
    expected = [
        {"path": name, "sha256": _digest(content), "size": len(content)}
        for name, content in sorted(members.items())
    ]
    observed: list[dict[str, object]] = []
    for record in records:
        if not isinstance(record, dict):
            raise HostedDeploymentError("hosted_manifest_member_mismatch")
        observed.append({key: record.get(key) for key in ("path", "sha256", "size")})
    if observed != expected or manifest.get("member_count") != len(members):
        raise HostedDeploymentError("hosted_manifest_member_mismatch")
    if manifest.get("total_bytes") != sum(len(content) for content in members.values()):
        raise HostedDeploymentError("hosted_manifest_member_mismatch")


def _validate_member_content(contract: HostedDeploymentContract, members: Mapping[str, bytes]) -> None:
    validation = validate_hosted_deployment(contract)
    for name in validation.archive_paths:
        expected = canonical_content_bytes(validation.source_paths[name], validation.content_policies[name])
        if members.get(name) != expected:
            raise HostedDeploymentError("hosted_archive_source_mismatch", name)

    skill_roots = {
        name.split("/")[1]
        for name in members
        if name.startswith("skills/") and name.endswith("/SKILL.md") and name.count("/") >= 2
    }
    if skill_roots != set(contract.expected_skills):
        raise HostedDeploymentError("expected_skill_mismatch")
    for skill in contract.explicit_only_skills:
        policy_name = f"skills/{skill}/agents/openai.yaml"
        try:
            policy = members[policy_name].decode("utf-8")
        except (KeyError, UnicodeError) as exc:
            raise HostedDeploymentError("explicit_only_policy_missing", skill) from exc
        if "allow_implicit_invocation: false" not in policy:
            raise HostedDeploymentError("explicit_only_policy_missing", skill)

    for name, payload in members.items():
        if name.endswith(".json"):
            try:
                json.loads(payload.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise HostedDeploymentError("hosted_json_invalid", name) from exc
        if name.endswith(".md"):
            try:
                text = payload.decode("utf-8")
            except UnicodeError as exc:
                raise HostedDeploymentError("hosted_reference_invalid", name) from exc
            parent = PurePosixPath(name).parent
            for raw_target in _LINK.findall(text):
                target = raw_target.strip().split("#", 1)[0].strip().strip("<>")
                if not target or "://" in target or target.startswith(("#", "mailto:")):
                    continue
                reference = parent.joinpath(PurePosixPath(target))
                if reference.is_absolute() or ".." in reference.parts:
                    raise HostedDeploymentError("hosted_reference_missing", f"{name}:{target}")
                normalized = reference.as_posix()
                if normalized not in members:
                    raise HostedDeploymentError("hosted_reference_missing", f"{name}:{target}")


def _find_command(contract: HostedDeploymentContract, command_id: str) -> VerificationCommand:
    for command in contract.application.verification.commands:
        if command.command_id == command_id:
            return command
    raise HostedDeploymentError("capability_local_verification_command_missing", command_id)


def _repository_root(application_root: Path) -> Path:
    for candidate in (application_root, *application_root.parents):
        if (candidate / ".git").exists():
            return candidate
    return application_root.parent


def _run_command(contract: HostedDeploymentContract, command: VerificationCommand) -> None:
    with tempfile.TemporaryDirectory(prefix="hosted-deployment-verification-") as temporary:
        diagnostics = Path(temporary).resolve()
        context = ExpansionContext(
            python=sys.executable,
            repository_root=_repository_root(contract.application_root),
            application_root=contract.application_root,
            diagnostics=diagnostics,
            plugin_id=contract.application.plugin_id,
            application_id=contract.application.application_id,
            version=contract.application.version,
        )
        argv = expand_argv(command.argv, context)
        environment = dict(os.environ)
        for key in tuple(environment):
            if any(key.startswith(prefix) for prefix in command.clean_environment_prefixes):
                del environment[key]
        try:
            completed = subprocess.run(
                argv,
                cwd=contract.application_root,
                env=environment,
                capture_output=True,
                check=False,
                timeout=_COMMAND_TIMEOUT_SECONDS,
            )
            (diagnostics / "stdout.log").write_bytes(completed.stdout)
            (diagnostics / "stderr.log").write_bytes(completed.stderr)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise HostedDeploymentError(
                "capability_local_verification_failed", command.command_id
            ) from exc
        if completed.returncode != 0:
            raise HostedDeploymentError(
                "capability_local_verification_failed", command.command_id
            )


def _capability_evidence(contract: HostedDeploymentContract) -> Mapping[str, CapabilityEvidence]:
    result: dict[str, CapabilityEvidence] = {}
    for capability in sorted(contract.capabilities, key=lambda item: item.capability_id):
        local = "NOT APPLICABLE"
        if capability.local_verification_test is not None:
            command = _find_command(contract, capability.local_verification_test)
            _run_command(contract, command)
            local = "STATICALLY VERIFIED"
        result[capability.capability_id] = CapabilityEvidence(
            package_static="STATICALLY VERIFIED",
            local_execution=local,
            hosted_execution="NOT VERIFIED",
        )
    return result


def verify_hosted_deployment(
    contract: HostedDeploymentContract,
    artifact: Path,
) -> HostedDeploymentVerification:
    """Verify a built artifact without mutating it or any external platform."""

    validation = validate_hosted_deployment(contract)
    root = Path(artifact).resolve()
    if not root.is_dir() or root.is_symlink():
        raise HostedDeploymentError("hosted_artifact_invalid")
    expected_files = {contract.archive_name, *_REPORT_NAMES}
    actual_entries = tuple(root.iterdir())
    if any(entry.is_symlink() or not entry.is_file() for entry in actual_entries):
        raise HostedDeploymentError("hosted_artifact_set_mismatch")
    if {entry.name for entry in actual_entries} != expected_files:
        raise HostedDeploymentError("hosted_artifact_set_mismatch")

    archive_path = root / contract.archive_name
    archive_paths, members, infos = _read_archive(archive_path)
    if archive_paths != validation.archive_paths:
        raise HostedDeploymentError("complete_archive_mismatch")
    if any(info.date_time != _FIXED_TIMESTAMP for info in infos):
        raise HostedDeploymentError("archive_metadata_mismatch")

    archive_sha256 = _file_digest(archive_path)
    manifest = _json_object(root / "deployment-manifest.json", "hosted_report_invalid")
    validation_report = _json_object(root / "validation-report.json", "hosted_report_invalid")
    deployment_report = _json_object(root / "deployment-report.json", "hosted_report_invalid")
    _validate_manifest(contract, manifest, members, archive_sha256)
    if (
        validation_report.get("report_schema") != "hosted-validation-report-v1"
        or validation_report.get("application_id") != contract.application_id
        or validation_report.get("status") != "PASS"
    ):
        raise HostedDeploymentError("hosted_validation_report_mismatch")
    if (
        deployment_report.get("report_schema") != "hosted-deployment-report-v1"
        or deployment_report.get("application_id") != contract.application_id
        or deployment_report.get("package_name") != contract.package_name
        or deployment_report.get("target_version") != contract.target_version
        or deployment_report.get("operation") != contract.operation
    ):
        raise HostedDeploymentError("hosted_deployment_report_mismatch")
    artifact_sha256 = _core_artifact_hash(root, contract.archive_name)
    if (
        deployment_report.get("archive_sha256") != archive_sha256
        or deployment_report.get("artifact_sha256") != artifact_sha256
    ):
        raise HostedDeploymentError("hosted_report_hash_mismatch")
    if (
        deployment_report.get("upload_status") != "NOT_PERFORMED"
        or deployment_report.get("installation_status") != "NOT VERIFIED"
        or deployment_report.get("marketplace_status") != "NOT_PERFORMED"
        or deployment_report.get("public_submission_status") != "NOT_PERFORMED"
    ):
        raise HostedDeploymentError("hosted_external_status_mismatch")

    _validate_member_content(contract, members)
    capabilities = _capability_evidence(contract)
    return HostedDeploymentVerification(
        artifact_sha256=artifact_sha256,
        archive_sha256=archive_sha256,
        archive_paths=archive_paths,
        capabilities=capabilities,
        gates={
            "capabilities": "PASS",
            "complete_archive": "PASS",
            "manifests": "PASS",
            "references": "PASS",
            "reports": "PASS",
            "skills": "PASS",
        },
        upload_status="NOT_PERFORMED",
        installation_status="NOT VERIFIED",
        marketplace_status="NOT_PERFORMED",
        publication_status="NOT_PERFORMED",
    )
