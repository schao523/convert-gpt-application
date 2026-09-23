"""Read-only Git byte evidence for staged marketplace artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import subprocess
from tempfile import TemporaryDirectory
from typing import Sequence


@dataclass(frozen=True)
class GitEvidenceReport:
    status: str
    codes: tuple[str, ...]
    files_checked: int


def exact_byte_attributes(scopes: Sequence[str]) -> str:
    """Return sorted `.gitattributes` rules that disable text conversion."""

    normalized = sorted({_scope(scope) for scope in scopes})
    return "".join(
        f"/{scope.rstrip('/')}/** -text whitespace=cr-at-eol\n"
        for scope in normalized
    )


def verify_git_evidence(
    marketplace: Path,
    scopes: Sequence[str],
    *,
    commit: str | None = None,
    fresh_checkout: bool = False,
) -> GitEvidenceReport:
    """Compare scoped working, index, commit, and optional checkout bytes."""

    root = Path(marketplace).resolve()
    normalized = tuple(sorted({_scope(scope) for scope in scopes}))
    codes: set[str] = set()
    index_entries = _index_entries(root, normalized)
    stage_zero = {path: oid for path, stage, oid in index_entries if stage == "0"}
    if any(stage != "0" for _, stage, _ in index_entries):
        codes.add("incomplete_index_entry")

    working = _working_files(root, normalized)
    if set(working) - set(stage_zero):
        codes.add("untracked_artifact")
    for path, oid in stage_zero.items():
        index_bytes = _git_bytes(root, "cat-file", "blob", oid)
        if path not in working or working[path].read_bytes() != index_bytes:
            codes.add("working_tree_mismatch")
    committed: dict[str, str] = {}
    resolved_commit: str | None = None
    if commit is not None:
        resolved_commit = _resolve_commit(root, commit)
        if resolved_commit is None:
            codes.add("commit_not_found")
        else:
            committed = _tree_entries(root, resolved_commit, normalized)
            if set(committed) != set(stage_zero) or any(
                committed[path] != stage_zero[path]
                for path in set(committed) & set(stage_zero)
            ):
                codes.add("index_blob_mismatch")

    checked_paths = tuple(sorted(set(working) | set(stage_zero) | set(committed)))
    attributes = _attributes(root, checked_paths)
    if any(not _deterministic_attributes(attributes.get(path)) for path in checked_paths):
        codes.add("exact_byte_attribute_missing")

    if fresh_checkout:
        if commit is None:
            codes.add("fresh_checkout_commit_required")
        elif resolved_commit is not None:
            _verify_fresh_checkout(root, resolved_commit, committed, codes)

    return GitEvidenceReport(
        status="PASS" if not codes else "FAIL",
        codes=tuple(sorted(codes)),
        files_checked=len(checked_paths),
    )


def _index_entries(root: Path, scopes: Sequence[str]) -> tuple[tuple[str, str, str], ...]:
    payload = _git_bytes(root, "ls-files", "--stage", "-z", "--", *scopes)
    entries = []
    for record in payload.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        _mode, oid, stage = metadata.decode("ascii").split(" ")
        entries.append((raw_path.decode("utf-8", "surrogateescape"), stage, oid))
    return tuple(entries)


def _tree_entries(root: Path, commit: str, scopes: Sequence[str]) -> dict[str, str]:
    payload = _git_bytes(root, "ls-tree", "-r", "-z", commit, "--", *scopes)
    entries: dict[str, str] = {}
    for record in payload.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        _mode, kind, oid = metadata.decode("ascii").split(" ")
        if kind == "blob":
            entries[raw_path.decode("utf-8", "surrogateescape")] = oid
    return entries


def _resolve_commit(root: Path, commit: str) -> str | None:
    completed = _run_git(root, "rev-parse", "--verify", f"{commit}^{{commit}}")
    if completed.returncode != 0:
        return None
    return completed.stdout.decode("ascii").strip()


def _working_files(root: Path, scopes: Sequence[str]) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for scope in scopes:
        base = root / Path(scope)
        if base.is_file():
            files[scope] = base
        elif base.is_dir():
            for path in base.rglob("*"):
                if path.is_file():
                    files[path.relative_to(root).as_posix()] = path
    return files


def _attributes(root: Path, paths: Sequence[str]) -> dict[str, tuple[str, str]]:
    if not paths:
        return {}
    payload = _git_bytes(root, "check-attr", "-z", "text", "eol", "--", *paths)
    parts = payload.split(b"\0")
    raw: dict[str, dict[str, str]] = {}
    for index in range(0, len(parts) - 2, 3):
        path = parts[index].decode("utf-8", "surrogateescape")
        attribute = parts[index + 1].decode("ascii")
        raw.setdefault(path, {})[attribute] = parts[index + 2].decode("utf-8", "replace")
    return {
        path: (values.get("text", "unspecified"), values.get("eol", "unspecified"))
        for path, values in raw.items()
    }


def _deterministic_attributes(policy: tuple[str, str] | None) -> bool:
    if policy is None:
        return False
    text, eol = policy
    return text == "unset" or (text == "set" and eol in {"lf", "crlf"})


def _verify_fresh_checkout(
    root: Path,
    commit: str,
    committed: dict[str, str],
    codes: set[str],
) -> None:
    with TemporaryDirectory(prefix="git-evidence-") as temporary:
        checkout = Path(temporary) / "checkout"
        clone = subprocess.run(
            ["git", "-c", "core.autocrlf=true", "clone", "--no-hardlinks", "--no-checkout", str(root), str(checkout)],
            shell=False,
            timeout=30,
            check=False,
            capture_output=True,
        )
        if clone.returncode != 0:
            codes.add("fresh_checkout_failed")
            return
        checked_out = subprocess.run(
            ["git", "-c", "core.autocrlf=true", "checkout", "--detach", commit],
            cwd=checkout,
            shell=False,
            timeout=30,
            check=False,
            capture_output=True,
        )
        if checked_out.returncode != 0:
            codes.add("fresh_checkout_failed")
            return
        for path, oid in committed.items():
            candidate = checkout / Path(path)
            expected = _git_bytes(root, "cat-file", "blob", oid)
            if not candidate.is_file() or candidate.read_bytes() != expected:
                codes.add("fresh_checkout_mismatch")


def _git_bytes(root: Path, *arguments: str) -> bytes:
    completed = _run_git(root, *arguments)
    if completed.returncode != 0:
        raise ValueError("git_evidence_command_failed")
    return completed.stdout


def _run_git(root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        shell=False,
        timeout=30,
        check=False,
        capture_output=True,
    )


def _scope(value: str) -> str:
    text = str(value).replace("\\", "/").strip("/")
    path = PurePosixPath(text)
    if not text or path.is_absolute() or ".." in path.parts:
        raise ValueError("invalid_git_scope")
    return path.as_posix()
