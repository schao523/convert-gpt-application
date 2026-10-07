from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest


TESTS = Path(__file__).parent
SCRIPTS = TESTS.parent / "scripts"
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from plugin_builder_core.artifact_quality import audit_artifact_quality
from test_create_candidate import prepared_workspace, read_result, run_cli


class ArtifactQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def proposal(self, files: list[dict], *, adopted: bool = False, consultation: str | None = None, ownership=None) -> dict:
        return {
            "operation": "create",
            "files": files,
            "requirements": [
                {"id": "RQ1", "owner_skill": "alpha"},
                {"id": "RQ2", "owner_skill": "beta"},
            ],
            "implementation_decisions": {
                "knowledge_policy": {
                    "adopt_general_knowledge": adopted,
                    "consultation_skill": consultation,
                },
                "reference_ownership": ownership or {},
            },
            "skills": [{"name": "alpha"}, {"name": "beta"}],
        }

    def write(self, relative: str, payload: bytes = b"knowledge") -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    def recipe(self, path: str, role: str | None, requirement: str = "RQ1") -> dict:
        row = {"path": path, "requirement_ids": [requirement]}
        if role is not None:
            row["content_role"] = role
        return row

    def test_missing_and_unknown_content_roles_fail(self) -> None:
        self.write("a.txt")
        self.write("b.txt")
        report = audit_artifact_quality(
            self.proposal([
                self.recipe("a.txt", None),
                self.recipe("b.txt", "MYSTERY"),
            ]),
            self.root,
        )
        self.assertIn("artifact.content_role_missing:a.txt", report.diagnostics)
        self.assertIn("artifact.content_role_invalid:b.txt", report.diagnostics)

    def test_knowledge_placement_and_general_policy_fail_closed(self) -> None:
        cases = (
            ("skills/alpha/assets/ref.md", "PROFESSIONAL_KNOWLEDGE", "artifact.knowledge_in_skill_assets"),
            ("references/ref.md", "PROFESSIONAL_KNOWLEDGE", "artifact.professional_knowledge_owner_path"),
            ("skills/alpha/references/general.md", "GENERAL_KNOWLEDGE", "artifact.general_knowledge_policy_invalid"),
        )
        for path, role, code in cases:
            with self.subTest(path=path):
                case_root = self.root / sha256(path.encode()).hexdigest()[:8]
                case_root.mkdir()
                target = case_root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"knowledge")
                report = audit_artifact_quality(self.proposal([self.recipe(path, role)]), case_root)
                self.assertTrue(any(item.startswith(f"{code}:") for item in report.diagnostics), report)

    def test_multiple_general_indexes_fail(self) -> None:
        paths = [
            "skills/alpha/references/knowledge-index.json",
            "skills/beta/references/knowledge-index.json",
        ]
        for path in paths:
            self.write(path, b"{}")
        report = audit_artifact_quality(
            self.proposal(
                [self.recipe(path, "GENERAL_KNOWLEDGE") for path in paths],
                adopted=True,
                consultation="alpha",
            ),
            self.root,
        )
        self.assertIn("artifact.multiple_general_knowledge_indexes", report.diagnostics)

    def test_professional_and_consultation_skill_cases_pass(self) -> None:
        professional = "skills/alpha/references/professional.md"
        self.write(professional)
        report = audit_artifact_quality(
            self.proposal([self.recipe(professional, "PROFESSIONAL_KNOWLEDGE")]),
            self.root,
        )
        self.assertEqual(report.diagnostics, ())

        general = "skills/alpha/references/general.md"
        self.write(general, b"general")
        report = audit_artifact_quality(
            self.proposal(
                [self.recipe(general, "GENERAL_KNOWLEDGE")],
                adopted=True,
                consultation="alpha",
            ),
            self.root,
        )
        self.assertEqual(report.diagnostics, ())

    def test_professional_duplicate_requires_digest_keyed_rationale(self) -> None:
        paths = [
            "skills/alpha/references/shared.md",
            "skills/beta/references/shared.md",
        ]
        for path in paths:
            self.write(path, b"same professional bytes")
        digest = sha256(b"same professional bytes").hexdigest()
        files = [
            self.recipe(paths[0], "PROFESSIONAL_KNOWLEDGE", "RQ1"),
            self.recipe(paths[1], "PROFESSIONAL_KNOWLEDGE", "RQ2"),
        ]
        blocked = audit_artifact_quality(self.proposal(files), self.root)
        self.assertIn(f"artifact.professional_duplicate_ownership_required:{digest}", blocked.diagnostics)
        duplicate = next(item for item in blocked.as_dict()["duplicate_groups"] if item["sha256"] == digest)
        self.assertEqual(duplicate["paths"], paths)
        self.assertEqual(duplicate["member_count"], 2)
        self.assertEqual(duplicate["duplicate_bytes"], len(b"same professional bytes"))

        passed = audit_artifact_quality(
            self.proposal(files, ownership={digest: "Both skills require the same approved source."}),
            self.root,
        )
        self.assertEqual(passed.diagnostics, ())

    def test_unrelated_generated_duplicates_are_reported_without_failure(self) -> None:
        paths = ["generated/a.txt", "generated/b.txt"]
        for path in paths:
            self.write(path, b"same generated bytes")
        report = audit_artifact_quality(
            self.proposal([self.recipe(path, "OTHER") for path in paths]),
            self.root,
        )
        self.assertEqual(report.diagnostics, ())
        self.assertEqual(report.as_dict()["duplicate_groups"][0]["paths"], paths)

    def test_v1_baseline_roles_are_inherited_without_reclassification(self) -> None:
        preserved = "skills/old/references/legacy.md"
        changed = "skills/alpha/references/new.md"
        self.write(preserved, b"legacy")
        self.write(changed, b"new")
        proposal = self.proposal([self.recipe(changed, "PROFESSIONAL_KNOWLEDGE")])
        proposal["operation"] = "update"
        report = audit_artifact_quality(
            proposal,
            self.root,
            baseline_manifest={
                "schema": "plugin-builder-candidate-manifest-v1",
                "members": [{"path": preserved}],
            },
        )
        roles = report.as_dict()["file_roles"]
        self.assertEqual(roles[preserved], "INHERITED_UNCLASSIFIED")
        self.assertEqual(roles[changed], "PROFESSIONAL_KNOWLEDGE")

    def test_build_blocks_approved_v1_plan_for_replanning(self) -> None:
        workspace = prepared_workspace(self.root)
        plan_path = workspace / "implementation-plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["schema"] = "plugin-builder-implementation-plan-v1"
        plan.pop("preflight_evidence", None)
        plan_path.write_text(
            json.dumps(plan, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="ascii",
        )
        plan_hash = sha256(plan_path.read_bytes()).hexdigest()
        session_path = workspace / "session.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))
        session["plan"]["sha256"] = plan_hash
        session["w1"]["plan_sha256"] = plan_hash
        session_path.write_text(json.dumps(session), encoding="utf-8")
        before = session_path.read_bytes()

        completed = run_cli("build", "--session", str(session_path), "--json")

        self.assertEqual(completed.returncode, 2)
        self.assertIn("build.plan_schema_upgrade_required", read_result(completed)["errors"])
        self.assertEqual(session_path.read_bytes(), before)
        self.assertFalse((workspace / "candidate").exists())

    def test_build_rejects_preflight_evidence_drift_without_candidate_mutation(self) -> None:
        workspace = prepared_workspace(self.root)
        plan_path = workspace / "implementation-plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["preflight_evidence"]["materialized_tree_sha256"] = "0" * 64
        plan_path.write_text(
            json.dumps(plan, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="ascii",
        )
        plan_hash = sha256(plan_path.read_bytes()).hexdigest()
        session_path = workspace / "session.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))
        session["plan"]["sha256"] = plan_hash
        session["w1"]["plan_sha256"] = plan_hash
        session_path.write_text(json.dumps(session), encoding="utf-8")

        completed = run_cli("build", "--session", str(session_path), "--json")

        self.assertEqual(completed.returncode, 2)
        self.assertIn("build.preflight_evidence_mismatch", read_result(completed)["errors"])
        self.assertFalse((workspace / "candidate").exists())


if __name__ == "__main__":
    unittest.main()
