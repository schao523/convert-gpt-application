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

    @unittest.skipUnless(os.name == "nt", "Windows-only environment probe")
    def test_in_process_invocation_restores_caller_environment(self) -> None:
        command = (
            "$env:TEMP='caller-temp'; $env:TMP='caller-tmp'; "
            "$env:PYTHONUTF8='caller-utf8'; Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue; "
            f"& '{RUNNER}' -ProbeOnly; "
            "[pscustomobject]@{TEMP=$env:TEMP;TMP=$env:TMP;PYTHONUTF8=$env:PYTHONUTF8;"
            "PYTHONIOENCODING=[Environment]::GetEnvironmentVariable('PYTHONIOENCODING')} | "
            "ConvertTo-Json -Compress"
        )
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        restored = json.loads([line for line in completed.stdout.splitlines() if line][-1])
        self.assertEqual(restored["TEMP"], "caller-temp")
        self.assertEqual(restored["TMP"], "caller-tmp")
        self.assertEqual(restored["PYTHONUTF8"], "caller-utf8")
        self.assertIsNone(restored["PYTHONIOENCODING"])

    @unittest.skipUnless(os.name == "nt", "Windows-only environment probe")
    def test_cleanup_failure_still_emits_structured_environment_result(self) -> None:
        command = (
            "function Remove-Item { throw 'simulated cleanup failure' }; "
            f"& '{RUNNER}' -ProbeOnly"
        )
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(completed.returncode, 0)
        lines = [line for line in completed.stdout.splitlines() if line]
        self.assertTrue(lines, completed.stderr)
        report = json.loads(lines[-1])
        disposable_root = Path(report["disposable_root"])
        expected_parent = Path(report["system_temp"]) / "obvious-one-plugin-tests"
        try:
            self.assertEqual(disposable_root.parent.resolve(), expected_parent.resolve())
            self.assertTrue(disposable_root.is_dir())
            self.assertEqual(report["schema"], "windows-test-environment-v1")
            self.assertEqual(report["status"], "BLOCKED")
            self.assertEqual(report["classification"], "ENVIRONMENT")
            self.assertTrue(any("cleanup failed" in item for item in report["diagnostics"]))
        finally:
            if disposable_root.parent.resolve() == expected_parent.resolve():
                quoted_root = str(disposable_root).replace("'", "''")
                cleanup = subprocess.run(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-Command",
                        f"Remove-Item -LiteralPath '{quoted_root}' -Recurse -Force",
                    ],
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(cleanup.returncode, 0, cleanup.stdout + cleanup.stderr)
        self.assertFalse(disposable_root.exists())


if __name__ == "__main__":
    unittest.main()
