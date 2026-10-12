"""Canonical identity-bound receipts for marketplace filesystem verification."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Mapping

from .results import ArtifactRecord, Diagnostic, OperationResult

if TYPE_CHECKING:
    from .marketplace import PreparationCatalog


RECEIPT_SCHEMA = "marketplace-filesystem-verification-receipt-v1"
_TOP_LEVEL_KEYS = {
    "schema",
    "marketplace_id",
    "operation",
    "status",
    "marketplace_identity",
    "controls",
    "plugins",
    "verification_profile",
    "receipt_sha256",
}
_CONTROL_PATHS = {
    "preparation_catalog": None,
    "validation_registry": ".obvious-one-validation.json",
    "marketplace_verifier": "tools/verify_marketplace.py",
    "marketplace_selector": "tools/select_marketplace_plugins.py",
}
_DIGEST_KEYS = frozenset(_CONTROL_PATHS)


def marketplace_tree_identity(root: Path, *, exclude_git: bool = True) -> dict[str, object]:
    """Return a portable SHA-256 identity for every regular file below root."""

    tree = Path(root).resolve()
    if not tree.is_dir():
        raise ValueError("marketplace_destination_missing")
    _reject_links(tree)
    records: list[dict[str, object]] = []
    for path in sorted(
        tree.rglob("*"),
        key=lambda candidate: candidate.relative_to(tree).as_posix(),
    ):
        relative = path.relative_to(tree)
        if path.is_file() and (not exclude_git or ".git" not in relative.parts):
            data = path.read_bytes()
            records.append(
                {
                    "path": relative.as_posix(),
                    "size": len(data),
                    "sha256": sha256(data).hexdigest(),
                }
            )
    encoded = json.dumps(
        records,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return {
        "content_sha256": sha256(encoded).hexdigest(),
        "file_count": len(records),
        "total_bytes": sum(int(record["size"]) for record in records),
        "files": records,
    }


def build_marketplace_filesystem_receipt(
    catalog: PreparationCatalog,
    marketplace: Path,
    verification: OperationResult,
) -> dict[str, object]:
    """Build a receipt only for the exact marketplace tree already verified."""

    root = Path(marketplace).resolve()
    identity = marketplace_tree_identity(root)
    _require_passing_verification(verification, root, identity)
    payload = _current_payload(catalog, root, identity)
    payload["receipt_sha256"] = _payload_digest(payload)
    _validate_shape(payload)
    return payload


def write_marketplace_filesystem_receipt(
    catalog: PreparationCatalog,
    marketplace: Path,
    verification: OperationResult,
    output: Path,
) -> ArtifactRecord:
    """Write one receipt transactionally outside the marketplace tree."""

    root = Path(marketplace).resolve()
    destination = validate_marketplace_receipt_output(
        catalog,
        root,
        output,
    )
    payload = build_marketplace_filesystem_receipt(catalog, root, verification)
    encoded = _document_bytes(payload)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".marketplace-receipt-", dir=destination.parent) as temporary:
        staged = Path(temporary) / destination.name
        staged.write_bytes(encoded)
        os.replace(staged, destination)
    return ArtifactRecord(
        destination.name,
        "marketplace_filesystem_verification_receipt",
        sha256(encoded).hexdigest(),
        len(encoded),
    )


def validate_marketplace_receipt_output(
    catalog: PreparationCatalog,
    marketplace: Path,
    output: Path,
) -> Path:
    """Return a safe receipt destination without following linked components."""

    root = Path(marketplace).resolve()
    lexical = Path(os.path.abspath(Path(output)))
    for component in reversed((lexical, *lexical.parents)):
        if _path_is_link(component):
            raise ValueError("unsafe_receipt_output")
    destination = lexical.resolve()
    if (
        destination == root
        or destination.is_relative_to(root)
        or root.is_relative_to(destination)
    ):
        raise ValueError("receipt_output_overlaps_marketplace")
    if destination == catalog.catalog_path.resolve():
        raise ValueError("unsafe_receipt_output")
    repository = catalog.repository_root.resolve()
    if destination.is_relative_to(repository):
        relative = destination.relative_to(repository)
        if not relative.parts or relative.parts[0].casefold() not in {".tmp", "dist"}:
            raise ValueError("unsafe_receipt_output")
    return destination


def verify_marketplace_filesystem_receipt(
    catalog: PreparationCatalog,
    marketplace: Path,
    receipt: Path,
) -> OperationResult:
    """Validate a receipt against current SHA-256-bound marketplace identities."""

    receipt_path = Path(receipt).resolve()
    try:
        raw = json.loads(receipt_path.read_text(encoding="ascii"))
        if not isinstance(raw, dict):
            raise ValueError("receipt_payload_invalid")
        _validate_shape(raw)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        code = str(exc) if str(exc).startswith("receipt_") else "receipt_payload_invalid"
        return _failure("marketplace_receipt_invalid", code)

    root = Path(marketplace).resolve()
    try:
        identity = marketplace_tree_identity(root)
        expected = _current_payload(catalog, root, identity)
        expected["receipt_sha256"] = _payload_digest(expected)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        code = str(exc) or "receipt_identity_unavailable"
        return _failure("marketplace_receipt_mismatch", code)
    if raw != expected:
        return _failure("marketplace_receipt_mismatch", "receipt_identity_mismatch")

    encoded = receipt_path.read_bytes()
    return OperationResult(
        operation="verify-marketplace-receipt",
        status="PASS",
        code="marketplace_receipt_verified",
        artifacts=(
            ArtifactRecord(
                receipt_path.name,
                "marketplace_filesystem_verification_receipt",
                sha256(encoded).hexdigest(),
                len(encoded),
            ),
        ),
        evidence={
            "marketplace_id": catalog.marketplace_id,
            "marketplace_sha256": expected["marketplace_identity"]["content_sha256"],
            "receipt_sha256": expected["receipt_sha256"],
        },
    )


def _current_payload(
    catalog: PreparationCatalog,
    root: Path,
    identity: Mapping[str, object],
) -> dict[str, object]:
    registry_path = root / ".obvious-one-validation.json"
    registry = _load_mapping(registry_path)
    records = registry.get("plugins")
    if registry.get("marketplace_id") != catalog.marketplace_id or not isinstance(records, list):
        raise ValueError("receipt_registry_invalid")
    by_id: dict[str, Mapping[str, object]] = {}
    for record in records:
        if not isinstance(record, Mapping) or not isinstance(record.get("plugin_id"), str):
            raise ValueError("receipt_registry_invalid")
        plugin_id = record["plugin_id"]
        if plugin_id in by_id:
            raise ValueError("receipt_duplicate_plugin")
        by_id[plugin_id] = record

    plugins = []
    expected_ids = {entry.application.plugin_id for entry in catalog.applications}
    if set(by_id) != expected_ids:
        raise ValueError("receipt_registry_invalid")
    for entry in sorted(catalog.applications, key=lambda item: item.application.plugin_id):
        plugin_id = entry.application.plugin_id
        record = by_id[plugin_id]
        if record.get("version") != entry.application.version:
            raise ValueError("receipt_registry_invalid")
        registry_targets = record.get("targets")
        if not isinstance(registry_targets, Mapping):
            raise ValueError("receipt_registry_invalid")
        targets = []
        for name, target in entry.applicable_targets():
            recorded = registry_targets.get(name)
            if not isinstance(recorded, Mapping):
                raise ValueError("receipt_registry_invalid")
            destination = _safe_relative(target.destination)
            artifact = recorded.get("artifact")
            if recorded.get("path") != destination or not isinstance(artifact, Mapping):
                raise ValueError("receipt_registry_invalid")
            content_sha256 = artifact.get("content_sha256")
            if not _is_digest(content_sha256):
                raise ValueError("receipt_registry_invalid")
            targets.append(
                {
                    "name": name,
                    "destination": destination,
                    "artifact_content_sha256": content_sha256,
                }
            )
        plugins.append(
            {
                "plugin_id": plugin_id,
                "version": entry.application.version,
                "targets": targets,
            }
        )

    controls = {}
    for name, relative in _CONTROL_PATHS.items():
        path = catalog.catalog_path if relative is None else root / relative
        controls[name] = _file_sha256(path)
    return {
        "schema": RECEIPT_SCHEMA,
        "marketplace_id": catalog.marketplace_id,
        "operation": "verify-marketplace",
        "status": "PASS",
        "marketplace_identity": {
            "content_sha256": identity["content_sha256"],
            "file_count": identity["file_count"],
            "total_bytes": identity["total_bytes"],
        },
        "controls": controls,
        "plugins": plugins,
        "verification_profile": {
            "portable_verifier_contract_version": 1,
            "receipt_schema_version": 1,
        },
    }


def _require_passing_verification(
    verification: OperationResult,
    root: Path,
    identity: Mapping[str, object],
) -> None:
    if (
        verification.operation != "verify-marketplace"
        or verification.status != "PASS"
        or verification.code != "marketplace_verified"
        or verification.evidence.get("gates", {}).get("filesystem") != "PASS"
    ):
        raise ValueError("receipt_verification_not_passed")
    artifacts = [item for item in verification.artifacts if item.kind == "marketplace_stage"]
    if len(artifacts) != 1:
        raise ValueError("receipt_verification_identity_mismatch")
    artifact = artifacts[0]
    if (
        artifact.path != root.name
        or artifact.sha256 != identity["content_sha256"]
        or artifact.size != identity["total_bytes"]
    ):
        raise ValueError("receipt_verification_identity_mismatch")


def _validate_shape(payload: Mapping[str, object]) -> None:
    if set(payload) != _TOP_LEVEL_KEYS:
        raise ValueError("receipt_schema_invalid")
    if (
        payload.get("schema") != RECEIPT_SCHEMA
        or payload.get("operation") != "verify-marketplace"
        or payload.get("status") != "PASS"
        or not isinstance(payload.get("marketplace_id"), str)
        or not payload["marketplace_id"]
    ):
        raise ValueError("receipt_schema_invalid")
    if payload.get("receipt_sha256") != _payload_digest(payload):
        raise ValueError("receipt_digest_invalid")

    identity = payload.get("marketplace_identity")
    if not isinstance(identity, Mapping) or set(identity) != {
        "content_sha256", "file_count", "total_bytes"
    }:
        raise ValueError("receipt_schema_invalid")
    if not _is_digest(identity.get("content_sha256")):
        raise ValueError("receipt_digest_invalid")
    for field in ("file_count", "total_bytes"):
        if not isinstance(identity.get(field), int) or isinstance(identity.get(field), bool) or identity[field] < 0:
            raise ValueError("receipt_schema_invalid")

    controls = payload.get("controls")
    if not isinstance(controls, Mapping) or set(controls) != _DIGEST_KEYS:
        raise ValueError("receipt_schema_invalid")
    if not all(_is_digest(value) for value in controls.values()):
        raise ValueError("receipt_digest_invalid")

    profile = payload.get("verification_profile")
    if profile != {
        "portable_verifier_contract_version": 1,
        "receipt_schema_version": 1,
    }:
        raise ValueError("receipt_schema_invalid")
    plugins = payload.get("plugins")
    if not isinstance(plugins, list):
        raise ValueError("receipt_schema_invalid")
    plugin_ids = []
    for plugin in plugins:
        if not isinstance(plugin, Mapping) or set(plugin) != {"plugin_id", "version", "targets"}:
            raise ValueError("receipt_schema_invalid")
        plugin_id = plugin.get("plugin_id")
        version = plugin.get("version")
        targets = plugin.get("targets")
        if not isinstance(plugin_id, str) or not plugin_id or not isinstance(version, str) or not version:
            raise ValueError("receipt_schema_invalid")
        if not isinstance(targets, list) or not targets:
            raise ValueError("receipt_schema_invalid")
        names = []
        for target in targets:
            if not isinstance(target, Mapping) or set(target) != {
                "name", "destination", "artifact_content_sha256"
            }:
                raise ValueError("receipt_schema_invalid")
            name = target.get("name")
            if name not in {"codex", "openclaw"}:
                raise ValueError("receipt_schema_invalid")
            _safe_relative(target.get("destination"))
            if not _is_digest(target.get("artifact_content_sha256")):
                raise ValueError("receipt_digest_invalid")
            names.append(name)
        if names != sorted(set(names)):
            raise ValueError("receipt_schema_invalid")
        plugin_ids.append(plugin_id)
    if plugin_ids != sorted(set(plugin_ids)):
        raise ValueError("receipt_duplicate_plugin")


def _failure(result_code: str, diagnostic_code: str) -> OperationResult:
    return OperationResult(
        operation="verify-marketplace-receipt",
        status="FAIL",
        code=result_code,
        diagnostics=(
            Diagnostic(
                code=diagnostic_code,
                path=None,
                message="marketplace receipt verification failed",
            ),
        ),
    )


def _load_mapping(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("receipt_registry_invalid")
    return value


def _file_sha256(path: Path) -> str:
    if not path.is_file() or _path_is_link(path):
        raise ValueError("receipt_control_missing")
    return sha256(path.read_bytes()).hexdigest()


def _safe_relative(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("receipt_path_invalid")
    normalized = value.replace("\\", "/")
    posix = PurePosixPath(normalized)
    windows = PureWindowsPath(value)
    if (
        posix.is_absolute()
        or windows.is_absolute()
        or bool(windows.drive)
        or any(part in {"", ".", ".."} for part in posix.parts)
    ):
        raise ValueError("receipt_path_invalid")
    return posix.as_posix()


def _payload_digest(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("receipt_sha256", None)
    return sha256(_canonical_bytes(unsigned)).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _document_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("ascii")


def _is_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _reject_links(root: Path) -> None:
    if _path_is_link(root):
        raise ValueError("receipt_link_forbidden")
    for directory, names, files in os.walk(root, followlinks=False):
        parent = Path(directory)
        for name in (*names, *files):
            if _path_is_link(parent / name):
                raise ValueError("receipt_link_forbidden")


def _path_is_link(path: Path) -> bool:
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except FileNotFoundError:
        return False
    return path.is_symlink() or bool(attributes & 0x400)
