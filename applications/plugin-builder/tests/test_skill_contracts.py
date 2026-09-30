from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXPECTED_SKILLS = {
    "guiding-plugin-builder-sessions": {
        "references/session-workflow.md",
        "references/state-and-recovery.md",
    },
    "planning-plugin-implementations": {
        "references/input-and-plan-contract.md",
        "references/requirement-coverage-contract.md",
    },
    "building-and-updating-plugins": {
        "references/candidate-and-update-contract.md",
        "references/application-tool-contract.md",
    },
    "verifying-and-packaging-plugins": {
        "references/evidence-and-package-contract.md",
        "references/tool-evidence-contract.md",
    },
}


def read_skill(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if len(lines) < 4 or lines[0] != "---":
        raise AssertionError("missing frontmatter")
    end = lines.index("---", 1)
    result: dict[str, str] = {}
    for line in lines[1:end]:
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"')
    return result


def contract_rows(path: Path, heading: str) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    start = lines.index(f"## {heading}")
    rows: dict[str, str] = {}
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 2 and cells[0] not in {"Key", "---"}:
            rows[cells[0]] = cells[1]
    return rows


class SkillContractTests(unittest.TestCase):
    # Catches a deleted or renamed skill, invalid frontmatter, or a broken progressive-disclosure link.
    def test_skill_discovery_and_reference_closure(self) -> None:
        self.assertEqual(
            {path.name for path in SKILLS.iterdir() if path.is_dir()},
            set(EXPECTED_SKILLS),
        )
        for name, expected_references in EXPECTED_SKILLS.items():
            text = read_skill(name)
            metadata = frontmatter(text)
            self.assertEqual(metadata["name"], name)
            self.assertTrue(metadata["description"])
            links = {
                target
                for target in re.findall(r"\[[^]]+\]\(([^)]+\.md)\)", text)
                if target.startswith("references/")
            }
            self.assertEqual(links, expected_references, name)
            for target in links:
                self.assertTrue((SKILLS / name / target).is_file(), target)

    # Catches routing that skips planning, loses pause state, or permits mutation/package before W1/W2.
    def test_session_routing_and_human_gates(self) -> None:
        root = SKILLS / "guiding-plugin-builder-sessions"
        routing = contract_rows(root / "references/session-workflow.md", "Routing contract")
        self.assertEqual(
            routing,
            {
                "CREATE": "PLAN",
                "UPDATE": "REQUIRE_BASELINE_THEN_PLAN",
                "PAUSE": "H1_PAUSED",
                "RESUME": "RESTORE_AND_SUMMARIZE",
                "CANCEL": "E2_CANCELLED",
            },
        )
        gates = contract_rows(root / "references/session-workflow.md", "Gate contract")
        self.assertEqual(gates["W1"], "BLOCK_MUTATION_UNTIL_APPROVED")
        self.assertEqual(gates["W2"], "BLOCK_PACKAGING_UNTIL_APPROVED")

    # Catches planning from an unapproved input, missing requirement coverage, or self-approved behavior changes.
    def test_planning_requires_authority_and_traceability(self) -> None:
        root = SKILLS / "planning-plugin-implementations" / "references"
        contract = contract_rows(root / "input-and-plan-contract.md", "Planning contract")
        self.assertEqual(contract["INPUT_AUTHORITY"], "APPROVED_SPEC_REQUIRED")
        self.assertEqual(contract["OUTPUT"], "REQUIREMENT_COVERAGE_PLAN")
        self.assertEqual(contract["BEHAVIOR_CHANGE"], "RETURN_FOR_NEW_APPROVAL")

    # Catches update data loss, create/update ambiguity, building before W1, or premature final ZIP creation.
    def test_building_preserves_update_content_and_returns_candidate(self) -> None:
        path = SKILLS / "building-and-updating-plugins" / "references/candidate-and-update-contract.md"
        contract = contract_rows(path, "Candidate contract")
        self.assertEqual(contract["PRECONDITION"], "W1_APPROVED")
        self.assertEqual(contract["MODES"], "CREATE_OR_UPDATE_EXPLICIT")
        self.assertEqual(contract["UNEXPLAINED_UPDATE_CONTENT"], "PRESERVE_AND_WAIT")
        self.assertEqual(contract["OUTPUT"], "CANDIDATE_NOT_FINAL_ZIP")

    # Catches evidence inflation, packaging after a required failure, bypassed W2, or automatic upload/deployment.
    def test_verification_blocks_failures_and_keeps_upload_manual(self) -> None:
        path = SKILLS / "verifying-and-packaging-plugins" / "references/evidence-and-package-contract.md"
        evidence = contract_rows(path, "Evidence states")
        self.assertEqual(
            set(evidence),
            {"EXPECTED", "STATICALLY VERIFIED", "RUNTIME VERIFIED", "NOT VERIFIED"},
        )
        package = contract_rows(path, "Packaging contract")
        self.assertEqual(package["REQUIRED_FAILURE"], "BLOCK_ARTIFACT")
        self.assertEqual(package["PRECONDITION"], "W2_APPROVED")
        self.assertEqual(package["DELIVERY"], "RETURN_ZIP_FOR_MANUAL_UPLOAD")

    # Catches accidental scope expansion or unsupported evidence claims in skill entrypoints.
    def test_skill_entrypoints_do_not_claim_excluded_capabilities(self) -> None:
        combined = "\n".join(read_skill(name) for name in EXPECTED_SKILLS)
        for forbidden in (
            "supports OpenClaw",
            "automatic deployment",
            "publishes to",
            "RUNTIME VERIFIED",
        ):
            self.assertNotIn(forbidden.casefold(), combined.casefold())

    def test_stage_skills_route_to_concrete_cli_and_tool_references(self) -> None:
        guiding = read_skill("guiding-plugin-builder-sessions")
        planning = read_skill("planning-plugin-implementations")
        building = read_skill("building-and-updating-plugins")
        verifying = read_skill("verifying-and-packaging-plugins")
        for command in ("inspect", "pause", "resume", "cancel"):
            self.assertIn(f"`{command}`", guiding)
        for command in ("plan", "approve-w1"):
            self.assertIn(f"`{command}`", planning)
        for command in ("resolve-update", "build"):
            self.assertIn(f"`{command}`", building)
        for command in ("verify", "approve-w2", "package"):
            self.assertIn(f"`{command}`", verifying)
        self.assertIn("application-tool-contract.md", building)
        self.assertIn("tool-evidence-contract.md", verifying)


if __name__ == "__main__":
    unittest.main()
