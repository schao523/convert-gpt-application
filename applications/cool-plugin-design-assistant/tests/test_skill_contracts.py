from pathlib import Path
import re
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

    def test_reference_material_skill_reserves_technical_binding_for_workbench(
        self,
    ) -> None:
        text = read_skill("evaluating-reference-materials")
        for phrase in (
            "Reference Material Usage Map",
            "workflow",
            "Instruction Module",
            "decision",
            "output",
            "provenance",
            "rights",
            "exact quotation",
            "advisory",
        ):
            self.assertIn(phrase, text)
        for forbidden in ("assign to a Skill", "choose a RAG", "choose runtime storage"):
            self.assertNotIn(forbidden, text)

    def test_specification_has_approved_sections_and_handoff_gate(self) -> None:
        contract = read_reference(
            "creating-application-plugin-design-specifications",
            "specification-contract.md",
        )
        self.assertEqual(len(re.findall(r"(?m)^\d+\. \*\*", contract)), 21)
        skill = read_skill("creating-application-plugin-design-specifications")
        self.assertIn("explicit user confirmation", skill)
        self.assertIn("Application Workbench", skill)
        self.assertIn("must not prescribe", skill)

    def test_implementation_review_requires_both_inputs_and_classifies_findings(
        self,
    ) -> None:
        text = read_skill("reviewing-application-implementations")
        self.assertIn("approved specification", text)
        self.assertIn("Application Implementation", text)
        for classification in (
            "error",
            "omission",
            "optional improvement",
            "approved deviation",
        ):
            self.assertIn(classification, text)
        self.assertIn("do not redesign", text)
        self.assertIn("do not promise later correction", text)

    def test_test_planning_requires_inputs_and_never_invents_execution(self) -> None:
        text = read_skill("planning-application-tests-and-improvements")
        for phrase in (
            "approved specification",
            "requirement ID",
            "observable",
            "EXPECTED",
            "STATICALLY VERIFIED",
            "RUNTIME VERIFIED",
            "NOT VERIFIED",
            "supplied results",
            "versioned",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
