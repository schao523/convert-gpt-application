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


if __name__ == "__main__":
    unittest.main()
