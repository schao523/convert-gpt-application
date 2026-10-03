from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from plugin_builder_core.bootstrap import workbench_handoff
from plugin_builder_core.inspection import inspect_design_package


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


class CanonicalRequirementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def archive(self, name: str, members: dict[str, bytes], *, wrapped: bool = False) -> Path:
        path = self.root / name
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as output:
            for member, content in sorted(members.items()):
                output.writestr(f"sample-plugin/{member}" if wrapped else member, content)
        return path

    def baseline(self, name: str, *, wrapped: bool = False) -> Path:
        manifest = canonical({"name": "sample-plugin", "version": "1.0.0"})
        return self.archive(name, {"plugin.json": manifest, "owner.txt": b"preserve me\n"}, wrapped=wrapped)

    def handoff(self, name: str, operation: str, baseline: Path | None = None) -> Path:
        design = "Requirement DAC-01 keeps punctuation \u9177 and exact text.\n".encode("utf-8")
        handoff: dict[str, object] = {
            "schema": "workbench-handoff-v1.1",
            "operation": operation,
            "approval": {"state": "approved", "confirmed_by": "owner", "evidence": "record"},
            "approved_specification": {"state": "approved", "file": "design.md", "id": "SPEC-1", "version": "1"},
            "requirements": [{
                "id": "DAC-01",
                "source": "design.md#requirements",
                "verbatim": "Requirement DAC-01 keeps punctuation \u9177 and exact text.",
            }],
            "unresolved_owner_decisions": [],
        }
        if operation == "update":
            assert baseline is not None
            identity = workbench_handoff.baseline_identity_from_archive(baseline)
            handoff["requirements"][0]["change"] = "modify"  # type: ignore[index]
            handoff["baseline"] = {
                "plugin_id": identity.plugin_id,
                "version": identity.version,
                "archive_sha256": identity.archive_sha256,
            }
            handoff["baseline_preservation"] = {
                "preserve_unaffected_members": True,
                "removal_requires_requirement": True,
                "identity_must_match": True,
            }
        handoff_bytes = canonical(handoff)
        manifest = {
            "package_schema_version": 1,
            "package_kind": "normalized-workbench-handoff",
            "handoff_contract": "WORKBENCH_HANDOFF_V1_1",
            "operation": operation,
            "runtime_scope": "OPENAI_ONLY_PHASE_ONE",
            "gate": "APPROVED",
            "artifacts": [{
                "file": "design.md", "id": "SPEC-1", "role": "approved_specification",
                "state": "approved", "version": "1", "provenance": "fixture",
                "requirements": ["DAC-01"], "sha256": sha256(design).hexdigest(), "size": len(design),
            }],
            "supporting_files": [],
            "canonical_handoff": {
                "file": "workbench-handoff.json",
                "sha256": sha256(handoff_bytes).hexdigest(),
                "size": len(handoff_bytes),
            },
        }
        return self.archive(name, {
            "design.md": design,
            "workbench-handoff.json": handoff_bytes,
            "package-manifest.json": canonical(manifest),
        })

    def test_inspect_accepts_v11_create_and_registers_exact_ids(self) -> None:
        workspace = self.root / "create"
        outcome = inspect_design_package(self.handoff("create.zip", "create"), workspace, "create")
        self.assertEqual((outcome.status, outcome.stage), ("PASS", "S2"), outcome.errors)
        inspection = json.loads((workspace / "inspection.json").read_bytes())
        session = json.loads((workspace / "session.json").read_bytes())
        expected = {
            "id": "DAC-01", "required": True, "source": "design.md#requirements",
            "source_paths": ["input/design.md"],
            "verbatim": "Requirement DAC-01 keeps punctuation \u9177 and exact text.",
        }
        self.assertEqual(inspection["requirements"], [expected])
        self.assertEqual(session["requirements"], [expected])
        self.assertEqual(session["inspection"]["normalization"]["profile"], "WORKBENCH_HANDOFF_V1_1")

    def test_inspect_accepts_v11_update_only_when_supplied_baseline_matches(self) -> None:
        baseline = self.baseline("baseline.zip")
        design = self.handoff("update.zip", "update", baseline)
        accepted = inspect_design_package(design, self.root / "accepted", "update", baseline)
        self.assertEqual((accepted.status, accepted.stage), ("PASS", "S2"), accepted.errors)
        session = json.loads((self.root / "accepted/session.json").read_bytes())
        self.assertEqual(session["requirements"][0]["change"], "modify")

        other = self.baseline("other.zip", wrapped=True)
        rejected = inspect_design_package(design, self.root / "rejected", "update", other)
        self.assertEqual((rejected.status, rejected.stage), ("BLOCKED", "F1"))
        self.assertIn("baseline.archive_sha256_mismatch", rejected.errors)

    def test_flat_and_wrapped_baselines_share_identity_but_retain_archive_hash(self) -> None:
        flat = workbench_handoff.baseline_identity_from_archive(self.baseline("flat.zip"))
        wrapped = workbench_handoff.baseline_identity_from_archive(self.baseline("wrapped.zip", wrapped=True))
        self.assertEqual((flat.plugin_id, flat.version), (wrapped.plugin_id, wrapped.version))
        self.assertNotEqual(flat.archive_sha256, wrapped.archive_sha256)
        self.assertEqual(flat.envelope_profile, "LEGACY_FLAT")
        self.assertEqual(wrapped.envelope_profile, "PORTABLE_SINGLE_DIRECTORY")


if __name__ == "__main__":
    unittest.main()
