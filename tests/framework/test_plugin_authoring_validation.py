from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.plugin_authoring import (
    validate_plugin_tree,
    validate_reference_closure,
    validate_skill_tree,
)


class PluginAuthoringValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "plugin"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, relative: str, content: str) -> Path:
        destination = self.root / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        return destination

    def write_skill(self, name: str, description: str, body: str = "# Instructions\n") -> Path:
        return self.write(
            f"skills/{name}/SKILL.md",
            f"---\nname: {name}\ndescription: {description}\n---\n\n{body}",
        )

    @staticmethod
    def codes(issues) -> set[str]:
        return {issue.code for issue in issues}

    def valid_manifest(self) -> dict[str, object]:
        return {
            "name": "sample-plugin",
            "version": "1.2.3",
            "description": "A portable sample plugin.",
            "author": {"name": "Example Developer"},
            "skills": "./skills/",
            "interface": {
                "displayName": "Sample Plugin",
                "shortDescription": "A portable sample.",
                "longDescription": "A portable sample plugin used to exercise the authoring contract.",
                "developerName": "Example Developer",
                "category": "Productivity",
                "capabilities": ["Interactive", "Read"],
                "defaultPrompt": "Help me use the sample plugin.",
                "iconSmall": "./assets/icon-small.png",
            },
        }

    def test_plugin_validator_matches_creator_contract_for_supported_shape(self) -> None:
        manifest = self.valid_manifest()
        self.write(".codex-plugin/plugin.json", json.dumps(manifest))
        self.write("assets/icon-small.png", "image")
        self.write_skill("first-skill", "Perform the first supported user workflow.")
        self.write_skill("second-skill", "Perform the second supported user workflow.")

        self.assertEqual(validate_plugin_tree(self.root), ())

        manifest["surprise"] = True
        manifest["interface"]["iconSmall"] = "C:/private/icon.png"  # type: ignore[index]
        self.write(".codex-plugin/plugin.json", json.dumps(manifest))
        issues = validate_plugin_tree(self.root)
        self.assertIn("plugin_manifest_unknown_key", self.codes(issues))
        self.assertIn("plugin_asset_path_invalid", self.codes(issues))

    def test_skill_validator_rejects_invalid_frontmatter_and_placeholders(self) -> None:
        self.write(
            "skills/Bad_Name/SKILL.md",
            "---\n"
            "name: Bad_Name\n"
            "description: Replace <TODO> with a real description.\n"
            "unexpected: true\n"
            "---\n\n"
            "# TODO: finish these instructions\n",
        )

        issues = validate_skill_tree(self.root)
        self.assertEqual(
            self.codes(issues),
            {
                "skill_directory_name_invalid",
                "skill_description_invalid",
                "skill_frontmatter_name_invalid",
                "skill_frontmatter_unknown_key",
                "unfinished_scaffold_marker",
            },
        )

    def test_reference_closure_requires_existing_directly_routed_files(self) -> None:
        self.write_skill(
            "professional-workflow",
            "Use the professional method for the requested workflow.",
            "# Professional workflow\n\nRead [the method](references/method.md).\n",
        )
        self.write("skills/professional-workflow/references/method.md", "# Method\n")
        self.write("skills/professional-workflow/references/orphan.md", "# Orphan\n")

        self.write_skill(
            "consulting-general-knowledge",
            "Consult general knowledge when the workflow needs it.",
            "# General knowledge\n\nRead [the topic guide](references/knowledge-index.json).\n",
        )
        self.write("skills/consulting-general-knowledge/references/guide.md", "# Guide\n")
        self.write(
            "skills/consulting-general-knowledge/references/knowledge-index.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "files": [
                        {
                            "path": "guide.md",
                            "purpose": "General operating guidance.",
                            "topics": [
                                {
                                    "name": "Operations",
                                    "chapters": [],
                                    "sections": ["Guide"],
                                    "keywords": ["operations"],
                                    "page_ranges": [],
                                }
                            ],
                        }
                    ],
                }
            ),
        )

        issues = validate_reference_closure(self.root)
        self.assertEqual(self.codes(issues), {"professional_reference_unlinked"})
        self.assertEqual(issues[0].path, "skills/professional-workflow/references/orphan.md")

        (self.root / "skills/professional-workflow/references/orphan.md").unlink()
        index_path = self.root / "skills/consulting-general-knowledge/references/knowledge-index.json"
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        payload["files"][0]["path"] = "missing.md"
        index_path.write_text(json.dumps(payload), encoding="utf-8")
        self.assertIn(
            "general_reference_missing",
            self.codes(validate_reference_closure(self.root)),
        )


if __name__ == "__main__":
    unittest.main()
