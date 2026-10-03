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
    def owners(kind: str) -> list[str]:
        return sorted({requirement for check in plan.get("checks", []) if isinstance(check, dict) and check.get("kind") == kind for requirement in check.get("requirement_ids", [])})
    actual = {item.path for item in plugin_authoring.tree_manifest(candidate)}
    expected = set(manifest.get("expected_members", []))
    exact_state = "PASS" if actual == expected else "FAIL"
    checks = [
        _check("builtin-plugin-structure", "PLUGIN_STRUCTURE", True, owners("PLUGIN_STRUCTURE"), "PASS" if not plugin_errors else "FAIL", plugin_errors),
        _check("builtin-skill-structure", "SKILL_STRUCTURE", True, owners("SKILL_STRUCTURE"), "PASS" if not plugin_errors else "FAIL", plugin_errors),
        _check("builtin-reference-closure", "REFERENCE_CLOSURE", True, owners("REFERENCE_CLOSURE"), "PASS" if not plugin_errors else "FAIL", plugin_errors),
        _check("builtin-exact-members", "EXACT_MEMBERS", True, [], exact_state, [] if exact_state == "PASS" else ["candidate_member_mismatch"]),
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
            "builtin-update-preservation", "UPDATE_PRESERVATION", True, [],
            "PASS" if changes is not None and not failures else "FAIL", failures,
            {"preserved_members": sorted(preserved)},
        ))
    return checks


def _candidate_safety_and_bindings(candidate: Path, plan: dict[str, Any], manifest: dict[str, Any]) -> tuple[list[str], list[str]]:
    safety: list[str] = []
    bindings: list[str] = []
    members = {item.path for item in plugin_authoring.tree_manifest(candidate)}
    for path in sorted(members):
        lowered = path.casefold()
        if Path(path).name.casefold() in {".env", ".env.local", "credentials.json"}:
            safety.append(f"credential_file:{path}")
        if lowered.endswith((".pem", ".p12", ".pfx")):
            safety.append(f"credential_file:{path}")
    manifest_bindings = {item.get("tool_id"): item for item in manifest.get("tool_bindings", []) if isinstance(item, dict)}
    for tool in plan.get("tools", []):
        if not isinstance(tool, dict):
            continue
        identifier = tool.get("id")
        binding = manifest_bindings.get(identifier)
        if binding is None:
            bindings.append(f"tool_binding_missing:{identifier}")
        for path in tool.get("files", []):
            if path not in members:
                bindings.append(f"tool_file_missing:{identifier}:{path}")
        for skill in tool.get("skill_bindings", []):
            skill_path = candidate / "skills" / skill / "SKILL.md"
            try:
                text = skill_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                bindings.append(f"tool_skill_missing:{identifier}:{skill}")
            else:
                if str(identifier) not in text:
                    bindings.append(f"tool_skill_unrouted:{identifier}:{skill}")
    return safety, bindings


def verify_candidate(session_path: Path) -> VerificationOutcome:
    session_file = Path(session_path)
    session = _load(session_file)
    if session is None or session.get("schema_version") != 2 or not isinstance(session.get("candidate"), dict):
        return VerificationOutcome("FAIL", ("verify.candidate_required",))
    if session.get("stage") == "E2":
        return VerificationOutcome("BLOCKED", ("verify.session_cancelled",))
    if session.get("stage") == "H1":
        return VerificationOutcome("BLOCKED", ("verify.session_paused",))
    root = session_file.parent
    candidate = root / str(session["candidate"].get("path", ""))
    if not candidate.is_dir() or plugin_authoring.tree_sha256(candidate) != session["candidate"].get("sha256"):
        session["verification"] = None
        session["w2"] = None
        session["package"] = None
        write_bytes_transactionally(session_file, canonical_bytes(session))
        return VerificationOutcome("BLOCKED", ("verify.candidate_sha256_mismatch",))
    plan_path = root / str((session.get("plan") or {}).get("path", ""))
    try:
        plan_bytes = plan_path.read_bytes()
        plan = json.loads(plan_bytes.decode("ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        plan = None
        plan_bytes = b""
    manifest = _load(candidate / "PLUGIN-BUILDER-MANIFEST.json")
    if plan is None or manifest is None:
        return VerificationOutcome("FAIL", ("verify.inputs_invalid",))
    plan_hash = sha256(plan_bytes).hexdigest()
    tools_hash = sha256(canonical_bytes(plan.get("tools", []))).hexdigest()
    identities = [
        ((session.get("plan") or {}).get("sha256"), "verify.plan_sha256_mismatch"),
        ((session.get("w1") or {}).get("plan_sha256"), "verify.w1_plan_sha256_mismatch"),
        ((session.get("candidate") or {}).get("plan_sha256"), "verify.candidate_plan_sha256_mismatch"),
        (manifest.get("plan_sha256"), "verify.manifest_plan_sha256_mismatch"),
    ]
    identity_errors = [code for expected, code in identities if expected != plan_hash]
    if (session.get("plan") or {}).get("tools_sha256") != tools_hash or (session.get("w1") or {}).get("tools_sha256") != tools_hash or manifest.get("tools_sha256") != tools_hash:
        identity_errors.append("verify.tools_sha256_mismatch")
    if identity_errors:
        session["verification"] = session["w2"] = session["package"] = None
        write_bytes_transactionally(session_file, canonical_bytes(session))
        return VerificationOutcome("BLOCKED", tuple(sorted(set(identity_errors))))
    checks = _structural_checks(candidate, plan, manifest)
    tool_results = [verify_application_tool(tool, candidate) for tool in plan.get("tools", []) if isinstance(tool, dict)]
    safety_errors, binding_errors = _candidate_safety_and_bindings(candidate, plan, manifest)
    checks.extend([
        _check("builtin-distribution-safety", "DISTRIBUTION_SAFETY", True, [], "PASS" if not safety_errors else "FAIL", safety_errors),
        _check("builtin-tool-binding", "TOOL_BINDING", True, [], "PASS" if not binding_errors else "FAIL", binding_errors, {"binding_count": len(manifest.get("tool_bindings", []))}),
    ])

    for planned in plan.get("checks", []):
        if not isinstance(planned, dict):
            continue
        kind = planned.get("kind")
        if kind == "PYTHON_ARGV":
            result = next((item for item in tool_results if item.get("argv") == planned.get("argv", [])), None)
            if result is None:
                result = {"state": "NOT VERIFIED", "diagnostics": ["approved_tool_binding_missing"], "argv": planned.get("argv", []), "executed": False, "stdout_sha256": None, "stderr_sha256": None}
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
        states += [
            item["state"]
            for item in tool_results
            if identifier in item["requirement_ids"]
            and (item["required"] or item["state"] == "FAIL")
        ]
        state = "FAIL" if "FAIL" in states else "NOT VERIFIED" if "NOT VERIFIED" in states else "PASS" if states else "NOT VERIFIED"
        requirements.append({"id": identifier, "required": True, "state": state})
    blocked_tool = any(
        item["required"] and item["state"] != "PASS" and (item.get("fallback") or {}).get("policy") == "BLOCK"
        for item in tool_results
    )
    blocked = blocked_tool or any(item["required"] and item["state"] != "PASS" for item in requirements) or any(item["required"] and item["state"] != "PASS" for item in checks)
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
