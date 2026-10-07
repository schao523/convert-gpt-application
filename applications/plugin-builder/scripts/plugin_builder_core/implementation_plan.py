"""Compile semantic proposals into canonical, hash-bound implementation plans."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
from typing import Any

from .bootstrap import plugin_authoring
from .artifact_quality import CONTENT_ROLES
from .proposed_tree import preflight_proposed_tree
from .mcp_realization import expected_mcp_members
from .runtime_adapters import (
    adapter_registry_sha256,
    validate_realization_against_registry,
)
from .tool_contract import validate_tool_contract


_PROPOSAL_V1_KEYS = {
    "schema", "operation", "plugin", "requirements", "skills", "files", "tools",
    "implementation_decisions", "checks", "expected_members",
}
_PROPOSAL_V2_KEYS = _PROPOSAL_V1_KEYS | {"capabilities"}
_CHECK_KINDS = {"PLUGIN_STRUCTURE", "SKILL_STRUCTURE", "REFERENCE_CLOSURE", "REQUIREMENT_COVERAGE", "PYTHON_ARGV"}


@dataclass(frozen=True)
class PlanOutcome:
    status: str
    errors: tuple[str, ...]
    blockers: tuple[str, ...]
    plan_sha256: str | None = None
    tools_sha256: str | None = None
    capabilities_sha256: str | None = None
    realizations_sha256: str | None = None
    adapter_registry_sha256: str | None = None


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def write_bytes_transactionally(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
            temporary = output.name
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def _safe_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        return False
    parts = value.split("/")
    return not any(part in {"", ".", ".."} for part in parts) and ":" not in parts[0] and PurePosixPath(value).as_posix() == value


def _load(value: object, code: str) -> tuple[dict[str, Any] | None, list[str]]:
    if isinstance(value, dict):
        return value, []
    if not isinstance(value, (str, Path)):
        return None, [code]
    try:
        payload = json.loads(Path(value).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, [code]
    return (payload, []) if isinstance(payload, dict) else (None, [code])


def _json_strings(value: object) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return set().union(*(_json_strings(item) for item in value), set())
    if isinstance(value, dict):
        return set().union(*(_json_strings(item) for item in value.values()), set())
    return set()


def _canonicalize_manifest_intent(proposal: dict[str, Any]) -> list[str]:
    """Make root plugin.json authoritative before validation and W1 hashing."""
    files = proposal.get("files")
    expected = proposal.get("expected_members")
    decisions = proposal.get("implementation_decisions")
    if not isinstance(files, list) or not isinstance(expected, list) or not isinstance(decisions, dict):
        return []
    root_recipe = next(
        (item for item in files if isinstance(item, dict) and item.get("path") == "plugin.json"),
        None,
    )
    legacy_recipe = next(
        (item for item in files if isinstance(item, dict) and item.get("path") == ".codex-plugin/plugin.json"),
        None,
    )
    decision = "GENERATE" if root_recipe is not None else "PRESERVE"
    errors: list[str] = []
    if root_recipe is None and legacy_recipe is not None:
        legacy = legacy_recipe.get("inline_json")
        try:
            portable = plugin_authoring.portable_manifest_from_legacy(legacy)
        except plugin_authoring.PluginAuthoringError:
            errors.append("plan.legacy_manifest_invalid")
        else:
            root_recipe = dict(legacy_recipe)
            root_recipe["path"] = "plugin.json"
            root_recipe["inline_json"] = portable
            root_recipe["source_sha256"] = sha256(canonical_bytes(portable)).hexdigest()
            files[files.index(legacy_recipe)] = root_recipe
            decision = "ADAPT"
    elif root_recipe is not None and legacy_recipe is not None:
        files.remove(legacy_recipe)
        decision = "GENERATE"
    if root_recipe is not None:
        payload = root_recipe.get("inline_json")
        if not isinstance(payload, dict) or payload.get("$schema") != plugin_authoring.PORTABLE_PLUGIN_SCHEMA:
            errors.append("plan.portable_manifest_invalid")
    for member in ("plugin.json", ".codex-plugin/plugin.json"):
        if member not in expected:
            expected.append(member)
    decisions["manifest_authority"] = {
        "authority": "plugin.json",
        "compatibility_overlay": ".codex-plugin/plugin.json",
        "decision": decision,
    }
    return errors


def compile_plan(inspection: object, proposal: object, output: Path) -> PlanOutcome:
    inspection_payload, errors = _load(inspection, "inspection.invalid_json")
    proposal_payload, proposal_errors = _load(proposal, "proposal.invalid_json")
    errors.extend(proposal_errors)
    if inspection_payload is None or proposal_payload is None:
        return PlanOutcome("FAIL", tuple(sorted(set(errors))), ())
    if inspection_payload.get("schema") != "plugin-builder-inspection-v1":
        errors.append("inspection.schema_unsupported")
    proposal_schema = proposal_payload.get("schema")
    if proposal_schema == "plugin-builder-plan-proposal-v1":
        return PlanOutcome("BLOCKED", (), ("plan.proposal_v2_required",))
    if proposal_schema != "plugin-builder-plan-proposal-v2":
        errors.append("proposal.schema_unsupported")
    if set(proposal_payload) != _PROPOSAL_V2_KEYS:
        errors.append("proposal.invalid_keys")
    if proposal_payload.get("operation") != inspection_payload.get("operation"):
        errors.append("plan.operation_mismatch")
    errors.extend(_canonicalize_manifest_intent(proposal_payload))

    inspected_requirements = {
        item.get("id") for item in inspection_payload.get("requirements", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    proposed_requirements = proposal_payload.get("requirements")
    proposed_ids: set[str] = set()
    if not isinstance(proposed_requirements, list):
        errors.append("plan.requirements_invalid")
        proposed_requirements = []
    for item in proposed_requirements:
        if not isinstance(item, dict) or set(item) != {"id", "owner_skill", "implementation_paths", "evidence_targets"}:
            errors.append("plan.requirement_invalid")
            continue
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier:
            errors.append("plan.requirement_id_invalid")
            continue
        if identifier in proposed_ids:
            errors.append(f"plan.requirement_duplicate:{identifier}")
        proposed_ids.add(identifier)
        if not isinstance(item.get("implementation_paths"), list) or not item["implementation_paths"]:
            errors.append(f"plan.requirement_implementation_missing:{identifier}")
        if not isinstance(item.get("evidence_targets"), list) or not item["evidence_targets"]:
            errors.append(f"plan.requirement_evidence_missing:{identifier}")
    for identifier in sorted(inspected_requirements - proposed_ids):
        errors.append(f"plan.requirement_uncovered:{identifier}")
    for identifier in sorted(proposed_ids - inspected_requirements):
        errors.append(f"plan.requirement_invented:{identifier}")

    blockers: list[str] = []
    skills = proposal_payload.get("skills")
    skill_names: set[str] = set()
    if not isinstance(skills, list) or len(skills) < 1:
        errors.append("plan.skills_invalid")
        skills = []
    for item in skills:
        if not isinstance(item, dict) or set(item) != {"name", "description", "requirement_ids"}:
            errors.append("plan.skill_invalid")
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name:
            errors.append("plan.skill_name_invalid")
        else:
            skill_names.add(name)
        if any(req not in inspected_requirements for req in item.get("requirement_ids", [])):
            errors.append(f"plan.skill_requirement_unknown:{name}")
    for item in proposed_requirements:
        if isinstance(item, dict) and item.get("owner_skill") not in skill_names:
            errors.append(f"plan.requirement_owner_unknown:{item.get('id', '')}")

    capabilities = proposal_payload.get("capabilities")
    capability_errors, capability_blockers = plugin_authoring.validate_capability_register(
        capabilities,
        requirement_ids={item for item in inspected_requirements if isinstance(item, str)},
        skill_names=skill_names,
    )
    errors.extend(capability_errors)
    blockers.extend(capability_blockers)
    capability_ids = {
        item.get("id") for item in capabilities or []
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    } if isinstance(capabilities, list) else set()
    covered_requirements = {
        requirement
        for capability in capabilities or [] if isinstance(capability, dict)
        for requirement in capability.get("requirement_ids", [])
        if isinstance(requirement, str)
    } if isinstance(capabilities, list) else set()
    for identifier in sorted(inspected_requirements - covered_requirements):
        errors.append(f"plan.requirement_capability_uncovered:{identifier}")

    files = proposal_payload.get("files")
    recipe_paths: set[str] = set()
    recipes_by_path: dict[str, dict[str, Any]] = {}
    if not isinstance(files, list):
        errors.append("plan.files_invalid")
        files = []
    workspace_root = Path(inspection).parent if isinstance(inspection, (str, Path)) else Path(output).parent
    for item in files:
        if not isinstance(item, dict):
            errors.append("plan.file_recipe_invalid")
            continue
        path = item.get("path")
        if not _safe_path(path):
            errors.append("plan.file_path_invalid")
            continue
        if path in recipe_paths:
            errors.append(f"plan.file_duplicate:{path}")
        recipe_paths.add(path)
        recipes_by_path[path] = item
        origins = [key for key in ("inline_text", "inline_json", "source_path") if key in item]
        allowed = {
            "path", "requirement_ids", "classification", "content_role", "source_sha256",
            "redistribution", *origins,
        }
        if set(item) != allowed or len(origins) != 1:
            errors.append(f"plan.file_origin_invalid:{path}")
        role = item.get("content_role")
        if role is None:
            errors.append(f"plan.content_role_missing:{path}")
        elif role not in CONTENT_ROLES:
            errors.append(f"plan.content_role_invalid:{path}")
        if any(req not in inspected_requirements for req in item.get("requirement_ids", [])):
            errors.append(f"plan.file_requirement_unknown:{path}")
        redistribution = item.get("redistribution")
        if (
            not isinstance(redistribution, dict)
            or set(redistribution) != {"state", "evidence"}
            or redistribution.get("state") != "APPROVED"
            or not redistribution.get("evidence")
        ):
            errors.append(f"plan.file_rights_unapproved:{path}")
        expected_classification = {
            "inline_text": "generated_text",
            "inline_json": "generated_json",
            "source_path": "approved_source",
        }.get(origins[0] if len(origins) == 1 else "")
        if item.get("classification") != expected_classification:
            errors.append(f"plan.file_classification_invalid:{path}")
        if "source_path" in item:
            source_path = item["source_path"]
            if not _safe_path(source_path) or not (workspace_root / Path(*PurePosixPath(source_path).parts)).is_file():
                errors.append(f"plan.file_source_missing:{path}")
    for path, item in recipes_by_path.items():
        marker = "/references/"
        if marker not in path or "source_path" not in item:
            continue
        skill_prefix, reference_name = path.split(marker, 1)
        skill_recipe = recipes_by_path.get(f"{skill_prefix}/SKILL.md")
        skill_text = skill_recipe.get("inline_text") if isinstance(skill_recipe, dict) else None
        target = f"references/{reference_name}"
        directly_routed = isinstance(skill_text, str) and (
            f"]({target})" in skill_text or f"](<{target}>)" in skill_text
        )
        index_target = "references/knowledge-index.json"
        index_recipe = recipes_by_path.get(f"{skill_prefix}/{index_target}")
        index_linked = isinstance(skill_text, str) and (
            f"]({index_target})" in skill_text or f"](<{index_target}>)" in skill_text
        )
        index_values = _json_strings(index_recipe.get("inline_json")) if isinstance(index_recipe, dict) else set()
        indexed = index_linked and any(value in {reference_name, target} or value.endswith(f"/{reference_name}") for value in index_values)
        if not directly_routed and not indexed:
            errors.append(f"plan.reference_unrouted:{path}")
    expected = proposal_payload.get("expected_members")
    derived_paths = {
        f"skills/{name}/agents/openai.yaml" for name in skill_names
    } | {".codex-plugin/plugin.json", "PLUGIN-BUILDER-MANIFEST.json"} | set(expected_mcp_members(proposal_payload))
    if proposal_payload.get("operation") == "update":
        derived_paths.add("PLUGIN-BUILDER-CHANGES.json")
    expected_paths: set[str] = set()
    if not isinstance(expected, list) or any(not _safe_path(item) for item in expected):
        errors.append("plan.expected_members_invalid")
    else:
        expected_paths = set(expected)
        minimum = recipe_paths | derived_paths
        if len(expected) != len(expected_paths) or (
            proposal_payload.get("operation") == "create" and expected_paths != minimum
        ) or (
            proposal_payload.get("operation") == "update" and not minimum.issubset(expected_paths)
        ):
            errors.append("plan.expected_members_mismatch")

    checks = proposal_payload.get("checks")
    if not isinstance(checks, list):
        errors.append("plan.checks_invalid")
        checks = []
    check_ids: set[str] = set()
    checks_by_id: dict[str, dict[str, Any]] = {}
    for item in checks:
        if not isinstance(item, dict) or item.get("kind") not in _CHECK_KINDS:
            errors.append("plan.check_invalid")
            continue
        if type(item.get("required")) is not bool or not isinstance(item.get("id"), str):
            errors.append("plan.check_invalid")
        elif item["id"] in check_ids:
            errors.append(f"plan.check_duplicate:{item['id']}")
        else:
            check_ids.add(item["id"])
            checks_by_id[item["id"]] = item
        if item.get("required") is True and not item.get("requirement_ids"):
            errors.append(f"plan.check_requirement_missing:{item.get('id', '')}")
        if any(req not in inspected_requirements for req in item.get("requirement_ids", [])):
            errors.append(f"plan.check_requirement_unknown:{item.get('id', '')}")
        if item.get("kind") == "PYTHON_ARGV":
            argv = item.get("argv")
            if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) or not arg for arg in argv):
                errors.append(f"plan.check_argv_invalid:{item.get('id', '')}")

    tools = proposal_payload.get("tools")
    if not isinstance(tools, list):
        errors.append("plan.tools_invalid")
        tools = []
    tool_ids: set[str] = set()
    for tool in tools:
        tool_errors, tool_blockers = validate_tool_contract(
            tool,
            requirement_ids=inspected_requirements,
            skill_names=skill_names,
            recipe_paths=expected_paths if proposal_payload.get("operation") == "update" else recipe_paths,
            capability_ids={item for item in capability_ids if isinstance(item, str)},
        )
        errors.extend(tool_errors)
        blockers.extend(tool_blockers)
        if isinstance(tool, dict) and isinstance(tool.get("id"), str):
            if tool["id"] in tool_ids:
                errors.append(f"tool.duplicate_id:{tool['id']}")
            tool_ids.add(tool["id"])

    tools_by_id = {
        tool["id"]: tool for tool in tools
        if isinstance(tool, dict) and isinstance(tool.get("id"), str)
    }
    operations_by_id = {
        operation.get("id"): tool
        for tool in tools if isinstance(tool, dict)
        for operation in [tool.get("operation")]
        if isinstance(operation, dict) and isinstance(operation.get("id"), str)
    }
    for capability in capabilities or []:
        if not isinstance(capability, dict) or not isinstance(capability.get("id"), str):
            continue
        capability_id = capability["id"]
        tool_id = capability.get("tool_id")
        if capability.get("realization_need") != "TOOL_REQUIRED":
            continue
        tool = tools_by_id.get(tool_id)
        if tool is None:
            errors.append(f"capability.{capability_id}.tool_unknown:{tool_id}")
            continue
        if capability_id not in tool.get("capability_ids", []):
            errors.append(f"capability.{capability_id}.tool_binding_missing:{tool_id}")

    installation_channel = "OPENAI_PORTABLE_PLUGIN"
    realizations_for_hash: list[dict[str, Any]] = []
    registry_blockers_by_realization: dict[tuple[str, str], tuple[str, ...]] = {}
    for tool_id, tool in sorted(tools_by_id.items()):
        realizations = tool.get("realizations")
        if not isinstance(realizations, list):
            continue
        for realization in realizations:
            if not isinstance(realization, dict):
                continue
            realizations_for_hash.append({"tool_id": tool_id, **realization})
            registry_errors, registry_blockers = validate_realization_against_registry(
                realization,
                installation_channel=installation_channel,
            )
            errors.extend(registry_errors)
            target = realization.get("target_runtime")
            if isinstance(target, str):
                registry_blockers_by_realization[(tool_id, target)] = registry_blockers

    processed_realizations: set[tuple[str, str]] = set()
    for capability in capabilities or []:
        if not isinstance(capability, dict) or capability.get("realization_need") != "TOOL_REQUIRED":
            continue
        capability_id = capability.get("id")
        tool = tools_by_id.get(capability.get("tool_id"))
        if not isinstance(capability_id, str) or tool is None:
            continue
        by_target = {
            item.get("target_runtime"): item
            for item in tool.get("realizations", [])
            if isinstance(item, dict) and isinstance(item.get("target_runtime"), str)
        }
        for target in capability.get("runtime_targets", []):
            identity = (str(capability.get("tool_id")), str(target))
            processed_realizations.add(identity)
            realization = by_target.get(target)
            if not isinstance(realization, dict):
                continue
            state = realization.get("feasibility_state")
            if state in {"FEASIBLE", "FEASIBLE_WITH_SETUP"}:
                blockers.extend(registry_blockers_by_realization.get(identity, ()))
                continue
            fallback = tool.get("fallback") if isinstance(tool.get("fallback"), dict) else {}
            alternative_id = fallback.get("alternative_operation_id")
            alternative = operations_by_id.get(alternative_id)
            alternative_realization = next(
                (
                    item for item in alternative.get("realizations", [])
                    if isinstance(item, dict)
                    and item.get("target_runtime") == target
                    and item.get("feasibility_state") in {"FEASIBLE", "FEASIBLE_WITH_SETUP"}
                ),
                None,
            ) if isinstance(alternative, dict) else None
            preserves = set(capability.get("requirement_ids", [])).issubset(
                set(fallback.get("preserved_requirement_ids", []))
            )
            if fallback.get("policy") == "ALTERNATIVE" and alternative_realization is not None and preserves:
                if set(fallback.get("degraded_requirement_ids", [])) & set(capability.get("requirement_ids", [])):
                    blockers.append(f"capability.{capability_id}.fallback_design_approval_required:{target}")
                continue
            if fallback.get("policy") == "OMIT_OPTIONAL" and tool.get("required") is False:
                continue
            blockers.extend(registry_blockers_by_realization.get(identity, ()))
            blockers.append(f"capability.{capability_id}.runtime_infeasible:{target}:{state}")
    for identity, registry_blockers in registry_blockers_by_realization.items():
        if identity not in processed_realizations:
            blockers.extend(registry_blockers)

    tool_commands = {
        tuple((tool.get("verification") or {}).get("argv", [])): tool
        for tool in tools if isinstance(tool, dict) and isinstance(tool.get("verification"), dict)
    }
    for item in checks:
        if isinstance(item, dict) and item.get("kind") == "PYTHON_ARGV":
            bound_tool = tool_commands.get(tuple(item.get("argv", [])))
            if bound_tool is None:
                errors.append(f"plan.check_tool_unbound:{item.get('id', '')}")
            elif not set(item.get("requirement_ids", [])).issubset(set(bound_tool.get("requirement_ids", []))):
                errors.append(f"plan.check_tool_requirement_mismatch:{item.get('id', '')}")

    evidence_ids = check_ids | tool_ids
    for requirement in proposed_requirements:
        if not isinstance(requirement, dict) or not isinstance(requirement.get("id"), str):
            continue
        identifier = requirement["id"]
        for path in requirement.get("implementation_paths", []):
            if path not in expected_paths:
                errors.append(f"plan.requirement_implementation_unknown:{identifier}:{path}")
        for target in requirement.get("evidence_targets", []):
            if target not in evidence_ids:
                errors.append(f"plan.requirement_evidence_unknown:{identifier}:{target}")
                continue
            owner = checks_by_id.get(target)
            if owner is None:
                owner = next((tool for tool in tools if isinstance(tool, dict) and tool.get("id") == target), None)
            if isinstance(owner, dict) and identifier not in owner.get("requirement_ids", []):
                errors.append(f"plan.requirement_evidence_unowned:{identifier}:{target}")

    preflight_evidence: dict[str, Any] | None = None
    if not errors:
        preflight = preflight_proposed_tree(proposal_payload, workspace_root)
        errors.extend(preflight.diagnostics)
        preflight_evidence = preflight.evidence

    if errors:
        return PlanOutcome("FAIL", tuple(sorted(set(errors))), tuple(sorted(set(blockers))))
    assert isinstance(capabilities, list)
    sorted_capabilities = sorted(capabilities, key=lambda item: item["id"])
    sorted_realizations = sorted(
        realizations_for_hash,
        key=lambda item: (item["tool_id"], item["target_runtime"]),
    )
    capabilities_hash = sha256(canonical_bytes(sorted_capabilities)).hexdigest()
    realizations_hash = sha256(canonical_bytes(sorted_realizations)).hexdigest()
    registry_hash = adapter_registry_sha256()
    plan = dict(proposal_payload)
    plan["schema"] = "plugin-builder-implementation-plan-v2"
    plan["preflight_evidence"] = preflight_evidence
    plan["requirements"] = sorted(plan["requirements"], key=lambda item: item["id"])
    plan["skills"] = sorted(plan["skills"], key=lambda item: item["name"])
    plan["files"] = sorted(plan["files"], key=lambda item: item["path"])
    plan["tools"] = sorted(plan["tools"], key=lambda item: item["id"])
    plan["capabilities"] = sorted_capabilities
    plan["capabilities_sha256"] = capabilities_hash
    plan["realizations_sha256"] = realizations_hash
    plan["adapter_registry_sha256"] = registry_hash
    plan["checks"] = sorted(plan["checks"], key=lambda item: item["id"])
    plan["expected_members"] = sorted(plan["expected_members"])
    payload = canonical_bytes(plan)
    tools_payload = canonical_bytes(plan["tools"])
    write_bytes_transactionally(Path(output), payload)
    return PlanOutcome(
        "BLOCKED" if blockers else "PASS",
        (),
        tuple(sorted(set(blockers))),
        sha256(payload).hexdigest(),
        sha256(tools_payload).hexdigest(),
        capabilities_hash,
        realizations_hash,
        registry_hash,
    )
