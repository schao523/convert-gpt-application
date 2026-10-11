"""Validate explicit delegation of skill-owned professional references."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re

from .validation import ValidationIssue


_PROFILE_KEYS = {
    "schema",
    "skill",
    "major_intents",
    "required",
    "conditional",
    "optional",
    "prohibited_substitutions",
    "fallback",
    "delegated_references",
}
_DELEGATION_KEYS = {"reference_id", "owner_skill", "access_mode", "local_copy"}
_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_REFERENCE_ID = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")
_MARKDOWN_LINK = re.compile(
    r"!?\[[^\]]*\]\(\s*(?:<(?P<angle>[^>]+)>|(?P<plain>[^\s)]+))"
)


def _issue(code: str, path: str = "", detail: str = "") -> ValidationIssue:
    return ValidationIssue(code, path, detail)


def _sorted_unique(issues: list[ValidationIssue]) -> tuple[ValidationIssue, ...]:
    return tuple(
        sorted(
            set(issues),
            key=lambda item: (item.path.casefold(), item.path, item.code, item.detail),
        )
    )


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _load_mapping(path: Path) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _safe_relative(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.as_posix()


def _index_bindings(skill: Path) -> tuple[tuple[str, str], ...]:
    payload = _load_mapping(skill / "assets" / "knowledge-index.json")
    if payload is None or not isinstance(payload.get("assets"), list):
        return ()
    bindings: list[tuple[str, str]] = []
    for item in payload["assets"]:
        if not isinstance(item, dict):
            continue
        reference_id = item.get("id")
        relative = _safe_relative(item.get("file"))
        if isinstance(reference_id, str) and reference_id and relative is not None:
            bindings.append((reference_id, relative))
    return tuple(bindings)


def _matches_reference_id(index_id: str, reference_id: str) -> bool:
    """Match an exact ID or one legacy filename-qualified ID."""

    return index_id == reference_id or index_id.startswith(reference_id + "_")


def _matching_index_bindings(
    bindings: tuple[tuple[str, str], ...], reference_id: str
) -> tuple[str, ...]:
    return tuple(
        relative
        for index_id, relative in sorted(bindings)
        if _matches_reference_id(index_id, reference_id)
    )


def _local_links(skill: Path) -> set[str]:
    try:
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return set()
    return {
        PurePosixPath(target).as_posix()
        for match in _MARKDOWN_LINK.finditer(text)
        if (target := (match.group("angle") or match.group("plain")))
        and _safe_relative(target) is not None
    }


def _handoff_prose_issues(
    skill: Path,
    root: Path,
    owner_names: set[str],
) -> list[ValidationIssue]:
    relative = _relative(skill / "SKILL.md", root)
    try:
        text = (skill / "SKILL.md").read_text(encoding="utf-8").casefold()
    except (OSError, UnicodeError):
        return [_issue("delegated_reference_handoff_missing", relative)]
    issues: list[ValidationIssue] = []
    if "handoff" not in text or any(owner.casefold() not in text for owner in owner_names):
        issues.append(_issue("delegated_reference_handoff_missing", relative))
    if "- triggers:" not in text:
        issues.append(_issue("delegated_reference_trigger_missing", relative))
    if "- input:" not in text:
        issues.append(_issue("delegated_reference_input_missing", relative))
    if "returns to the response owner" not in text:
        issues.append(_issue("delegated_reference_return_missing", relative))
    if not all(
        token in text
        for token in (
            "- fallback:",
            "unavailable",
            "disclose the limitation",
            "do not claim reference-grounded output",
        )
    ):
        issues.append(_issue("delegated_reference_fallback_missing", relative))
    return issues


def validate_delegated_references(root: Path) -> tuple[ValidationIssue, ...]:
    """Validate `skill-reference-profile-v2` HANDOFF reference closure."""

    plugin_root = Path(root)
    skills_root = plugin_root / "skills"
    if not skills_root.is_dir():
        return ()
    skills = {
        path.name: path
        for path in skills_root.iterdir()
        if path.is_dir()
    }
    issues: list[ValidationIssue] = []
    for skill_name, skill in sorted(skills.items()):
        profile_path = skill / "assets" / "reference-profile.json"
        profile = _load_mapping(profile_path)
        if profile is None or profile.get("schema") != "skill-reference-profile-v2":
            continue
        relative_profile = _relative(profile_path, plugin_root)
        for unknown in sorted(set(profile) - _PROFILE_KEYS):
            issues.append(
                _issue("delegated_reference_profile_unknown_key", relative_profile, unknown)
            )
        missing = sorted(_PROFILE_KEYS - set(profile))
        if missing:
            issues.append(
                _issue("delegated_reference_profile_missing_key", relative_profile, missing[0])
            )
        if profile.get("skill") != skill_name:
            issues.append(
                _issue("delegated_reference_profile_skill_mismatch", relative_profile)
            )
        records = profile.get("delegated_references")
        if not isinstance(records, list) or not records:
            issues.append(_issue("delegated_reference_records_invalid", relative_profile))
            continue
        seen: set[str] = set()
        owners: set[str] = set()
        non_owner_index = _index_bindings(skill)
        non_owner_links = _local_links(skill)
        for position, record in enumerate(records):
            detail = f"delegated_references[{position}]"
            if not isinstance(record, dict) or set(record) != _DELEGATION_KEYS:
                issues.append(_issue("delegated_reference_record_invalid", relative_profile, detail))
                continue
            reference_id = record.get("reference_id")
            owner_name = record.get("owner_skill")
            if not isinstance(reference_id, str) or _REFERENCE_ID.fullmatch(reference_id) is None:
                issues.append(_issue("delegated_reference_id_invalid", relative_profile, detail))
                continue
            if reference_id in seen:
                issues.append(_issue("delegated_reference_duplicate", relative_profile, reference_id))
            seen.add(reference_id)
            if not isinstance(owner_name, str) or _NAME.fullmatch(owner_name) is None:
                issues.append(_issue("delegated_reference_owner_invalid", relative_profile, reference_id))
                continue
            owners.add(owner_name)
            owner = skills.get(owner_name)
            if owner is None:
                issues.append(_issue("delegated_reference_owner_missing", relative_profile, owner_name))
                continue
            if record.get("access_mode") != "HANDOFF":
                issues.append(_issue("delegated_reference_access_mode_invalid", relative_profile, reference_id))
            if record.get("local_copy") is not False:
                issues.append(_issue("delegated_reference_local_copy_forbidden", relative_profile, reference_id))
            if _matching_index_bindings(non_owner_index, reference_id):
                issues.append(_issue("delegated_reference_non_owner_indexed", relative_profile, reference_id))

            owner_index = _index_bindings(owner)
            owner_matches = _matching_index_bindings(owner_index, reference_id)
            if not owner_matches:
                issues.append(_issue("delegated_reference_owner_index_missing", relative_profile, reference_id))
                continue
            if len(owner_matches) != 1:
                issues.append(_issue("delegated_reference_owner_index_ambiguous", relative_profile, reference_id))
                continue
            owner_relative = owner_matches[0]
            owner_asset = owner / "assets" / Path(*PurePosixPath(owner_relative).parts)
            if not owner_asset.is_file():
                issues.append(_issue("delegated_reference_owner_asset_missing", relative_profile, reference_id))
            owner_link = f"assets/{owner_relative}"
            if owner_link not in _local_links(owner):
                issues.append(_issue("delegated_reference_owner_link_missing", relative_profile, reference_id))
            if owner_link in non_owner_links or f"assets/{owner_relative}" in non_owner_links:
                issues.append(_issue("delegated_reference_non_owner_linked", relative_profile, reference_id))
            for candidate_skill_name, candidate_skill in skills.items():
                if candidate_skill_name == owner_name:
                    continue
                duplicate = candidate_skill / "assets" / Path(*PurePosixPath(owner_relative).parts)
                if duplicate.is_file():
                    issues.append(
                        _issue(
                            "delegated_reference_asset_duplicated",
                            _relative(duplicate, plugin_root),
                            reference_id,
                        )
                    )
        issues.extend(_handoff_prose_issues(skill, plugin_root, owners))
    return _sorted_unique(issues)
