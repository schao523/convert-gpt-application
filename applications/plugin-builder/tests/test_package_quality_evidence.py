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


class PackageQualityEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _ready(self, root: Path | None = None) -> Path:
        workspace = prepared_workspace(root or self.root)
        self.assertEqual(run_cli("build", "--session", str(workspace / "session.json"), "--json").returncode, 0)
        verified = run_cli("verify", "--session", str(workspace / "session.json"), "--json")
        self.assertEqual(verified.returncode, 0, verified.stdout)
        approved = run_cli(
            "approve-w2", "--session", str(workspace / "session.json"),
            "--confirmed-by", "owner", "--evidence", "reviewed evidence", "--json",
        )
        self.assertEqual(approved.returncode, 0, approved.stdout)
        return workspace

    def _package(self, workspace: Path):
        return run_cli("package", "--session", str(workspace / "session.json"), "--json")

    def test_verification_and_sidecar_bind_approved_quality_evidence(self) -> None:
        workspace = self._ready()
        report = json.loads((workspace / "verification-report.json").read_text(encoding="utf-8"))
        plan = json.loads((workspace / "implementation-plan.json").read_text(encoding="utf-8"))
        self.assertEqual(report["schema"], "plugin-builder-verification-report-v2")
        self.assertEqual(report["preflight_evidence"], plan["preflight_evidence"])
        self.assertEqual(report["tools"][0]["declared_argv"], ["{python}", "tools/normalize.py", "--self-test"])
        self.assertEqual(report["tools"][0]["adapter"], "CURRENT_PYTHON")
        self.assertTrue(Path(report["tools"][0]["observed_argv"][0]).is_absolute())
        self.assertEqual(report["evidence_states"]["structural_validation"], "STATICALLY VERIFIED")
        self.assertEqual(report["evidence_states"]["installation"], "NOT VERIFIED")
        self.assertEqual(report["evidence_states"]["tool_execution"], "STATICALLY VERIFIED")
        self.assertEqual(report["evidence_states"]["reference_consultation"], "NOT VERIFIED")
        self.assertEqual(report["evidence_states"]["conversation"], "NOT VERIFIED")

        packaged = self._package(workspace)
        self.assertEqual(packaged.returncode, 0, packaged.stdout)
        metadata_path = workspace / "dist/package-metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        session = json.loads((workspace / "session.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["schema"], "plugin-builder-package-v2")
        self.assertEqual(metadata["preflight_evidence"], plan["preflight_evidence"])
        self.assertEqual(metadata["manifest_profile"], plan["preflight_evidence"]["manifest_profile"])
        self.assertEqual(metadata["command_evidence"], report["tools"])
        self.assertEqual(metadata["evidence_states"], report["evidence_states"])
        self.assertEqual(session["package"]["metadata_path"], "dist/package-metadata.json")
        self.assertEqual(session["package"]["metadata_sha256"], sha256(metadata_path.read_bytes()).hexdigest())
        with zipfile.ZipFile(workspace / "dist/sample-plugin.zip") as archive:
            self.assertNotIn("package-metadata.json", archive.namelist())

    def test_wrapped_archive_matches_candidate_and_sidecar_remains_external(self) -> None:
        workspace = self._ready()
        packaged = self._package(workspace)
        self.assertEqual(packaged.returncode, 0, packaged.stdout)
        archive_path = workspace / "dist/sample-plugin.zip"
        extracted = self.root / "extracted-quality"
        plugin_authoring.extract_archive(archive_path, extracted)
        located = plugin_authoring.locate_plugin_archive_root(extracted)
        self.assertEqual(located.profile, "PORTABLE_SINGLE_DIRECTORY")
        self.assertTrue((located.path / "plugin.json").is_file())
        self.assertEqual(plugin_authoring.tree_manifest(located.path), plugin_authoring.tree_manifest(workspace / "candidate"))
        with zipfile.ZipFile(archive_path) as archive:
            self.assertIn("sample-plugin/plugin.json", archive.namelist())
            self.assertFalse(any(name.endswith("package-metadata.json") for name in archive.namelist()))

    def test_existing_archive_or_sidecar_tampering_is_rejected(self) -> None:
        for index, (relative, expected) in enumerate((
            ("dist/sample-plugin.zip", "package.existing_archive_sha256_mismatch"),
            ("dist/package-metadata.json", "package.existing_metadata_sha256_mismatch"),
        )):
            with self.subTest(relative=relative):
                case_root = self.root / f"case-{index}"
                case_root.mkdir()
                workspace = self._ready(case_root)
                self.assertEqual(self._package(workspace).returncode, 0)
                (workspace / relative).write_bytes(b"tampered\n")
                rejected = self._package(workspace)
                self.assertEqual(rejected.returncode, 2, rejected.stdout)
                self.assertIn(expected, read_result(rejected)["errors"])


if __name__ == "__main__":
    unittest.main()
