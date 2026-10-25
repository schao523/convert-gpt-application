from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from obvious_one_plugin_framework.workbench_handoff import preflight_handoff_archive, normalize_handoff_archive


ROOT = Path(__file__).resolve().parents[2]
FULL = ROOT / "tests/fixtures/workbench-handoff/full"
DELTA = ROOT / "tests/fixtures/workbench-handoff/delta"


class SourcePreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="source-preflight-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def archive(self, name="source.zip", members=None):
        if members is None:
            members = {p.name: p.read_bytes() for p in FULL.iterdir() if p.is_file()}
        path = self.root / name
        with zipfile.ZipFile(path, "w") as output:
            for key, value in sorted(members.items()):
                output.writestr(key, value)
        return path

    def members(self):
        return {p.name: p.read_bytes() for p in FULL.iterdir() if p.is_file()}

    def changed_manifest(self, change):
        members = self.members()
        manifest = json.loads(members["handoff_manifest.json"])
        change(manifest)
        members["handoff_manifest.json"] = json.dumps(manifest, ensure_ascii=True).encode()
        return members

    def test_full_source_passes_without_canonical_output_or_mutation(self):
        source = self.archive()
        original = source.read_bytes()
        first = preflight_handoff_archive(source)
        second = preflight_handoff_archive(source)
        self.assertEqual(first.status, "PASS", first.diagnostics)
        self.assertEqual(first.profile, "COOL_DESIGN_ASSISTANT_FULL_V1")
        self.assertEqual(first.report, second.report)
        self.assertEqual(first.report["source_archive_sha256"], sha256(original).hexdigest())
        self.assertEqual(source.read_bytes(), original)
        self.assertEqual(list(self.root.iterdir()), [source])
        self.assertTrue(first.report["normalization_ready"])
        self.assertEqual(first.report["target_output_profile"], "WORKBENCH_HANDOFF_V1_1")

    def test_unknown_and_missing_manifest_block(self):
        for members in ({"staging.json": b"{}"}, {"Design_APPROVED.md": b"approved"}):
            with self.subTest(members=members):
                outcome = preflight_handoff_archive(self.archive("unknown.zip", members))
                self.assertEqual(outcome.status, "BLOCKED")
                self.assertIn("profile.unrecognized", outcome.diagnostics)

    def test_delta_source_checks_baseline_digest(self):
        members = {p.name: p.read_bytes() for p in DELTA.iterdir() if p.is_file()}
        manifest = json.loads(members["delta_handoff_manifest.json"])
        manifest["baseline"]["archive_sha256"] = "a" * 64
        members["delta_handoff_manifest.json"] = json.dumps(manifest).encode()
        outcome = preflight_handoff_archive(self.archive("delta.zip", members))
        self.assertEqual(outcome.status, "PASS", outcome.diagnostics)
        self.assertEqual(outcome.profile, "COOL_DESIGN_ASSISTANT_DELTA_V1")
        manifest["baseline"]["archive_sha256"] = "invalid"
        members["delta_handoff_manifest.json"] = json.dumps(manifest).encode()
        outcome = preflight_handoff_archive(self.archive("invalid-delta.zip", members))
        self.assertEqual(outcome.status, "BLOCKED")
        self.assertIn("baseline.archive_sha256_invalid", outcome.diagnostics)

    def test_requirement_and_binding_failures_block(self):
        cases = [
            (lambda m: m["requirements"][0].pop("verbatim"), "requirements.text_invalid:D-01"),
            (lambda m: m["requirements"].append(dict(m["requirements"][0], verbatim="different")), "requirements.duplicate_id:D-01"),
            (lambda m: m["artifacts"][0]["requirements"].append("UNKNOWN"), "requirements.artifact_binding_unknown:UNKNOWN"),
            (lambda m: m["artifacts"][0].update(file="missing.md"), "package.declared_member_missing:missing.md"),
            (lambda m: m["artifacts"][1].update(role="unknown_role"), "package.artifact_role_invalid:Workflow_APPROVED.md"),
            (lambda m: m.update(approval_evidence=""), "approval.not_approved"),
            (lambda m: m.update(unresolved_owner_decisions=[{"decision_id":"RIGHTS-1","summary":"rights unresolved","owner":"owner","impact":"distribution","blocking":True}]), "owner_decisions.blocking:RIGHTS-1"),
        ]
        for index, (change, code) in enumerate(cases):
            with self.subTest(code=code):
                outcome = preflight_handoff_archive(self.archive(f"bad-{index}.zip", self.changed_manifest(change)))
                self.assertEqual(outcome.status, "BLOCKED", outcome.report)
                self.assertIn(code, outcome.diagnostics)
                checks = {item["id"]: item["status"] for item in outcome.report["checks"]}
                self.assertEqual(checks["PF01"], "PASS")
                self.assertIn("PASS", checks.values())
                self.assertIn("BLOCKED", checks.values())
                self.assertTrue(all(item["corrective_action"] for item in outcome.report["diagnostics"]))

    def test_unsafe_zip_blocks(self):
        outcome = preflight_handoff_archive(self.archive("escape.zip", {"../escape": b"x"}))
        self.assertEqual(outcome.status, "BLOCKED")
        self.assertIn("archive_path_escape", outcome.diagnostics)

    def test_semantic_override_and_conflicting_approval_block(self):
        cases = [
            (lambda m: m.update(approval={"state": "pending"}), "approval.conflicting_authority"),
            (lambda m: m.update(reference_material_inventory_evaluation_and_usage_map="missing"), "reference.usage_map_invalid"),
            (lambda m: m.update(rights_and_redistribution_decisions="approved"), "rights.decision_invalid"),
            (lambda m: m.update(approved_design_statement=[]), "handoff.semantic_field_invalid:approved_design_statement"),
        ]
        for index, (change, code) in enumerate(cases):
            with self.subTest(code=code):
                outcome = preflight_handoff_archive(self.archive(f"semantic-{index}.zip", self.changed_manifest(change)))
                self.assertEqual(outcome.status, "BLOCKED")
                self.assertIn(code, outcome.diagnostics)

    def test_historical_draft_text_with_later_manifest_approval_passes(self):
        members = self.members()
        members["Design_APPROVED.md"] = b"# Historical DRAFT\nD-01 preserves the approved application intent exactly.\nDAC-01 preserves UTF-8 text: \xe9\x85\xb7\xe6\x8f\x92\xe4\xbb\xb6\xe8\xa8\xad\xe8\xa8\x88\xe5\x8a\xa9\xe7\x90\x86.\n"
        result = preflight_handoff_archive(self.archive("draft-approved.zip", members))
        self.assertEqual(result.status, "PASS", result.diagnostics)

    def test_conflicting_authority_blocks(self):
        members = self.members()
        members["delta_handoff_manifest.json"] = members["handoff_manifest.json"]
        outcome = preflight_handoff_archive(self.archive("mixed.zip", members))
        self.assertEqual(outcome.status, "BLOCKED")
        self.assertIn("profile.multiple_authorities", outcome.diagnostics)

    def test_declared_wrong_hash_blocks_preflight_and_normalization(self):
        source = self.archive("wrong-hash.zip", self.changed_manifest(
            lambda manifest: manifest["artifacts"][0].update(sha256="0" * 64)
        ))
        preflight = preflight_handoff_archive(source)
        normalized = normalize_handoff_archive(source, self.root / "normalized", self.root / "normalized.zip")
        self.assertEqual(preflight.status, "BLOCKED")
        self.assertEqual(normalized.status, "FAIL")
        self.assertIn("package.declared_member_mismatch:Design_APPROVED.md", preflight.diagnostics)
        self.assertIn("package.declared_member_mismatch:Design_APPROVED.md", normalized.diagnostics)
        self.assertFalse((self.root / "normalized.zip").exists())


if __name__ == "__main__":
    unittest.main()
