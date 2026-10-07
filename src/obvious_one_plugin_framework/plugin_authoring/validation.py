"""Standard-library validation for the portable plugin shape Builder emits."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import unquote, urlsplit

from .manifests import PORTABLE_PLUGIN_SCHEMA, manifest_pair_mismatches


_PORTABLE_PLUGIN_KEYS = {
    "$schema",
    "author",
    "brandColor",
    "brandColorDark",
    "composerIcon",
    "composerIconDark",
    "description",
    "extensions",
    "homepage",
    "keywords",
    "license",
    "logo",
    "logoDark",
    "name",
    "repository",
    "version",
}
_PORTABLE_FORBIDDEN_KEYS = {"apps", "interface", "mcpServers", "skills"}
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
_PATH_TOKEN = re.compile(
    r"(?:[A-Za-z]:[\\/][^\s`\"'<>]+|(?:\.\.?[\\/])[^\s`\"'<>]+|"
    r"(?:[A-Za-z0-9_.-]+[\\/])+[A-Za-z0-9_.-]+\.(?:md|json|ya?ml|py|txt))"
)


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


def _load_manifest(path: Path, relative: str, missing: str, invalid: str) -> tuple[dict[str, object] | None, list[ValidationIssue]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [_issue(missing, relative)]
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, [_issue(invalid, relative)]
    if not isinstance(payload, dict):
        return None, [_issue(invalid, relative)]
    return payload, []


def validate_portable_manifest(root: Path) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    plugin_root = Path(root)
    relative = "plugin.json"
    payload, load_issues = _load_manifest(
        plugin_root / relative,
        relative,
        "portable_manifest_missing",
        "portable_manifest_invalid",
    )
    if payload is None:
        return tuple(load_issues)
    for forbidden in sorted(set(payload) & _PORTABLE_FORBIDDEN_KEYS):
        issues.append(_issue("portable_manifest_forbidden_key", relative, forbidden))
    for unknown in sorted(set(payload) - _PORTABLE_PLUGIN_KEYS - _PORTABLE_FORBIDDEN_KEYS):
        issues.append(_issue("portable_manifest_unknown_key", relative, unknown))
    if payload.get("$schema") != PORTABLE_PLUGIN_SCHEMA:
        issues.append(_issue("portable_manifest_schema_invalid", relative))
    for required in ("name", "version", "description", "author", "extensions"):
        if required not in payload:
            issues.append(_issue("portable_manifest_required_key_missing", relative, required))
    name = payload.get("name")
    if not isinstance(name, str) or len(name) > 64 or _NAME.fullmatch(name) is None:
        issues.append(_issue("portable_name_invalid", relative))
    version = payload.get("version")
    if not isinstance(version, str) or _SEMVER.fullmatch(version) is None:
        issues.append(_issue("portable_version_invalid", relative))
    description = payload.get("description")
    if not isinstance(description, str) or not description.strip():
        issues.append(_issue("portable_description_invalid", relative))
    author = payload.get("author")
    if not (
        isinstance(author, dict)
        and set(author) == {"name"}
        and isinstance(author.get("name"), str)
        and author["name"].strip()
    ):
        issues.append(_issue("portable_author_invalid", relative))
    extensions = payload.get("extensions")
    if not isinstance(extensions, dict) or not isinstance(extensions.get("com.openai"), dict):
        issues.append(_issue("portable_openai_extension_missing", relative))
        return _sorted_unique(issues)
    interface = extensions["com.openai"].get("interface")
    if not isinstance(interface, dict):
        issues.append(_issue("portable_interface_invalid", relative))
        return _sorted_unique(issues)
    for unknown in sorted(set(interface) - _INTERFACE_KEYS):
        issues.append(_issue("portable_interface_unknown_key", relative, unknown))
    for required in sorted(_REQUIRED_INTERFACE_KEYS):
        value = interface.get(required)
        if required == "capabilities":
            if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
                issues.append(_issue("portable_interface_invalid", relative, required))
        elif required == "defaultPrompt":
            valid_prompt = isinstance(value, str) and bool(value.strip())
            valid_prompts = (
                isinstance(value, list)
                and 1 <= len(value) <= 3
                and all(isinstance(item, str) and item.strip() for item in value)
            )
            if not valid_prompt and not valid_prompts:
                issues.append(_issue("portable_interface_invalid", relative, required))
        elif not isinstance(value, str) or not value.strip():
            issues.append(_issue("portable_interface_invalid", relative, required))
    short = interface.get("shortDescription")
    if isinstance(short, str) and len(short) > 30:
        issues.append(_issue("portable_short_description_too_long", relative))
    for key in ("iconSmall", "iconLarge"):
        if key not in interface:
            continue
        safe = _safe_relative_path(interface[key])
        if safe is None or not (plugin_root / Path(*PurePosixPath(safe).parts)).is_file():
            issues.append(_issue("portable_asset_path_invalid", relative, key))
    for key in ("logo", "logoDark", "composerIcon", "composerIconDark"):
        if key not in payload:
            continue
        safe = _safe_relative_path(payload[key])
        if safe is None or not (plugin_root / Path(*PurePosixPath(safe).parts)).is_file():
            issues.append(_issue("portable_asset_path_invalid", relative, key))
    if _UNFINISHED.search(json.dumps(payload, ensure_ascii=False)):
        issues.append(_issue("unfinished_scaffold_marker", relative))
    return _sorted_unique(issues)


def validate_manifest_pair(root: Path) -> tuple[ValidationIssue, ...]:
    plugin_root = Path(root)
    issues = list(validate_portable_manifest(plugin_root))
    overlay_path = plugin_root / ".codex-plugin" / "plugin.json"
    if not overlay_path.exists():
        return _sorted_unique(issues)
    portable, portable_issues = _load_manifest(
        plugin_root / "plugin.json",
        "plugin.json",
        "portable_manifest_missing",
        "portable_manifest_invalid",
    )
    overlay, overlay_issues = _load_manifest(
        overlay_path,
        ".codex-plugin/plugin.json",
        "compatibility_overlay_missing",
        "compatibility_overlay_invalid",
    )
    issues.extend(portable_issues)
    issues.extend(overlay_issues)
    if portable is not None and overlay is not None:
        for mismatch in manifest_pair_mismatches(portable, overlay):
            issues.append(_issue("manifest_pair_mismatch", ".codex-plugin/plugin.json", mismatch))
    return _sorted_unique(issues)


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


def _path_tokens(value: object) -> set[str]:
    if isinstance(value, str):
        return {match.group(0).rstrip(".,;:)") for match in _PATH_TOKEN.finditer(value)}
    if isinstance(value, list):
        return set().union(*(_path_tokens(item) for item in value), set())
    if isinstance(value, dict):
        return set().union(*(_path_tokens(item) for item in value.values()), set())
    return set()


def validate_path_bindings(root: Path) -> tuple[ValidationIssue, ...]:
    """Validate path-like bindings without interpreting ordinary prose as paths."""

    plugin_root = Path(root)
    issues: list[ValidationIssue] = []
    for path in sorted(
        item for item in plugin_root.rglob("*")
        if item.is_file() and item.suffix.casefold() in {".md", ".json", ".yaml", ".yml"}
    ):
        relative = path.relative_to(plugin_root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        payload: object = text
        if path.suffix.casefold() == ".json":
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                payload = text
        tokens = _path_tokens(payload)
        if path.name == "SKILL.md":
            tokens.update(_markdown_targets(text))
        for token in sorted(tokens):
            if "://" in token:
                continue
            safe = _safe_relative_path(token)
            if safe is None or "\\" in token or _WINDOWS_DRIVE.match(token):
                issues.append(_issue("path_binding_invalid", relative, token))
                continue
            if path.name == "SKILL.md":
                target = path.parent.joinpath(*PurePosixPath(safe).parts)
                try:
                    target.resolve(strict=False).relative_to(path.parent.resolve(strict=True))
                except (OSError, ValueError):
                    issues.append(_issue("path_binding_invalid", relative, token))
                else:
                    if not target.is_file():
                        issues.append(_issue("path_binding_missing", relative, safe))
        if isinstance(payload, dict) and payload.get("schema") == "plugin-builder-application-tool-v1":
            for token in payload.get("files", []):
                safe = _safe_relative_path(token)
                if safe is None or not plugin_root.joinpath(*PurePosixPath(safe).parts).is_file():
                    issues.append(_issue("path_binding_invalid", relative, str(token)))
    return _sorted_unique(issues)


def validate_plugin_tree(root: Path) -> tuple[ValidationIssue, ...]:
    plugin_root = Path(root)
    if not plugin_root.is_dir():
        return (_issue("plugin_root_missing"),)
    issues = list(validate_manifest_pair(plugin_root))
    issues.extend(validate_skill_tree(plugin_root))
    issues.extend(validate_reference_closure(plugin_root))
    issues.extend(validate_path_bindings(plugin_root))
    return _sorted_unique(issues)
