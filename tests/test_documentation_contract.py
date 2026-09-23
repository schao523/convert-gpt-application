from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
COMMAND_REFERENCE = ROOT / "docs" / "PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md"
USER_GUIDE = ROOT / "docs" / "GPT_TO_PLUGIN_USER_GUIDE.md"
TECHNICAL_REFERENCE = ROOT / "docs" / "PLUGIN_SKILLS_TECHNICAL_REFERENCE.md"


class DocumentationContractTests(unittest.TestCase):
    def test_all_governed_documents_share_hardened_framework_basics(self) -> None:
        documents = (AGENTS, COMMAND_REFERENCE, USER_GUIDE, TECHNICAL_REFERENCE)
        for path in documents:
            content = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("Python 3.11 or newer", content)
                self.assertIn("schema v3", content.lower())
                self.assertIn("result-schema-v1", content)
                self.assertIn("catalog-driven", content)
                self.assertIn("prepare-marketplace", content)
                self.assertIn("verify-marketplace", content)
                self.assertIn("publication", content.lower())
                self.assertIn("approval", content.lower())

    def test_documents_multi_application_verification_and_readiness(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in (README, COMMAND_REFERENCE)
        )
        for required in (
            "--all",
            "--application",
            "--marketplace",
            '"schema_version": 3',
            "NOT VERIFIED",
            "NOT APPLICABLE",
            "applications/*/conversion.json",
            ".tmp/verification/",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)
        self.assertIn("Codex and OpenClaw", combined)
        self.assertIn("not release-readiness evidence", combined)

    def test_documents_v3_recovery_and_local_marketplace_workflow(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (README, COMMAND_REFERENCE, USER_GUIDE)
        )
        for required in (
            "validate-contract",
            "migrate-contract",
            "prepare-marketplace",
            "verify-marketplace",
            "verify_existing",
            "legacy_contract_read_only",
            "conversion caller",
            "decision owner",
            "schema v1 and schema v2",
            "does not apply or publish the delta",
            "NOT APPLICABLE",
            "-text whitespace=cr-at-eol",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)

    def test_documents_application_aware_provenance_and_independent_shared_gates(self) -> None:
        content = COMMAND_REFERENCE.read_text(encoding="utf-8")
        self.assertIn("write_extraction_provenance.py", content)
        self.assertIn("--application <plugin-id>", content)
        self.assertIn("Shared gates do not require a reference application", content)

    def test_documents_runtime_and_schema_prerequisites(self) -> None:
        command_reference = COMMAND_REFERENCE.read_text(encoding="utf-8")
        technical_reference = TECHNICAL_REFERENCE.read_text(encoding="utf-8")
        for content in (command_reference, technical_reference):
            self.assertIn("Python 3.11 or newer", content)
            lowered = content.lower()
            self.assertIn("distribution-contract schema v3", lowered)
            self.assertIn("application-configuration schema v2", lowered)

    def test_technical_reference_uses_hardened_distribution_workflow(self) -> None:
        content = TECHNICAL_REFERENCE.read_text(encoding="utf-8")
        for required in (
            "validate-contract",
            "migrate-contract",
            "prepare-marketplace",
            "verify-marketplace",
            "result-schema-v1",
            "content_rules",
            "verify_existing",
            "catalog-driven",
            "-text whitespace=cr-at-eol",
            "ClawHub",
        ):
            with self.subTest(required=required):
                self.assertIn(required, content)
        self.assertNotIn(
            "python ./my-gpt-plugin/scripts/build_marketplace_release.py",
            content,
        )

    def test_guides_preserve_local_staging_and_publication_boundaries(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (COMMAND_REFERENCE, USER_GUIDE, TECHNICAL_REFERENCE)
        )
        for required in (
            "catalog-driven CI",
            "nested Git worktree",
            "GitHub marketplace publication",
            "GitHub Release",
            "ClawHub publication",
            "universal-directory submission",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)


if __name__ == "__main__":
    unittest.main()
