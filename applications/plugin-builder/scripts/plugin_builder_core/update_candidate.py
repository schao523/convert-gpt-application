"""Transactional update overlay with exact preservation and change evidence."""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import tempfile

from .bootstrap import plugin_authoring
from .candidate import CandidateOutcome, _agent_yaml, _load, _replace_candidate
from .implementation_plan import canonical_bytes, write_bytes_transactionally


def _hashes(root: Path, *, controls: bool = False) -> dict[str, str]:
    result = {item.path: item.sha256 for item in plugin_authoring.tree_manifest(root)}
    if not controls:
        result.pop("PLUGIN-BUILDER-MANIFEST.json", None)
        result.pop("PLUGIN-BUILDER-CHANGES.json", None)
    return result


def _decisions(root: Path, baseline_sha256: str) -> tuple[dict[str, str], str | None]:
    path = root / "update-decisions.json"
    if not path.is_file():
        return {}, None
    payload, error = _load(path, "build.update_decisions_invalid")
    if error is not None or payload is None:
        return {}, error or "build.update_decisions_invalid"
    if payload.get("schema") != "plugin-builder-update-decisions-v1" or payload.get("baseline_sha256") != baseline_sha256:
        return {}, "build.update_decisions_stale"
    result: dict[str, str] = {}
    for item in payload.get("members", []):
        if (
            isinstance(item, dict) and isinstance(item.get("member"), str)
            and item.get("decision") in {"keep", "replace", "remove"}
            and isinstance(item.get("evidence"), str) and item["evidence"]
        ):
            result[item["member"]] = item["decision"]
    return result, None


def build_update_candidate(session_path: Path) -> CandidateOutcome:
    session_file = Path(session_path)
    session, error = _load(session_file, "build.session_invalid")
    if error is not None or session is None:
        return CandidateOutcome("FAIL", (error or "build.session_invalid",))
    plan_identity = session.get("plan")
    w1 = session.get("w1")
    if not isinstance(plan_identity, dict) or not isinstance(w1, dict) or w1.get("approved") is not True:
        return CandidateOutcome("BLOCKED", ("build.w1_required",))
    root = session_file.parent
    plan_path = root / str(plan_identity.get("path", ""))
    plan, error = _load(plan_path, "build.plan_unreadable")
    if error is not None or plan is None or plan.get("operation") != "update":
        return CandidateOutcome("FAIL", (error or "build.plan_invalid",))
    plan_bytes = plan_path.read_bytes()
    plan_hash = sha256(plan_bytes).hexdigest()
    tools = plan.get("tools") if isinstance(plan.get("tools"), list) else []
    tools_hash = sha256(canonical_bytes(tools)).hexdigest()
    binding_errors = []
    if plan_hash != plan_identity.get("sha256") or plan_hash != w1.get("plan_sha256"):
        binding_errors.append("build.plan_sha256_mismatch")
    if tools_hash != plan_identity.get("tools_sha256") or tools_hash != w1.get("tools_sha256"):
        binding_errors.append("build.tools_sha256_mismatch")
    if binding_errors:
        return CandidateOutcome("BLOCKED", tuple(sorted(binding_errors)))

    baseline_identity = session.get("baseline")
    if not isinstance(baseline_identity, dict):
        return CandidateOutcome("BLOCKED", ("build.baseline_required",))
    baseline = root / str(baseline_identity.get("path", ""))
    if not baseline.is_dir() or plugin_authoring.tree_sha256(baseline) != baseline_identity.get("manifest_sha256"):
        return CandidateOutcome("BLOCKED", ("build.baseline_stale",))
    previous, error = _load(baseline / "PLUGIN-BUILDER-MANIFEST.json", "build.baseline_manifest_invalid")
    if error is not None or previous is None:
        return CandidateOutcome("BLOCKED", (error or "build.baseline_manifest_invalid",))
    try:
        baseline_manifest_path = baseline / "plugin.json"
        if baseline_manifest_path.is_file():
            baseline_plugin = json.loads(baseline_manifest_path.read_text(encoding="utf-8"))
        else:
            baseline_plugin = plugin_authoring.portable_manifest_from_legacy(
                json.loads((baseline / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
            )
    except (OSError, UnicodeError, json.JSONDecodeError):
        return CandidateOutcome("FAIL", ("build.baseline_plugin_invalid",))
    except plugin_authoring.PluginAuthoringError:
        return CandidateOutcome("FAIL", ("build.baseline_plugin_invalid",))
    planned_plugin = plan.get("plugin") or {}
    if any(baseline_plugin.get(key) != planned_plugin.get(key) for key in ("name", "version")):
        return CandidateOutcome("BLOCKED", ("build.plugin_identity_change_forbidden",))

    recipes = plan.get("files") if isinstance(plan.get("files"), list) else []
    recipe_paths = {item.get("path") for item in recipes if isinstance(item, dict)}
    expected = set(plan.get("expected_members", []))
    before_all = _hashes(baseline, controls=True)
    managed = {
        item.get("path") for item in previous.get("members", [])
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    } | {"PLUGIN-BUILDER-MANIFEST.json", "PLUGIN-BUILDER-CHANGES.json"}
    decisions, decision_error = _decisions(root, str(baseline_identity.get("sha256", "")))
    if decision_error:
        return CandidateOutcome("BLOCKED", (decision_error,))
    blockers: list[str] = []
    for path in sorted(set(before_all) - managed):
        required = "replace" if path in recipe_paths else "keep" if path in expected else "remove"
        if decisions.get(path) != required:
            blockers.append(f"build.update_decision_required:{path}:{required}")
    removals = sorted(set(before_all) - expected - {"PLUGIN-BUILDER-MANIFEST.json", "PLUGIN-BUILDER-CHANGES.json"})
    for path in removals:
        if decisions.get(path) != "remove":
            blockers.append(f"build.remove_decision_required:{path}")
    if blockers:
        return CandidateOutcome("BLOCKED", tuple(sorted(set(blockers))))

    diagnostics: list[str] = []
    tool_contracts: list[dict] = []
    for payload in tools:
        validated = plugin_authoring.validate_application_tool_contract(payload)
        diagnostics.extend(validated.errors)
        diagnostics.extend(validated.blockers)
        if isinstance(payload, dict):
            tool_contracts.append(payload)
    if diagnostics:
        return CandidateOutcome("FAIL", tuple(sorted(set(diagnostics))))

    destination = root / "candidate"
    try:
        with tempfile.TemporaryDirectory(dir=root, prefix=".candidate-update-") as name:
            temporary = Path(name)
            stage = temporary / "candidate"
            plugin_authoring.overlay_files(baseline, recipes, root, stage, remove=removals)
            (stage / "PLUGIN-BUILDER-MANIFEST.json").unlink(missing_ok=True)
            (stage / "PLUGIN-BUILDER-CHANGES.json").unlink(missing_ok=True)
            for skill in plan.get("skills", []):
                if isinstance(skill, dict):
                    target = stage / "skills" / str(skill["name"]) / "agents" / "openai.yaml"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(_agent_yaml(skill))
            plugin_authoring.materialize_manifest_pair(stage)
            pair_issues = plugin_authoring.validate_manifest_pair(stage)
            if pair_issues:
                return CandidateOutcome(
                    "FAIL",
                    tuple(f"candidate.{item.code}:{item.path}" for item in pair_issues),
                )
            bindings = []
            tool_files: set[str] = set()
            for tool in sorted(tool_contracts, key=lambda item: item["id"]):
                tool_files.update(tool["files"])
                bindings.append({
                    "contract_sha256": sha256(canonical_bytes(tool)).hexdigest(),
                    "dependencies": tool["dependencies"], "files": tool["files"],
                    "implementation_kind": tool["implementation_kind"], "permissions": tool["permissions"],
                    "requirements": tool["requirement_ids"], "runtime_targets": tool["runtime_targets"],
                    "skills": tool["skill_bindings"], "tool_id": tool["id"],
                })
            before = _hashes(baseline)
            after = _hashes(stage)
            added = sorted(set(after) - set(before))
            removed = sorted(set(before) - set(after))
            changed = sorted(path for path in set(before) & set(after) if before[path] != after[path])
            preserved = sorted(path for path in set(before) & set(after) if before[path] == after[path])
            change_document = {
                "schema": "plugin-builder-change-manifest-v1",
                "baseline_tree_sha256": baseline_identity["manifest_sha256"],
                "plan_sha256": plan_hash,
                "added": added, "changed": changed, "removed": removed, "preserved": preserved,
                "application_tool_artifacts": sorted(tool_files & (set(added) | set(changed) | set(removed))),
                "application_tool_contracts": [
                    {"contract_sha256": item["contract_sha256"], "tool_id": item["tool_id"]}
                    for item in bindings
                ],
            }
            (stage / "PLUGIN-BUILDER-CHANGES.json").write_bytes(canonical_bytes(change_document))
            members = plugin_authoring.tree_manifest(stage)
            if {item.path for item in members} != expected - {"PLUGIN-BUILDER-MANIFEST.json"}:
                return CandidateOutcome("FAIL", ("build.expected_members_mismatch",))
            manifest = {
                "schema": "plugin-builder-candidate-manifest-v1", "operation": "update",
                "plan_sha256": plan_hash, "tools_sha256": tools_hash,
                "content_tree_sha256": plugin_authoring.tree_sha256(stage),
                "expected_members": sorted(expected), "members": [asdict(item) for item in members],
                "tool_bindings": bindings, "tool_contracts": sorted(tool_contracts, key=lambda item: item["id"]),
            }
            manifest_bytes = canonical_bytes(manifest)
            (stage / "PLUGIN-BUILDER-MANIFEST.json").write_bytes(manifest_bytes)
            if {item.path for item in plugin_authoring.tree_manifest(stage)} != expected:
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

    session["candidate"] = {"path": "candidate", "sha256": candidate_hash, "plan_sha256": plan_hash, "manifest_sha256": manifest_hash}
    session["verification"] = None
    session["w2"] = None
    session["package"] = None
    session["stage"] = "S4"
    write_bytes_transactionally(session_file, canonical_bytes(session))
    return CandidateOutcome("PASS", (), candidate_hash, manifest_hash)
