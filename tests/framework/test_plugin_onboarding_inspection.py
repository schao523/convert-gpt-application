from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import stat
import tempfile
import unittest
import warnings
import zipfile

from obvious_one_plugin_framework import plugin_authoring
from obvious_one_plugin_framework.plugin_onboarding.contract import (
    OnboardingError,
    load_legacy_plugin_builder_adoption,
    load_onboarding_metadata,
    load_package_metadata,
)
from obvious_one_plugin_framework.plugin_onboarding.inspection import (
    inspect_legacy_plugin_archive,
    inspect_legacy_plugin_builder_package,
    inspect_workbench_repaired_package,
    inspect_plugin_builder_package,
)
from obvious_one_plugin_framework.plugin_onboarding import (
    load_repair_contract,
    repair_delegated_reference_archive,
)
from tests.framework.plugin_onboarding_fixtures import (
    canonical_bytes,
    rebuild_legacy_plugin_builder_fixture,
    write_plugin_builder_fixture,
    write_legacy_adoption,
    write_legacy_plugin_builder_fixture,
    write_legacy_repair_fixture,
    write_runtime_evidence_bundle,
)
from tests.framework.test_plugin_authoring_tools import bundled_tool


class PluginOnboardingInspectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def inspect(self, fixture, *, evidence: Path | None = None):
        return inspect_plugin_builder_package(
            fixture.archive,
            load_package_metadata(fixture.metadata),
            evidence=evidence,
        )

    def rewrite_metadata(self, fixture, mutate) -> None:
        payload = json.loads(fixture.metadata.read_text(encoding="utf-8"))
        mutate(payload)
        fixture.metadata.write_bytes(canonical_bytes(payload))

    def rewrite_member_and_manifest(self, fixture, mutate) -> None:
        def update(payload) -> None:
            mutate(payload["members"][0])
            payload["member_manifest_sha256"] = sha256(
                canonical_bytes(payload["members"])
            ).hexdigest()

        self.rewrite_metadata(fixture, update)

    def assert_failure(self, callable_, code: str) -> None:
        with self.assertRaises(OnboardingError) as caught:
            callable_()
        self.assertEqual(caught.exception.status, "FAIL")
        self.assertEqual(caught.exception.code, code)

    def test_v2_and_v3_packages_close_archive_members_candidate_and_manifests(self) -> None:
        for schema in ("plugin-builder-package-v2", "plugin-builder-package-v3"):
            with self.subTest(schema=schema):
                fixture = write_plugin_builder_fixture(self.root / schema, schema=schema)
                inspected = self.inspect(fixture)
                self.assertEqual(inspected.schema, "plugin-onboarding-inspection-v1")
                self.assertEqual(inspected.plugin_id, "sample-plugin")
                self.assertEqual(inspected.version, "1.2.3")
                self.assertEqual(inspected.package_state, "STATICALLY VERIFIED")
                self.assertEqual(inspected.archive_sha256, fixture.metadata_payload["archive_sha256"])
                self.assertEqual(inspected.candidate_sha256, fixture.metadata_payload["candidate_sha256"])
                self.assertEqual(inspected.verification_sha256, "2" * 64)
                self.assertEqual(inspected.members, load_package_metadata(fixture.metadata).members)

    def test_legacy_inspection_separates_producer_claims_from_observation(self) -> None:
        fixture = write_legacy_repair_fixture(self.root / "legacy")
        inspected = inspect_legacy_plugin_archive(fixture.archive)
        self.assertEqual(inspected.input_profile, "PLUGIN_BUILDER_CANDIDATE_V1")
        self.assertEqual(inspected.archive_sha256, plugin_authoring.inventory_archive(fixture.archive).archive_sha256)
        self.assertEqual(inspected.producer_claims["w1_state"], "APPROVED")
        self.assertEqual(inspected.producer_claims["w2_state"], "APPROVED")
        self.assertEqual(inspected.producer_evidence_states["verification"], "NOT VERIFIED")
        self.assertEqual(set(inspected.evidence_states.values()), {"NOT VERIFIED"})
        self.assertIsNone(inspected.candidate_sha256)
        self.assertIsNone(inspected.verification_sha256)

    def inspect_legacy_builder(self, fixture):
        return inspect_legacy_plugin_builder_package(
            fixture.archive,
            load_legacy_plugin_builder_adoption(fixture.adoption),
        )

    def test_deterministic_content_v2_adoption_closes_without_runtime_promotion(self) -> None:
        fixture = write_legacy_plugin_builder_fixture(self.root / "legacy-builder")

        inspected = self.inspect_legacy_builder(fixture)

        self.assertEqual(inspected.input_profile, "PLUGIN_BUILDER_DETERMINISTIC_CONTENT_V2")
        self.assertEqual(inspected.plugin_id, "sample-plugin")
        self.assertEqual(inspected.version, "1.2.3")
        self.assertEqual(inspected.package_state, "STATICALLY VERIFIED")
        self.assertIsNone(inspected.candidate_sha256)
        self.assertIsNone(inspected.verification_sha256)
        self.assertEqual(inspected.approved_executable_files, ("scripts/helper.py",))
        self.assertEqual(inspected.approved_dependency_files, ("requirements.txt",))
        self.assertEqual(inspected.executable_files, ("scripts/helper.py",))
        self.assertEqual(inspected.dependency_files, ("requirements.txt",))
        self.assertEqual(set(inspected.evidence_states.values()), {"NOT VERIFIED"})
        self.assertEqual(inspected.runtime_realization_state, "NOT VERIFIED")
        self.assertEqual(inspected.evidence_bundle_state, "NOT VERIFIED")
        self.assertEqual(inspected.producer_claims["content_manifest_format"], "deterministic-content-manifest-v2")
        self.assertEqual(inspected.producer_claims["candidate_manifest_format"], "candidate-content-manifest-v2")
        self.assertEqual(inspected.producer_claims["verification_stage"], "PRE_W2")
        self.assertEqual(inspected.producer_claims["blocking_failures"], 0)

    def test_legacy_adoption_archive_and_internal_hashes_are_non_transferable(self) -> None:
        fixture = write_legacy_plugin_builder_fixture(self.root / "legacy-hashes")
        cases = (
            ({"archive_sha256": "f" * 64}, "archive_sha256_mismatch"),
            ({"member_manifest_sha256": "f" * 64}, "member_manifest_sha256_mismatch"),
            ({"content_tree_sha256": "f" * 64}, "content_tree_sha256_mismatch"),
            ({"content_manifest_sha256": "f" * 64}, "content_manifest_sha256_mismatch"),
            ({"candidate_manifest_sha256": "f" * 64}, "candidate_manifest_sha256_mismatch"),
            ({"verification_report_sha256": "f" * 64}, "verification_report_sha256_mismatch"),
        )
        for index, (overrides, suffix) in enumerate(cases):
            with self.subTest(suffix=suffix):
                adoption = write_legacy_adoption(
                    self.root / f"legacy-hash-{index}.json",
                    fixture,
                    overrides=overrides,
                )
                self.assert_failure(
                    lambda adoption=adoption: inspect_legacy_plugin_builder_package(
                        fixture.archive,
                        load_legacy_plugin_builder_adoption(adoption),
                    ),
                    f"onboarding.inspection.{suffix}",
                )

    def test_legacy_content_manifest_must_close_every_other_archive_member(self) -> None:
        fixture = write_legacy_plugin_builder_fixture(self.root / "legacy-content-closure")
        manifest_path = fixture.candidate / "CONTENT-MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"] = manifest["files"][:-1]
        manifest["file_count_excluding_manifest"] -= 1
        manifest_path.write_bytes(canonical_bytes(manifest))
        fixture = rebuild_legacy_plugin_builder_fixture(
            fixture,
            regenerate_candidate_manifest=False,
            regenerate_content_manifest=False,
        )

        self.assert_failure(
            lambda: self.inspect_legacy_builder(fixture),
            "onboarding.inspection.content_manifest_members_mismatch",
        )

    def test_legacy_candidate_manifest_exclusions_are_enforced(self) -> None:
        fixture = write_legacy_plugin_builder_fixture(self.root / "legacy-candidate-exclusions")
        candidate_path = fixture.candidate / "docs" / "candidate-content-manifest.json"
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidate["self_excluded"] = False
        candidate_path.write_bytes(canonical_bytes(candidate))
        fixture = rebuild_legacy_plugin_builder_fixture(
            fixture,
            regenerate_candidate_manifest=False,
            regenerate_content_manifest=True,
        )

        self.assert_failure(
            lambda: self.inspect_legacy_builder(fixture),
            "onboarding.inspection.candidate_manifest_exclusions_invalid",
        )

    def test_legacy_verification_identity_must_match_the_manifests(self) -> None:
        fixture = write_legacy_plugin_builder_fixture(self.root / "legacy-verification")
        report_path = fixture.candidate / "docs" / "verification-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["plugin_identity"] = "other-plugin"
        report_path.write_bytes(canonical_bytes(report))
        fixture = rebuild_legacy_plugin_builder_fixture(fixture)

        self.assert_failure(
            lambda: self.inspect_legacy_builder(fixture),
            "onboarding.inspection.verification_report_identity_mismatch",
        )

    def test_legacy_authority_mixing_and_unknown_internal_formats_fail_closed(self) -> None:
        mixed = write_legacy_plugin_builder_fixture(self.root / "legacy-mixed")
        (mixed.candidate / "PLUGIN-BUILDER-MANIFEST.json").write_bytes(
            canonical_bytes({"schema": "plugin-builder-candidate-manifest-v3"})
        )
        mixed = rebuild_legacy_plugin_builder_fixture(mixed)
        self.assert_failure(
            lambda: self.inspect_legacy_builder(mixed),
            "onboarding.inspection.authority_ambiguous",
        )

        unknown = write_legacy_plugin_builder_fixture(self.root / "legacy-unknown")
        content_path = unknown.candidate / "CONTENT-MANIFEST.json"
        content = json.loads(content_path.read_text(encoding="utf-8"))
        content["format"] = "deterministic-content-manifest-v1"
        content_path.write_bytes(canonical_bytes(content))
        unknown = rebuild_legacy_plugin_builder_fixture(
            unknown,
            regenerate_candidate_manifest=False,
            regenerate_content_manifest=False,
        )
        self.assert_failure(
            lambda: self.inspect_legacy_builder(unknown),
            "onboarding.inspection.content_manifest_invalid",
        )

    def test_legacy_approved_executable_and_dependency_sets_must_match_observation(self) -> None:
        fixture = write_legacy_plugin_builder_fixture(self.root / "legacy-approved-paths")
        cases = (
            ({"executable_files": []}, "executable_files_mismatch"),
            ({"dependency_files": []}, "dependency_files_mismatch"),
        )
        for index, (overrides, suffix) in enumerate(cases):
            with self.subTest(suffix=suffix):
                adoption = write_legacy_adoption(
                    self.root / f"legacy-paths-{index}.json",
                    fixture,
                    overrides=overrides,
                )
                self.assert_failure(
                    lambda adoption=adoption: inspect_legacy_plugin_builder_package(
                        fixture.archive,
                        load_legacy_plugin_builder_adoption(adoption),
                    ),
                    f"onboarding.inspection.{suffix}",
                )

    def test_legacy_manifest_pair_allows_later_omissions_but_not_contradictions(self) -> None:
        omitted = write_legacy_plugin_builder_fixture(self.root / "legacy-omitted")
        portable_path = omitted.candidate / "plugin.json"
        portable = json.loads(portable_path.read_text(encoding="utf-8"))
        interface = portable["extensions"]["com.openai"]["interface"]
        for field in ("longDescription", "developerName", "category", "capabilities"):
            interface.pop(field)
        portable_path.write_bytes(canonical_bytes(portable))
        omitted = rebuild_legacy_plugin_builder_fixture(omitted)
        inspected = self.inspect_legacy_builder(omitted)
        self.assertEqual(inspected.manifest_identity["long_description"], "A portable sample plugin for onboarding tests.")

        contradictory = write_legacy_plugin_builder_fixture(self.root / "legacy-contradictory")
        compatibility_path = contradictory.candidate / ".codex-plugin" / "plugin.json"
        compatibility = json.loads(compatibility_path.read_text(encoding="utf-8"))
        compatibility["description"] = "Contradictory description"
        compatibility_path.write_bytes(canonical_bytes(compatibility))
        contradictory = rebuild_legacy_plugin_builder_fixture(contradictory)
        self.assert_failure(
            lambda: self.inspect_legacy_builder(contradictory),
            "onboarding.inspection.manifest_pair_mismatch",
        )

    def test_legacy_public_content_scan_rejects_development_imports_and_secrets(self) -> None:
        cases = (
            ("development.py", b"import obvious_one_plugin_framework\n", "development_import_forbidden"),
            ("secret.txt", b"api_key = 'not-for-publication'\n", "credential_material_forbidden"),
        )
        for filename, content, suffix in cases:
            with self.subTest(filename=filename):
                fixture = write_legacy_plugin_builder_fixture(self.root / filename)
                path = fixture.candidate / "tools" / filename
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(content)
                fixture = rebuild_legacy_plugin_builder_fixture(fixture)
                adoption_payload = json.loads(fixture.adoption.read_text(encoding="utf-8"))
                if filename.endswith(".py"):
                    adoption_payload["executable_files"].append(f"tools/{filename}")
                    fixture.adoption.write_bytes(canonical_bytes(adoption_payload))
                self.assert_failure(
                    lambda fixture=fixture: self.inspect_legacy_builder(fixture),
                    f"onboarding.inspection.{suffix}",
                )

    def test_repaired_inspection_closes_workbench_metadata_without_builder_claims(self) -> None:
        fixture = write_legacy_repair_fixture(self.root / "repair")
        contract_path = self.root / "repair.json"
        contract_path.write_bytes(canonical_bytes(fixture.contract_payload))
        repaired = repair_delegated_reference_archive(
            fixture.archive,
            load_repair_contract(contract_path),
            self.root / "candidate.zip",
            self.root / "metadata.json",
        )
        inspected = inspect_workbench_repaired_package(
            repaired.archive, load_onboarding_metadata(repaired.metadata)
        )
        self.assertEqual(inspected.input_profile, "WORKBENCH_REPAIRED_PLUGIN_V1")
        self.assertEqual(inspected.producer_claims["verification_state"], "NOT VERIFIED")
        self.assertIsNone(inspected.candidate_sha256)
        self.assertIsNone(inspected.verification_sha256)
        self.assertEqual(set(inspected.evidence_states.values()), {"NOT VERIFIED"})

    def test_repaired_metadata_source_digest_is_bound_to_repair_manifest(self) -> None:
        fixture = write_legacy_repair_fixture(self.root / "repair-provenance")
        contract_path = self.root / "repair-provenance.json"
        contract_path.write_bytes(canonical_bytes(fixture.contract_payload))
        repaired = repair_delegated_reference_archive(
            fixture.archive,
            load_repair_contract(contract_path),
            self.root / "provenance-candidate.zip",
            self.root / "provenance-metadata.json",
        )
        payload = json.loads(repaired.metadata.read_text(encoding="utf-8"))
        payload["source_archive_sha256"] = "f" * 64
        repaired.metadata.write_bytes(canonical_bytes(payload))

        self.assert_failure(
            lambda: inspect_workbench_repaired_package(
                repaired.archive, load_onboarding_metadata(repaired.metadata)
            ),
            "onboarding.inspection.source_archive_sha256_mismatch",
        )

    def test_repaired_v2_metadata_revalidates_and_restores_tool_declarations(self) -> None:
        fixture = write_legacy_repair_fixture(self.root / "repair-tools")
        contract_path = self.root / "repair-tools.json"
        contract_path.write_bytes(canonical_bytes(fixture.contract_payload))
        repaired = repair_delegated_reference_archive(
            fixture.archive,
            load_repair_contract(contract_path),
            self.root / "tool-base.zip",
            self.root / "tool-base-metadata.json",
        )
        tree = self.root / "tool-tree"
        plugin_authoring.extract_archive(repaired.archive, tree)
        (tree / "tools").mkdir()
        (tree / "tools" / "normalize.py").write_bytes(b"print('ok')\n")
        tool = bundled_tool()
        binding = {
            "tool_id": tool["id"],
            "contract_sha256": sha256(canonical_bytes(tool)).hexdigest(),
            "files": tool["files"],
            "skills": tool["skill_bindings"],
            "dependencies": tool["dependencies"],
        }
        repair_path = tree / "WORKBENCH-REPAIR-MANIFEST.json"
        repair_payload = json.loads(repair_path.read_text(encoding="utf-8"))
        repair_payload["tool_bindings"] = [binding]
        repair_payload["tool_contracts"] = [tool]
        repair_path.write_bytes(canonical_bytes(repair_payload))
        archive = self.root / "tool-candidate.zip"
        archive_sha256 = plugin_authoring.write_deterministic_zip(tree, archive)
        inventory = plugin_authoring.inventory_archive(archive)
        metadata_payload = json.loads(repaired.metadata.read_text(encoding="utf-8"))
        metadata_payload.update(
            {
                "schema": "workbench-repaired-plugin-v2",
                "archive_sha256": archive_sha256,
                "member_manifest_sha256": sha256(
                    canonical_bytes([asdict(member) for member in inventory.members])
                ).hexdigest(),
                "content_tree_sha256": plugin_authoring.tree_sha256(tree),
                "members": [asdict(member) for member in inventory.members],
                "input_profile": "PLUGIN_BUILDER_VERSIONED_LEGACY_V1",
                "repair_manifest_sha256": next(
                    member.sha256
                    for member in inventory.members
                    if member.path == "WORKBENCH-REPAIR-MANIFEST.json"
                ),
                "tool_bindings": [binding],
                "tool_contracts_sha256": sha256(canonical_bytes([tool])).hexdigest(),
                "offline_validators": [],
                "offline_validators_sha256": sha256(canonical_bytes([])).hexdigest(),
            }
        )
        repair_payload = json.loads(repair_path.read_text(encoding="utf-8"))
        repair_payload["offline_validators"] = []
        repair_path.write_bytes(canonical_bytes(repair_payload))
        archive_sha256 = plugin_authoring.write_deterministic_zip(tree, archive)
        inventory = plugin_authoring.inventory_archive(archive)
        metadata_payload["archive_sha256"] = archive_sha256
        metadata_payload["member_manifest_sha256"] = sha256(
            canonical_bytes([asdict(member) for member in inventory.members])
        ).hexdigest()
        metadata_payload["content_tree_sha256"] = plugin_authoring.tree_sha256(tree)
        metadata_payload["members"] = [asdict(member) for member in inventory.members]
        metadata_payload["repair_manifest_sha256"] = next(
            member.sha256
            for member in inventory.members
            if member.path == "WORKBENCH-REPAIR-MANIFEST.json"
        )
        metadata_path = self.root / "tool-metadata.json"
        metadata_path.write_bytes(canonical_bytes(metadata_payload))

        inspected = inspect_workbench_repaired_package(
            archive,
            load_onboarding_metadata(metadata_path),
        )

        self.assertEqual(inspected.tool_contracts[0]["id"], "normalize-input")
        self.assertEqual(inspected.tool_bindings[0]["tool_id"], "normalize-input")
        self.assertEqual(inspected.executable_files, ("tools/normalize.py",))

    def test_repaired_v2_metadata_restores_hash_bound_offline_validator_files(self) -> None:
        fixture = write_legacy_repair_fixture(self.root / "repair-offline")
        contract_path = self.root / "repair-offline.json"
        contract_path.write_bytes(canonical_bytes(fixture.contract_payload))
        repaired = repair_delegated_reference_archive(
            fixture.archive,
            load_repair_contract(contract_path),
            self.root / "offline-base.zip",
            self.root / "offline-base-metadata.json",
        )
        tree = self.root / "offline-tree"
        plugin_authoring.extract_archive(repaired.archive, tree)
        (tree / "scripts").mkdir()
        (tree / "scripts" / "validate.py").write_bytes(b"print('ok')\n")
        validator = {
            "id": "package-validator",
            "files": ["scripts/validate.py"],
            "runtime_role": "OFFLINE_PACKAGE_VALIDATION_ONLY",
            "required": False,
            "installed_runtime_callable": False,
            "source_contract_sha256": "b" * 64,
        }
        repair_path = tree / "WORKBENCH-REPAIR-MANIFEST.json"
        repair_payload = json.loads(repair_path.read_text(encoding="utf-8"))
        repair_payload.update(
            {
                "tool_bindings": [],
                "tool_contracts": [],
                "offline_validators": [validator],
            }
        )
        repair_path.write_bytes(canonical_bytes(repair_payload))
        archive = self.root / "offline-candidate.zip"
        archive_sha256 = plugin_authoring.write_deterministic_zip(tree, archive)
        inventory = plugin_authoring.inventory_archive(archive)
        metadata_payload = json.loads(repaired.metadata.read_text(encoding="utf-8"))
        metadata_payload.update(
            {
                "schema": "workbench-repaired-plugin-v2",
                "archive_sha256": archive_sha256,
                "member_manifest_sha256": sha256(
                    canonical_bytes([asdict(member) for member in inventory.members])
                ).hexdigest(),
                "content_tree_sha256": plugin_authoring.tree_sha256(tree),
                "members": [asdict(member) for member in inventory.members],
                "input_profile": "PLUGIN_BUILDER_VERSIONED_LEGACY_V1",
                "repair_manifest_sha256": next(
                    member.sha256
                    for member in inventory.members
                    if member.path == "WORKBENCH-REPAIR-MANIFEST.json"
                ),
                "tool_bindings": [],
                "tool_contracts_sha256": sha256(canonical_bytes([])).hexdigest(),
                "offline_validators": [validator],
                "offline_validators_sha256": sha256(
                    canonical_bytes([validator])
                ).hexdigest(),
            }
        )
        metadata_path = self.root / "offline-metadata.json"
        metadata_path.write_bytes(canonical_bytes(metadata_payload))

        inspected = inspect_workbench_repaired_package(
            archive,
            load_onboarding_metadata(metadata_path),
        )

        self.assertEqual(inspected.offline_validator_files, ("scripts/validate.py",))
        self.assertEqual(inspected.tool_contracts, ())
        self.assertEqual(inspected.input_profile, "WORKBENCH_REPAIRED_PLUGIN_V2")
        self.assertEqual(set(inspected.evidence_states.values()), {"NOT VERIFIED"})

    def test_mixed_legacy_and_workbench_authorities_are_rejected(self) -> None:
        fixture = write_legacy_repair_fixture(self.root / "mixed")
        mixed = self.root / "mixed-tree"
        plugin_authoring.extract_archive(fixture.archive, mixed)
        (mixed / "WORKBENCH-REPAIR-MANIFEST.json").write_bytes(
            canonical_bytes({"schema": "workbench-repair-manifest-v1"})
        )
        archive = self.root / "mixed.zip"
        plugin_authoring.write_deterministic_zip(mixed, archive)
        self.assert_failure(
            lambda: inspect_legacy_plugin_archive(archive),
            "onboarding.inspection.authority_ambiguous",
        )

    def test_nested_nonempty_tool_bindings_preserve_exact_json_identity(self) -> None:
        binding = {
            "tool_id": "normalize-input",
            "contract_sha256": "a" * 64,
            "files": ["tools/normalize.py"],
            "skills": ["answering-requests"],
            "dependencies": [
                {"id": "python", "runtime_targets": ["Codex", "ChatGPT Work Local/Desktop"]}
            ],
        }
        files = write_plugin_builder_fixture(self.root / "base").candidate_files
        files["tools/normalize.py"] = b"print('ok')\n"
        fixture = write_plugin_builder_fixture(
            self.root / "nested-bindings",
            files=files,
            tool_bindings=[binding],
            tool_contracts=[bundled_tool()],
        )

        inspected = self.inspect(fixture)

        self.assertEqual(inspected.tool_bindings[0]["tool_id"], "normalize-input")
        dependency = inspected.tool_bindings[0]["dependencies"][0]
        self.assertEqual(
            dependency["runtime_targets"],
            ("Codex", "ChatGPT Work Local/Desktop"),
        )

    def test_member_manifest_digest_is_recomputed_canonically(self) -> None:
        fixture = write_plugin_builder_fixture(self.root / "stale")
        self.rewrite_metadata(
            fixture,
            lambda value: value.update({"member_manifest_sha256": "f" * 64}),
        )
        self.assert_failure(
            lambda: self.inspect(fixture),
            "onboarding.inspection.member_manifest_sha256_mismatch",
        )

    def test_producer_validation_states_must_be_clean_passes(self) -> None:
        for field in ("extracted_validation", "safety_validation"):
            with self.subTest(field=field):
                fixture = write_plugin_builder_fixture(self.root / field)
                self.rewrite_metadata(
                    fixture,
                    lambda value, field=field: value[field].update(
                        {"state": "FAIL", "diagnostics": ["producer failure"]}
                    ),
                )
                self.assert_failure(
                    lambda fixture=fixture: self.inspect(fixture),
                    f"onboarding.inspection.{field}_invalid",
                )

    def test_manifest_identity_interface_and_decision_fields_are_preserved(self) -> None:
        inspected = self.inspect(write_plugin_builder_fixture(self.root / "manifest"))
        self.assertEqual(
            inspected.manifest_identity,
            {
                "plugin_id": "sample-plugin",
                "version": "1.2.3",
                "author": "Example Developer",
                "description": "A portable sample plugin.",
                "display_name": "Sample Plugin",
                "short_description": "Portable sample",
                "long_description": "A portable sample plugin for onboarding tests.",
                "developer_name": "Example Developer",
                "category": "Productivity",
                "capabilities": ("Interactive", "Read"),
                "default_prompt": "Help me use this plugin.",
            },
        )
        self.assertEqual(inspected.manifest_profile, "PORTABLE_WITH_OPENAI_COMPATIBILITY")

    def test_tool_mcp_dependency_and_runtime_states_are_inventoried_without_execution(self) -> None:
        files = {
            **write_plugin_builder_fixture(self.root / "source").candidate_files,
        }
        files.update(
            {
                "mcp.json": canonical_bytes({"mcpServers": {"sample": {"type": "stdio", "command": "python", "args": ["tools/run.py"]}}}),
                ".mcp.json": canonical_bytes({"mcpServers": {"sample": {"command": "python", "args": ["tools/run.py"]}}}),
                "tools/run.py": b"print('not executed')\n",
                "requirements.txt": b"example-package==1.0\n",
            }
        )
        fixture = write_plugin_builder_fixture(self.root / "inventory", files=files)
        inspected = self.inspect(fixture)
        self.assertEqual(inspected.mcp_files, (".mcp.json", "mcp.json"))
        self.assertEqual(inspected.executable_files, ("tools/run.py",))
        self.assertEqual(inspected.dependency_files, ("requirements.txt",))
        self.assertEqual(inspected.runtime_realization_state, "NOT VERIFIED")
        self.assertEqual(inspected.executed_files, ())

    def test_no_evidence_keeps_all_installed_layers_not_verified(self) -> None:
        inspected = self.inspect(write_plugin_builder_fixture(self.root / "no-evidence"))
        self.assertTrue(inspected.evidence_states)
        self.assertEqual(set(inspected.evidence_states.values()), {"NOT VERIFIED"})

    def test_archive_and_metadata_tampering_fail_closed(self) -> None:
        mutations = (
            ("archive", lambda fixture: fixture.archive.write_bytes(fixture.archive.read_bytes() + b"x"), "archive_sha256_mismatch"),
            ("size", lambda fixture: self.rewrite_member_and_manifest(fixture, lambda member: member.update({"size": member["size"] + 1})), "archive_members_mismatch"),
            ("hash", lambda fixture: self.rewrite_member_and_manifest(fixture, lambda member: member.update({"sha256": "e" * 64})), "archive_members_mismatch"),
            ("candidate", lambda fixture: self.rewrite_metadata(fixture, lambda value: value["candidate_members"][0].update({"sha256": "d" * 64})), "candidate_members_mismatch"),
        )
        for name, mutate, suffix in mutations:
            with self.subTest(name=name):
                fixture = write_plugin_builder_fixture(self.root / name)
                mutate(fixture)
                self.assert_failure(
                    lambda fixture=fixture: self.inspect(fixture),
                    f"onboarding.inspection.{suffix}",
                )

    def test_manifest_development_import_and_credential_content_fail_closed(self) -> None:
        cases = {
            "portable": {"plugin.json": b"{}\n"},
            "compatibility": {".codex-plugin/plugin.json": b"{}\n"},
            "development": {"tools/run.py": b"import obvious_one_plugin_framework\n"},
            "credential": {"notes.txt": b"api_key = 'should-not-ship'\n"},
            "environment": {".env": b"SERVICE_TOKEN=should-not-ship\n"},
            "credential-file": {"credentials.json": b"{}\n"},
            "private-key-file": {"id_rsa": b"not-a-real-key\n"},
            "private-key-block": {
                "notes.md": b"-----BEGIN PRIVATE KEY-----\nnot-a-real-key\n"
            },
            "github-token": {
                "notes.md": b"ghp_abcdefghijklmnopqrstuvwxyz123456\n"
            },
            "aws-access-key": {"notes.md": b"AKIAABCDEFGHIJKLMNOP\n"},
        }
        expected = {
            "portable": "plugin_tree_invalid",
            "compatibility": "plugin_tree_invalid",
            "development": "development_import_forbidden",
            "credential": "credential_material_forbidden",
            "environment": "credential_material_forbidden",
            "credential-file": "credential_material_forbidden",
            "private-key-file": "credential_material_forbidden",
            "private-key-block": "credential_material_forbidden",
            "github-token": "credential_material_forbidden",
            "aws-access-key": "credential_material_forbidden",
        }
        baseline = write_plugin_builder_fixture(self.root / "baseline")
        base_files = baseline.candidate_files
        for name, changes in cases.items():
            with self.subTest(name=name):
                fixture = write_plugin_builder_fixture(
                    self.root / name,
                    files={**base_files, **changes},
                )
                self.assert_failure(
                    lambda fixture=fixture: self.inspect(fixture),
                    f"onboarding.inspection.{expected[name]}",
                )

    def test_unsafe_archive_forms_are_rejected_before_extraction(self) -> None:
        fixture = write_plugin_builder_fixture(self.root / "safe")
        cases = {
            "duplicate": [("sample-plugin/plugin.json", b"{}"), ("sample-plugin/plugin.json", b"{}")],
            "alias": [("sample-plugin/plugin.json", b"{}"), ("sample-plugin\\plugin.json", b"{}")],
            "casefold": [("sample-plugin/plugin.json", b"{}"), ("Sample-Plugin/plugin.json", b"{}")],
            "traversal": [("../plugin.json", b"{}")],
            "collision": [("sample-plugin/plugin.json", b"{}"), ("sample-plugin/plugin.json/file", b"{}")],
        }
        for name, members in cases.items():
            with self.subTest(name=name):
                archive_path = self.root / f"{name}.zip"
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    with zipfile.ZipFile(archive_path, "w") as archive:
                        for member, content in members:
                            archive.writestr(member, content)
                with self.assertRaises(OnboardingError) as caught:
                    inspect_plugin_builder_package(
                        archive_path,
                        load_package_metadata(fixture.metadata),
                    )
                self.assertTrue(caught.exception.code.startswith("onboarding.inspection.archive_"))

        link_path = self.root / "link.zip"
        with zipfile.ZipFile(link_path, "w") as archive:
            info = zipfile.ZipInfo("sample-plugin/link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, b"plugin.json")
        with self.assertRaises(OnboardingError) as caught:
            inspect_plugin_builder_package(link_path, load_package_metadata(fixture.metadata))
        self.assertEqual(caught.exception.code, "onboarding.inspection.archive_link_member")

        compressed_path = self.root / "unsupported-compression.zip"
        with zipfile.ZipFile(compressed_path, "w", compression=zipfile.ZIP_BZIP2) as archive:
            archive.writestr("sample-plugin/plugin.json", b"{}")
        with self.assertRaises(OnboardingError) as caught:
            inspect_plugin_builder_package(
                compressed_path, load_package_metadata(fixture.metadata)
            )
        self.assertEqual(
            caught.exception.code,
            "onboarding.inspection.archive_compression_unsupported",
        )

    def test_flat_archive_is_rejected_even_when_all_hashes_match(self) -> None:
        fixture = write_plugin_builder_fixture(self.root / "flat")
        flat_archive = self.root / "flat.zip"
        archive_sha = plugin_authoring.write_deterministic_zip(
            fixture.candidate, flat_archive
        )
        inventory = plugin_authoring.inventory_archive(flat_archive)

        def match_flat(payload) -> None:
            payload["archive_sha256"] = archive_sha
            payload["members"] = [asdict(member) for member in inventory.members]
            payload["member_manifest_sha256"] = sha256(
                canonical_bytes(payload["members"])
            ).hexdigest()

        self.rewrite_metadata(fixture, match_flat)
        self.assert_failure(
            lambda: inspect_plugin_builder_package(
                flat_archive, load_package_metadata(fixture.metadata)
            ),
            "onboarding.inspection.envelope_profile_mismatch",
        )

    def test_optional_evidence_mismatch_fails_and_never_promotes_runtime_state(self) -> None:
        fields = (
            "zip_sha256",
            "member_manifest_sha256",
            "candidate_sha256",
            "verification_sha256",
            "plan_sha256",
            "session_sha256",
            "operation_identities",
        )
        for field in fields:
            with self.subTest(field=field):
                fixture = write_plugin_builder_fixture(self.root / f"evidence-{field}")
                value: object = [] if field == "operation_identities" else "f" * 64
                if field == "operation_identities":
                    value = [{"operation_id": "stale", "sha256": "f" * 64}]
                overrides: dict[str, object] = {field: value}
                if field == "session_sha256":
                    overrides["evidence_states"] = {
                        "installation": "RUNTIME VERIFIED",
                        "skill_invocation": "NOT VERIFIED",
                        "capability_discovery": "NOT VERIFIED",
                        "operation_execution": "NOT VERIFIED",
                        "result_delivery": "NOT VERIFIED",
                        "conversation": "NOT VERIFIED",
                    }
                evidence = write_runtime_evidence_bundle(
                    self.root / f"{field}.zip",
                    fixture,
                    overrides=overrides,
                )
                with self.assertRaises(OnboardingError) as caught:
                    self.inspect(fixture, evidence=evidence)
                self.assertEqual(caught.exception.status, "FAIL")
                self.assertTrue(caught.exception.code.startswith("onboarding.inspection.evidence_"))

    def test_matching_static_evidence_preserves_only_directly_observed_states(self) -> None:
        fixture = write_plugin_builder_fixture(self.root / "matching")
        evidence = write_runtime_evidence_bundle(self.root / "matching.zip", fixture)
        inspected = self.inspect(fixture, evidence=evidence)
        self.assertEqual(set(inspected.evidence_states.values()), {"NOT VERIFIED"})
        self.assertEqual(inspected.evidence_bundle_state, "STATICALLY VERIFIED")


if __name__ == "__main__":
    unittest.main()
