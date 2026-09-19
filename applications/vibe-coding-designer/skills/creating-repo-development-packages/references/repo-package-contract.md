# Repo development package contract

## Minimum architecture

- `AGENTS.md`: mission, sources of truth, required reading, repository boundaries, workflow, tests, definition of done, decision boundaries, and documentation update rules.
- `Spec.md`: goals, non-goals, actors, stable functional requirements, flows, form-specific interfaces, data, integrations, quality attributes, constraints, acceptance criteria, and open questions.
- `Tasks.md`: stable task IDs, objectives, spec references, dependencies, likely areas, implementation steps, validation, expected results, and completion criteria.

Add `Architecture.md`, `UI.md`, `API.md`, `Data.md`, `Workflows.md`, `Testing.md`, `Security.md`, `Environment.md`, `Deployment.md`, `Conventions.md`, or `Decisions.md` only when the content has a distinct responsibility, multiple consumers, and explicit inbound references.

## Validation

Check input coverage, document integrity, reference resolution, requirement-to-task traceability, task-to-requirement justification, dependency cycles/order, agent executability, duplication, contradictions, and context efficiency. Report each dimension as `PASS`, `PARTIAL`, or `FAIL` and list blocking issues separately.
