"""Deterministic archives for assets owned by one plugin."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import zipfile

from .contract import AssetGroup, DistributionContract, validate_contract


ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
ZIP_CREATE_SYSTEM = 0
ZIP_COMPRESSION = zipfile.ZIP_STORED


class AssetBuildError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code if not detail else f"{code}: {detail}")
        self.code = code


@dataclass(frozen=True)
class MemberRecord:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ArchiveRecord:
    name: str
    owner_plugin_id: str
    size: int
    sha256: str
    members: tuple[MemberRecord, ...]
    install_subdir: str


def _sha_bytes(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _sha_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_source(root: Path, relative: str) -> Path:
    posix = PurePosixPath(relative)
    if posix.is_absolute() or ".." in posix.parts:
        raise AssetBuildError("source_path_escape", relative)
    candidate = (root / Path(*posix.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise AssetBuildError("source_path_escape", relative) from exc
    if not candidate.is_file():
        raise AssetBuildError("source_file_missing", relative)
    if candidate.is_symlink():
        raise AssetBuildError("source_link_forbidden", relative)
    return candidate


def _build_group(
    contract: DistributionContract,
    group: AssetGroup,
    output_dir: Path,
) -> ArchiveRecord:
    archive_name = group.archive_name.format(version=contract.version)
    output = output_dir / archive_name
    temporary = output.with_suffix(output.suffix + ".tmp")
    members: list[MemberRecord] = []
    if temporary.exists():
        temporary.unlink()
    try:
        with zipfile.ZipFile(temporary, "w", compression=ZIP_COMPRESSION) as archive:
            for relative in sorted(group.source_paths):
                source = _safe_source(contract.source_root, relative)
                payload = source.read_bytes()
                info = zipfile.ZipInfo(relative, ZIP_EPOCH)
                info.create_system = ZIP_CREATE_SYSTEM
                info.compress_type = ZIP_COMPRESSION
                info.external_attr = 0o100644 << 16
                archive.writestr(info, payload, compress_type=ZIP_COMPRESSION)
                members.append(MemberRecord(relative, len(payload), _sha_bytes(payload)))
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()
    return ArchiveRecord(
        name=archive_name,
        owner_plugin_id=contract.plugin_id,
        size=output.stat().st_size,
        sha256=_sha_file(output),
        members=tuple(members),
        install_subdir=group.install_subdir,
    )


def build_asset_groups(
    contract: DistributionContract,
    output_dir: Path,
) -> tuple[ArchiveRecord, ...]:
    validate_contract(contract, contract.source_root)
    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    return tuple(
        _build_group(contract, group, destination)
        for group in sorted(contract.rag.asset_groups, key=lambda item: item.name)
    )


def remote_manifest_data(
    contract: DistributionContract,
    records: tuple[ArchiveRecord, ...],
) -> dict[str, object]:
    release_tag = contract.release_tag_template.format(version=contract.version)
    base = f"https://github.com/{contract.release_repository}/releases/download/{release_tag}"
    groups = []
    for record in sorted(records, key=lambda item: item.name):
        item = asdict(record)
        item["members"] = [asdict(member) for member in record.members]
        item["url"] = f"{base}/{record.name}"
        groups.append(item)
    return {
        "schema_version": 1,
        "plugin_id": contract.plugin_id,
        "version": contract.version,
        "release_repository": contract.release_repository,
        "release_tag": release_tag,
        "asset_groups": groups,
    }


def write_remote_manifest(
    contract: DistributionContract,
    records: tuple[ArchiveRecord, ...],
    path: Path,
) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            remote_manifest_data(contract, records),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, destination)
