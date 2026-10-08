"""Semantic artifact placement and exact-content duplicate policy."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from .bootstrap import plugin_authoring


CONTENT_ROLES = frozenset({
    "PLUGIN_MANIFEST",
    "SKILL_ENTRYPOINT",
    "PROFESSIONAL_KNOWLEDGE",
    "GENERAL_KNOWLEDGE",
    "EXECUTABLE_TOOL",
    "STATIC_ASSET",
    "GENERATED_METADATA",
    "OTHER",
})
_KNOWLEDGE_ROLES = {"PROFESSIONAL_KNOWLEDGE", "GENERAL_KNOWLEDGE"}
_CONTROLS = {"PLUGIN-BUILDER-MANIFEST.json", "PLUGIN-BUILDER-CHANGES.json"}


@dataclass(frozen=True)
class ArtifactQualityReport:
    diagnostics: tuple[str, ...]
    knowledge_ownership: tuple[dict[str, Any], ...]
    duplicate_groups: tuple[dict[str, Any], ...]
    duplicate_bytes: int
    file_roles: dict[str, str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "plugin-builder-artifact-quality-v1",
            "knowledge_ownership": [dict(item) for item in self.knowledge_ownership],
            "duplicate_groups": [dict(item) for item in self.duplicate_groups],
            "duplicate_bytes": self.duplicate_bytes,
            "file_roles": dict(sorted(self.file_roles.items())),
        }


def _skill_name(path: str) -> str | None:
    parts = path.split("/")
    return parts[1] if len(parts) >= 3 and parts[0] == "skills" else None


def audit_artifact_quality(
    proposal: dict[str, Any],
    materialized_root: Path,
    *,
    baseline_manifest: dict[str, Any] | None = None,
) -> ArtifactQualityReport:
    root = Path(materialized_root)
    diagnostics: list[str] = []
    recipes = proposal.get("files") if isinstance(proposal.get("files"), list) else []
    roles: dict[str, str] = {}
    recipe_by_path: dict[str, dict[str, Any]] = {}
    for recipe in recipes:
        if not isinstance(recipe, dict) or not isinstance(recipe.get("path"), str):
            continue
        path = recipe["path"]
        recipe_by_path[path] = recipe
        role = recipe.get("content_role")
        if role is None:
            diagnostics.append(f"artifact.content_role_missing:{path}")
            continue
        if role not in CONTENT_ROLES:
            diagnostics.append(f"artifact.content_role_invalid:{path}")
            continue
        roles[path] = role

    for skill in proposal.get("skills", []):
        if isinstance(skill, dict) and isinstance(skill.get("name"), str):
            roles.setdefault(
                f"skills/{skill['name']}/agents/openai.yaml",
                "GENERATED_METADATA",
            )
    if (root / ".codex-plugin/plugin.json").is_file():
        roles.setdefault(".codex-plugin/plugin.json", "GENERATED_METADATA")
    for generated in ("mcp.json", ".mcp.json"):
        if (root / generated).is_file():
            roles.setdefault(generated, "GENERATED_METADATA")

    baseline_roles = baseline_manifest.get("file_roles") if isinstance(baseline_manifest, dict) else None
    baseline_members = baseline_manifest.get("members", []) if isinstance(baseline_manifest, dict) else []
    baseline_paths = {
        item.get("path")
        for item in baseline_members
        if isinstance(item, dict)
        and isinstance(item.get("path"), str)
    }
    for path in sorted(item for item in baseline_paths if isinstance(item, str)):
        if path in _CONTROLS or path in roles or not (root / path).is_file():
            continue
        role = baseline_roles.get(path) if isinstance(baseline_roles, dict) else None
        roles[path] = role if role in CONTENT_ROLES else "INHERITED_UNCLASSIFIED"
    if proposal.get("operation") == "update":
        for member in plugin_authoring.tree_manifest(root):
            if member.path not in _CONTROLS:
                roles.setdefault(member.path, "INHERITED_UNCLASSIFIED")

    decisions = proposal.get("implementation_decisions")
    policy = decisions.get("knowledge_policy") if isinstance(decisions, dict) else None
    ownership = decisions.get("reference_ownership") if isinstance(decisions, dict) else None
    policy_valid = (
        isinstance(policy, dict)
        and set(policy) == {"adopt_general_knowledge", "consultation_skill"}
        and type(policy.get("adopt_general_knowledge")) is bool
        and (
            (policy["adopt_general_knowledge"] is True and isinstance(policy.get("consultation_skill"), str) and bool(policy["consultation_skill"]))
            or (policy["adopt_general_knowledge"] is False and policy.get("consultation_skill") is None)
        )
    )
    if not policy_valid:
        diagnostics.append("artifact.knowledge_policy_invalid")
    if not isinstance(ownership, dict) or any(
        not isinstance(key, str)
        or len(key) != 64
        or key != key.lower()
        or any(char not in "0123456789abcdef" for char in key)
        or not isinstance(value, str)
        or not value.strip()
        for key, value in (ownership.items() if isinstance(ownership, dict) else [])
    ):
        diagnostics.append("artifact.reference_ownership_invalid")
        ownership = {}

    requirement_owners = {
        item.get("id"): item.get("owner_skill")
        for item in proposal.get("requirements", [])
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and isinstance(item.get("owner_skill"), str)
    }
    general_indexes: list[str] = []
    for path, role in sorted(roles.items()):
        if role in _KNOWLEDGE_ROLES and "/assets/" in f"/{path}":
            diagnostics.append(f"artifact.knowledge_in_skill_assets:{path}")
        if role == "PROFESSIONAL_KNOWLEDGE":
            recipe = recipe_by_path.get(path)
            if recipe is None:
                parts = path.split("/")
                valid_inherited_path = (
                    len(parts) >= 4
                    and parts[0] == "skills"
                    and parts[2] == "references"
                )
                if not valid_inherited_path:
                    diagnostics.append(f"artifact.professional_knowledge_owner_path:{path}")
            else:
                owners = {
                    requirement_owners.get(identifier)
                    for identifier in recipe.get("requirement_ids", [])
                    if requirement_owners.get(identifier)
                }
                owner = next(iter(owners)) if len(owners) == 1 else None
                if owner is None or not path.startswith(f"skills/{owner}/references/"):
                    diagnostics.append(f"artifact.professional_knowledge_owner_path:{path}")
        if role == "GENERAL_KNOWLEDGE":
            if path.endswith("/references/knowledge-index.json"):
                general_indexes.append(path)
            consultation = policy.get("consultation_skill") if policy_valid and policy.get("adopt_general_knowledge") else None
            if consultation is None or not path.startswith(f"skills/{consultation}/references/"):
                diagnostics.append(f"artifact.general_knowledge_policy_invalid:{path}")
    if len(general_indexes) > 1:
        diagnostics.append("artifact.multiple_general_knowledge_indexes")

    groups: dict[str, list[tuple[str, int]]] = {}
    for member in plugin_authoring.tree_manifest(root):
        if member.path in _CONTROLS:
            continue
        groups.setdefault(member.sha256, []).append((member.path, member.size))
    duplicate_groups: list[dict[str, Any]] = []
    knowledge_rows: list[dict[str, Any]] = []
    duplicate_bytes = 0
    for digest, members in sorted(groups.items()):
        paths = sorted(path for path, _size in members)
        size = members[0][1]
        member_roles = {roles.get(path, "INHERITED_UNCLASSIFIED") for path in paths}
        knowledge_paths = [path for path in paths if roles.get(path) in _KNOWLEDGE_ROLES]
        if knowledge_paths:
            knowledge_rows.append({
                "sha256": digest,
                "paths": knowledge_paths,
                "rationale": ownership.get(digest) if isinstance(ownership, dict) else None,
            })
        if len(paths) < 2:
            continue
        repeated = (len(paths) - 1) * size
        duplicate_bytes += repeated
        duplicate_groups.append({
            "sha256": digest,
            "paths": paths,
            "member_count": len(paths),
            "size": size,
            "duplicate_bytes": repeated,
        })
        professional_skills = {
            _skill_name(path)
            for path in paths
            if roles.get(path) == "PROFESSIONAL_KNOWLEDGE"
        }
        requires_rationale = len({item for item in professional_skills if item}) > 1 or (
            "INHERITED_UNCLASSIFIED" in member_roles and bool(knowledge_paths)
        )
        if requires_rationale and not (
            isinstance(ownership, dict)
            and isinstance(ownership.get(digest), str)
            and ownership[digest].strip()
        ):
            diagnostics.append(f"artifact.professional_duplicate_ownership_required:{digest}")

    return ArtifactQualityReport(
        tuple(sorted(set(diagnostics))),
        tuple(sorted(knowledge_rows, key=lambda item: (item["sha256"], item["paths"]))),
        tuple(sorted(duplicate_groups, key=lambda item: (item["sha256"], item["paths"]))),
        duplicate_bytes,
        dict(sorted(roles.items())),
    )


__all__ = ["CONTENT_ROLES", "ArtifactQualityReport", "audit_artifact_quality"]
