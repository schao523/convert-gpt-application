"""Plan-time application-tool contract validation."""

from __future__ import annotations

from pathlib import PurePosixPath
import re
from typing import Any


TOOL_KINDS = frozenset({
    "BUNDLED_LOCAL", "RUNTIME_NATIVE", "FRAMEWORK_ADAPTER", "MCP_ADAPTER", "UNRESOLVED"
})
RUNTIME_TARGETS = frozenset({"ChatGPT Work Local/Desktop", "Codex"})
PERMISSIONS = frozenset({"workspace:read", "workspace:write", "network", "runtime:native"})
_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_KEYS = {
    "schema", "id", "required", "implementation_kind", "requirement_ids",
    "skill_bindings", "files", "input_schema", "output_schema", "side_effects",
    "permissions", "runtime_targets", "dependencies", "configuration", "fallback",
    "verification", "redistribution",
}


def _safe_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        return False
    parts = value.split("/")
    return not any(part in {"", ".", ".."} for part in parts) and ":" not in parts[0] and PurePosixPath(value).as_posix() == value


def validate_tool_contract(
    payload: object,
    *,
    requirement_ids: set[str],
    skill_names: set[str],
    recipe_paths: set[str],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    blockers: list[str] = []
    if not isinstance(payload, dict):
        return ["tool.invalid_object"], blockers
    identifier = payload.get("id")
    prefix = f"tool.{identifier}" if isinstance(identifier, str) and identifier else "tool"
    if set(payload) != _KEYS:
        errors.append(f"{prefix}.invalid_keys")
    if payload.get("schema") != "plugin-builder-application-tool-v1":
        errors.append(f"{prefix}.schema_unsupported")
    if not isinstance(identifier, str) or _ID.fullmatch(identifier) is None:
        errors.append("tool.id_invalid")
    required = payload.get("required")
    if type(required) is not bool:
        errors.append(f"{prefix}.required_invalid")
    kind = payload.get("implementation_kind")
    if kind not in TOOL_KINDS:
        errors.append(f"{prefix}.implementation_kind_unsupported")
    elif kind == "UNRESOLVED" and required is True:
        blockers.append(f"{prefix}.unresolved_required")

    owned = payload.get("requirement_ids")
    if not isinstance(owned, list) or not owned or any(not isinstance(item, str) for item in owned):
        errors.append(f"{prefix}.requirement_binding_required")
    else:
        for item in owned:
            if item not in requirement_ids:
                errors.append(f"{prefix}.unknown_requirement:{item}")
    bindings = payload.get("skill_bindings")
    if not isinstance(bindings, list) or not bindings:
        blockers.append(f"{prefix}.skill_binding_required")
    elif any(item not in skill_names for item in bindings):
        errors.append(f"{prefix}.skill_binding_unknown")
    files = payload.get("files")
    if not isinstance(files, list) or any(not _safe_path(item) for item in files):
        errors.append(f"{prefix}.files_invalid")
    elif any(item not in recipe_paths for item in files):
        errors.append(f"{prefix}.file_recipe_missing")
    if kind in {"BUNDLED_LOCAL", "FRAMEWORK_ADAPTER", "MCP_ADAPTER"} and not files:
        blockers.append(f"{prefix}.implementation_file_required")
    for key in ("input_schema", "output_schema"):
        schema = payload.get(key)
        if not isinstance(schema, dict) or schema.get("type") != "object":
            errors.append(f"{prefix}.{key}_invalid")
    for key in ("side_effects", "dependencies"):
        value = payload.get(key)
        if not isinstance(value, list):
            errors.append(f"{prefix}.{key}_invalid")
    permissions = payload.get("permissions")
    if not isinstance(permissions, list) or any(item not in PERMISSIONS for item in permissions):
        errors.append(f"{prefix}.permissions_invalid")
    runtimes = payload.get("runtime_targets")
    if not isinstance(runtimes, list) or not runtimes or any(item not in RUNTIME_TARGETS for item in runtimes):
        errors.append(f"{prefix}.runtime_targets_invalid")
    elif required is True and set(runtimes) != RUNTIME_TARGETS:
        blockers.append(f"{prefix}.required_runtime_unsupported")
    configuration = payload.get("configuration")
    if not isinstance(configuration, dict) or set(configuration) != {"authentication", "setup"}:
        errors.append(f"{prefix}.configuration_invalid")
    elif kind == "MCP_ADAPTER" and configuration.get("authentication") not in {"NOT_REQUIRED", "USER_CONFIGURED"}:
        blockers.append(f"{prefix}.authentication_decision_required")
    fallback = payload.get("fallback")
    if not isinstance(fallback, dict) or set(fallback) != {"policy", "description"} or fallback.get("policy") not in {"BLOCK", "OPTIONAL"}:
        errors.append(f"{prefix}.fallback_invalid")
    verification = payload.get("verification")
    if not isinstance(verification, dict) or set(verification) != {"kind", "argv", "network"}:
        errors.append(f"{prefix}.verification_invalid")
    else:
        argv = verification.get("argv")
        if verification.get("kind") not in {"PYTHON_ARGV", "RUNTIME_CAPABILITY", "MCP_CONTRACT"}:
            errors.append(f"{prefix}.verification_kind_unsupported")
        if not isinstance(argv, list) or any(not isinstance(item, str) or not item for item in argv):
            errors.append(f"{prefix}.verification_argv_invalid")
        elif any(any(symbol in item for symbol in (";", "&&", "||", "|", "`", "$(`")) for item in argv):
            errors.append(f"{prefix}.verification_shell_forbidden")
        if type(verification.get("network")) is not bool:
            errors.append(f"{prefix}.verification_network_invalid")
    redistribution = payload.get("redistribution")
    if not isinstance(redistribution, dict) or set(redistribution) != {"state", "evidence"}:
        errors.append(f"{prefix}.redistribution_invalid")
    elif kind in {"BUNDLED_LOCAL", "FRAMEWORK_ADAPTER", "MCP_ADAPTER"} and redistribution.get("state") != "APPROVED":
        blockers.append(f"{prefix}.redistribution_unapproved")
    return sorted(set(errors)), sorted(set(blockers))
