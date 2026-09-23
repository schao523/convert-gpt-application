"""Stable, path-safe machine-readable operation results."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Literal, Mapping, TypeAlias, cast


ResultStatus: TypeAlias = Literal["PASS", "BLOCKED", "FAIL"]
_RESULT_STATUSES = frozenset({"PASS", "BLOCKED", "FAIL"})
_RESULT_KEYS = frozenset(
    {
        "result_schema_version",
        "operation",
        "status",
        "code",
        "diagnostics",
        "artifacts",
        "mutations",
        "evidence",
    }
)


@dataclass(frozen=True)
class Diagnostic:
    code: str
    path: str | None
    message: str
    candidates: tuple[str, ...] = ()


@dataclass(frozen=True)
class ArtifactRecord:
    path: str
    kind: str
    sha256: str
    size: int


@dataclass(frozen=True)
class MutationRecord:
    path: str
    action: str


@dataclass(frozen=True)
class OperationResult:
    operation: str
    status: ResultStatus
    code: str
    diagnostics: tuple[Diagnostic, ...] = ()
    artifacts: tuple[ArtifactRecord, ...] = ()
    mutations: tuple[MutationRecord, ...] = ()
    evidence: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in _RESULT_STATUSES:
            raise ValueError("invalid_result_status")


def result_payload(result: OperationResult) -> dict[str, object]:
    """Return the canonical JSON-compatible payload for an operation result."""

    payload: dict[str, object] = {
        "result_schema_version": 1,
        **asdict(result),
    }
    _reject_private_absolute_paths(payload)
    return payload


def operation_result_from_payload(payload: Mapping[str, object]) -> OperationResult:
    """Parse and validate a versioned operation-result payload."""

    unknown = set(payload) - _RESULT_KEYS
    if unknown:
        raise ValueError(f"unknown_result_key:{sorted(unknown)[0]}")
    if payload.get("result_schema_version") != 1:
        raise ValueError("unsupported_result_schema_version")

    required = {"operation", "status", "code"}
    missing = required - set(payload)
    if missing:
        raise ValueError(f"missing_result_key:{sorted(missing)[0]}")

    result = OperationResult(
        operation=_required_string(payload["operation"], "operation"),
        status=cast(ResultStatus, _required_string(payload["status"], "status")),
        code=_required_string(payload["code"], "code"),
        diagnostics=tuple(
            _diagnostic_from_payload(item)
            for item in _required_sequence(payload.get("diagnostics", []), "diagnostics")
        ),
        artifacts=tuple(
            _artifact_from_payload(item)
            for item in _required_sequence(payload.get("artifacts", []), "artifacts")
        ),
        mutations=tuple(
            _mutation_from_payload(item)
            for item in _required_sequence(payload.get("mutations", []), "mutations")
        ),
        evidence=_required_mapping(payload.get("evidence", {}), "evidence"),
    )
    _reject_private_absolute_paths(result_payload(result))
    return result


def result_json(result: OperationResult) -> str:
    """Serialize an operation result as stable, newline-terminated JSON."""

    return json.dumps(
        result_payload(result),
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    ) + "\n"


def load_result(path: Path) -> OperationResult:
    """Load an operation result from UTF-8 JSON."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("invalid_result_payload")
    return operation_result_from_payload(raw)


def _diagnostic_from_payload(value: object) -> Diagnostic:
    payload = _record_payload(value, "diagnostic", {"code", "path", "message", "candidates"})
    path = payload.get("path")
    if path is not None and not isinstance(path, str):
        raise ValueError("invalid_diagnostic_path")
    return Diagnostic(
        code=_required_string(payload.get("code"), "diagnostic_code"),
        path=path,
        message=_required_string(payload.get("message"), "diagnostic_message"),
        candidates=tuple(
            _required_string(item, "diagnostic_candidate")
            for item in _required_sequence(payload.get("candidates", []), "diagnostic_candidates")
        ),
    )


def _artifact_from_payload(value: object) -> ArtifactRecord:
    payload = _record_payload(value, "artifact", {"path", "kind", "sha256", "size"})
    size = payload.get("size")
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise ValueError("invalid_artifact_size")
    return ArtifactRecord(
        path=_required_string(payload.get("path"), "artifact_path"),
        kind=_required_string(payload.get("kind"), "artifact_kind"),
        sha256=_required_string(payload.get("sha256"), "artifact_sha256"),
        size=size,
    )


def _mutation_from_payload(value: object) -> MutationRecord:
    payload = _record_payload(value, "mutation", {"path", "action"})
    return MutationRecord(
        path=_required_string(payload.get("path"), "mutation_path"),
        action=_required_string(payload.get("action"), "mutation_action"),
    )


def _record_payload(value: object, kind: str, allowed: set[str]) -> Mapping[str, object]:
    payload = _required_mapping(value, kind)
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError(f"unknown_{kind}_key:{sorted(unknown)[0]}")
    return payload


def _required_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"invalid_{name}")
    if not all(isinstance(key, str) for key in value):
        raise ValueError(f"invalid_{name}_key")
    return value


def _required_sequence(value: object, name: str) -> list[object] | tuple[object, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"invalid_{name}")
    return value


def _required_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"invalid_{name}")
    return value


def _reject_private_absolute_paths(value: object) -> None:
    if isinstance(value, str):
        if PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
            raise ValueError("private_absolute_path")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_private_absolute_paths(key)
            _reject_private_absolute_paths(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_private_absolute_paths(item)
