from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "vibe_designer.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("vibe_designer", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ToolTests(unittest.TestCase):
    def test_status_reports_skill_only_ready_runtime(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "status", "--json"],
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["plugin_id"], "vibe-coding-designer")
        self.assertEqual(payload["version"], "1.0.0")
        self.assertEqual(payload["skill_count"], 7)
        self.assertEqual(payload["rag"], "NOT APPLICABLE")
        self.assertEqual(payload["status"], "PASS")

    def test_workflow_validator_checks_references_and_terminal_reachability(self) -> None:
        tool = load_tool()
        valid = json.loads((ROOT / "tests/fixtures/workflow-valid.json").read_text())
        self.assertEqual(tool.validate_workflow(valid), [])
        broken = json.loads(json.dumps(valid))
        broken["states"][1]["on"]["failure"] = "missing_state"
        broken["states"][1]["action"]["binding_ref"] = "missing.binding"
        errors = tool.validate_workflow(broken)
        self.assertIn("unknown state transition: validate -> missing_state", errors)
        self.assertIn("unknown binding_ref: missing.binding", errors)

    def test_workflow_validator_rejects_noncanonical_declaration_shapes(self) -> None:
        tool = load_tool()
        valid = json.loads((ROOT / "tests/fixtures/workflow-valid.json").read_text())
        broken = json.loads(json.dumps(valid))
        broken["roles"] = ["operator"]
        broken["events"] = ["report.requested"]
        broken["guards"] = ["valid_request"]
        broken["schemas"] = ["ReportRequest"]
        broken["policies"] = ["privacy"]
        errors = tool.validate_workflow(broken)
        self.assertIn("roles must be an array of objects with unique non-empty ids", errors)
        self.assertIn("events must be an array of objects with unique non-empty ids", errors)
        self.assertIn("guards must be an array of objects with unique non-empty ids", errors)
        self.assertIn("schemas must be an object", errors)
        self.assertIn("policies must be an object", errors)

    def test_non_gui_design_spec_is_valid_without_web_sections(self) -> None:
        tool = load_tool()
        errors = tool.validate_design_spec(ROOT / "tests/fixtures/cli-design-spec.md")
        self.assertEqual(errors, [])

    def test_coverage_is_computed_only_from_explicit_requirement_mapping(self) -> None:
        tool = load_tool()
        report = tool.coverage_report(
            {
                "requirements": ["FR-001", "FR-002", "FR-003"],
                "tests": [
                    {"id": "T-001", "requirements": ["FR-001"]},
                    {"id": "T-002", "requirements": ["FR-002"]},
                ],
            }
        )
        self.assertEqual(report["covered"], 2)
        self.assertEqual(report["total"], 3)
        self.assertEqual(report["percent"], 66.67)
        self.assertEqual(report["uncovered"], ["FR-003"])
        with self.assertRaisesRegex(ValueError, "requirements must be explicit"):
            tool.coverage_report({"tests": []})


if __name__ == "__main__":
    unittest.main()
