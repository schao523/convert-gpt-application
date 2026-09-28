from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from obvious_one_plugin_framework.knowledge_policy import (
    KnowledgePolicyError,
    discover_knowledge_policy,
)


class KnowledgePolicyParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.plugin_root = Path(self.temporary.name) / "plugin"
        self.plugin_root.mkdir()

    def _skill(self, name: str) -> Path:
        skill = self.plugin_root / "skills" / name
        (skill / "references").mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
        return skill

    @staticmethod
    def _valid_index(path: str = "architecture-guide.md") -> dict[str, object]:
        return {
            "schema_version": 1,
            "files": [
                {
                    "path": path,
                    "purpose": "Background for comparing architectures.",
                    "topics": [
                        {
                            "name": "Event-driven architecture",
                            "chapters": ["Asynchronous systems"],
                            "sections": ["Delivery guarantees"],
                            "keywords": ["event-driven"],
                            "page_ranges": [{"start": 4, "end": 9}],
                        }
                    ],
                }
            ],
        }

    def _write_index(self, skill: Path, payload: object) -> Path:
        path = skill / "references" / "knowledge-index.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def _assert_error(self, code: str, action) -> KnowledgePolicyError:
        with self.assertRaises(KnowledgePolicyError) as captured:
            action()
        self.assertEqual(captured.exception.code, code)
        self.assertTrue(captured.exception.detail)
        self.assertIsInstance(captured.exception.paths, tuple)
        return captured.exception

    def test_discovers_professional_only_and_zero_knowledge_plugins(self) -> None:
        professional = self._skill("designing-systems")
        (professional / "references" / "rules.md").write_text(
            "# Rules\n",
            encoding="utf-8",
        )

        policy = discover_knowledge_policy(self.plugin_root)

        self.assertIsNone(policy.consultation_skill)
        self.assertEqual(
            [(item.skill_name, item.path) for item in policy.professional_files],
            [("designing-systems", "skills/designing-systems/references/rules.md")],
        )
        self.assertEqual(policy.general_files, ())

        empty_root = Path(self.temporary.name) / "empty-plugin"
        empty_root.mkdir()
        empty = discover_knowledge_policy(empty_root)
        self.assertEqual(empty.professional_files, ())
        self.assertEqual(empty.general_files, ())
        self.assertIsNone(empty.consultation_skill)

    def test_discovers_valid_general_knowledge_in_deterministic_order(self) -> None:
        skill = self._skill("consulting-product-knowledge")
        (skill / "references" / "architecture-guide.md").write_text(
            "# Guide\n",
            encoding="utf-8",
        )
        self._write_index(skill, self._valid_index())

        policy = discover_knowledge_policy(self.plugin_root)

        self.assertEqual(policy.consultation_skill, "consulting-product-knowledge")
        self.assertEqual(policy.professional_files, ())
        self.assertEqual(policy.general_files[0].path, "architecture-guide.md")
        topic = policy.general_files[0].topics[0]
        self.assertEqual(topic.keywords, ("event-driven",))
        self.assertEqual(topic.chapters, ("Asynchronous systems",))
        self.assertEqual(topic.sections, ("Delivery guarantees",))
        self.assertEqual((topic.page_ranges[0].start, topic.page_ranges[0].end), (4, 9))

    def test_rejects_malformed_utf8_and_json(self) -> None:
        skill = self._skill("consulting-product-knowledge")
        index = skill / "references" / "knowledge-index.json"
        for content in (b"\xff\xfe", b"{not-json"):
            with self.subTest(content=content):
                index.write_bytes(content)
                error = self._assert_error(
                    "general_knowledge_index_invalid",
                    lambda: discover_knowledge_policy(self.plugin_root),
                )
                self.assertEqual(
                    error.paths,
                    ("skills/consulting-product-knowledge/references/knowledge-index.json",),
                )

    def test_rejects_unknown_keys_at_every_index_level(self) -> None:
        mutations = {
            "root": (
                "general_knowledge_index_invalid",
                lambda value: value.update({"unexpected": True}),
            ),
            "file": (
                "general_knowledge_index_invalid",
                lambda value: value["files"][0].update({"unexpected": True}),
            ),
            "topic": (
                "general_knowledge_topic_incomplete",
                lambda value: value["files"][0]["topics"][0].update(
                    {"unexpected": True}
                ),
            ),
            "page_range": (
                "general_knowledge_page_range_invalid",
                lambda value: value["files"][0]["topics"][0]["page_ranges"][
                    0
                ].update({"unexpected": True}),
            ),
        }
        for level, (expected_code, mutate) in mutations.items():
            with self.subTest(level=level):
                root = Path(self.temporary.name) / level
                root.mkdir()
                previous = self.plugin_root
                self.plugin_root = root
                try:
                    skill = self._skill("consulting-product-knowledge")
                    payload = self._valid_index()
                    mutate(payload)
                    self._write_index(skill, payload)
                    self._assert_error(
                        expected_code,
                        lambda: discover_knowledge_policy(root),
                    )
                finally:
                    self.plugin_root = previous

    def test_rejects_unsupported_schema_and_invalid_root_shapes(self) -> None:
        invalid_payloads = [
            {"schema_version": 2, "files": []},
            {"schema_version": True, "files": []},
            {"schema_version": 1, "files": {}},
            {"schema_version": 1, "files": []},
        ]
        for position, payload in enumerate(invalid_payloads):
            with self.subTest(position=position):
                root = Path(self.temporary.name) / f"root-{position}"
                root.mkdir()
                previous = self.plugin_root
                self.plugin_root = root
                try:
                    skill = self._skill("consulting-product-knowledge")
                    self._write_index(skill, payload)
                    self._assert_error(
                        "general_knowledge_index_invalid",
                        lambda: discover_knowledge_policy(root),
                    )
                finally:
                    self.plugin_root = previous

    def test_rejects_incomplete_file_and_topic_metadata(self) -> None:
        def mutate_purpose(payload: dict[str, object]) -> None:
            payload["files"][0]["purpose"] = "  "

        def mutate_topics(payload: dict[str, object]) -> None:
            payload["files"][0]["topics"] = []

        def mutate_name(payload: dict[str, object]) -> None:
            payload["files"][0]["topics"][0]["name"] = ""

        def mutate_keywords(payload: dict[str, object]) -> None:
            payload["files"][0]["topics"][0]["keywords"] = []

        def mutate_locator(payload: dict[str, object]) -> None:
            payload["files"][0]["topics"][0]["sections"] = "not-an-array"

        for name, mutate in {
            "purpose": mutate_purpose,
            "topics": mutate_topics,
            "name": mutate_name,
            "keywords": mutate_keywords,
            "locator": mutate_locator,
        }.items():
            with self.subTest(name=name):
                root = Path(self.temporary.name) / f"incomplete-{name}"
                root.mkdir()
                previous = self.plugin_root
                self.plugin_root = root
                try:
                    skill = self._skill("consulting-product-knowledge")
                    payload = self._valid_index()
                    mutate(payload)
                    self._write_index(skill, payload)
                    self._assert_error(
                        "general_knowledge_topic_incomplete",
                        lambda: discover_knowledge_policy(root),
                    )
                finally:
                    self.plugin_root = previous

    def test_rejects_invalid_page_range_types_and_bounds(self) -> None:
        invalid_ranges = [
            {"start": 0, "end": 1},
            {"start": 2, "end": 1},
            {"start": True, "end": 2},
            {"start": 1, "end": "2"},
            {"start": 1},
            {"start": 1, "end": 2, "label": "printed"},
        ]
        for position, page_range in enumerate(invalid_ranges):
            with self.subTest(page_range=page_range):
                root = Path(self.temporary.name) / f"range-{position}"
                root.mkdir()
                previous = self.plugin_root
                self.plugin_root = root
                try:
                    skill = self._skill("consulting-product-knowledge")
                    payload = self._valid_index()
                    payload["files"][0]["topics"][0]["page_ranges"] = [page_range]
                    self._write_index(skill, payload)
                    self._assert_error(
                        "general_knowledge_page_range_invalid",
                        lambda: discover_knowledge_policy(root),
                    )
                finally:
                    self.plugin_root = previous

    def test_rejects_unsafe_general_file_paths(self) -> None:
        unsafe = [
            "",
            ".",
            "../secret.md",
            "/absolute.md",
            "C:/absolute.md",
            "folder\\file.md",
            "folder/../file.md",
        ]
        for position, path in enumerate(unsafe):
            with self.subTest(path=path):
                root = Path(self.temporary.name) / f"unsafe-{position}"
                root.mkdir()
                previous = self.plugin_root
                self.plugin_root = root
                try:
                    skill = self._skill("consulting-product-knowledge")
                    self._write_index(skill, self._valid_index(path))
                    self._assert_error(
                        "general_knowledge_index_invalid",
                        lambda: discover_knowledge_policy(root),
                    )
                finally:
                    self.plugin_root = previous

    def test_rejects_duplicate_and_casefold_general_paths(self) -> None:
        for position, second in enumerate(("guide.md", "GUIDE.md")):
            with self.subTest(second=second):
                root = Path(self.temporary.name) / f"duplicate-{position}"
                root.mkdir()
                previous = self.plugin_root
                self.plugin_root = root
                try:
                    skill = self._skill("consulting-product-knowledge")
                    payload = self._valid_index("guide.md")
                    duplicate = json.loads(json.dumps(payload["files"][0]))
                    duplicate["path"] = second
                    payload["files"].append(duplicate)
                    self._write_index(skill, payload)
                    self._assert_error(
                        "general_knowledge_index_invalid",
                        lambda: discover_knowledge_policy(root),
                    )
                finally:
                    self.plugin_root = previous

    def test_rejects_multiple_general_knowledge_indexes(self) -> None:
        first = self._skill("consulting-product-knowledge")
        second = self._skill("consulting-other-knowledge")
        self._write_index(first, self._valid_index("first.md"))
        self._write_index(second, self._valid_index("second.md"))

        error = self._assert_error(
            "multiple_general_knowledge_indexes",
            lambda: discover_knowledge_policy(self.plugin_root),
        )

        self.assertEqual(
            error.paths,
            (
                "skills/consulting-other-knowledge/references/knowledge-index.json",
                "skills/consulting-product-knowledge/references/knowledge-index.json",
            ),
        )


if __name__ == "__main__":
    unittest.main()
