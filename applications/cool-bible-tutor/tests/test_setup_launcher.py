from contextlib import closing
import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import unittest


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "cool_bible_tutor.py"


def load_launcher():
    if not MODULE_PATH.is_file():
        raise ModuleNotFoundError("cool_bible_tutor.py does not exist")
    spec = importlib.util.spec_from_file_location("cool_bible_tutor_launcher", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Completed:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class RecordingRunner:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append((list(command), dict(kwargs)))
        return Completed(self.returncode, self.stdout, self.stderr)


class SetupLauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.launcher = load_launcher()

    def test_data_directory_precedence_keeps_generated_state_external(self):
        root = self.launcher.PLUGIN_ROOT.parent / ".launcher-test-paths"
        explicit = root / "explicit"
        configured = root / "configured"
        plugin_data = root / "plugin-data"
        local_app_data = root / "local-app-data"

        self.assertEqual(
            self.launcher.resolve_data_dir(
                explicit,
                {
                    "COOL_BIBLE_TUTOR_DATA_DIR": str(configured),
                    "PLUGIN_DATA": str(plugin_data),
                },
                local_app_data=local_app_data,
            ),
            explicit.resolve(),
        )
        self.assertEqual(
            self.launcher.resolve_data_dir(
                None,
                {
                    "COOL_BIBLE_TUTOR_DATA_DIR": str(configured),
                    "PLUGIN_DATA": str(plugin_data),
                },
                local_app_data=local_app_data,
            ),
            configured.resolve(),
        )
        self.assertEqual(
            self.launcher.resolve_data_dir(
                None,
                {"PLUGIN_DATA": str(plugin_data)},
                local_app_data=local_app_data,
            ),
            (plugin_data / "cuv").resolve(),
        )
        self.assertEqual(
            self.launcher.resolve_data_dir(
                None, {}, local_app_data=local_app_data,
            ),
            (
                local_app_data / "ObviousOne" / "plugins" / "cool-bible-tutor"
                / "authoring-data"
            ).resolve(),
        )

    def test_init_delegates_to_builder_with_advanced_options(self):
        root = self.launcher.PLUGIN_ROOT.parent / ".launcher-test-options"
        data_dir = root / "data"
        scratch_dir = root / "scratch"
        parser = self.launcher.build_parser()
        args = parser.parse_args([
            "init",
            "--data-dir", str(data_dir),
            "--scratch-dir", str(scratch_dir),
            "--tessdata-dir", str(root / "tessdata"),
            "--dpi", "240",
        ])

        command = self.launcher.build_delegated_command(
            args, data_dir.resolve(), python_executable=Path(sys.executable)
        )

        self.assertEqual(command[0:2], [str(Path(sys.executable)), "-B"])
        self.assertEqual(Path(command[2]).name, "build_cuv_index.py")
        self.assertEqual(command[3:5], ["--data-dir", str(data_dir.resolve())])
        self.assertEqual(
            command[5:],
            [
                "--tessdata-dir", str((root / "tessdata").resolve()),
                "--scratch-dir", str(scratch_dir.resolve()),
                "--dpi", "240",
            ],
        )

    def test_review_and_passage_preserve_user_facing_arguments(self):
        data_dir = (
            self.launcher.PLUGIN_ROOT.parent / ".launcher-test-delegation"
        ).resolve()
        parser = self.launcher.build_parser()

        review = parser.parse_args([
            "review", "--data-dir", str(data_dir), "--port", "8123", "--no-open",
        ])
        review_command = self.launcher.build_delegated_command(
            review, data_dir, python_executable=Path(sys.executable)
        )
        self.assertEqual(Path(review_command[2]).name, "review_cuv_index.py")
        self.assertEqual(
            review_command[3:],
            ["--data-dir", str(data_dir), "--port", "8123", "--no-open"],
        )

        passage = parser.parse_args([
            "passage", "約 3:16", "--data-dir", str(data_dir), "--format", "json",
        ])
        passage_command = self.launcher.build_delegated_command(
            passage, data_dir, python_executable=Path(sys.executable)
        )
        self.assertEqual(Path(passage_command[2]).name, "get_passage.py")
        self.assertEqual(
            passage_command[3:],
            [
                "--reference", "約 3:16",
                "--data-dir", str(data_dir),
                "--format", "json",
            ],
        )

    def test_main_propagates_the_delegated_tool_exit_code(self):
        data_dir = self.launcher.PLUGIN_ROOT.parent / ".launcher-test-exit"
        runner = RecordingRunner(returncode=3)
        result = self.launcher.main(
            ["passage", "約 3:16", "--data-dir", str(data_dir)],
            environ={"LAUNCHER_TEST_MARKER": "preserved"},
            runner=runner,
        )

        self.assertEqual(result, 3)
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(Path(runner.calls[0][0][2]).name, "get_passage.py")
        child_env = runner.calls[0][1]["env"]
        self.assertEqual(child_env["LAUNCHER_TEST_MARKER"], "preserved")
        self.assertEqual(child_env["PYTHONUTF8"], "1")

    def test_status_reports_missing_database_without_starting_a_child(self):
        data_dir = self.launcher.PLUGIN_ROOT.parent / ".launcher-test-missing"
        runner = RecordingRunner()
        output = io.StringIO()
        result = self.launcher.main(
            ["status", "--data-dir", str(data_dir), "--json"],
            environ={},
            runner=runner,
            stdout=output,
        )

        report = json.loads(output.getvalue())
        self.assertEqual(result, 2)
        self.assertEqual(report["database"], "missing")
        self.assertEqual(report["rag"], "not_configured")
        self.assertEqual(runner.calls, [])

    def test_status_uses_bundled_core_without_external_configuration(self):
        output = io.StringIO()

        result = self.launcher.main(
            ["status", "--json"], environ={}, stdout=output
        )

        report = json.loads(output.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(report["core_status"], "core_ready")
        self.assertEqual(report["corpus_origin"], "bundled")
        self.assertEqual(report["approved_source_gaps"], 71)
        self.assertEqual(report["total_rows"], 31008)

    def test_review_never_targets_bundled_database(self):
        args = self.launcher.build_parser().parse_args(["review", "--no-open"])

        with self.assertRaisesRegex(ValueError, "external writable"):
            self.launcher.build_delegated_command(
                args,
                self.launcher.BUNDLED_DATABASE.parent,
                python_executable=Path(sys.executable),
            )

    def test_json_reports_are_safe_on_a_legacy_windows_console(self):
        data_dir = self.launcher.PLUGIN_ROOT.parent / "私人資料"
        bytes_output = io.BytesIO()
        output = io.TextIOWrapper(bytes_output, encoding="cp1252")

        result = self.launcher.main(
            ["status", "--data-dir", str(data_dir), "--json"],
            environ={},
            stdout=output,
        )
        output.flush()
        report = json.loads(bytes_output.getvalue().decode("cp1252"))

        self.assertEqual(result, 2)
        self.assertEqual(report["data_dir"], str(data_dir.resolve()))

    def test_rag_check_reports_optional_missing_configuration(self):
        from types import SimpleNamespace
        from unittest.mock import patch

        output = io.StringIO()
        managed = SimpleNamespace(status="rag_setup_required", reasons=("model missing",))
        with patch.object(self.launcher, "_managed_rag_report", return_value=managed):
            result = self.launcher.main(
                ["rag-check", "--json"],
                environ={},
                stdout=output,
            )

        report = json.loads(output.getvalue())
        self.assertEqual(result, 4)
        self.assertEqual(report["status"], "rag_setup_required")
        self.assertEqual(report["reasons"], ["model missing"])
        self.assertTrue(report["optional"])

    def test_rag_check_recognizes_ready_managed_runtime_without_environment_overrides(self):
        from types import SimpleNamespace
        from unittest.mock import patch

        output = io.StringIO()
        managed = SimpleNamespace(status="rag_ready", reasons=())
        with patch.object(self.launcher, "_managed_rag_report", return_value=managed):
            result = self.launcher.main(
                ["rag-check", "--json"],
                environ={},
                runner=RecordingRunner(),
                stdout=output,
            )

        report = json.loads(output.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(report["status"], "rag_ready")
        self.assertEqual(report["reasons"], [])
        self.assertTrue(report["optional"])

    def test_setup_rag_noninteractive_requires_explicit_consent(self):
        output = io.StringIO()
        runner = RecordingRunner()
        result = self.launcher.main(
            ["setup-rag", "--json"],
            environ={"LOCALAPPDATA": str(self.launcher.PLUGIN_ROOT.parent / ".setup-rag-test")},
            runner=runner,
            stdin=io.StringIO(""),
            stdout=output,
        )
        report = json.loads(output.getvalue())
        self.assertEqual(result, 2)
        self.assertEqual(report["status"], "consent_required")
        self.assertIn("setup-rag", report["next_command"])
        self.assertEqual(runner.calls, [])

    def test_lightweight_package_uses_remote_asset_setup_after_consent(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch

        output = io.StringIO()
        assets = SimpleNamespace(core_ready=False)
        required = SimpleNamespace(status="rag_setup_required")
        ready = SimpleNamespace(status="rag_ready")
        remote_setup = Mock(return_value=ready)
        bundled_setup = Mock(side_effect=AssertionError("bundled setup must not run"))
        with patch.object(self.launcher, "bundled_runtime_assets", return_value=assets), patch.object(
            self.launcher, "inspect_rag_setup", return_value=required
        ), patch.object(self.launcher, "setup_remote_rag", remote_setup, create=True), patch.object(
            self.launcher, "setup_rag", bundled_setup
        ):
            result = self.launcher.main(
                ["setup-rag", "--accept-downloads", "--json"],
                environ={"LOCALAPPDATA": str(self.launcher.PLUGIN_ROOT.parent / ".remote-rag-test")},
                runner=RecordingRunner(),
                stdin=io.StringIO(""),
                stdout=output,
            )

        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "rag_ready")
        remote_setup.assert_called_once()
        bundled_setup.assert_not_called()

    def test_generated_data_inside_the_plugin_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside the installed plugin"):
            self.launcher.resolve_data_dir(
                self.launcher.PLUGIN_ROOT / "generated-data", {},
            )

    def test_doctor_checks_required_tools_pdfs_and_traditional_chinese_ocr(self):
        output = io.StringIO()
        runner = RecordingRunner(
            returncode=0,
            stdout="List of available languages (2):\neng\nchi_tra\n",
        )

        result = self.launcher.main(
            ["doctor", "--json"],
            environ={"LOCALAPPDATA": str(self.launcher.PLUGIN_ROOT.parent / ".launcher-app-data")},
            runner=runner,
            which=lambda name: str(Path("tools") / name),
            stdout=output,
        )

        report = json.loads(output.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(report["source_pdfs"], "ready")
        self.assertEqual(report["ocr_language"], "ready")
        self.assertEqual(
            report["prerequisites"],
            {
                "pdfinfo": "ready",
                "pdftoppm": "ready",
                "pdftotext": "ready",
                "tesseract": "ready",
            },
        )
        self.assertEqual(runner.calls[0][0][-1], "--list-langs")

    def test_doctor_fails_when_required_tools_or_chi_tra_are_missing(self):
        output = io.StringIO()
        runner = RecordingRunner(returncode=0, stdout="eng\n")

        result = self.launcher.main(
            ["doctor", "--json"],
            environ={"LOCALAPPDATA": str(self.launcher.PLUGIN_ROOT.parent / ".launcher-app-data")},
            runner=runner,
            which=lambda name: None if name == "pdftoppm" else name,
            stdout=output,
        )

        report = json.loads(output.getvalue())
        self.assertEqual(result, 2)
        self.assertEqual(report["prerequisites"]["pdftoppm"], "missing")
        self.assertEqual(report["ocr_language"], "missing")

    def test_rag_check_imports_with_the_configured_python(self):
        output = io.StringIO()
        runner = RecordingRunner(returncode=0)

        result = self.launcher.main(
            ["rag-check", "--json"],
            environ={"COOL_BIBLE_TUTOR_RAG_PYTHON": str(Path(sys.executable))},
            runner=runner,
            stdout=output,
        )

        report = json.loads(output.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(report["status"], "ready")
        self.assertEqual(runner.calls[0][0][0], str(Path(sys.executable).resolve()))
        self.assertIn("import rag_subsystem", runner.calls[0][0][-1])

    def test_rag_ingest_and_discover_delegate_filters_without_exposing_chunks(self):
        data_dir = (self.launcher.PLUGIN_ROOT.parent / ".launcher-rag-data").resolve()
        parser = self.launcher.build_parser()

        ingest = parser.parse_args([
            "rag-ingest", "--data-dir", str(data_dir), "--book", "約翰福音", "--chapter", "3",
        ])
        ingest_command = self.launcher.build_delegated_command(
            ingest, data_dir, python_executable=Path(sys.executable)
        )
        self.assertEqual(Path(ingest_command[2]).name, "ingest_bible_rag.py")
        self.assertEqual(
            ingest_command[3:],
            ["--data-dir", str(data_dir), "--book", "約翰福音", "--chapter", "3"],
        )

        discover = parser.parse_args([
            "rag-discover", "饒恕與恩典", "--data-dir", str(data_dir),
            "--top-k", "5", "--book", "馬太福音",
        ])
        discover_command = self.launcher.build_delegated_command(
            discover, data_dir, python_executable=Path(sys.executable)
        )
        self.assertEqual(Path(discover_command[2]).name, "discover_bible_references.py")
        self.assertEqual(
            discover_command[3:],
            [
                "--query", "饒恕與恩典",
                "--data-dir", str(data_dir),
                "--top-k", "5",
                "--book", "馬太福音",
            ],
        )

    def test_status_reports_unverified_rows_and_stale_rag_index(self):
        data_dir = self.launcher.PLUGIN_ROOT.parent / "tmp" / "launcher-status-fixture"
        data_dir.mkdir(parents=True, exist_ok=True)
        database = data_dir / "cuv.sqlite3"
        database.unlink(missing_ok=True)
        try:
            with closing(sqlite3.connect(database)) as connection:
                with connection:
                    connection.executescript(
                        """
                    CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                    CREATE TABLE verses(
                        book_id INTEGER, chapter INTEGER, verse INTEGER, text TEXT,
                        source_file TEXT, source_page INTEGER,
                        ocr_confidence REAL, verified INTEGER
                    );
                    INSERT INTO metadata VALUES('confidence_threshold', '90.0');
                    INSERT INTO metadata VALUES('rag_index_state', 'stale');
                    INSERT INTO verses VALUES(43, 3, 16, '合成甲', 'source.pdf', 1, 99, 1);
                    INSERT INTO verses VALUES(43, 3, 17, '合成乙', 'source.pdf', 1, 89, 0);
                        """
                    )

            output = io.StringIO()
            result = self.launcher.main(
                ["status", "--data-dir", str(data_dir), "--json"],
                environ={},
                stdout=output,
            )
            report = json.loads(output.getvalue())

            self.assertEqual(result, 0)
            self.assertEqual(report["database"], "present")
            self.assertEqual(report["total_rows"], 2)
            self.assertEqual(report["unverified_rows"], 1)
            self.assertEqual(report["rag_index"], "stale")
        finally:
            database.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
