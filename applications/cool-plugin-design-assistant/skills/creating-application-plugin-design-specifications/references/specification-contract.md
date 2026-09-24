# Application Plugin Design Specification contract

Produce these sections in this order. Each section states positive requirements
and traces them to confirmed design inputs; use `not applicable` only with a
reason.

1. **Application identity and purpose** — stable name, purpose, and product boundary.
2. **Design Statement** — the approved version, quoted or embedded without expansion.
3. **Intended users and contexts** — actors, needs, environments, and accessibility context.
4. **Application mission and success outcomes** — mission plus observable success boundaries.
5. **Scope and exclusions** — supported work, explicit non-goals, and authority limits.
6. **Primary mission workflow** — stages, transitions, state effects, and terminal states.
7. **Conditional and alternative workflows** — guards, branches, re-entry, pause, stop, and recovery.
8. **Instruction Module contracts** — behavior-level primary-workflow, intent-triggered, and cross-cutting modules.
9. **User-intent routing requirements** — recognizable goals, conflicts, precedence, and route outcomes.
10. **User-interaction protocols** — modes, question limits, waits, alternatives, revision, and finalization.
11. **Human-in-the-Loop checkpoints** — decisions requiring human input or explicit confirmation.
12. **Inputs, outputs, and state requirements** — schemas, provenance, lifecycle, retention, and state ownership.
13. **Reference Material requirements and behavior-level usage map** — knowledge, stage/intent, exactness, rights, and fallbacks.
14. **Deterministic-operation requirements** — operations requiring reproducible logic and their input/output contracts.
15. **Tool, data, runtime, and external-service requirements** — capability needs and constraints without implementation selection.
16. **Safety, privacy, and policy boundaries** — prohibited behavior, data handling, and escalation.
17. **Failure, uncertainty, and recovery behavior** — visible failure states, retained state, retries, and fallbacks.
18. **Acceptance criteria** — observable requirement-level success and failure conditions.
19. **Representative application tests** — traceable scenarios, expected outcomes, and evidence limits.
20. **Assumptions, decisions, recommendations, and unresolved questions** — separate ledgers with owners and impact.
21. **Application Workbench handoff contract** — approval state, included artifacts, gates, and reserved implementation decisions.

## Decision blocks

After the requirement sections, preserve five explicit blocks:

- **Requirements:** normative behavior and constraints, with identifiers.
- **Confirmed decisions:** user-approved choices and the artifact/version where
  approval occurred.
- **Assumptions:** reversible premises, affected requirements, and validation
  point.
- **Recommendations:** advised choices, rationale, tradeoffs, and approval state.
- **Unresolved questions:** owner, impact, blocking status, and evidence or
  decision needed.

Do not present a requirement derived only from an assumption as confirmed. Do
not hide unresolved rights or distribution status inside the Reference Material
section. Cross-reference requirements to acceptance criteria and representative
tests without inventing executed evidence.

## Lifecycle

Start at `draft`. Present the complete version for revision and allow the user
to confirm, revise, reject, compare, pause, or stop. Only explicit confirmation
of that complete identified version changes it to `approved`. Earlier approval
of a Design Statement, workflow, module, or individual section is not approval
of the complete specification. An approved specification may be revised only as
a new draft version; prior approval does not transfer automatically.

The specification defines behavior and capability requirements. It does not
mandate Skill count or names, Skill folder structure or collaboration,
Reference Material-to-Skill bindings, runtime adapters, concrete storage/RAG,
or implementation packaging.
