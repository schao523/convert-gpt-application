from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"


class AgentsContractTests(unittest.TestCase):
    def test_governs_dual_runtime_portability_and_readiness(self) -> None:
        text = AGENTS.read_text(encoding="utf-8")
        self.assertIn(
            "Every converted plugin targets both Codex and OpenClaw by default.",
            text,
        )
        self.assertIn("PORTABLE WITH ADAPTER", text)
        self.assertIn("CONVERSION COMPLETE — RUNTIME VALIDATION PENDING", text)
        self.assertIn("Installed ≠ Ready", text)

    def test_routes_agents_to_repository_tools_without_a_missing_skill(self) -> None:
        text = AGENTS.read_text(encoding="utf-8")
        for command in (
            "validate-contract",
            "migrate-contract",
            "build-package",
            "verify",
            "prepare-marketplace",
            "verify-marketplace",
            "build-assets",
            "check-index-reuse",
            "derive-index",
            "scripts/verify_extraction.py",
        ):
            self.assertIn(command, text)
        self.assertNotIn("invoke and follow the `convert-gpt-application` skill", text)

    def test_routes_each_guide_by_task_instead_of_requiring_all_guides(self) -> None:
        text = AGENTS.read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        self.assertIn("owner decisions, approvals, or conversion workflow", normalized)
        self.assertIn("designing, authoring, or reviewing skills and plugin structure", normalized)
        self.assertIn("framework CLI, packaging, verification, or marketplace operations", normalized)
        self.assertIn("command reference is authoritative", normalized.lower())

    def test_governs_hardened_framework_contracts(self) -> None:
        text = AGENTS.read_text(encoding="utf-8")
        for fragment in (
            "Python 3.11 or newer",
            "schema v3",
            "read-only legacy formats",
            "result-schema-v1",
            "catalog-driven",
            "nested Git worktrees",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_uses_automation_neutral_conversion_roles(self) -> None:
        text = AGENTS.read_text(encoding="utf-8")
        self.assertIn("conversion caller", text)
        self.assertIn("decision owner", text)
        self.assertNotIn("conversion maintainer", text)

    def test_preserves_repository_and_approval_boundaries(self) -> None:
        text = AGENTS.read_text(encoding="utf-8")
        for fragment in (
            "src/obvious_one_plugin_framework",
            "applications/<plugin-id>",
            "conversion.local.json",
            "explicit user approval",
            "model downloads",
            "marketplace mutation",
            "Git pushes",
            "source cleanup",
        ):
            self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
