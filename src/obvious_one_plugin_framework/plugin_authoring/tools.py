"""Portable application-facing tool contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import re
from typing import Any, Mapping


IMPLEMENTATION_KINDS = frozenset({
    "BUNDLED_LOCAL", "RUNTIME_NATIVE", "FRAMEWORK_ADAPTER", "MCP_ADAPTER", "UNRESOLVED"
})
RUNTIME_TARGETS = frozenset({"ChatGPT Work Local/Desktop", "Codex"})
PERMISSIONS = frozenset({"workspace:read", "workspace:write", "network", "runtime:native"})
_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_KEYS = {
    "schema", "id", "required", "implementation_kind", "requirement_ids", "skill_bindings",
    "files", "input_schema", "output_schema", "side_effects", "permissions", "runtime_targets",
    "dependencies", "configuration", "fallback", "verification", "redistribution", "execution",
    "fixtures", "runtime_capability", "adapter", "mcp",
}
_CREDENTIAL_KEYS = {"api_key", "apikey", "credential", "credentials", "password", "secret", "token"}


@dataclass(frozen=True)
class ApplicationToolContract:
    id: str
    implementation_kind: str
    required: bool
    payload: Mapping[str, Any]
    errors: tuple[str, ...]
    blockers: tuple[str, ...]


def _safe_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        return False
    parts = value.split("/")
    return not any(part in {"", ".", ".."} for part in parts) and ":" not in parts[0] and PurePosixPath(value).as_posix() == value


def _contains_credentials(value: object) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).casefold() in _CREDENTIAL_KEYS:
                return True
            if _contains_credentials(child):
                return True
    elif isinstance(value, list):
        return any(_contains_credentials(item) for item in value)
    return False


def _shell_forbidden(argv: object) -> bool:
    if not isinstance(argv, list) or any(not isinstance(item, str) or not item for item in argv):
        return False
    return any(any(token in item for token in ("&&", "||", ";", "|", "`", "$(", "\n", "\r")) for item in argv)


def _argv_invalid(argv: object, *, allow_empty: bool = False) -> bool:
    if not isinstance(argv, list) or (not argv and not allow_empty) or any(not isinstance(item, str) or not item for item in argv):
        return True
    for item in argv:
        if item.startswith("{") and item.endswith("}") and item != "{python}":
            return True
        if "://" in item or item.startswith("-") or item == "{python}":
            continue
        if "\\" in item or item.startswith("/") or re.match(r"^[A-Za-z]:", item):
            return True
        if "/" in item and not _safe_path(item):
            return True
    return False


def validate_application_tool_contract(payload: object) -> ApplicationToolContract:
    errors: list[str] = []
    blockers: list[str] = []
    if not isinstance(payload, dict):
        return ApplicationToolContract("", "", False, {}, ("tool.invalid_object",), ())
    identifier = payload.get("id") if isinstance(payload.get("id"), str) else ""
    prefix = f"tool.{identifier}" if identifier else "tool"
    kind = payload.get("implementation_kind") if isinstance(payload.get("implementation_kind"), str) else ""
    required = payload.get("required") is True
    if set(payload) != _KEYS:
        errors.append(f"{prefix}.invalid_keys")
    if payload.get("schema") != "plugin-builder-application-tool-v1":
        errors.append(f"{prefix}.schema_unsupported")
    if not identifier or _ID.fullmatch(identifier) is None:
        errors.append("tool.id_invalid")
    if type(payload.get("required")) is not bool:
        errors.append(f"{prefix}.required_invalid")
    if kind not in IMPLEMENTATION_KINDS:
        errors.append(f"{prefix}.implementation_kind_unsupported")
    if kind == "UNRESOLVED" and required:
        blockers.append(f"{prefix}.unresolved_required")
    for key in ("requirement_ids", "skill_bindings"):
        value = payload.get(key)
        if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
            suffix = "requirement_binding_required" if key == "requirement_ids" else "skill_binding_required"
            target = blockers if key == "skill_bindings" else errors
            target.append(f"{prefix}.{suffix}")
    files = payload.get("files")
    if not isinstance(files, list) or any(not _safe_path(item) for item in files):
        errors.append(f"{prefix}.files_invalid")
    for key in ("input_schema", "output_schema"):
        value = payload.get(key)
        if not isinstance(value, dict) or value.get("type") != "object":
            errors.append(f"{prefix}.{key}_invalid")
    for key in ("side_effects", "dependencies"):
        if not isinstance(payload.get(key), list):
            errors.append(f"{prefix}.{key}_invalid")
    permissions = payload.get("permissions")
    if not isinstance(permissions, list) or any(item not in PERMISSIONS for item in permissions):
        errors.append(f"{prefix}.permissions_invalid")
    runtimes = payload.get("runtime_targets")
    if not isinstance(runtimes, list) or not runtimes or any(item not in RUNTIME_TARGETS for item in runtimes):
        errors.append(f"{prefix}.runtime_targets_invalid")
    elif required and set(runtimes) != RUNTIME_TARGETS:
        blockers.append(f"{prefix}.required_runtime_unsupported")
    configuration = payload.get("configuration")
    if not isinstance(configuration, dict) or set(configuration) != {"authentication", "setup"}:
        errors.append(f"{prefix}.configuration_invalid")
    fallback = payload.get("fallback")
    if not isinstance(fallback, dict) or set(fallback) != {"policy", "description"} or fallback.get("policy") not in {"BLOCK", "OPTIONAL"}:
        errors.append(f"{prefix}.fallback_invalid")
    redistribution = payload.get("redistribution")
    if not isinstance(redistribution, dict) or set(redistribution) != {"state", "evidence"}:
        errors.append(f"{prefix}.redistribution_invalid")
    if _contains_credentials(payload):
        errors.append(f"{prefix}.credential_material_forbidden")

    verification = payload.get("verification")
    if not isinstance(verification, dict) or set(verification) != {"kind", "argv", "network"}:
        errors.append(f"{prefix}.verification_invalid")
    else:
        if _argv_invalid(
            verification.get("argv"),
            allow_empty=kind not in {"BUNDLED_LOCAL", "FRAMEWORK_ADAPTER"},
        ):
            errors.append(f"{prefix}.verification_argv_invalid")
        if _shell_forbidden(verification.get("argv")):
            errors.append(f"{prefix}.verification_shell_forbidden")

    execution = payload.get("execution")
    if kind in {"BUNDLED_LOCAL", "FRAMEWORK_ADAPTER"}:
        if not files:
            errors.append(f"{prefix}.files_required")
        if not isinstance(execution, dict) or set(execution) != {"argv", "clean_environment", "timeout_seconds"}:
            errors.append(f"{prefix}.execution_invalid")
        else:
            if _argv_invalid(execution.get("argv")):
                errors.append(f"{prefix}.execution_argv_invalid")
            elif _shell_forbidden(execution["argv"]):
                errors.append(f"{prefix}.execution_shell_forbidden")
            if execution.get("clean_environment") is not True:
                errors.append(f"{prefix}.clean_environment_required")
            timeout = execution.get("timeout_seconds")
            if type(timeout) is not int or timeout <= 0 or timeout > 300:
                errors.append(f"{prefix}.timeout_invalid")
        fixtures = payload.get("fixtures")
        if not isinstance(fixtures, dict) or set(fixtures) != {"input", "output"}:
            errors.append(f"{prefix}.fixtures_invalid")
    if kind == "FRAMEWORK_ADAPTER":
        adapter = payload.get("adapter")
        if not isinstance(adapter, dict) or set(adapter) != {"source", "portable_files", "provenance"}:
            errors.append(f"{prefix}.adapter_invalid")
        else:
            provenance = adapter.get("provenance")
            if not isinstance(provenance, dict) or set(provenance) != {"version", "sha256"} or _SHA256.fullmatch(str(provenance.get("sha256", ""))) is None:
                errors.append(f"{prefix}.adapter_provenance_invalid")
            if not isinstance(adapter.get("portable_files"), list) or any(not _safe_path(item) for item in adapter["portable_files"]):
                errors.append(f"{prefix}.adapter_files_invalid")
    if kind == "RUNTIME_NATIVE":
        capability = payload.get("runtime_capability")
        if not isinstance(capability, dict) or set(capability) != {"name", "runtimes"} or not capability.get("name"):
            errors.append(f"{prefix}.runtime_capability_required")
        elif set(capability.get("runtimes", [])) != set(runtimes or []):
            errors.append(f"{prefix}.runtime_capability_mismatch")
    if kind == "MCP_ADAPTER":
        mcp = payload.get("mcp")
        expected = {"server_id", "config_file", "transport", "permission_scopes", "authentication", "setup", "service_boundary"}
        if not isinstance(mcp, dict) or set(mcp) != expected or not _safe_path(mcp.get("config_file")):
            errors.append(f"{prefix}.mcp_contract_invalid")
        if not isinstance(permissions, list) or "network" not in permissions:
            errors.append(f"{prefix}.network_permission_required")
        if isinstance(mcp, dict) and mcp.get("authentication") not in {"NOT_REQUIRED", "USER_CONFIGURED"}:
            blockers.append(f"{prefix}.authentication_decision_required")
    return ApplicationToolContract(
        identifier,
        kind,
        required,
        dict(payload),
        tuple(sorted(set(errors))),
        tuple(sorted(set(blockers))),
    )
