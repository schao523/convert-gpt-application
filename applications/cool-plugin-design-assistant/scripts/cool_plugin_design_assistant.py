"""Deterministic validators for Cool Plugin Design Assistant artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, deque
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any


FORBIDDEN_ARCHITECTURE_KEYS = {
    "skill",
    "skill_id",
    "skill_name",
    "skill_assignment",
    "skill_architecture",
    "runtime_adapter",
    "storage_path",
    "rag_index",
    "reference_binding",
}

WORKFLOW_FIELDS = {
    "workflow_id",
    "mission_outcome",
    "actors",
    "inputs",
    "states",
    "start",
    "terminal_states",
    "hitl_checkpoints",
    "completion_criteria",
}

MODULE_FIELDS = {
    "module_id",
    "name",
    "classification",
    "purpose",
    "mission_outcome",
    "trigger",
    "inputs",
    "preconditions",
    "procedure",
    "outputs",
    "user_interaction_protocol",
    "transitions",
    "stop_wait_completion",
    "error_recovery",
    "safety_boundaries",
    "reference_material_requirements",
    "acceptance_criteria",
}

MODULE_TYPES = {"primary-workflow", "intent-triggered", "cross-cutting"}

SKILL_NAMES = [
    "guiding-ai-application-design-sessions",
    "creating-design-statements",
    "designing-application-workflows-and-instruction-modules",
    "evaluating-reference-materials",
    "creating-application-plugin-design-specifications",
    "reviewing-application-implementations",
    "planning-application-tests-and-improvements",
]

HANDOFF_FIELDS = {
    "approved_design_statement",
    "approved_specification",
    "workflow_definitions_and_instruction_modules",
    "reference_material_inventory_evaluation_and_usage_map",
    "application_invariants_and_hitl_checkpoints",
    "deterministic_operation_candidates",
    "tool_data_runtime_and_service_requirements",
    "acceptance_criteria_and_representative_scenarios",
    "rights_and_redistribution_decisions",
    "unresolved_owner_decisions",
    "explicit_exclusions",
    "approval",
}

DESIGN_STATEMENT_HEADINGS = {
    "audience",
    "context",
    "problem",
    "application role or method",
    "desired outcome",
    "style and tone",
}

SPECIFICATION_DECISION_HEADINGS = {
    "requirements",
    "confirmed decisions",
    "assumptions",
    "recommendations",
    "unresolved questions",
}

SPECIFICATION_SECTION_TITLES = (
    "Application identity and purpose",
    "Design Statement",
    "Intended users and contexts",
    "Application mission and success outcomes",
    "Scope and exclusions",
    "Primary mission workflow",
    "Conditional and alternative workflows",
    "Instruction Module contracts",
    "User-intent routing requirements",
    "User-interaction protocols",
    "Human-in-the-Loop checkpoints",
    "Inputs, outputs, and state requirements",
    "Reference Material requirements and behavior-level usage map",
    "Deterministic-operation requirements",
    "Tool, data, runtime, and external-service requirements",
    "Safety, privacy, and policy boundaries",
    "Failure, uncertainty, and recovery behavior",
    "Acceptance criteria",
    "Representative application tests",
    "Assumptions, decisions, recommendations, and unresolved questions",
    "Application Workbench handoff contract",
)

WORKFLOW_KINDS = {"start", "action", "wait", "failure", "end"}


def _sorted(errors: list[str]) -> list[str]:
    return sorted(set(errors))


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_string_array(value: Any, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(_is_nonempty_string(item) for item in value)
    )


def _validate_inputs(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{label} inputs must be an object")
        return
    if not _is_string_array(value.get("required")):
        errors.append(f"{label} inputs required must be a non-empty string array")
    if not _is_string_array(value.get("optional"), allow_empty=True):
        errors.append(f"{label} inputs optional must be a string array")


def _valid_transitions(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return all(
        _is_nonempty_string(target)
        or _is_string_array(target)
        for target in value.values()
    )


def _targets(transitions: Any) -> list[str]:
    if not isinstance(transitions, dict):
        return []
    targets: list[str] = []
    for value in transitions.values():
        if isinstance(value, str):
            targets.append(value)
        elif isinstance(value, list):
            targets.extend(item for item in value if isinstance(item, str))
    return targets


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            if isinstance(key, str) and key.casefold() in FORBIDDEN_ARCHITECTURE_KEYS:
                return True
            if _contains_forbidden_key(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def validate_workflow(payload: Any) -> list[str]:
    """Return sorted deterministic errors for a canonical workflow object."""

    if not isinstance(payload, dict):
        return ["workflow must be an object"]

    errors: list[str] = []
    for field in WORKFLOW_FIELDS:
        if field not in payload:
            errors.append(f"workflow missing field: {field}")

    for field in ("workflow_id", "mission_outcome", "start"):
        if not _is_nonempty_string(payload.get(field)):
            errors.append(f"workflow field must be a non-empty string: {field}")
    for field in ("actors", "terminal_states", "hitl_checkpoints", "completion_criteria"):
        if not _is_string_array(payload.get(field)):
            errors.append(f"workflow field must be a non-empty string array: {field}")
    _validate_inputs(payload.get("inputs"), "workflow", errors)

    states = payload.get("states")
    if not isinstance(states, list):
        errors.append("workflow states must be an array")
        return _sorted(errors)

    records = [state for state in states if isinstance(state, dict)]
    if len(records) != len(states):
        errors.append("workflow state must be an object")

    ids = [state.get("id") for state in records if _is_nonempty_string(state.get("id"))]
    for state_id, count in Counter(ids).items():
        if count > 1:
            errors.append(f"duplicate state id: {state_id}")
    known = set(ids)

    starts = [state for state in records if state.get("kind") == "start"]
    ends = [state for state in records if state.get("kind") == "end"]
    failure_ids = {
        state.get("id")
        for state in records
        if state.get("kind") == "failure" and _is_nonempty_string(state.get("id"))
    }
    if len(starts) != 1:
        errors.append("exactly one start state required")
    if not ends:
        errors.append("terminal state required")

    failure_path = False
    approval_wait = False
    graph: dict[str, set[str]] = {state_id: set() for state_id in known}

    for index, state in enumerate(records):
        state_id = state.get("id")
        label = state_id if _is_nonempty_string(state_id) else f"index-{index}"
        for field in ("id", "kind", "interaction_protocol", "wait", "transitions"):
            if field not in state:
                errors.append(f"state {label} missing field: {field}")
        if not _is_nonempty_string(state.get("id")):
            errors.append(f"state {label} id must be a non-empty string")
        if state.get("kind") not in WORKFLOW_KINDS:
            errors.append(f"state {label} has invalid kind")
        if not _is_nonempty_string(state.get("interaction_protocol")):
            errors.append(f"state {label} missing interaction protocol")
        if not isinstance(state.get("wait"), bool):
            errors.append(f"state {label} wait must be a boolean")
        transitions = state.get("transitions")
        if not isinstance(transitions, dict):
            errors.append(f"state {label} transitions must be an object")
            continue
        if not _valid_transitions(transitions):
            errors.append(f"state {label} transitions contain an invalid target")
            continue
        if "failure" in transitions:
            failure_path = failure_path or any(
                target in failure_ids
                for target in _targets({"failure": transitions["failure"]})
            )
        if state.get("kind") == "wait" and state.get("wait") is True:
            approval_wait = True
        for target in _targets(transitions):
            if target not in known:
                errors.append(f"unknown state transition: {label} -> {target}")
            elif state_id in graph:
                graph[state_id].add(target)

    if not failure_path:
        errors.append("failure path required")
    if not approval_wait:
        errors.append("approval wait state required")

    start_id = starts[0].get("id") if len(starts) == 1 else None
    if isinstance(start_id, str) and payload.get("start") != start_id:
        errors.append("workflow start does not match start state")

    if isinstance(start_id, str) and start_id in graph:
        reachable: set[str] = set()
        queue = deque([start_id])
        while queue:
            current = queue.popleft()
            if current in reachable:
                continue
            reachable.add(current)
            queue.extend(sorted(graph.get(current, set()) - reachable))
        for state_id in known - reachable:
            errors.append(f"unreachable state: {state_id}")

    terminal_ids = {
        state["id"]
        for state in ends
        if isinstance(state.get("id"), str) and state["id"] in known
    }
    declared_terminals = payload.get("terminal_states")
    if _is_string_array(declared_terminals) and set(declared_terminals) != terminal_ids:
        errors.append("workflow terminal_states must match end states")
    checkpoints = payload.get("hitl_checkpoints")
    if _is_string_array(checkpoints):
        wait_ids = {
            state.get("id")
            for state in records
            if _is_nonempty_string(state.get("id")) and state.get("wait") is True
        }
        for checkpoint in checkpoints:
            if checkpoint not in wait_ids:
                errors.append(
                    f"workflow HITL checkpoint must reference a wait state: {checkpoint}"
                )
    if terminal_ids:
        reverse: dict[str, set[str]] = {state_id: set() for state_id in known}
        for source, targets in graph.items():
            for target in targets:
                reverse[target].add(source)
        can_finish = set(terminal_ids)
        queue = deque(sorted(terminal_ids))
        while queue:
            current = queue.popleft()
            for source in sorted(reverse.get(current, set())):
                if source not in can_finish:
                    can_finish.add(source)
                    queue.append(source)
        for state_id in known - can_finish:
            errors.append(f"state cannot reach terminal: {state_id}")

    return _sorted(errors)


def validate_modules(payload: Any) -> list[str]:
    """Return sorted deterministic errors for canonical module contracts."""

    if not isinstance(payload, dict):
        return ["modules must be an object"]

    errors: list[str] = []
    if _contains_forbidden_key(payload):
        errors.append("implementation architecture forbidden")

    modules = payload.get("modules")
    if not isinstance(modules, list):
        errors.append("modules must be an array")
        return _sorted(errors)

    records = [module for module in modules if isinstance(module, dict)]
    if len(records) != len(modules):
        errors.append("module must be an object")

    ids = [
        module.get("module_id")
        for module in records
        if _is_nonempty_string(module.get("module_id"))
    ]
    for module_id, count in Counter(ids).items():
        if count > 1:
            errors.append(f"duplicate module id: {module_id}")
    known = set(ids)

    for index, module in enumerate(records):
        module_id = module.get("module_id")
        label = module_id if _is_nonempty_string(module_id) else f"index-{index}"
        for field in MODULE_FIELDS:
            if field not in module:
                errors.append(f"module {label} missing field: {field}")
        for field in (
            "module_id",
            "name",
            "purpose",
            "mission_outcome",
            "trigger",
            "user_interaction_protocol",
        ):
            if not _is_nonempty_string(module.get(field)):
                errors.append(f"module {label} field must be a non-empty string: {field}")
        classification = module.get("classification")
        if classification not in MODULE_TYPES:
            errors.append(f"module {label} has invalid classification")
        protocol = module.get("user_interaction_protocol")
        if not isinstance(protocol, str) or not protocol:
            errors.append(f"module {label} missing user-interaction protocol")
        _validate_inputs(module.get("inputs"), f"module {label}", errors)
        for field in (
            "preconditions",
            "procedure",
            "outputs",
            "safety_boundaries",
            "acceptance_criteria",
        ):
            if not _is_string_array(module.get(field)):
                errors.append(
                    f"module {label} field must be a non-empty string array: {field}"
                )
        if not _is_string_array(
            module.get("reference_material_requirements"), allow_empty=True
        ):
            errors.append(
                f"module {label} field must be a string array: reference_material_requirements"
            )
        for field, keys in (
            ("stop_wait_completion", ("stop", "wait", "completion")),
            ("error_recovery", ("error", "recovery")),
        ):
            value = module.get(field)
            if not isinstance(value, dict) or not all(
                _is_nonempty_string(value.get(key)) for key in keys
            ):
                key_phrase = (
                    f"{keys[0]} and {keys[1]}"
                    if len(keys) == 2
                    else f"{', '.join(keys[:-1])}, and {keys[-1]}"
                )
                errors.append(
                    f"module {label} {field} requires non-empty {key_phrase}"
                )
        transitions = module.get("transitions")
        if not isinstance(transitions, dict):
            errors.append(f"module {label} transitions must be an object")
            continue
        if not transitions:
            errors.append(f"module {label} transitions must be a non-empty object")
            continue
        if not _valid_transitions(transitions):
            errors.append(f"module {label} transitions contain an invalid target")
            continue
        for target in _targets(transitions):
            if target not in known:
                errors.append(f"unknown module transition: {label} -> {target}")

    return _sorted(errors)


def _read_utf8(path: Path, label: str, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        errors.append(f"{label} must be a readable UTF-8 file")
        return None


def validate_design_artifacts(statement_path: str | Path, specification_path: str | Path) -> list[str]:
    """Validate distinct Design Statement and 21-section specification files."""

    errors: list[str] = []
    statement = Path(statement_path)
    specification = Path(specification_path)
    try:
        if statement.resolve() == specification.resolve():
            errors.append("design statement and specification must be distinct files")
    except OSError:
        pass

    statement_text = _read_utf8(statement, "design statement", errors)
    specification_text = _read_utf8(specification, "design specification", errors)

    if statement_text is not None:
        headings = {
            heading.strip().casefold()
            for heading in re.findall(r"(?m)^##\s+(.+?)\s*$", statement_text)
        }
        for heading in DESIGN_STATEMENT_HEADINGS - headings:
            errors.append(f"design statement missing field: {heading}")
        statement_sections = list(
            re.finditer(r"(?m)^##\s+(.+?)\s*$", statement_text)
        )
        for index, match in enumerate(statement_sections):
            heading = match.group(1).strip().casefold()
            if heading not in DESIGN_STATEMENT_HEADINGS:
                continue
            end = (
                statement_sections[index + 1].start()
                if index + 1 < len(statement_sections)
                else len(statement_text)
            )
            if not statement_text[match.end() : end].strip():
                errors.append(f"design statement field must be non-empty: {heading}")
        if not re.search(r"(?im)^state:\s*(draft|approved)\s*$", statement_text):
            errors.append("design statement state required")

    if specification_text is not None:
        section_pattern = re.compile(
            r"(?m)^(\d+)\.\s+\*\*(.+?)\*\*\s*(?:(?:—|-|:)\s*(.*))?$"
        )
        matches = list(section_pattern.finditer(specification_text))
        numbers: list[int] = []
        nonempty = True
        for index, match in enumerate(matches):
            numbers.append(int(match.group(1)))
            number = int(match.group(1))
            if 1 <= number <= len(SPECIFICATION_SECTION_TITLES):
                expected = SPECIFICATION_SECTION_TITLES[number - 1]
                if match.group(2).strip() != expected:
                    errors.append(
                        f"design specification section {number} must be: {expected}"
                    )
            inline = (match.group(3) or "").strip()
            body_end = matches[index + 1].start() if index + 1 < len(matches) else len(
                specification_text
            )
            following = specification_text[match.end() : body_end]
            following = re.split(r"(?m)^##\s+", following, maxsplit=1)[0].strip()
            if not inline and not following:
                nonempty = False
        if numbers != list(range(1, 22)) or not nonempty:
            errors.append("design specification requires 21 numbered non-empty sections")
        headings = {
            heading.strip().casefold()
            for heading in re.findall(r"(?m)^##\s+(.+?)\s*$", specification_text)
        }
        for heading in SPECIFICATION_DECISION_HEADINGS - headings:
            errors.append(f"design specification missing decision heading: {heading}")
        if not re.search(r"(?im)^state:\s*(draft|approved)\s*$", specification_text):
            errors.append("design specification approval state required")

    return _sorted(errors)


def validate_handoff(payload: Any) -> list[str]:
    """Validate an approval-gated, architecture-neutral Workbench handoff."""

    if not isinstance(payload, dict):
        return ["handoff must be an object"]

    errors: list[str] = []
    for field in HANDOFF_FIELDS:
        if field not in payload:
            errors.append(f"handoff missing field: {field}")

    approval = payload.get("approval")
    if not isinstance(approval, dict) or approval.get("state") != "approved":
        errors.append("handoff requires explicit approval")
    if isinstance(approval, dict):
        for field in ("specification_version", "confirmed_by"):
            if not _is_nonempty_string(approval.get(field)):
                errors.append(f"handoff approval requires non-empty {field}")

    for artifact_field in ("approved_design_statement", "approved_specification"):
        artifact = payload.get(artifact_field)
        if not isinstance(artifact, dict) or artifact.get("state") != "approved":
            errors.append(f"handoff requires approved artifact: {artifact_field}")
            continue
        for field in ("id", "version"):
            if not _is_nonempty_string(artifact.get(field)):
                errors.append(
                    f"approved artifact requires non-empty {field}: {artifact_field}"
                )

    for field in (
        "workflow_definitions_and_instruction_modules",
        "application_invariants_and_hitl_checkpoints",
        "acceptance_criteria_and_representative_scenarios",
    ):
        if not _is_string_array(payload.get(field)):
            errors.append(f"handoff field must be a non-empty string array: {field}")
    for field in ("deterministic_operation_candidates", "explicit_exclusions"):
        if not _is_string_array(payload.get(field), allow_empty=True):
            errors.append(f"handoff field must be a string array: {field}")

    reference_map = payload.get("reference_material_inventory_evaluation_and_usage_map")
    if not isinstance(reference_map, list) or not all(
        isinstance(item, dict) and bool(item) for item in reference_map
    ):
        errors.append(
            "handoff reference material inventory, evaluation, and usage map must be an object array"
        )
    requirements = payload.get("tool_data_runtime_and_service_requirements")
    if not isinstance(requirements, dict) or not requirements:
        errors.append("handoff tool, data, runtime, and service requirements must be a non-empty object")
    rights = payload.get("rights_and_redistribution_decisions")
    if not isinstance(rights, dict) or not rights:
        errors.append("handoff rights and redistribution decisions must be a non-empty object")

    unresolved = payload.get("unresolved_owner_decisions")
    if not isinstance(unresolved, list):
        errors.append("unresolved owner decisions must be an array")
    else:
        for item in unresolved:
            if not isinstance(item, dict):
                errors.append("unresolved owner decision must be an object")
                continue
            decision_id = item.get("decision_id")
            if not _is_nonempty_string(decision_id):
                errors.append("unresolved owner decision requires non-empty decision_id")
                decision_id = "unidentified"
            for field in ("summary", "owner"):
                if not _is_nonempty_string(item.get(field)):
                    errors.append(
                        f"unresolved owner decision {decision_id} requires non-empty {field}"
                    )
            if not isinstance(item.get("blocking"), bool):
                errors.append(
                    f"unresolved owner decision {decision_id} requires boolean blocking"
                )
            elif item["blocking"]:
                errors.append(f"blocking owner decision: {decision_id}")

    if _contains_forbidden_key(payload):
        errors.append("implementation architecture forbidden")

    return _sorted(errors)


def handoff_gate_state(payload: Any) -> str:
    """Return the documented Workbench handoff state for a validated payload."""

    if validate_handoff(payload):
        return "HANDOFF BLOCKED"
    if payload.get("unresolved_owner_decisions"):
        return "APPROVED WITH NONBLOCKING DECISIONS"
    return "READY FOR WORKBENCH"


def coverage_report(payload: Any) -> dict[str, Any]:
    """Return coverage only when requirements and mappings are explicit."""

    unavailable = {
        "status": "NOT VERIFIED",
        "covered": 0,
        "total": 0,
        "percentage": None,
        "uncovered_ids": [],
    }
    if not isinstance(payload, dict):
        return unavailable

    requirements = payload.get("requirements")
    mappings = payload.get("mappings")
    if (
        not isinstance(requirements, list)
        or not requirements
        or not all(isinstance(item, str) and item for item in requirements)
        or not isinstance(mappings, list)
        or not mappings
    ):
        return unavailable

    ordered_requirements = list(dict.fromkeys(requirements))
    mapped: set[str] = set()
    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        requirement_id = mapping.get("requirement_id")
        test_ids = mapping.get("test_ids")
        if (
            requirement_id in ordered_requirements
            and isinstance(test_ids, list)
            and any(isinstance(test_id, str) and test_id for test_id in test_ids)
        ):
            mapped.add(requirement_id)

    covered = len(mapped)
    total = len(ordered_requirements)
    uncovered = sorted(set(ordered_requirements) - mapped)
    return {
        "status": "PASS",
        "covered": covered,
        "total": total,
        "percentage": round(covered * 100.0 / total, 2),
        "uncovered_ids": uncovered,
    }


def status() -> dict[str, Any]:
    """Return static product capability status before runtime verification."""

    return {
        "status": "PASS",
        "plugin_id": "cool-plugin-design-assistant",
        "version": "1.0.0",
        "skills": list(SKILL_NAMES),
        "rag": "NOT APPLICABLE",
        "clawhub": "NOT APPLICABLE",
        "runtime_evidence": {
            "codex": "NOT VERIFIED",
            "openclaw": "NOT VERIFIED",
        },
    }


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _document(operation: str, result_status: str, errors: list[str], **data: Any) -> dict[str, Any]:
    return {
        "status": result_status,
        "operation": operation,
        "errors": _sorted(errors),
        **data,
    }


def _print_document(document: dict[str, Any]) -> None:
    print(json.dumps(document, ensure_ascii=True, sort_keys=True))


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="cool_plugin_design_assistant.py")
    commands = parser.add_subparsers(dest="command", required=True)

    def add_json(command: argparse.ArgumentParser) -> None:
        command.add_argument("--json", action="store_true", help="Emit JSON output")

    add_json(commands.add_parser("status"))
    design = commands.add_parser("validate-design")
    design.add_argument("design_statement")
    design.add_argument("design_specification")
    add_json(design)
    for name in ("validate-workflow", "validate-modules", "validate-handoff", "coverage"):
        command = commands.add_parser(name)
        command.add_argument("artifact")
        add_json(command)
    audit = commands.add_parser("distribution-audit")
    audit.add_argument("stage", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    add_json(audit)
    return parser


def _run_distribution_audit(stage: str | Path) -> tuple[str, list[str]]:
    script = Path(__file__).with_name("distribution_audit.py")
    if not script.is_file():
        return "BLOCKED", ["distribution audit unavailable"]
    spec = importlib.util.spec_from_file_location("distribution_audit", script)
    if spec is None or spec.loader is None:
        return "BLOCKED", ["distribution audit unavailable"]
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = Path(stage)
    if (root / "conversion.json").is_file() and hasattr(module, "audit_public_source"):
        errors = module.audit_public_source(root)
    else:
        errors = module.audit_distribution(root, None)
    return ("PASS", []) if not errors else ("FAIL", list(errors))


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
    except ValueError as exc:
        _print_document(_document("invocation", "BLOCKED", [str(exc)]))
        return 2

    operation = args.command
    try:
        if operation == "status":
            data = status()
            result_status = data.pop("status")
            document = _document(operation, result_status, [], **data)
        elif operation == "validate-design":
            errors = validate_design_artifacts(
                args.design_statement, args.design_specification
            )
            document = _document(operation, "PASS" if not errors else "FAIL", errors)
        elif operation == "validate-workflow":
            errors = validate_workflow(_load_json(args.artifact))
            document = _document(operation, "PASS" if not errors else "FAIL", errors)
        elif operation == "validate-modules":
            errors = validate_modules(_load_json(args.artifact))
            document = _document(operation, "PASS" if not errors else "FAIL", errors)
        elif operation == "validate-handoff":
            payload = _load_json(args.artifact)
            errors = validate_handoff(payload)
            document = _document(
                operation,
                "PASS" if not errors else "FAIL",
                errors,
                gate_state=handoff_gate_state(payload),
            )
        elif operation == "coverage":
            report = coverage_report(_load_json(args.artifact))
            report_status = report.pop("status")
            result_status = "PASS" if report_status == "PASS" else "BLOCKED"
            errors = [] if result_status == "PASS" else ["coverage evidence incomplete"]
            document = _document(
                operation,
                result_status,
                errors,
                evidence_status=report_status,
                **report,
            )
        elif operation == "distribution-audit":
            result_status, errors = _run_distribution_audit(args.stage)
            document = _document(operation, result_status, errors)
        else:
            document = _document(operation, "BLOCKED", ["unsupported operation"])
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        document = _document(operation, "BLOCKED", [str(exc)])

    _print_document(document)
    if document["status"] == "PASS":
        return 0
    if document["status"] == "BLOCKED":
        return 2
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
