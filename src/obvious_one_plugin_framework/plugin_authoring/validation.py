"""Standard-library validation for the portable plugin shape Builder emits."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import unquote, urlsplit


_PLUGIN_KEYS = {
    "apps",
    "author",
    "description",
    "homepage",
    "interface",
    "keywords",
    "license",
    "mcpServers",
    "name",
    "repository",
    "skills",
    "version",
}
_INTERFACE_KEYS = {
    "capabilities",
    "category",
    "defaultPrompt",
    "developerName",
    "displayName",
    "iconLarge",
    "iconSmall",
    "longDescription",
    "shortDescription",
}
_REQUIRED_INTERFACE_KEYS = {
    "capabilities",
    "category",
    "defaultPrompt",
    "developerName",
    "displayName",
    "longDescription",
    "shortDescription",
}
_SKILL_KEYS = {"allowed-tools", "description", "license", "metadata", "name"}
_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(\s*(?:<(?P<angle>[^>]+)>|(?P<plain>[^\s)]+))")
_UNFINISHED = re.compile(r"(?i)(?:\bTODO\b|\bTBD\b|\bFIXME\b|<[^>]*(?:TODO|TBD|FIXME)[^>]*>)")
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


@dataclass(frozen=True, order=True)
class ValidationIssue:
    code: str
    path: str = ""
    detail: str = ""


def _issue(code: str, path: str = "", detail: str = "") -> ValidationIssue:
    return ValidationIssue(code, path, detail)


def _sorted_unique(issues: list[ValidationIssue]) -> tuple[ValidationIssue, ...]:
    return tuple(sorted(set(issues), key=lambda item: (item.path.casefold(), item.path, item.code, item.detail)))


def _read_text(path: Path, relative: str, issues: list[ValidationIssue]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        issues.append(_issue("file_unreadable", relative))
        return None


def _parse_frontmatter(text: str, relative: str) -> tuple[dict[str, str], list[ValidationIssue]]:
    issues: list[ValidationIssue] = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, [_issue("skill_frontmatter_missing", relative)]
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        return {}, [_issue("skill_frontmatter_invalid", relative, "closing delimiter missing")]
    result: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1].isspace() or ":" not in line:
            issues.append(_issue("skill_frontmatter_invalid", relative, "only scalar key-value fields are supported"))
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if not key or not value or key in result:
            issues.append(_issue("skill_frontmatter_invalid", relative, key))
            continue
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        result[key] = value
    return result, issues


def _safe_relative_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value or _WINDOWS_DRIVE.match(value):
        return None
    plain = value[2:] if value.startswith("./") else value
    path = PurePosixPath(plain)
    if not plain or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.as_posix()


def _skill_directories(root: Path) -> tuple[Path, ...]:
    skills = root / "skills"
    if not skills.is_dir():
        return ()
    return tuple(sorted((item for item in skills.iterdir() if item.is_dir()), key=lambda item: item.name))


def validate_skill_tree(root: Path) -> tuple[ValidationIssue, ...]:
    plugin_root = Path(root)
    issues: list[ValidationIssue] = []
    skills_root = plugin_root / "skills"
    if not skills_root.is_dir():
        return (_issue("skills_directory_missing", "skills"),)
    for skill in _skill_directories(plugin_root):
        skill_relative = skill.relative_to(plugin_root).as_posix()
        if len(skill.name) > 64 or _NAME.fullmatch(skill.name) is None:
            issues.append(_issue("skill_directory_name_invalid", skill_relative))
        skill_file = skill / "SKILL.md"
        relative = skill_file.relative_to(plugin_root).as_posix()
        if not skill_file.is_file():
            issues.append(_issue("skill_file_missing", relative))
            continue
        text = _read_text(skill_file, relative, issues)
        if text is None:
            continue
        fields, parse_issues = _parse_frontmatter(text, relative)
        issues.extend(parse_issues)
        for unknown in sorted(set(fields) - _SKILL_KEYS):
            issues.append(_issue("skill_frontmatter_unknown_key", relative, unknown))
        name = fields.get("name", "")
        if len(name) > 64 or _NAME.fullmatch(name) is None:
            issues.append(_issue("skill_frontmatter_name_invalid", relative))
        elif name != skill.name:
            issues.append(_issue("skill_name_mismatch", relative, name))
        description = fields.get("description", "")
        if not description or len(description) > 1024 or "<" in description or ">" in description:
            issues.append(_issue("skill_description_invalid", relative))
        if _UNFINISHED.search(text):
            issues.append(_issue("unfinished_scaffold_marker", relative))
    if not _skill_directories(plugin_root):
        issues.append(_issue("skill_missing", "skills"))
    return _sorted_unique(issues)


def _validate_manifest(root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    path = root / ".codex-plugin" / "plugin.json"
    relative = ".codex-plugin/plugin.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [_issue("plugin_manifest_missing", relative)]
    except (OSError, UnicodeError, json.JSONDecodeError):
        return [_issue("plugin_manifest_invalid", relative)]
    if not isinstance(payload, dict):
        return [_issue("plugin_manifest_invalid", relative)]
    for unknown in sorted(set(payload) - _PLUGIN_KEYS):
        issues.append(_issue("plugin_manifest_unknown_key", relative, unknown))
    for required in ("name", "version", "description", "author", "skills", "interface"):
        if required not in payload:
            issues.append(_issue("plugin_manifest_required_key_missing", relative, required))
    name = payload.get("name")
    if not isinstance(name, str) or len(name) > 64 or _NAME.fullmatch(name) is None:
        issues.append(_issue("plugin_name_invalid", relative))
    version = payload.get("version")
    if not isinstance(version, str) or _SEMVER.fullmatch(version) is None:
        issues.append(_issue("plugin_version_invalid", relative))
    description = payload.get("description")
    if not isinstance(description, str) or not description.strip():
        issues.append(_issue("plugin_description_invalid", relative))
    author = payload.get("author")
    if not (
        isinstance(author, dict)
        and set(author) == {"name"}
        and isinstance(author.get("name"), str)
        and author["name"].strip()
    ):
        issues.append(_issue("plugin_author_invalid", relative))
    if payload.get("skills") != "./skills/":
        issues.append(_issue("plugin_skills_path_invalid", relative))
    interface = payload.get("interface")
    if not isinstance(interface, dict):
        issues.append(_issue("plugin_interface_invalid", relative))
        return issues
    for unknown in sorted(set(interface) - _INTERFACE_KEYS):
        issues.append(_issue("plugin_interface_unknown_key", relative, unknown))
    for required in sorted(_REQUIRED_INTERFACE_KEYS):
        value = interface.get(required)
        if required == "capabilities":
            if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
                issues.append(_issue("plugin_interface_invalid", relative, required))
        elif not isinstance(value, str) or not value.strip():
            issues.append(_issue("plugin_interface_invalid", relative, required))
    for key in ("iconSmall", "iconLarge"):
        if key not in interface:
            continue
        safe = _safe_relative_path(interface[key])
        if safe is None or not (root / Path(*PurePosixPath(safe).parts)).is_file():
            issues.append(_issue("plugin_asset_path_invalid", relative, key))
    if _UNFINISHED.search(json.dumps(payload, ensure_ascii=False)):
        issues.append(_issue("unfinished_scaffold_marker", relative))
    return issues


def _markdown_targets(text: str) -> tuple[str, ...]:
    return tuple(match.group("angle") or match.group("plain") for match in _MARKDOWN_LINK.finditer(text))


def _direct_local_links(skill: Path, root: Path, issues: list[ValidationIssue]) -> set[str]:
    skill_file = skill / "SKILL.md"
    relative = skill_file.relative_to(root).as_posix()
    text = _read_text(skill_file, relative, issues)
    if text is None:
        return set()
    links: set[str] = set()
    for target in _markdown_targets(text):
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        decoded = unquote(parsed.path)
        safe = _safe_relative_path(decoded)
        if safe is None:
            issues.append(_issue("reference_path_invalid", relative, decoded))
            continue
        candidate = skill / Path(*PurePosixPath(safe).parts)
        try:
            candidate.resolve(strict=False).relative_to(skill.resolve(strict=True))
        except (OSError, ValueError):
            issues.append(_issue("reference_path_invalid", relative, decoded))
            continue
        if not candidate.is_file():
            issues.append(_issue("reference_link_missing", relative, safe))
        links.add(PurePosixPath(safe).as_posix())
    return links


def _general_index_issues(index: Path, skill: Path, root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    relative = index.relative_to(root).as_posix()
    try:
        payload = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return [_issue("general_knowledge_index_invalid", relative)]
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "files"}:
        return [_issue("general_knowledge_index_invalid", relative)]
    files = payload.get("files")
    if payload.get("schema_version") != 1 or not isinstance(files, list) or not files:
        return [_issue("general_knowledge_index_invalid", relative)]
    indexed: set[str] = set()
    for position, item in enumerate(files):
        if not isinstance(item, dict) or set(item) != {"path", "purpose", "topics"}:
            issues.append(_issue("general_knowledge_index_invalid", relative, f"files[{position}]"))
            continue
        safe = _safe_relative_path(item.get("path"))
        if safe is None:
            issues.append(_issue("general_knowledge_index_invalid", relative, f"files[{position}].path"))
            continue
        indexed.add(safe)
        if not (index.parent / Path(*PurePosixPath(safe).parts)).is_file():
            issues.append(_issue("general_reference_missing", relative, safe))
        if not isinstance(item.get("purpose"), str) or not item["purpose"].strip():
            issues.append(_issue("general_knowledge_index_invalid", relative, f"files[{position}].purpose"))
        if not isinstance(item.get("topics"), list) or not item["topics"]:
            issues.append(_issue("general_knowledge_index_invalid", relative, f"files[{position}].topics"))
    actual = {
        path.relative_to(index.parent).as_posix()
        for path in index.parent.rglob("*")
        if path.is_file() and path != index
    }
    for path in sorted(actual - indexed):
        issues.append(_issue("general_reference_unindexed", (index.parent / path).relative_to(root).as_posix()))
    return issues


def validate_reference_closure(root: Path) -> tuple[ValidationIssue, ...]:
    plugin_root = Path(root)
    issues: list[ValidationIssue] = []
    if (plugin_root / "knowledge").exists():
        issues.append(_issue("plugin_root_knowledge_directory_forbidden", "knowledge"))
    indexes = sorted((plugin_root / "skills").glob("*/references/knowledge-index.json"))
    if len(indexes) > 1:
        issues.append(_issue("multiple_general_knowledge_indexes", "skills"))
    consultation_skill = indexes[0].parent.parent if len(indexes) == 1 else None
    for skill in _skill_directories(plugin_root):
        direct_links = _direct_local_links(skill, plugin_root, issues)
        references = skill / "references"
        if not references.is_dir():
            continue
        if skill == consultation_skill:
            if "references/knowledge-index.json" not in direct_links:
                issues.append(_issue("general_knowledge_index_unlinked", indexes[0].relative_to(plugin_root).as_posix()))
            issues.extend(_general_index_issues(indexes[0], skill, plugin_root))
            continue
        for reference in sorted(path for path in references.rglob("*") if path.is_file()):
            relative_to_skill = reference.relative_to(skill).as_posix()
            if relative_to_skill not in direct_links:
                issues.append(_issue("professional_reference_unlinked", reference.relative_to(plugin_root).as_posix()))
    return _sorted_unique(issues)


def validate_plugin_tree(root: Path) -> tuple[ValidationIssue, ...]:
    plugin_root = Path(root)
    if not plugin_root.is_dir():
        return (_issue("plugin_root_missing"),)
    issues = _validate_manifest(plugin_root)
    issues.extend(validate_skill_tree(plugin_root))
    issues.extend(validate_reference_closure(plugin_root))
    return _sorted_unique(issues)
