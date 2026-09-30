from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DESIGN = Path(__file__).parent / "fixtures/design-package-create"
PLAN = Path(__file__).parent / "fixtures/plan-create.json"


def _release_module():
    spec = importlib.util.spec_from_file_location("plugin_builder_release", ROOT / "scripts/build_marketplace_release.py")
    if spec is None or spec.loader is None:
        raise AssertionError("release module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StandaloneArtifactTests(unittest.TestCase):
    def test_t7_generated_artifact_runs_create_update_and_local_tool_without_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            release_root = root / "release"
            _release_module().build_release(ROOT, release_root, "0.1.0")
            plugin = release_root / "plugins/plugin-builder"
            self.assertTrue((plugin / "scripts/vendor/obvious_one_plugin_framework/plugin_authoring/__init__.py").is_file())
            external = root / "external"
            external.mkdir()
            design_zip = external / "design.zip"
            with zipfile.ZipFile(design_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(DESIGN.iterdir()):
                    archive.write(path, path.name)
            create_proposal = external / "create-proposal.json"
            create_proposal.write_bytes(PLAN.read_bytes())
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

            update_proposal = json.loads(PLAN.read_text(encoding="utf-8"))
            update_proposal["operation"] = "update"
            baseline = create / "dist/sample-plugin.zip"
            with zipfile.ZipFile(baseline) as archive:
                expected = {item.filename for item in archive.infolist() if not item.is_dir()}
            expected.add("PLUGIN-BUILDER-CHANGES.json")
            update_proposal["expected_members"] = sorted(expected)
            update_proposal_path = external / "update-proposal.json"
            update_proposal_path.write_text(json.dumps(update_proposal, sort_keys=True), encoding="utf-8")
            update = external / "update"
            update_commands = [
                ("inspect", str(design_zip), "--workspace", str(update), "--operation", "update", "--baseline", str(baseline), "--json"),
                ("plan", "--session", str(update / "session.json"), "--proposal", str(update_proposal_path), "--json"),
                ("approve-w1", "--session", str(update / "session.json"), "--confirmed-by", "owner", "--evidence", "approved update", "--json"),
                ("build", "--session", str(update / "session.json"), "--json"),
                ("verify", "--session", str(update / "session.json"), "--json"),
                ("approve-w2", "--session", str(update / "session.json"), "--confirmed-by", "owner", "--evidence", "reviewed update", "--json"),
                ("package", "--session", str(update / "session.json"), "--json"),
            ]
            for command in update_commands:
                completed, document = run(*command)
                self.assertEqual(completed.returncode, 0, document)
            self.assertTrue((update / "dist/sample-plugin.zip").is_file())


if __name__ == "__main__":
    unittest.main()
