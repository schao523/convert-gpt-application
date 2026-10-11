from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from obvious_one_plugin_framework.plugin_onboarding import load_repair_contract
from tests.framework.plugin_onboarding_fixtures import write_legacy_repair_fixture


APPLICATION = Path(__file__).resolve().parents[1]
SCRIPT = APPLICATION / "scripts" / "build_repaired_release.py"


def _load_launcher():
    spec = importlib.util.spec_from_file_location("growing_with_children_release", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("release launcher could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GrowingWithChildrenReleaseBuilderTests(unittest.TestCase):
    def test_compact_fixture_uses_generic_repair_and_stays_below_output(self) -> None:
        launcher = _load_launcher()
        with tempfile.TemporaryDirectory(prefix="growing-release-test-") as temporary:
            root = Path(temporary)
            fixture = write_legacy_repair_fixture(root / "fixture")
            contract_path = root / "fixture-contract.json"
            contract_path.write_text(
                json.dumps(fixture.contract_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            output = root / "output"

            with patch.object(launcher, "CONTRACT_PATH", contract_path):
                result = launcher.build_repaired_release(fixture.archive, output)

            self.assertTrue(result.archive.is_relative_to(output))
            self.assertTrue(result.metadata.is_relative_to(output))
            self.assertEqual(result.source_archive_sha256, load_repair_contract(contract_path).source_archive_sha256)
            self.assertEqual(sorted(item.name for item in output.iterdir()), [
                "package-metadata.json",
                "sample-plugin-1.0.2.zip",
            ])

    def test_wrong_source_digest_fails_without_output_artifacts(self) -> None:
        launcher = _load_launcher()
        with tempfile.TemporaryDirectory(prefix="growing-release-wrong-") as temporary:
            root = Path(temporary)
            source = root / "wrong.zip"
            source.write_bytes(b"not the approved archive")
            output = root / "output"

            with self.assertRaises(Exception):
                launcher.build_repaired_release(source, output)

            self.assertFalse(output.exists())

    def test_json_cli_failure_is_ascii_safe_and_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="growing-release-cli-") as temporary:
            root = Path(temporary)
            source = root / "wrong.zip"
            source.write_bytes(b"wrong")
            output = root / "output"
            completed = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--source", str(source), "--output", str(output), "--json"],
                cwd=APPLICATION.parents[1],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertTrue(completed.stdout.isascii())
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["result_schema_version"], 1)
            self.assertEqual(payload["operation"], "build-growing-with-children-repair")
            self.assertEqual(payload["status"], "FAIL")
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
