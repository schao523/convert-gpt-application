from __future__ import annotations

from hashlib import sha256
import copy
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from plugin_builder_core.evidence import build_runtime_evidence_bundle, validate_runtime_result


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def valid_result(evidence_digest: str | None) -> dict:
    return {
        "schema": "plugin-builder-runtime-result-v1",
        "runtime": {"name": "Codex", "version": "1", "os": "Windows", "clean_workspace": True, "discovery_observed": True, "repository_absent": True},
        "artifact": {"zip_sha256": "a" * 64, "member_manifest_sha256": "b" * 64},
        "scenarios": [
            {"id": f"T{index}", "state": "RUNTIME VERIFIED" if index == 1 else "NOT VERIFIED", "result": "PASS" if index == 1 else "NOT VERIFIED", "evidence_sha256": evidence_digest if index == 1 else None, "limitations": []}
            for index in range(1, 8)
        ],
        "tools": [{"tool_id": "normalize", "implementation_kind": "BUNDLED_LOCAL", "state": "RUNTIME VERIFIED", "executed": True, "network_contacted": False, "contract_sha256": "c" * 64, "skill_bindings": ["answering"]}],
        "overall_state": "RUNTIME VERIFIED",
    }


def valid_result_v2(evidence_digest: str | None) -> dict:
    payload = valid_result(evidence_digest)
    payload["schema"] = "plugin-builder-runtime-result-v2"
    payload["runtime"].update({"upload_observed": True, "envelope_profile": "PORTABLE_SINGLE_DIRECTORY"})
    payload["tools"][0].update({
        "declared_argv": ["{python}", "tools/normalize.py", "--self-test"],
        "observed_argv": [sys.executable, "tools/normalize.py", "--self-test"],
        "adapter": "CURRENT_PYTHON",
    })
    payload["evidence_states"] = {
        "structural_validation": "STATICALLY VERIFIED",
        "installation": "RUNTIME VERIFIED",
        "tool_execution": "RUNTIME VERIFIED",
        "reference_consultation": "NOT VERIFIED",
        "conversation": "NOT VERIFIED",
    }
    return payload


def valid_result_v3(evidence_digest: str) -> dict:
    layer = {"state": "RUNTIME VERIFIED", "evidence_sha256": evidence_digest}
    realization = {
        "target_runtime": "Codex", "installation_channel": "OPENAI_PORTABLE_PLUGIN",
        "skill_id": "answering", "capability_id": "normalize-content", "operation_id": "normalize",
        "adapter_id": "mcp-streamable-http", "exposed_capability": "normalize",
        "input_sha256": "d" * 64, "output_sha256": "e" * 64,
        "executed": True, "network_contacted": False, "permissions_observed": [],
        "layers": {name: dict(layer) for name in (
            "structural_validation", "installation", "skill_invocation", "capability_discovery",
            "operation_execution", "result_delivery", "skill_behavior",
        )},
        "state": "RUNTIME VERIFIED", "result": "PASS", "limitations": [],
    }
    return {
        "schema": "plugin-builder-runtime-result-v3",
        "runtime": {
            "name": "Codex", "version": "1", "os": "Windows", "installation_channel": "OPENAI_PORTABLE_PLUGIN",
            "clean_workspace": True, "upload_observed": True, "discovery_observed": True,
            "repository_absent": True, "envelope_profile": "PORTABLE_SINGLE_DIRECTORY",
        },
        "artifact": {
            "plugin_id": "sample-plugin", "version": "1.0.0",
            "zip_sha256": "a" * 64, "member_manifest_sha256": "b" * 64,
        },
        "scenarios": [
            {"id": f"T{index}", "state": "RUNTIME VERIFIED" if index == 8 else "NOT VERIFIED",
             "result": "PASS" if index == 8 else "NOT VERIFIED",
             "evidence_sha256": evidence_digest if index == 8 else None, "limitations": []}
            for index in range(1, 9)
        ],
        "tools": [{
            "tool_id": "normalize", "implementation_kind": "MCP_ADAPTER", "contract_sha256": "c" * 64,
            "skill_bindings": ["answering"],
            "operation_execution": {"operation_id": "normalize", "environment": "INSTALLED_RUNTIME", "state": "RUNTIME VERIFIED", "evidence_sha256": evidence_digest},
            "realizations": [realization],
        }],
        "evidence_states": {
            "structural_validation": "RUNTIME VERIFIED", "installation": "RUNTIME VERIFIED",
            "tool_execution": "RUNTIME VERIFIED", "reference_consultation": "NOT VERIFIED",
            "conversation": "NOT VERIFIED",
        },
        "overall_state": "NOT VERIFIED",
    }


class RuntimeEvidencePackagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.evidence = self.root / "evidence"
        self.evidence.mkdir()
        self.body = b"scenario evidence\n"
        self.digest = sha256(self.body).hexdigest()
        (self.evidence / f"{self.digest}.log").write_bytes(self.body)
        self.result = self.root / "result.json"
        self.result.write_bytes(canonical(valid_result(self.digest)))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_every_non_null_scenario_digest_requires_exactly_one_member(self) -> None:
        duplicate = self.evidence / f"{self.digest}.txt"
        duplicate.write_bytes(self.body)
        outcome = build_runtime_evidence_bundle(self.result, self.evidence, self.root / "bundle.zip")
        self.assertEqual(outcome.status, "FAIL")
        self.assertIn(f"evidence.duplicate:{self.digest}", outcome.errors)

    def test_mentioned_but_absent_digest_is_rejected(self) -> None:
        (self.evidence / f"{self.digest}.log").unlink()
        outcome = build_runtime_evidence_bundle(self.result, self.evidence, self.root / "bundle.zip")
        self.assertIn(f"evidence.missing:{self.digest}", outcome.errors)

    def test_wrong_digest_or_size_is_rejected(self) -> None:
        (self.evidence / f"{self.digest}.log").write_bytes(b"wrong")
        outcome = build_runtime_evidence_bundle(self.result, self.evidence, self.root / "bundle.zip")
        self.assertIn(f"evidence.digest_mismatch:{self.digest}", outcome.errors)

    def test_unindexed_extra_evidence_is_rejected(self) -> None:
        extra = b"extra"
        (self.evidence / f"{sha256(extra).hexdigest()}.log").write_bytes(extra)
        outcome = build_runtime_evidence_bundle(self.result, self.evidence, self.root / "bundle.zip")
        self.assertIn("evidence.unindexed", outcome.errors)

    def test_tool_contract_identity_is_not_mistaken_for_scenario_evidence(self) -> None:
        errors = validate_runtime_result(valid_result(None))
        self.assertEqual(errors, ())

    def test_runtime_result_v2_records_wrapped_installation_commands_and_layers(self) -> None:
        self.assertEqual(validate_runtime_result(valid_result_v2(self.digest)), ())

    def test_v3_accepts_exact_installed_skill_to_result_chain_and_deterministic_bundle(self) -> None:
        payload = valid_result_v3(self.digest)
        self.assertEqual(validate_runtime_result(payload), ())
        self.result.write_bytes(canonical(payload))
        first, second = self.root / "v3-first.zip", self.root / "v3-second.zip"
        self.assertEqual(build_runtime_evidence_bundle(self.result, self.evidence, first).status, "PASS")
        self.assertEqual(build_runtime_evidence_bundle(self.result, self.evidence, second).status, "PASS")
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_v3_rejects_incomplete_or_cross_runtime_realization_claims(self) -> None:
        payload = valid_result_v3(self.digest)
        realization = payload["tools"][0]["realizations"][0]
        realization["layers"]["result_delivery"]["evidence_sha256"] = None
        self.assertIn("result.v3.layer_digest_required:result_delivery", validate_runtime_result(payload))
        realization["layers"]["result_delivery"]["evidence_sha256"] = self.digest
        realization["target_runtime"] = "ChatGPT Work Local/Desktop"
        self.assertIn("result.v3.cross_runtime_realization", validate_runtime_result(payload))

    def test_v3_bundle_requires_every_layer_digest_member(self) -> None:
        payload = valid_result_v3(self.digest)
        other = sha256(b"missing skill invocation").hexdigest()
        payload["tools"][0]["realizations"][0]["layers"]["skill_invocation"]["evidence_sha256"] = other
        self.result.write_bytes(canonical(payload))
        outcome = build_runtime_evidence_bundle(self.result, self.evidence, self.root / "v3-missing.zip")
        self.assertEqual(outcome.status, "FAIL")
        self.assertIn(f"evidence.missing:{other}", outcome.errors)

    def test_v3_rejects_duplicate_stale_private_and_local_only_claims(self) -> None:
        payload = valid_result_v3(self.digest)
        payload["tools"][0]["realizations"].append(copy.deepcopy(payload["tools"][0]["realizations"][0]))
        self.assertIn("result.v3.realization_duplicate", validate_runtime_result(payload))
        payload = valid_result_v3(self.digest)
        payload["artifact"]["zip_sha256"] = "0" * 64
        self.assertIn("result.artifact_identity_invalid", validate_runtime_result(payload))
        payload = valid_result_v3(self.digest)
        payload["tools"][0]["realizations"][0]["permissions_observed"] = ["token=private"]
        self.assertIn("result.v3.permissions_invalid", validate_runtime_result(payload))
        self.assertIn("result.v3.private_value_forbidden", validate_runtime_result(payload))
        payload = valid_result_v3(self.digest)
        realization = payload["tools"][0]["realizations"][0]
        realization["layers"]["skill_invocation"]["state"] = "NOT VERIFIED"
        self.assertIn("result.v3.realization_claim_incomplete", validate_runtime_result(payload))
        payload = valid_result_v3(self.digest)
        payload["tools"][0]["operation_execution"]["environment"] = "BUILD_HOST_LOCAL_MCP"
        self.assertIn("result.v3.local_operation_not_installed", validate_runtime_result(payload))
        payload = valid_result_v3(self.digest)
        payload["tools"][0]["realizations"][0]["adapter_id"] = "unknown-adapter"
        self.assertIn("result.v3.adapter_unsupported", validate_runtime_result(payload))

    def test_v3_malformed_types_fail_closed_without_exception(self) -> None:
        payload = valid_result_v3(self.digest)
        payload["tools"][0]["realizations"][0]["target_runtime"] = ["Codex"]
        self.assertIn("result.v3.invalid_type", validate_runtime_result(payload))
        payload = valid_result_v3(self.digest)
        payload["tools"][0]["realizations"][0]["layers"]["installation"] = []
        self.assertTrue(validate_runtime_result(payload))

    def test_v3_overall_and_t8_claims_require_matching_layer_evidence(self) -> None:
        payload = valid_result_v3(self.digest)
        payload["overall_state"] = "RUNTIME VERIFIED"
        self.assertIn("result.v3.overall_claim_invalid", validate_runtime_result(payload))
        payload = valid_result_v3(self.digest)
        payload["tools"][0]["realizations"][0]["state"] = "NOT VERIFIED"
        self.assertIn("result.v3.t8_realization_required", validate_runtime_result(payload))

    def test_runtime_result_v2_requires_digest_evidence_for_reference_or_conversation_claims(self) -> None:
        payload = valid_result_v2(None)
        payload["evidence_states"]["reference_consultation"] = "RUNTIME VERIFIED"
        self.assertIn("result.layer_evidence_required:reference_consultation", validate_runtime_result(payload))
        payload["evidence_states"]["reference_consultation"] = "NOT VERIFIED"
        payload["evidence_states"]["conversation"] = "RUNTIME VERIFIED"
        self.assertIn("result.layer_evidence_required:conversation", validate_runtime_result(payload))

    def test_runtime_result_v2_rejects_conflated_declared_and_observed_command_shape(self) -> None:
        payload = valid_result_v2(self.digest)
        payload["tools"][0].pop("observed_argv")
        self.assertIn("result.tool_invalid", validate_runtime_result(payload))

    def test_bundle_contains_digest_named_result_evidence_and_index(self) -> None:
        outcome = build_runtime_evidence_bundle(self.result, self.evidence, self.root / "bundle.zip")
        self.assertEqual(outcome.status, "PASS", outcome.errors)
        result_digest = sha256(self.result.read_bytes()).hexdigest()
        with zipfile.ZipFile(self.root / "bundle.zip") as archive:
            self.assertEqual(archive.namelist(), sorted([f"evidence/{self.digest}.log", "evidence-index.json", f"results/{result_digest}.json"]))

    def test_two_evidence_bundles_are_byte_identical(self) -> None:
        first = self.root / "first.zip"
        second = self.root / "second.zip"
        self.assertEqual(build_runtime_evidence_bundle(self.result, self.evidence, first).status, "PASS")
        self.assertEqual(build_runtime_evidence_bundle(self.result, self.evidence, second).status, "PASS")
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_source_replacement_during_copy_cannot_produce_a_false_pass(self) -> None:
        real_copy = __import__("shutil").copyfile

        def replace_then_copy(source, destination):
            Path(source).write_bytes(b"replacement after validation\n")
            return real_copy(source, destination)

        with mock.patch("plugin_builder_core.evidence.shutil.copyfile", side_effect=replace_then_copy):
            outcome = build_runtime_evidence_bundle(self.result, self.evidence, self.root / "raced.zip")
        self.assertEqual(outcome.status, "FAIL")
        self.assertIn(f"evidence.digest_mismatch:{self.digest}", outcome.errors)
        self.assertFalse((self.root / "raced.zip").exists())

    def test_failed_rebuild_preserves_previous_valid_bundle(self) -> None:
        destination = self.root / "bundle.zip"
        self.assertEqual(build_runtime_evidence_bundle(self.result, self.evidence, destination).status, "PASS")
        before = destination.read_bytes()
        (self.evidence / f"{self.digest}.log").unlink()
        self.assertEqual(build_runtime_evidence_bundle(self.result, self.evidence, destination).status, "FAIL")
        self.assertEqual(destination.read_bytes(), before)

    def test_cli_packages_runtime_evidence_with_one_ascii_result(self) -> None:
        destination = self.root / "cli.zip"
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "plugin_builder.py"), "package-runtime-evidence",
             "--result", str(self.result), "--evidence-root", str(self.evidence),
             "--output", str(destination), "--json"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(completed.stderr, "")
        self.assertEqual(len(completed.stdout.splitlines()), 1)
        completed.stdout.encode("ascii")
        self.assertEqual(json.loads(completed.stdout)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
