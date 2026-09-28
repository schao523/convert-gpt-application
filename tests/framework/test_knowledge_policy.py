from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from obvious_one_plugin_framework.knowledge_policy import (
    KnowledgePolicyError,
    discover_knowledge_policy,
    validate_knowledge_policy,
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


class KnowledgePolicyValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.plugin_root = Path(self.temporary.name) / "plugin"
        self.plugin_root.mkdir()

    def _skill(self, name: str, instructions: str = "") -> Path:
        skill = self.plugin_root / "skills" / name
        (skill / "references").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"# {name}\n\n{instructions}",
            encoding="utf-8",
        )
        return skill

    @staticmethod
    def _valid_index(path: str = "architecture-guide.md") -> dict[str, object]:
        return KnowledgePolicyParserTests._valid_index(path)

    def _write_index(self, skill: Path, payload: object) -> None:
        (skill / "references" / "knowledge-index.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def _assert_error(self, code: str, action) -> KnowledgePolicyError:
        with self.assertRaises(KnowledgePolicyError) as captured:
            action()
        self.assertEqual(captured.exception.code, code)
        return captured.exception

    def test_accepts_inline_and_reference_definition_links(self) -> None:
        skill = self._skill(
            "designing-systems",
            "Use [core rules](references/core.md).\n"
            "Consult [nested rules][nested].\n\n"
            "[nested]: references/nested/rules.md\n",
        )
        (skill / "references" / "core.md").write_text("Core\n", encoding="utf-8")
        nested = skill / "references" / "nested"
        nested.mkdir()
        (nested / "rules.md").write_text("Nested\n", encoding="utf-8")

        evidence = validate_knowledge_policy(self.plugin_root)

        self.assertEqual(evidence.professional_reference_count, 2)
        self.assertEqual(evidence.general_reference_count, 0)
        self.assertEqual(evidence.package_structure, "STATICALLY VERIFIED")
        self.assertEqual(evidence.deterministic_discovery, "NOT APPLICABLE")
        self.assertEqual(evidence.coverage_traceability, "NOT VERIFIED")
        self.assertEqual(evidence.behavior, "NOT VERIFIED")
        self.assertEqual(evidence.codex_execution, "NOT VERIFIED")
        self.assertEqual(evidence.openclaw_execution, "NOT VERIFIED")

    def test_bare_or_code_spanned_filename_is_not_a_direct_link(self) -> None:
        for position, instructions in enumerate(
            ("Read references/rules.md.\n", "Read `references/rules.md`.\n")
        ):
            with self.subTest(instructions=instructions):
                root = Path(self.temporary.name) / f"bare-{position}"
                root.mkdir()
                previous = self.plugin_root
                self.plugin_root = root
                try:
                    skill = self._skill("designing-systems", instructions)
                    (skill / "references" / "rules.md").write_text(
                        "Rules\n", encoding="utf-8"
                    )
                    self._assert_error(
                        "professional_reference_unlinked",
                        lambda: validate_knowledge_policy(root),
                    )
                finally:
                    self.plugin_root = previous

    def test_rejects_missing_broken_and_escaping_local_links(self) -> None:
        cases = {
            "missing": "[missing](references/missing.md)",
            "broken": "[readme](README.md)",
            "escaping": "[outside](../outside.md)",
            "windows_drive": "[outside](C:/outside.md)",
            "network_absolute": "[outside](//server/share/outside.md)",
            "file_uri": "[outside](file:///C:/outside.md)",
        }
        for name, instructions in cases.items():
            with self.subTest(name=name):
                root = Path(self.temporary.name) / name
                root.mkdir()
                previous = self.plugin_root
                self.plugin_root = root
                try:
                    self._skill("designing-systems", instructions)
                    self._assert_error(
                        "professional_reference_missing",
                        lambda: validate_knowledge_policy(root),
                    )
                finally:
                    self.plugin_root = previous

    def test_rejects_linked_skill_root_before_discovery(self) -> None:
        skill = self._skill(
            "designing-systems",
            "[rules](references/rules.md)\n",
        )
        (skill / "references" / "rules.md").write_text(
            "Rules\n", encoding="utf-8"
        )
        original = Path.is_symlink

        def simulated_link(path: Path) -> bool:
            return path == skill or original(path)

        with patch.object(Path, "is_symlink", autospec=True, side_effect=simulated_link):
            self._assert_error(
                "knowledge_plugin_root_invalid",
                lambda: validate_knowledge_policy(self.plugin_root),
            )

    def test_rejects_symlinked_professional_reference(self) -> None:
        skill = self._skill(
            "designing-systems",
            "[rules](references/rules.md)\n",
        )
        outside = Path(self.temporary.name) / "outside.md"
        outside.write_text("Outside\n", encoding="utf-8")
        link = skill / "references" / "rules.md"
        try:
            os.symlink(outside, link)
        except OSError as error:
            self.skipTest(f"file symlinks are unavailable: {error}")

        self._assert_error(
            "professional_reference_missing",
            lambda: validate_knowledge_policy(self.plugin_root),
        )

    def test_rejects_casefold_professional_path_aliases(self) -> None:
        skill = self._skill(
            "designing-systems",
            "[upper](references/Rule.md)\n[lower](references/rule.md)\n",
        )
        upper = skill / "references" / "Rule.md"
        lower = skill / "references" / "rule.md"
        upper.write_text("Upper\n", encoding="utf-8")
        lower.write_text("Lower\n", encoding="utf-8")
        if len(list((skill / "references").glob("*.md"))) != 2:
            self.skipTest("filesystem is case-insensitive")

        self._assert_error(
            "professional_reference_path_collision",
            lambda: validate_knowledge_policy(self.plugin_root),
        )

    def test_rejects_missing_indexed_general_file(self) -> None:
        skill = self._skill(
            "consulting-product-knowledge",
            "[topic guide](references/knowledge-index.json)\n",
        )
        self._write_index(skill, self._valid_index())

        self._assert_error(
            "general_knowledge_index_path_missing",
            lambda: validate_knowledge_policy(self.plugin_root),
        )

    def test_rejects_unindexed_general_file(self) -> None:
        skill = self._skill(
            "consulting-product-knowledge",
            "[topic guide](references/knowledge-index.json)\n",
        )
        (skill / "references" / "architecture-guide.md").write_text(
            "Guide\n", encoding="utf-8"
        )
        (skill / "references" / "orphan.md").write_text("Orphan\n", encoding="utf-8")
        self._write_index(skill, self._valid_index())

        self._assert_error(
            "general_knowledge_file_unindexed",
            lambda: validate_knowledge_policy(self.plugin_root),
        )

    def test_rejects_consultation_skill_that_does_not_link_index(self) -> None:
        skill = self._skill("consulting-product-knowledge", "Use the topic guide.\n")
        (skill / "references" / "architecture-guide.md").write_text(
            "Guide\n", encoding="utf-8"
        )
        self._write_index(skill, self._valid_index())

        self._assert_error(
            "general_knowledge_index_invalid",
            lambda: validate_knowledge_policy(self.plugin_root),
        )

    def test_accepts_nested_indexed_general_file(self) -> None:
        skill = self._skill(
            "consulting-product-knowledge",
            "[topic guide](references/knowledge-index.json)\n",
        )
        nested = skill / "references" / "architecture"
        nested.mkdir()
        (nested / "guide.md").write_text("Guide\n", encoding="utf-8")
        self._write_index(skill, self._valid_index("architecture/guide.md"))

        evidence = validate_knowledge_policy(self.plugin_root)

        self.assertEqual(evidence.general_reference_count, 1)
        self.assertEqual(evidence.consultation_skill, "consulting-product-knowledge")
        self.assertEqual(evidence.deterministic_discovery, "STATICALLY VERIFIED")

    def test_rejects_plugin_root_knowledge_directory(self) -> None:
        (self.plugin_root / "knowledge").mkdir()

        self._assert_error(
            "plugin_root_knowledge_directory_forbidden",
            lambda: validate_knowledge_policy(self.plugin_root),
        )

    def test_coverage_traceability_is_separate_from_behavior(self) -> None:
        skill = self._skill(
            "designing-systems",
            "[rules](references/rules.md)\n",
        )
        (skill / "references" / "rules.md").write_text("Rules\n", encoding="utf-8")
        matrix = self.plugin_root / "tests" / "coverage-matrix.md"
        matrix.parent.mkdir()
        matrix.write_text(
            "| Knowledge file | Scenario |\n"
            "| --- | --- |\n"
            "| skills/designing-systems/references/rules.md | distinctive rule |\n",
            encoding="utf-8",
        )

        absent = validate_knowledge_policy(self.plugin_root)
        present = validate_knowledge_policy(self.plugin_root, matrix)

        self.assertEqual(absent.coverage_traceability, "NOT VERIFIED")
        self.assertEqual(present.coverage_traceability, "STATICALLY VERIFIED")
        self.assertEqual(present.behavior, "NOT VERIFIED")

    def test_required_coverage_rejects_missing_knowledge_path(self) -> None:
        skill = self._skill(
            "designing-systems",
            "[rules](references/rules.md)\n",
        )
        (skill / "references" / "rules.md").write_text("Rules\n", encoding="utf-8")
        matrix = self.plugin_root / "tests" / "coverage-matrix.md"
        matrix.parent.mkdir()
        matrix.write_text("# Coverage\n", encoding="utf-8")

        with self.assertRaisesRegex(
            KnowledgePolicyError,
            "knowledge_behavior_evidence_missing",
        ):
            validate_knowledge_policy(
                self.plugin_root,
                matrix,
                require_coverage=True,
            )

    def test_no_knowledge_has_not_applicable_coverage(self) -> None:
        evidence = validate_knowledge_policy(
            self.plugin_root,
            require_coverage=True,
        )

        self.assertEqual(evidence.coverage_traceability, "NOT APPLICABLE")


if __name__ == "__main__":
    unittest.main()
