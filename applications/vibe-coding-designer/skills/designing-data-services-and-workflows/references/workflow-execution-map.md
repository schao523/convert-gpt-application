# Workflow execution map

The canonical JSON object contains exactly these shapes:

- `workflow_id`, `version`, and `description`;
- `roles`, `events`, and `guards` arrays of objects, each with a unique,
  non-empty string `id`;
- `states` with unique `id`, a `type` of `start`, `task`, `saga`, or `end`, actions, and `on` transitions;
- `bindings` with unique service identifiers and kinds;
- `schemas` as an object keyed by schema identifier;
- `policies` as an object keyed by privacy, rate, security, or reliability
  policy identifier.

Each state's `on` value is an object mapping event IDs to target state IDs.
Model alternatives as separate transitions. In particular, never describe a
recoverable path inside a terminal state: route lenient recovery back to a task
state and strict failure to an end state.

Every transition target must name a declared state. Every `binding_ref`, including compensation and saga steps, must name a declared binding. The graph must have one start state, reachable terminal states, and no reachable path that cannot eventually terminate unless the requirements explicitly define a long-running loop.

Represent retries with explicit maximum attempts and backoff. Represent compensating actions in reverse dependency order. Include a manual-intervention terminal outcome when automated compensation can fail.

Before returning a workflow, run `python -B scripts/vibe_designer.py
validate-workflow <workflow.json> --json` when the packaged script is
available. Otherwise perform the same checks explicitly: declaration shapes,
unique IDs, transition targets, binding references, exactly one start,
reachable ends, and termination reachability. Do not call a workflow canonical
or validated when any check is unperformed or failing.
