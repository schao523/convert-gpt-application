from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from obvious_one_plugin_framework.contract import load_contract
from obvious_one_plugin_framework.package_builder import build_package, verify_package


PLUGIN = Path(__file__).resolve().parents[1]
CONTRACT = PLUGIN / "openclaw" / "distribution.json"


class OpenClawReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.contract = load_contract(CONTRACT)

    def runtime_environment(self):
        environment = dict(os.environ)
        for name in (
            "COOL_BIBLE_TUTOR_DATA_DIR",
            "COOL_BIBLE_TUTOR_SOURCE_PDFS",
            "COOL_BIBLE_TUTOR_RAG_PYTHON",
            "COOL_BIBLE_TUTOR_RAG_ROOT",
            "PLUGIN_DATA",
        ):
            environment.pop(name, None)
        return environment

    def test_lightweight_package_is_complete_without_large_bible_assets(self):
        result = build_package(self.contract, self.root / "cool-bible-tutor")
        output = result.output

        self.assertTrue(
            (output / "vendor/obvious-one-runtime/obvious_one_runtime/setup.py").is_file()
        )
        self.assertTrue((output / "assets/scripture/cuv.sqlite3").is_file())
        self.assertTrue((output / "assets/openclaw/remote-assets.json").is_file())
        self.assertFalse((output / "assets/rag/cuv-rag-index.sqlite3").exists())
        self.assertEqual(list(output.rglob("*.pdf")), [])
        self.assertFalse((output / "openclaw.plugin.json").exists())
        self.assertFalse((output / "tests/test_openclaw_release.py").exists())
        self.assertFalse((output / "tests/test_vendored_runtime.py").exists())
        self.assertLess(result.total_bytes, 47_185_920)
        self.assertEqual(
            len(list((output / "skills").glob("*/SKILL.md"))),
            8,
        )
        package = json.loads((output / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["name"], "@obvious-one/cool-bible-tutor")
        self.assertEqual(package["version"], "2.4.6")
        self.assertIn("setup-rag --accept-downloads", (output / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(verify_package(self.contract, output), result)

    def test_repeat_build_has_identical_manifest_and_file_hashes(self):
        first = build_package(self.contract, self.root / "first")
        second = build_package(self.contract, self.root / "second")
        first_manifest = json.loads(
            (first.output / "CONTENT-MANIFEST.json").read_text(encoding="utf-8")
        )
        second_manifest = json.loads(
            (second.output / "CONTENT-MANIFEST.json").read_text(encoding="utf-8")
        )
        self.assertEqual(first_manifest, second_manifest)
        self.assertEqual(first.content_sha256, second.content_sha256)

    def test_lightweight_launcher_validates_frozen_core_without_source_pdfs(self):
        output = build_package(self.contract, self.root / "cool-bible-tutor").output
        launcher = output / "scripts" / "cool_bible_tutor.py"

        status = subprocess.run(
            [sys.executable, "-B", str(launcher), "status", "--json"],
            cwd=output,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=self.runtime_environment(),
        )
        verification = subprocess.run(
            [sys.executable, "-B", str(launcher), "verify", "--json"],
            cwd=output,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=self.runtime_environment(),
        )

        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(json.loads(status.stdout)["core_status"], "core_ready")
        self.assertEqual(verification.returncode, 0, verification.stderr)
        self.assertTrue(json.loads(verification.stdout)["production_ready"])

    def test_lightweight_launcher_retrieves_exact_verse_without_source_pdfs(self):
        output = build_package(self.contract, self.root / "cool-bible-tutor").output
        launcher = output / "scripts" / "cool_bible_tutor.py"
        payloads = []
        for root, candidate in (
            (PLUGIN, PLUGIN / "scripts" / "cool_bible_tutor.py"),
            (output, launcher),
        ):
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(candidate),
                    "passage",
                    "約翰福音 3:16",
                    "--format",
                    "json",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=self.runtime_environment(),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payloads.append(json.loads(completed.stdout))

        self.assertEqual(payloads[0], payloads[1])
        self.assertEqual(payloads[1]["canonical_reference"], "約翰福音 3:16")
        self.assertEqual(payloads[1]["trust_status"], "verified")

    def test_lightweight_package_declares_layered_runtime_compatibility(self):
        output = build_package(self.contract, self.root / "cool-bible-tutor").output
        contract = json.loads(
            (output / "assets" / "openclaw" / "runtime-compatibility.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(contract["artifact_type"], "compatible-bundle")
        self.assertEqual(contract["bundle_format"], "codex")
        self.assertEqual(contract["execution_contract"], "inline-launcher")
        self.assertEqual(contract["skill_count"], 8)
        self.assertEqual(
            set(contract["readiness_layers"]),
            {"package", "skills", "exact_retrieval", "semantic_rag", "review", "publication"},
        )
        self.assertFalse(contract["native_openclaw_plugin"])


if __name__ == "__main__":
    unittest.main()
