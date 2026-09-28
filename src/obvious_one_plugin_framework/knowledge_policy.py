"""Deterministic knowledge-reference discovery for portable plugins."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


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
