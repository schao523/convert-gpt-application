"""Deterministic validators for Cool Plugin Design Assistant artifacts."""

from __future__ import annotations

from collections import Counter, deque
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


def _sorted(errors: list[str]) -> list[str]:
    return sorted(set(errors))


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

    states = payload.get("states")
    if not isinstance(states, list):
        errors.append("workflow states must be an array")
        return _sorted(errors)

    records = [state for state in states if isinstance(state, dict)]
    if len(records) != len(states):
        errors.append("workflow state must be an object")

    ids = [state.get("id") for state in records if isinstance(state.get("id"), str)]
    for state_id, count in Counter(ids).items():
        if count > 1:
            errors.append(f"duplicate state id: {state_id}")
    known = set(ids)

    starts = [state for state in records if state.get("kind") == "start"]
    ends = [state for state in records if state.get("kind") == "end"]
    if len(starts) != 1:
        errors.append("exactly one start state required")
    if not ends:
        errors.append("terminal state required")

    failure_path = False
    approval_wait = False
    graph: dict[str, set[str]] = {state_id: set() for state_id in known}

    for index, state in enumerate(records):
        state_id = state.get("id")
        label = state_id if isinstance(state_id, str) else f"index-{index}"
        for field in ("id", "kind", "interaction_protocol", "wait", "transitions"):
            if field not in state:
                errors.append(f"state {label} missing field: {field}")
        if not isinstance(state.get("interaction_protocol"), str) or not state.get(
            "interaction_protocol"
        ):
            errors.append(f"state {label} missing interaction protocol")
        transitions = state.get("transitions")
        if not isinstance(transitions, dict):
            errors.append(f"state {label} transitions must be an object")
            continue
        if "failure" in transitions:
            failure_path = True
        if state.get("kind") == "wait" and state.get("wait") is True:
            approval_wait = True
        for target in _targets(transitions):
            if target not in known:
                errors.append(f"unknown state transition: {label} -> {target}")
            elif isinstance(state_id, str):
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

    if not isinstance(payload.get("completion_criteria"), list) or not payload.get(
        "completion_criteria"
    ):
        errors.append("completion criteria required")

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
        if isinstance(module.get("module_id"), str)
    ]
    for module_id, count in Counter(ids).items():
        if count > 1:
            errors.append(f"duplicate module id: {module_id}")
    known = set(ids)

    for index, module in enumerate(records):
        module_id = module.get("module_id")
        label = module_id if isinstance(module_id, str) else f"index-{index}"
        for field in MODULE_FIELDS:
            if field not in module:
                errors.append(f"module {label} missing field: {field}")
        classification = module.get("classification")
        if classification not in MODULE_TYPES:
            errors.append(f"module {label} has invalid classification")
        protocol = module.get("user_interaction_protocol")
        if not isinstance(protocol, str) or not protocol:
            errors.append(f"module {label} missing user-interaction protocol")
        transitions = module.get("transitions")
        if not isinstance(transitions, dict):
            errors.append(f"module {label} transitions must be an object")
            continue
        for target in _targets(transitions):
            if target not in known:
                errors.append(f"unknown module transition: {label} -> {target}")

    return _sorted(errors)
