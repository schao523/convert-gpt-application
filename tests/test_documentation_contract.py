from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
COMMAND_REFERENCE = ROOT / "docs" / "PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md"


class DocumentationContractTests(unittest.TestCase):
    def test_documents_multi_application_verification_and_readiness(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in (README, COMMAND_REFERENCE)
        )
        for required in (
            "--all",
            "--application",
            "--marketplace",
            '"schema_version": 2',
            "NOT VERIFIED",
            "NOT APPLICABLE",
            "applications/*/conversion.json",
            ".tmp/verification/",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)
        self.assertIn("Codex and OpenClaw", combined)
        self.assertIn("not release-readiness evidence", combined)

    def test_documents_application_aware_provenance_and_independent_shared_gates(self) -> None:
        content = COMMAND_REFERENCE.read_text(encoding="utf-8")
        self.assertIn("write_extraction_provenance.py", content)
        self.assertIn("--application <plugin-id>", content)
        self.assertIn("Shared gates do not require a reference application", content)


if __name__ == "__main__":
    unittest.main()
