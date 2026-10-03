from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from obvious_one_plugin_framework.plugin_authoring import extract_archive
from obvious_one_plugin_framework.workbench_handoff import (
    canonical_json_bytes,
    classify_handoff_profile,
    normalize_handoff_archive,
)


def _member(content: bytes) -> dict[str, object]:
    return {"sha256": sha256(content).hexdigest(), "size": len(content)}


class WorkbenchHandoffNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def archive(self, name: str, members: dict[str, bytes]) -> Path:
        path = self.root / name
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as output:
            for member_name, content in sorted(members.items()):
                output.writestr(member_name, content)
        return path

    def extracted(self, name: str, members: dict[str, bytes]) -> Path:
        destination = self.root / f"{name}-tree"
        extract_archive(self.archive(f"{name}.zip", members), destination)
        return destination

    def v11(self, operation: str = "create") -> dict[str, bytes]:
        source = "Requirement D-01: retain exact UTF-8 text \u9177.\n".encode("utf-8")
        handoff: dict[str, object] = {
            "schema": "workbench-handoff-v1.1",
            "operation": operation,
            "approval": {"state": "approved", "confirmed_by": "owner", "evidence": "record"},
            "approved_specification": {"state": "approved", "file": "design.md", "id": "SPEC-1", "version": "1"},
            "approved_design_statement": {"state": "approved", "file": "design.md", "id": "DS-1", "version": "1"},
            "workflow_definitions_and_instruction_modules": [],
            "reference_material_inventory_evaluation_and_usage_map": [],
            "application_invariants_and_hitl_checkpoints": [],
            "deterministic_operation_candidates": [],
            "tool_data_runtime_and_service_requirements": {"runtime_scope": "OPENAI_ONLY_PHASE_ONE"},
            "acceptance_criteria_and_representative_scenarios": [],
            "rights_and_redistribution_decisions": {"normalization_authority": "format-only"},
            "explicit_exclusions": [],
            "requirements": [{"id": "D-01", "source": "design.md", "verbatim": source.decode("utf-8").rstrip("\n")}],
            "unresolved_owner_decisions": [],
        }
        if operation == "update":
            handoff["requirements"][0]["change"] = "modify"  # type: ignore[index]
            handoff["baseline"] = {"plugin_id": "sample", "version": "1.0.0", "archive_sha256": "a" * 64}
            handoff["baseline_preservation"] = {
                "preserve_unaffected_members": True,
                "removal_requires_requirement": True,
                "identity_must_match": True,
            }
        handoff_bytes = canonical_json_bytes(handoff)
        manifest = {
            "package_schema_version": 1,
            "package_kind": "normalized-workbench-handoff",
            "handoff_contract": "WORKBENCH_HANDOFF_V1_1",
            "operation": operation,
            "runtime_scope": "OPENAI_ONLY_PHASE_ONE",
            "artifacts": [{
                "file": "design.md", "id": "SPEC-1", "role": "approved_specification",
                "state": "approved", "version": "1", "provenance": "fixture",
                "requirements": ["D-01"], **_member(source),
            }],
            "supporting_files": [],
            "canonical_handoff": {"file": "workbench-handoff.json", **_member(handoff_bytes)},
        }
        return {
            "design.md": source,
            "workbench-handoff.json": handoff_bytes,
            "package-manifest.json": canonical_json_bytes(manifest),
        }

    def full(self, *, exact: bool = True) -> dict[str, bytes]:
        source = b"Requirement DAC-01: exact full-design authority.\n"
        statement = b"Approved design statement.\n"
        manifest: dict[str, object] = {
            "application": "Sample",
            "spec_version": "1.0",
            "gate": "READY FOR WORKBENCH",
            "approval_evidence": "owner approved",
            "artifacts": [
                {
                    "id": "SPEC-1", "file": "design.md", "version": "1.0", "state": "approved",
                    "provenance": "design assistant", "requirements": ["DAC-01"] if exact else "DAC-01",
                    "role": "approved_specification",
                },
                {
                    "id": "DS-1", "file": "statement.md", "version": "1.0", "state": "approved",
                    "provenance": "design assistant", "requirements": [],
                    "role": "approved_design_statement",
                },
            ],
            "requirements": [{"id": "DAC-01", "source": "design.md", "verbatim": "Requirement DAC-01: exact full-design authority."}] if exact else [],
            "unresolved_owner_decisions": [],
            "exclusions": [],
            "reserved_workbench_decisions": ["Skill architecture"],
            "readiness_note": "ready",
        }
        return {
            "design.md": source,
            "statement.md": statement,
            "handoff_manifest.json": canonical_json_bytes(manifest),
        }

    def delta(self) -> dict[str, bytes]:
        members = self.full()
        manifest = json.loads(members.pop("handoff_manifest.json"))
        manifest["requirements"][0]["change"] = "modify"
        manifest["baseline"] = {"plugin_id": "sample", "version": "1.0.0", "archive_sha256": "b" * 64}
        manifest["baseline_preservation"] = {
            "preserve_unaffected_members": True,
            "removal_requires_requirement": True,
            "identity_must_match": True,
        }
        members["delta_handoff_manifest.json"] = canonical_json_bytes(manifest)
        return members

    def legacy_workbench(self) -> dict[str, bytes]:
        source = b"RQ1 exact legacy requirement.\n"
        manifest = {
            "application_name": "Legacy",
            "specification_state": "approved",
            "approval_evidence": "owner approved",
            "gate_result": "APPROVED",
            "specification_version": "1",
            "included_artifacts": [{
                "artifact_id": "SPEC-1", "path": "legacy.md", "relation": "authoritative specification",
                "state": "approved", "version": "1", "provenance": "legacy", "requirements": "RQ1",
            }],
            "unresolved_owner_decisions": [],
        }
        return {"legacy.md": source, "workbench_handoff_manifest.json": canonical_json_bytes(manifest)}

    def test_every_supported_compatibility_profile_is_classified(self) -> None:
        legacy_canonical = deepcopy(self.v11())
        package = json.loads(legacy_canonical["package-manifest.json"])
        package.pop("handoff_contract")
        package.pop("operation")
        handoff = json.loads(legacy_canonical["workbench-handoff.json"])
        handoff.pop("schema")
        handoff.pop("operation")
        handoff.pop("requirements")
        legacy_canonical["workbench-handoff.json"] = canonical_json_bytes(handoff)
        package["canonical_handoff"] = {"file": "workbench-handoff.json", **_member(legacy_canonical["workbench-handoff.json"])}
        legacy_canonical["package-manifest.json"] = canonical_json_bytes(package)
        cases = {
            "v11-create": (self.v11(), "WORKBENCH_HANDOFF_V1_1"),
            "v11-update": (self.v11("update"), "WORKBENCH_HANDOFF_V1_1"),
            "canonical": (legacy_canonical, "CANONICAL_V1"),
            "legacy": (self.legacy_workbench(), "LEGACY_WORKBENCH_V1"),
            "full": (self.full(), "COOL_DESIGN_ASSISTANT_FULL_V1"),
            "delta": (self.delta(), "COOL_DESIGN_ASSISTANT_DELTA_V1"),
        }
        for name, (members, expected) in cases.items():
            with self.subTest(name=name):
                self.assertEqual(classify_handoff_profile(self.extracted(name, members)).profile, expected)

    def test_mixed_canonical_and_legacy_authorities_is_ambiguous_without_output(self) -> None:
        members = self.v11() | self.full()
        source = self.archive("mixed.zip", members)
        outcome = normalize_handoff_archive(source, self.root / "output", self.root / "output.zip")
        self.assertEqual((outcome.status, outcome.profile), ("BLOCKED", "AMBIGUOUS"))
        self.assertIn("profile.multiple_authorities", outcome.diagnostics)
        self.assertFalse((self.root / "output").exists())
        self.assertFalse((self.root / "output.zip").exists())

    def test_unknown_envelope_is_blocked_without_selecting_authority(self) -> None:
        outcome = normalize_handoff_archive(
            self.archive("unknown.zip", {"approved.md": b"approved"}), self.root / "output"
        )
        self.assertEqual((outcome.status, outcome.profile), ("BLOCKED", "UNKNOWN"))
        self.assertEqual(outcome.diagnostics, ("profile.unrecognized",))

    def test_full_design_legacy_requires_exact_requirement_records(self) -> None:
        outcome = normalize_handoff_archive(
            self.archive("full.zip", self.full(exact=False)), self.root / "output"
        )
        self.assertEqual(outcome.status, "BLOCKED")
        self.assertIn("requirements.explicit_records_required", outcome.diagnostics)
        self.assertFalse((self.root / "output").exists())

    def test_delta_legacy_requires_approved_baseline_and_preservation_contract(self) -> None:
        members = self.delta()
        manifest = json.loads(members["delta_handoff_manifest.json"])
        manifest.pop("baseline")
        members["delta_handoff_manifest.json"] = canonical_json_bytes(manifest)
        outcome = normalize_handoff_archive(self.archive("delta.zip", members), self.root / "output")
        self.assertEqual(outcome.status, "BLOCKED")
        self.assertIn("baseline.required_for_update", outcome.diagnostics)

    def test_v11_create_and_update_pass_through_after_validation(self) -> None:
        for operation in ("create", "update"):
            with self.subTest(operation=operation):
                source = self.archive(f"{operation}.zip", self.v11(operation))
                outcome = normalize_handoff_archive(source, self.root / operation, self.root / f"{operation}-out.zip")
                self.assertEqual(outcome.status, "PASS", outcome.diagnostics)
                self.assertEqual((self.root / operation / "design.md").read_bytes(), self.v11(operation)["design.md"])

    def test_canonical_schema_or_integrity_error_fails_but_missing_authority_blocks(self) -> None:
        invalid = self.v11()
        handoff = json.loads(invalid["workbench-handoff.json"])
        handoff.pop("approved_design_statement")
        invalid["workbench-handoff.json"] = canonical_json_bytes(handoff)
        manifest = json.loads(invalid["package-manifest.json"])
        manifest["canonical_handoff"] = {"file": "workbench-handoff.json", **_member(invalid["workbench-handoff.json"])}
        invalid["package-manifest.json"] = canonical_json_bytes(manifest)
        failed = normalize_handoff_archive(self.archive("invalid-v11.zip", invalid), self.root / "invalid-v11")
        self.assertEqual(failed.status, "FAIL")
        self.assertIn("handoff.semantic_field_missing:approved_design_statement", failed.diagnostics)

        pending = self.full()
        legacy = json.loads(pending["handoff_manifest.json"])
        legacy["approval_evidence"] = ""
        pending["handoff_manifest.json"] = canonical_json_bytes(legacy)
        blocked = normalize_handoff_archive(self.archive("pending-full.zip", pending), self.root / "pending-full")
        self.assertEqual(blocked.status, "BLOCKED")
        self.assertIn("approval.not_approved", blocked.diagnostics)

    def test_full_and_delta_profiles_normalize_to_v11(self) -> None:
        for name, members, operation in (("full", self.full(), "create"), ("delta", self.delta(), "update")):
            with self.subTest(name=name):
                outcome = normalize_handoff_archive(self.archive(f"{name}.zip", members), self.root / name)
                self.assertEqual(outcome.status, "PASS", outcome.diagnostics)
                handoff = json.loads((self.root / name / "workbench-handoff.json").read_bytes())
                self.assertEqual((handoff["schema"], handoff["operation"]), ("workbench-handoff-v1.1", operation))
                self.assertEqual(handoff["requirements"][0]["id"], "DAC-01")

    def test_legacy_workbench_is_adapted_without_claiming_v11(self) -> None:
        outcome = normalize_handoff_archive(
            self.archive("legacy.zip", self.legacy_workbench()), self.root / "legacy"
        )
        self.assertEqual(outcome.status, "PASS", outcome.diagnostics)
        manifest = json.loads((self.root / "legacy/package-manifest.json").read_bytes())
        self.assertNotIn("handoff_contract", manifest)

    def test_blocked_normalization_preserves_existing_destination_and_cleans_temporary_files(self) -> None:
        destination = self.root / "output"
        destination.mkdir()
        (destination / "owner.txt").write_bytes(b"owner bytes")
        output_zip = self.root / "output.zip"
        output_zip.write_bytes(b"owner zip bytes")
        outcome = normalize_handoff_archive(
            self.archive("unknown.zip", {"unknown.txt": b"unknown"}), destination, output_zip
        )
        self.assertEqual(outcome.status, "BLOCKED")
        self.assertEqual((destination / "owner.txt").read_bytes(), b"owner bytes")
        self.assertEqual(output_zip.read_bytes(), b"owner zip bytes")
        self.assertEqual(list(self.root.glob(".output.normalize-*")), [])

    def test_identical_input_produces_identical_tree_and_zip_hashes(self) -> None:
        source = self.archive("full.zip", self.full())
        first = normalize_handoff_archive(source, self.root / "first", self.root / "first.zip")
        second = normalize_handoff_archive(source, self.root / "second", self.root / "second.zip")
        self.assertEqual(first.status, "PASS", first.diagnostics)
        self.assertEqual(first.output_tree_sha256, second.output_tree_sha256)
        self.assertEqual(first.output_archive_sha256, second.output_archive_sha256)
        self.assertEqual((self.root / "first.zip").read_bytes(), (self.root / "second.zip").read_bytes())


if __name__ == "__main__":
    unittest.main()
