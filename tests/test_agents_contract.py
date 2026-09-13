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
            "build-package",
            "verify",
            "build-assets",
            "check-index-reuse",
            "derive-index",
            "scripts/verify_extraction.py",
        ):
            self.assertIn(command, text)
        self.assertNotIn("invoke and follow the `convert-gpt-application` skill", text)

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
