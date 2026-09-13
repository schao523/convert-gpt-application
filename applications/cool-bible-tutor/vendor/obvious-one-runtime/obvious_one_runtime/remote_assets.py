"""Verified download and safe extraction for plugin-owned asset archives."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path, PurePosixPath
import shutil
from typing import Mapping
from urllib.request import Request, urlopen
import zipfile


class SetupError(RuntimeError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code if not detail else f"{code}: {detail}")
        self.code = code


@dataclass(frozen=True)
class RemoteMemberRecord:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class RemoteAssetGroup:
    name: str
    url: str
    size: int
    sha256: str
    install_subdir: str
    members: tuple[RemoteMemberRecord, ...]


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_file(path: Path, size: int, sha256_hex: str) -> None:
    if not path.is_file() or path.stat().st_size != size:
        raise SetupError("download_size_mismatch", str(path))
    if sha256_file(path) != sha256_hex.lower():
        raise SetupError("download_digest_mismatch", str(path))


def download_verified(url: str, destination: Path, size: int, sha256_hex: str) -> Path:
    if not url.startswith("https://"):
        raise SetupError("https_required", url)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file():
        try:
            verify_file(destination, size, sha256_hex)
            return destination
        except SetupError:
            destination.unlink()
    partial = destination.with_suffix(destination.suffix + ".partial")
    offset = partial.stat().st_size if partial.is_file() else 0
    request = Request(url, headers={"Range": f"bytes={offset}-"} if offset else {})
    try:
        with urlopen(request, timeout=60) as response:
            append = offset > 0 and getattr(response, "status", None) == 206
            mode = "ab" if append else "wb"
            with partial.open(mode) as stream:
                shutil.copyfileobj(response, stream, length=1024 * 1024)
    except OSError as exc:
        raise SetupError("download_failed", url) from exc
    verify_file(partial, size, sha256_hex)
    os.replace(partial, destination)
    return destination


def _safe_member(name: str) -> PurePosixPath:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts or any(part in {"", "."} for part in path.parts):
        raise SetupError("unsafe_archive_member", name)
    return path


def extract_verified(
    archive: Path,
    destination: Path,
    expected_members: Mapping[str, RemoteMemberRecord],
) -> None:
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    try:
        with zipfile.ZipFile(archive) as source:
            for info in source.infolist():
                member = _safe_member(info.filename)
                name = member.as_posix()
                if name in seen or name not in expected_members:
                    raise SetupError("unexpected_archive_member", name)
                seen.add(name)
                mode = info.external_attr >> 16
                if mode & 0o170000 in {0o120000, 0o020000, 0o060000}:
                    raise SetupError("unsafe_archive_member", name)
                if info.is_dir():
                    raise SetupError("unexpected_archive_directory", name)
                output = (destination / Path(*member.parts)).resolve()
                try:
                    output.relative_to(destination)
                except ValueError as exc:
                    raise SetupError("unsafe_archive_member", name) from exc
                payload = source.read(info)
                record = expected_members[name]
                if len(payload) != record.size or sha256(payload).hexdigest() != record.sha256.lower():
                    raise SetupError("archive_member_digest_mismatch", name)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(payload)
    except zipfile.BadZipFile as exc:
        raise SetupError("invalid_archive", str(archive)) from exc
    if seen != set(expected_members):
        missing = sorted(set(expected_members) - seen)
        raise SetupError("archive_member_missing", missing[0])
