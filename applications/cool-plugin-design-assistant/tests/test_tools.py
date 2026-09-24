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

        fake_failure = copy.deepcopy(valid)
        for state in fake_failure["states"]:
            if "failure" in state["transitions"]:
                state["transitions"]["failure"] = "complete"
        self.assertIn("failure path required", tool.validate_workflow(fake_failure))

    def test_workflow_validator_rejects_empty_wrong_type_and_inconsistent_fields(self) -> None:
        valid = load_fixture("workflow-valid.json")

        for field in ("workflow_id", "mission_outcome", "start"):
            broken = copy.deepcopy(valid)
            broken[field] = None
            self.assertIn(
                f"workflow field must be a non-empty string: {field}",
                tool.validate_workflow(broken),
            )

        for field in ("actors", "terminal_states", "hitl_checkpoints", "completion_criteria"):
            broken = copy.deepcopy(valid)
            broken[field] = []
            self.assertIn(
                f"workflow field must be a non-empty string array: {field}",
                tool.validate_workflow(broken),
            )

        broken = copy.deepcopy(valid)
        broken["inputs"] = {"required": [], "optional": [None]}
        errors = tool.validate_workflow(broken)
        self.assertIn("workflow inputs required must be a non-empty string array", errors)
        self.assertIn("workflow inputs optional must be a string array", errors)

        broken = copy.deepcopy(valid)
        broken["terminal_states"] = ["complete"]
        self.assertIn(
            "workflow terminal_states must match end states",
            tool.validate_workflow(broken),
        )

        broken = copy.deepcopy(valid)
        broken["hitl_checkpoints"] = ["analyze"]
        self.assertIn(
            "workflow HITL checkpoint must reference a wait state: analyze",
            tool.validate_workflow(broken),
        )

        for field, value in (
            ("id", ""),
            ("kind", []),
            ("interaction_protocol", None),
            ("wait", "yes"),
            ("transitions", []),
        ):
            broken = copy.deepcopy(valid)
            broken["states"][0][field] = value
            self.assertTrue(tool.validate_workflow(broken), field)

    def test_workflow_validator_rejects_success_paths_that_bypass_required_hitl(self) -> None:
        valid = load_fixture("workflow-valid.json")
        valid["successful_terminal_states"] = ["complete"]
        self.assertEqual(tool.validate_workflow(valid), [])

        bypass = copy.deepcopy(valid)
        bypass["states"][1]["transitions"]["bypass"] = "complete"
        self.assertIn(
            "workflow required HITL checkpoint can be bypassed: approval",
            tool.validate_workflow(bypass),
        )

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

    def test_module_validator_rejects_empty_and_wrong_type_contract_fields(self) -> None:
        valid = load_fixture("modules-valid.json")
        string_fields = (
            "module_id",
            "name",
            "purpose",
            "mission_outcome",
            "trigger",
            "user_interaction_protocol",
        )
        for field in string_fields:
            broken = copy.deepcopy(valid)
            broken["modules"][0][field] = None
            label = "index-0" if field == "module_id" else "intake"
            self.assertIn(
                f"module {label} field must be a non-empty string: {field}",
                tool.validate_modules(broken),
            )

        for field in (
            "preconditions",
            "procedure",
            "outputs",
            "safety_boundaries",
            "acceptance_criteria",
        ):
            broken = copy.deepcopy(valid)
            broken["modules"][0][field] = []
            self.assertIn(
                f"module intake field must be a non-empty string array: {field}",
                tool.validate_modules(broken),
            )

        broken = copy.deepcopy(valid)
        broken["modules"][0]["classification"] = {}
        self.assertIn(
            "module intake has invalid classification",
            tool.validate_modules(broken),
        )

        broken = copy.deepcopy(valid)
        broken["modules"][0]["inputs"] = None
        broken["modules"][0]["transitions"] = {}
        broken["modules"][0]["stop_wait_completion"] = {"stop": "", "wait": "", "completion": ""}
        broken["modules"][0]["error_recovery"] = {"error": "", "recovery": ""}
        errors = tool.validate_modules(broken)
        self.assertIn("module intake inputs must be an object", errors)
        self.assertIn("module intake transitions must be a non-empty object", errors)
        self.assertIn("module intake stop_wait_completion requires non-empty stop, wait, and completion", errors)
        self.assertIn("module intake error_recovery requires non-empty error and recovery", errors)

        broken = copy.deepcopy(valid)
        broken["modules"][0]["reference_material_requirements"] = [None]
        self.assertIn(
            "module intake field must be a string array: reference_material_requirements",
            tool.validate_modules(broken),
        )

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

    def test_design_validator_requires_canonical_sections_and_nonempty_statement_fields(self) -> None:
        statement = ROOT / "tests" / "fixtures" / "design-statement-valid.md"
        specification = ROOT / "tests" / "fixtures" / "design-spec-valid.md"
        original_statement = statement.read_text(encoding="utf-8")
        original_specification = specification.read_text(encoding="utf-8")

        import tempfile

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            empty_statement = root / "statement.md"
            empty_statement.write_text(
                original_statement.replace(
                    "## Audience\n\nVolunteer event coordinators.",
                    "## Audience\n\n",
                ),
                encoding="utf-8",
            )
            self.assertIn(
                "design statement field must be non-empty: audience",
                tool.validate_design_artifacts(empty_statement, specification),
            )

            renamed_specification = root / "specification.md"
            renamed_specification.write_text(
                original_specification.replace(
                    "1. **Application identity and purpose**",
                    "1. **Different title**",
                ),
                encoding="utf-8",
            )
            self.assertIn(
                "design specification section 1 must be: Application identity and purpose",
                tool.validate_design_artifacts(statement, renamed_specification),
            )

    def test_handoff_validator_requires_approval_and_reports_unresolved_decisions(
        self,
    ) -> None:
        valid = load_fixture("handoff-valid.json")
        self.assertEqual(tool.validate_handoff(valid), [])
        broken = copy.deepcopy(valid)
        broken["approval"]["state"] = "draft"
        broken["unresolved_owner_decisions"] = [
            {
                "decision_id": "redistribution",
                "summary": "Confirm redistribution rights",
                "owner": "product owner",
                "blocking": True,
            }
        ]
        errors = tool.validate_handoff(broken)
        self.assertIn("handoff requires explicit approval", errors)
        self.assertIn("blocking owner decision: redistribution", errors)

    def test_handoff_validator_preserves_nonblocking_decisions_and_gate_state(self) -> None:
        valid = load_fixture("handoff-valid.json")
        self.assertEqual(tool.handoff_gate_state(valid), "READY FOR WORKBENCH")

        nonblocking = copy.deepcopy(valid)
        nonblocking["unresolved_owner_decisions"] = [
            {
                "decision_id": "release-timing",
                "summary": "Choose the later publication date",
                "owner": "product owner",
                "blocking": False,
            }
        ]
        self.assertEqual(tool.validate_handoff(nonblocking), [])
        self.assertEqual(
            tool.handoff_gate_state(nonblocking),
            "APPROVED WITH NONBLOCKING DECISIONS",
        )

        malformed = copy.deepcopy(valid)
        malformed["unresolved_owner_decisions"] = ["release-timing"]
        self.assertIn(
            "unresolved owner decision must be an object",
            tool.validate_handoff(malformed),
        )
        self.assertEqual(tool.handoff_gate_state(malformed), "HANDOFF BLOCKED")

    def test_handoff_validator_rejects_approval_for_an_older_specification_version(
        self,
    ) -> None:
        stale = load_fixture("handoff-valid.json")
        stale["approved_specification"]["version"] = "v2"
        self.assertIn(
            "handoff approval specification_version must match approved specification version",
            tool.validate_handoff(stale),
        )
        self.assertEqual(tool.handoff_gate_state(stale), "HANDOFF BLOCKED")

    def test_cli_returns_structured_errors_for_malformed_json_field_types(self) -> None:
        import tempfile

        cases = []
        workflow = load_fixture("workflow-valid.json")
        workflow["states"][0]["kind"] = []
        cases.append(("validate-workflow", workflow))
        modules = load_fixture("modules-valid.json")
        modules["modules"][0]["classification"] = {}
        cases.append(("validate-modules", modules))

        with tempfile.TemporaryDirectory() as temp:
            for command, payload in cases:
                path = Path(temp) / f"{command}.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                completed = subprocess.run(
                    [sys.executable, "-B", str(SCRIPT), command, str(path), "--json"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(completed.returncode, 3, completed.stderr)
                document = json.loads(completed.stdout)
                self.assertEqual(document["status"], "FAIL")
                self.assertTrue(document["errors"])

    def test_handoff_validator_rejects_empty_and_wrong_type_package_fields(self) -> None:
        valid = load_fixture("handoff-valid.json")
        for field in (
            "workflow_definitions_and_instruction_modules",
            "application_invariants_and_hitl_checkpoints",
            "acceptance_criteria_and_representative_scenarios",
        ):
            broken = copy.deepcopy(valid)
            broken[field] = []
            self.assertIn(
                f"handoff field must be a non-empty string array: {field}",
                tool.validate_handoff(broken),
            )

        broken = copy.deepcopy(valid)
        broken["approved_design_statement"]["id"] = ""
        broken["approval"]["confirmed_by"] = None
        broken["rights_and_redistribution_decisions"] = {}
        errors = tool.validate_handoff(broken)
        self.assertIn("approved artifact requires non-empty id: approved_design_statement", errors)
        self.assertIn("handoff approval requires non-empty confirmed_by", errors)
        self.assertIn("handoff rights and redistribution decisions must be a non-empty object", errors)

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
        self.assertEqual(status["plugin_id"], "cool-plugin-design-assistant")
        self.assertEqual(status["version"], "1.0.0")
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
