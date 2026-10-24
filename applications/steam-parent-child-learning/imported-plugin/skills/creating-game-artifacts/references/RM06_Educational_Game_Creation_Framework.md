# RM06 — Educational Game Creation Framework
Version: R02 preparation v0.1 | Provenance: project-prepared derivative draft | Review: pending

## Learning-first production contract
Convert an **approved** game design into a production specification, rather than inventing new learning objectives during coding. Record age band, objective, assessment evidence, STEAM linkage, game rules and 3-level progression. Ask the adult to opt into artifact production after design review.

## Medium selection
- **Printable:** printable sheets, game board, cards, facilitator rules, scoring sheet, preparation/cut guidance and accessibility alternatives. Do not imply PDF export if not available.
- **Standalone web:** browser-based local prototype with no external scripts or child accounts by default; keyboard/touch equivalent controls, legible text, persistent-in-session state, explicit restart and win/lose states.
- **Advanced project:** versioned production brief for a selected coding agent/toolchain without assuming access, including acceptance tests, asset license needs, instructions and integration constraints.

## Production specification required fields
1. Game identity; exact grade/age band; adult facilitator; consent/supervision assumptions.
2. Observable learning outcome and corresponding in-game action/decision; avoid cosmetic educational labeling.
3. Rules and mechanics: legal actions, score and feedback, fail/win conditions, retries, difficulty and fairness.
4. Three levels with increasing conceptual challenge; age-sensitive reading and time limits; remedial branch.
5. Complete state table (`state`, `event`, `guard`, `action`, `next_state`), including start, pause, restart, failure and completion.
6. Screen/card inventory; assets manifest including dimensions or print sizes, labels, audio alternatives, provenance, rights and missing assets.
7. Inputs/outputs, validation, error messages, deterministic scoring rules, seed/answer handling, offline/network assumptions and accessibility.
8. Manual acceptance scenarios: correct/incorrect answer, invalid input, restart, progress, age fit, tool absence, no child-data retention.
9. Runnable-entrypoint instructions if actually built; `produced`, `executed`, `tested` must be independently recorded.
10. If tools unavailable: complete coding-agent handoff with files to create, technology-neutral behavior, pass/fail criteria, user setup and known uncertainties.

## Example state transition table
| State | Event | Guard | Action | Next |
|---|---|---|---|---|
| READY | Start | adult confirms objective | reset score | LEVEL1 |
| LEVEL1 | Answer | valid | assess reasoning and give explanation | LEVEL1 or LEVEL2 |
| LEVEL2 | Answer | valid | assess application and progress | LEVEL2 or LEVEL3 |
| LEVEL3 | Finish | tasks complete | summarize learning evidence | REVIEW |
| any active | Stop | always | stop activity and retain current summary | STOPPED |

## Quality boundary
Never claim an application runs merely because code is printed. Mark each artifact `design only`, `generated untested`, `tested with evidence`, or `fallback handoff`. Keep reward loops non-compulsive, avoid online social contact and collect no identifying child data by default.
