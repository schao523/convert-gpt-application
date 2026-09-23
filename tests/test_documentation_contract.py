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

    def test_owner_and_technical_guides_route_commands_to_command_reference(self) -> None:
        link = "[Plugin and Framework Command Reference](PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md)"
        owner = " ".join(USER_GUIDE.read_text(encoding="utf-8").split())
        technical = " ".join(TECHNICAL_REFERENCE.read_text(encoding="utf-8").split())
        for content in (owner, technical):
            self.assertIn(link, content)
            self.assertIn("authoritative", content.lower())
            self.assertIn("commands", content.lower())
            self.assertIn("packaging", content.lower())
            self.assertIn("verification", content.lower())
            self.assertIn("marketplace operations", content.lower())

    def test_each_governed_document_preserves_its_publication_boundary(self) -> None:
        expectations = {
            AGENTS: (
                "marketplace mutation",
                "Git pushes",
                "GitHub Releases",
                "ClawHub",
                "external registry",
            ),
            COMMAND_REFERENCE: (
                "Commands that require explicit approval",
                "GitHub marketplace",
                "GitHub Release",
                "ClawHub",
                "universal OpenAI directory",
            ),
            USER_GUIDE: (
                "GitHub marketplace publication",
                "GitHub Release",
                "ClawHub publication",
                "universal-directory submission",
                "separate external actions",
            ),
            TECHNICAL_REFERENCE: (
                "GitHub marketplace publication",
                "GitHub Release",
                "ClawHub publication",
                "universal-directory submission",
                "separate explicit approval",
            ),
        }
        for path, required_fragments in expectations.items():
            content = path.read_text(encoding="utf-8")
            for required in required_fragments:
                with self.subTest(path=path.name, required=required):
                    self.assertIn(required, content)


if __name__ == "__main__":
    unittest.main()
