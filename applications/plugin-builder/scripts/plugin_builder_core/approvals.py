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
    blockers: list[str] = []
    for tool in tools:
        tool_errors, tool_blockers = validate_tool_contract(
            tool,
            requirement_ids={item for item in requirements if isinstance(item, str)},
            skill_names={item for item in skills if isinstance(item, str)},
            recipe_paths={item for item in recipes if isinstance(item, str)},
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
