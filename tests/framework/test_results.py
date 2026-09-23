from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.results import (
    ArtifactRecord,
    Diagnostic,
    MutationRecord,
    OperationResult,
    load_result,
    operation_result_from_payload,
    result_json,
    result_payload,
)


class OperationResultTests(unittest.TestCase):
    def test_result_json_is_stable_and_path_safe(self) -> None:
        result = OperationResult(
            operation="validate-contract",
            status="BLOCKED",
            code="unclassified_files",
            diagnostics=(
                Diagnostic(
                    "unclassified_file",
                    "skills/demo/SKILL.md",
                    "classification required",
                    ("text", "binary"),
                ),
            ),
        )

        first = result_json(result)

        self.assertEqual(first, result_json(result))
        self.assertTrue(first.endswith("\n"))
        self.assertNotIn("C:\\Users", first)
        self.assertEqual(
            json.loads(first),
            {
                "artifacts": [],
                "code": "unclassified_files",
                "diagnostics": [
                    {
                        "candidates": ["text", "binary"],
                        "code": "unclassified_file",
                        "message": "classification required",
                        "path": "skills/demo/SKILL.md",
                    }
                ],
                "evidence": {},
                "mutations": [],
                "operation": "validate-contract",
                "result_schema_version": 1,
                "status": "BLOCKED",
            },
        )

    def test_result_rejects_unknown_status(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid_result_status"):
            OperationResult(operation="verify", status="OK", code="ok")

    def test_result_rejects_private_absolute_path_in_evidence(self) -> None:
        result = OperationResult(
            operation="verify",
            status="FAIL",
            code="io_failure",
            evidence={"source": "C:\\Users\\person\\private"},
        )

        with self.assertRaisesRegex(ValueError, "private_absolute_path"):
            result_payload(result)

    def test_result_rejects_absolute_record_paths(self) -> None:
        cases = (
            OperationResult(
                operation="verify",
                status="FAIL",
                code="bad_path",
                diagnostics=(Diagnostic("bad", "/private/source", "unsafe"),),
            ),
            OperationResult(
                operation="build",
                status="PASS",
                code="built",
                artifacts=(ArtifactRecord("C:\\output\\bundle.zip", "archive", "a" * 64, 4),),
            ),
            OperationResult(
                operation="prepare",
                status="PASS",
                code="prepared",
                mutations=(MutationRecord("/marketplace/plugin", "create"),),
            ),
        )
        for result in cases:
            with self.subTest(result=result):
                with self.assertRaisesRegex(ValueError, "private_absolute_path"):
                    result_payload(result)

    def test_payload_round_trip_and_file_loading(self) -> None:
        expected = OperationResult(
            operation="build-package",
            status="PASS",
            code="package_built",
            artifacts=(ArtifactRecord("dist/plugin.zip", "archive", "b" * 64, 42),),
            mutations=(MutationRecord("dist/plugin.zip", "create"),),
            evidence={"files": 3, "reproducible": True},
        )

        payload = result_payload(expected)
        self.assertEqual(operation_result_from_payload(payload), expected)

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "result.json"
            path.write_text(result_json(expected), encoding="utf-8")
            self.assertEqual(load_result(path), expected)

    def test_payload_rejects_unknown_fields_and_schema_versions(self) -> None:
        base = result_payload(OperationResult("verify", "PASS", "verified"))
        for key, value, error in (
            ("surprise", True, "unknown_result_key"),
            ("result_schema_version", 2, "unsupported_result_schema_version"),
        ):
            with self.subTest(key=key):
                payload = dict(base)
                payload[key] = value
                with self.assertRaisesRegex(ValueError, error):
                    operation_result_from_payload(payload)


if __name__ == "__main__":
    unittest.main()
