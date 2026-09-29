#!/usr/bin/env python3
"""Stable Plugin Builder status and session-validation CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from plugin_builder_core.result import operation_document
from plugin_builder_core.inspection import inspect_design_package
from plugin_builder_core.session_contract import session_gate_state, validate_session


CAPABILITIES = {
    "session_contract": "STATICALLY VERIFIED",
    "candidate_build": "NOT VERIFIED",
    "package_build": "NOT VERIFIED",
    "codex_execution": "NOT VERIFIED",
    "chatgpt_work_execution": "NOT VERIFIED",
    "openclaw_execution": "NOT APPLICABLE",
}


def _emit(document: dict[str, object]) -> None:
    print(json.dumps(document, ensure_ascii=True, sort_keys=True, separators=(",", ":")))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="plugin_builder.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    status = subparsers.add_parser("status")
    status.add_argument("--json", action="store_true", required=True)
    validate = subparsers.add_parser("validate-session")
    validate.add_argument("session", type=Path)
    validate.add_argument("--json", action="store_true", required=True)
    inspect = subparsers.add_parser("inspect")
    inspect.add_argument("design_package", type=Path)
    inspect.add_argument("--workspace", type=Path, required=True)
    inspect.add_argument("--operation", choices=("create", "update"), required=True)
    inspect.add_argument("--baseline", type=Path)
    inspect.add_argument("--json", action="store_true", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.command == "status":
        _emit(operation_document("status", "PASS", [], capabilities=CAPABILITIES))
        return 0

    if arguments.command == "inspect":
        try:
            outcome = inspect_design_package(
                arguments.design_package,
                arguments.workspace,
                arguments.operation,
                arguments.baseline,
            )
        except OSError:
            _emit(operation_document("inspect", "FAIL", ["inspection.local_io_failure"], stage="F1"))
            return 4
        _emit(
            operation_document(
                "inspect",
                outcome.status,
                list(outcome.errors),
                stage=outcome.stage,
                inspection_sha256=outcome.inspection_sha256,
                session_sha256=outcome.session_sha256,
            )
        )
        return 0 if outcome.status == "PASS" else 2 if outcome.status == "BLOCKED" else 3

    try:
        payload = json.loads(arguments.session.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors = ["session_input.invalid_json"]
        _emit(operation_document("validate-session", "FAIL", errors, gate="INVALID"))
        return 3

    errors = validate_session(payload)
    status = "PASS" if not errors else "FAIL"
    _emit(
        operation_document(
            "validate-session",
            status,
            errors,
            gate=session_gate_state(payload),
        )
    )
    return 0 if not errors else 3


if __name__ == "__main__":
    raise SystemExit(main())
