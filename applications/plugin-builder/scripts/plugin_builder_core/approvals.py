"""Explicit W1 approval recording for exact canonical plan identities."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from .implementation_plan import canonical_bytes, write_bytes_transactionally
from .tool_contract import validate_tool_contract


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
    for tool in tools:
        tool_errors, tool_blockers = validate_tool_contract(
            tool,
            requirement_ids={item for item in requirements if isinstance(item, str)},
            skill_names={item for item in skills if isinstance(item, str)},
            recipe_paths={item for item in available_paths if isinstance(item, str)},
        )
        errors.extend(tool_errors)
        blockers.extend(tool_blockers)
    if errors:
        return "FAIL", sorted(set(errors)), {}
    if blockers:
        return "BLOCKED", sorted(set(blockers)), {
            "plan_sha256": plan_hash,
            "tools_sha256": tools_hash,
        }
    if not confirmed_by.strip() or not evidence.strip():
        return "FAIL", ["w1.confirmation_incomplete"], {}
    session["w1"] = {
        "approved": True,
        "confirmed_by": confirmed_by,
        "evidence": evidence,
        "plan_sha256": plan_hash,
        "tools_sha256": tools_hash,
    }
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
    return "PASS", [], {"plan_sha256": plan_hash, "tools_sha256": tools_hash, "tool_summary": summary}


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
        if report.get("candidate_sha256") != candidate.get("sha256"):
            errors.append("w2.report_candidate_mismatch")
        if any(item.get("required") is True and item.get("state") == "FAIL" for item in report.get("requirements", [])):
            errors.append("w2.required_failure")
        if any(item.get("required") is True and item.get("state") != "PASS" for item in report.get("checks", [])):
            errors.append("w2.required_check_incomplete")
        if any(item.get("required") is True and item.get("state") != "PASS" and (item.get("fallback") or {}).get("policy") == "BLOCK" for item in report.get("tools", [])):
            errors.append("w2.required_tool_evidence_missing")
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
