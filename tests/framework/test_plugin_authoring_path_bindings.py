from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.plugin_authoring import validate_path_bindings


class PluginAuthoringPathBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.skill = self.root / "skills/example"
        self.skill.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def issues(self) -> tuple[str, ...]:
        return tuple(
            ":".join(part for part in (item.code, item.path, item.detail) if part)
            for item in validate_path_bindings(self.root)
        )

    def test_rejects_escaping_and_platform_specific_paths_in_supported_text_forms(self) -> None:
        cases = {
            "markdown": "[bad](../../scripts/tool.py)",
            "backtick": "Run `..\\..\\scripts\\tool.py`.",
            "prose": "Command: C:/private/tool.py",
            "yaml": "command: ../../scripts/tool.py",
            "json": json.dumps({"command": "../../scripts/tool.py"}),
            "example": "python ../../scripts/tool.py",
        }
        for label, text in cases.items():
            with self.subTest(label=label):
                suffix = "json" if label == "json" else "yaml" if label == "yaml" else "md"
                (self.skill / f"{label}.{suffix}").write_text(text, encoding="utf-8")
                self.assertTrue(any(item.startswith("path_binding_invalid:") for item in self.issues()))
                (self.skill / f"{label}.{suffix}").unlink()

    def test_valid_reference_tool_id_and_url_have_no_false_positive(self) -> None:
        references = self.skill / "references"
        references.mkdir()
        (references / "method.md").write_text("method", encoding="utf-8")
        (self.skill / "SKILL.md").write_text(
            "Read [method](references/method.md), invoke `normalize-input`, and see https://example.com.",
            encoding="utf-8",
        )
        self.assertEqual(self.issues(), ())

    def test_explicit_plugin_root_paths_resolve_without_changing_skill_local_scope(self) -> None:
        tools = self.root / "tools"
        tools.mkdir()
        (tools / "run.py").write_text("print('ok')", encoding="utf-8")
        other = self.root / "skills/other"
        other.mkdir()
        (other / "SKILL.md").write_text("---\nname: other\ndescription: Other.\n---\n", encoding="utf-8")
        references = self.skill / "references"
        references.mkdir()
        (references / "method.md").write_text("method", encoding="utf-8")
        (self.root / "tool.json").write_text(
            json.dumps({"schema": "plugin-builder-application-tool-v1", "files": ["tools/run.py"]}),
            encoding="utf-8",
        )
        (self.skill / "SKILL.md").write_text(
            "Read [method](references/method.md) and [other](skills/other/SKILL.md); see `tools/run.py`.",
            encoding="utf-8",
        )
        self.assertEqual(self.issues(), ())

    def test_missing_explicit_plugin_root_paths_are_reported(self) -> None:
        (self.skill / "SKILL.md").write_text(
            "See `tools/missing.py` and [other](skills/missing/SKILL.md).", encoding="utf-8"
        )
        self.assertIn(
            "path_binding_missing:skills/example/SKILL.md:tools/missing.py",
            self.issues(),
        )
        self.assertIn(
            "path_binding_missing:skills/example/SKILL.md:skills/missing/SKILL.md",
            self.issues(),
        )

    def test_prefixed_plugin_root_paths_in_skill_prose_remain_invalid(self) -> None:
        tools = self.root / "tools"
        tools.mkdir()
        (tools / "run.py").write_text("print('ok')", encoding="utf-8")
        for token in ("/tools/run.py", "\\tools/run.py"):
            with self.subTest(token=token):
                (self.skill / "SKILL.md").write_text(f"Run `{token}`.\n", encoding="utf-8")
                self.assertIn(
                    f"path_binding_invalid:skills/example/SKILL.md:{token}",
                    self.issues(),
                )

    def test_runtime_document_placeholder_is_not_an_absolute_skill_binding(self) -> None:
        runtime = self.root / "runtime"
        runtime.mkdir()
        (runtime / "scenarios.md").write_text(
            "Use `<workspace>/t1/session.json` for the test fixture.\n", encoding="utf-8"
        )
        self.assertEqual(self.issues(), ())

    def test_plugin_root_symlink_escape_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as outside_dir:
            outside = Path(outside_dir) / "outside-tool.py"
            outside.write_text("print('outside')", encoding="utf-8")
            try:
                tools = self.root / "tools"
                tools.mkdir()
                (tools / "escape.py").symlink_to(outside)
            except OSError as error:
                self.skipTest(f"native symlink unavailable: {error}")
            (self.skill / "SKILL.md").write_text("See `tools/escape.py`.", encoding="utf-8")
            self.assertIn("path_binding_invalid:skills/example/SKILL.md:tools/escape.py", self.issues())


if __name__ == "__main__":
    unittest.main()
