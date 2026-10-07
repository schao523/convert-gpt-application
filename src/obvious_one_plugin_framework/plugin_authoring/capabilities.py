"""Capability-register contracts for Plugin Builder planning."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
import re
from typing import Any, Mapping


RUNTIME_TARGETS = frozenset({"ChatGPT Work Local/Desktop", "Codex"})
REALIZATION_NEEDS = frozenset({"SKILL_ONLY", "TOOL_REQUIRED"})
EVIDENCE_TARGETS = frozenset({"STRUCTURE", "OPERATION", "INSTALLED_REALIZATION", "BEHAVIOR"})
_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_KEYS = {
    "schema",
    "id",
    "requirement_ids",
    "skill_bindings",
    "realization_need",
    "tool_id",
    "runtime_targets",
    "evidence_targets",
}


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(child) for child in value)
    return value


def _string_list(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and bool(item) for item in value)
        and len(value) == len(set(value))
    )


@dataclass(frozen=True)
class CapabilityContract:
    id: str
    payload: Mapping[str, Any]
    errors: tuple[str, ...]
    blockers: tuple[str, ...]


def validate_capability_contract(payload: object) -> CapabilityContract:
    if not isinstance(payload, dict):
        return CapabilityContract("", MappingProxyType({}), ("capability.invalid_object",), ())

    identifier = payload.get("id") if isinstance(payload.get("id"), str) else ""
    prefix = f"capability.{identifier}" if identifier else "capability"
    errors: list[str] = []

    if set(payload) != _KEYS:
        errors.append(f"{prefix}.invalid_keys")
    if payload.get("schema") != "plugin-builder-capability-v1":
        errors.append(f"{prefix}.schema_unsupported")
    if not identifier or _ID.fullmatch(identifier) is None:
        errors.append(f"{prefix}.id_invalid")

    requirements = payload.get("requirement_ids")
    if not _string_list(requirements):
        errors.append(f"{prefix}.requirement_binding_required")
    skills = payload.get("skill_bindings")
    if not _string_list(skills):
        errors.append(f"{prefix}.skill_binding_required")

    need = payload.get("realization_need")
    if need not in REALIZATION_NEEDS:
        errors.append(f"{prefix}.realization_need_unsupported")
    tool_id = payload.get("tool_id")
    if need == "TOOL_REQUIRED" and (not isinstance(tool_id, str) or _ID.fullmatch(tool_id) is None):
        errors.append(f"{prefix}.tool_id_required")
    if need == "SKILL_ONLY" and tool_id is not None:
        errors.append(f"{prefix}.tool_id_forbidden")

    runtimes = payload.get("runtime_targets")
    if not _string_list(runtimes) or any(item not in RUNTIME_TARGETS for item in runtimes):
        errors.append(f"{prefix}.runtime_targets_invalid")
    elif set(runtimes) != RUNTIME_TARGETS:
        errors.append(f"{prefix}.runtime_targets_incomplete")

    evidence = payload.get("evidence_targets")
    if not _string_list(evidence) or any(item not in EVIDENCE_TARGETS for item in evidence):
        errors.append(f"{prefix}.evidence_targets_invalid")

    return CapabilityContract(
        identifier,
        _freeze(payload),
        tuple(sorted(set(errors))),
        (),
    )


def validate_capability_register(
    payloads: object,
    *,
    requirement_ids: set[str],
    skill_names: set[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not isinstance(payloads, list):
        return ("capabilities.invalid",), ()

    errors: list[str] = []
    blockers: list[str] = []
    seen: set[str] = set()
    for payload in payloads:
        contract = validate_capability_contract(payload)
        errors.extend(contract.errors)
        blockers.extend(contract.blockers)
        identifier = contract.id
        prefix = f"capability.{identifier}" if identifier else "capability"
        if identifier in seen:
            errors.append(f"{prefix}.duplicate_id")
        elif identifier:
            seen.add(identifier)
        if isinstance(payload, dict):
            for requirement in payload.get("requirement_ids", []):
                if isinstance(requirement, str) and requirement not in requirement_ids:
                    errors.append(f"{prefix}.unknown_requirement:{requirement}")
            for skill in payload.get("skill_bindings", []):
                if isinstance(skill, str) and skill not in skill_names:
                    errors.append(f"{prefix}.skill_binding_unknown:{skill}")
    return tuple(sorted(set(errors))), tuple(sorted(set(blockers)))
