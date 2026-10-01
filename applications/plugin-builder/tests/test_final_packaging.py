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

from test_create_candidate import prepared_workspace, read_result, run_cli
from plugin_builder_core.bootstrap import plugin_authoring


def _failing_tool(proposal: dict) -> None:
    recipe = next(item for item in proposal["files"] if item["path"] == "tools/normalize.py")
    recipe["inline_text"] = "raise SystemExit(11)\n"
    recipe["source_sha256"] = sha256(recipe["inline_text"].encode("utf-8")).hexdigest()


class FinalPackagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _ready(self, *, approve: bool = True, failing: bool = False) -> Path:
        workspace = prepared_workspace(self.root, mutate=_failing_tool if failing else None)
        self.assertEqual(run_cli("build", "--session", str(workspace / "session.json"), "--json").returncode, 0)
        verified = run_cli("verify", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(verified.returncode, 2 if failing else 0, verified.stdout)
        if approve:
            approved = run_cli("approve-w2", "--session", str(workspace / "session.json"), "--confirmed-by", "owner", "--evidence", "reviewed evidence", "--json")
            self.assertEqual(approved.returncode, 2 if failing else 0, approved.stdout)
        return workspace

    def _package(self, workspace: Path):
        return run_cli("package", "--session", str(workspace / "session.json"), "--json")

    def test_package_is_blocked_before_w2(self) -> None:
        workspace = self._ready(approve=False)
        completed = self._package(workspace)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("package.w2_required", read_result(completed)["errors"])
        self.assertFalse((workspace / "dist/sample-plugin.zip").exists())

    def test_required_failure_emits_no_upload_zip(self) -> None:
        workspace = self._ready(failing=True)
        completed = self._package(workspace)
        self.assertEqual(completed.returncode, 2)
        self.assertFalse((workspace / "dist/sample-plugin.zip").exists())

    def test_package_uses_exact_w2_approved_candidate(self) -> None:
        workspace = self._ready()
        (workspace / "candidate/tools/normalize.py").write_text("tampered\n", encoding="utf-8")
        completed = self._package(workspace)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("package.candidate_sha256_mismatch", read_result(completed)["errors"])

    def test_two_packages_are_byte_identical_with_exact_members(self) -> None:
        workspace = self._ready()
        first = self._package(workspace)
        self.assertEqual(first.returncode, 0, first.stdout)
        archive = workspace / "dist/sample-plugin.zip"
        first_bytes = archive.read_bytes()
        first_inventory = plugin_authoring.inventory_archive(archive)
        second = self._package(workspace)
        self.assertEqual(second.returncode, 0, second.stdout)
        self.assertEqual(archive.read_bytes(), first_bytes)
        self.assertEqual(first_inventory, plugin_authoring.inventory_archive(archive))
        candidate_members = {item.path for item in plugin_authoring.tree_manifest(workspace / "candidate")}
        self.assertEqual(
            {item.path for item in first_inventory.members},
            {f"sample-plugin/{item}" for item in candidate_members},
        )
        with zipfile.ZipFile(archive) as packaged:
            self.assertIn("sample-plugin/plugin.json", packaged.namelist())
            self.assertIn("sample-plugin/.codex-plugin/plugin.json", packaged.namelist())

    def test_tool_files_dependencies_and_bindings_match_w2_candidate(self) -> None:
        workspace = self._ready()
        self.assertEqual(self._package(workspace).returncode, 0)
        metadata = json.loads((workspace / "dist/package-metadata.json").read_text(encoding="utf-8"))
        candidate = json.loads((workspace / "candidate/PLUGIN-BUILDER-MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["tool_bindings"], candidate["tool_bindings"])
        self.assertEqual(metadata["tool_contracts_sha256"], sha256(json.dumps(candidate["tool_contracts"], ensure_ascii=True, indent=2, sort_keys=True).encode("ascii") + b"\n").hexdigest())

    def test_extracted_zip_passes_plugin_skill_tool_and_safety_validation(self) -> None:
        workspace = self._ready()
        self.assertEqual(self._package(workspace).returncode, 0)
        extracted = self.root / "extracted"
        plugin_authoring.extract_archive(workspace / "dist/sample-plugin.zip", extracted)
        located = plugin_authoring.locate_plugin_archive_root(extracted)
        self.assertEqual(located.profile, "PORTABLE_SINGLE_DIRECTORY")
        self.assertEqual(plugin_authoring.validate_plugin_tree(located.path), ())
        metadata = json.loads((workspace / "dist/package-metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["extracted_validation"]["state"], "PASS")
        self.assertEqual(metadata["safety_validation"]["state"], "PASS")

    def test_packaging_failure_preserves_previous_artifact(self) -> None:
        workspace = self._ready()
        self.assertEqual(self._package(workspace).returncode, 0)
        archive = workspace / "dist/sample-plugin.zip"
        before = archive.read_bytes()
        (workspace / "verification-report.json").write_text("{}\n", encoding="ascii")
        failed = self._package(workspace)
        self.assertEqual(failed.returncode, 2)
        self.assertEqual(archive.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
