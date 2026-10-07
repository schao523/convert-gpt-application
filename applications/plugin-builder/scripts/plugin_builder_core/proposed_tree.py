"""Materialize the exact plugin tree proposed by an implementation plan."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Any

from .bootstrap import plugin_authoring


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
                tree_hash = plugin_authoring.tree_sha256(plugin)
    except OSError:
        diagnostics.append("plan.preflight.local_io_failure")
    return ProposedTreePreflight(
        tuple(sorted(set(diagnostics))),
        {
            "schema": "plugin-builder-preflight-v1",
            "materialized_tree_sha256": tree_hash,
        },
    )


__all__ = [
    "ProposedTreePreflight",
    "agent_yaml",
    "materialize_proposed_tree",
    "preflight_proposed_tree",
]
