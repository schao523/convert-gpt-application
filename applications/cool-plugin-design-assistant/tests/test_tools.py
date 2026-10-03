import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


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


def test_temp_directory():
    temp_root = ROOT.parents[1] / ".tmp" / "cool-plugin-design-assistant-tests"
    temp_root.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=temp_root)


def write_approved_handoff_package(
    path: Path,
    *,
    extra_members: dict[str, bytes] | None = None,
    operation: str = "create",
) -> dict[str, bytes]:
    artifacts = {
        "Plugin_Builder_Application_Spec_v1.0_APPROVED.md": b"# Approved specification\nRequirement SPEC-01 is exact.\n",
        "Design_Statement_v1_APPROVED.md": b"# Approved design statement\nRequirement DS-01 is exact.\n",
        "Behavioral_Workflows_and_Modules_v1.1_APPROVED.md": b"# Approved workflows\nRequirement BW-01 is exact.\n",
        "Reference_Material_Usage_Map_v1.0.md": b"# Reference material map\nRequirement RM-01 is exact.\n",
        "Invariants_Capabilities_and_Gates_v1.0.md": b"# Invariants and gates\nRequirement INV-01 is exact.\n",
        "Acceptance_and_Test_Scenarios_v1.0.md": b"# Acceptance scenarios\nRequirement TEST-01 is exact.\n",
        "Decisions_and_Exclusions_v1.0.md": b"# Decisions and exclusions\nRequirement DEC-01 is exact.\n",
        "README.md": b"# Approved Plugin Builder handoff\n",
    }
    artifact_rows = [
        ("SPEC-v1.0", "Plugin_Builder_Application_Spec_v1.0_APPROVED.md", "v1.0", "approved"),
        ("DS-v1", "Design_Statement_v1_APPROVED.md", "v1", "approved-derived"),
        ("BW-v1.1", "Behavioral_Workflows_and_Modules_v1.1_APPROVED.md", "v1.1", "approved"),
        ("RM-v1.0", "Reference_Material_Usage_Map_v1.0.md", "v1.0", "approved-derived"),
        ("INV-v1.0", "Invariants_Capabilities_and_Gates_v1.0.md", "v1.0", "approved-derived"),
        ("TEST-v1.0", "Acceptance_and_Test_Scenarios_v1.0.md", "v1.0", "approved-derived"),
        ("DEC-v1.0", "Decisions_and_Exclusions_v1.0.md", "v1.0", "approved-derived"),
    ]
    manifest = {
        "application": "Plugin Builder",
        "spec_version": "v1.0",
        "gate": "APPROVED WITH NONBLOCKING DECISIONS",
        "approval_evidence": "The decision owner approved the package.",
        "artifacts": [
            {
                "id": artifact_id,
                "file": filename,
                "version": version,
                "state": state,
                "provenance": "approved handoff",
                "requirements": [f"{artifact_id.split('-', 1)[0]}-01"],
            }
            for index, (artifact_id, filename, version, state) in enumerate(
                artifact_rows, start=1
            )
        ],
        "unresolved_owner_decisions": [
            {
                "decision_id": "UD-01",
                "summary": "Choose the initial model allowlist.",
                "owner": "decision owner",
                "impact": "Workbench must retain the decision without guessing.",
                "blocking": False,
            }
        ],
        "exclusions": [
            "OpenClaw and Claude targets",
            "automatic deployment",
            "public marketplace publication",
        ],
        "reserved_workbench_decisions": ["Skill architecture"],
        "readiness_note": "Ready for deterministic normalization.",
        "requirements": [
            {
                "id": f"{artifact_id.split('-', 1)[0]}-01",
                "source": filename,
                "verbatim": f"Requirement {artifact_id.split('-', 1)[0]}-01 is exact.",
                **({"change": "modify"} if operation == "update" else {}),
            }
            for artifact_id, filename, _version, _state in artifact_rows
        ],
    }
    if operation == "update":
        manifest["baseline"] = {
            "plugin_id": "plugin-builder",
            "version": "0.1.2",
            "archive_sha256": "a" * 64,
        }
        manifest["baseline_preservation"] = {
            "preserve_unaffected_members": True,
            "removal_requires_requirement": True,
            "identity_must_match": True,
        }
    authority_name = "handoff_manifest.json" if operation == "create" else "delta_handoff_manifest.json"
    members = {
        **artifacts,
        authority_name: json.dumps(
            manifest, ensure_ascii=False, sort_keys=True
        ).encode("utf-8"),
        **(extra_members or {}),
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return artifacts


class ToolTests(unittest.TestCase):
    def test_normalizes_approved_package_into_valid_workbench_handoff(self) -> None:
        with test_temp_directory() as temp:
            root = Path(temp)
            source = root / "approved.zip"
            output = root / "approved-normalized.zip"
            artifacts = write_approved_handoff_package(source)
            source_bytes = source.read_bytes()

            result = tool.normalize_handoff_package(
                source,
                output,
                confirmed_by="decision owner",
                runtime_scope="OPENAI_ONLY_PHASE_ONE",
            )

            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertEqual(result["gate_state"], "APPROVED WITH NONBLOCKING DECISIONS")
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertEqual(names, sorted(names))
                self.assertNotIn("handoff_manifest.json", names)
                self.assertIn("package-manifest.json", names)
                self.assertIn("workbench-handoff.json", names)
                for name, content in artifacts.items():
                    self.assertEqual(archive.read(name), content)
                handoff = json.loads(archive.read("workbench-handoff.json"))
                package_manifest = json.loads(archive.read("package-manifest.json"))

            self.assertEqual(tool.validate_handoff(handoff), [])
            self.assertEqual(handoff["approved_specification"]["version"], "v1.0")
            self.assertEqual(handoff["schema"], "workbench-handoff-v1.1")
            self.assertEqual(handoff["operation"], "create")
            self.assertEqual(handoff["requirements"][0]["id"], "SPEC-01")
            self.assertEqual(
                handoff["tool_data_runtime_and_service_requirements"]["runtime_scope"],
                "OPENAI_ONLY_PHASE_ONE",
            )
            self.assertEqual(
                package_manifest["source_archive_sha256"],
                hashlib.sha256(source_bytes).hexdigest(),
            )
            self.assertEqual(package_manifest["canonical_handoff"]["file"], "workbench-handoff.json")
            self.assertEqual(package_manifest["handoff_contract"], "WORKBENCH_HANDOFF_V1_1")
            supporting = {item["file"]: item for item in package_manifest["supporting_files"]}
            self.assertEqual(supporting["README.md"]["sha256"], hashlib.sha256(artifacts["README.md"]).hexdigest())

    def test_normalizes_delta_package_to_v11_update_with_baseline_contract(self) -> None:
        with test_temp_directory() as temp:
            root = Path(temp)
            source = root / "delta.zip"
            output = root / "delta-normalized.zip"
            write_approved_handoff_package(source, operation="update")

            result = tool.normalize_handoff_package(source, output, confirmed_by="decision owner")

            self.assertEqual(result["profile"], "COOL_DESIGN_ASSISTANT_DELTA_V1")
            with zipfile.ZipFile(output) as archive:
                handoff = json.loads(archive.read("workbench-handoff.json"))
            self.assertEqual(handoff["operation"], "update")
            self.assertEqual(handoff["requirements"][0]["change"], "modify")
            self.assertEqual(handoff["baseline"]["plugin_id"], "plugin-builder")
            self.assertTrue(handoff["baseline_preservation"]["preserve_unaffected_members"])

    def test_rejects_legacy_package_without_exact_requirement_authority(self) -> None:
        with test_temp_directory() as temp:
            root = Path(temp)
            source = root / "approved.zip"
            output = root / "normalized.zip"
            write_approved_handoff_package(source)
            with zipfile.ZipFile(source) as archive:
                members = {name: archive.read(name) for name in archive.namelist()}
                manifest = json.loads(archive.read("handoff_manifest.json"))
            manifest.pop("requirements")
            members["handoff_manifest.json"] = json.dumps(manifest).encode("utf-8")
            with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for name, content in sorted(members.items()):
                    archive.writestr(name, content)
            result = tool.normalize_handoff_package(source, output, confirmed_by="decision owner")
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("requirements.explicit_records_required", result["diagnostics"])
            self.assertFalse(output.exists())

    def test_handoff_normalization_is_byte_deterministic(self) -> None:
        with test_temp_directory() as temp:
            root = Path(temp)
            source = root / "approved.zip"
            first = root / "normalized-one.zip"
            second = root / "normalized-two.zip"
            write_approved_handoff_package(source)

            tool.normalize_handoff_package(source, first, confirmed_by="decision owner")
            tool.normalize_handoff_package(source, second, confirmed_by="decision owner")

            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_handoff_normalization_rejects_unlisted_members_without_output(self) -> None:
        with test_temp_directory() as temp:
            root = Path(temp)
            source = root / "approved.zip"
            output = root / "normalized.zip"
            write_approved_handoff_package(
                source,
                extra_members={"unapproved.txt": b"not in the approved manifest"},
            )

            result = tool.normalize_handoff_package(source, output, confirmed_by="decision owner")
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("package.undeclared_member:unapproved.txt", result["diagnostics"])
            self.assertFalse(output.exists())

    def test_normalize_handoff_cli_reports_repository_gate(self) -> None:
        with test_temp_directory() as temp:
            root = Path(temp)
            source = root / "approved.zip"
            output = root / "normalized.zip"
            write_approved_handoff_package(source)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPT),
                    "normalize-handoff-package",
                    str(source),
                    str(output),
                    "--confirmed-by",
                    "decision owner",
                    "--runtime-scope",
                    "OPENAI_ONLY_PHASE_ONE",
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            document = json.loads(completed.stdout)
            self.assertEqual(document["status"], "PASS")
            self.assertEqual(
                document["gate_state"], "APPROVED WITH NONBLOCKING DECISIONS"
            )
            self.assertTrue(output.is_file())

    def test_handoff_reference_requires_canonical_records_and_one_envelope(self) -> None:
        reference = (
            ROOT
            / "skills/creating-application-plugin-design-specifications/references/workbench-handoff-contract.md"
        ).read_text(encoding="utf-8")
        self.assertIn("WORKBENCH_HANDOFF_V1_1", reference)
        self.assertIn("exact `id`, `source`, and `verbatim`", reference)
        self.assertIn("one semantic authority", reference)

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
        self.assertEqual(status["version"], "1.0.1")
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
