from __future__ import annotations

import sys
from pathlib import Path
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
TESTS = Path(__file__).resolve().parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from test_create_candidate import PLAN_FIXTURE
from plugin_builder_core.runtime_commands import resolve_direct_argv
from plugin_builder_core.tool_verification import execute_direct, verify_application_tool


class ToolExecutionPortabilityTests(unittest.TestCase):
    def test_unavailable_literal_python3_is_not_silently_substituted(self) -> None:
        resolution = resolve_direct_argv(
            ["python3", "tools/run.py"], Path("."), executable_lookup=lambda _name: None
        )
        self.assertEqual(resolution.declared_argv, ("python3", "tools/run.py"))
        self.assertIsNone(resolution.observed_argv)
        self.assertIsNone(resolution.adapter)
        self.assertEqual(resolution.diagnostic, "executable_unavailable")

    def test_python_adapter_resolves_only_explicit_token(self) -> None:
        resolution = resolve_direct_argv(["{python}", "tools/run.py"], Path("."))
        self.assertEqual(resolution.observed_argv, (sys.executable, "tools/run.py"))
        self.assertEqual(resolution.adapter, "CURRENT_PYTHON")
        self.assertIsNone(resolution.diagnostic)

    def test_execute_direct_does_not_run_unavailable_literal(self) -> None:
        with tempfile.TemporaryDirectory() as name, mock.patch(
            "plugin_builder_core.tool_verification.subprocess.run"
        ) as run:
            result = execute_direct(["definitely-missing-executable", "--version"], Path(name), 5)
        run.assert_not_called()
        self.assertEqual(result["state"], "NOT VERIFIED")
        self.assertEqual(result["declared_argv"], ["definitely-missing-executable", "--version"])
        self.assertIsNone(result["observed_argv"])

    def test_tool_evidence_retains_declared_and_observed_argv(self) -> None:
        import json

        tool = json.loads(PLAN_FIXTURE.read_text(encoding="utf-8"))["tools"][0]
        with tempfile.TemporaryDirectory() as name:
            candidate = Path(name)
            target = candidate / "tools/normalize.py"
            target.parent.mkdir(parents=True)
            target.write_text(
                "import json,sys; value=json.load(sys.stdin); print(json.dumps({'normalized': value['text'].strip()}, sort_keys=True))",
                encoding="utf-8",
            )
            result = verify_application_tool(tool, candidate)
        self.assertEqual(result["argv"], ["{python}", "tools/normalize.py", "--self-test"])
        self.assertEqual(result["declared_argv"], result["argv"])
        self.assertEqual(result["observed_argv"][0], sys.executable)
        self.assertEqual(result["adapter"], "CURRENT_PYTHON")


if __name__ == "__main__":
    unittest.main()
