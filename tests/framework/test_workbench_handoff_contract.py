from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from obvious_one_plugin_framework.plugin_authoring import extract_archive, inventory_archive
from obvious_one_plugin_framework.workbench_handoff import (
    HANDOFF_CONTRACT,
    HANDOFF_SCHEMA,
    BaselineIdentity,
    baseline_identity_from_archive,
    canonical_json_bytes,
    validate_canonical_handoff,
    validate_update_baseline,
)


class WorkbenchHandoffContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _package(
        self,
        *,
        operation: str = "create",
        requirements: list[dict[str, str]] | None = None,
        artifact_requirements: list[str] | None = None,
        source: bytes = b"# Approved\r\nRequirement alpha\r\nSecond line\r\n",
        supporting_source: bytes | None = None,
    ):
        records = requirements if requirements is not None else [
            {
                "id": "D-01",
                "source": "approved.md#d-01",
                "verbatim": "Requirement alpha\r\nSecond line",
            }
        ]
        if operation == "update":
            records = [dict(record, change=record.get("change", "modify")) for record in records]
        handoff = {
            "schema": HANDOFF_SCHEMA,
            "operation": operation,
            "approval": {
                "state": "approved",
                "specification_version": "v1",
                "confirmed_by": "decision owner",
                "evidence": "owner approved",
            },
            "approved_specification": {
                "file": "approved.md",
                "id": "SPEC-v1",
                "state": "approved",
                "version": "v1",
            },
            "approved_design_statement": {"file": "approved.md", "id": "DS-v1", "state": "approved", "version": "v1"},
            "workflow_definitions_and_instruction_modules": [],
            "reference_material_inventory_evaluation_and_usage_map": [],
            "application_invariants_and_hitl_checkpoints": [],
            "deterministic_operation_candidates": [],
            "tool_data_runtime_and_service_requirements": {"runtime_scope": "OPENAI_ONLY_PHASE_ONE"},
            "acceptance_criteria_and_representative_scenarios": [],
            "rights_and_redistribution_decisions": {"normalization_authority": "format-only"},
            "explicit_exclusions": [],
            "unresolved_owner_decisions": [],
            "requirements": records,
        }
        if operation == "update":
            handoff["baseline"] = {
                "plugin_id": "sample-plugin",
                "version": "1.0.0",
                "archive_sha256": "a" * 64,
            }
            handoff["baseline_preservation"] = {
                "preserve_unaffected_members": True,
                "removal_requires_requirement": True,
                "identity_must_match": True,
            }
        handoff_bytes = canonical_json_bytes(handoff)
        manifest = {
            "package_schema_version": 1,
            "package_kind": "normalized-workbench-handoff",
            "handoff_contract": HANDOFF_CONTRACT,
            "operation": operation,
            "runtime_scope": "OPENAI_ONLY_PHASE_ONE",
            "gate": "READY FOR WORKBENCH",
            "artifacts": [{
                "file": "approved.md",
                "id": "SPEC-v1",
                "provenance": "approved design",
                "requirements": artifact_requirements if artifact_requirements is not None else [record["id"] for record in records],
                "role": "approved_specification",
                "sha256": sha256(source).hexdigest(),
                "size": len(source),
                "state": "approved",
                "version": "v1",
            }],
            "supporting_files": [] if supporting_source is None else [{
                "file": "supporting.md",
                "sha256": sha256(supporting_source).hexdigest(),
                "size": len(supporting_source),
            }],
            "canonical_handoff": {
                "file": "workbench-handoff.json",
                "sha256": sha256(handoff_bytes).hexdigest(),
                "size": len(handoff_bytes),
            },
        }
        members = {
            "approved.md": source,
            "workbench-handoff.json": handoff_bytes,
            "package-manifest.json": canonical_json_bytes(manifest),
        }
        if supporting_source is not None:
            members["supporting.md"] = supporting_source
        archive_path = self.root / f"{operation}-{len(list(self.root.glob('*.zip')))}.zip"
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, payload in members.items():
                archive.writestr(name, payload)
        extracted = self.root / f"extracted-{len(list(self.root.glob('extracted-*')))}"
        inventory = extract_archive(archive_path, extracted)
        return manifest, handoff, inventory, extracted

    def _validate(self, manifest, handoff, inventory, extracted, expected_operation=None):
        return validate_canonical_handoff(
            manifest,
            handoff,
            inventory,
            extracted,
            expected_operation=expected_operation,
        )

    def test_v11_create_requires_matching_contract_operation_and_exact_requirements(self) -> None:
        manifest, handoff, inventory, extracted = self._package()
        manifest["handoff_contract"] = "UNKNOWN"
        handoff["operation"] = "update"
        handoff.pop("requirements")

        result = self._validate(manifest, handoff, inventory, extracted, "create")

        self.assertEqual(result.status, "FAIL")
        self.assertIn("handoff.contract_mismatch", result.diagnostics)
        self.assertIn("handoff.operation_mismatch", result.diagnostics)
        self.assertIn("requirements.explicit_records_required", result.diagnostics)

    def test_v11_requirement_keeps_arbitrary_id_and_matches_utf8_bytes_without_newline_translation(self) -> None:
        source = "# 核准\r\n精確需求甲\r\n第二行\r\n".encode("utf-8")
        record = {"id": "IM-09/甲", "source": "approved.md#im-09", "verbatim": "精確需求甲\r\n第二行"}
        manifest, handoff, inventory, extracted = self._package(requirements=[record], source=source)

        result = self._validate(manifest, handoff, inventory, extracted, "create")

        self.assertEqual(result.status, "PASS")
        self.assertEqual(handoff["requirements"][0], record)

        changed = deepcopy(handoff)
        changed["requirements"][0]["verbatim"] = "精確需求甲\n第二行"
        mismatch = self._validate(manifest, changed, inventory, extracted, "create")
        self.assertIn("requirements.text_mismatch:IM-09/甲", mismatch.diagnostics)

    def test_v11_rejects_duplicate_missing_mismatched_and_unindexed_requirements(self) -> None:
        cases = []
        base = {"id": "D-01", "source": "approved.md#d", "verbatim": "Requirement alpha"}
        cases.append(([base, deepcopy(base)], ["D-01"], "requirements.duplicate_id:D-01"))
        cases.append(([dict(base, source="missing.md#d")], ["D-01"], "requirements.source_missing:D-01"))
        cases.append(([dict(base, verbatim="not approved")], ["D-01"], "requirements.text_mismatch:D-01"))
        cases.append(([base], [], "requirements.artifact_binding_missing:D-01"))

        for records, bindings, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                manifest, handoff, inventory, extracted = self._package(
                    requirements=records,
                    artifact_requirements=bindings,
                )
                result = self._validate(manifest, handoff, inventory, extracted)
                self.assertIn(diagnostic, result.diagnostics)

    def test_v11_requires_complete_semantic_fields_and_owner_decision_shape(self) -> None:
        manifest, handoff, inventory, extracted = self._package()
        handoff.pop("approved_design_statement")
        handoff["unresolved_owner_decisions"] = [{"decision_id": "OD-1", "blocking": False}]

        result = self._validate(manifest, handoff, inventory, extracted)

        self.assertIn("handoff.semantic_field_missing:approved_design_statement", result.diagnostics)
        self.assertIn("owner_decisions.invalid:0", result.diagnostics)

    def test_v11_requirement_source_must_be_its_indexing_artifact_not_supporting_material(self) -> None:
        supporting = b"Requirement alpha\r\nSecond line\r\n"
        manifest, handoff, inventory, extracted = self._package(supporting_source=supporting)
        handoff["requirements"][0]["source"] = "supporting.md#d-01"

        result = self._validate(manifest, handoff, inventory, extracted)

        self.assertIn("requirements.source_not_artifact:D-01", result.diagnostics)

    def test_v11_update_requires_change_baseline_and_preservation_contract(self) -> None:
        manifest, handoff, inventory, extracted = self._package(operation="update")
        handoff["requirements"][0].pop("change")
        handoff.pop("baseline")
        handoff.pop("baseline_preservation")

        result = self._validate(manifest, handoff, inventory, extracted, "update")

        self.assertIn("requirements.change_required:D-01", result.diagnostics)
        self.assertIn("baseline.required_for_update", result.diagnostics)
        self.assertIn("baseline.preservation_required", result.diagnostics)
        self.assertEqual(validate_update_baseline(handoff, None), ("baseline.required_for_update",))

    def test_v11_rejects_remove_preserve_conflict_and_unbound_removal(self) -> None:
        records = [
            {"id": "D-01", "source": "approved.md", "verbatim": "Requirement alpha", "change": "remove"},
            {"id": "D-01", "source": "approved.md", "verbatim": "Requirement alpha", "change": "preserve"},
        ]
        manifest, handoff, inventory, extracted = self._package(
            operation="update",
            requirements=records,
            artifact_requirements=[],
        )

        result = self._validate(manifest, handoff, inventory, extracted, "update")

        self.assertIn("requirements.change_conflict:D-01", result.diagnostics)
        self.assertIn("requirements.removal_unbound:D-01", result.diagnostics)

    def test_baseline_identity_supports_flat_and_wrapped_plugins_but_hashes_supplied_archive(self) -> None:
        plugin = canonical_json_bytes({"name": "sample-plugin", "version": "1.0.0"})
        flat = self.root / "flat.zip"
        wrapped = self.root / "wrapped.zip"
        with zipfile.ZipFile(flat, "w") as archive:
            archive.writestr("plugin.json", plugin)
        with zipfile.ZipFile(wrapped, "w") as archive:
            archive.writestr("sample-plugin/plugin.json", plugin)

        flat_identity = baseline_identity_from_archive(flat)
        wrapped_identity = baseline_identity_from_archive(wrapped)

        self.assertEqual((flat_identity.plugin_id, flat_identity.version), ("sample-plugin", "1.0.0"))
        self.assertEqual((wrapped_identity.plugin_id, wrapped_identity.version), ("sample-plugin", "1.0.0"))
        self.assertEqual(flat_identity.envelope_profile, "LEGACY_FLAT")
        self.assertEqual(wrapped_identity.envelope_profile, "PORTABLE_SINGLE_DIRECTORY")
        self.assertNotEqual(flat_identity.archive_sha256, wrapped_identity.archive_sha256)
        self.assertEqual(flat_identity.archive_sha256, inventory_archive(flat).archive_sha256)

        handoff = {
            "baseline": {
                "plugin_id": "different-plugin",
                "version": "9.0.0",
                "archive_sha256": "0" * 64,
            }
        }
        self.assertEqual(
            validate_update_baseline(handoff, flat_identity),
            ("baseline.archive_sha256_mismatch", "baseline.identity_mismatch"),
        )


if __name__ == "__main__":
    unittest.main()
