#!/usr/bin/env python3
"""Stable Plugin Builder status and session-validation CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from plugin_builder_core.result import operation_document
from plugin_builder_core.inspection import inspect_design_package
from plugin_builder_core.approvals import approve_w1
from plugin_builder_core.implementation_plan import (
    canonical_bytes,
    compile_plan,
    write_bytes_transactionally,
)
from plugin_builder_core.candidate import build_candidate
from plugin_builder_core.update import resolve_update_member
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
    plan = subparsers.add_parser("plan")
    plan.add_argument("--session", type=Path, required=True)
    plan.add_argument("--proposal", type=Path, required=True)
    plan.add_argument("--json", action="store_true", required=True)
    approve = subparsers.add_parser("approve-w1")
    approve.add_argument("--session", type=Path, required=True)
    approve.add_argument("--confirmed-by", required=True)
    approve.add_argument("--evidence", required=True)
    approve.add_argument("--json", action="store_true", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--session", type=Path, required=True)
    build.add_argument("--json", action="store_true", required=True)
    resolve = subparsers.add_parser("resolve-update")
    resolve.add_argument("--session", type=Path, required=True)
    resolve.add_argument("--member", required=True)
    resolve.add_argument("--decision", choices=("keep", "replace", "remove"), required=True)
    resolve.add_argument("--evidence", required=True)
    resolve.add_argument("--json", action="store_true", required=True)
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

    if arguments.command == "plan":
        try:
            session = json.loads(arguments.session.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            _emit(operation_document("plan", "FAIL", ["session_input.invalid_json"], stage="F1"))
            return 3
        if not isinstance(session, dict) or session.get("schema_version") != 2 or not isinstance(session.get("inspection"), dict):
            _emit(operation_document("plan", "FAIL", ["session.v2_inspection_required"], stage="F1"))
            return 3
        root = arguments.session.parent
        inspection_path = root / session["inspection"].get("path", "")
        output = root / "implementation-plan.json"
        outcome = compile_plan(inspection_path, arguments.proposal, output)
        if outcome.status != "FAIL":
            session["plan"] = {
                "path": "implementation-plan.json",
                "sha256": outcome.plan_sha256,
                "tools_sha256": outcome.tools_sha256,
            }
            for key in ("w1", "candidate", "verification", "w2", "package"):
                session[key] = None
            session["stage"] = "W1"
            write_bytes_transactionally(arguments.session, canonical_bytes(session))
        errors = [*outcome.errors, *outcome.blockers]
        _emit(operation_document(
            "plan", outcome.status, errors,
            stage="W1" if outcome.status != "FAIL" else "F1",
            plan_sha256=outcome.plan_sha256,
            tools_sha256=outcome.tools_sha256,
        ))
        return 0 if outcome.status == "PASS" else 2 if outcome.status == "BLOCKED" else 3

    if arguments.command == "approve-w1":
        status, errors, data = approve_w1(arguments.session, arguments.confirmed_by, arguments.evidence)
        _emit(operation_document("approve-w1", status, errors, stage="S3" if status == "PASS" else "W1", **data))
        return 0 if status == "PASS" else 2 if status == "BLOCKED" else 3

    if arguments.command == "build":
        outcome = build_candidate(arguments.session)
        _emit(operation_document(
            "build", outcome.status, list(outcome.errors),
            stage="S4" if outcome.status == "PASS" else "S3",
            candidate_sha256=outcome.candidate_sha256,
            manifest_sha256=outcome.manifest_sha256,
        ))
        return 0 if outcome.status == "PASS" else 2 if outcome.status == "BLOCKED" else 3

    if arguments.command == "resolve-update":
        outcome = resolve_update_member(
            arguments.session, arguments.member, arguments.decision, arguments.evidence
        )
        _emit(operation_document(
            "resolve-update", outcome.status, list(outcome.errors),
            member=outcome.member, decision=outcome.decision,
        ))
        return 0 if outcome.status == "PASS" else 3

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
