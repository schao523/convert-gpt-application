"""Plugin Builder context checks around the portable application-tool contract."""

from __future__ import annotations

from .bootstrap import plugin_authoring


def validate_tool_contract(
    payload: object,
    *,
    requirement_ids: set[str],
    skill_names: set[str],
    recipe_paths: set[str],
) -> tuple[list[str], list[str]]:
    validated = plugin_authoring.validate_application_tool_contract(payload)
    errors = list(validated.errors)
    blockers = list(validated.blockers)
    if not isinstance(payload, dict):
        return sorted(set(errors)), sorted(set(blockers))
    identifier = payload.get("id") if isinstance(payload.get("id"), str) else ""
    prefix = f"tool.{identifier}" if identifier else "tool"
    owned = payload.get("requirement_ids")
    if isinstance(owned, list):
        for item in owned:
            if item not in requirement_ids:
                errors.append(f"{prefix}.unknown_requirement:{item}")
    bindings = payload.get("skill_bindings")
    if isinstance(bindings, list) and any(item not in skill_names for item in bindings):
        errors.append(f"{prefix}.skill_binding_unknown")
    files = payload.get("files")
    if isinstance(files, list) and any(item not in recipe_paths for item in files):
        errors.append(f"{prefix}.file_recipe_missing")
    return sorted(set(errors)), sorted(set(blockers))
