from __future__ import annotations

from hashlib import sha256
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeKitBuilderTests(unittest.TestCase):
    def test_kit_is_deterministic_complete_and_bound_to_exact_release(self) -> None:
        release_builder = load(ROOT / "scripts/build_marketplace_release.py", "runtime_kit_release")
        kit_builder = load(ROOT / "tests/runtime/build-runtime-kit.py", "runtime_kit_builder")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            release = root / "release"
            release_builder.build_release(ROOT, release, "1.0.1")
            plugin_zip = root / "plugin.zip"
            release_builder.write_upload_archive(release, plugin_zip)
            first = root / "kit-a.zip"
            second = root / "kit-b.zip"
            self.assertEqual(
                kit_builder.build_kit(ROOT, release, plugin_zip, first),
                kit_builder.build_kit(ROOT, release, plugin_zip, second),
            )
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                names = set(archive.namelist())
                self.assertGreaterEqual(names, {
                    "plugin-builder.zip", "release-manifest.json", "identity.json",
                    "sample-legacy-handoff-v1.1.zip", "sample-normalized-handoff-v1.1.zip",
                    "runtime/T1-T7-runtime-scenarios.md", "runtime/T8-runtime-realization-scenario.md",
                    "runtime/runtime-result-schema.json", "runtime/runtime-result-v3-schema.json",
                    "runtime/runtime-result-v3-template.json", "scenario-inputs/t8-local-mcp-plan.json",
                })
                identity = json.loads(archive.read("identity.json"))
                self.assertEqual(identity["plugin_zip_sha256"], sha256(plugin_zip.read_bytes()).hexdigest())
                self.assertEqual(identity["installed_runtime_evidence"], "NOT VERIFIED")
                self.assertEqual(
                    identity["members"],
                    {name: sha256(archive.read(name)).hexdigest() for name in names - {"identity.json"}},
                )
                with zipfile.ZipFile(io.BytesIO(archive.read("sample-normalized-handoff-v1.1.zip"))) as handoff:
                    for plan_name in (
                        "runtime/create-plan.json",
                        "scenario-inputs/t3-unresolved-plan.json",
                        "scenario-inputs/t5-failing-tool-plan.json",
                        "scenario-inputs/t6-runtime-native-plan.json",
                        "scenario-inputs/t8-local-mcp-plan.json",
                    ):
                        plan = json.loads(archive.read(plan_name))
                        reference = next(item for item in plan["files"] if item["path"].endswith("/references/Reference.md"))
                        self.assertEqual(reference["source_path"], "input/professional_knowledge/reference.md")
                        member = reference["source_path"].removeprefix("input/")
                        self.assertEqual(reference["source_sha256"], sha256(handoff.read(member)).hexdigest())

    def test_unmodified_owner_kit_reaches_w1_without_proposal_repair(self) -> None:
        release_builder = load(ROOT / "scripts/build_marketplace_release.py", "runtime_kit_release_smoke")
        kit_builder = load(ROOT / "tests/runtime/build-runtime-kit.py", "runtime_kit_builder_smoke")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            release = root / "release"
            release_builder.build_release(ROOT, release, "1.0.1")
            plugin_zip = root / "plugin.zip"
            release_builder.write_upload_archive(release, plugin_zip)
            kit = root / "kit.zip"
            kit_builder.build_kit(ROOT, release, plugin_zip, kit)
            kit_root = root / "owner-kit"
            kit_root.mkdir()
            with zipfile.ZipFile(kit) as archive:
                archive.extractall(kit_root)
            plugin_root = root / "installed-copy"
            plugin_root.mkdir()
            with zipfile.ZipFile(kit_root / "plugin-builder.zip") as archive:
                archive.extractall(plugin_root)
            cli = plugin_root / "scripts/plugin_builder.py"
            workspace = root / "t1"
            environment = dict(os.environ)
            environment.pop("PYTHONPATH", None)
            environment.pop("PYTHONHOME", None)
            inspect = subprocess.run(
                [sys.executable, "-B", str(cli), "inspect", str(kit_root / "sample-legacy-handoff-v1.1.zip"),
                 "--workspace", str(workspace), "--operation", "create", "--json"],
                cwd=root, env=environment, capture_output=True, text=True, encoding="utf-8", check=False,
            )
            self.assertEqual(inspect.returncode, 0, inspect.stderr + inspect.stdout)
            plan = subprocess.run(
                [sys.executable, "-B", str(cli), "plan", "--session", str(workspace / "session.json"),
                 "--proposal", str(kit_root / "runtime/create-plan.json"), "--json"],
                cwd=root, env=environment, capture_output=True, text=True, encoding="utf-8", check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stderr + plan.stdout)
            self.assertEqual(json.loads(plan.stdout)["stage"], "W1")
            self.assertFalse((workspace / "candidate").exists())


if __name__ == "__main__":
    unittest.main()
