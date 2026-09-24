# Behavioral Workflow Blueprint contract

Define behavior precisely enough for specification and acceptance testing
without choosing an implementation architecture.

| Field | Required content |
| --- | --- |
| `workflow_id` | Stable behavior-level identifier. |
| `mission_outcome` | Observable result and success boundary. |
| `actors` | User roles and external actors, with responsibilities. |
| `inputs` | Required and optional inputs, including provenance expectations. |
| `stages` | Ordered or stateful stages with purpose and produced state. |
| `conditional_paths` | Conditions, alternatives, and re-entry points. |
| `transitions` | Source, trigger/guard, destination, and preserved state. |
| `terminal_states` | Successful, stopped, declined, and unrecoverable endings. |
| `failure_and_recovery_paths` | Failure signal, user-visible response, retained state, retry or fallback. |
| `hitl_checkpoints` | Decisions requiring human input or explicit confirmation. |
| `completion_criteria` | Evidence that the mission outcome is complete. |

## Design method

Start with the shortest primary path that completes the mission. Add a
conditional path only for a material alternative, ambiguity, safety boundary,
or recoverable failure. Every transition must name its condition and state
effect; do not rely on “continue as appropriate.” Every wait is a state, not a
hidden pause. Define how pause, resume, stop, decline, and retry affect state.

Connect each stage to logical Instruction Modules and a user-interaction
protocol. Do not assign modules to concrete Skills, files, runtime events, or
adapters. Present the blueprint as `draft` until the user explicitly approves
the identified version.
