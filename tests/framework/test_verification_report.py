from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from obvious_one_plugin_framework.verification import (
    RESULT_STATES,
    discover_applications,
)
from scripts.verify_extraction import (
    ApplicationResult,
    RunContext,
    VerificationReport,
    run_application,
    write_report,
)


FIXTURES = Path(__file__).parents[1] / "fixtures" / "verification"


def _repository(root: Path, *application_ids: str) -> Path:
    repository = root / "repository"
    applications = repository / "applications"
    applications.mkdir(parents=True)
    for application_id in application_ids:
        shutil.copytree(FIXTURES / application_id, applications / application_id)
    docs = repository / "docs"
    docs.mkdir()
    for application_id in application_ids:
        (docs / f"{application_id}-source.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "application_id": application_id,
                    "plugin_id": application_id,
                    "source_repository": f"{application_id}-source",
                    "source_commit": "1" * 40,
                    "marketplace_repository": "example/plugins",
                    "marketplace_commit": "0" * 40,
                    "incorporated_branches": [],
                    "source_inventory": [],
                }
            ),
            encoding="utf-8",
        )
    (docs / "delta.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "marketplace_commit": "0" * 40,
                "codex": {"missing": [], "unexpected": [], "digest_mismatch": []},
                "openclaw": {"missing": [], "unexpected": [], "digest_mismatch": []},
            }
        ),
        encoding="utf-8",
    )
    return repository


class RecordingRunner:
    def __init__(self, fail_build_package: bool = False) -> None:
        self.calls: list[tuple[list[str], dict[str, object]]] = []
        self.fail_build_package = fail_build_package

    def __call__(self, command, **kwargs):
        argv = list(command)
        self.calls.append((argv, dict(kwargs)))
        if self.fail_build_package and "build-package" in argv:
            return subprocess.CompletedProcess(argv, 3, "", "synthetic failure")
        return subprocess.run(argv, **kwargs)


class VerificationReportTests(unittest.TestCase):
    def test_application_and_report_states_reject_unsupported_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid result state"):
            ApplicationResult("plugin-alpha", "SKIPPED", (), {})
        with self.assertRaisesRegex(ValueError, "invalid result state"):
            VerificationReport(
                "SKIPPED",
                Path("diagnostics"),
                Path("diagnostics/report.json"),
                (),
                (),
            )

    def test_real_synthetic_application_builds_and_verifies_both_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = _repository(Path(temp), "plugin-beta")
            config = discover_applications(repository)[0]
            diagnostics = repository / ".tmp" / "verification" / "run-test"
            runner = RecordingRunner()
            context = RunContext(
                repository_root=repository,
                diagnostics=diagnostics,
                python=sys.executable,
                command_runner=runner,
            )

            result = run_application(config, context)
            report = write_report(context, (), (result,))

            states = {gate.gate_id: gate.state for gate in result.gates}
            self.assertEqual(
                result.state,
                "PASS",
                [(gate.gate_id, gate.state, gate.detail) for gate in result.gates],
            )
            self.assertEqual(states["codex-build"], "PASS")
            self.assertEqual(states["openclaw-build-a"], "PASS")
            self.assertEqual(states["openclaw-build-b"], "PASS")
            self.assertEqual(states["openclaw-verify"], "PASS")
            self.assertEqual(states["openclaw-determinism"], "PASS")
            self.assertEqual(states["marketplace"], "NOT APPLICABLE")
            self.assertIn("codex_content_sha256", result.artifacts)
            self.assertIn("openclaw_content_sha256", result.artifacts)
            self.assertEqual(
                sum("build-package" in command for command, _ in runner.calls), 2
            )
            self.assertEqual(sum("verify" in command for command, _ in runner.calls), 1)
            self.assertTrue(all(call[1]["shell"] is False for call in runner.calls))
            payload = json.loads(report.report_path.read_text(encoding="utf-8"))
            reported_states = {
                gate["state"]
                for application in payload["applications"]
                for gate in application["gates"]
            }
            self.assertLessEqual(reported_states, RESULT_STATES)

    def test_configured_marketplace_without_path_is_not_verified_but_locally_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = _repository(Path(temp), "plugin-alpha")
            config = discover_applications(repository)[0]
            context = RunContext(
                repository_root=repository,
                diagnostics=repository / ".tmp" / "verification" / "run-test",
                python=sys.executable,
            )

            result = run_application(config, context)

            marketplace = next(gate for gate in result.gates if gate.gate_id == "marketplace")
            self.assertEqual(
                result.state,
                "PASS",
                [(gate.gate_id, gate.state, gate.detail) for gate in result.gates],
            )
            self.assertEqual(marketplace.state, "NOT VERIFIED")

    def test_openclaw_build_failure_marks_dependent_gates_not_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = _repository(Path(temp), "plugin-alpha")
            config = discover_applications(repository)[0]
            runner = RecordingRunner(fail_build_package=True)
            context = RunContext(
                repository_root=repository,
                diagnostics=repository / ".tmp" / "verification" / "run-test",
                python=sys.executable,
                command_runner=runner,
            )

            result = run_application(config, context)

            states = {gate.gate_id: gate.state for gate in result.gates}
            self.assertEqual(result.state, "FAIL")
            self.assertEqual(states["openclaw-build-a"], "FAIL")
            self.assertEqual(states["openclaw-build-b"], "FAIL")
            self.assertEqual(states["openclaw-verify"], "NOT VERIFIED")
            self.assertEqual(states["openclaw-determinism"], "NOT VERIFIED")
            self.assertEqual(states["marketplace"], "NOT VERIFIED")

    def test_marketplace_gate_passes_exact_clean_tree_and_rejects_dirty_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repository = _repository(Path(temp), "plugin-alpha")
            config = discover_applications(repository)[0]
            diagnostics = repository / ".tmp" / "verification" / "run-test"
            initial = RunContext(
                repository_root=repository,
                diagnostics=diagnostics,
                python=sys.executable,
            )
            local_result = run_application(config, initial)
            local_artifacts = dict(local_result.artifacts)
            codex = repository / Path(local_artifacts["codex"])
            openclaw = repository / Path(local_artifacts["openclaw"])

            marketplace = Path(temp) / "marketplace"
            shutil.copytree(codex, marketplace / "plugins" / "plugin-alpha")
            shutil.copytree(openclaw, marketplace / "openclaw" / "plugin-alpha")
            subprocess.run(["git", "init", "-b", "main"], cwd=marketplace, check=True, capture_output=True)
            subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=marketplace, check=True)
            subprocess.run(["git", "config", "user.email", "fixture@example.test"], cwd=marketplace, check=True)
            subprocess.run(["git", "config", "user.name", "Fixture"], cwd=marketplace, check=True)
            subprocess.run(["git", "add", "."], cwd=marketplace, check=True)
            subprocess.run(["git", "commit", "-m", "fixture"], cwd=marketplace, check=True, capture_output=True)
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=marketplace, text=True
            ).strip()
            provenance_path = repository / "docs" / "plugin-alpha-source.json"
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            provenance["marketplace_commit"] = commit
            provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
            delta = json.loads((repository / "docs" / "delta.json").read_text(encoding="utf-8"))
            delta["marketplace_commit"] = commit
            (repository / "docs" / "delta.json").write_text(json.dumps(delta), encoding="utf-8")

            clean_context = RunContext(
                repository_root=repository,
                diagnostics=repository / ".tmp" / "verification" / "run-clean",
                python=sys.executable,
                marketplace=marketplace,
            )
            clean = run_application(config, clean_context)
            clean_gate = next(gate for gate in clean.gates if gate.gate_id == "marketplace")
            self.assertEqual(clean_gate.state, "PASS")
            self.assertEqual(clean_gate.data["commit"], commit)

            (marketplace / "dirty.txt").write_text("dirty", encoding="utf-8")
            dirty_context = RunContext(
                repository_root=repository,
                diagnostics=repository / ".tmp" / "verification" / "run-dirty",
                python=sys.executable,
                marketplace=marketplace,
            )
            dirty = run_application(config, dirty_context)
            dirty_gate = next(gate for gate in dirty.gates if gate.gate_id == "marketplace")
            self.assertEqual(dirty_gate.state, "FAIL")
            self.assertIn("not clean", dirty_gate.detail)

            (marketplace / "dirty.txt").unlink()
            readme = marketplace / "plugins" / "plugin-alpha" / "README.md"
            readme.write_text("# Changed publication\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=marketplace, check=True)
            subprocess.run(
                ["git", "commit", "-m", "unapproved change"],
                cwd=marketplace,
                check=True,
                capture_output=True,
            )
            changed_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=marketplace, text=True
            ).strip()
            provenance["marketplace_commit"] = changed_commit
            provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
            delta["marketplace_commit"] = changed_commit
            (repository / "docs" / "delta.json").write_text(json.dumps(delta), encoding="utf-8")
            changed_context = RunContext(
                repository_root=repository,
                diagnostics=repository / ".tmp" / "verification" / "run-changed",
                python=sys.executable,
                marketplace=marketplace,
            )

            changed = run_application(config, changed_context)

            changed_gate = next(
                gate for gate in changed.gates if gate.gate_id == "marketplace"
            )
            self.assertEqual(changed_gate.state, "FAIL")
            self.assertIn("delta is not approved", changed_gate.detail)
            self.assertEqual(
                changed_gate.data["codex"]["digest_mismatch"], ["README.md"]
            )


if __name__ == "__main__":
    unittest.main()
