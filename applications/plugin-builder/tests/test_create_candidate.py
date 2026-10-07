from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DESIGN_FIXTURE = Path(__file__).parent / "fixtures" / "design-package-create"
PLAN_FIXTURE = Path(__file__).parent / "fixtures" / "plan-create.json"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from plugin_builder_core.inspection import inspect_design_package
from plugin_builder_core.bootstrap import plugin_authoring
from plugin_builder_core.proposed_tree import materialize_proposed_tree


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPTS / "plugin_builder.py"), *arguments],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="strict", check=False,
    )


def read_result(completed: subprocess.CompletedProcess[str]) -> dict:
    if completed.stderr or len(completed.stdout.splitlines()) != 1:
        raise AssertionError(completed.stderr or completed.stdout)
    return json.loads(completed.stdout)


def prepared_workspace(root: Path, *, approve: bool = True, mutate=None) -> Path:
    archive_path = root / "design.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(DESIGN_FIXTURE.iterdir(), key=lambda item: item.name):
            archive.write(path, path.name)
    workspace = root / "workspace"
    outcome = inspect_design_package(archive_path, workspace, "create")
    if outcome.status != "PASS":
        raise AssertionError(outcome)
    proposal = json.loads(PLAN_FIXTURE.read_text(encoding="utf-8"))
    if mutate is not None:
        mutate(proposal)
    proposal_path = root / "proposal.json"
    proposal_path.write_text(json.dumps(proposal, ensure_ascii=True, sort_keys=True), encoding="utf-8")
    planned = run_cli("plan", "--session", str(workspace / "session.json"), "--proposal", str(proposal_path), "--json")
    if planned.returncode != 0:
        raise AssertionError(planned.stdout)
    if approve:
        approved = run_cli(
            "approve-w1", "--session", str(workspace / "session.json"),
            "--confirmed-by", "fixture owner", "--evidence", "reviewed plan and tools", "--json",
        )
        if approved.returncode != 0:
            raise AssertionError(approved.stdout)
    return workspace


class CreateCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_build_is_blocked_before_w1(self) -> None:
        workspace = prepared_workspace(self.root, approve=False)
        completed = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("build.w1_required", read_result(completed)["errors"])
        self.assertFalse((workspace / "candidate").exists())

    def test_shared_materializer_matches_created_candidate_before_control_manifest(self) -> None:
        workspace = prepared_workspace(self.root)
        plan = json.loads(
            (workspace / "implementation-plan.json").read_text(encoding="utf-8")
        )
        proposed = self.root / "proposed"

        materialize_proposed_tree(plan, workspace, proposed)
        completed = run_cli("build", "--session", str(workspace / "session.json"), "--json")

        self.assertEqual(completed.returncode, 0, completed.stdout)
        candidate = workspace / "candidate"
        candidate_members = {
            path.relative_to(candidate).as_posix(): path.read_bytes()
            for path in candidate.rglob("*")
            if path.is_file() and path.name != "PLUGIN-BUILDER-MANIFEST.json"
        }
        proposed_members = {
            path.relative_to(proposed).as_posix(): path.read_bytes()
            for path in proposed.rglob("*")
            if path.is_file()
        }
        self.assertEqual(proposed_members, candidate_members)

    def test_create_builds_real_multi_skill_plugin_with_references_and_local_tool(self) -> None:
        workspace = prepared_workspace(self.root)
        completed = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        candidate = workspace / "candidate"
        self.assertTrue((candidate / ".codex-plugin/plugin.json").is_file())
        self.assertTrue((candidate / "skills/answering-structured-requests/references/Reference.md").is_file())
        self.assertTrue((candidate / "skills/answering-structured-requests/agents/openai.yaml").is_file())
        self.assertTrue((candidate / "skills/checking-traceability/agents/openai.yaml").is_file())
        self.assertTrue((candidate / "tools/normalize.py").is_file())
        self.assertEqual(plugin_authoring.validate_plugin_tree(candidate), ())

    def test_create_candidate_materializes_portable_and_legacy_manifests(self) -> None:
        workspace = prepared_workspace(self.root)
        completed = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        candidate = workspace / "candidate"
        portable = json.loads((candidate / "plugin.json").read_text(encoding="utf-8"))
        legacy = json.loads((candidate / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(portable["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertEqual((portable["name"], portable["version"]), (legacy["name"], legacy["version"]))
        self.assertEqual(portable["extensions"]["com.openai"]["interface"], legacy["interface"])
        self.assertEqual(plugin_authoring.validate_manifest_pair(candidate), ())

    def test_create_candidate_hash_matches_exact_manifest(self) -> None:
        workspace = prepared_workspace(self.root)
        completed = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        document = read_result(completed)
        session = json.loads((workspace / "session.json").read_text(encoding="utf-8"))
        manifest_path = workspace / "candidate/PLUGIN-BUILDER-MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "plugin-builder-candidate-manifest-v2")
        self.assertEqual(manifest["operation"], "create")
        self.assertEqual(manifest["file_roles"]["plugin.json"], "PLUGIN_MANIFEST")
        self.assertRegex(manifest["preflight_evidence_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(manifest["manifest_profile"]["profile"], "PRIVATE_LOCAL")
        self.assertRegex(manifest["manifest_profile_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(session["candidate"]["sha256"], plugin_authoring.tree_sha256(workspace / "candidate"))
        self.assertEqual(document["candidate_sha256"], session["candidate"]["sha256"])
        self.assertEqual(session["candidate"]["manifest_sha256"], __import__("hashlib").sha256(manifest_path.read_bytes()).hexdigest())
        self.assertEqual({item["path"] for item in manifest["members"]}, set(manifest["expected_members"]) - {"PLUGIN-BUILDER-MANIFEST.json"})

    def test_repeated_create_is_byte_identical(self) -> None:
        workspace = prepared_workspace(self.root)
        first = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(first.returncode, 0, first.stdout)
        first_bytes = {
            path.relative_to(workspace / "candidate").as_posix(): path.read_bytes()
            for path in (workspace / "candidate").rglob("*") if path.is_file()
        }
        second = run_cli("build", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(second.returncode, 0, second.stdout)
        second_bytes = {
            path.relative_to(workspace / "candidate").as_posix(): path.read_bytes()
            for path in (workspace / "candidate").rglob("*") if path.is_file()
        }
        self.assertEqual(first_bytes, second_bytes)


if __name__ == "__main__":
    unittest.main()
