import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from plugin_builder_core.result import operation_document
from plugin_builder_core.session_contract import session_gate_state, validate_session


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def w1_waiting_create() -> dict:
    return {
        "schema_version": 1,
        "operation": "create",
        "stage": "W1",
        "workspace_path": "sessions/demo",
        "approved_spec_sha256": HASH_A,
        "plan_sha256": HASH_B,
        "baseline": None,
        "w1": None,
        "candidate": None,
        "verification": None,
        "w2": None,
        "package": None,
        "requirements": [
            {
                "id": "RQ1",
                "owner": "guiding-plugin-builder-sessions",
                "evidence": "NOT VERIFIED",
                "required": True,
            }
        ],
    }


def package_ready() -> dict:
    payload = w1_waiting_create()
    payload["requirements"].append(
        {
            "id": "AC6",
            "owner": "verifying-and-packaging-plugins",
            "evidence": "NOT VERIFIED",
            "required": False,
        }
    )
    payload.update(
        {
            "stage": "S5",
            "w1": {"approved": True, "plan_sha256": HASH_B},
            "candidate": {
                "path": "candidate/plugin-builder",
                "sha256": HASH_C,
                "plan_sha256": HASH_B,
            },
            "verification": {
                "sha256": HASH_D,
                "candidate_sha256": HASH_C,
                "results": [
                    {"id": "RQ1", "required": True, "state": "PASS"},
                    {"id": "AC6", "required": False, "state": "NOT VERIFIED"},
                ],
            },
            "w2": {
                "approved": True,
                "candidate_sha256": HASH_C,
                "verification_sha256": HASH_D,
            },
            "package": {
                "path": "dist/plugin-builder.zip",
                "sha256": HASH_A,
                "candidate_sha256": HASH_C,
                "verification_sha256": HASH_D,
            },
        }
    )
    return payload


def inspected_v2() -> dict:
    return {
        "schema_version": 2,
        "operation": "create",
        "stage": "S2",
        "workspace_path": ".",
        "approved_spec_sha256": HASH_A,
        "inspection": {
            "path": "inspection.json",
            "sha256": HASH_B,
            "package_sha256": HASH_C,
            "baseline_sha256": None,
        },
        "pending_decisions": [],
        "requirements": [
            {"id": "RQ1", "required": True, "source_paths": ["input/Design.md"]}
        ],
        "baseline": None,
        "plan": None,
        "w1": None,
        "candidate": None,
        "verification": None,
        "w2": None,
        "package": None,
    }


class SessionContractTests(unittest.TestCase):
    def test_valid_v2_inspected_session(self) -> None:
        payload = inspected_v2()
        self.assertEqual(validate_session(payload), [])
        self.assertEqual(session_gate_state(payload), "PLANNING")

    def test_v2_rejects_unsafe_inspection_and_impossible_stage(self) -> None:
        payload = inspected_v2()
        payload["inspection"]["path"] = "../inspection.json"
        payload["stage"] = "S3"
        errors = validate_session(payload)
        self.assertIn("inspection.path.invalid_relative_posix_path", errors)
        self.assertIn("stage.S3.requires_plan", errors)
        self.assertIn("stage.S3.requires_approved_w1", errors)

    def test_v2_rejects_unknown_keys_and_stale_baseline_binding(self) -> None:
        payload = inspected_v2()
        payload["surprise"] = True
        payload["operation"] = "update"
        payload["inspection"]["baseline_sha256"] = HASH_A
        payload["baseline"] = {
            "path": "baseline",
            "sha256": HASH_B,
            "manifest_sha256": HASH_C,
        }
        errors = validate_session(payload)
        self.assertIn("session.unknown_key:surprise", errors)
        self.assertIn("inspection.baseline_sha256_mismatch", errors)

    def test_valid_w1_waiting_create_session(self) -> None:
        payload = w1_waiting_create()
        self.assertEqual(validate_session(payload), [])
        self.assertEqual(session_gate_state(payload), "WAITING_FOR_W1")

    def test_update_requires_relative_baseline_identity(self) -> None:
        payload = w1_waiting_create()
        payload["operation"] = "update"
        self.assertIn("baseline.required_for_update", validate_session(payload))

        payload["baseline"] = {"path": "C:/private/plugin.zip", "sha256": HASH_A}
        errors = validate_session(payload)
        self.assertIn("baseline.path.invalid_relative_posix_path", errors)

    def test_candidate_requires_matching_w1_plan(self) -> None:
        payload = w1_waiting_create()
        payload["stage"] = "S3"
        payload["candidate"] = {
            "path": "candidate/plugin-builder",
            "sha256": HASH_C,
            "plan_sha256": HASH_D,
        }
        errors = validate_session(payload)
        self.assertIn("candidate.requires_approved_w1", errors)
        self.assertIn("candidate.plan_sha256_mismatch", errors)

    def test_package_requires_matching_w2_and_no_required_failure(self) -> None:
        for mutation, expected in (
            (lambda value: value.__setitem__("w2", None), "package.requires_approved_w2"),
            (
                lambda value: value["w2"].__setitem__("candidate_sha256", HASH_A),
                "w2.candidate_sha256_mismatch",
            ),
            (
                lambda value: value["w2"].__setitem__("verification_sha256", HASH_A),
                "w2.verification_sha256_mismatch",
            ),
            (
                lambda value: value["verification"]["results"][0].__setitem__("state", "FAIL"),
                "package.blocked_by_required_failure",
            ),
        ):
            with self.subTest(expected=expected):
                payload = package_ready()
                mutation(payload)
                self.assertIn(expected, validate_session(payload))

    def test_w2_requires_bound_candidate_and_verification(self) -> None:
        payload = w1_waiting_create()
        payload["stage"] = "W2"
        payload["w1"] = {"approved": True, "plan_sha256": HASH_B}
        payload["w2"] = {
            "approved": True,
            "candidate_sha256": HASH_C,
            "verification_sha256": HASH_D,
        }
        errors = validate_session(payload)
        self.assertIn("w2.requires_candidate", errors)
        self.assertIn("w2.requires_verification", errors)

    def test_stage_cannot_bypass_approval_and_artifact_prerequisites(self) -> None:
        expected_errors = {
            "S3": {"stage.S3.requires_approved_w1"},
            "S5": {
                "stage.S5.requires_approved_w1",
                "stage.S5.requires_candidate",
                "stage.S5.requires_verification",
                "stage.S5.requires_approved_w2",
            },
            "E1": {
                "stage.E1.requires_approved_w1",
                "stage.E1.requires_candidate",
                "stage.E1.requires_verification",
                "stage.E1.requires_approved_w2",
                "stage.E1.requires_package",
            },
        }
        for stage, expected in expected_errors.items():
            with self.subTest(stage=stage):
                payload = w1_waiting_create()
                payload["stage"] = stage
                errors = validate_session(payload)
                self.assertTrue(expected <= set(errors), errors)
                self.assertEqual(session_gate_state(payload), "INVALID")

    def test_verification_covers_registered_required_results_and_requiredness(self) -> None:
        missing = package_ready()
        missing["verification"]["results"] = []
        self.assertIn(
            "verification.missing_required_result:RQ1", validate_session(missing)
        )
        self.assertEqual(session_gate_state(missing), "INVALID")

        downgraded = package_ready()
        downgraded["verification"]["results"][0]["required"] = False
        downgraded["verification"]["results"][0]["state"] = "FAIL"
        errors = validate_session(downgraded)
        self.assertIn("verification.results[0].required_mismatch", errors)
        self.assertEqual(session_gate_state(downgraded), "INVALID")

    def test_package_hash_bindings_match_candidate_and_report(self) -> None:
        payload = package_ready()
        payload["package"]["candidate_sha256"] = HASH_A
        payload["package"]["verification_sha256"] = HASH_A
        errors = validate_session(payload)
        self.assertIn("package.candidate_sha256_mismatch", errors)
        self.assertIn("package.verification_sha256_mismatch", errors)

    def test_not_verified_is_not_collapsed_into_pass(self) -> None:
        payload = package_ready()
        payload["stage"] = "W2"
        payload["w2"] = None
        payload["package"] = None
        self.assertEqual(validate_session(payload), [])
        self.assertEqual(session_gate_state(payload), "WAITING_FOR_W2")
        self.assertEqual(payload["verification"]["results"][1]["state"], "NOT VERIFIED")

    def test_rejects_unsafe_paths_duplicate_ids_and_unsupported_evidence(self) -> None:
        payload = w1_waiting_create()
        payload["workspace_path"] = "../escape"
        payload["requirements"].append(
            {"id": "RQ1", "owner": "duplicate", "evidence": "PROBABLY", "required": True}
        )
        errors = validate_session(payload)
        self.assertIn("workspace_path.invalid_relative_posix_path", errors)
        self.assertIn("requirements.duplicate_id:RQ1", errors)
        self.assertIn("requirements[1].evidence.unsupported", errors)

    def test_rejects_malformed_approvals(self) -> None:
        payload = package_ready()
        payload["w1"] = {"approved": "yes", "plan_sha256": HASH_B, "extra": True}
        payload["w2"] = {"approved": True, "candidate_sha256": HASH_C}
        errors = validate_session(payload)
        self.assertIn("w1.invalid_approval", errors)
        self.assertIn("w2.invalid_approval", errors)

    def test_returns_all_errors_in_deterministic_order(self) -> None:
        payload = {"operation": "delete", "stage": "UNKNOWN", "workspace_path": "/absolute"}
        errors = validate_session(payload)
        self.assertGreater(len(errors), 3)
        self.assertEqual(errors, sorted(set(errors)))

    def test_valid_package_and_operation_document(self) -> None:
        payload = package_ready()
        self.assertEqual(validate_session(payload), [])
        self.assertEqual(session_gate_state(payload), "PACKAGE_ALLOWED")
        self.assertEqual(
            operation_document("validate-session", "FAIL", ["z", "a", "a"], gate="INVALID"),
            {
                "result_schema_version": 1,
                "operation": "validate-session",
                "status": "FAIL",
                "errors": ["a", "z"],
                "gate": "INVALID",
            },
        )


class CliContractTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "plugin_builder.py"), *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
        )

    def assert_ascii_document(self, completed: subprocess.CompletedProcess[str]) -> dict:
        self.assertEqual(completed.stderr, "")
        self.assertEqual(len(completed.stdout.splitlines()), 1)
        completed.stdout.encode("ascii")
        return json.loads(completed.stdout)

    def test_status_is_one_ascii_safe_result_document(self) -> None:
        completed = self.run_cli("status", "--json")
        self.assertEqual(completed.returncode, 0)
        document = self.assert_ascii_document(completed)
        self.assertEqual(document["operation"], "status")
        self.assertEqual(document["status"], "PASS")
        self.assertEqual(document["errors"], [])
        self.assertEqual(
            document["capabilities"],
            {
                "session_contract": "STATICALLY VERIFIED",
                "candidate_build": "NOT VERIFIED",
                "package_build": "NOT VERIFIED",
                "codex_execution": "NOT VERIFIED",
                "chatgpt_work_execution": "NOT VERIFIED",
                "openclaw_execution": "NOT APPLICABLE",
            },
        )

    def test_validate_session_uses_exit_zero_and_three(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            valid_path = root / "valid.json"
            invalid_path = root / "invalid.json"
            valid_path.write_text(json.dumps(w1_waiting_create()), encoding="utf-8")
            invalid_path.write_text(json.dumps({"operation": "delete"}), encoding="utf-8")

            valid = self.run_cli("validate-session", str(valid_path), "--json")
            self.assertEqual(valid.returncode, 0)
            valid_document = self.assert_ascii_document(valid)
            self.assertEqual(valid_document["operation"], "validate-session")
            self.assertEqual(valid_document["status"], "PASS")
            self.assertEqual(valid_document["gate"], "WAITING_FOR_W1")

            invalid = self.run_cli("validate-session", str(invalid_path), "--json")
            self.assertEqual(invalid.returncode, 3)
            invalid_document = self.assert_ascii_document(invalid)
            self.assertEqual(invalid_document["operation"], "validate-session")
            self.assertEqual(invalid_document["status"], "FAIL")
            self.assertEqual(invalid_document["gate"], "INVALID")
            self.assertEqual(invalid_document["errors"], sorted(invalid_document["errors"]))

    def test_malformed_enum_types_return_one_structured_failure(self) -> None:
        payload = package_ready()
        payload["operation"] = []
        payload["stage"] = []
        payload["requirements"][0]["evidence"] = {}
        payload["verification"]["results"][0]["state"] = []
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "malformed.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            completed = self.run_cli("validate-session", str(path), "--json")

        self.assertEqual(completed.returncode, 3)
        document = self.assert_ascii_document(completed)
        self.assertEqual(document["status"], "FAIL")
        self.assertEqual(document["gate"], "INVALID")
        self.assertIn("operation.unsupported", document["errors"])
        self.assertIn("stage.unsupported", document["errors"])
        self.assertIn("requirements[0].evidence.unsupported", document["errors"])
        self.assertIn("verification.results[0].state.unsupported", document["errors"])


if __name__ == "__main__":
    unittest.main()
