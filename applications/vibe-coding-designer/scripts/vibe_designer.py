#!/usr/bin/env python3
"""Deterministic validation and status tools for Vibe Coding Designer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable


PLUGIN_ID = "vibe-coding-designer"
VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[1]
HEADING = re.compile(r"(?m)^##\s+(\d+)\.\s+(.+?)\s*$")


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    return {value for value in values if value in seen or seen.add(value)}


def validate_design_spec(path: Path) -> list[str]:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"design spec unreadable: {exc}"]
    headings = [(int(number), title) for number, title in HEADING.findall(text)]
    numbers = [number for number, _ in headings]
    errors: list[str] = []
    if numbers != list(range(1, 15)):
        errors.append("design spec must contain numbered sections 1 through 14 in order")
    for index, match in enumerate(HEADING.finditer(text)):
        end = HEADING.search(text, match.end())
        body = text[match.end() : end.start() if end else len(text)].strip()
        if not body:
            errors.append(f"empty design section: {match.group(1)}")
    return sorted(errors)


def _binding_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "binding_ref" and isinstance(item, str):
                refs.add(item)
            refs.update(_binding_refs(item))
    elif isinstance(value, list):
        for item in value:
            refs.update(_binding_refs(item))
    return refs


def validate_workflow(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["workflow must be an object"]
    errors: set[str] = set()
    required = {
        "workflow_id", "version", "description", "roles", "events", "guards",
        "states", "bindings", "schemas", "policies",
    }
    for key in sorted(required - set(payload)):
        errors.add(f"missing workflow field: {key}")
    for key in ("roles", "events", "guards"):
        declarations = payload.get(key)
        declaration_ids = (
            [item.get("id") for item in declarations]
            if isinstance(declarations, list)
            and all(isinstance(item, dict) for item in declarations)
            else []
        )
        if (
            not isinstance(declarations, list)
            or not all(isinstance(item, dict) for item in declarations)
            or not all(isinstance(item, str) and item for item in declaration_ids)
            or len(declaration_ids) != len(set(declaration_ids))
        ):
            errors.add(f"{key} must be an array of objects with unique non-empty ids")
    for key in ("schemas", "policies"):
        if not isinstance(payload.get(key), dict):
            errors.add(f"{key} must be an object")
    states = payload.get("states")
    bindings = payload.get("bindings")
    if not isinstance(states, list) or not all(isinstance(item, dict) for item in states):
        errors.add("states must be an array of objects")
        states = []
    if not isinstance(bindings, list) or not all(isinstance(item, dict) for item in bindings):
        errors.add("bindings must be an array of objects")
        bindings = []
    state_ids = [item.get("id") for item in states if isinstance(item.get("id"), str)]
    binding_ids = [item.get("id") for item in bindings if isinstance(item.get("id"), str)]
    for value in sorted(_duplicates(state_ids)):
        errors.add(f"duplicate state id: {value}")
    for value in sorted(_duplicates(binding_ids)):
        errors.add(f"duplicate binding id: {value}")
    declared_states = set(state_ids)
    declared_bindings = set(binding_ids)
    starts = [item for item in states if item.get("type") == "start"]
    ends = {item.get("id") for item in states if item.get("type") == "end"}
    if len(starts) != 1:
        errors.add("workflow must declare exactly one start state")
    if not ends:
        errors.add("workflow must declare at least one end state")
    graph: dict[str, set[str]] = {state: set() for state in state_ids}
    for state in states:
        state_id = state.get("id")
        if not isinstance(state_id, str):
            errors.add("state id must be non-empty text")
            continue
        transitions = state.get("on", {})
        if transitions is not None and not isinstance(transitions, dict):
            errors.add(f"state transitions must be an object: {state_id}")
            continue
        for target in (transitions or {}).values():
            if not isinstance(target, str):
                errors.add(f"state transition must be text: {state_id}")
            elif target not in declared_states:
                errors.add(f"unknown state transition: {state_id} -> {target}")
            else:
                graph[state_id].add(target)
    for reference in sorted(_binding_refs(states)):
        if reference not in declared_bindings:
            errors.add(f"unknown binding_ref: {reference}")
    if len(starts) == 1 and isinstance(starts[0].get("id"), str):
        reachable: set[str] = set()
        pending = [starts[0]["id"]]
        while pending:
            current = pending.pop()
            if current in reachable:
                continue
            reachable.add(current)
            pending.extend(graph.get(current, ()))
        for state_id in sorted(declared_states - reachable):
            errors.add(f"unreachable state: {state_id}")
        reverse: dict[str, set[str]] = {state: set() for state in declared_states}
        for source, targets in graph.items():
            for target in targets:
                reverse[target].add(source)
        can_terminate = set(ends)
        pending = list(ends)
        while pending:
            current = pending.pop()
            for predecessor in reverse.get(current, ()):
                if predecessor not in can_terminate:
                    can_terminate.add(predecessor)
                    pending.append(predecessor)
        for state_id in sorted(reachable - can_terminate):
            errors.add(f"state cannot reach an end: {state_id}")
    return sorted(errors)


def coverage_report(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("requirements"), list):
        raise ValueError("requirements must be explicit")
    requirements = payload["requirements"]
    if not all(isinstance(item, str) and item for item in requirements):
        raise ValueError("requirements must be explicit")
    unique = list(dict.fromkeys(requirements))
    tests = payload.get("tests", [])
    if not isinstance(tests, list):
        raise ValueError("tests must be a list")
    covered = {
        requirement
        for item in tests
        if isinstance(item, dict) and isinstance(item.get("requirements"), list)
        for requirement in item["requirements"]
        if requirement in unique
    }
    total = len(unique)
    percent = round((len(covered) / total * 100) if total else 100.0, 2)
    return {
        "covered": len(covered),
        "total": total,
        "percent": percent,
        "uncovered": [item for item in unique if item not in covered],
    }


def status() -> dict[str, Any]:
    skill_root = ROOT / "skills"
    skills = sorted(path.name for path in skill_root.iterdir() if (path / "SKILL.md").is_file())
    errors = []
    if len(skills) != 7:
        errors.append(f"expected 7 skills, found {len(skills)}")
    return {
        "plugin_id": PLUGIN_ID,
        "version": VERSION,
        "skill_count": len(skills),
        "skills": skills,
        "rag": "NOT APPLICABLE",
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _print(payload: Any, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True))
    elif isinstance(payload, list):
        print("PASS" if not payload else "\n".join(payload))
    else:
        print(payload)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--json", action="store_true")
    design = subparsers.add_parser("validate-design")
    design.add_argument("path", type=Path)
    design.add_argument("--json", action="store_true")
    workflow = subparsers.add_parser("validate-workflow")
    workflow.add_argument("path", type=Path)
    workflow.add_argument("--json", action="store_true")
    coverage = subparsers.add_parser("coverage")
    coverage.add_argument("path", type=Path)
    coverage.add_argument("--json", action="store_true")
    options = parser.parse_args(argv)
    try:
        if options.command == "status":
            result = status()
            _print(result, options.json)
            return 0 if result["status"] == "PASS" else 1
        if options.command == "validate-design":
            errors = validate_design_spec(options.path)
            _print({"status": "PASS" if not errors else "FAIL", "errors": errors} if options.json else errors, options.json)
            return 0 if not errors else 1
        payload = json.loads(options.path.read_text(encoding="utf-8"))
        if options.command == "validate-workflow":
            errors = validate_workflow(payload)
            _print({"status": "PASS" if not errors else "FAIL", "errors": errors} if options.json else errors, options.json)
            return 0 if not errors else 1
        result = coverage_report(payload)
        _print(result, options.json)
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        _print({"status": "FAIL", "errors": [str(exc)]}, True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
