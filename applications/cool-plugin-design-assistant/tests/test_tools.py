import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "cool_plugin_design_assistant.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("cool_plugin_design_assistant", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_fixture(name: str):
    return json.loads((ROOT / "tests" / "fixtures" / name).read_text(encoding="utf-8"))


tool = load_tool()


class ToolTests(unittest.TestCase):
    def test_workflow_validator_requires_reachable_terminal_and_failure_paths(self) -> None:
        valid = load_fixture("workflow-valid.json")
        self.assertEqual(tool.validate_workflow(valid), [])
        broken = copy.deepcopy(valid)
        broken["states"][1]["transitions"]["failure"] = "missing"
        self.assertIn(
            "unknown state transition: analyze -> missing",
            tool.validate_workflow(broken),
        )

    def test_module_validator_rejects_implementation_architecture_at_any_depth(
        self,
    ) -> None:
        valid = load_fixture("modules-valid.json")
        self.assertEqual(tool.validate_modules(valid), [])
        broken = copy.deepcopy(valid)
        broken["modules"][0]["implementation"] = {
            "nested": {"skill_assignment": "one-skill"}
        }
        self.assertIn("implementation architecture forbidden", tool.validate_modules(broken))

    def test_workflow_validator_rejects_duplicate_missing_and_unreachable_states(
        self,
    ) -> None:
        valid = load_fixture("workflow-valid.json")

        duplicate = copy.deepcopy(valid)
        duplicate["states"].append(copy.deepcopy(duplicate["states"][0]))
        self.assertIn("duplicate state id: intake", tool.validate_workflow(duplicate))

        no_terminal = copy.deepcopy(valid)
        no_terminal["states"] = [
            state for state in no_terminal["states"] if state["kind"] != "end"
        ]
        self.assertIn("terminal state required", tool.validate_workflow(no_terminal))

        unreachable = copy.deepcopy(valid)
        unreachable["states"].append(
            {
                "id": "orphan",
                "kind": "action",
                "interaction_protocol": "orphan-protocol",
                "wait": False,
                "transitions": {"success": "complete", "failure": "recover"},
            }
        )
        self.assertIn("unreachable state: orphan", tool.validate_workflow(unreachable))

    def test_workflow_validator_requires_wait_and_object_payload(self) -> None:
        self.assertEqual(tool.validate_workflow([]), ["workflow must be an object"])
        valid = load_fixture("workflow-valid.json")
        broken = copy.deepcopy(valid)
        for state in broken["states"]:
            state["wait"] = False
        self.assertIn("approval wait state required", tool.validate_workflow(broken))

        no_failure = copy.deepcopy(valid)
        for state in no_failure["states"]:
            state["transitions"].pop("failure", None)
        self.assertIn("failure path required", tool.validate_workflow(no_failure))

    def test_module_validator_rejects_unknown_transition_missing_protocol_and_non_object(
        self,
    ) -> None:
        self.assertEqual(tool.validate_modules([]), ["modules must be an object"])
        valid = load_fixture("modules-valid.json")

        unknown = copy.deepcopy(valid)
        unknown["modules"][0]["transitions"]["success"] = "missing"
        self.assertIn(
            "unknown module transition: intake -> missing",
            tool.validate_modules(unknown),
        )

        missing_protocol = copy.deepcopy(valid)
        del missing_protocol["modules"][0]["user_interaction_protocol"]
        self.assertIn(
            "module intake missing field: user_interaction_protocol",
            tool.validate_modules(missing_protocol),
        )

        duplicate = copy.deepcopy(valid)
        duplicate["modules"].append(copy.deepcopy(duplicate["modules"][0]))
        self.assertIn("duplicate module id: intake", tool.validate_modules(duplicate))

    def test_errors_are_sorted_deterministically(self) -> None:
        broken = {"states": []}
        errors = tool.validate_workflow(broken)
        self.assertEqual(errors, sorted(errors))

    def test_design_validator_requires_distinct_complete_artifacts(self) -> None:
        statement = ROOT / "tests" / "fixtures" / "design-statement-valid.md"
        specification = ROOT / "tests" / "fixtures" / "design-spec-valid.md"
        self.assertEqual(tool.validate_design_artifacts(statement, specification), [])
        self.assertIn(
            "design statement and specification must be distinct files",
            tool.validate_design_artifacts(statement, statement),
        )

    def test_handoff_validator_requires_approval_and_reports_unresolved_decisions(
        self,
    ) -> None:
        valid = load_fixture("handoff-valid.json")
        self.assertEqual(tool.validate_handoff(valid), [])
        broken = copy.deepcopy(valid)
        broken["approval"]["state"] = "draft"
        broken["unresolved_owner_decisions"] = ["redistribution"]
        errors = tool.validate_handoff(broken)
        self.assertIn("handoff requires explicit approval", errors)
        self.assertIn("unresolved owner decisions: redistribution", errors)

    def test_handoff_validator_rejects_architecture_fields_recursively(self) -> None:
        broken = load_fixture("handoff-valid.json")
        broken["approved_specification"]["implementation"] = {
            "runtime_adapter": "codex-only"
        }
        self.assertIn(
            "implementation architecture forbidden",
            tool.validate_handoff(broken),
        )

    def test_coverage_reports_not_verified_without_explicit_mapping(self) -> None:
        self.assertEqual(
            tool.coverage_report({"requirements": ["INV-001"]})["status"],
            "NOT VERIFIED",
        )
        report = tool.coverage_report(load_fixture("coverage-valid.json"))
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["percentage"], 100.0)

    def test_status_and_cli_use_stable_ascii_result_shape(self) -> None:
        status = tool.status()
        self.assertEqual(status["status"], "PASS")
        self.assertEqual(len(status["skills"]), 7)
        self.assertEqual(status["rag"], "NOT APPLICABLE")
        self.assertEqual(status["clawhub"], "NOT APPLICABLE")
        self.assertEqual(set(status["runtime_evidence"].values()), {"NOT VERIFIED"})

        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "status", "--json"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        document = json.loads(completed.stdout)
        self.assertEqual(document["operation"], "status")
        self.assertEqual(document["errors"], [])
        completed.stdout.encode("ascii")


if __name__ == "__main__":
    unittest.main()
