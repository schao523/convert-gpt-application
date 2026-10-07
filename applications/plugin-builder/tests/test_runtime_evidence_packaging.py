from __future__ import annotations

from hashlib import sha256
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
