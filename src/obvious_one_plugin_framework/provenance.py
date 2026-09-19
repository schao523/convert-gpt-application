"""Deterministic, application-configured source provenance."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Mapping, Sequence

from .verification import ApplicationConfig, ProvenanceInventoryRule


_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_COMMON_KEYS = {
    "schema_version",
    "source_repository",
    "source_commit",
    "marketplace_repository",
    "marketplace_commit",
    "incorporated_branches",
    "source_inventory",
}
_SCHEMA_KEYS = {1: _COMMON_KEYS, 2: _COMMON_KEYS | {"application_id", "plugin_id"}}
_SCHEMA_KEYS[3] = (_SCHEMA_KEYS[2] - {"source_commit"}) | {"source_tree_sha256"}
_INVENTORY_KEYS = {"classification", "path", "sha256"}


class ProvenanceError(ValueError):
    """Raised when provenance cannot be generated or validated safely."""


def _digest(path: Path) -> str:
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _git_head(repository: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        shell=False,
        check=False,
    )
    if completed.returncode:
        raise ProvenanceError("git_commit_unavailable")
    commit = completed.stdout.strip()
    if not _COMMIT.fullmatch(commit):
        raise ProvenanceError("invalid_git_commit")
    return commit


def _safe_relative(value: str, error: str) -> PurePosixPath:
    normalized = value.replace("\\", "/")
    candidate = PurePosixPath(normalized)
    if (
        candidate.is_absolute()
        or ".." in candidate.parts
        or (candidate.parts and candidate.parts[0].endswith(":"))
    ):
        raise ProvenanceError(error)
    return candidate


def inventory_source(
    source: Path,
    rules: Sequence[ProvenanceInventoryRule],
) -> tuple[dict[str, str], ...]:
    """Return a stable inventory selected only by declarative rules."""

    source_root = Path(source).resolve()
    if not source_root.is_dir():
        raise ProvenanceError("source_repository_missing")
    records: dict[str, dict[str, str]] = {}
    for rule in rules:
        relative_root = _safe_relative(rule.root.as_posix(), "inventory_root_escape")
        rule_root = (source_root / Path(*relative_root.parts)).resolve()
        if not rule_root.is_relative_to(source_root):
            raise ProvenanceError("inventory_root_escape")
        for pattern in rule.include:
            _safe_relative(pattern, "inventory_pattern_escape")
            for candidate in rule_root.glob(pattern):
                if candidate.is_symlink() or not candidate.is_file():
                    continue
                resolved = candidate.resolve()
                if not resolved.is_relative_to(source_root):
                    raise ProvenanceError("inventory_path_escape")
                relative = resolved.relative_to(source_root).as_posix()
                if relative in records:
                    if records[relative]["classification"] != rule.classification:
                        raise ProvenanceError("duplicate_inventory_path")
                    continue
                records[relative] = {
                    "classification": rule.classification,
                    "path": relative,
                    "sha256": _digest(resolved),
                }
    return tuple(
        sorted(records.values(), key=lambda item: (item["classification"], item["path"]))
    )


def build_provenance(
    config: ApplicationConfig,
    source_repo: Path,
    marketplace_repo: Path,
) -> dict[str, object]:
    """Build a schema-v2 provenance record for one configured application."""

    inventory = list(inventory_source(Path(source_repo), config.provenance.inventory_rules))
    common = {
        "application_id": config.application_id,
        "plugin_id": config.plugin_id,
        "source_repository": config.provenance.source_repository,
        "marketplace_repository": config.marketplace_repository,
        "marketplace_commit": _git_head(Path(marketplace_repo).resolve()),
        "incorporated_branches": list(config.provenance.incorporated_branches),
        "source_inventory": inventory,
    }
    try:
        return {"schema_version": 2, **common, "source_commit": _git_head(Path(source_repo).resolve())}
    except ProvenanceError as exc:
        if str(exc) != "git_commit_unavailable":
            raise
    encoded = json.dumps(
        inventory, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return {
        "schema_version": 3,
        **common,
        "source_tree_sha256": sha256(encoded).hexdigest(),
    }


def _required_text(payload: Mapping[str, object], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise ProvenanceError(f"invalid_{field}")
    return value


def validate_provenance(
    payload: Mapping[str, object],
    config: ApplicationConfig,
) -> None:
    """Validate identity and integrity metadata for one application."""

    version = payload.get("schema_version")
    if type(version) is not int or version not in (1, 2, 3):
        raise ProvenanceError("unsupported_schema_version")
    if set(payload) - _SCHEMA_KEYS[version]:
        raise ProvenanceError("unknown_provenance_field")
    if version in (2, 3):
        if _required_text(payload, "application_id") != config.application_id:
            raise ProvenanceError("application_identity_mismatch")
        if _required_text(payload, "plugin_id") != config.plugin_id:
            raise ProvenanceError("plugin_identity_mismatch")
    if _required_text(payload, "source_repository") != config.provenance.source_repository:
        raise ProvenanceError("source_repository_mismatch")
    if _required_text(payload, "marketplace_repository") != config.marketplace_repository:
        raise ProvenanceError("marketplace_identity_mismatch")
    if version == 3:
        if not _DIGEST.fullmatch(_required_text(payload, "source_tree_sha256")):
            raise ProvenanceError("invalid_source_tree_sha256")
    elif not _COMMIT.fullmatch(_required_text(payload, "source_commit")):
        raise ProvenanceError("invalid_source_commit")
    if not _COMMIT.fullmatch(_required_text(payload, "marketplace_commit")):
        raise ProvenanceError("invalid_marketplace_commit")
    branches = payload.get("incorporated_branches")
    if not isinstance(branches, list) or not all(
        isinstance(item, str) and item for item in branches
    ):
        raise ProvenanceError("invalid_incorporated_branches")
    if tuple(branches) != config.provenance.incorporated_branches:
        raise ProvenanceError("incorporated_branches_mismatch")
    inventory = payload.get("source_inventory")
    if not isinstance(inventory, list):
        raise ProvenanceError("invalid_source_inventory")
    paths: set[str] = set()
    for item in inventory:
        if not isinstance(item, dict):
            raise ProvenanceError("invalid_inventory_record")
        if set(item) - _INVENTORY_KEYS:
            raise ProvenanceError("unknown_inventory_field")
        classification = item.get("classification")
        if not isinstance(classification, str) or not classification.strip():
            raise ProvenanceError("invalid_inventory_classification")
        path = item.get("path")
        if not isinstance(path, str) or not path:
            raise ProvenanceError("invalid_inventory_path")
        normalized = _safe_relative(path, "inventory_path_escape").as_posix()
        if normalized in {"", "."}:
            raise ProvenanceError("invalid_inventory_path")
        if normalized in paths:
            raise ProvenanceError("duplicate_inventory_path")
        paths.add(normalized)
        digest = item.get("sha256")
        if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
            raise ProvenanceError("invalid_inventory_digest")
