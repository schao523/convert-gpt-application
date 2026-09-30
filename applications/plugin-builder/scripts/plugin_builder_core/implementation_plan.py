"""Compile semantic proposals into canonical, hash-bound implementation plans."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
from typing import Any

from .tool_contract import validate_tool_contract


_PROPOSAL_KEYS = {
    "schema", "operation", "plugin", "requirements", "skills", "files", "tools",
    "implementation_decisions", "checks", "expected_members",
}
_CHECK_KINDS = {"PLUGIN_STRUCTURE", "SKILL_STRUCTURE", "REFERENCE_CLOSURE", "REQUIREMENT_COVERAGE", "PYTHON_ARGV"}


@dataclass(frozen=True)
class PlanOutcome:
    status: str
    errors: tuple[str, ...]
    blockers: tuple[str, ...]
    plan_sha256: str | None = None
    tools_sha256: str | None = None


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


def compile_plan(inspection: object, proposal: object, output: Path) -> PlanOutcome:
    inspection_payload, errors = _load(inspection, "inspection.invalid_json")
    proposal_payload, proposal_errors = _load(proposal, "proposal.invalid_json")
    errors.extend(proposal_errors)
    if inspection_payload is None or proposal_payload is None:
        return PlanOutcome("FAIL", tuple(sorted(set(errors))), ())
    if inspection_payload.get("schema") != "plugin-builder-inspection-v1":
        errors.append("inspection.schema_unsupported")
    if proposal_payload.get("schema") != "plugin-builder-plan-proposal-v1":
        errors.append("proposal.schema_unsupported")
    if set(proposal_payload) != _PROPOSAL_KEYS:
        errors.append("proposal.invalid_keys")
    if proposal_payload.get("operation") != inspection_payload.get("operation"):
        errors.append("plan.operation_mismatch")

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
            "path", "requirement_ids", "classification", "source_sha256",
            "redistribution", *origins,
        }
        if set(item) != allowed or len(origins) != 1:
            errors.append(f"plan.file_origin_invalid:{path}")
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
    } | {"PLUGIN-BUILDER-MANIFEST.json"}
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
    blockers: list[str] = []
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
        )
        errors.extend(tool_errors)
        blockers.extend(tool_blockers)
        if isinstance(tool, dict) and isinstance(tool.get("id"), str):
            if tool["id"] in tool_ids:
                errors.append(f"tool.duplicate_id:{tool['id']}")
            tool_ids.add(tool["id"])

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

    if errors:
        return PlanOutcome("FAIL", tuple(sorted(set(errors))), tuple(sorted(set(blockers))))
    plan = dict(proposal_payload)
    plan["schema"] = "plugin-builder-implementation-plan-v1"
    plan["requirements"] = sorted(plan["requirements"], key=lambda item: item["id"])
    plan["skills"] = sorted(plan["skills"], key=lambda item: item["name"])
    plan["files"] = sorted(plan["files"], key=lambda item: item["path"])
    plan["tools"] = sorted(plan["tools"], key=lambda item: item["id"])
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
    )
