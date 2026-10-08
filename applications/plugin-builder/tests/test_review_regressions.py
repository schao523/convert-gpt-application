"""Regression tests for Phase 2 final-review security and lifecycle findings."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

TESTS = Path(__file__).parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from test_create_candidate import DESIGN_FIXTURE, PLAN_FIXTURE, prepared_workspace, read_result, run_cli
from plugin_builder_core.implementation_plan import compile_plan
from plugin_builder_core.inspection import inspect_design_package


class FinalReviewRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _design_zip(self) -> Path:
        destination = self.root / "design.zip"
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(DESIGN_FIXTURE.iterdir(), key=lambda item: item.name):
                archive.write(path, path.name)
        return destination

    def _compile(self, mutate):
        workspace = self.root / "workspace"
        inspected = inspect_design_package(self._design_zip(), workspace, "create")
        self.assertEqual(inspected.status, "PASS")
        proposal = json.loads(PLAN_FIXTURE.read_text(encoding="utf-8"))
        mutate(proposal)
        proposal_path = self.root / "proposal.json"
        proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
        return compile_plan(workspace / "inspection.json", proposal_path, self.root / "plan.json")

    def test_plan_tampering_after_w1_blocks_verification_without_execution(self) -> None:
        workspace = prepared_workspace(self.root)
        self.assertEqual(run_cli("build", "--session", str(workspace / "session.json"), "--json").returncode, 0)
        marker = workspace / "must-not-exist.txt"
        plan_path = workspace / "implementation-plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["checks"].append({"id": "tampered", "kind": "PYTHON_ARGV", "required": True,
            "requirement_ids": ["RQ1"], "argv": ["{python}", "-c", f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')"]})
        plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="ascii")
        completed = run_cli("verify", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("verify.plan_sha256_mismatch", read_result(completed)["errors"])
        self.assertFalse(marker.exists())

    def test_inspection_refuses_to_replace_nonempty_workspace(self) -> None:
        workspace = self.root / "workspace"
        workspace.mkdir()
        owner_file = workspace / "owner.txt"
        owner_file.write_text("preserve", encoding="utf-8")
        outcome = inspect_design_package(self._design_zip(), workspace, "create")
        self.assertEqual(outcome.status, "BLOCKED")
        self.assertIn("workspace.nonempty", outcome.errors)
        self.assertEqual(owner_file.read_text(encoding="utf-8"), "preserve")

    def test_cancelled_session_blocks_build(self) -> None:
        workspace = prepared_workspace(self.root)
        self.assertEqual(run_cli("cancel", "--session", str(workspace / "session.json"), "--json").returncode, 0)
        completed = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("build.session_cancelled", read_result(completed)["errors"])
        self.assertFalse((workspace / "candidate").exists())

    def test_required_check_must_own_requirement_and_match_tool_command(self) -> None:
        def mutate(proposal):
            check = next(item for item in proposal["checks"] if item["id"] == "normalize-self-test")
            check["requirement_ids"] = []
            check["argv"] = ["{python}", "-c", "print('bypass')"]
        outcome = self._compile(mutate)
        self.assertEqual(outcome.status, "FAIL")
        self.assertIn("plan.check_requirement_missing:normalize-self-test", outcome.errors)
        self.assertIn("plan.check_tool_unbound:normalize-self-test", outcome.errors)

    def test_requirement_paths_and_evidence_targets_must_resolve(self) -> None:
        def mutate(proposal):
            requirement = next(item for item in proposal["requirements"] if item["id"] == "RQ1")
            requirement["implementation_paths"] = ["missing.py"]
            requirement["evidence_targets"] = ["missing-check"]
        outcome = self._compile(mutate)
        self.assertEqual(outcome.status, "FAIL")
        self.assertIn("plan.requirement_implementation_unknown:RQ1:missing.py", outcome.errors)
        self.assertIn("plan.requirement_evidence_unknown:RQ1:missing-check", outcome.errors)

    def test_general_knowledge_reference_may_route_through_directly_linked_index(self) -> None:
        def mutate(proposal):
            skill = next(item for item in proposal["files"] if item["path"] == "skills/answering-structured-requests/SKILL.md")
            skill["inline_text"] = skill["inline_text"].replace("[the approved method](references/Reference.md)", "[the knowledge index](references/knowledge-index.json)")
            skill["source_sha256"] = sha256(skill["inline_text"].encode()).hexdigest()
            index = {"path": "skills/answering-structured-requests/references/knowledge-index.json",
                "classification": "generated_json", "content_role": "GENERAL_KNOWLEDGE", "source_sha256": "0" * 64,
                "redistribution": {"state": "APPROVED", "evidence": "owner approved index"},
                "inline_json": {
                    "schema_version": 1,
                    "files": [{
                        "path": "Reference.md",
                        "purpose": "Approved general method reference.",
                        "topics": ["structured requests"],
                    }],
                },
                "requirement_ids": ["RQ1"]}
            index["source_sha256"] = sha256((json.dumps(index["inline_json"], ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")).hexdigest()
            proposal["files"].append(index)
            proposal["expected_members"].append(index["path"])
            proposal["implementation_decisions"]["knowledge_policy"] = {
                "adopt_general_knowledge": True,
                "consultation_skill": "answering-structured-requests",
            }
        outcome = self._compile(mutate)
        self.assertEqual(outcome.status, "PASS", outcome.errors)

    def test_distribution_credential_file_blocks_verification(self) -> None:
        def mutate(proposal):
            proposal["files"].append({"path": ".env", "classification": "generated_text", "content_role": "OTHER",
                "source_sha256": sha256(b"API_KEY=fake\n").hexdigest(),
                "redistribution": {"state": "APPROVED", "evidence": "negative fixture"},
                "inline_text": "API_KEY=fake\n", "requirement_ids": ["RQ1"]})
            proposal["expected_members"].append(".env")
        workspace = prepared_workspace(self.root, mutate=mutate)
        self.assertEqual(run_cli("build", "--session", str(workspace / "session.json"), "--json").returncode, 0)
        completed = run_cli("verify", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(completed.returncode, 2)
        report = json.loads((workspace / "verification-report.json").read_text(encoding="utf-8"))
        safety = next(item for item in report["checks"] if item["kind"] == "DISTRIBUTION_SAFETY")
        self.assertEqual(safety["state"], "FAIL")

    def test_declared_tool_fixture_output_is_compared(self) -> None:
        def mutate(proposal):
            proposal["tools"][0]["fixtures"]["output"] = {"normalized": "different"}
        workspace = prepared_workspace(self.root, mutate=mutate)
        self.assertEqual(run_cli("build", "--session", str(workspace / "session.json"), "--json").returncode, 0)
        completed = run_cli("verify", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(completed.returncode, 2)
        report = json.loads((workspace / "verification-report.json").read_text(encoding="utf-8"))
        self.assertIn("fixture_output_mismatch", report["tools"][0]["diagnostics"])


if __name__ == "__main__":
    unittest.main()
