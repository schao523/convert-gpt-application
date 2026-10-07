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

    def test_tool_contract_root_binding_is_valid_but_skill_direct_route_is_not(self) -> None:
        tools = self.root / "tools"
        tools.mkdir()
        (tools / "run.py").write_text("print('ok')", encoding="utf-8")
        (self.root / "tool.json").write_text(
            json.dumps({"schema": "plugin-builder-application-tool-v1", "files": ["tools/run.py"]}),
            encoding="utf-8",
        )
        (self.skill / "SKILL.md").write_text("Invoke `normalize-input`.", encoding="utf-8")
        self.assertEqual(self.issues(), ())

        (self.skill / "SKILL.md").write_text("Run `tools/run.py`.", encoding="utf-8")
        self.assertIn(
            "path_binding_missing:skills/example/SKILL.md:tools/run.py",
            self.issues(),
        )


if __name__ == "__main__":
    unittest.main()
