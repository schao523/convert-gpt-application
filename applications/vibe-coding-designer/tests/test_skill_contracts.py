from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "guiding-vibe-design-sessions",
    "creating-software-design-specifications",
    "designing-data-services-and-workflows",
    "creating-implementation-prompts",
    "reviewing-software-design-specifications",
    "planning-software-tests",
    "creating-repo-development-packages",
}


class SkillContractTests(unittest.TestCase):
    def test_plugin_identity_and_portable_skill_inventory(self) -> None:
        manifest = json.loads(
            (ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "vibe-coding-designer")
        self.assertEqual(manifest["version"], "1.0.0")
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["author"]["name"], "schao523")
        self.assertEqual(manifest["interface"]["displayName"], "Vibe Coding Designer")
        self.assertEqual(
            {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()},
            SKILLS,
        )
        self.assertFalse((ROOT / "openclaw" / "skills").exists())

    def test_every_skill_has_valid_discovery_metadata(self) -> None:
        for name in SKILLS:
            with self.subTest(skill=name):
                skill = ROOT / "skills" / name
                text = (skill / "SKILL.md").read_text(encoding="utf-8")
                match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
                self.assertIsNotNone(match)
                self.assertIn(f"name: {name}", match.group(1))
                self.assertRegex(match.group(1), r"(?m)^description: Use when ")
                metadata = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")
                self.assertIn("display_name:", metadata)
                self.assertIn("short_description:", metadata)
                self.assertNotIn("[TODO:", text + metadata)

    def test_general_software_scope_does_not_force_web_gui(self) -> None:
        session = (ROOT / "skills/guiding-vibe-design-sessions/SKILL.md").read_text(
            encoding="utf-8"
        )
        method = (
            ROOT
            / "skills/creating-software-design-specifications/references/software-design-contract.md"
        ).read_text(encoding="utf-8")
        combined = session + method
        for form in ("CLI", "TUI", "desktop", "mobile", "API", "worker", "library"):
            self.assertIn(form, combined)
        self.assertIn("Web GUI", combined)
        self.assertRegex(combined, r"(?i)only when.*(requested|required)")
        self.assertIn("simplest software form", combined)

    def test_session_contract_preserves_explicit_eleven_stage_wizard(self) -> None:
        contract = (
            ROOT / "skills/guiding-vibe-design-sessions/references/session-contract.md"
        ).read_text(encoding="utf-8")
        stages = re.findall(r"(?m)^\d+\. \*\*", contract)
        self.assertEqual(len(stages), 11)
        self.assertIn("one focused question", contract)
        self.assertIn("Traditional Chinese", contract)

    def test_design_contract_has_fourteen_numbered_sections_and_conditional_web_rules(self) -> None:
        contract = (
            ROOT
            / "skills/creating-software-design-specifications/references/software-design-contract.md"
        ).read_text(encoding="utf-8")
        sections = re.findall(r"(?m)^\d+\. \*\*", contract)
        self.assertEqual(len(sections), 14)
        self.assertIn("WCAG", contract)
        self.assertIn("SEO", contract)
        self.assertIn("conditional", contract.lower())

    def test_safety_and_truthfulness_rules_are_explicit(self) -> None:
        all_text = "\n".join(
            path.read_text(encoding="utf-8") for path in (ROOT / "skills").rglob("*.md")
        )
        self.assertIn("Do not implement the designed application", all_text)
        self.assertIn("Do not invent a coverage percentage", all_text)
        self.assertIn("Never include credentials", all_text)
        self.assertIn("non-executable", all_text)


if __name__ == "__main__":
    unittest.main()
