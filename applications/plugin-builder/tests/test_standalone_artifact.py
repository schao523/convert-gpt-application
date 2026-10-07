from __future__ import annotations

import importlib.util
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from obvious_one_plugin_framework.workbench_handoff import normalize_handoff_archive


ROOT = Path(__file__).resolve().parents[1]
DESIGN = Path(__file__).parent / "fixtures/design-package-legacy"
PLAN = Path(__file__).parent / "fixtures/plan-create.json"
INTEROP = ROOT.parents[1] / "tests/fixtures/workbench-handoff"


def _write_deterministic_zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in sorted(members.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, payload)


def _members(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def _release_module():
    spec = importlib.util.spec_from_file_location("plugin_builder_release", ROOT / "scripts/build_marketplace_release.py")
    if spec is None or spec.loader is None:
        raise AssertionError("release module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StandaloneArtifactTests(unittest.TestCase):
    def test_extracted_artifact_accepts_canonical_full_and_delta_without_repository_imports(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            release_root = root / "release"
            _release_module().build_release(ROOT, release_root, "1.0.1")
            plugin = release_root / "plugins/plugin-builder"

            full_source = root / "full-source.zip"
            _write_deterministic_zip(full_source, _members(INTEROP / "full"))
            full = root / "full-canonical.zip"
            full_result = normalize_handoff_archive(full_source, root / "full-tree", full)
            self.assertEqual(full_result.status, "PASS", full_result.diagnostics)

            baseline_members = _members(INTEROP / "delta/baseline")
            baseline = root / "baseline.zip"
            _write_deterministic_zip(baseline, baseline_members)
            delta_members = {
                name: payload for name, payload in _members(INTEROP / "delta").items()
                if not name.startswith("baseline/")
            }
            delta_manifest = json.loads(delta_members["delta_handoff_manifest.json"])
            delta_manifest["baseline"]["archive_sha256"] = sha256(baseline.read_bytes()).hexdigest()
            delta_members["delta_handoff_manifest.json"] = (
                json.dumps(delta_manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
            ).encode("ascii")
            delta_source = root / "delta-source.zip"
            _write_deterministic_zip(delta_source, delta_members)
            delta = root / "delta-canonical.zip"
            delta_result = normalize_handoff_archive(delta_source, root / "delta-tree", delta)
            self.assertEqual(delta_result.status, "PASS", delta_result.diagnostics)

            environment = {
                key: value for key, value in os.environ.items()
                if key.upper() not in {"PYTHONPATH", "PYTHONHOME"}
                and str(ROOT.parents[1]).casefold() not in value.casefold()
            }

            def inspect(*arguments: str) -> dict:
                completed = subprocess.run(
                    [sys.executable, "-B", str(plugin / "scripts/plugin_builder.py"), "inspect", *arguments, "--json"],
                    cwd=root, env=environment, capture_output=True, text=True,
                    encoding="utf-8", errors="strict", check=False,
                )
                self.assertEqual(completed.stderr, "")
                self.assertEqual(len(completed.stdout.splitlines()), 1)
                document = json.loads(completed.stdout)
                self.assertEqual(completed.returncode, 0, document)
                return document

            created = inspect(str(full), "--workspace", str(root / "create"), "--operation", "create")
            updated = inspect(
                str(delta), "--workspace", str(root / "update"), "--operation", "update",
                "--baseline", str(baseline),
            )
            self.assertEqual((created["status"], created["stage"]), ("PASS", "S2"))
            self.assertEqual((updated["status"], updated["stage"]), ("PASS", "S2"))
            self.assertEqual(
                (root / "update/baseline/skills/existing/SKILL.md").read_bytes(),
                baseline_members["skills/existing/SKILL.md"],
            )

    def test_t7_generated_artifact_runs_create_update_and_local_tool_without_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            release_root = root / "release"
            _release_module().build_release(ROOT, release_root, "1.0.1")
            plugin = release_root / "plugins/plugin-builder"
            self.assertTrue((plugin / "scripts/vendor/obvious_one_plugin_framework/plugin_authoring/__init__.py").is_file())
            external = root / "external"
            external.mkdir()
            design_zip = external / "design.zip"
            with zipfile.ZipFile(design_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(DESIGN.rglob("*")):
                    if path.is_file():
                        archive.write(path, path.relative_to(DESIGN).as_posix())
            create_proposal = external / "create-proposal.json"
            create_payload = json.loads(PLAN.read_text(encoding="utf-8"))
            reference = next(item for item in create_payload["files"] if "/references/" in item["path"])
            reference["source_path"] = "input/professional_knowledge/reference.md"
            reference["source_sha256"] = sha256((DESIGN / "professional_knowledge/reference.md").read_bytes()).hexdigest()
            create_proposal.write_text(json.dumps(create_payload), encoding="utf-8")
            environment = {
                key: value for key, value in os.environ.items()
                if key.upper() not in {"PYTHONPATH", "PYTHONHOME"} and str(ROOT).casefold() not in value.casefold()
            }

            def run(*arguments: str):
                completed = subprocess.run(
                    [sys.executable, "-B", str(plugin / "scripts/plugin_builder.py"), *arguments],
                    cwd=external, env=environment, capture_output=True, text=True,
                    encoding="utf-8", errors="strict", check=False,
                )
                if completed.stderr or len(completed.stdout.splitlines()) != 1:
                    raise AssertionError(completed.stderr or completed.stdout)
                return completed, json.loads(completed.stdout)

            self.assertEqual(run("status", "--json")[0].returncode, 0)
            create = external / "create"
            commands = [
                ("inspect", str(design_zip), "--workspace", str(create), "--operation", "create", "--json"),
                ("plan", "--session", str(create / "session.json"), "--proposal", str(create_proposal), "--json"),
                ("approve-w1", "--session", str(create / "session.json"), "--confirmed-by", "owner", "--evidence", "approved", "--json"),
                ("build", "--session", str(create / "session.json"), "--json"),
                ("verify", "--session", str(create / "session.json"), "--json"),
                ("approve-w2", "--session", str(create / "session.json"), "--confirmed-by", "owner", "--evidence", "reviewed", "--json"),
                ("package", "--session", str(create / "session.json"), "--json"),
            ]
            for command in commands:
                completed, document = run(*command)
                self.assertEqual(completed.returncode, 0, document)
            report = json.loads((create / "verification-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["tools"][0]["state"], "PASS")

            update_proposal = json.loads(json.dumps(create_payload))
            update_proposal["operation"] = "update"
            baseline = create / "dist/sample-plugin.zip"
            with zipfile.ZipFile(baseline, "a", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("sample-plugin/owner-notes.txt", b"owner bytes\x00preserved")
            with zipfile.ZipFile(baseline) as archive:
                expected = {"/".join(item.filename.split("/")[1:]) for item in archive.infolist() if not item.is_dir()}
            expected.add("PLUGIN-BUILDER-CHANGES.json")
            update_proposal["expected_members"] = sorted(expected)
            update_proposal_path = external / "update-proposal.json"
            update_proposal_path.write_text(json.dumps(update_proposal, sort_keys=True), encoding="utf-8")
            update = external / "update"
            update_commands = [
                ("inspect", str(design_zip), "--workspace", str(update), "--operation", "update", "--baseline", str(baseline), "--json"),
                ("plan", "--session", str(update / "session.json"), "--proposal", str(update_proposal_path), "--json"),
                ("approve-w1", "--session", str(update / "session.json"), "--confirmed-by", "owner", "--evidence", "approved update", "--json"),
                ("resolve-update", "--session", str(update / "session.json"), "--member", "owner-notes.txt", "--decision", "keep", "--evidence", "owner preservation decision", "--json"),
                ("build", "--session", str(update / "session.json"), "--json"),
                ("verify", "--session", str(update / "session.json"), "--json"),
                ("approve-w2", "--session", str(update / "session.json"), "--confirmed-by", "owner", "--evidence", "reviewed update", "--json"),
                ("package", "--session", str(update / "session.json"), "--json"),
            ]
            for command in update_commands:
                completed, document = run(*command)
                self.assertEqual(completed.returncode, 0, document)
            self.assertTrue((update / "dist/sample-plugin.zip").is_file())
            with zipfile.ZipFile(update / "dist/sample-plugin.zip") as archive:
                self.assertEqual(archive.read("sample-plugin/owner-notes.txt"), b"owner bytes\x00preserved")

            evidence_root = external / "evidence"
            evidence_root.mkdir()
            evidence_body = b"installed standalone T7 evidence\n"
            evidence_digest = sha256(evidence_body).hexdigest()
            (evidence_root / f"{evidence_digest}.log").write_bytes(evidence_body)
            runtime_result = {
                "schema": "plugin-builder-runtime-result-v1",
                "runtime": {"name": "Codex", "version": "test", "os": os.name, "clean_workspace": True, "discovery_observed": False, "repository_absent": True},
                "artifact": {"zip_sha256": sha256((release_root / ".release-manifest.json").read_bytes()).hexdigest(), "member_manifest_sha256": "d" * 64},
                "scenarios": [
                    {"id": f"T{index}", "state": "RUNTIME VERIFIED" if index == 7 else "NOT VERIFIED", "result": "PASS" if index == 7 else "NOT VERIFIED", "evidence_sha256": evidence_digest if index == 7 else None, "limitations": []}
                    for index in range(1, 8)
                ],
                "tools": [{"tool_id": "normalize-input", "implementation_kind": "BUNDLED_LOCAL", "state": "RUNTIME VERIFIED", "executed": True, "network_contacted": False, "contract_sha256": "e" * 64, "skill_bindings": ["answering-structured-requests"]}],
                "overall_state": "RUNTIME VERIFIED",
            }
            result_path = external / "runtime-result.json"
            result_path.write_text(json.dumps(runtime_result, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="ascii")
            evidence_zip = external / "runtime-evidence.zip"
            completed, document = run(
                "package-runtime-evidence", "--result", str(result_path),
                "--evidence-root", str(evidence_root), "--output", str(evidence_zip), "--json",
            )
            self.assertEqual(completed.returncode, 0, document)
            self.assertTrue(evidence_zip.is_file())


if __name__ == "__main__":
    unittest.main()
