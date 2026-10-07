"""Materialize the exact plugin tree proposed by an implementation plan."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from typing import Any

from .bootstrap import plugin_authoring
from .artifact_quality import audit_artifact_quality
from .runtime_commands import resolve_direct_argv


@dataclass(frozen=True)
class ProposedTreePreflight:
    diagnostics: tuple[str, ...]
    evidence: dict[str, Any]


def agent_yaml(skill: dict[str, Any]) -> bytes:
    """Return deterministic Codex discovery metadata for one declared Skill."""

    display = " ".join(part.capitalize() for part in str(skill["name"]).split("-"))
    description = str(skill["description"]).replace('"', "'")
    return (
        "interface:\n"
        f'  display_name: "{display}"\n'
        f'  short_description: "{description}"\n'
    ).encode("utf-8")


def materialize_proposed_tree(
    proposal: dict[str, Any],
    workspace_root: Path,
    destination: Path,
) -> None:
    """Materialize a create proposal without Builder control manifests."""

    operation = proposal.get("operation")
    if operation not in {"create", "update"}:
        raise plugin_authoring.PluginAuthoringError("proposal_operation_unsupported")
    recipes = proposal.get("files")
    if not isinstance(recipes, list):
        raise plugin_authoring.PluginAuthoringError("materialize_recipe_invalid")
    root = Path(workspace_root)
    output = Path(destination)
    if operation == "create":
        plugin_authoring.materialize_files(recipes, root, output)
    else:
        baseline = root / "baseline"
        if not baseline.is_dir():
            raise plugin_authoring.PluginAuthoringError("proposal_baseline_missing")
        expected = proposal.get("expected_members")
        if not isinstance(expected, list):
            raise plugin_authoring.PluginAuthoringError("proposal_expected_members_invalid")
        expected_paths = set(expected)
        controls = {"PLUGIN-BUILDER-MANIFEST.json", "PLUGIN-BUILDER-CHANGES.json"}
        baseline_paths = {member.path for member in plugin_authoring.tree_manifest(baseline)}
        removals = sorted(baseline_paths - expected_paths - controls)
        plugin_authoring.overlay_files(baseline, recipes, root, output, remove=removals)
        for control in controls:
            (output / control).unlink(missing_ok=True)
    skills = proposal.get("skills")
    for skill in skills if isinstance(skills, list) else []:
        if not isinstance(skill, dict):
            continue
        agent = output / "skills" / str(skill["name"]) / "agents" / "openai.yaml"
        agent.parent.mkdir(parents=True, exist_ok=True)
        agent.write_bytes(agent_yaml(skill))
    plugin_authoring.materialize_manifest_pair(output)


def _issue_diagnostic(issue: Any) -> str:
    fields = [f"plan.preflight.{issue.code}"]
    if issue.path:
        fields.append(issue.path)
    if issue.detail:
        fields.append(issue.detail)
    return ":".join(fields)


def preflight_proposed_tree(
    proposal: dict[str, Any],
    workspace_root: Path,
) -> ProposedTreePreflight:
    """Materialize and validate a proposal without changing persistent state."""

    root = Path(workspace_root)
    diagnostics: list[str] = []
    tree_hash: str | None = None
    quality_evidence: dict[str, Any] | None = None
    command_evidence: list[dict[str, Any]] = []
    try:
        with tempfile.TemporaryDirectory(dir=root, prefix=".plan-preflight-") as name:
            plugin = Path(name) / "plugin"
            try:
                materialize_proposed_tree(proposal, root, plugin)
            except plugin_authoring.PluginAuthoringError as error:
                diagnostic = f"plan.preflight.{error.code}"
                if error.detail:
                    diagnostic = f"{diagnostic}:{error.detail}"
                diagnostics.append(diagnostic)
            if plugin.is_dir():
                diagnostics.extend(
                    _issue_diagnostic(issue)
                    for issue in plugin_authoring.validate_plugin_tree(plugin)
                )
                baseline_manifest: dict[str, Any] | None = None
                baseline_manifest_path = root / "baseline" / "PLUGIN-BUILDER-MANIFEST.json"
                if proposal.get("operation") == "update" and baseline_manifest_path.is_file():
                    try:
                        loaded = json.loads(baseline_manifest_path.read_text(encoding="utf-8"))
                        baseline_manifest = loaded if isinstance(loaded, dict) else None
                    except (OSError, UnicodeError, json.JSONDecodeError):
                        diagnostics.append("plan.preflight.baseline_manifest_invalid")
                quality = audit_artifact_quality(
                    proposal,
                    plugin,
                    baseline_manifest=baseline_manifest,
                )
                diagnostics.extend(f"plan.preflight.{item}" for item in quality.diagnostics)
                quality_evidence = quality.as_dict()
                for tool in proposal.get("tools", []):
                    if not isinstance(tool, dict) or tool.get("implementation_kind") not in {"BUNDLED_LOCAL", "FRAMEWORK_ADAPTER"}:
                        continue
                    for purpose in ("execution", "verification"):
                        command = tool.get(purpose)
                        argv = command.get("argv") if isinstance(command, dict) else None
                        if not isinstance(argv, list):
                            continue
                        resolution = resolve_direct_argv(argv, plugin)
                        command_evidence.append({
                            "tool_id": tool.get("id"),
                            "purpose": purpose,
                            "declared_argv": list(resolution.declared_argv),
                            "observed_argv": list(resolution.observed_argv) if resolution.observed_argv is not None else None,
                            "adapter": resolution.adapter,
                            "diagnostic": resolution.diagnostic,
                            "resolution_scope": "BUILD_HOST",
                            "evidence_state": "STATICALLY VERIFIED" if resolution.diagnostic is None else "NOT VERIFIED",
                        })
                        if resolution.diagnostic is not None:
                            diagnostics.append(
                                f"plan.preflight.command_unresolved:{tool.get('id', '')}:{purpose}:{resolution.diagnostic}"
                            )
                tree_hash = plugin_authoring.tree_sha256(plugin)
    except OSError:
        diagnostics.append("plan.preflight.local_io_failure")
    return ProposedTreePreflight(
        tuple(sorted(set(diagnostics))),
        {
            "schema": "plugin-builder-preflight-v1",
            "materialized_tree_sha256": tree_hash,
            "artifact_quality": quality_evidence,
            "command_resolution": sorted(
                command_evidence,
                key=lambda item: (str(item["tool_id"]), str(item["purpose"])),
            ),
        },
    )


__all__ = [
    "ProposedTreePreflight",
    "agent_yaml",
    "materialize_proposed_tree",
    "preflight_proposed_tree",
]
