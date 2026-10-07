from __future__ import annotations

from hashlib import sha256
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


class PlanningWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        design = self.root / "design.zip"
        with zipfile.ZipFile(design, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(DESIGN_FIXTURE.iterdir(), key=lambda item: item.name):
                archive.write(path, path.name)
        self.workspace = self.root / "workspace"
        outcome = inspect_design_package(design, self.workspace, "create")
        self.assertEqual(outcome.status, "PASS")
        self.session_path = self.workspace / "session.json"
        self.proposal_path = self.root / "proposal.json"
        self.proposal_path.write_bytes(PLAN_FIXTURE.read_bytes())

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "plugin_builder.py"), *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
        )

    def document(self, completed: subprocess.CompletedProcess[str]) -> dict:
        self.assertEqual(completed.stderr, "")
        self.assertEqual(len(completed.stdout.splitlines()), 1)
        completed.stdout.encode("ascii")
        return json.loads(completed.stdout)

    def plan(self) -> tuple[dict, dict]:
        completed = self.run_cli(
            "plan", "--session", str(self.session_path), "--proposal", str(self.proposal_path), "--json"
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        return self.document(completed), json.loads((self.workspace / "implementation-plan.json").read_text(encoding="utf-8"))

    def proposal(self) -> dict:
        return json.loads(self.proposal_path.read_text(encoding="utf-8"))

    def write_proposal(self, payload: dict) -> None:
        self.proposal_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    def refresh_recipe_hash(self, recipe: dict) -> None:
        if "inline_json" in recipe:
            payload = (
                json.dumps(recipe["inline_json"], ensure_ascii=True, indent=2, sort_keys=True)
                + "\n"
            ).encode("ascii")
        else:
            payload = recipe["inline_text"].replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        recipe["source_sha256"] = sha256(payload).hexdigest()

    def test_plan_covers_every_design_requirement_and_derives_multiple_skills(self) -> None:
        document, plan = self.plan()
        self.assertEqual(document["stage"], "W1")
        self.assertEqual(plan["schema"], "plugin-builder-implementation-plan-v2")
        self.assertEqual(plan["preflight_evidence"]["schema"], "plugin-builder-preflight-v1")
        self.assertRegex(plan["preflight_evidence"]["materialized_tree_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual([item["id"] for item in plan["requirements"]], ["AC1", "RQ1"])
        self.assertEqual(
            [item["name"] for item in plan["skills"]],
            ["answering-structured-requests", "checking-traceability"],
        )
        self.assertTrue(all(item["implementation_paths"] and item["evidence_targets"] for item in plan["requirements"]))

    def test_plan_preflight_rejects_missing_author_and_interface_before_w1(self) -> None:
        payload = self.proposal()
        manifest = next(item for item in payload["files"] if item["path"] == "plugin.json")
        manifest["inline_json"].pop("author")
        manifest["inline_json"]["extensions"]["com.openai"].pop("interface")
        self.refresh_recipe_hash(manifest)
        self.write_proposal(payload)

        completed = self.run_cli(
            "plan", "--session", str(self.session_path), "--proposal", str(self.proposal_path), "--json"
        )

        self.assertEqual(completed.returncode, 3)
        errors = self.document(completed)["errors"]
        self.assertIn("plan.preflight.portable_author_invalid:plugin.json", errors)
        self.assertIn("plan.preflight.portable_interface_invalid:plugin.json", errors)
        session = json.loads(self.session_path.read_text(encoding="utf-8"))
        self.assertIsNone(session["plan"])
        self.assertFalse((self.workspace / "candidate").exists())

    def test_plan_preflight_rejects_escaping_skill_reference_before_w1(self) -> None:
        payload = self.proposal()
        skill = next(
            item for item in payload["files"]
            if item["path"] == "skills/answering-structured-requests/SKILL.md"
        )
        skill["inline_text"] += "\n[escape](../../resources/Reference.md)\n"
        self.refresh_recipe_hash(skill)
        self.write_proposal(payload)

        completed = self.run_cli(
            "plan", "--session", str(self.session_path), "--proposal", str(self.proposal_path), "--json"
        )

        self.assertEqual(completed.returncode, 3)
        self.assertIn(
            "plan.preflight.reference_path_invalid:skills/answering-structured-requests/SKILL.md:../../resources/Reference.md",
            self.document(completed)["errors"],
        )
        self.assertFalse((self.workspace / "implementation-plan.json").exists())

    def test_plan_preflight_aggregates_static_failures_and_cleans_temporary_tree(self) -> None:
        candidate = self.workspace / "candidate"
        candidate.mkdir()
        sentinel = candidate / "sentinel.txt"
        sentinel.write_bytes(b"preserve me")
        payload = self.proposal()
        manifest = next(item for item in payload["files"] if item["path"] == "plugin.json")
        manifest["inline_json"].pop("author")
        self.refresh_recipe_hash(manifest)
        skill = next(
            item for item in payload["files"]
            if item["path"] == "skills/answering-structured-requests/SKILL.md"
        )
        skill["inline_text"] += "\n[escape](../../outside.md)\n"
        self.refresh_recipe_hash(skill)
        self.write_proposal(payload)

        completed = self.run_cli(
            "plan", "--session", str(self.session_path), "--proposal", str(self.proposal_path), "--json"
        )

        self.assertEqual(completed.returncode, 3)
        errors = self.document(completed)["errors"]
        self.assertEqual(errors, sorted(set(errors)))
        self.assertTrue(any("portable_author_invalid" in error for error in errors))
        self.assertTrue(any("reference_path_invalid" in error for error in errors))
        self.assertEqual(sentinel.read_bytes(), b"preserve me")
        self.assertEqual(list(self.workspace.glob(".plan-preflight-*")), [])

    def test_plan_records_reuse_bundle_and_validation_decisions(self) -> None:
        _, plan = self.plan()
        self.assertEqual(plan["implementation_decisions"]["reuse"], ["portable plugin validators"])
        self.assertEqual(plan["implementation_decisions"]["bundle"], ["tools/normalize.py"])
        self.assertIn("PLUGIN_STRUCTURE", {item["kind"] for item in plan["checks"]})
        recipes = {item["path"]: item for item in plan["files"]}
        self.assertEqual(recipes["skills/answering-structured-requests/references/Reference.md"]["source_path"], "input/Reference.md")

    def test_plan_requires_portable_manifest_and_declares_compatibility_overlay(self) -> None:
        _, plan = self.plan()
        recipes = {item["path"]: item for item in plan["files"]}
        self.assertIn("plugin.json", recipes)
        self.assertNotIn(".codex-plugin/plugin.json", recipes)
        self.assertIn("plugin.json", plan["expected_members"])
        self.assertIn(".codex-plugin/plugin.json", plan["expected_members"])
        self.assertEqual(
            plan["implementation_decisions"]["manifest_authority"],
            {"authority": "plugin.json", "compatibility_overlay": ".codex-plugin/plugin.json", "decision": "GENERATE"},
        )

    def test_legacy_overlay_only_proposal_is_adapted_before_w1(self) -> None:
        payload = self.proposal()
        portable = payload["files"][0]["inline_json"]
        payload["files"][0]["path"] = ".codex-plugin/plugin.json"
        payload["files"][0]["inline_json"] = plugin_authoring.legacy_overlay_from_portable(portable)
        payload["expected_members"].remove("plugin.json")
        self.write_proposal(payload)

        _, plan = self.plan()

        recipes = {item["path"]: item for item in plan["files"]}
        self.assertIn("plugin.json", recipes)
        self.assertNotIn(".codex-plugin/plugin.json", recipes)
        self.assertEqual(plan["implementation_decisions"]["manifest_authority"]["decision"], "ADAPT")

    def test_manifest_pair_is_part_of_plan_and_tools_hash_invalidation(self) -> None:
        planned, plan = self.plan()
        self.assertTrue({"plugin.json", ".codex-plugin/plugin.json"}.issubset(plan["expected_members"]))
        first_hash = planned["plan_sha256"]
        payload = self.proposal()
        payload["files"][0]["inline_json"]["extensions"]["com.openai"]["interface"]["defaultPrompt"] = ["First", "Second"]
        self.refresh_recipe_hash(payload["files"][0])
        self.write_proposal(payload)
        revised, _ = self.plan()
        self.assertNotEqual(revised["plan_sha256"], first_hash)

    def test_plan_classifies_and_binds_every_application_tool(self) -> None:
        _, plan = self.plan()
        tool = plan["tools"][0]
        self.assertEqual(tool["schema"], "plugin-builder-application-tool-v1")
        self.assertEqual(tool["implementation_kind"], "BUNDLED_LOCAL")
        self.assertEqual(tool["skill_bindings"], ["answering-structured-requests"])
        self.assertEqual(tool["requirement_ids"], ["RQ1"])
        self.assertEqual(tool["verification"]["argv"], ["python", "tools/normalize.py", "--self-test"])

    def test_unresolved_or_unbound_required_tool_blocks_w1(self) -> None:
        for mutation, expected in (
            (lambda tool: tool.__setitem__("implementation_kind", "UNRESOLVED"), "tool.normalize-input.unresolved_required"),
            (lambda tool: tool.__setitem__("skill_bindings", []), "tool.normalize-input.skill_binding_required"),
        ):
            with self.subTest(expected=expected):
                payload = self.proposal()
                mutation(payload["tools"][0])
                self.write_proposal(payload)
                planned = self.run_cli(
                    "plan", "--session", str(self.session_path), "--proposal", str(self.proposal_path), "--json"
                )
                self.assertEqual(planned.returncode, 2)
                self.assertIn(expected, self.document(planned)["errors"])
                approval = self.run_cli(
                    "approve-w1", "--session", str(self.session_path),
                    "--confirmed-by", "fixture owner", "--evidence", "reviewed plan", "--json",
                )
                self.assertEqual(approval.returncode, 2)
                self.assertIn(expected, self.document(approval)["errors"])
                self.proposal_path.write_bytes(PLAN_FIXTURE.read_bytes())

    def test_plan_rejects_invented_or_unowned_requirements(self) -> None:
        payload = self.proposal()
        payload["requirements"] = [item for item in payload["requirements"] if item["id"] != "AC1"]
        payload["requirements"].append({
            "id": "RQ999", "owner_skill": "answering-structured-requests",
            "implementation_paths": ["tools/normalize.py"], "evidence_targets": ["normalize-self-test"],
        })
        self.write_proposal(payload)
        completed = self.run_cli(
            "plan", "--session", str(self.session_path), "--proposal", str(self.proposal_path), "--json"
        )
        self.assertEqual(completed.returncode, 3)
        errors = self.document(completed)["errors"]
        self.assertIn("plan.requirement_uncovered:AC1", errors)
        self.assertIn("plan.requirement_invented:RQ999", errors)

    def test_plan_rejects_unrouted_or_unapproved_reference(self) -> None:
        payload = self.proposal()
        reference = next(item for item in payload["files"] if "/references/" in item["path"])
        reference["redistribution"]["state"] = "UNRESOLVED"
        skill = next(item for item in payload["files"] if item["path"] == "skills/answering-structured-requests/SKILL.md")
        skill["inline_text"] = skill["inline_text"].replace(
            "Read [the approved method](references/Reference.md), then ", ""
        )
        self.write_proposal(payload)

        completed = self.run_cli(
            "plan", "--session", str(self.session_path), "--proposal", str(self.proposal_path), "--json"
        )
        self.assertEqual(completed.returncode, 3)
        errors = self.document(completed)["errors"]
        self.assertIn(
            "plan.file_rights_unapproved:skills/answering-structured-requests/references/Reference.md",
            errors,
        )
        self.assertIn(
            "plan.reference_unrouted:skills/answering-structured-requests/references/Reference.md",
            errors,
        )

    def test_w1_binds_exact_plan_and_tool_hashes(self) -> None:
        planned, _ = self.plan()
        completed = self.run_cli(
            "approve-w1", "--session", str(self.session_path),
            "--confirmed-by", "fixture owner", "--evidence", "reviewed plan and tools", "--json",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        document = self.document(completed)
        session = json.loads(self.session_path.read_text(encoding="utf-8"))
        self.assertEqual(session["stage"], "S3")
        self.assertEqual(session["w1"]["plan_sha256"], planned["plan_sha256"])
        self.assertEqual(session["w1"]["tools_sha256"], planned["tools_sha256"])
        self.assertEqual(document["plan_sha256"], session["plan"]["sha256"])

    def test_plan_change_invalidates_w1_and_downstream_evidence(self) -> None:
        self.plan()
        approved = self.run_cli(
            "approve-w1", "--session", str(self.session_path),
            "--confirmed-by", "fixture owner", "--evidence", "reviewed plan", "--json",
        )
        self.assertEqual(approved.returncode, 0)
        session = json.loads(self.session_path.read_text(encoding="utf-8"))
        old_hash = session["plan"]["sha256"]
        session["candidate"] = {"path": "candidate", "sha256": "c" * 64, "plan_sha256": old_hash, "manifest_sha256": "d" * 64}
        session["verification"] = {"path": "verification.json", "sha256": "e" * 64, "candidate_sha256": "c" * 64, "results": []}
        session["w2"] = {"approved": True, "candidate_sha256": "c" * 64, "verification_sha256": "e" * 64, "confirmed_by": "owner", "evidence": "review"}
        session["package"] = {"path": "plugin.zip", "sha256": "f" * 64, "candidate_sha256": "c" * 64, "verification_sha256": "e" * 64, "member_manifest_sha256": "a" * 64}
        self.session_path.write_text(json.dumps(session), encoding="utf-8")
        payload = self.proposal()
        payload["plugin"]["description"] = "Revised non-behavioral description."
        payload["files"][0]["inline_json"]["description"] = "Revised non-behavioral description."
        self.refresh_recipe_hash(payload["files"][0])
        self.write_proposal(payload)

        completed = self.run_cli(
            "plan", "--session", str(self.session_path), "--proposal", str(self.proposal_path), "--json"
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        revised = json.loads(self.session_path.read_text(encoding="utf-8"))
        self.assertNotEqual(revised["plan"]["sha256"], old_hash)
        for key in ("w1", "candidate", "verification", "w2", "package"):
            self.assertIsNone(revised[key], key)
        self.assertEqual(revised["stage"], "W1")


if __name__ == "__main__":
    unittest.main()
