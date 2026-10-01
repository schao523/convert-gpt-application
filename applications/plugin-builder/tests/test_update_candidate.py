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

from test_create_candidate import (
    PLAN_FIXTURE,
    prepared_workspace,
    read_result,
    run_cli,
)
from plugin_builder_core.bootstrap import plugin_authoring
from plugin_builder_core.inspection import inspect_design_package


class UpdateCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _archive_tree(self, source: Path, destination: Path) -> None:
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(source.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(source).as_posix())

    def _prepare(self, *, keep_unrelated: bool = True, remove_unrelated: bool = False, identity: str = "sample-plugin") -> Path:
        index = len(list(self.root.glob("create-*")))
        create_root = self.root / f"create-{index}"
        create_root.mkdir()
        create = prepared_workspace(create_root)
        built = run_cli("build", "--session", str(create / "session.json"), "--json")
        self.assertEqual(built.returncode, 0, built.stdout)
        baseline_tree = create / "candidate"
        (baseline_tree / "owner-notes.txt").write_bytes(b"owner bytes\r\nunchanged\x00")
        baseline_zip = self.root / f"baseline-{index}.zip"
        self._archive_tree(baseline_tree, baseline_zip)

        design_zip = create_root / "design.zip"
        workspace = self.root / f"update-{index}"
        inspected = inspect_design_package(design_zip, workspace, "update", baseline_zip)
        self.assertEqual(inspected.status, "PASS")
        proposal = json.loads(PLAN_FIXTURE.read_text(encoding="utf-8"))
        proposal["operation"] = "update"
        proposal["plugin"]["name"] = identity
        changed = next(item for item in proposal["files"] if item["path"] == "skills/checking-traceability/SKILL.md")
        changed["inline_text"] += "\nPreserve approved baseline content during updates.\n"
        changed["source_sha256"] = sha256(changed["inline_text"].encode("utf-8")).hexdigest()
        proposal["files"] = [changed]
        expected = {path.relative_to(baseline_tree).as_posix() for path in baseline_tree.rglob("*") if path.is_file()}
        expected.add("PLUGIN-BUILDER-CHANGES.json")
        if remove_unrelated:
            expected.remove("owner-notes.txt")
        proposal["expected_members"] = sorted(expected)
        proposal_path = self.root / f"update-proposal-{index}.json"
        proposal_path.write_text(json.dumps(proposal, sort_keys=True), encoding="utf-8")
        planned = run_cli("plan", "--session", str(workspace / "session.json"), "--proposal", str(proposal_path), "--json")
        self.assertEqual(planned.returncode, 0, planned.stdout)
        approved = run_cli("approve-w1", "--session", str(workspace / "session.json"), "--confirmed-by", "owner", "--evidence", "approved update", "--json")
        self.assertEqual(approved.returncode, 0, approved.stdout)
        if keep_unrelated:
            resolved = run_cli("resolve-update", "--session", str(workspace / "session.json"), "--member", "owner-notes.txt", "--decision", "remove" if remove_unrelated else "keep", "--evidence", "owner decision", "--json")
            self.assertEqual(resolved.returncode, 0, resolved.stdout)
        return workspace

    def test_update_preserves_unaffected_managed_and_unrelated_bytes(self) -> None:
        workspace = self._prepare()
        baseline = workspace / "baseline"
        expected = {path: (baseline / path).read_bytes() for path in [".codex-plugin/plugin.json", "owner-notes.txt"]}
        completed = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        for path, payload in expected.items():
            self.assertEqual((workspace / "candidate" / path).read_bytes(), payload)
        changes = json.loads((workspace / "candidate/PLUGIN-BUILDER-CHANGES.json").read_text(encoding="utf-8"))
        self.assertIn("owner-notes.txt", changes["preserved"])
        self.assertIn("skills/checking-traceability/SKILL.md", changes["changed"])

    def test_update_adds_portable_manifest_to_legacy_baseline(self) -> None:
        workspace = self._prepare()
        baseline = workspace / "baseline"
        (baseline / "plugin.json").unlink()
        session_path = workspace / "session.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))
        session["baseline"]["manifest_sha256"] = plugin_authoring.tree_sha256(baseline)
        session_path.write_text(json.dumps(session), encoding="utf-8")
        plan_path = workspace / "implementation-plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["expected_members"] = sorted(set(plan["expected_members"]) | {"plugin.json"})
        plan_path.write_text(json.dumps(plan, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="ascii")
        plan_hash = sha256(plan_path.read_bytes()).hexdigest()
        session = json.loads(session_path.read_text(encoding="utf-8"))
        session["plan"]["sha256"] = plan_hash
        session["w1"]["plan_sha256"] = plan_hash
        session_path.write_text(json.dumps(session), encoding="utf-8")

        completed = run_cli("build", "--session", str(session_path), "--json")

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertTrue((workspace / "candidate/plugin.json").is_file())
        self.assertEqual(plugin_authoring.validate_manifest_pair(workspace / "candidate"), ())

    def test_update_rejects_unapproved_manifest_identity_change(self) -> None:
        workspace = self._prepare()
        plan_path = workspace / "implementation-plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["plugin"]["version"] = "2.0.0"
        plan_path.write_text(json.dumps(plan, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="ascii")
        plan_hash = sha256(plan_path.read_bytes()).hexdigest()
        session_path = workspace / "session.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))
        session["plan"]["sha256"] = plan_hash
        session["w1"]["plan_sha256"] = plan_hash
        session_path.write_text(json.dumps(session), encoding="utf-8")

        completed = run_cli("build", "--session", str(session_path), "--json")

        self.assertEqual(completed.returncode, 2)
        self.assertIn("build.plugin_identity_change_forbidden", read_result(completed)["errors"])

    def test_update_preserves_unaffected_tool_implementation_and_skill_binding(self) -> None:
        workspace = self._prepare()
        before = (workspace / "baseline/tools/normalize.py").read_bytes()
        completed = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual((workspace / "candidate/tools/normalize.py").read_bytes(), before)
        manifest = json.loads((workspace / "candidate/PLUGIN-BUILDER-MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["tool_bindings"][0]["skills"], ["answering-structured-requests"])

    def test_tool_contract_change_requires_plan_and_w1_reapproval(self) -> None:
        workspace = self._prepare()
        plan_path = workspace / "implementation-plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["tools"][0]["permissions"].append("network:access")
        plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="ascii")
        completed = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("build.plan_sha256_mismatch", read_result(completed)["errors"])

    def test_unexplained_member_blocks_before_candidate_mutation(self) -> None:
        workspace = self._prepare(keep_unrelated=False)
        completed = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("build.update_decision_required:owner-notes.txt:keep", read_result(completed)["errors"])
        self.assertFalse((workspace / "candidate").exists())

    def test_keep_decision_unblocks_without_changing_member(self) -> None:
        workspace = self._prepare(keep_unrelated=False)
        resolved = run_cli("resolve-update", "--session", str(workspace / "session.json"), "--member", "owner-notes.txt", "--decision", "keep", "--evidence", "owner says preserve", "--json")
        self.assertEqual(resolved.returncode, 0, resolved.stdout)
        before = (workspace / "baseline/owner-notes.txt").read_bytes()
        completed = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual((workspace / "candidate/owner-notes.txt").read_bytes(), before)

    def test_remove_requires_explicit_plan_and_member_decision(self) -> None:
        workspace = self._prepare(keep_unrelated=False, remove_unrelated=True)
        blocked = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("build.update_decision_required:owner-notes.txt:remove", read_result(blocked)["errors"])
        run_cli("resolve-update", "--session", str(workspace / "session.json"), "--member", "owner-notes.txt", "--decision", "remove", "--evidence", "approved removal", "--json")
        built = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(built.returncode, 0, built.stdout)
        self.assertFalse((workspace / "candidate/owner-notes.txt").exists())

    def test_update_rejects_identity_change_and_stale_baseline(self) -> None:
        identity = self._prepare(identity="different-plugin")
        rejected = run_cli("build", "--session", str(identity / "session.json"), "--json")
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("build.plugin_identity_change_forbidden", read_result(rejected)["errors"])
        stale = self._prepare()
        (stale / "baseline/.codex-plugin/plugin.json").write_text("tampered", encoding="utf-8")
        rejected = run_cli("build", "--session", str(stale / "session.json"), "--json")
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("build.baseline_stale", read_result(rejected)["errors"])

    def test_failed_update_preserves_previous_candidate(self) -> None:
        workspace = self._prepare()
        first = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(first.returncode, 0, first.stdout)
        before = plugin_authoring.tree_sha256(workspace / "candidate")
        (workspace / "baseline/.codex-plugin/plugin.json").write_text("tampered", encoding="utf-8")
        failed = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(failed.returncode, 2)
        self.assertEqual(plugin_authoring.tree_sha256(workspace / "candidate"), before)


if __name__ == "__main__":
    unittest.main()
