from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import shutil
import tempfile
from types import MappingProxyType
import unittest

from obvious_one_plugin_framework import plugin_authoring
from obvious_one_plugin_framework.plugin_onboarding.contract import (
    OnboardingError,
    PackageMember,
    load_package_metadata,
    load_publication_decisions,
)
from obvious_one_plugin_framework.plugin_onboarding.inspection import (
    inspect_plugin_builder_package,
)
from obvious_one_plugin_framework.plugin_onboarding.proposal import (
    build_onboarding_proposal,
)
from tests.framework.plugin_onboarding_fixtures import (
    canonical_bytes,
    write_plugin_builder_fixture,
    write_publication_decisions,
)


SOURCE_REPOSITORY = Path(__file__).resolve().parents[2]


class PluginOnboardingProposalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fixture = write_plugin_builder_fixture(self.root / "package")
        self.inspection = inspect_plugin_builder_package(
            self.fixture.archive,
            load_package_metadata(self.fixture.metadata),
        )
        self.decisions_path = write_publication_decisions(self.root / "decisions.json")
        self.decisions = load_publication_decisions(self.decisions_path)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def repository_fixture(self, name: str, *, codex_destination: str = "plugins/plugin-builder") -> Path:
        repository = self.root / name
        source = SOURCE_REPOSITORY / "applications" / "plugin-builder"
        shutil.copytree(source, repository / "applications" / "plugin-builder")
        catalog = {
            "schema_version": 2,
            "marketplace_id": "obvious-one",
            "applications": [
                {
                    "application_config": "applications/plugin-builder/conversion.json",
                    "distribution_contract": "applications/plugin-builder/openclaw/distribution.json",
                    "targets": {
                        "codex": {"mode": "build", "destination": codex_destination},
                        "openclaw": {"mode": "not_applicable"},
                    },
                }
            ],
        }
        (repository / "marketplaces").mkdir()
        (repository / "marketplaces" / "obvious-one.json").write_bytes(
            canonical_bytes(catalog)
        )
        return repository

    def assert_error(self, callable_, code: str, status: str = "FAIL") -> None:
        with self.assertRaises(OnboardingError) as caught:
            callable_()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(caught.exception.status, status)

    def test_proposal_is_path_independent_and_excludes_recorded_at_from_identity(self) -> None:
        first_repository = self.repository_fixture("repository-one")
        second_repository = self.repository_fixture("repository-two")
        later = replace(self.decisions, decision_recorded_at="2026-10-10T12:00:00+08:00")

        first = build_onboarding_proposal(self.inspection, self.decisions, first_repository)
        second = build_onboarding_proposal(self.inspection, later, second_repository)

        self.assertEqual(first.proposal_sha256, second.proposal_sha256)
        self.assertNotIn(str(first_repository), first.proposal_json())
        self.assertNotIn(str(second_repository), second.proposal_json())
        self.assertIn("2026-10-09T10:30:00+08:00", first.proposal_json())
        self.assertIn("2026-10-10T12:00:00+08:00", second.proposal_json())

    def test_proposal_is_codex_build_and_openclaw_not_applicable(self) -> None:
        proposal = build_onboarding_proposal(
            self.inspection, self.decisions, self.repository_fixture("targets")
        )
        self.assertEqual(
            proposal.catalog_entry["targets"],
            {
                "codex": {"mode": "build", "destination": "plugins/sample-plugin"},
                "openclaw": {"mode": "not_applicable"},
            },
        )
        self.assertEqual(proposal.application_path, "applications/sample-plugin")

    def test_proposal_preserves_builder_and_runtime_evidence_states(self) -> None:
        proposal = build_onboarding_proposal(
            self.inspection, self.decisions, self.repository_fixture("evidence")
        )
        self.assertEqual(proposal.builder_evidence["candidate_sha256"], self.inspection.candidate_sha256)
        self.assertEqual(proposal.builder_evidence["verification_sha256"], self.inspection.verification_sha256)
        self.assertEqual(
            proposal.builder_evidence["preflight_evidence"],
            {"manifest_profile": "PORTABLE_WITH_OPENAI_COMPATIBILITY", "state": "PASS"},
        )
        self.assertEqual(proposal.builder_evidence["command_evidence"], ())
        self.assertEqual(proposal.builder_evidence["fallback_activations"], ())
        self.assertEqual(
            proposal.builder_evidence["producer_evidence_states"],
            {
                "installed_skill_invocation": "NOT VERIFIED",
                "package_structure": "PASS",
            },
        )
        self.assertEqual(proposal.builder_evidence["tool_bindings"], ())
        self.assertRegex(proposal.builder_evidence["tool_contracts_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(proposal.builder_evidence["capabilities_sha256"], "3" * 64)
        self.assertEqual(proposal.builder_evidence["realizations_sha256"], "4" * 64)
        self.assertEqual(proposal.builder_evidence["adapter_registry_sha256"], "5" * 64)
        self.assertEqual(
            proposal.builder_evidence["generated_runtime_configuration_sha256"],
            "6" * 64,
        )
        self.assertEqual(proposal.builder_evidence["runtime_realizations"], ())
        self.assertEqual(proposal.runtime_evidence_states, self.inspection.evidence_states)
        self.assertEqual(set(proposal.runtime_evidence_states.values()), {"NOT VERIFIED"})

    def test_repository_paths_and_private_input_locations_never_enter_payload(self) -> None:
        repository = self.repository_fixture("private-owner-repository")
        inspection = replace(
            self.inspection,
            command_evidence=(
                MappingProxyType(
                    {
                        "tool_id": "sample",
                        "observed_argv": (r"C:\private\python.exe", "tool.py"),
                    }
                ),
            ),
        )
        proposal = build_onboarding_proposal(inspection, self.decisions, repository)
        payload = proposal.proposal_json()
        self.assertNotIn(str(self.root), payload)
        self.assertNotIn("private-owner-repository", payload)
        self.assertNotIn(str(self.fixture.archive), payload)
        self.assertNotIn(r"C:\\private\\python.exe", payload)
        self.assertIn("<absolute-path>", payload)

    def test_byte_identical_inputs_produce_identical_proposal_json_and_sha256(self) -> None:
        repository = self.repository_fixture("repeatable")
        first = build_onboarding_proposal(self.inspection, self.decisions, repository)
        second = build_onboarding_proposal(self.inspection, self.decisions, repository)
        self.assertEqual(first.proposal_sha256, second.proposal_sha256)
        self.assertEqual(first.proposal_json(), second.proposal_json())

    def test_publication_authority_license_identity_destination_and_notices_are_audited(self) -> None:
        repository = self.repository_fixture("authority")
        cases = (
            (replace(self.decisions, license="Apache-2.0"), "onboarding.decisions.unsupported_license", "FAIL"),  # type: ignore[arg-type]
            (replace(self.decisions, redistribution_approved=False), "onboarding.decisions.redistribution_approved_required", "BLOCKED"),  # type: ignore[arg-type]
            (replace(self.decisions, public_marketplace_approved=False), "onboarding.decisions.public_marketplace_approved_required", "BLOCKED"),  # type: ignore[arg-type]
            (replace(self.decisions, plugin_id="other-plugin"), "onboarding.proposal.plugin_identity_mismatch", "FAIL"),
            (replace(self.decisions, version="9.0.0"), "onboarding.proposal.version_mismatch", "FAIL"),
            (replace(self.decisions, author="Other Author"), "onboarding.proposal.author_mismatch", "FAIL"),
            (replace(self.decisions, codex_destination="../escape"), "onboarding.proposal.destination_invalid", "FAIL"),
            (replace(self.decisions, third_party_content="INCLUDED_WITH_PLUGIN_NOTICES"), "onboarding.proposal.third_party_notices_required", "FAIL"),  # type: ignore[arg-type]
        )
        for decisions, code, status in cases:
            with self.subTest(code=code):
                self.assert_error(
                    lambda decisions=decisions: build_onboarding_proposal(
                        self.inspection, decisions, repository
                    ),
                    code,
                    status,
                )

    def test_undeclared_executable_dependency_service_remote_asset_and_secret_findings_fail(self) -> None:
        repository = self.repository_fixture("findings")
        cases = (
            (replace(self.inspection, executable_files=("tools/run.py",)), "undeclared_executable"),
            (replace(self.inspection, dependency_files=("requirements.txt",)), "undeclared_dependency"),
            (replace(self.inspection, mcp_files=("mcp.json",)), "undeclared_external_service"),
            (
                replace(
                    self.inspection,
                    members=self.inspection.members
                    + (PackageMember("sample-plugin/assets/remote-assets.json", 2, "f" * 64),),
                ),
                "undeclared_remote_asset",
            ),
            (replace(self.inspection, diagnostics=("credential_material_forbidden",)), "secret_finding"),
        )
        for inspection, suffix in cases:
            with self.subTest(suffix=suffix):
                self.assert_error(
                    lambda inspection=inspection: build_onboarding_proposal(
                        inspection, self.decisions, repository
                    ),
                    f"onboarding.proposal.{suffix}",
                )

    def test_existing_application_requires_separate_update_design_without_mutation(self) -> None:
        repository = self.repository_fixture("existing-application")
        (repository / "applications" / "sample-plugin").mkdir()
        before = plugin_authoring.tree_sha256(repository)
        decisions = replace(self.decisions, version="9.0.0")
        inspection = replace(
            self.inspection,
            version="9.0.0",
            manifest_identity=MappingProxyType(
                {**self.inspection.manifest_identity, "version": "9.0.0"}
            ),
        )

        self.assert_error(
            lambda: build_onboarding_proposal(inspection, decisions, repository),
            "onboarding.existing_plugin_requires_update_design",
            "BLOCKED",
        )
        self.assertEqual(plugin_authoring.tree_sha256(repository), before)

    def test_existing_catalog_destination_requires_separate_update_design_without_mutation(self) -> None:
        repository = self.repository_fixture(
            "existing-catalog", codex_destination="plugins/sample-plugin"
        )
        before = plugin_authoring.tree_sha256(repository)

        self.assert_error(
            lambda: build_onboarding_proposal(
                self.inspection, self.decisions, repository
            ),
            "onboarding.existing_plugin_requires_update_design",
            "BLOCKED",
        )
        self.assertEqual(plugin_authoring.tree_sha256(repository), before)


if __name__ == "__main__":
    unittest.main()
