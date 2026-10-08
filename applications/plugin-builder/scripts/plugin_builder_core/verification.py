"""Deterministic candidate verification and requirement aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .bootstrap import plugin_authoring
from .candidate_identity import expected_tool_bindings, runtime_approval_errors, runtime_identity_fields
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


def _effective_tool_states(
    contracts: list[dict[str, Any]], results: list[dict[str, Any]],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Apply only W1-declared, behavior-preserving alternative operations."""
    by_operation = {
        tool["operation"]["id"]: tool
        for tool in contracts
        if isinstance(tool.get("operation"), dict) and isinstance(tool["operation"].get("id"), str)
    }
    states = {result["tool_id"]: result["state"] for result in results}
    activations: list[dict[str, Any]] = []
    for tool in contracts:
        if states.get(tool["id"]) == "PASS":
            continue
        fallback = tool.get("fallback")
        if not isinstance(fallback, dict) or fallback.get("policy") != "ALTERNATIVE":
            continue
        alternative = by_operation.get(fallback.get("alternative_operation_id"))
        requirements = set(tool.get("requirement_ids", []))
        if (
            alternative is None or states.get(alternative["id"]) != "PASS"
            or not requirements.issubset(set(fallback.get("preserved_requirement_ids", [])))
            or requirements & set(fallback.get("degraded_requirement_ids", []))
        ):
            continue
        states[tool["id"]] = "PASS"
        activations.append({
            "tool_id": tool["id"], "alternative_tool_id": alternative["id"],
            "operation_id": alternative["operation"]["id"],
            "preserved_requirement_ids": sorted(requirements),
        })
    return states, sorted(activations, key=lambda item: item["tool_id"])


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
                for realization in tool.get("realizations", []):
                    exposed = realization.get("exposed_capability") if isinstance(realization, dict) else None
                    if isinstance(exposed, str) and exposed not in text:
                        bindings.append(f"tool_capability_unrouted:{identifier}:{skill}:{exposed}")
    return safety, bindings


def verify_candidate(session_path: Path, *, allow_loopback: bool = False) -> VerificationOutcome:
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
    if isinstance(plan.get("capabilities"), list):
        if manifest.get("schema") != "plugin-builder-candidate-manifest-v3":
            identity_errors.append("verify.candidate_manifest_v3_required")
        identity_errors.extend(
            item.replace("build.", "verify.", 1)
            for item in runtime_approval_errors(plan, session.get("plan") or {}, session.get("w1") or {})
        )
        try:
            expected_runtime = runtime_identity_fields(plan, candidate)
        except (ValueError, OSError, KeyError, TypeError) as error:
            identity_errors.append(f"verify.runtime_identity_invalid:{error}")
        else:
            for key, value in expected_runtime.items():
                if manifest.get(key) != value:
                    identity_errors.append(f"verify.{key}_mismatch")
    if manifest.get("tool_contracts") != plan.get("tools"):
        identity_errors.append("verify.tool_contracts_mismatch")
    if manifest.get("tool_bindings") != expected_tool_bindings(plan.get("tools", [])):
        identity_errors.append("verify.tool_bindings_mismatch")
    preflight_evidence = plan.get("preflight_evidence")
    if not isinstance(preflight_evidence, dict):
        identity_errors.append("verify.preflight_evidence_missing")
    else:
        preflight_hash = sha256(canonical_bytes(preflight_evidence)).hexdigest()
        if manifest.get("preflight_evidence_sha256") != preflight_hash:
            identity_errors.append("verify.preflight_evidence_sha256_mismatch")
        artifact_quality = preflight_evidence.get("artifact_quality")
        if not isinstance(artifact_quality, dict) or manifest.get("file_roles") != artifact_quality.get("file_roles"):
            identity_errors.append("verify.artifact_quality_mismatch")
        manifest_profile = preflight_evidence.get("manifest_profile")
        if manifest.get("manifest_profile") != manifest_profile:
            identity_errors.append("verify.manifest_profile_mismatch")
        if manifest.get("manifest_profile_sha256") != sha256(canonical_bytes(manifest_profile)).hexdigest():
            identity_errors.append("verify.manifest_profile_sha256_mismatch")
    if identity_errors:
        session["verification"] = session["w2"] = session["package"] = None
        write_bytes_transactionally(session_file, canonical_bytes(session))
        return VerificationOutcome("BLOCKED", tuple(sorted(set(identity_errors))))
    checks = _structural_checks(candidate, plan, manifest)
    tool_results = [
        verify_application_tool(tool, candidate, allow_loopback=allow_loopback)
        for tool in plan.get("tools", []) if isinstance(tool, dict)
    ]
    effective_tool_states, fallback_activations = _effective_tool_states(
        [tool for tool in plan.get("tools", []) if isinstance(tool, dict)], tool_results,
    )
    if isinstance(plan.get("capabilities"), list):
        contracts = {tool["id"]: tool for tool in plan.get("tools", []) if isinstance(tool, dict)}
        for result in tool_results:
            contract = contracts[result["tool_id"]]
            operation = result.get("operation_execution")
            if not isinstance(operation, dict):
                operation = {
                    "state": result["state"],
                    "evidence_sha256": result.get("stdout_sha256") if result["state"] == "PASS" else None,
                }
                result["operation_execution"] = operation
            observed = {
                item["target_runtime"]: item for item in result.get("realizations", [])
                if isinstance(item, dict) and isinstance(item.get("target_runtime"), str)
            }
            result["realizations"] = [
                {
                    "target_runtime": realization["target_runtime"],
                    "adapter_id": realization["adapter_id"],
                    "operation_id": realization["operation_id"],
                    "exposed_capability": realization["exposed_capability"],
                    "evidence_policy": realization["evidence_policy"],
                    "state": "NOT VERIFIED",
                    **observed.get(realization["target_runtime"], {}),
                }
                for realization in contract.get("realizations", [])
            ]
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
            effective_tool_states[item["tool_id"]]
            for item in tool_results
            if identifier in item["requirement_ids"]
            and (item["required"] or item["state"] == "FAIL")
        ]
        state = "FAIL" if "FAIL" in states else "NOT VERIFIED" if "NOT VERIFIED" in states else "PASS" if states else "NOT VERIFIED"
        requirements.append({"id": identifier, "required": True, "state": state})
    blocked_tool = any(
        item["required"] and effective_tool_states[item["tool_id"]] != "PASS" and (item.get("fallback") or {}).get("policy") == "BLOCK"
        for item in tool_results
    )
    blocked_runtime = any(
        realization.get("evidence_policy") == "REQUIRED_BEFORE_W2" and realization.get("state") != "RUNTIME VERIFIED"
        for result in tool_results if result["required"]
        for realization in result.get("realizations", [])
    )
    blocked = blocked_tool or blocked_runtime or any(item["required"] and item["state"] != "PASS" for item in requirements) or any(item["required"] and item["state"] != "PASS" for item in checks)
    structural_pass = all(item["state"] == "PASS" for item in checks if item["required"])
    if not tool_results:
        tool_state = "NOT APPLICABLE"
    elif all(item["state"] == "PASS" and item["executed"] for item in tool_results):
        tool_state = "STATICALLY VERIFIED"
    else:
        tool_state = "NOT VERIFIED"
    evidence_states = {
        "structural_validation": "STATICALLY VERIFIED" if structural_pass else "NOT VERIFIED",
        "installation": "NOT VERIFIED",
        "tool_execution": tool_state,
        "reference_consultation": "NOT VERIFIED",
        "conversation": "NOT VERIFIED",
    }


    report = {
        "schema": "plugin-builder-verification-report-v3" if isinstance(plan.get("capabilities"), list) else "plugin-builder-verification-report-v2",
        "candidate_sha256": session["candidate"]["sha256"],
        "plan_sha256": session["candidate"]["plan_sha256"],
        "preflight_evidence": preflight_evidence,
        "checks": sorted(checks, key=lambda item: item["id"]),
        "tools": sorted(tool_results, key=lambda item: item["tool_id"]),
        "fallback_activations": fallback_activations,
        "requirements": sorted(requirements, key=lambda item: item["id"]),
        "evidence_states": evidence_states,
        "status": "BLOCKED" if blocked else "PASS",
    }
    if isinstance(plan.get("capabilities"), list):
        report["capabilities_sha256"] = plan["capabilities_sha256"]
        report["realizations_sha256"] = plan["realizations_sha256"]
        report["adapter_registry_sha256"] = plan["adapter_registry_sha256"]
        report["runtime_realizations"] = [
            {"tool_id": result["tool_id"], **realization}
            for result in tool_results for realization in result["realizations"]
        ]
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
