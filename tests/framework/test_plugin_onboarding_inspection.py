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
    load_package_metadata,
)
from obvious_one_plugin_framework.plugin_onboarding.inspection import (
    inspect_plugin_builder_package,
)
from tests.framework.plugin_onboarding_fixtures import (
    canonical_bytes,
    write_plugin_builder_fixture,
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
        }
        expected = {
            "portable": "plugin_tree_invalid",
            "compatibility": "plugin_tree_invalid",
            "development": "development_import_forbidden",
            "credential": "credential_material_forbidden",
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
