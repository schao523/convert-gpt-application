from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.cli import main
from obvious_one_plugin_framework.readiness_report import combine_results
from obvious_one_plugin_framework.results import OperationResult, result_json


class ReadinessReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write(self, name: str, status: str) -> Path:
        path = self.root / name
        path.write_text(
            result_json(OperationResult(name, status, f"{status.lower()}_gate")),
            encoding="utf-8",
            newline="\n",
        )
        return path

    def test_combine_results_uses_fail_then_blocked_then_pass_precedence(self) -> None:
        passed = self.write("pass.json", "PASS")
        blocked = self.write("blocked.json", "BLOCKED")
        failed = self.write("failed.json", "FAIL")

        self.assertEqual(combine_results((passed,)).status, "PASS")
        self.assertEqual(combine_results((passed, blocked)).status, "BLOCKED")
        self.assertEqual(combine_results((blocked, failed)).status, "FAIL")

    def test_report_cli_writes_canonical_deterministic_result_transactionally(self) -> None:
        passed = self.write("pass.json", "PASS")
        blocked = self.write("blocked.json", "BLOCKED")
        output = self.root / "report.json"
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            code = main([
                "report", "--inputs", str(passed), str(blocked),
                "--output", str(output), "--json",
            ])

        payload = json.loads(stdout.getvalue())
        self.assertEqual((code, payload["status"]), (2, "BLOCKED"))
        self.assertEqual(output.read_text(encoding="utf-8"), stdout.getvalue())
        self.assertNotIn("timestamp", output.read_text(encoding="utf-8").lower())
        self.assertNotIn(str(self.root), output.read_text(encoding="utf-8"))

    def test_report_failure_takes_precedence(self) -> None:
        blocked = self.write("blocked.json", "BLOCKED")
        failed = self.write("failed.json", "FAIL")

        result = combine_results((blocked, failed))

        self.assertEqual(result.status, "FAIL")


if __name__ == "__main__":
    unittest.main()
