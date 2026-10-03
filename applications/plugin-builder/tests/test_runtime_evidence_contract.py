from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tests/runtime"


class RuntimeEvidenceContractTests(unittest.TestCase):
    def test_runtime_contract_covers_t1_t7_tools_gates_and_clean_environment(self) -> None:
        text = (RUNTIME / "T1-T7-runtime-scenarios.md").read_text(encoding="utf-8")
        for scenario in range(1, 8):
            self.assertRegex(text, rf"(?m)^## T{scenario}\b")
        for required in (
            "W1", "W2", "BUNDLED_LOCAL", "RUNTIME_NATIVE", "MCP_ADAPTER",
            "PYTHONPATH", "credentials", "network", "repository", "pre-existing",
            "create", "update", "plugin_builder.py", "package-runtime-evidence",
        ):
            self.assertIn(required.casefold(), text.casefold())

    def test_runtime_result_schema_has_identity_scenarios_tools_and_honest_states(self) -> None:
        schema = json.loads((RUNTIME / "runtime-result-schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        required = set(schema["required"])
        self.assertGreaterEqual(required, {"schema", "runtime", "artifact", "scenarios", "tools", "overall_state"})
        states = set(schema["$defs"]["evidence_state"]["enum"])
        self.assertEqual(states, {"EXPECTED", "STATICALLY VERIFIED", "RUNTIME VERIFIED", "NOT VERIFIED", "NOT APPLICABLE"})
        self.assertEqual(schema["properties"]["scenarios"]["minItems"], 7)

    def test_runtime_scenario_preparer_emits_exact_t3_t4_t5_t6_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline = root / "t2.zip"
            with zipfile.ZipFile(baseline, "w") as archive:
                archive.writestr("sample-plugin/plugin.json", "{}")
            completed = subprocess.run(
                [sys.executable, "-B", str(RUNTIME / "prepare-runtime-scenarios.py"),
                 "--base-plan", str(ROOT / "tests/fixtures/plan-create.json"),
                 "--baseline", str(baseline), "--output", str(root / "out")],
                capture_output=True, text=True, encoding="utf-8", check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["status"], "PASS")
            expected = {
                "t3-unresolved-plan.json", "t4-update-baseline.zip", "t4-update-plan.json",
                "t5-failing-tool-plan.json", "t6-runtime-native-plan.json",
            }
            self.assertEqual({item.name for item in (root / "out").iterdir()}, expected)
            self.assertEqual(json.loads((root / "out/t4-update-plan.json").read_text())["operation"], "update")
            with zipfile.ZipFile(root / "out/t4-update-baseline.zip") as archive:
                self.assertEqual(archive.read("sample-plugin/owner-notes.txt"), b"owner bytes\x00preserved")

    def test_pending_installed_runtime_evidence_is_not_upgraded(self) -> None:
        compatibility = (ROOT / "docs/runtime-compatibility.md").read_text(encoding="utf-8")
        coverage = (ROOT / "tests/coverage-matrix.md").read_text(encoding="utf-8")
        self.assertIn("| Codex installed Plugin Builder execution | NOT VERIFIED |", compatibility)
        self.assertIn("| ChatGPT Work Local/Desktop Plugin Builder execution | NOT VERIFIED |", compatibility)
        self.assertIn("| RUNTIME-CODEX-APPLICATION | Codex installed Plugin Builder |", coverage)
        self.assertIn("| RUNTIME-WORK-APPLICATION | ChatGPT Work Local/Desktop Plugin Builder |", coverage)
        self.assertNotIn("READY", compatibility)


if __name__ == "__main__":
    unittest.main()
