# Behavioral Workflow Blueprint contract

Define behavior precisely enough for specification and acceptance testing
without choosing an implementation architecture.

| Field | Required content |
| --- | --- |
| `workflow_id` | Stable behavior-level identifier. |
| `mission_outcome` | Observable result and success boundary. |
| `actors` | Non-empty string array of user roles and external actors. |
| `inputs` | Object with a non-empty string array named `required` and a string array named `optional`. |
| `states` | Array of state objects using the canonical state shape below. |
| `start` | The ID of the single state whose `kind` is `start`. |
| `terminal_states` | IDs of all `end` states, including successful, stopped, declined, and unrecoverable endings. |
| `successful_terminal_states` | Non-empty subset of `terminal_states` that proves the mission outcome completed. |
| `hitl_checkpoints` | Wait-state IDs that every path to a successful terminal must traverse. |
| `completion_criteria` | Non-empty string array describing evidence that the mission outcome is complete. |

Each canonical state object contains `id`, `kind`, `interaction_protocol`,
`wait`, and `transitions`. `kind` is one of `start`, `action`, `wait`,
`failure`, or `end`. `transitions` is an object whose keys name triggers or
guards and whose values are destination state IDs. Conditional paths,
re-entry, failure, recovery, pause, stop, decline, and retry are represented by
these named transitions rather than by a second undocumented structure.
Every recoverable failure path uses a literal `failure` transition whose target
has `kind` set to `failure`; that state may then expose named `retry`, `stop`, or
other recovery transitions. An `end` state's `transitions` object is empty.

## Design method

Start with the shortest primary path that completes the mission. Add a
conditional path only for a material alternative, ambiguity, safety boundary,
or recoverable failure. Every transition must name its condition and state
effect; do not rely on “continue as appropriate.” Every wait is a state, not a
hidden pause. Define how pause, resume, stop, decline, and retry affect state.
No path from `start` to a member of `successful_terminal_states` may bypass a
required HITL checkpoint. Stop and failure terminals may bypass approval when
their behavior explicitly preserves the user's choice or the failure state.

Connect each stage to logical Instruction Modules and a user-interaction
protocol. Do not assign modules to concrete Skills, files, runtime events, or
adapters. Present the blueprint as `draft` until the user explicitly approves
the identified version.
