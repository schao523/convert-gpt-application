from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "invoke_windows_test_environment.ps1"
REFERENCE = ROOT / "docs" / "PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md"


class WindowsTestEnvironmentContractTests(unittest.TestCase):
    def test_runner_and_failure_classification_are_documented(self) -> None:
        self.assertTrue(RUNNER.is_file())
        script = RUNNER.read_text(encoding="utf-8")
        reference = REFERENCE.read_text(encoding="utf-8")

        self.assertNotIn("Invoke-Expression", script)
        self.assertIn("PYTHONUTF8", script)
        self.assertIn("PYTHONIOENCODING", script)
        self.assertIn("GetFolderPath", script)
        self.assertIn("New-Item -ItemType HardLink", script)
        self.assertIn("git clone --no-hardlinks", reference)
        self.assertIn("smallest affected regression", reference)
        for classification in (
            "IMPLEMENTATION",
            "TEST_FIXTURE",
            "ENVIRONMENT",
            "TRANSIENT",
        ):
            self.assertIn(classification, reference)

    @unittest.skipUnless(os.name == "nt", "Windows-only environment probe")
    def test_probe_uses_system_temp_utf8_and_direct_argv(self) -> None:
        environment = dict(os.environ)
        poisoned = ROOT / ".tmp" / "must-not-be-used-as-system-temp"
        environment["TEMP"] = str(poisoned)
        environment["TMP"] = str(poisoned)

        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(RUNNER),
                "-Executable",
                sys.executable,
                "-CommandArgument",
                "--version",
            ],
            cwd=ROOT,
            env=environment,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads([line for line in completed.stdout.splitlines() if line][-1])
        self.assertEqual(report["schema"], "windows-test-environment-v1")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["classification"], "NONE")
        self.assertFalse(report["inside_repository"])
        self.assertEqual(report["environment"]["PYTHONUTF8"], "1")
        self.assertEqual(report["environment"]["PYTHONIOENCODING"], "utf-8")
        self.assertEqual(report["command"]["exit_code"], 0)
        self.assertEqual(report["command"]["status"], "PASS")
        self.assertFalse(Path(report["disposable_root"]).exists())
        self.assertFalse(str(report["system_temp"]).casefold().startswith(str(ROOT).casefold()))
        self.assertEqual(
            set(report["capabilities"]),
            {"filesystem", "hard_link", "atomic_replace", "git", "packaging"},
        )
        self.assertTrue(all(value == "PASS" for value in report["capabilities"].values()))

    @unittest.skipUnless(os.name == "nt", "Windows-only environment probe")
    def test_command_launch_failure_requires_triage_not_environment_repair(self) -> None:
        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(RUNNER),
                "-Executable",
                "missing-obvious-one-test-command.exe",
            ],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(completed.returncode, 0)
        report = json.loads([line for line in completed.stdout.splitlines() if line][-1])
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["classification"], "REQUIRES_TRIAGE")
        self.assertEqual(report["command"]["status"], "FAIL")
        self.assertTrue(report["diagnostics"])


if __name__ == "__main__":
    unittest.main()
