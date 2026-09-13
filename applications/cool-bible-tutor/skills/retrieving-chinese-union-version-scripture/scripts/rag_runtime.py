from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
import hashlib
import importlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys


REEXEC_GUARD = "_COOL_BIBLE_TUTOR_RAG_REEXEC"
PLUGIN_ROOT = Path(__file__).resolve().parents[3]
BUNDLED_RAG_INDEX = PLUGIN_ROOT / "assets" / "rag" / "cuv-rag-index.sqlite3"
BUNDLED_RAG_MANIFEST = (
    PLUGIN_ROOT / "assets" / "rag" / "cuv-rag-runtime-manifest.json"
)
BUNDLED_MODEL_MANIFEST = (
    PLUGIN_ROOT / "assets" / "rag" / "bge-large-zh-v1.5-model-manifest.json"
)
BUNDLED_CORPUS_MANIFEST = (
    PLUGIN_ROOT / "assets" / "scripture" / "cuv-runtime-manifest.json"
)


class AdapterConfigError(ValueError):
    pass


class AdapterRuntimeError(RuntimeError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("manifest must be a JSON object")
    return payload


def bundled_rag_index_status(
    *,
    index: Path = BUNDLED_RAG_INDEX,
    runtime_manifest: Path = BUNDLED_RAG_MANIFEST,
    model_manifest: Path = BUNDLED_MODEL_MANIFEST,
    corpus_manifest: Path = BUNDLED_CORPUS_MANIFEST,
) -> dict[str, str]:
    paths = tuple(map(Path, (index, runtime_manifest, model_manifest, corpus_manifest)))
    if not all(path.is_file() for path in paths):
        return {"status": "incompatible", "reason": "runtime assets are incomplete"}
    try:
        runtime = _read_json(runtime_manifest)
        model = _read_json(model_manifest)
        corpus = _read_json(corpus_manifest)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return {"status": "incompatible", "reason": "runtime manifest is invalid"}

    try:
        if _sha256_file(index) != runtime.get("index_sha256"):
            return {"status": "tampered", "reason": "RAG index digest mismatch"}
        bindings = (
            (runtime.get("corpus_manifest_sha256"), _sha256_file(corpus_manifest)),
            (runtime.get("model_manifest_sha256"), _sha256_file(model_manifest)),
            (runtime.get("corpus_database_sha256"), corpus.get("database_sha256")),
            (runtime.get("corpus_structure_sha256"), corpus.get("corpus_structure_sha256")),
            (runtime.get("model_revision"), model.get("revision")),
            (runtime.get("model_files"), model.get("files")),
            (runtime.get("model_route"), model.get("route")),
            (runtime.get("dimensions"), model.get("dimensions")),
        )
        if any(expected != actual for expected, actual in bindings):
            return {"status": "incompatible", "reason": "runtime asset binding mismatch"}

        uri = index.resolve().as_uri() + "?mode=ro&immutable=1"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            metadata = dict(connection.execute("SELECT key, value FROM index_metadata"))
            count, dimensions, app_count, app_id = connection.execute(
                "SELECT COUNT(*), MIN(length(embedding)), COUNT(DISTINCT app_id), MIN(app_id) "
                "FROM chunks"
            ).fetchone()
            source_order = connection.execute(
                "SELECT MIN(source_order), MAX(source_order), COUNT(DISTINCT source_order) "
                "FROM chunks"
            ).fetchone()
        if integrity != "ok" or tables != {"index_metadata", "chunks"}:
            raise ValueError("SQLite integrity or table allowlist mismatch")
        if (count, dimensions, app_count, app_id) != (9942, 4096, 1, "cool-bible-tutor"):
            raise ValueError("SQLite item, dimension, or app identity mismatch")
        if source_order != (0, 9941, 9942):
            raise ValueError("SQLite source order mismatch")
        if any(
            metadata.get(key) != str(runtime[value])
            for key, value in (
                ("item_count", "item_count"),
                ("dimensions", "dimensions"),
                ("vector_identity_sha256", "vector_identity_sha256"),
                ("corpus_database_sha256", "corpus_database_sha256"),
                ("corpus_structure_sha256", "corpus_structure_sha256"),
                ("model_revision", "model_revision"),
            )
        ):
            raise ValueError("SQLite embedded metadata mismatch")
    except (OSError, sqlite3.Error, TypeError, ValueError):
        return {"status": "incompatible", "reason": "RAG index schema is incompatible"}
    return {"status": "current", "reason": "manifest and SQLite checks passed"}


def build_bundled_rag_environment(
    base: Mapping[str, str] | None = None,
) -> dict[str, str]:
    environment = dict(os.environ if base is None else base)
    configured_index = str(environment.get("RAG_VECTOR_STORE_PATH", "")).strip()
    if (
        environment.get("RAG_VECTOR_STORE_BACKEND") == "sqlite_readonly"
        and configured_index
        and Path(configured_index).is_file()
    ):
        return environment
    status = bundled_rag_index_status()
    if status["status"] != "current":
        raise AdapterRuntimeError(
            f"Bundled RAG index is {status['status']}: {status['reason']}"
        )
    environment["RAG_VECTOR_STORE_BACKEND"] = "sqlite_readonly"
    environment["RAG_VECTOR_STORE_PATH"] = str(BUNDLED_RAG_INDEX)
    return environment


def managed_runtime_environment(
    base: Mapping[str, str] | None = None,
) -> tuple[dict[str, str], object]:
    environment = dict(os.environ if base is None else base)
    from rag_setup import RuntimePaths, bundled_runtime_assets, inspect_rag_setup

    app_data = environment.get("LOCALAPPDATA") or environment.get("XDG_DATA_HOME")
    paths = RuntimePaths.for_user(Path(app_data) if app_data else None)
    assets = bundled_runtime_assets()
    report = inspect_rag_setup(paths, assets)
    if report.status == "rag_ready":
        environment["COOL_BIBLE_TUTOR_RAG_PYTHON"] = str(report.python_executable)
        environment["RAG_EMBEDDING_BACKEND"] = "local"
        environment["RAG_EMBEDDING_MODEL"] = "bge-large-zh"
        environment["RAG_EMBEDDING_MODEL_PATH"] = str(report.model_path)
        environment["RAG_EMBEDDING_LOCAL_ONLY"] = "true"
        environment["RAG_EMBEDDING_DIM"] = "1024"
        if report.index_path is not None:
            candidates = tuple(Path(report.index_path).rglob("cuv-rag-index.sqlite3"))
            if candidates:
                environment["RAG_VECTOR_STORE_BACKEND"] = "sqlite_readonly"
                environment["RAG_VECTOR_STORE_PATH"] = str(candidates[0].resolve())
        if report.source_assets_path is not None:
            sources = sorted(Path(report.source_assets_path).rglob("*.pdf"))
            if sources:
                environment["COOL_BIBLE_TUTOR_SOURCE_PDFS"] = os.pathsep.join(
                    str(path.resolve()) for path in sources
                )
    return environment, report


@dataclass(frozen=True)
class RagApi:
    process_files: Callable
    retrieve_data: Callable
    ProcessConfig: type
    default_retrieval_config: object


def load_rag_api(environ: Mapping[str, str] | None = None) -> RagApi:
    env = os.environ if environ is None else environ
    configured_root = str(env.get("COOL_BIBLE_TUTOR_RAG_ROOT", "")).strip()
    if configured_root:
        root = Path(configured_root).expanduser().resolve()
        package = root / "rag_subsystem" / "__init__.py"
        if not package.is_file():
            raise AdapterConfigError(
                "COOL_BIBLE_TUTOR_RAG_ROOT must contain rag_subsystem/__init__.py"
            )
        root_text = str(root)
        if root_text not in sys.path:
            sys.path.insert(0, root_text)

    try:
        module = importlib.import_module("rag_subsystem")
        return RagApi(
            process_files=module.process_files,
            retrieve_data=module.retrieve_data,
            ProcessConfig=module.ProcessConfig,
            default_retrieval_config=module.DEFAULT_RETRIEVAL_CONFIG,
        )
    except Exception as error:
        detail = f"{type(error).__name__}: {error}"
        raise AdapterRuntimeError(
            f"rag_subsystem is unavailable or has an incompatible API ({detail})"
        ) from error


def reexec_if_configured(
    script: Path,
    argv: Sequence[str],
    environ: Mapping[str, str] | None = None,
    runner: Callable = subprocess.run,
    current_python: Path | None = None,
) -> int | None:
    env = os.environ if environ is None else environ
    if env.get(REEXEC_GUARD) == "1":
        return None

    configured_python = str(env.get("COOL_BIBLE_TUTOR_RAG_PYTHON", "")).strip()
    if not configured_python:
        return None
    executable = Path(os.path.abspath(Path(configured_python).expanduser()))
    if not executable.is_file():
        raise AdapterConfigError("COOL_BIBLE_TUTOR_RAG_PYTHON must name an existing executable")

    active_executable = Path(sys.executable if current_python is None else current_python).resolve()
    if executable == active_executable:
        return None

    child_environment = dict(env)
    child_environment[REEXEC_GUARD] = "1"
    command = [str(executable), "-B", str(Path(script).resolve()), *argv]
    try:
        completed = runner(command, env=child_environment)
    except OSError as error:
        raise AdapterRuntimeError("Configured RAG Python could not be started") from error
    return int(completed.returncode)
