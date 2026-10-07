"""Per-runtime realization contracts for application-facing operations."""

from __future__ import annotations

from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import Any, Mapping


RUNTIME_TARGETS = frozenset({"ChatGPT Work Local/Desktop", "Codex"})
MECHANISMS = frozenset({
    "MCP_REMOTE_HTTPS",
    "MCP_REGISTERED",
    "MCP_LOCAL_PROCESS",
    "DIRECT_LOCAL",
    "RUNTIME_NATIVE",
    "UNSUPPORTED",
})
TRANSPORTS = frozenset({"DIRECT_ARGV", "RUNTIME_API", "MCP_STREAMABLE_HTTP", "NONE"})
EXECUTION_LOCATIONS = frozenset({"BUILD_HOST", "USER_DEVICE", "RUNTIME_HOST", "REMOTE_SERVICE"})
SETUP_OWNERS = frozenset({"OWNER", "SERVICE_OPERATOR", "RUNTIME", "BUILDER"})
FEASIBILITY_STATES = frozenset({
    "FEASIBLE", "FEASIBLE_WITH_SETUP", "NOT VERIFIED", "UNSUPPORTED", "BLOCKED"
})
EVIDENCE_POLICIES = frozenset({"REQUIRED_BEFORE_W2", "DEFERRED_ALLOWED"})

_ID = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
_KEYS = {
    "target_runtime",
    "mechanism",
    "adapter_id",
    "adapter_version",
    "exposed_capability",
    "operation_id",
    "transport",
    "execution_location",
    "dependency_ids",
    "permission_ids",
    "setup_requirements",
    "setup_owner",
    "feasibility_state",
    "evidence_policy",
}
_MECHANISM_SHAPES = {
    "MCP_REMOTE_HTTPS": ("MCP_STREAMABLE_HTTP", "REMOTE_SERVICE"),
    "MCP_REGISTERED": ("MCP_STREAMABLE_HTTP", "RUNTIME_HOST"),
    "MCP_LOCAL_PROCESS": ("MCP_STREAMABLE_HTTP", "USER_DEVICE"),
    "DIRECT_LOCAL": ("DIRECT_ARGV", "USER_DEVICE"),
    "RUNTIME_NATIVE": ("RUNTIME_API", "RUNTIME_HOST"),
    "UNSUPPORTED": ("NONE", "RUNTIME_HOST"),
}


@dataclass(frozen=True)
class RuntimeRealizationContract:
    target_runtime: str
    payload: Mapping[str, Any]
    errors: tuple[str, ...]
    blockers: tuple[str, ...]


def _freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({str(key): _freeze(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(child) for child in value)
    return value


def _valid_string_list(value: object, *, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) and bool(item) for item in value)
        and len(value) == len(set(value))
    )


def validate_runtime_realization(
    payload: object,
    *,
    operation_id: str,
    runtime_targets: set[str] | frozenset[str],
    dependency_ids: set[str] | frozenset[str],
    permission_ids: set[str] | frozenset[str],
) -> RuntimeRealizationContract:
    """Validate one exact runtime path without inferring missing authority."""

    if not isinstance(payload, dict):
        return RuntimeRealizationContract("", MappingProxyType({}), ("realization.invalid_object",), ())
    target = payload.get("target_runtime") if isinstance(payload.get("target_runtime"), str) else ""
    prefix = f"realization.{target}" if target else "realization"
    errors: list[str] = []
    if set(payload) != _KEYS:
        errors.append(f"{prefix}.invalid_keys")
    if target not in RUNTIME_TARGETS or target not in runtime_targets:
        errors.append(f"{prefix}.target_runtime_invalid")

    mechanism = payload.get("mechanism")
    if mechanism not in MECHANISMS:
        errors.append(f"{prefix}.mechanism_invalid")
    for key in ("adapter_id", "exposed_capability"):
        value = payload.get(key)
        if not isinstance(value, str) or _ID.fullmatch(value) is None:
            errors.append(f"{prefix}.{key}_invalid")
    if not isinstance(payload.get("adapter_version"), str) or not payload.get("adapter_version"):
        errors.append(f"{prefix}.adapter_version_invalid")
    if payload.get("operation_id") != operation_id:
        errors.append(f"{prefix}.operation_mismatch")

    transport = payload.get("transport")
    location = payload.get("execution_location")
    if transport not in TRANSPORTS:
        errors.append(f"{prefix}.transport_invalid")
    if location not in EXECUTION_LOCATIONS:
        errors.append(f"{prefix}.execution_location_invalid")
    expected = _MECHANISM_SHAPES.get(str(mechanism))
    if expected is not None:
        if transport != expected[0]:
            errors.append(f"{prefix}.transport_mismatch")
        if location != expected[1]:
            errors.append(f"{prefix}.execution_location_mismatch")

    for key, declared, suffix in (
        ("dependency_ids", dependency_ids, "dependency_unknown"),
        ("permission_ids", permission_ids, "permission_unknown"),
    ):
        values = payload.get(key)
        if not _valid_string_list(values):
            errors.append(f"{prefix}.{key}_invalid")
        else:
            for value in values:
                if value not in declared:
                    errors.append(f"{prefix}.{suffix}:{value}")

    setup = payload.get("setup_requirements")
    if not _valid_string_list(setup):
        errors.append(f"{prefix}.setup_requirements_invalid")
    if payload.get("setup_owner") not in SETUP_OWNERS:
        errors.append(f"{prefix}.setup_owner_invalid")
    feasibility = payload.get("feasibility_state")
    if feasibility not in FEASIBILITY_STATES:
        errors.append(f"{prefix}.feasibility_state_invalid")
    elif feasibility == "FEASIBLE_WITH_SETUP" and setup == []:
        errors.append(f"{prefix}.setup_requirements_required")
    if mechanism == "UNSUPPORTED" and feasibility != "UNSUPPORTED":
        errors.append(f"{prefix}.unsupported_feasibility_required")
    if mechanism != "UNSUPPORTED" and feasibility == "UNSUPPORTED":
        errors.append(f"{prefix}.mechanism_feasibility_mismatch")
    if payload.get("evidence_policy") not in EVIDENCE_POLICIES:
        errors.append(f"{prefix}.evidence_policy_invalid")

    return RuntimeRealizationContract(
        target,
        _freeze(payload),  # type: ignore[arg-type]
        tuple(sorted(set(errors))),
        (),
    )
