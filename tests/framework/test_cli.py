from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.cli import main


FIXTURES = Path(__file__).resolve().parent / "fixtures"


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

    def test_cli_builds_both_fixture_plugins(self) -> None:
        for name in ("plugin-alpha", "plugin-beta"):
            code, payload = self.invoke(
                "build-package",
                "--contract", str(FIXTURES / name / "distribution.json"),
                "--output", str(self.output / name),
                "--json",
            )
            self.assertEqual(code, 0)
            self.assertEqual(payload["plugin_id"], name)
            self.assertTrue((self.output / name / "CONTENT-MANIFEST.json").is_file())

    def test_cli_builds_assets_and_manifest(self) -> None:
        manifest = self.output / "remote-assets.json"
        code, payload = self.invoke(
            "build-assets",
            "--contract", str(FIXTURES / "plugin-alpha/distribution.json"),
            "--output", str(self.output / "assets"),
            "--manifest", str(manifest),
            "--json",
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["asset_count"], 2)
        self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["plugin_id"], "plugin-alpha")

    def test_cli_json_is_safe_on_legacy_windows_console(self) -> None:
        bytes_output = io.BytesIO()
        output = io.TextIOWrapper(bytes_output, encoding="cp1252")
        with contextlib.redirect_stdout(output):
            code = main([
                "build-assets",
                "--contract", str(FIXTURES / "plugin-alpha/distribution.json"),
                "--output", str(self.output / "legacy-assets"),
                "--json",
            ])
        output.flush()
        output.detach()
        self.assertEqual(code, 0)
        payload = json.loads(bytes_output.getvalue().decode("cp1252"))
        self.assertEqual(payload["asset_count"], 2)


if __name__ == "__main__":
    unittest.main()
