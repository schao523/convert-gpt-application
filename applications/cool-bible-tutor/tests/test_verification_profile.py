from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


APPLICATION = Path(__file__).resolve().parents[1]
CONVERSION = APPLICATION / "conversion.json"


def _profile() -> dict[str, object]:
    return json.loads(CONVERSION.read_text(encoding="utf-8"))["verification"]


def _expand(argv: list[str], diagnostics: Path, version: str) -> list[str]:
    values = {
        "python": sys.executable,
        "application_root": str(APPLICATION),
        "repository_root": str(APPLICATION.parents[1]),
        "diagnostics": str(diagnostics),
        "plugin_id": "cool-bible-tutor",
        "application_id": "cool-bible-tutor",
        "version": version,
    }
    return [argument.format_map(values) for argument in argv]


def _clean_environment(prefixes: list[str]) -> dict[str, str]:
    environment = dict(os.environ)
    for name in tuple(environment):
        if any(name.startswith(prefix) for prefix in prefixes):
            del environment[name]
    environment["PYTHONUTF8"] = "1"
    return environment


class CoolBibleTutorVerificationProfileTests(unittest.TestCase):
    def test_declared_smoke_commands_prove_bundled_runtime_invariants(self) -> None:
        profile = _profile()
        commands = {command["id"]: command for command in profile["commands"]}
        self.assertEqual(
            list(commands),
            ["distribution-audit", "exact-passage", "runtime-status"],
        )

        with tempfile.TemporaryDirectory() as temp:
            diagnostics = Path(temp)
            exact = subprocess.run(
                _expand(commands["exact-passage"]["argv"], diagnostics, "2.4.6"),
                cwd=APPLICATION,
                env=_clean_environment(
                    commands["exact-passage"].get("clean_environment_prefixes", [])
                ),
                capture_output=True,
                text=True,
                encoding="utf-8",
                shell=False,
                check=False,
            )
            self.assertEqual(exact.returncode, 0, exact.stderr)
            exact_report = json.loads(exact.stdout)
            self.assertIn("神愛世人", exact_report["verses"][0]["text"])

            status = subprocess.run(
                _expand(commands["runtime-status"]["argv"], diagnostics, "2.4.6"),
                cwd=APPLICATION,
                env=_clean_environment(
                    commands["runtime-status"].get("clean_environment_prefixes", [])
                ),
                capture_output=True,
                text=True,
                encoding="utf-8",
                shell=False,
                check=False,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            status_report = json.loads(status.stdout)
            self.assertEqual(status_report["core_status"], "core_ready")
            self.assertEqual(status_report["corpus_origin"], "bundled")
            self.assertEqual(status_report["total_rows"], 31008)
            self.assertEqual(status_report["approved_source_gaps"], 71)

            audit = subprocess.run(
                _expand(commands["distribution-audit"]["argv"], diagnostics, "2.4.6"),
                cwd=APPLICATION,
                env=_clean_environment([]),
                capture_output=True,
                text=True,
                encoding="utf-8",
                shell=False,
                check=False,
            )
            self.assertEqual(audit.returncode, 0, audit.stdout + audit.stderr)

    def test_declared_codex_builder_accepts_distribution_contract_version(self) -> None:
        profile = _profile()
        contract = json.loads(
            (APPLICATION / "openclaw" / "distribution.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temp:
            diagnostics = Path(temp)
            command = _expand(
                profile["codex_build"]["argv"], diagnostics, contract["version"]
            )
            completed = subprocess.run(
                command,
                cwd=APPLICATION,
                capture_output=True,
                text=True,
                encoding="utf-8",
                shell=False,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            manifest = json.loads(
                (
                    diagnostics
                    / "codex-marketplace"
                    / "plugins"
                    / "cool-bible-tutor"
                    / ".codex-plugin"
                    / "plugin.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["version"], contract["version"])


if __name__ == "__main__":
    unittest.main()
