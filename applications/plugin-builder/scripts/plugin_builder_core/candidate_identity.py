"""Canonical runtime identities shared by create, update, and verification."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from .implementation_plan import canonical_bytes
from .mcp_realization import expected_mcp_members, validate_mcp_projection
from .runtime_adapters import adapter_registry_sha256


def _digest(value: object) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def expected_tool_bindings(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "contract_sha256": _digest(tool),
            "dependencies": tool["dependencies"],
            "files": tool["files"],
            "implementation_kind": tool["implementation_kind"],
            "permissions": tool["permissions"],
            "requirements": tool["requirement_ids"],
            "runtime_targets": tool["runtime_targets"],
            "skills": tool["skill_bindings"],
            "tool_id": tool["id"],
        }
        for tool in sorted(tools, key=lambda item: item["id"])
    ]


def runtime_identity_fields(plan: dict[str, Any], tree: Path) -> dict[str, Any]:
    """Return exact W1-bound fields, or reject a stale runtime plan/tree."""
    capabilities = plan.get("capabilities")
    if not isinstance(capabilities, list):
        return {}
    tools = plan.get("tools")
    if not isinstance(tools, list):
        raise ValueError("runtime_tools_invalid")
    ordered_capabilities = sorted(capabilities, key=lambda item: item["id"])
    realizations = sorted(
        (
            {"tool_id": tool["id"], **realization}
            for tool in tools
            for realization in tool.get("realizations", [])
        ),
        key=lambda item: (item["tool_id"], item["target_runtime"]),
    )
    identities = {
        "capabilities_sha256": _digest(ordered_capabilities),
        "realizations_sha256": _digest(realizations),
        "adapter_registry_sha256": adapter_registry_sha256(),
    }
    if any(plan.get(key) != value for key, value in identities.items()):
        raise ValueError("runtime_plan_identity_mismatch")
    mcp_errors = validate_mcp_projection(plan, tree)
    if mcp_errors:
        raise ValueError("runtime_configuration_mismatch:" + mcp_errors[0])
    configuration = [
        {"path": path, "sha256": sha256((tree / path).read_bytes()).hexdigest()}
        for path in sorted(expected_mcp_members(plan))
    ]
    dependencies = sorted(
        ({"tool_id": tool["id"], **dependency} for tool in tools for dependency in tool["dependencies"]),
        key=canonical_bytes,
    )
    permissions = sorted(
        ({"tool_id": tool["id"], **permission} for tool in tools for permission in tool["permissions"]),
        key=canonical_bytes,
    )
    return {
        **identities,
        "capabilities": ordered_capabilities,
        "realizations": realizations,
        "generated_runtime_configuration": configuration,
        "generated_runtime_configuration_sha256": _digest(configuration),
        "dependencies_sha256": _digest(dependencies),
        "permissions_sha256": _digest(permissions),
    }


__all__ = ["expected_tool_bindings", "runtime_approval_errors", "runtime_identity_fields"]


def runtime_approval_errors(plan: dict[str, Any], plan_identity: dict, w1: dict) -> tuple[str, ...]:
    if not isinstance(plan.get("capabilities"), list):
        return ()
    errors = []
    for key in ("capabilities_sha256", "realizations_sha256", "adapter_registry_sha256"):
        if plan.get(key) != plan_identity.get(key) or plan.get(key) != w1.get(key):
            errors.append(f"build.{key}_mismatch")
    return tuple(errors)
