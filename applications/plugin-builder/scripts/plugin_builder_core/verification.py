"""Deterministic candidate verification and requirement aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .bootstrap import plugin_authoring
from .implementation_plan import canonical_bytes, write_bytes_transactionally
from .tool_verification import execute_direct, verify_application_tool


@dataclass(frozen=True)
class VerificationOutcome:
    status: str
    errors: tuple[str, ...]
    report_sha256: str | None = None


def _load(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _check(identifier: str, kind: str, required: bool, requirement_ids: list[str], state: str, diagnostics=(), evidence=None) -> dict[str, Any]:
    return {
        "id": identifier, "kind": kind, "required": required,
        "requirement_ids": sorted(requirement_ids), "state": state,
        "diagnostics": sorted(set(diagnostics)), "evidence": evidence or {},
    }


def _structural_checks(candidate: Path, plan: dict[str, Any], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    diagnostics = plugin_authoring.validate_plugin_tree(candidate)
    plugin_errors = [f"{item.code}:{item.path}" for item in diagnostics]
    all_requirements = [item["id"] for item in plan.get("requirements", []) if isinstance(item, dict)]
    actual = {item.path for item in plugin_authoring.tree_manifest(candidate)}
    expected = set(manifest.get("expected_members", []))
    exact_state = "PASS" if actual == expected else "FAIL"
    checks = [
        _check("builtin-plugin-structure", "PLUGIN_STRUCTURE", True, all_requirements, "PASS" if not plugin_errors else "FAIL", plugin_errors),
        _check("builtin-skill-structure", "SKILL_STRUCTURE", True, all_requirements, "PASS" if not plugin_errors else "FAIL", plugin_errors),
        _check("builtin-reference-closure", "REFERENCE_CLOSURE", True, all_requirements, "PASS" if not plugin_errors else "FAIL", plugin_errors),
        _check("builtin-distribution-safety", "DISTRIBUTION_SAFETY", True, all_requirements, "PASS" if not plugin_errors else "FAIL", plugin_errors),
        _check("builtin-exact-members", "EXACT_MEMBERS", True, all_requirements, exact_state, [] if exact_state == "PASS" else ["candidate_member_mismatch"]),
        _check("builtin-tool-binding", "TOOL_BINDING", True, all_requirements, "PASS", evidence={"binding_count": len(manifest.get("tool_bindings", []))}),
    ]
    if plan.get("operation") == "update":
        changes = _load(candidate / "PLUGIN-BUILDER-CHANGES.json")
        baseline = candidate.parent / "baseline"
        failures: list[str] = []
        preserved = changes.get("preserved", []) if isinstance(changes, dict) else []
        for path in preserved:
            left, right = baseline / path, candidate / path
            if not left.is_file() or not right.is_file() or left.read_bytes() != right.read_bytes():
                failures.append(f"preservation_mismatch:{path}")
        checks.append(_check(
            "builtin-update-preservation", "UPDATE_PRESERVATION", True, all_requirements,
            "PASS" if changes is not None and not failures else "FAIL", failures,
            {"preserved_members": sorted(preserved)},
        ))
    return checks


def verify_candidate(session_path: Path) -> VerificationOutcome:
    session_file = Path(session_path)
    session = _load(session_file)
    if session is None or session.get("schema_version") != 2 or not isinstance(session.get("candidate"), dict):
        return VerificationOutcome("FAIL", ("verify.candidate_required",))
    root = session_file.parent
    candidate = root / str(session["candidate"].get("path", ""))
    if not candidate.is_dir() or plugin_authoring.tree_sha256(candidate) != session["candidate"].get("sha256"):
        session["verification"] = None
        session["w2"] = None
        session["package"] = None
        write_bytes_transactionally(session_file, canonical_bytes(session))
        return VerificationOutcome("BLOCKED", ("verify.candidate_sha256_mismatch",))
    plan = _load(root / str((session.get("plan") or {}).get("path", "")))
    manifest = _load(candidate / "PLUGIN-BUILDER-MANIFEST.json")
    if plan is None or manifest is None:
        return VerificationOutcome("FAIL", ("verify.inputs_invalid",))
    checks = _structural_checks(candidate, plan, manifest)
    tool_results = [verify_application_tool(tool, candidate) for tool in plan.get("tools", []) if isinstance(tool, dict)]

    for planned in plan.get("checks", []):
        if not isinstance(planned, dict):
            continue
        kind = planned.get("kind")
        if kind == "PYTHON_ARGV":
            result = execute_direct(planned.get("argv", []), candidate, 30)
            checks.append(_check(planned["id"], kind, planned["required"], planned.get("requirement_ids", []), result["state"], result["diagnostics"], {
                "argv": result["argv"], "executed": result["executed"],
                "stdout_sha256": result["stdout_sha256"], "stderr_sha256": result["stderr_sha256"],
            }))
        else:
            checks.append(_check(planned["id"], kind, planned["required"], planned.get("requirement_ids", []), "PASS"))

    requirements = []
    for requirement in plan.get("requirements", []):
        identifier = requirement["id"]
        states = [item["state"] for item in checks if identifier in item["requirement_ids"]]
        states += [item["state"] for item in tool_results if identifier in item["requirement_ids"]]
        state = "FAIL" if "FAIL" in states else "NOT VERIFIED" if "NOT VERIFIED" in states else "PASS" if states else "NOT VERIFIED"
        requirements.append({"id": identifier, "required": True, "state": state})
    blocked_tool = any(
        item["required"] and item["state"] != "PASS" and (item.get("fallback") or {}).get("policy") == "BLOCK"
        for item in tool_results
    )
    blocked = blocked_tool or any(item["required"] and item["state"] != "PASS" for item in requirements)
    report = {
        "schema": "plugin-builder-verification-report-v1",
        "candidate_sha256": session["candidate"]["sha256"],
        "plan_sha256": session["candidate"]["plan_sha256"],
        "checks": sorted(checks, key=lambda item: item["id"]),
        "tools": sorted(tool_results, key=lambda item: item["tool_id"]),
        "requirements": sorted(requirements, key=lambda item: item["id"]),
        "status": "BLOCKED" if blocked else "PASS",
    }
    report_bytes = canonical_bytes(report)
    report_hash = sha256(report_bytes).hexdigest()
    write_bytes_transactionally(root / "verification-report.json", report_bytes)
    session["verification"] = {
        "path": "verification-report.json", "sha256": report_hash,
        "candidate_sha256": session["candidate"]["sha256"],
        "results": report["requirements"],
    }
    session["w2"] = None
    session["package"] = None
    session["stage"] = "W2"
    write_bytes_transactionally(session_file, canonical_bytes(session))
    errors = [] if not blocked else ["verify.required_evidence_incomplete"]
    return VerificationOutcome("PASS" if not blocked else "BLOCKED", tuple(errors), report_hash)
