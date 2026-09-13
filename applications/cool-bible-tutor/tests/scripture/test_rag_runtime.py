import json
import os
import shutil
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPTS = Path(__file__).parents[2] / "skills" / "retrieving-chinese-union-version-scripture" / "scripts"
sys.path.insert(0, str(SCRIPTS))
RUNTIME = Path(__file__).parents[1] / "_runtime_fixture"
RUNTIME.mkdir(exist_ok=True)

from rag_runtime import (  # noqa: E402
    AdapterConfigError,
    AdapterRuntimeError,
    build_bundled_rag_environment,
    bundled_rag_index_status,
    load_rag_api,
    reexec_if_configured,
)


class RagRuntimeTests(unittest.TestCase):
    def test_runtime_selects_bundled_readonly_index(self):
        environment = build_bundled_rag_environment({"PRESERVED": "yes"})
        self.assertEqual(environment["RAG_VECTOR_STORE_BACKEND"], "sqlite_readonly")
        self.assertEqual(
            Path(environment["RAG_VECTOR_STORE_PATH"]),
            Path(__file__).parents[2] / "assets" / "rag" / "cuv-rag-index.sqlite3",
        )
        self.assertEqual(environment["PRESERVED"], "yes")

    def test_runtime_preserves_verified_managed_index(self):
        managed = RUNTIME / "managed" / "cuv-rag-index.sqlite3"
        managed.parent.mkdir(parents=True, exist_ok=True)
        managed.touch()
        self.addCleanup(shutil.rmtree, managed.parents[1], True)
        environment = build_bundled_rag_environment({
            "RAG_VECTOR_STORE_BACKEND": "sqlite_readonly",
            "RAG_VECTOR_STORE_PATH": str(managed),
        })
        self.assertEqual(Path(environment["RAG_VECTOR_STORE_PATH"]), managed)

    def test_bundled_index_status_detects_tamper_and_incompatibility(self):
        plugin = Path(__file__).parents[2]
        source_assets = plugin / "assets"
        root = RUNTIME / "rag-runtime-status"
        if root.exists():
            shutil.rmtree(root)
        rag = root / "rag"
        scripture = root / "scripture"
        rag.mkdir(parents=True)
        scripture.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, root, True)
        for name in (
            "cuv-rag-index.sqlite3",
            "cuv-rag-runtime-manifest.json",
            "bge-large-zh-v1.5-model-manifest.json",
        ):
            shutil.copy2(source_assets / "rag" / name, rag / name)
        shutil.copy2(
            source_assets / "scripture" / "cuv-runtime-manifest.json",
            scripture / "cuv-runtime-manifest.json",
        )

        paths = {
            "index": rag / "cuv-rag-index.sqlite3",
            "runtime_manifest": rag / "cuv-rag-runtime-manifest.json",
            "model_manifest": rag / "bge-large-zh-v1.5-model-manifest.json",
            "corpus_manifest": scripture / "cuv-runtime-manifest.json",
        }
        self.assertEqual(bundled_rag_index_status(**paths)["status"], "current")

        with paths["index"].open("ab") as handle:
            handle.write(b"tampered")
        self.assertEqual(bundled_rag_index_status(**paths)["status"], "tampered")

        shutil.copy2(source_assets / "rag" / "cuv-rag-index.sqlite3", paths["index"])
        model = json.loads(paths["model_manifest"].read_text(encoding="utf-8"))
        model["revision"] = "0" * 40
        paths["model_manifest"].write_text(json.dumps(model), encoding="utf-8")
        self.assertEqual(bundled_rag_index_status(**paths)["status"], "incompatible")

    def test_invalid_configured_root_is_rejected(self):
        with self.assertRaisesRegex(AdapterConfigError, "rag_subsystem"):
            load_rag_api({"COOL_BIBLE_TUTOR_RAG_ROOT": str(RUNTIME / "missing")})

    def test_loader_exposes_only_the_public_rag_boundary(self):
        root = RUNTIME / "fake-rag-root"
        package = root / "rag_subsystem"
        package.mkdir(parents=True, exist_ok=True)
        init_file = package / "__init__.py"
        init_file.touch()
        self.addCleanup(init_file.unlink, missing_ok=True)
        public_module = SimpleNamespace(
            process_files=object(),
            retrieve_data=object(),
            ProcessConfig=object(),
            DEFAULT_RETRIEVAL_CONFIG=object(),
        )

        with patch("rag_runtime.importlib.import_module", return_value=public_module) as importer:
            api = load_rag_api({"COOL_BIBLE_TUTOR_RAG_ROOT": str(root)})

        importer.assert_called_once_with("rag_subsystem")
        self.assertIs(api.process_files, public_module.process_files)
        self.assertIs(api.retrieve_data, public_module.retrieve_data)
        self.assertIs(api.ProcessConfig, public_module.ProcessConfig)
        self.assertIs(api.default_retrieval_config, public_module.DEFAULT_RETRIEVAL_CONFIG)

    def test_import_failure_is_a_runtime_error(self):
        with patch("rag_runtime.importlib.import_module", side_effect=ModuleNotFoundError("missing")):
            with self.assertRaisesRegex(
                AdapterRuntimeError, "ModuleNotFoundError: missing"
            ):
                load_rag_api({})

    def test_reexec_uses_configured_python_once(self):
        calls = []
        fake_python = RUNTIME / "python.exe"
        fake_python.touch()
        self.addCleanup(fake_python.unlink, missing_ok=True)

        code = reexec_if_configured(
            Path("adapter.py"),
            ["--query", "恩典"],
            {"COOL_BIBLE_TUTOR_RAG_PYTHON": str(fake_python), "PRESERVED": "yes"},
            runner=lambda command, env: calls.append((command, env)) or SimpleNamespace(returncode=7),
            current_python=RUNTIME / "current.exe",
        )

        self.assertEqual(code, 7)
        self.assertEqual(calls[0][0], [str(fake_python.resolve()), "-B", str(Path("adapter.py").resolve()), "--query", "恩典"])
        self.assertEqual(calls[0][1]["_COOL_BIBLE_TUTOR_RAG_REEXEC"], "1")
        self.assertEqual(calls[0][1]["PRESERVED"], "yes")

    def test_reexec_preserves_the_configured_venv_executable_path(self):
        calls = []
        fake_python = RUNTIME / "venv" / "python.exe"
        system_python = RUNTIME / "system" / "python.exe"
        fake_python.parent.mkdir(parents=True, exist_ok=True)
        system_python.parent.mkdir(parents=True, exist_ok=True)
        fake_python.touch()
        system_python.touch()
        original_resolve = Path.resolve

        def simulated_resolve(path):
            if path == fake_python:
                return system_python
            return original_resolve(path)

        with patch("rag_runtime.Path.resolve", autospec=True, side_effect=simulated_resolve):
            reexec_if_configured(
                Path("adapter.py"),
                [],
                {"COOL_BIBLE_TUTOR_RAG_PYTHON": str(fake_python)},
                runner=lambda command, env: calls.append(command)
                or SimpleNamespace(returncode=0),
                current_python=RUNTIME / "current.exe",
            )

        self.assertEqual(calls[0][0], str(fake_python.absolute()))

    def test_guarded_process_does_not_reexec(self):
        result = reexec_if_configured(
            Path("adapter.py"),
            [],
            {"COOL_BIBLE_TUTOR_RAG_PYTHON": "python.exe", "_COOL_BIBLE_TUTOR_RAG_REEXEC": "1"},
        )
        self.assertIsNone(result)

    def test_missing_configured_python_is_rejected(self):
        with self.assertRaisesRegex(AdapterConfigError, "RAG_PYTHON"):
            reexec_if_configured(
                Path("adapter.py"),
                [],
                {"COOL_BIBLE_TUTOR_RAG_PYTHON": str(RUNTIME / "missing-python.exe")},
            )

    def test_unconfigured_python_keeps_current_process(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(reexec_if_configured(Path("adapter.py"), []))


if __name__ == "__main__":
    unittest.main()
