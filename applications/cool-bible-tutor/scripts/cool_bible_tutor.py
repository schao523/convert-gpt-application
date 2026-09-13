"""Stable command-line launcher for Cool Bible Tutor local supporting tools."""

from __future__ import annotations

import argparse
from contextlib import closing
import json
import os
import platform
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from typing import Mapping, Sequence, TextIO


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_SCRIPTS = PLUGIN_ROOT / "scripts"
SCRIPTURE_SCRIPTS = (
    PLUGIN_ROOT
    / "skills"
    / "retrieving-chinese-union-version-scripture"
    / "scripts"
)
BUNDLED_DATABASE = PLUGIN_ROOT / "assets" / "scripture" / "cuv.sqlite3"
BUNDLED_APPROVED_GAPS = (
    PLUGIN_ROOT / "assets" / "scripture" / "cuv-approved-gaps.json"
)
BUNDLED_RUNTIME_MANIFEST = (
    PLUGIN_ROOT / "assets" / "scripture" / "cuv-runtime-manifest.json"
)
DATA_ENV = "COOL_BIBLE_TUTOR_DATA_DIR"
RAG_PYTHON_ENV = "COOL_BIBLE_TUTOR_RAG_PYTHON"
RAG_ROOT_ENV = "COOL_BIBLE_TUTOR_RAG_ROOT"

for import_root in (LAUNCHER_SCRIPTS, SCRIPTURE_SCRIPTS):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from rag_setup import (  # noqa: E402
    ConsentRequired,
    IntegrityError,
    RuntimePaths,
    UnsupportedRuntime,
    bundled_runtime_assets,
    http_downloader,
    inspect_rag_setup,
    setup_rag,
    setup_remote_rag,
)


def _add_data_dir(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data-dir", type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Set up, verify, review, and test Cool Bible Tutor data."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check local prerequisites.")
    _add_data_dir(doctor)
    doctor.add_argument("--json", action="store_true")

    init = subparsers.add_parser("init", help="Create or resume cuv.sqlite3.")
    _add_data_dir(init)
    init.add_argument("--tessdata-dir", type=Path)
    init.add_argument("--scratch-dir", type=Path)
    init.add_argument("--dpi", type=int, default=300)

    status = subparsers.add_parser("status", help="Report local data readiness.")
    _add_data_dir(status)
    status.add_argument("--json", action="store_true")

    verify = subparsers.add_parser("verify", help="Verify the structured corpus.")
    _add_data_dir(verify)
    verify.add_argument("--json", action="store_true")

    review = subparsers.add_parser("review", help="Open the local review tool.")
    _add_data_dir(review)
    review.add_argument("--port", type=int, default=0)
    review.add_argument("--no-open", action="store_true")

    passage = subparsers.add_parser("passage", help="Test exact passage retrieval.")
    passage.add_argument("reference")
    _add_data_dir(passage)
    passage.add_argument("--format", choices=("json", "text"), default="text")

    rag_check = subparsers.add_parser("rag-check", help="Check optional RAGenius.")
    rag_check.add_argument("--json", action="store_true")

    setup = subparsers.add_parser(
        "setup-rag", help="Install the optional verified semantic-discovery runtime."
    )
    setup.add_argument("--accept-downloads", action="store_true")
    setup.add_argument("--repair", action="store_true")
    setup.add_argument("--json", action="store_true")

    rag_ingest = subparsers.add_parser("rag-ingest", help="Ingest the corpus into RAG.")
    _add_data_dir(rag_ingest)
    rag_ingest.add_argument("--book")
    rag_ingest.add_argument("--chapter", type=int)

    rag_discover = subparsers.add_parser(
        "rag-discover", help="Test topic-based reference discovery."
    )
    rag_discover.add_argument("query")
    _add_data_dir(rag_discover)
    rag_discover.add_argument("--top-k", type=int, default=10)
    rag_discover.add_argument("--book")
    return parser


def _default_local_app_data(environ: Mapping[str, str]) -> Path:
    configured = str(environ.get("LOCALAPPDATA", "")).strip()
    if configured:
        return Path(configured).expanduser()
    xdg = str(environ.get("XDG_DATA_HOME", "")).strip()
    if xdg:
        return Path(xdg).expanduser()
    return Path.home() / ".local" / "share"


def resolve_data_dir(
    explicit: Path | None,
    environ: Mapping[str, str],
    *,
    local_app_data: Path | None = None,
) -> Path:
    if explicit is not None:
        selected = explicit
    elif str(environ.get(DATA_ENV, "")).strip():
        selected = Path(environ[DATA_ENV])
    elif str(environ.get("PLUGIN_DATA", "")).strip():
        selected = Path(environ["PLUGIN_DATA"]) / "cuv"
    else:
        base = _default_local_app_data(environ) if local_app_data is None else local_app_data
        selected = (
            Path(base) / "ObviousOne" / "plugins" / "cool-bible-tutor"
            / "authoring-data"
        )
    resolved = Path(selected).expanduser().resolve()
    if resolved == PLUGIN_ROOT or resolved.is_relative_to(PLUGIN_ROOT):
        raise ValueError("Generated data must stay outside the installed plugin")
    return resolved


def resolve_runtime_database(
    explicit_data_dir: Path | None,
    environ: Mapping[str, str],
) -> tuple[Path, str]:
    if explicit_data_dir is not None:
        return Path(explicit_data_dir).expanduser().resolve() / "cuv.sqlite3", "external"
    configured = str(environ.get(DATA_ENV, "")).strip()
    if configured:
        return Path(configured).expanduser().resolve() / "cuv.sqlite3", "external"
    return BUNDLED_DATABASE, "bundled"


def _append_path(command: list[str], option: str, value: Path | None) -> None:
    if value is not None:
        command.extend((option, str(Path(value).expanduser().resolve())))


def build_delegated_command(
    args: argparse.Namespace,
    data_dir: Path,
    *,
    python_executable: Path,
) -> list[str]:
    scripts = {
        "init": "build_cuv_index.py",
        "verify": "verify_cuv_index.py",
        "review": "review_cuv_index.py",
        "passage": "get_passage.py",
        "rag-ingest": "ingest_bible_rag.py",
        "rag-discover": "discover_bible_references.py",
    }
    if args.command not in scripts:
        raise ValueError(f"Command is not delegated: {args.command}")
    resolved_data_dir = Path(data_dir).resolve()
    if args.command in {"init", "review", "rag-ingest"} and (
        resolved_data_dir == PLUGIN_ROOT
        or resolved_data_dir.is_relative_to(PLUGIN_ROOT)
    ):
        raise ValueError("Authoring commands require an external writable data directory")

    command = [
        str(Path(python_executable)),
        "-B",
        str(SCRIPTURE_SCRIPTS / scripts[args.command]),
    ]
    if args.command == "verify":
        command.append(str(data_dir / "cuv.sqlite3"))
        if (data_dir / "cuv.sqlite3").resolve() == BUNDLED_DATABASE.resolve():
            command.extend(("--approved-gaps", str(BUNDLED_APPROVED_GAPS)))
        if args.json:
            command.append("--json")
    elif args.command == "init":
        command.extend(("--data-dir", str(data_dir)))
        _append_path(command, "--tessdata-dir", args.tessdata_dir)
        _append_path(command, "--scratch-dir", args.scratch_dir)
        command.extend(("--dpi", str(args.dpi)))
    elif args.command == "review":
        command.extend(("--data-dir", str(data_dir), "--port", str(args.port)))
        if args.no_open:
            command.append("--no-open")
    elif args.command == "passage":
        command.extend((
            "--reference", args.reference,
            "--data-dir", str(data_dir),
            "--format", args.format,
        ))
    elif args.command == "rag-ingest":
        command.extend(("--data-dir", str(data_dir)))
        if args.book:
            command.extend(("--book", args.book))
        if args.chapter is not None:
            command.extend(("--chapter", str(args.chapter)))
    elif args.command == "rag-discover":
        command.extend((
            "--query", args.query,
            "--data-dir", str(data_dir),
            "--top-k", str(args.top_k),
        ))
        if args.book:
            command.extend(("--book", args.book))
    return command


def _write_report(report: dict, as_json: bool, stdout: TextIO) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=True, sort_keys=True), file=stdout)
        return
    for key, value in report.items():
        print(f"{key}: {value}", file=stdout)


def _frozen_corpus_verification() -> dict:
    from distribution_audit import audit_public_corpus

    issues = audit_public_corpus(PLUGIN_ROOT)
    try:
        runtime = json.loads(BUNDLED_RUNTIME_MANIFEST.read_text(encoding="utf-8"))
        gaps = json.loads(BUNDLED_APPROVED_GAPS.read_text(encoding="utf-8"))
        approved = list(gaps["gaps"])
        if len(approved) != runtime["approved_source_gaps"]:
            issues = sorted({*issues, "approved-gap count mismatch"})
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError):
        approved = []
        issues = sorted({*issues, "public corpus manifest is invalid"})
    return {
        "production_ready": not issues,
        "issues": issues,
        "approved_source_gaps": approved,
    }


def _rag_configuration(environ: Mapping[str, str]) -> str:
    if str(environ.get(RAG_PYTHON_ENV, "")).strip() or str(
        environ.get(RAG_ROOT_ENV, "")
    ).strip():
        return "configured"
    return "not_configured"


def _runtime_paths(environ: Mapping[str, str]) -> RuntimePaths:
    return RuntimePaths.for_user(_default_local_app_data(environ))


def _managed_rag_report(environ: Mapping[str, str]):
    assets = bundled_runtime_assets()
    return inspect_rag_setup(_runtime_paths(environ), assets)


def _platform_tag() -> str:
    machine = platform.machine().lower()
    arch = "arm64" if machine in {"arm64", "aarch64"} else "x86_64"
    system = "windows" if sys.platform == "win32" else "macos" if sys.platform == "darwin" else "linux"
    return f"{system}-{arch}"


def _setup_rag_command(
    args: argparse.Namespace,
    environ: Mapping[str, str],
    runner,
    downloader,
    stdin: TextIO,
    stdout: TextIO,
) -> int:
    assets = bundled_runtime_assets()
    paths = _runtime_paths(environ)
    current = inspect_rag_setup(paths, assets)
    if current.status == "rag_ready" and not args.repair:
        _write_report({"status": "rag_ready", "reused": True}, args.json, stdout)
        return 0
    consent = bool(args.accept_downloads)
    if not consent and bool(getattr(stdin, "isatty", lambda: False)()):
        notice = {
            "action": "Install a private CPU-only Python runtime and pinned embedding model",
            "download_bytes": 1302771424,
            "storage_root": str(paths.root),
            "licenses": "MIT model; dependency notices included with the plugin",
        }
        _write_report(notice, False, stdout)
        print("Type yes to continue:", file=stdout)
        consent = stdin.readline().strip().lower() == "yes"
    if not consent:
        _write_report({
            "status": "consent_required",
            "next_command": "python scripts/cool_bible_tutor.py setup-rag --accept-downloads",
        }, args.json, stdout)
        return 2
    try:
        setup = setup_rag if assets.core_ready else setup_remote_rag
        report = setup(
            paths,
            assets,
            consent=True,
            runner=runner,
            downloader=downloader,
            platform_tag=_platform_tag(),
            python_version=(sys.version_info.major, sys.version_info.minor),
            repair=args.repair,
        )
    except ConsentRequired:
        return 2
    except UnsupportedRuntime as error:
        _write_report({"status": "rag_incompatible", "reason": str(error)}, args.json, stdout)
        return 4
    except (IntegrityError, RuntimeError, OSError) as error:
        _write_report({"status": "rag_incomplete", "reason": str(error)}, args.json, stdout)
        return 4
    _write_report({"status": report.status, "reused": False}, args.json, stdout)
    return 0 if report.status == "rag_ready" else 4


def _status(
    database: Path,
    corpus_origin: str,
    environ: Mapping[str, str],
) -> tuple[int, dict]:
    report = {
        "data_dir": str(database.parent),
        "database": "present" if database.is_file() else "missing",
        "corpus_origin": corpus_origin,
        "core_status": "core_missing",
        "rag": _rag_configuration(environ),
        "rag_index": "unknown",
    }
    if not database.is_file():
        return 2, report

    try:
        uri = database.resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            metadata = dict(connection.execute("SELECT key, value FROM metadata"))
            threshold = float(metadata.get("confidence_threshold", "90.0"))
            total_rows, unverified_rows = connection.execute(
                """
                SELECT COUNT(*),
                       COALESCE(SUM(
                           CASE WHEN verified = 0 OR ocr_confidence < ? THEN 1 ELSE 0 END
                       ), 0)
                FROM verses
                """,
                (threshold,),
            ).fetchone()
    except (OSError, sqlite3.Error, TypeError, ValueError):
        report["database"] = "invalid"
        return 2, report

    report["total_rows"] = int(total_rows)
    report["unverified_rows"] = int(unverified_rows)
    report["approved_source_gaps"] = 0
    if corpus_origin == "bundled":
        verification = _frozen_corpus_verification()
        report["approved_source_gaps"] = len(verification["approved_source_gaps"])
        report["core_status"] = (
            "core_ready" if verification["production_ready"] else "runtime_asset_tampered"
        )
        if not verification["production_ready"]:
            report["core_issues"] = verification["issues"]
            return 2, report
    else:
        report["core_status"] = (
            "core_ready" if int(unverified_rows) == 0 else "core_review_required"
        )
    if metadata.get("rag_index_state") == "stale":
        report["rag_index"] = "stale"
    elif "rag_vector_item_count" in metadata:
        report["rag_index"] = "current"
    else:
        report["rag_index"] = "not_built"
    try:
        managed = _managed_rag_report(environ)
        report["rag"] = managed.status
        report["rag_reasons"] = list(managed.reasons)
    except IntegrityError as error:
        report["rag"] = "runtime_asset_tampered"
        report["rag_reasons"] = [str(error)]
    return 0, report


def _rag_check(environ: Mapping[str, str], runner) -> tuple[int, dict]:
    try:
        managed = _managed_rag_report(environ)
    except IntegrityError as error:
        return 4, {
            "status": "runtime_asset_tampered",
            "optional": True,
            "reasons": [str(error)],
        }
    if managed.status == "rag_ready":
        return 0, {
            "status": managed.status,
            "optional": True,
            "reasons": list(managed.reasons),
        }
    status = _rag_configuration(environ)
    if status == "not_configured":
        return 4, {
            "status": managed.status,
            "optional": True,
            "reasons": list(managed.reasons),
        }

    configured_python = str(environ.get(RAG_PYTHON_ENV, "")).strip()
    python_executable = Path(configured_python or sys.executable).expanduser().resolve()
    if not python_executable.is_file():
        return 4, {"status": "python_missing", "optional": True}

    child_environment = dict(environ)
    configured_root = str(environ.get(RAG_ROOT_ENV, "")).strip()
    if configured_root:
        rag_root = Path(configured_root).expanduser().resolve()
        if not (rag_root / "rag_subsystem" / "__init__.py").is_file():
            return 4, {"status": "root_invalid", "optional": True}
        existing = str(child_environment.get("PYTHONPATH", "")).strip()
        child_environment["PYTHONPATH"] = (
            str(rag_root) if not existing else str(rag_root) + os.pathsep + existing
        )

    try:
        completed = runner(
            [
                str(python_executable),
                "-B",
                "-c",
                "import rag_subsystem; print('rag_subsystem ready')",
            ],
            env=child_environment,
            capture_output=True,
            text=True,
        )
    except OSError:
        return 4, {"status": "unavailable", "optional": True}
    return (
        (0, {"status": "ready", "optional": True})
        if int(completed.returncode) == 0
        else (4, {"status": "unavailable", "optional": True})
    )


def _doctor(data_dir: Path, environ: Mapping[str, str], runner, which) -> tuple[int, dict]:
    tool_names = ("pdfinfo", "pdftoppm", "pdftotext", "tesseract")
    resolved_tools = {name: which(name) for name in tool_names}
    prerequisites = {
        name: "ready" if resolved_tools[name] else "missing" for name in tool_names
    }

    scripture_dir = PLUGIN_ROOT / "assets" / "scripture"
    source_pdfs = "ready" if len(tuple(scripture_dir.glob("*.pdf"))) == 2 else "missing"
    ocr_language = "missing"
    tesseract = resolved_tools["tesseract"]
    if tesseract:
        try:
            completed = runner(
                [str(tesseract), "--list-langs"],
                env=dict(environ),
                capture_output=True,
                text=True,
            )
            languages = set(str(getattr(completed, "stdout", "")).split())
            if int(completed.returncode) == 0 and "chi_tra" in languages:
                ocr_language = "ready"
        except OSError:
            pass

    report = {
        "data_dir": str(data_dir),
        "database": "present" if (data_dir / "cuv.sqlite3").is_file() else "missing",
        "source_pdfs": source_pdfs,
        "prerequisites": prerequisites,
        "ocr_language": ocr_language,
        "rag": _rag_configuration(environ),
    }
    required_ready = (
        source_pdfs == "ready"
        and ocr_language == "ready"
        and all(value == "ready" for value in prerequisites.values())
    )
    return (0 if required_ready else 2), report


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    runner=subprocess.run,
    which=shutil.which,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    stdin: TextIO | None = None,
    downloader=http_downloader,
) -> int:
    env = os.environ if environ is None else environ
    out = sys.stdout if stdout is None else stdout
    err = sys.stderr if stderr is None else stderr
    inp = sys.stdin if stdin is None else stdin
    args = build_parser().parse_args(argv)

    if args.command == "setup-rag":
        return _setup_rag_command(args, env, runner, downloader, inp, out)

    if args.command == "rag-check":
        code, report = _rag_check(env, runner)
        _write_report(report, args.json, out)
        return code

    runtime_commands = {"status", "verify", "passage", "rag-discover"}
    try:
        if args.command in runtime_commands:
            database, corpus_origin = resolve_runtime_database(
                getattr(args, "data_dir", None), env
            )
            data_dir = database.parent
        else:
            data_dir = resolve_data_dir(getattr(args, "data_dir", None), env)
            database, corpus_origin = data_dir / "cuv.sqlite3", "external"
    except ValueError as error:
        print(f"Cool Bible Tutor launcher failed: {error}", file=err)
        return 2
    if args.command == "status":
        code, report = _status(database, corpus_origin, env)
        _write_report(report, args.json, out)
        return code
    if args.command == "doctor":
        code, report = _doctor(data_dir, env, runner, which)
        _write_report(report, args.json, out)
        return code
    if args.command == "verify" and corpus_origin == "bundled":
        report = _frozen_corpus_verification()
        _write_report(report, args.json, out)
        return 0 if report["production_ready"] else 2

    try:
        command = build_delegated_command(
            args, data_dir, python_executable=Path(sys.executable)
        )
        child_env = dict(env)
        child_env["PYTHONUTF8"] = "1"
        completed = runner(command, env=child_env)
        return int(completed.returncode)
    except (OSError, ValueError) as error:
        print(f"Cool Bible Tutor launcher failed: {error}", file=err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
