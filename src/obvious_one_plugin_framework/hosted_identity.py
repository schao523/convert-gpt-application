"""Safe, one-time identity import for an exported hosted plugin archive."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from typing import Mapping
import zipfile

from .hosted_deployment_contract import HostedDeploymentError
from .results import ArtifactRecord, MutationRecord, OperationResult
from .verification import VerificationConfigError, load_application_config_path


_IDENTITY_MEMBERS = (".codex-plugin/plugin.json", "plugin.json")
_SUPPORTED_COMPRESSION = frozenset({zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED})
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")
_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


@dataclass(frozen=True)
class ArchiveLimits:
    max_members: int = 4096
    max_member_bytes: int = 64 * 1024 * 1024
    max_total_bytes: int = 256 * 1024 * 1024

    def __post_init__(self) -> None:
        if self.max_members <= 0 or self.max_member_bytes <= 0 or self.max_total_bytes <= 0:
            raise ValueError("invalid_archive_limits")


@dataclass(frozen=True)
class HostedIdentityCandidate:
    package_name: str
    version: str


@dataclass(frozen=True)
class HostedIdentityInventory:
    archive_sha256: str
    package_name: str
    version: str
    identity_members: tuple[tuple[str, str, int], ...]
    presentation_asset_hashes: Mapping[str, str]


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member_name(name: str) -> str:
    if not name or "\x00" in name:
        raise HostedDeploymentError("archive_path_escape")
    if "\\" in name:
        raise HostedDeploymentError("archive_path_alias", name)
    if name.startswith(("/", "//")) or _WINDOWS_DRIVE.match(name):
        raise HostedDeploymentError("archive_path_escape", name)
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise HostedDeploymentError("archive_path_escape", name)
    return path.as_posix()


def _is_link(info: zipfile.ZipInfo) -> bool:
    if info.create_system == 3:
        return stat.S_IFMT((info.external_attr >> 16) & 0xFFFF) == stat.S_IFLNK
    return bool((info.external_attr & 0xFFFF) & 0x0400)


def _stream_member_hash(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    digest = sha256()
    try:
        with archive.open(info, "r") as source:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise HostedDeploymentError("archive_member_read_failed", info.filename) from exc
    return digest.hexdigest()


def _manifest_payload(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> Mapping[str, object]:
    try:
        raw = archive.read(info)
        value = json.loads(raw.decode("utf-8"))
    except (OSError, RuntimeError, UnicodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        raise HostedDeploymentError("hosted_manifest_invalid", info.filename) from exc
    if not isinstance(value, dict):
        raise HostedDeploymentError("hosted_manifest_invalid", info.filename)
    return value


def _identity_from_manifests(manifests: list[Mapping[str, object]]) -> HostedIdentityCandidate:
    candidates: list[HostedIdentityCandidate] = []
    for manifest in manifests:
        name = manifest.get("name")
        version = manifest.get("version")
        if not isinstance(name, str) or not name.strip() or not isinstance(version, str):
            raise HostedDeploymentError("hosted_identity_missing")
        match = _SEMVER.fullmatch(version)
        if match is None or (
            match.group(4) is not None
            and any(item.isdigit() and len(item) > 1 and item.startswith("0") for item in match.group(4).split("."))
        ):
            raise HostedDeploymentError("hosted_identity_missing", "version")
        candidates.append(HostedIdentityCandidate(name, version))
    first = candidates[0]
    if any(item != first for item in candidates[1:]):
        raise HostedDeploymentError("hosted_manifest_identity_mismatch")
    return first


def inventory_hosted_identity_archive(
    path: Path,
    limits: ArchiveLimits = ArchiveLimits(),
) -> HostedIdentityInventory:
    archive_path = Path(path)
    if not archive_path.is_file():
        raise HostedDeploymentError("hosted_archive_missing")
    archive_digest = _hash_file(archive_path)
    try:
        archive = zipfile.ZipFile(archive_path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise HostedDeploymentError("hosted_archive_invalid") from exc
    with archive:
        infos = archive.infolist()
        if len(infos) > limits.max_members:
            raise HostedDeploymentError("archive_member_limit")
        names: list[str] = []
        total = 0
        for info in infos:
            name = _safe_member_name(info.orig_filename)
            names.append(name)
            if info.flag_bits & 0x1:
                raise HostedDeploymentError("archive_encrypted_member", name)
            if _is_link(info):
                raise HostedDeploymentError("archive_link_member", name)
            if info.compress_type not in _SUPPORTED_COMPRESSION:
                raise HostedDeploymentError("archive_compression_unsupported", name)
            if info.file_size > limits.max_member_bytes:
                raise HostedDeploymentError("archive_member_too_large", name)
            total += info.file_size
            if total > limits.max_total_bytes:
                raise HostedDeploymentError("archive_expansion_limit")
        if len(names) != len(set(names)):
            raise HostedDeploymentError("archive_duplicate_member")
        if len(names) != len({name.casefold() for name in names}):
            raise HostedDeploymentError("archive_casefold_collision")

        by_name = {info.filename: info for info in infos if not info.is_dir()}
        manifest_infos = [by_name[name] for name in _IDENTITY_MEMBERS if name in by_name]
        if not manifest_infos:
            raise HostedDeploymentError("hosted_manifest_missing")
        candidate = _identity_from_manifests([
            _manifest_payload(archive, info) for info in manifest_infos
        ])
        identity_members = tuple(
            (info.filename, _stream_member_hash(archive, info), info.file_size)
            for info in sorted(manifest_infos, key=lambda item: item.filename)
        )
        presentation_assets = {
            info.filename: _stream_member_hash(archive, info)
            for info in sorted(infos, key=lambda item: item.filename)
            if not info.is_dir() and info.filename.startswith("assets/")
        }
    return HostedIdentityInventory(
        archive_sha256=archive_digest,
        package_name=candidate.package_name,
        version=candidate.version,
        identity_members=identity_members,
        presentation_asset_hashes=presentation_assets,
    )


def _proposal_bytes(application_id: str, inventory: HostedIdentityInventory) -> bytes:
    payload = {
        "proposal_schema": "hosted-identity-proposal-v1",
        "application_id": application_id,
        "archive_sha256": inventory.archive_sha256,
        "candidate": {
            "package_name": inventory.package_name,
            "last_confirmed_version": inventory.version,
            "origin": "imported_hosted_archive",
        },
        "identity_members": [
            {"path": name, "sha256": digest, "size": size}
            for name, digest, size in inventory.identity_members
        ],
        "presentation_asset_hashes": dict(sorted(inventory.presentation_asset_hashes.items())),
        "deployment_confirmation": {
            "status": "unresolved",
            "recorded_at": None,
            "evidence_reference": None,
        },
    }
    return (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_new_file_transactionally(destination: Path, payload: bytes) -> bool:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return False
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=f".{destination.name}.", suffix=".tmp", delete=False) as temporary:
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        try:
            os.link(temporary_name, destination)
        except FileExistsError:
            return False
        return True
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def propose_hosted_identity(
    application_path: Path,
    archive: Path,
    output: Path,
) -> OperationResult:
    operation = "import-hosted-identity"
    destination = Path(output)
    if destination.exists():
        return OperationResult(operation, "FAIL", "hosted_identity_proposal_exists")
    config_path = Path(application_path).resolve()
    if config_path.is_dir():
        config_path = config_path / "conversion.json"
    try:
        application = load_application_config_path(config_path, config_path.parent)
    except VerificationConfigError as exc:
        raise HostedDeploymentError("invalid_application_config", str(exc)) from exc
    inventory = inventory_hosted_identity_archive(Path(archive))
    payload = _proposal_bytes(application.application_id, inventory)
    if not _write_new_file_transactionally(destination, payload):
        return OperationResult(operation, "FAIL", "hosted_identity_proposal_exists")
    digest = sha256(payload).hexdigest()
    return OperationResult(
        operation,
        "BLOCKED",
        "hosted_identity_approval_required",
        artifacts=(ArtifactRecord(destination.name, "hosted_identity_proposal", digest, len(payload)),),
        mutations=(MutationRecord(destination.name, "created"),),
        evidence={
            "application_id": application.application_id,
            "archive_sha256": inventory.archive_sha256,
            "package_name": inventory.package_name,
            "version": inventory.version,
            "approval_status": "UNRESOLVED",
        },
    )
