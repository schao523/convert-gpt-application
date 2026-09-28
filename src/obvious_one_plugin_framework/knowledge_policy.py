"""Deterministic knowledge-reference discovery for portable plugins."""

from __future__ import annotations

import json
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlsplit


_INDEX_NAME = "knowledge-index.json"
_ROOT_KEYS = {"schema_version", "files"}
_FILE_KEYS = {"path", "purpose", "topics"}
_TOPIC_KEYS = {
    "name",
    "chapters",
    "sections",
    "keywords",
    "page_ranges",
}
_PAGE_RANGE_KEYS = {"start", "end"}
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")
_INLINE_LINK = re.compile(
    r"!?\[[^\]]*\]\(\s*(?:<(?P<angle>[^>]+)>|(?P<plain>[^\s)]+))"
)
_REFERENCE_DEFINITION = re.compile(
    r"^\s*\[(?P<label>[^\]]+)\]:\s*(?:<(?P<angle>[^>]+)>|(?P<plain>\S+))",
    re.MULTILINE,
)
_REFERENCE_USE = re.compile(r"(?<!!)\[[^\]]+\]\[(?P<label>[^\]]+)\]")


class KnowledgePolicyError(ValueError):
    """A stable, path-safe knowledge-policy validation failure."""

    def __init__(
        self,
        code: str,
        detail: str,
        paths: tuple[str, ...] = (),
    ) -> None:
        self.code = code
        self.detail = detail
        self.paths = tuple(sorted(paths, key=lambda item: (item.casefold(), item)))
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class KnowledgePageRange:
    start: int
    end: int


@dataclass(frozen=True)
class KnowledgeTopic:
    name: str
    chapters: tuple[str, ...]
    sections: tuple[str, ...]
    keywords: tuple[str, ...]
    page_ranges: tuple[KnowledgePageRange, ...]


@dataclass(frozen=True)
class GeneralKnowledgeFile:
    path: str
    purpose: str
    topics: tuple[KnowledgeTopic, ...]


@dataclass(frozen=True)
class ProfessionalKnowledgeFile:
    skill_name: str
    path: str


@dataclass(frozen=True)
class KnowledgePolicy:
    professional_files: tuple[ProfessionalKnowledgeFile, ...]
    general_files: tuple[GeneralKnowledgeFile, ...]
    consultation_skill: str | None


@dataclass(frozen=True)
class KnowledgePolicyEvidence:
    professional_reference_count: int
    general_reference_count: int
    consultation_skill: str | None
    package_structure: str
    deterministic_discovery: str
    coverage_traceability: str
    behavior: str
    codex_execution: str
    openclaw_execution: str


def _relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _error(
    code: str,
    detail: str,
    index_relative: str,
) -> KnowledgePolicyError:
    return KnowledgePolicyError(code, detail, (index_relative,))


def _require_exact_keys(
    value: object,
    expected: set[str],
    *,
    index_relative: str,
    location: str,
    code: str = "general_knowledge_index_invalid",
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _error(code, f"{location} must be an object", index_relative)
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        parts = []
        if missing:
            parts.append(f"missing keys {missing}")
        if unknown:
            parts.append(f"unknown keys {unknown}")
        raise _error(code, f"{location} has {' and '.join(parts)}", index_relative)
    return value


def _nonempty_text(
    value: object,
    *,
    field: str,
    index_relative: str,
    code: str = "general_knowledge_topic_incomplete",
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _error(code, f"{field} must be nonempty text", index_relative)
    return value.strip()


def _text_array(
    value: object,
    *,
    field: str,
    index_relative: str,
    require_item: bool,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise _error(
            "general_knowledge_topic_incomplete",
            f"{field} must be an array",
            index_relative,
        )
    result = tuple(
        _nonempty_text(item, field=field, index_relative=index_relative)
        for item in value
    )
    if require_item and not result:
        raise _error(
            "general_knowledge_topic_incomplete",
            f"{field} must contain at least one item",
            index_relative,
        )
    return result


def _safe_general_path(value: object, index_relative: str) -> str:
    if not isinstance(value, str) or not value:
        raise _error(
            "general_knowledge_index_invalid",
            "file path must be nonempty text",
            index_relative,
        )
    if "\\" in value or _WINDOWS_DRIVE.match(value):
        raise _error(
            "general_knowledge_index_invalid",
            f"file path is not a portable POSIX relative path: {value!r}",
            index_relative,
        )
    candidate = PurePosixPath(value)
    if (
        candidate.is_absolute()
        or value in {".", ".."}
        or any(part in {"", ".", ".."} for part in candidate.parts)
        or candidate.as_posix() != value
    ):
        raise _error(
            "general_knowledge_index_invalid",
            f"file path is unsafe or noncanonical: {value!r}",
            index_relative,
        )
    return candidate.as_posix()


def _parse_page_range(
    value: object,
    *,
    index_relative: str,
    location: str,
) -> KnowledgePageRange:
    item = _require_exact_keys(
        value,
        _PAGE_RANGE_KEYS,
        index_relative=index_relative,
        location=location,
        code="general_knowledge_page_range_invalid",
    )
    start = item["start"]
    end = item["end"]
    if (
        type(start) is not int
        or type(end) is not int
        or start <= 0
        or end <= 0
        or start > end
    ):
        raise _error(
            "general_knowledge_page_range_invalid",
            f"{location} requires positive integer bounds with start <= end",
            index_relative,
        )
    return KnowledgePageRange(start=start, end=end)


def _parse_topic(
    value: object,
    *,
    index_relative: str,
    location: str,
) -> KnowledgeTopic:
    item = _require_exact_keys(
        value,
        _TOPIC_KEYS,
        index_relative=index_relative,
        location=location,
        code="general_knowledge_topic_incomplete",
    )
    ranges_value = item["page_ranges"]
    if not isinstance(ranges_value, list):
        raise _error(
            "general_knowledge_topic_incomplete",
            f"{location}.page_ranges must be an array",
            index_relative,
        )
    return KnowledgeTopic(
        name=_nonempty_text(
            item["name"],
            field=f"{location}.name",
            index_relative=index_relative,
        ),
        chapters=_text_array(
            item["chapters"],
            field=f"{location}.chapters",
            index_relative=index_relative,
            require_item=False,
        ),
        sections=_text_array(
            item["sections"],
            field=f"{location}.sections",
            index_relative=index_relative,
            require_item=False,
        ),
        keywords=_text_array(
            item["keywords"],
            field=f"{location}.keywords",
            index_relative=index_relative,
            require_item=True,
        ),
        page_ranges=tuple(
            _parse_page_range(
                page_range,
                index_relative=index_relative,
                location=f"{location}.page_ranges[{position}]",
            )
            for position, page_range in enumerate(ranges_value)
        ),
    )


def _parse_general_file(
    value: object,
    *,
    index_relative: str,
    position: int,
) -> GeneralKnowledgeFile:
    location = f"files[{position}]"
    item = _require_exact_keys(
        value,
        _FILE_KEYS,
        index_relative=index_relative,
        location=location,
    )
    topics_value = item["topics"]
    if not isinstance(topics_value, list) or not topics_value:
        raise _error(
            "general_knowledge_topic_incomplete",
            f"{location}.topics must contain at least one topic",
            index_relative,
        )
    return GeneralKnowledgeFile(
        path=_safe_general_path(item["path"], index_relative),
        purpose=_nonempty_text(
            item["purpose"],
            field=f"{location}.purpose",
            index_relative=index_relative,
        ),
        topics=tuple(
            _parse_topic(
                topic,
                index_relative=index_relative,
                location=f"{location}.topics[{topic_position}]",
            )
            for topic_position, topic in enumerate(topics_value)
        ),
    )


def _load_general_files(index: Path, plugin_root: Path) -> tuple[GeneralKnowledgeFile, ...]:
    index_relative = _relative_path(plugin_root, index)
    try:
        payload = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise _error(
            "general_knowledge_index_invalid",
            f"topic guide is not readable UTF-8 JSON: {type(error).__name__}",
            index_relative,
        ) from error
    root = _require_exact_keys(
        payload,
        _ROOT_KEYS,
        index_relative=index_relative,
        location="topic guide",
    )
    if type(root["schema_version"]) is not int or root["schema_version"] != 1:
        raise _error(
            "general_knowledge_index_invalid",
            "schema_version must be the integer 1",
            index_relative,
        )
    files_value = root["files"]
    if not isinstance(files_value, list) or not files_value:
        raise _error(
            "general_knowledge_index_invalid",
            "files must contain at least one entry",
            index_relative,
        )
    files = tuple(
        _parse_general_file(
            value,
            index_relative=index_relative,
            position=position,
        )
        for position, value in enumerate(files_value)
    )
    seen: dict[str, str] = {}
    for item in files:
        folded = item.path.casefold()
        if folded in seen:
            raise _error(
                "general_knowledge_index_invalid",
                f"general knowledge paths collide: {seen[folded]!r} and {item.path!r}",
                index_relative,
            )
        seen[folded] = item.path
    return tuple(sorted(files, key=lambda item: (item.path.casefold(), item.path)))


def discover_knowledge_policy(plugin_root: Path) -> KnowledgePolicy:
    """Discover professional references and the optional general topic guide."""

    root = Path(plugin_root)
    skills_root = root / "skills"
    if not skills_root.is_dir():
        return KnowledgePolicy((), (), None)

    indexes = tuple(
        sorted(
            skills_root.glob(f"*/references/{_INDEX_NAME}"),
            key=lambda path: (_relative_path(root, path).casefold(), _relative_path(root, path)),
        )
    )
    if len(indexes) > 1:
        raise KnowledgePolicyError(
            "multiple_general_knowledge_indexes",
            "a plugin may contain at most one general knowledge topic guide",
            tuple(_relative_path(root, path) for path in indexes),
        )

    consultation_skill = indexes[0].parent.parent.name if indexes else None
    general_files = _load_general_files(indexes[0], root) if indexes else ()
    professional: list[ProfessionalKnowledgeFile] = []
    for skill in sorted(
        (path for path in skills_root.iterdir() if path.is_dir()),
        key=lambda path: (path.name.casefold(), path.name),
    ):
        if skill.name == consultation_skill:
            continue
        references = skill / "references"
        if not references.is_dir():
            continue
        for reference in sorted(
            (path for path in references.rglob("*") if path.is_file()),
            key=lambda path: (_relative_path(root, path).casefold(), _relative_path(root, path)),
        ):
            professional.append(
                ProfessionalKnowledgeFile(
                    skill_name=skill.name,
                    path=_relative_path(root, reference),
                )
            )

    return KnowledgePolicy(
        professional_files=tuple(professional),
        general_files=general_files,
        consultation_skill=consultation_skill,
    )


def _is_within(path: Path, boundary: Path) -> bool:
    try:
        path.relative_to(boundary)
    except ValueError:
        return False
    return True


def _is_link_or_reparse(path: Path) -> bool:
    """Return whether *path* aliases another filesystem location."""

    try:
        metadata = path.lstat()
    except OSError:
        return False
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    file_attributes = getattr(metadata, "st_file_attributes", 0)
    return path.is_symlink() or bool(file_attributes & reparse_flag)


def _validate_discovery_roots(root: Path) -> None:
    if _is_link_or_reparse(root):
        raise KnowledgePolicyError(
            "knowledge_plugin_root_invalid",
            "plugin root must not be a linked or reparse path",
        )
    skills_root = root / "skills"
    if not skills_root.exists():
        return
    if _is_link_or_reparse(skills_root):
        raise KnowledgePolicyError(
            "knowledge_plugin_root_invalid",
            "skills root must not be a linked or reparse path",
            ("skills",),
        )
    try:
        skills = tuple(path for path in skills_root.iterdir() if path.is_dir())
    except OSError as error:
        raise KnowledgePolicyError(
            "knowledge_plugin_root_invalid",
            "skills root is unreadable",
            ("skills",),
        ) from error
    linked = tuple(
        sorted(
            (_relative_path(root, path) for path in skills if _is_link_or_reparse(path)),
            key=lambda item: (item.casefold(), item),
        )
    )
    if linked:
        raise KnowledgePolicyError(
            "knowledge_plugin_root_invalid",
            "skill directories must not be linked or reparse paths",
            linked,
        )


def _ensure_regular_confined_file(
    path: Path,
    boundary: Path,
    *,
    code: str,
    display_path: str,
) -> None:
    try:
        relative = path.relative_to(boundary)
    except ValueError as error:
        raise KnowledgePolicyError(
            code,
            f"path escapes its owning skill: {display_path}",
            (display_path,),
        ) from error
    current = boundary
    for part in relative.parts:
        current = current / part
        if _is_link_or_reparse(current):
            raise KnowledgePolicyError(
                code,
                f"linked paths are not knowledge files: {display_path}",
                (display_path,),
            )
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
        resolved_boundary = boundary.resolve(strict=True)
    except OSError as error:
        raise KnowledgePolicyError(
            code,
            f"knowledge path is missing or unreadable: {display_path}",
            (display_path,),
        ) from error
    if not stat.S_ISREG(metadata.st_mode) or not _is_within(resolved, resolved_boundary):
        raise KnowledgePolicyError(
            code,
            f"knowledge path is not a confined regular file: {display_path}",
            (display_path,),
        )


def _markdown_targets(text: str) -> tuple[str, ...]:
    targets = [
        match.group("angle") or match.group("plain")
        for match in _INLINE_LINK.finditer(text)
    ]
    definitions = {
        match.group("label").strip().casefold(): match.group("angle")
        or match.group("plain")
        for match in _REFERENCE_DEFINITION.finditer(text)
    }
    for match in _REFERENCE_USE.finditer(text):
        target = definitions.get(match.group("label").strip().casefold())
        if target is not None:
            targets.append(target)
    return tuple(targets)


def _resolve_local_markdown_target(
    target: str,
    *,
    markdown_path: Path,
    skill_root: Path,
) -> Path | None:
    decoded_target = unquote(target)
    display = f"{markdown_path.name} -> {decoded_target}"
    if (
        "\\" in decoded_target
        or _WINDOWS_DRIVE.match(decoded_target)
        or decoded_target.startswith("/")
    ):
        raise KnowledgePolicyError(
            "professional_reference_missing",
            f"local Markdown link is not portable: {display}",
            (display,),
        )
    parsed = urlsplit(target)
    if parsed.scheme.casefold() == "file":
        raise KnowledgePolicyError(
            "professional_reference_missing",
            f"local Markdown link uses a file URI: {display}",
            (display,),
        )
    if parsed.scheme or parsed.netloc:
        return None
    if not parsed.path:
        return None
    decoded = unquote(parsed.path)
    display = f"{markdown_path.name} -> {decoded}"
    candidate_path = Path(decoded)
    if candidate_path.is_absolute():
        raise KnowledgePolicyError(
            "professional_reference_missing",
            f"local Markdown link is absolute: {display}",
            (display,),
        )
    unresolved = markdown_path.parent / candidate_path
    try:
        lexical = Path(*PurePosixPath(decoded).parts)
        normalized = markdown_path.parent.joinpath(lexical)
        normalized.resolve(strict=False).relative_to(skill_root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise KnowledgePolicyError(
            "professional_reference_missing",
            f"local Markdown link escapes its owning skill: {display}",
            (display,),
        ) from error
    _ensure_regular_confined_file(
        unresolved,
        skill_root,
        code="professional_reference_missing",
        display_path=display,
    )
    return unresolved


def _skill_markdown_links(skill_root: Path) -> tuple[str, ...]:
    skill_file = skill_root / "SKILL.md"
    if not skill_file.is_file() or _is_link_or_reparse(skill_file):
        return ()
    direct_targets: list[str] = []
    markdown_files = tuple(
        sorted(
            (path for path in skill_root.rglob("*.md") if path.is_file()),
            key=lambda path: (
                path.relative_to(skill_root).as_posix().casefold(),
                path.relative_to(skill_root).as_posix(),
            ),
        )
    )
    for markdown in markdown_files:
        try:
            text = markdown.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            display = markdown.relative_to(skill_root).as_posix()
            raise KnowledgePolicyError(
                "professional_reference_missing",
                f"Markdown file is not readable UTF-8: {display}",
                (display,),
            ) from error
        for target in _markdown_targets(text):
            resolved = _resolve_local_markdown_target(
                target,
                markdown_path=markdown,
                skill_root=skill_root,
            )
            if resolved is not None and markdown == skill_file:
                direct_targets.append(resolved.relative_to(skill_root).as_posix())
    return tuple(sorted(set(direct_targets), key=lambda item: (item.casefold(), item)))


def _validate_professional_references(
    root: Path,
    policy: KnowledgePolicy,
) -> None:
    folded: dict[str, str] = {}
    links_by_skill: dict[str, tuple[str, ...]] = {}
    for reference in policy.professional_files:
        previous = folded.get(reference.path.casefold())
        if previous is not None:
            raise KnowledgePolicyError(
                "professional_reference_path_collision",
                f"professional reference paths collide: {previous!r} and {reference.path!r}",
                (previous, reference.path),
            )
        folded[reference.path.casefold()] = reference.path
        skill_root = root / "skills" / reference.skill_name
        _ensure_regular_confined_file(
            root / Path(*PurePosixPath(reference.path).parts),
            skill_root,
            code="professional_reference_missing",
            display_path=reference.path,
        )
        links = links_by_skill.setdefault(
            reference.skill_name,
            _skill_markdown_links(skill_root),
        )
        relative_to_skill = PurePosixPath(reference.path).relative_to(
            PurePosixPath("skills") / reference.skill_name
        ).as_posix()
        if relative_to_skill not in links:
            raise KnowledgePolicyError(
                "professional_reference_unlinked",
                f"professional reference is not directly linked from SKILL.md: {reference.path}",
                (reference.path,),
            )

    for skill in sorted(
        (root / "skills").iterdir() if (root / "skills").is_dir() else (),
        key=lambda path: (path.name.casefold(), path.name),
    ):
        if skill.is_dir() and skill.name != policy.consultation_skill:
            links_by_skill.setdefault(skill.name, _skill_markdown_links(skill))


def _validate_general_references(root: Path, policy: KnowledgePolicy) -> None:
    if policy.consultation_skill is None:
        return
    skill_root = root / "skills" / policy.consultation_skill
    references = skill_root / "references"
    index = references / _INDEX_NAME
    index_display = _relative_path(root, index)
    _ensure_regular_confined_file(
        index,
        skill_root,
        code="general_knowledge_index_invalid",
        display_path=index_display,
    )
    direct_links = _skill_markdown_links(skill_root)
    if f"references/{_INDEX_NAME}" not in direct_links:
        raise KnowledgePolicyError(
            "general_knowledge_index_invalid",
            "the consultation SKILL.md must directly link knowledge-index.json",
            (index_display,),
        )

    actual: dict[str, str] = {}
    for path in sorted(
        (candidate for candidate in references.rglob("*") if candidate.is_file()),
        key=lambda candidate: (
            candidate.relative_to(references).as_posix().casefold(),
            candidate.relative_to(references).as_posix(),
        ),
    ):
        relative = path.relative_to(references).as_posix()
        if relative == _INDEX_NAME:
            continue
        _ensure_regular_confined_file(
            path,
            references,
            code="general_knowledge_index_path_missing",
            display_path=relative,
        )
        folded = relative.casefold()
        if folded in actual:
            raise KnowledgePolicyError(
                "general_knowledge_index_invalid",
                f"general knowledge paths collide: {actual[folded]!r} and {relative!r}",
                (actual[folded], relative),
            )
        actual[folded] = relative

    indexed = {item.path.casefold(): item.path for item in policy.general_files}
    missing = tuple(
        indexed[key]
        for key in sorted(indexed)
        if key not in actual or actual[key] != indexed[key]
    )
    if missing:
        raise KnowledgePolicyError(
            "general_knowledge_index_path_missing",
            "one or more indexed general knowledge files are missing",
            missing,
        )
    unindexed = tuple(
        actual[key]
        for key in sorted(actual)
        if key not in indexed or indexed[key] != actual[key]
    )
    if unindexed:
        raise KnowledgePolicyError(
            "general_knowledge_file_unindexed",
            "one or more general knowledge files are not indexed",
            unindexed,
        )


def _knowledge_paths(policy: KnowledgePolicy) -> tuple[str, ...]:
    paths = [item.path for item in policy.professional_files]
    if policy.consultation_skill is not None:
        prefix = f"skills/{policy.consultation_skill}/references"
        paths.extend(f"{prefix}/{item.path}" for item in policy.general_files)
    return tuple(sorted(paths, key=lambda item: (item.casefold(), item)))


def _coverage_state(
    root: Path,
    policy: KnowledgePolicy,
    coverage_matrix: Path | None,
    require_coverage: bool,
) -> str:
    knowledge_paths = _knowledge_paths(policy)
    if not knowledge_paths:
        return "NOT APPLICABLE"
    if coverage_matrix is None:
        if require_coverage:
            raise KnowledgePolicyError(
                "knowledge_behavior_evidence_missing",
                "coverage matrix is required for knowledge references",
                knowledge_paths,
            )
        return "NOT VERIFIED"

    matrix = Path(coverage_matrix)
    try:
        resolved_root = root.resolve(strict=True)
        resolved_matrix = matrix.resolve(strict=True)
        resolved_matrix.relative_to(resolved_root)
        if _is_link_or_reparse(matrix) or not matrix.is_file():
            raise OSError("coverage matrix is not a regular file")
        text = matrix.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as error:
        raise KnowledgePolicyError(
            "knowledge_behavior_evidence_missing",
            "coverage matrix is missing, unreadable, or outside the plugin root",
        ) from error

    missing = tuple(
        path
        for path in knowledge_paths
        if re.search(
            rf"(?<![\w./-]){re.escape(path)}(?![\w./-])",
            text,
        )
        is None
    )
    if missing and require_coverage:
        raise KnowledgePolicyError(
            "knowledge_behavior_evidence_missing",
            "coverage matrix does not trace every knowledge file",
            missing,
        )
    return "STATICALLY VERIFIED" if not missing else "NOT VERIFIED"


def validate_knowledge_policy(
    plugin_root: Path,
    coverage_matrix: Path | None = None,
    require_coverage: bool = False,
) -> KnowledgePolicyEvidence:
    """Validate knowledge structure and report static evidence only."""

    root = Path(plugin_root)
    if not root.is_dir():
        raise KnowledgePolicyError(
            "knowledge_plugin_root_invalid",
            "plugin root must be an existing directory",
        )
    _validate_discovery_roots(root)
    forbidden = root / "knowledge"
    if forbidden.exists() or _is_link_or_reparse(forbidden):
        raise KnowledgePolicyError(
            "plugin_root_knowledge_directory_forbidden",
            "plugin-root knowledge directories are not supported",
            ("knowledge",),
        )

    policy = discover_knowledge_policy(root)
    _validate_professional_references(root, policy)
    _validate_general_references(root, policy)
    return KnowledgePolicyEvidence(
        professional_reference_count=len(policy.professional_files),
        general_reference_count=len(policy.general_files),
        consultation_skill=policy.consultation_skill,
        package_structure="STATICALLY VERIFIED",
        deterministic_discovery=(
            "STATICALLY VERIFIED" if policy.general_files else "NOT APPLICABLE"
        ),
        coverage_traceability=_coverage_state(
            root,
            policy,
            coverage_matrix,
            require_coverage,
        ),
        behavior="NOT VERIFIED",
        codex_execution="NOT VERIFIED",
        openclaw_execution="NOT VERIFIED",
    )
