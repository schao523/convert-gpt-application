"""Explicit W1 approval recording for exact canonical plan identities."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from .bootstrap import plugin_authoring
from .implementation_plan import canonical_bytes, write_bytes_transactionally
from .runtime_adapters import adapter_registry_sha256, validate_realization_against_registry
from .tool_contract import validate_tool_contract


def _runtime_identities(plan: dict[str, object]) -> tuple[str, str, str]:
    capabilities = plan.get("capabilities")
    tools = plan.get("tools")
    sorted_capabilities = sorted(capabilities, key=lambda item: item["id"]) if isinstance(capabilities, list) else []
    realizations = sorted(
        (
            {"tool_id": tool["id"], **realization}
            for tool in tools if isinstance(tool, dict) and isinstance(tool.get("id"), str)
            for realization in tool.get("realizations", []) if isinstance(realization, dict)
        ),
        key=lambda item: (item["tool_id"], item["target_runtime"]),
    ) if isinstance(tools, list) else []
    return (
        sha256(canonical_bytes(sorted_capabilities)).hexdigest(),
        sha256(canonical_bytes(realizations)).hexdigest(),
        adapter_registry_sha256(),
    )


def approve_w1(session_path: Path, confirmed_by: str, evidence: str) -> tuple[str, list[str], dict[str, object]]:
    try:
        session = json.loads(Path(session_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "FAIL", ["session_input.invalid_json"], {}
    if not isinstance(session, dict) or session.get("schema_version") != 2 or not isinstance(session.get("plan"), dict):
        return "FAIL", ["w1.plan_required"], {}
    plan_path = Path(session_path).parent / session["plan"].get("path", "")
    try:
        plan_bytes = plan_path.read_bytes()
        plan = json.loads(plan_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "FAIL", ["w1.plan_unreadable"], {}
    plan_hash = sha256(plan_bytes).hexdigest()
    tools = plan.get("tools") if isinstance(plan, dict) else None
    if not isinstance(tools, list):
        return "FAIL", ["w1.plan_invalid"], {}
    tools_hash = sha256(canonical_bytes(tools)).hexdigest()
    errors: list[str] = []
    if plan_hash != session["plan"].get("sha256"):
        errors.append("w1.plan_sha256_mismatch")
    if tools_hash != session["plan"].get("tools_sha256"):
        errors.append("w1.tools_sha256_mismatch")
    requirements = {item.get("id") for item in plan.get("requirements", []) if isinstance(item, dict)}
    skills = {item.get("name") for item in plan.get("skills", []) if isinstance(item, dict)}
    recipes = {item.get("path") for item in plan.get("files", []) if isinstance(item, dict)}
    available_paths = (
        set(plan.get("expected_members", []))
        if plan.get("operation") == "update"
        else recipes
    )
    blockers: list[str] = []
    capabilities = plan.get("capabilities")
    runtime_plan = isinstance(capabilities, list)
    capability_ids: set[str] | None = None
    runtime_hashes: tuple[str, str, str] | None = None
    if runtime_plan:
        capability_ids = {
            item.get("id") for item in capabilities
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        capability_errors, capability_blockers = plugin_authoring.validate_capability_register(
            capabilities,
            requirement_ids={item for item in requirements if isinstance(item, str)},
            skill_names={item for item in skills if isinstance(item, str)},
        )
        errors.extend(capability_errors)
        blockers.extend(capability_blockers)
        runtime_hashes = _runtime_identities(plan)
        for key, actual in zip(
            ("capabilities_sha256", "realizations_sha256", "adapter_registry_sha256"),
            runtime_hashes,
        ):
            if plan.get(key) != actual or session["plan"].get(key) != actual:
                errors.append(f"w1.{key}_mismatch")
    registry_blockers_by_realization: dict[tuple[str, str], tuple[str, ...]] = {}
    for tool in tools:
        tool_errors, tool_blockers = validate_tool_contract(
            tool,
            requirement_ids={item for item in requirements if isinstance(item, str)},
            skill_names={item for item in skills if isinstance(item, str)},
            recipe_paths={item for item in available_paths if isinstance(item, str)},
            capability_ids=capability_ids,
        )
        errors.extend(tool_errors)
        blockers.extend(tool_blockers)
        if runtime_plan and isinstance(tool, dict):
            for realization in tool.get("realizations", []):
                if not isinstance(realization, dict):
                    continue
                registry_errors, registry_blockers = validate_realization_against_registry(
                    realization,
                    installation_channel="OPENAI_PORTABLE_PLUGIN",
                )
                errors.extend(registry_errors)
                target = realization.get("target_runtime")
                if isinstance(tool.get("id"), str) and isinstance(target, str):
                    registry_blockers_by_realization[(tool["id"], target)] = registry_blockers
    if runtime_plan:
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
        processed: set[tuple[str, str]] = set()
        for capability in capabilities:
            if not isinstance(capability, dict) or capability.get("realization_need") != "TOOL_REQUIRED":
                continue
            capability_id = capability.get("id")
            tool_id = capability.get("tool_id")
            tool = tools_by_id.get(tool_id)
            if not isinstance(capability_id, str) or not isinstance(tool_id, str) or tool is None:
                continue
            by_target = {
                item.get("target_runtime"): item
                for item in tool.get("realizations", []) if isinstance(item, dict)
            }
            for target in capability.get("runtime_targets", []):
                identity = (tool_id, target)
                processed.add(identity)
                realization = by_target.get(target)
                if not isinstance(realization, dict):
                    continue
                state = realization.get("feasibility_state")
                if state in {"FEASIBLE", "FEASIBLE_WITH_SETUP"}:
                    blockers.extend(registry_blockers_by_realization.get(identity, ()))
                    continue
                fallback = tool.get("fallback") if isinstance(tool.get("fallback"), dict) else {}
                alternative = operations_by_id.get(fallback.get("alternative_operation_id"))
                alternative_ready = any(
                    isinstance(item, dict)
                    and item.get("target_runtime") == target
                    and item.get("feasibility_state") in {"FEASIBLE", "FEASIBLE_WITH_SETUP"}
                    for item in alternative.get("realizations", [])
                ) if isinstance(alternative, dict) else False
                preserves = set(capability.get("requirement_ids", [])).issubset(
                    set(fallback.get("preserved_requirement_ids", []))
                )
                if fallback.get("policy") == "ALTERNATIVE" and alternative_ready and preserves:
                    if set(fallback.get("degraded_requirement_ids", [])) & set(capability.get("requirement_ids", [])):
                        blockers.append(f"capability.{capability_id}.fallback_design_approval_required:{target}")
                    continue
                if fallback.get("policy") == "OMIT_OPTIONAL" and tool.get("required") is False:
                    continue
                blockers.extend(registry_blockers_by_realization.get(identity, ()))
                blockers.append(f"capability.{capability_id}.runtime_infeasible:{target}:{state}")
        for identity, registry_blockers in registry_blockers_by_realization.items():
            if identity not in processed:
                blockers.extend(registry_blockers)
    if errors:
        return "FAIL", sorted(set(errors)), {}
    if blockers:
        return "BLOCKED", sorted(set(blockers)), {
            "plan_sha256": plan_hash,
            "tools_sha256": tools_hash,
        }
    if not confirmed_by.strip() or not evidence.strip():
        return "FAIL", ["w1.confirmation_incomplete"], {}
    w1_record = {
        "approved": True,
        "confirmed_by": confirmed_by,
        "evidence": evidence,
        "plan_sha256": plan_hash,
        "tools_sha256": tools_hash,
    }
    if runtime_hashes is not None:
        w1_record.update({
            "capabilities_sha256": runtime_hashes[0],
            "realizations_sha256": runtime_hashes[1],
            "adapter_registry_sha256": runtime_hashes[2],
        })
    session["w1"] = w1_record
    session["stage"] = "S3"
    write_bytes_transactionally(Path(session_path), canonical_bytes(session))
    summary = [
        {
            "id": tool["id"],
            "implementation_kind": tool["implementation_kind"],
            "permissions": tool["permissions"],
            "runtime_targets": tool["runtime_targets"],
            "dependencies": tool["dependencies"],
            "fallback": tool["fallback"],
            "verification": tool["verification"],
        }
        for tool in tools
    ]
    result: dict[str, object] = {
        "plan_sha256": plan_hash,
        "tools_sha256": tools_hash,
        "tool_summary": summary,
    }
    if runtime_hashes is not None:
        result.update({
            "capabilities_sha256": runtime_hashes[0],
            "realizations_sha256": runtime_hashes[1],
            "adapter_registry_sha256": runtime_hashes[2],
            "capability_summary": [
                {
                    "id": capability["id"],
                    "tool_id": capability["tool_id"],
                    "runtime_targets": [
                        {
                            "target_runtime": target,
                            **(
                                next(
                                    (
                                        {
                                            "feasibility_state": item["feasibility_state"],
                                            "setup_owner": item["setup_owner"],
                                            "dependency_ids": item["dependency_ids"],
                                            "permission_ids": item["permission_ids"],
                                            "evidence_policy": item["evidence_policy"],
                                        }
                                        for tool in tools if isinstance(tool, dict) and tool.get("id") == capability.get("tool_id")
                                        for item in tool.get("realizations", [])
                                        if isinstance(item, dict) and item.get("target_runtime") == target
                                    ),
                                    {"feasibility_state": "SKILL_ONLY"},
                                )
                            ),
                        }
                        for target in capability["runtime_targets"]
                    ],
                }
                for capability in sorted(capabilities, key=lambda item: item["id"])
            ],
        })
    return "PASS", [], result


def approve_w2(session_path: Path, confirmed_by: str, evidence: str) -> tuple[str, list[str], dict[str, object]]:
    path = Path(session_path)
    try:
        session = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "FAIL", ["session_input.invalid_json"], {}
    candidate = session.get("candidate") if isinstance(session, dict) else None
    verification = session.get("verification") if isinstance(session, dict) else None
    if not isinstance(candidate, dict) or not isinstance(verification, dict):
        return "BLOCKED", ["w2.verification_required"], {}
    if session.get("stage") in {"H1", "E2"}:
        return "BLOCKED", ["w2.session_inactive"], {}
    from .bootstrap import plugin_authoring

    candidate_root = path.parent / str(candidate.get("path", ""))
    report_path = path.parent / str(verification.get("path", ""))
    errors: list[str] = []
    if not candidate_root.is_dir() or plugin_authoring.tree_sha256(candidate_root) != candidate.get("sha256"):
        errors.append("w2.candidate_sha256_mismatch")
    try:
        report_bytes = report_path.read_bytes()
        report = json.loads(report_bytes.decode("ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        report = None
        report_bytes = b""
        errors.append("w2.report_invalid")
    if sha256(report_bytes).hexdigest() != verification.get("sha256"):
        errors.append("w2.report_sha256_mismatch")
    if isinstance(report, dict):
        if report.get("status") != "PASS":
            errors.append("w2.verification_incomplete")
        if report.get("candidate_sha256") != candidate.get("sha256"):
            errors.append("w2.report_candidate_mismatch")
        if any(item.get("required") is True and item.get("state") == "FAIL" for item in report.get("requirements", [])):
            errors.append("w2.required_failure")
        if any(item.get("required") is True and item.get("state") != "PASS" for item in report.get("checks", [])):
            errors.append("w2.required_check_incomplete")
        if any(item.get("required") is True and item.get("state") != "PASS" and (item.get("fallback") or {}).get("policy") == "BLOCK" for item in report.get("tools", [])):
            errors.append("w2.required_tool_evidence_missing")
        if any(
            item.get("evidence_policy") == "REQUIRED_BEFORE_W2" and item.get("state") != "RUNTIME VERIFIED"
            for item in report.get("runtime_realizations", []) if isinstance(item, dict)
        ):
            errors.append("w2.required_runtime_realization_missing")
    plan_identity = session.get("plan") or {}
    plan_path = path.parent / str(plan_identity.get("path", ""))
    try:
        plan_bytes = plan_path.read_bytes()
    except OSError:
        plan_bytes = b""
    plan_hash = sha256(plan_bytes).hexdigest()
    if plan_hash != plan_identity.get("sha256") or plan_hash != (session.get("w1") or {}).get("plan_sha256") or plan_hash != candidate.get("plan_sha256"):
        errors.append("w2.plan_sha256_mismatch")
    if errors:
        session["w2"] = None
        session["package"] = None
        write_bytes_transactionally(path, canonical_bytes(session))
        return "BLOCKED", sorted(set(errors)), {}
    if not confirmed_by.strip() or not evidence.strip():
        return "FAIL", ["w2.confirmation_incomplete"], {}
    session["w2"] = {
        "approved": True, "confirmed_by": confirmed_by.strip(), "evidence": evidence.strip(),
        "candidate_sha256": candidate["sha256"], "verification_sha256": verification["sha256"],
    }
    session["stage"] = "S5"
    write_bytes_transactionally(path, canonical_bytes(session))
    return "PASS", [], {
        "candidate_sha256": candidate["sha256"], "verification_sha256": verification["sha256"],
        "tool_summary": report.get("tools", []) if isinstance(report, dict) else [],
    }
