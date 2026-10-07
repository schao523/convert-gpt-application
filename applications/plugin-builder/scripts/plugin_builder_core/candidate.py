"""Transactional candidate construction from a W1-approved canonical plan."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile

from .bootstrap import plugin_authoring
from .implementation_plan import canonical_bytes, write_bytes_transactionally
from .proposed_tree import materialize_proposed_tree


@dataclass(frozen=True)
class CandidateOutcome:
    status: str
    errors: tuple[str, ...]
    candidate_sha256: str | None = None
    manifest_sha256: str | None = None


def _load(path: Path, code: str) -> tuple[dict | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, code
    return (value, None) if isinstance(value, dict) else (None, code)


def _replace_candidate(stage: Path, destination: Path, temporary: Path) -> None:
    backup = temporary / "previous"
    moved = False
    try:
        if destination.exists():
            os.replace(destination, backup)
            moved = True
        os.replace(stage, destination)
    except OSError:
        if moved and backup.exists() and not destination.exists():
            os.replace(backup, destination)
        raise


def build_candidate(session_path: Path) -> CandidateOutcome:
    session_file = Path(session_path)
    session, error = _load(session_file, "build.session_invalid")
    if error is not None or session is None:
        return CandidateOutcome("FAIL", (error or "build.session_invalid",))
    if session.get("schema_version") != 2 or session.get("operation") not in {"create", "update"}:
        return CandidateOutcome("FAIL", ("build.session_required",))
    if session.get("stage") == "E2":
        return CandidateOutcome("BLOCKED", ("build.session_cancelled",))
    if session.get("stage") == "H1":
        return CandidateOutcome("BLOCKED", ("build.session_paused",))
    if session.get("operation") == "update":
        from .update_candidate import build_update_candidate

        return build_update_candidate(session_file)
    plan_identity = session.get("plan")
    w1 = session.get("w1")
    if not isinstance(plan_identity, dict) or not isinstance(w1, dict) or w1.get("approved") is not True:
        return CandidateOutcome("BLOCKED", ("build.w1_required",))
    root = session_file.parent
    plan_path = root / str(plan_identity.get("path", ""))
    try:
        plan_bytes = plan_path.read_bytes()
        plan = json.loads(plan_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return CandidateOutcome("FAIL", ("build.plan_unreadable",))
    if not isinstance(plan, dict):
        return CandidateOutcome("FAIL", ("build.plan_invalid",))
    plan_hash = sha256(plan_bytes).hexdigest()
    tools = plan.get("tools")
    tools_hash = sha256(canonical_bytes(tools)).hexdigest() if isinstance(tools, list) else ""
    binding_errors: list[str] = []
    if plan_hash != plan_identity.get("sha256") or plan_hash != w1.get("plan_sha256"):
        binding_errors.append("build.plan_sha256_mismatch")
    if tools_hash != plan_identity.get("tools_sha256") or tools_hash != w1.get("tools_sha256"):
        binding_errors.append("build.tools_sha256_mismatch")
    if binding_errors:
        return CandidateOutcome("BLOCKED", tuple(sorted(binding_errors)))

    diagnostics: list[str] = []
    blockers: list[str] = []
    tool_contracts = []
    recipes = plan.get("files") if isinstance(plan.get("files"), list) else []
    recipes_by_path = {item.get("path"): item for item in recipes if isinstance(item, dict)}
    for payload in tools if isinstance(tools, list) else []:
        validated = plugin_authoring.validate_application_tool_contract(payload)
        diagnostics.extend(validated.errors)
        blockers.extend(validated.blockers)
        if validated.implementation_kind == "RUNTIME_NATIVE" and validated.required:
            fallback = payload.get("fallback") if isinstance(payload, dict) else None
            if not isinstance(fallback, dict) or fallback.get("policy") == "BLOCK":
                blockers.append(f"tool.{validated.id}.runtime_capability_unavailable")
        if isinstance(payload, dict):
            for skill_name in payload.get("skill_bindings", []):
                skill_recipe = recipes_by_path.get(f"skills/{skill_name}/SKILL.md")
                text = skill_recipe.get("inline_text") if isinstance(skill_recipe, dict) else None
                if not isinstance(text, str) or payload.get("id") not in text:
                    diagnostics.append(f"tool.{payload.get('id', '')}.skill_route_missing:{skill_name}")
            if payload.get("implementation_kind") == "FRAMEWORK_ADAPTER":
                adapter = payload.get("adapter")
                if isinstance(adapter, dict) and set(adapter.get("portable_files", [])) != set(payload.get("files", [])):
                    diagnostics.append(f"tool.{payload.get('id', '')}.adapter_files_mismatch")
            tool_contracts.append(payload)
    if diagnostics:
        return CandidateOutcome("FAIL", tuple(sorted(set(diagnostics))))
    if blockers:
        return CandidateOutcome("BLOCKED", tuple(sorted(set(blockers))))

    destination = root / "candidate"
    try:
        with tempfile.TemporaryDirectory(dir=root, prefix=".candidate-build-") as name:
            temporary = Path(name)
            stage = temporary / "candidate"
            materialize_proposed_tree(plan, root, stage)
            pair_issues = plugin_authoring.validate_manifest_pair(stage)
            if pair_issues:
                return CandidateOutcome(
                    "FAIL",
                    tuple(f"candidate.{item.code}:{item.path}" for item in pair_issues),
                )
            members = plugin_authoring.tree_manifest(stage)
            actual_without_manifest = {member.path for member in members}
            expected = set(plan.get("expected_members", []))
            if actual_without_manifest != expected - {"PLUGIN-BUILDER-MANIFEST.json"}:
                return CandidateOutcome("FAIL", ("build.expected_members_mismatch",))
            bindings = []
            for tool in sorted(tool_contracts, key=lambda item: item["id"]):
                bindings.append({
                    "contract_sha256": sha256(canonical_bytes(tool)).hexdigest(),
                    "dependencies": tool["dependencies"],
                    "files": tool["files"],
                    "implementation_kind": tool["implementation_kind"],
                    "permissions": tool["permissions"],
                    "requirements": tool["requirement_ids"],
                    "runtime_targets": tool["runtime_targets"],
                    "skills": tool["skill_bindings"],
                    "tool_id": tool["id"],
                })
            manifest = {
                "schema": "plugin-builder-candidate-manifest-v1",
                "plan_sha256": plan_hash,
                "tools_sha256": tools_hash,
                "content_tree_sha256": plugin_authoring.tree_sha256(stage),
                "expected_members": sorted(expected),
                "members": [asdict(member) for member in members],
                "tool_bindings": bindings,
                "tool_contracts": sorted(tool_contracts, key=lambda item: item["id"]),
            }
            manifest_bytes = canonical_bytes(manifest)
            (stage / "PLUGIN-BUILDER-MANIFEST.json").write_bytes(manifest_bytes)
            if {member.path for member in plugin_authoring.tree_manifest(stage)} != expected:
                return CandidateOutcome("FAIL", ("build.expected_members_mismatch",))
            validation = plugin_authoring.validate_plugin_tree(stage)
            if validation:
                return CandidateOutcome("FAIL", tuple(f"candidate.{item.code}:{item.path}" for item in validation))
            candidate_hash = plugin_authoring.tree_sha256(stage)
            manifest_hash = sha256(manifest_bytes).hexdigest()
            _replace_candidate(stage, destination, temporary)
    except plugin_authoring.PluginAuthoringError as authoring_error:
        return CandidateOutcome("FAIL", (f"build.{authoring_error.code}",))
    except OSError:
        return CandidateOutcome("FAIL", ("build.local_io_failure",))

    session["candidate"] = {
        "path": "candidate",
        "sha256": candidate_hash,
        "plan_sha256": plan_hash,
        "manifest_sha256": manifest_hash,
    }
    session["verification"] = None
    session["w2"] = None
    session["package"] = None
    session["stage"] = "S4"
    write_bytes_transactionally(session_file, canonical_bytes(session))
    return CandidateOutcome("PASS", (), candidate_hash, manifest_hash)
