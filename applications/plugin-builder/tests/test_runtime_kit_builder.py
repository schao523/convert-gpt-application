from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
