"""Materialize the exact plugin tree proposed by an implementation plan."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .bootstrap import plugin_authoring


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

    if proposal.get("operation") != "create":
        raise plugin_authoring.PluginAuthoringError("proposal_operation_unsupported")
    recipes = proposal.get("files")
    if not isinstance(recipes, list):
        raise plugin_authoring.PluginAuthoringError("materialize_recipe_invalid")
    plugin_authoring.materialize_files(recipes, Path(workspace_root), Path(destination))
    skills = proposal.get("skills")
    for skill in skills if isinstance(skills, list) else []:
        if not isinstance(skill, dict):
            continue
        agent = Path(destination) / "skills" / str(skill["name"]) / "agents" / "openai.yaml"
        agent.parent.mkdir(parents=True, exist_ok=True)
        agent.write_bytes(agent_yaml(skill))
    plugin_authoring.materialize_manifest_pair(Path(destination))


__all__ = ["agent_yaml", "materialize_proposed_tree"]
