# RM07 — Educational Game Playtesting & Evaluation Guide
Version: R02 preparation v0.1 | Provenance: project-prepared derivative draft | Review: pending

## Separate evaluation lenses
- **Functionality:** game loads, controls work, input validation, states and score correct, reset and completion paths verified.
- **Usability/accessibility:** child understands controls, readable labels, keyboard/touch input, equivalent text to audio/color, no time pressure without accessibility setting.
- **Developmental fit:** reading and reasoning demands suited to learner; facilitator observes fatigue/frustration, offers opt-out.
- **Learning outcome:** child demonstrates intended knowledge in choices, explains why, transfers concept to an analogous task. A score alone is insufficient proof.

## Session protocol
1. Adult checks safe device/location and obtains appropriate consent; no names, recordings, or accounts required.
2. Record build/version, intended age band, learning goal and test context.
3. Do a functional smoke test without child first. If broken or unsafe, do not present it as ready.
4. Run a brief child-assisted task with low-stakes verbal prompts and optional quiet breaks; stop on discomfort.
5. Record observed actions and words without personal identifiers; mark observations distinct from interpretation.
6. Compare one pre-task or matched baseline prompt with a similar post-task when feasible; do not equate differences with causal learning gain.
7. Prioritize one change, update design/build version, and rerun affected tests.

## Observation template
| Build | Test case | Observed evidence | Lens | Issue severity | Suggested change | Retest status |
|---|---|---|---|---|---|---|
| v0.1 | Example: restart after error | not yet tested | functionality | unknown | verify reset path | pending |

## Release decision
Function success and learning plausibility are separate gates. Any untested component remains `not tested`. Adult retains educational judgment and consent authority.
