# Plugin Builder invariant register

`SPEC-v1.0` and its normalized handoff are the behavioral authority. Evidence states describe only what has actually been exercised.

| Invariant | Non-negotiable behavior | Owner | Enforcement/evidence target | Current state |
| --- | --- | --- | --- | --- |
| INV-PB-001 | Only the approved `SPEC-v1.0` snapshot and explicit later owner decisions may define application behavior. | guiding-plugin-builder-sessions | Approved-design hash and canonical-gate tests | STATICALLY VERIFIED |
| INV-PB-002 | W1 approval precedes every create/update mutation; W2 approval precedes packaging. | guiding-plugin-builder-sessions | Session transition validator and T1/T2/T3 | NOT VERIFIED |
| INV-PB-003 | Every RQ and AC maps to an implementation owner and observable evidence target. | planning-plugin-implementations | Coverage-matrix completeness test | STATICALLY VERIFIED |
| INV-PB-004 | Evidence uses `EXPECTED`, `STATICALLY VERIFIED`, `RUNTIME VERIFIED`, `NOT VERIFIED`, or explicit runtime `NOT APPLICABLE` without upgrading unsupported claims. | verifying-and-packaging-plugins | Coverage schema and result-report tests | STATICALLY VERIFIED |
| INV-PB-005 | Any explicit required-check failure blocks W2 completion and artifact packaging. | verifying-and-packaging-plugins | Session validator plus T5 | NOT VERIFIED |
| INV-PB-006 | Update mode preserves unaffected members and waits for an explicit decision on unexplained members. | building-and-updating-plugins | Update inventory/diff contract plus T4 | NOT VERIFIED |
| INV-PB-007 | A requested behavioral change returns to design approval; Plugin Builder never self-approves a changed specification. | guiding-plugin-builder-sessions | Transition validator plus T3 | NOT VERIFIED |
| INV-PB-008 | ZIP intake and output are confined, reject traversal, duplicate logical paths, and case-fold collisions, and never follow escaping links. | building-and-updating-plugins | Archive validator security fixtures | NOT VERIFIED |
| INV-PB-009 | Persisted records use relative paths and retain the minimum private data needed for the active workspace. | building-and-updating-plugins | State-schema and privacy tests | NOT VERIFIED |
| INV-PB-010 | Manifests and ZIP outputs are deterministic for identical approved inputs and tool versions. | verifying-and-packaging-plugins | Repeated-build byte/hash comparison | NOT VERIFIED |
| INV-PB-011 | The final artifact is returned for manual upload; automatic account deployment and publication are forbidden. | verifying-and-packaging-plugins | Distribution audit and T2 | STATICALLY VERIFIED |
| INV-PB-012 | Phase one targets only Codex and ChatGPT Work Local/Desktop; OpenClaw and Claude remain excluded. | guiding-plugin-builder-sessions | Scope/configuration tests | STATICALLY VERIFIED |

Task 0 runtime evidence proves the five required local filesystem and ZIP primitives in both target environments. It does not prove application-level T1–T7 behavior.
