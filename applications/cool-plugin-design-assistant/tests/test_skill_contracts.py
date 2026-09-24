from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def read_reference(skill: str, filename: str) -> str:
    return (ROOT / "skills" / skill / "references" / filename).read_text(
        encoding="utf-8"
    )


class SkillContractTests(unittest.TestCase):
    def test_guiding_session_preserves_draft_and_waiting_states(self) -> None:
        text = read_skill("guiding-ai-application-design-sessions")
        for phrase in (
            "one focused question",
            "wait",
            "confirmed",
            "assumption",
            "recommendation",
            "unresolved",
            "draft",
            "explicit confirmation",
            "Traditional Chinese",
            "never Simplified Chinese",
            "scan for Simplified Chinese forms",
        ):
            self.assertIn(phrase, text)

    def test_design_statement_is_concise_separate_and_revisable(self) -> None:
        text = read_skill("creating-design-statements")
        self.assertIn("audience", text)
        self.assertIn("context", text)
        self.assertIn("problem", text)
        self.assertIn("outcome", text)
        self.assertIn("draft", text)
        self.assertIn("approved", text)
        self.assertIn("separate", text)
        self.assertIn("inverse of the problem", text)
        self.assertNotIn("choose the Skill Architecture", text)

    def test_workflow_skill_defines_modules_and_user_interaction_protocols_not_skills(
        self,
    ) -> None:
        text = read_skill("designing-application-workflows-and-instruction-modules")
        for phrase in (
            "primary-workflow",
            "intent-triggered",
            "cross-cutting",
            "user-interaction protocol",
            "transitions",
            "failure",
            "completion",
            "Application Workbench",
        ):
            self.assertIn(phrase, text)
        self.assertIn("Instruction Module is not a Skill", text)


if __name__ == "__main__":
    unittest.main()
