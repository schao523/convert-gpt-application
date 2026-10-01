from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURE = Path(__file__).parent / "fixtures" / "design-package-create"


class InspectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def archive_directory(self, source: Path, name: str = "design.zip") -> Path:
        destination = self.root / name
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(source.iterdir(), key=lambda item: item.name):
                if path.is_file():
                    archive.write(path, path.name)
        return destination

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

    def result(self, completed: subprocess.CompletedProcess[str]) -> dict:
        self.assertEqual(completed.stderr, "")
        self.assertEqual(len(completed.stdout.splitlines()), 1)
        completed.stdout.encode("ascii")
        return json.loads(completed.stdout)

    def test_inspect_normalizes_conforming_approved_package(self) -> None:
        archive = self.archive_directory(FIXTURE)
        workspace = self.root / "workspace"
        completed = self.run_cli(
            "inspect",
            str(archive),
            "--workspace",
            str(workspace),
            "--operation",
            "create",
            "--json",
        )

        self.assertEqual(completed.returncode, 0, completed.stdout)
        document = self.result(completed)
        self.assertEqual(document["status"], "PASS")
        self.assertEqual(document["stage"], "S2")
        inspection = json.loads((workspace / "inspection.json").read_text(encoding="utf-8"))
        session = json.loads((workspace / "session.json").read_text(encoding="utf-8"))
        self.assertEqual(inspection["schema"], "plugin-builder-inspection-v1")
        self.assertEqual(inspection["operation"], "create")
        self.assertEqual(
            [item["path"] for item in inspection["authoritative_files"]],
            ["Design_APPROVED.md", "Reference.md"],
        )
        self.assertEqual(inspection["resources"][0]["path"], "Reference.md")
        self.assertEqual(session["schema_version"], 2)
        self.assertEqual(session["stage"], "S2")
        self.assertEqual(session["inspection"]["path"], "inspection.json")
        self.assertEqual(session["requirements"], [
            {"id": "AC1", "required": True, "source_paths": ["input/Design_APPROVED.md"]},
            {"id": "RQ1", "required": True, "source_paths": ["input/Design_APPROVED.md", "input/Reference.md"]},
        ])

    def test_inspect_update_requires_safe_baseline(self) -> None:
        archive = self.archive_directory(FIXTURE)
        missing = self.run_cli(
            "inspect", str(archive), "--workspace", str(self.root / "missing"),
            "--operation", "update", "--json",
        )
        self.assertEqual(missing.returncode, 2)
        self.assertIn("baseline.required_for_update", self.result(missing)["errors"])

        unsafe = self.root / "unsafe.zip"
        with zipfile.ZipFile(unsafe, "w") as baseline:
            baseline.writestr("../escape.txt", "escape")
        rejected = self.run_cli(
            "inspect", str(archive), "--workspace", str(self.root / "unsafe-workspace"),
            "--operation", "update", "--baseline", str(unsafe), "--json",
        )
        self.assertEqual(rejected.returncode, 3)
        self.assertIn("baseline.archive_path_escape", self.result(rejected)["errors"])
        self.assertFalse((self.root / "escape.txt").exists())

    def test_wrapped_update_baseline_is_normalized_to_plugin_relative_bytes(self) -> None:
        archive = self.archive_directory(FIXTURE)
        baseline = self.root / "wrapped.zip"
        with zipfile.ZipFile(baseline, "w", compression=zipfile.ZIP_DEFLATED) as output:
            output.writestr("sample-plugin/plugin.json", "{}\n")
            output.writestr("sample-plugin/owner-notes.txt", b"owner\x00bytes")
        workspace = self.root / "wrapped-workspace"

        completed = self.run_cli(
            "inspect", str(archive), "--workspace", str(workspace),
            "--operation", "update", "--baseline", str(baseline), "--json",
        )

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual((workspace / "baseline/owner-notes.txt").read_bytes(), b"owner\x00bytes")
        self.assertFalse((workspace / "baseline/sample-plugin").exists())
        inspection = json.loads((workspace / "inspection.json").read_text(encoding="utf-8"))
        self.assertEqual(inspection["baseline"]["envelope_profile"], "PORTABLE_SINGLE_DIRECTORY")

    def test_inspect_blocks_missing_approval_and_required_resource(self) -> None:
        source = self.root / "source"
        shutil.copytree(FIXTURE, source)
        handoff_path = source / "workbench-handoff.json"
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        handoff["approval"]["state"] = "draft"
        handoff_path.write_text(json.dumps(handoff, sort_keys=True), encoding="utf-8")
        manifest_path = source / "package-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["canonical_handoff"]["sha256"] = sha256(handoff_path.read_bytes()).hexdigest()
        manifest["canonical_handoff"]["size"] = handoff_path.stat().st_size
        manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
        (source / "Reference.md").unlink()

        completed = self.run_cli(
            "inspect", str(self.archive_directory(source, "blocked.zip")),
            "--workspace", str(self.root / "blocked"), "--operation", "create", "--json",
        )
        self.assertEqual(completed.returncode, 2)
        document = self.result(completed)
        self.assertEqual(document["status"], "BLOCKED")
        self.assertEqual(document["stage"], "F1")
        self.assertIn("approval.not_approved", document["errors"])
        self.assertIn("package.declared_member_missing:Reference.md", document["errors"])

    def test_inspect_is_deterministic_and_persists_only_relative_paths(self) -> None:
        archive = self.archive_directory(FIXTURE)
        first = self.root / "one" / "workspace"
        second = self.root / "two" / "workspace"
        for workspace in (first, second):
            completed = self.run_cli(
                "inspect", str(archive), "--workspace", str(workspace),
                "--operation", "create", "--json",
            )
            self.assertEqual(completed.returncode, 0, completed.stdout)

        self.assertEqual((first / "inspection.json").read_bytes(), (second / "inspection.json").read_bytes())
        self.assertEqual((first / "session.json").read_bytes(), (second / "session.json").read_bytes())
        serialized = (first / "inspection.json").read_text(encoding="utf-8") + (first / "session.json").read_text(encoding="utf-8")
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("\\", serialized)


if __name__ == "__main__":
    unittest.main()
