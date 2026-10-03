# Plugin Builder coverage matrix

Each approved requirement and representative test appears exactly once in the ID column. An evidence target is a planned observable check unless the state says otherwise.

| ID | Owner | Evidence target | State |
| --- | --- | --- | --- |
| RQ1 | guiding-plugin-builder-sessions + building-and-updating-plugins | Repository-local create/update state scenarios T1 and standalone T7 | RUNTIME VERIFIED |
| RQ2 | planning-plugin-implementations | Derived skill/responsibility coverage in T1 and T2 | RUNTIME VERIFIED |
| RQ3 | guiding-plugin-builder-sessions | W1/W2 transition assertions in T1–T3 | RUNTIME VERIFIED |
| RQ4 | verifying-and-packaging-plugins + session-validator | Required-failure and unexecuted-test evidence in T5/T6 | RUNTIME VERIFIED |
| RQ5 | building-and-updating-plugins | Baseline member preservation and unresolved-member wait in T4 | RUNTIME VERIFIED |
| RQ6 | verifying-and-packaging-plugins | Deterministic ZIP and manual-return boundary in T2 | RUNTIME VERIFIED |
| RQ7 | planning-plugin-implementations + runtime adapters | Reuse evidence and standalone clean-process execution in T7 | RUNTIME VERIFIED |
| AC1 | guiding-plugin-builder-sessions | New and update flows from a generated artifact without repository imports in T7 | RUNTIME VERIFIED |
| AC2 | planning-plugin-implementations | Skills responsibility plan from behavior-only input in T1 | RUNTIME VERIFIED |
| AC3 | session-validator | W1 blocks mutation and W2 blocks packaging in T1–T3 | RUNTIME VERIFIED |
| AC4 | planning-plugin-implementations | Requirement-to-implementation-to-result trace in T2 | RUNTIME VERIFIED |
| AC5 | verifying-and-packaging-plugins | Required failure suppresses artifact in T5 | RUNTIME VERIFIED |
| AC6 | verifying-and-packaging-plugins | Unexecuted tests remain individually visible in T6 | RUNTIME VERIFIED |
| AC7 | building-and-updating-plugins | Unaffected and unexplained update members in T4 | RUNTIME VERIFIED |
| AC8 | verifying-and-packaging-plugins | Returned manual-upload ZIP with no deployment action in T2 | RUNTIME VERIFIED |
| AC9 | planning-plugin-implementations | Recorded reuse/adapt/bundle decision evidence in T7 | RUNTIME VERIFIED |
| AC10 | guiding-plugin-builder-sessions | Machine-readable create/update end-to-end results in T7 | RUNTIME VERIFIED |
| T1 | guiding-plugin-builder-sessions + planning-plugin-implementations | Behavior-only input reaches W1 without mutation | RUNTIME VERIFIED |
| T2 | verifying-and-packaging-plugins | Successful create trace, W2, and deterministic ZIP checks | RUNTIME VERIFIED |
| T3 | guiding-plugin-builder-sessions | Missing/conflicting behavior waits for newly approved design | RUNTIME VERIFIED |
| T4 | building-and-updating-plugins | Unspecified baseline content waits and is not deleted | RUNTIME VERIFIED |
| T5 | verifying-and-packaging-plugins | Persistent required failure yields no artifact | RUNTIME VERIFIED |
| T6 | verifying-and-packaging-plugins | Environmental limitation remains NOT VERIFIED and visible through W2 | RUNTIME VERIFIED |
| T7 | guiding-plugin-builder-sessions + runtime adapters | Generated 1.0.0 candidate normalizes canonical and retained legacy intake, runs clean-process wrapped create/update with preservation, executes its bundled tool, and closes digest-addressed evidence without repository imports | RUNTIME VERIFIED |
| RUNTIME-CODEX | Codex | Task 0 filesystem/ZIP primitive probe | RUNTIME VERIFIED |
| RUNTIME-WORK | ChatGPT Work Local/Desktop | Task 0 filesystem/ZIP primitive probe | RUNTIME VERIFIED |
| RUNTIME-CODEX-APPLICATION | Codex installed Plugin Builder | Representative T1–T7 execution from the generated artifact | NOT VERIFIED |
| RUNTIME-WORK-APPLICATION | ChatGPT Work Local/Desktop Plugin Builder | Representative T1–T7 execution from the generated artifact | NOT VERIFIED |
| RUNTIME-OPENCLAW | OpenClaw | Excluded phase-one runtime | NOT APPLICABLE |
| RUNTIME-CLAUDE | Claude | Excluded phase-one runtime | NOT APPLICABLE |
| STRUCT-SKILLS | Four portable skill contracts | Discovery, frontmatter, direct-reference closure, semantic contract parser tests, and installed Skill Creator validation on source and extracted artifact | STATICALLY VERIFIED |
| BEHAVIOR-SCENARIOS | T1–T7 local fixtures | Repository-local and standalone generated-artifact forward execution | RUNTIME VERIFIED |
| CONTRACT-SESSION | W1/W2, hashes, evidence, paths, and failure gates | Deterministic API and subprocess CLI tests | STATICALLY VERIFIED |
| CONTRACT-DISTRIBUTION | Deny-by-default content contract | Schema-v3 validation, product audit, exact selection, and two-build package identity | STATICALLY VERIFIED |
| ARTIFACT-CODEX | Generated local Codex artifact | Exact 60-member flat-root host-upload envelope, synchronized manifest pair, source/extracted plugin validation, exclusions, and byte-identical two-build ZIP/runtime-kit identity | STATICALLY VERIFIED |
| REPOSITORY-DISCOVERY | Application configuration | Repository discovery and configured command-path tests | STATICALLY VERIFIED |
| HANDOFF-INTERFACE-V1.1 | Design Assistant producer + Plugin Builder consumer | Full/create and delta/update cross-product tests preserve arbitrary IDs, exact UTF-8 text/source bytes, baseline identity, unaffected members, and deterministic ZIP bytes | RUNTIME VERIFIED |

## Phase-two design-to-implementation review

| Concern | Implementation | Direct evidence | Remaining state |
| --- | --- | --- | --- |
| RQ1–RQ7 and AC1–AC10 | Four workflow skills, `plugin_builder_core`, and explicit CLI orchestration | Rows above; product T1–T7 and standalone-artifact tests | Repository/local artifact `RUNTIME VERIFIED`; installed runtimes `NOT VERIFIED` |
| T1–T7 | `test_end_to_end_scenarios.py` and `test_standalone_artifact.py` | 13-scenario completion suite plus full product suite | Installed Codex/Work replay `NOT VERIFIED` |
| INV-PB-001–INV-PB-013 | `docs/application-invariants.md`, session, approval, candidate, verification, packaging, and tool services | Product contracts and full repository verifier | Installed-runtime rows remain `NOT VERIFIED` |
| S0–S5, W1, W2, H1, E1–E3, F1–F3 | `session_contract.py`, `session_state.py`, and CLI commands | Session-contract, pause/resume/cancel, failure, and recovery tests | Direct installed-runtime interaction `NOT VERIFIED` |
| W1/W2 approval gates | `approvals.py`, plan/tool hashes, candidate/report hashes | Planning, candidate, verification, and packaging tests | No remaining repository gap |
| Failure routes | Inspection, planning, build, verification, packaging result documents | T3, T4, T5, malformed-input and transaction-failure tests | Runtime-specific environment failures require target evidence |
| Reference policy | Direct SKILL.md links and candidate materialization | Skill contract, Creator validation, and reference-closure tests | No remaining repository gap |
| Application-tool contracts and bindings | `tool_contract.py`, plan compiler, candidate manifest, tool verifier | Bundled, framework, runtime-native, and MCP tests | Runtime-native/MCP execution `NOT VERIFIED` without target capability/auth |
| Dependencies, permissions, and configuration | Tool v1 contract plus W1 identity | Contract-negative tests and generated-candidate audits | Owner-configured external services `NOT VERIFIED` |
| Update preservation | `update.py`, `update_candidate.py`, change manifest | T4 and update preservation/tool-binding tests | No remaining repository gap |
| Distribution and publication | Deny-by-default audit, deterministic ZIP, manual delivery | Two-build identity, exact-member checks, extracted artifact validation | Publication `NOT PERFORMED`; OpenClaw/Claude `NOT APPLICABLE` |

The installed-runtime contract is `tests/runtime/T1-T7-runtime-scenarios.md`, with results constrained by `tests/runtime/runtime-result-schema.json`. Until a conforming target-runtime result is returned, classification is `CONDITIONALLY PORTABLE`, never `READY`.
