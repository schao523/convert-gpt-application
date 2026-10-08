"""Portable application-facing tool contracts."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import PurePosixPath
import re
from typing import Any, Mapping
from urllib.parse import urlsplit

from .runtime_realization import validate_runtime_realization


IMPLEMENTATION_KINDS = frozenset({
    "BUNDLED_LOCAL", "RUNTIME_NATIVE", "FRAMEWORK_ADAPTER", "MCP_ADAPTER", "UNRESOLVED"
})
RUNTIME_TARGETS = frozenset({"ChatGPT Work Local/Desktop", "Codex"})
PERMISSIONS = frozenset({"workspace:read", "workspace:write", "network", "runtime:native"})
_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_PERMISSION_ID = re.compile(r"^[a-z0-9]+(?:(?:-|:)[a-z0-9]+)*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_V1_KEYS = {
    "schema", "id", "required", "implementation_kind", "requirement_ids", "skill_bindings",
    "files", "input_schema", "output_schema", "side_effects", "permissions", "runtime_targets",
    "dependencies", "configuration", "fallback", "verification", "redistribution", "execution",
    "fixtures", "runtime_capability", "adapter", "mcp",
}
_V2_KEYS = _V1_KEYS | {"capability_ids", "operation", "realizations"}
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


def _argv_invalid(argv: object, *, allow_empty: bool = False, allow_port: bool = False) -> bool:
    if not isinstance(argv, list) or (not argv and not allow_empty) or any(not isinstance(item, str) or not item for item in argv):
        return True
    for item in argv:
        if item.startswith("{") and item.endswith("}") and item != "{python}" and not (allow_port and item == "{port}"):
            return True
        if "://" in item or item.startswith("-") or item == "{python}":
            continue
        if "\\" in item or item.startswith("/") or re.match(r"^[A-Za-z]:", item):
            return True
        if "/" in item and not _safe_path(item):
            return True
    return False


def _validate_v1_application_tool_contract(payload: object) -> ApplicationToolContract:
    errors: list[str] = []
    blockers: list[str] = []
    if not isinstance(payload, dict):
        return ApplicationToolContract("", "", False, {}, ("tool.invalid_object",), ())
    identifier = payload.get("id") if isinstance(payload.get("id"), str) else ""
    prefix = f"tool.{identifier}" if identifier else "tool"
    kind = payload.get("implementation_kind") if isinstance(payload.get("implementation_kind"), str) else ""
    required = payload.get("required") is True
    if set(payload) != _V1_KEYS:
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


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    encoded = (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")
    return sha256(encoded).hexdigest()


def _valid_unique_strings(value: object, *, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) and bool(item) for item in value)
        and len(value) == len(set(value))
    )


def _validate_v2_application_tool_contract(payload: dict[str, Any]) -> ApplicationToolContract:
    errors: list[str] = []
    blockers: list[str] = []
    identifier = payload.get("id") if isinstance(payload.get("id"), str) else ""
    prefix = f"tool.{identifier}" if identifier else "tool"
    kind = payload.get("implementation_kind") if isinstance(payload.get("implementation_kind"), str) else ""
    required = payload.get("required") is True

    if set(payload) != _V2_KEYS:
        errors.append(f"{prefix}.invalid_keys")
    if not identifier or _ID.fullmatch(identifier) is None:
        errors.append("tool.id_invalid")
    if type(payload.get("required")) is not bool:
        errors.append(f"{prefix}.required_invalid")
    if kind not in IMPLEMENTATION_KINDS:
        errors.append(f"{prefix}.implementation_kind_unsupported")
    if kind == "UNRESOLVED" and required:
        blockers.append(f"{prefix}.unresolved_required")

    for key in ("requirement_ids", "skill_bindings", "capability_ids"):
        value = payload.get(key)
        if not _valid_unique_strings(value, allow_empty=False):
            suffix = {
                "requirement_ids": "requirement_binding_required",
                "skill_bindings": "skill_binding_required",
                "capability_ids": "capability_binding_required",
            }[key]
            (blockers if key == "skill_bindings" else errors).append(f"{prefix}.{suffix}")

    files = payload.get("files")
    if not isinstance(files, list) or any(not _safe_path(item) for item in files):
        errors.append(f"{prefix}.files_invalid")
    for key in ("input_schema", "output_schema"):
        value = payload.get(key)
        if not isinstance(value, dict) or value.get("type") != "object":
            errors.append(f"{prefix}.{key}_invalid")
    if not isinstance(payload.get("side_effects"), list):
        errors.append(f"{prefix}.side_effects_invalid")

    runtimes = payload.get("runtime_targets")
    if not _valid_unique_strings(runtimes, allow_empty=False) or any(
        item not in RUNTIME_TARGETS for item in runtimes or []
    ):
        errors.append(f"{prefix}.runtime_targets_invalid")
        declared_runtimes: set[str] = set()
    else:
        declared_runtimes = set(runtimes)
        if required and declared_runtimes != RUNTIME_TARGETS:
            blockers.append(f"{prefix}.required_runtime_unsupported")

    operation = payload.get("operation")
    operation_keys = {
        "id", "protocol", "input_schema_sha256", "output_schema_sha256",
        "side_effect_class", "idempotent", "capability_ids",
    }
    if not isinstance(operation, dict) or set(operation) != operation_keys:
        errors.append(f"{prefix}.operation_invalid")
    else:
        if operation.get("id") != identifier:
            errors.append(f"{prefix}.operation_id_mismatch")
        if operation.get("protocol") not in {"JSON_STDIN_STDOUT", "MCP_TOOL_CALL", "RUNTIME_API"}:
            errors.append(f"{prefix}.operation_protocol_invalid")
        if operation.get("side_effect_class") not in {"NONE", "READ_ONLY", "WORKSPACE_WRITE", "EXTERNAL_WRITE"}:
            errors.append(f"{prefix}.operation_side_effect_class_invalid")
        if type(operation.get("idempotent")) is not bool:
            errors.append(f"{prefix}.operation_idempotent_invalid")
        if operation.get("capability_ids") != payload.get("capability_ids"):
            errors.append(f"{prefix}.operation_capability_mismatch")
        if isinstance(payload.get("input_schema"), dict) and operation.get("input_schema_sha256") != _canonical_sha256(payload["input_schema"]):
            errors.append(f"{prefix}.operation_input_schema_mismatch")
        if isinstance(payload.get("output_schema"), dict) and operation.get("output_schema_sha256") != _canonical_sha256(payload["output_schema"]):
            errors.append(f"{prefix}.operation_output_schema_mismatch")

    dependencies = payload.get("dependencies")
    dependency_ids: set[str] = set()
    dependency_keys = {
        "id", "type", "provider", "version", "sha256", "runtime_targets",
        "setup_owner", "required", "absence_policy",
    }
    if not isinstance(dependencies, list):
        errors.append(f"{prefix}.dependencies_invalid")
    else:
        for item in dependencies:
            if not isinstance(item, dict) or set(item) != dependency_keys:
                errors.append(f"{prefix}.dependency_invalid")
                continue
            dependency_id = item.get("id")
            if not isinstance(dependency_id, str) or _ID.fullmatch(dependency_id) is None:
                errors.append(f"{prefix}.dependency_id_invalid")
                continue
            if dependency_id in dependency_ids:
                errors.append(f"{prefix}.dependency_duplicate:{dependency_id}")
            dependency_ids.add(dependency_id)
            if item.get("type") not in {"EXECUTABLE", "PYTHON_PACKAGE", "NODE_PACKAGE", "RUNTIME_CAPABILITY", "SERVICE"}:
                errors.append(f"{prefix}.dependency_type_invalid:{dependency_id}")
            if item.get("provider") not in {"BUNDLED", "RUNTIME_PROVIDED", "OWNER_CONFIGURED", "REMOTE_SERVICE"}:
                errors.append(f"{prefix}.dependency_provider_invalid:{dependency_id}")
            if item.get("version") is not None and not isinstance(item.get("version"), str):
                errors.append(f"{prefix}.dependency_version_invalid:{dependency_id}")
            digest = item.get("sha256")
            if digest is not None and (not isinstance(digest, str) or _SHA256.fullmatch(digest) is None):
                errors.append(f"{prefix}.dependency_sha256_invalid:{dependency_id}")
            if item.get("provider") == "BUNDLED" and not isinstance(digest, str):
                errors.append(f"{prefix}.dependency_sha256_required:{dependency_id}")
            targets = item.get("runtime_targets")
            if not _valid_unique_strings(targets, allow_empty=False) or any(target not in RUNTIME_TARGETS for target in targets or []):
                errors.append(f"{prefix}.dependency_runtime_targets_invalid:{dependency_id}")
            if item.get("setup_owner") not in {"BUILDER", "OWNER", "SERVICE_OPERATOR", "RUNTIME"}:
                errors.append(f"{prefix}.dependency_setup_owner_invalid:{dependency_id}")
            if type(item.get("required")) is not bool:
                errors.append(f"{prefix}.dependency_required_invalid:{dependency_id}")
            if item.get("absence_policy") not in {"BLOCK", "FALLBACK"}:
                errors.append(f"{prefix}.dependency_absence_policy_invalid:{dependency_id}")

    permissions = payload.get("permissions")
    permission_ids_by_runtime: dict[str, set[str]] = {runtime: set() for runtime in RUNTIME_TARGETS}
    permission_keys = {"id", "target_runtime", "grant_source", "required", "purpose", "verification"}
    seen_permissions: set[tuple[str, str]] = set()
    if not isinstance(permissions, list):
        errors.append(f"{prefix}.permissions_invalid")
    else:
        for item in permissions:
            if not isinstance(item, dict) or set(item) != permission_keys:
                errors.append(f"{prefix}.permission_invalid")
                continue
            permission_id = item.get("id")
            target = item.get("target_runtime")
            if not isinstance(permission_id, str) or _PERMISSION_ID.fullmatch(permission_id) is None:
                errors.append(f"{prefix}.permission_id_invalid")
                continue
            if target not in RUNTIME_TARGETS:
                errors.append(f"{prefix}.permission_runtime_invalid:{permission_id}")
            else:
                identity = (target, permission_id)
                if identity in seen_permissions:
                    errors.append(f"{prefix}.permission_duplicate:{target}:{permission_id}")
                seen_permissions.add(identity)
                permission_ids_by_runtime[target].add(permission_id)
            if item.get("grant_source") not in {"RUNTIME", "OWNER", "SERVICE"}:
                errors.append(f"{prefix}.permission_grant_source_invalid:{permission_id}")
            if type(item.get("required")) is not bool:
                errors.append(f"{prefix}.permission_required_invalid:{permission_id}")
            for key in ("purpose", "verification"):
                if not isinstance(item.get(key), str) or not item.get(key):
                    errors.append(f"{prefix}.permission_{key}_invalid:{permission_id}")

    configuration = payload.get("configuration")
    if not isinstance(configuration, dict) or set(configuration) != {"authentication", "setup"}:
        errors.append(f"{prefix}.configuration_invalid")

    fallback = payload.get("fallback")
    fallback_keys = {
        "policy", "trigger_conditions", "alternative_operation_id",
        "preserved_requirement_ids", "degraded_requirement_ids",
    }
    if not isinstance(fallback, dict) or set(fallback) != fallback_keys:
        errors.append(f"{prefix}.fallback_invalid")
    else:
        policy = fallback.get("policy")
        if policy not in {"BLOCK", "ALTERNATIVE", "OMIT_OPTIONAL"}:
            errors.append(f"{prefix}.fallback_policy_invalid")
        if not _valid_unique_strings(fallback.get("trigger_conditions"), allow_empty=False):
            errors.append(f"{prefix}.fallback_trigger_conditions_invalid")
        alternative = fallback.get("alternative_operation_id")
        if policy == "ALTERNATIVE":
            if not isinstance(alternative, str) or _ID.fullmatch(alternative) is None:
                errors.append(f"{prefix}.fallback_alternative_required")
        elif alternative is not None:
            errors.append(f"{prefix}.fallback_alternative_forbidden")
        requirement_ids = set(payload.get("requirement_ids") or [])
        for key in ("preserved_requirement_ids", "degraded_requirement_ids"):
            values = fallback.get(key)
            if not _valid_unique_strings(values) or any(value not in requirement_ids for value in values or []):
                errors.append(f"{prefix}.fallback_{key}_invalid")

    redistribution = payload.get("redistribution")
    if not isinstance(redistribution, dict) or set(redistribution) != {"state", "evidence"}:
        errors.append(f"{prefix}.redistribution_invalid")

    verification = payload.get("verification")
    if not isinstance(verification, dict) or set(verification) != {"kind", "argv", "network"}:
        errors.append(f"{prefix}.verification_invalid")
    else:
        if _argv_invalid(verification.get("argv"), allow_empty=kind not in {"BUNDLED_LOCAL", "FRAMEWORK_ADAPTER"}, allow_port=kind == "MCP_ADAPTER" and verification.get("kind") == "MCP_CONTRACT"):
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
            elif _shell_forbidden(execution.get("argv")):
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
    if kind == "RUNTIME_NATIVE":
        capability = payload.get("runtime_capability")
        if not isinstance(capability, dict) or set(capability) != {"name", "runtimes"} or not capability.get("name"):
            errors.append(f"{prefix}.runtime_capability_required")

    mcp = payload.get("mcp")
    mcp_keys = {
        "server_id", "config_file", "transport", "permission_scopes", "authentication",
        "setup", "service_boundary", "url",
    }
    mcp_mechanisms = {"MCP_REMOTE_HTTPS", "MCP_REGISTERED", "MCP_LOCAL_PROCESS"}
    raw_realizations = payload.get("realizations")
    needs_mcp = isinstance(raw_realizations, list) and any(
        isinstance(item, dict) and item.get("mechanism") in mcp_mechanisms for item in raw_realizations
    )
    if needs_mcp:
        if not isinstance(mcp, dict) or set(mcp) != mcp_keys or not _safe_path(mcp.get("config_file")):
            errors.append(f"{prefix}.mcp_contract_invalid")
        elif any(item.get("mechanism") == "MCP_REMOTE_HTTPS" for item in raw_realizations if isinstance(item, dict)):
            endpoint = mcp.get("url")
            parsed = urlsplit(endpoint) if isinstance(endpoint, str) else None
            if (
                parsed is None
                or parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
            ):
                errors.append(f"{prefix}.mcp_url_invalid")
            if parsed is not None and (parsed.username is not None or parsed.password is not None):
                errors.append(f"{prefix}.credential_material_forbidden")

    if _contains_credentials(payload):
        errors.append(f"{prefix}.credential_material_forbidden")

    realization_targets: list[str] = []
    if not isinstance(raw_realizations, list):
        errors.append(f"{prefix}.realizations_invalid")
    else:
        for item in raw_realizations:
            target = item.get("target_runtime") if isinstance(item, dict) and isinstance(item.get("target_runtime"), str) else ""
            if target:
                realization_targets.append(target)
            result = validate_runtime_realization(
                item,
                operation_id=identifier,
                runtime_targets=declared_runtimes,
                dependency_ids=dependency_ids,
                permission_ids=permission_ids_by_runtime.get(target, set()),
            )
            errors.extend(result.errors)
            blockers.extend(result.blockers)
        for target in sorted(declared_runtimes):
            count = realization_targets.count(target)
            if count == 0:
                errors.append(f"{prefix}.realization_missing:{target}")
            elif count > 1:
                errors.append(f"{prefix}.realization_duplicate:{target}")

    return ApplicationToolContract(
        identifier,
        kind,
        required,
        dict(payload),
        tuple(sorted(set(errors))),
        tuple(sorted(set(blockers))),
    )


def validate_application_tool_contract(payload: object) -> ApplicationToolContract:
    """Validate the explicitly versioned application-tool contract."""

    if not isinstance(payload, dict):
        return ApplicationToolContract("", "", False, {}, ("tool.invalid_object",), ())
    if payload.get("schema") == "plugin-builder-application-tool-v2":
        return _validate_v2_application_tool_contract(payload)
    return _validate_v1_application_tool_contract(payload)
