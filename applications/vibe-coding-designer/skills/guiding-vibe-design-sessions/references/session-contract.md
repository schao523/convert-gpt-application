# Session contract

Use one focused question at a time. A user may answer several stages at once; record those answers and continue with the earliest unresolved consequential stage. Do not repeat answered questions.

The explicit eleven-stage wizard is:

1. **Purpose and outcome** — the problem, intended result, and success signal.
2. **Users and actors** — people, systems, roles, and permissions.
3. **Software form** — CLI, TUI, desktop, mobile, API/service, worker/automation, library/tool, or Web GUI.
4. **Core capabilities** — required behavior, priorities, and non-goals.
5. **Interfaces** — commands, public APIs, screens, events, files, or library surface as applicable.
6. **Data and persistence** — entities, validation, lifecycle, storage, or an explicit no-persistence decision.
7. **Workflows and integrations** — triggers, steps, services, retries, compensation, and failure paths.
8. **Quality attributes** — security, privacy, performance, accessibility, reliability, observability, and compatibility as applicable.
9. **Technology and environment** — constraints, deployment target, runtime, and justified defaults.
10. **Validation** — acceptance criteria, test levels, fixtures, and traceability.
11. **Delivery** — requested artifacts, implementation handoff, assumptions, and unresolved decisions.

## Interaction rules

- Match the user's language; use Traditional Chinese by default when it cannot be inferred.
- Explain technical terms briefly and give a recommendation when presenting choices.
- Preserve user decisions in meaning, but normalize terminology across artifacts.
- If the user asks for a rapid draft, proceed with clearly labeled reversible assumptions.
- Pause only for a choice that materially changes scope, architecture, rights, or external effects.
