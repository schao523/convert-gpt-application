from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from obvious_one_plugin_framework.cli import main


FIXTURES = Path(__file__).resolve().parent / "fixtures"
LEGACY = FIXTURES / "plugin-alpha" / "distribution.json"
V3 = FIXTURES / "plugin-v3" / "distribution.json"


class FrameworkCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)

    def invoke(self, *arguments: str) -> tuple[int, dict[str, object]]:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(list(arguments))
        return code, json.loads(stdout.getvalue())

    def test_cli_builds_schema_v3_fixture(self) -> None:
        name = "plugin-v3"
        code, payload = self.invoke(
            "build-package",
            "--contract", str(FIXTURES / name / "distribution.json"),
            "--output", str(self.output / name),
            "--json",
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["code"], "package_built")
        self.assertEqual(payload["evidence"]["plugin_id"], name)
        self.assertTrue((self.output / name / "CONTENT-MANIFEST.json").is_file())

    def test_cli_builds_assets_and_manifest(self) -> None:
        manifest = self.output / "remote-assets.json"
        code, payload = self.invoke(
            "build-assets",
            "--contract", str(FIXTURES / "plugin-v3/distribution.json"),
            "--output", str(self.output / "assets"),
            "--manifest", str(manifest),
            "--json",
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["evidence"]["asset_count"], 1)
        self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["plugin_id"], "plugin-v3")

    def test_cli_json_is_safe_on_legacy_windows_console(self) -> None:
        bytes_output = io.BytesIO()
        output = io.TextIOWrapper(bytes_output, encoding="cp1252")
        with contextlib.redirect_stdout(output):
            code = main([
                "build-assets",
                "--contract", str(FIXTURES / "plugin-v3/distribution.json"),
                "--output", str(self.output / "legacy-assets"),
                "--json",
            ])
        output.flush()
        output.detach()
        self.assertEqual(code, 0)
        payload = json.loads(bytes_output.getvalue().decode("cp1252"))
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["evidence"]["asset_count"], 1)

    def test_cli_reports_blocked_legacy_build(self) -> None:
        target = self.output / "legacy"

        code, payload = self.invoke(
            "build-package", "--contract", str(LEGACY), "--output", str(target)
        )

        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "BLOCKED")
        self.assertEqual(payload["code"], "legacy_contract_read_only")
        self.assertEqual(payload["mutations"], [])
        self.assertFalse(target.exists())

    def test_validate_contract_requires_no_interaction(self) -> None:
        with patch("builtins.input", side_effect=AssertionError("interactive input forbidden")):
            code, payload = self.invoke("validate-contract", "--contract", str(V3))

        self.assertEqual((code, payload["status"]), (0, "PASS"))
        self.assertEqual(payload["code"], "contract_valid")

    def test_parser_error_is_a_single_result_document(self) -> None:
        code, payload = self.invoke("build-package", "--contract", str(V3))

        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["code"], "invalid_cli_arguments")

    def test_invalid_json_is_fail_with_stable_exit_code(self) -> None:
        invalid = self.output / "invalid.json"
        invalid.write_text("not json", encoding="utf-8")

        code, payload = self.invoke("validate-contract", "--contract", str(invalid))

        self.assertEqual(code, 3)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["code"], "invalid_json")

    def test_migration_destination_collision_is_fail_and_preserves_file(self) -> None:
        destination = self.output / "proposal.json"
        destination.write_text("keep", encoding="utf-8")

        code, payload = self.invoke(
            "migrate-contract",
            "--contract", str(LEGACY),
            "--output", str(destination),
        )

        self.assertEqual(code, 3)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["code"], "migration_destination_exists")
        self.assertEqual(destination.read_text(encoding="utf-8"), "keep")

    def test_migration_returns_blocked_result_and_writes_proposal(self) -> None:
        destination = self.output / "proposal.json"

        code, payload = self.invoke(
            "migrate-contract",
            "--contract", str(LEGACY),
            "--output", str(destination),
        )

        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "BLOCKED")
        self.assertEqual(payload["code"], "migration_decisions_required")
        self.assertTrue(destination.is_file())


if __name__ == "__main__":
    unittest.main()
