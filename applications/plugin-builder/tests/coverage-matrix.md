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
| T7 | guiding-plugin-builder-sessions + runtime adapters | Generated artifact runs clean-process create/update without repository imports | RUNTIME VERIFIED |
| RUNTIME-CODEX | Codex | Task 0 filesystem/ZIP primitive probe | RUNTIME VERIFIED |
| RUNTIME-WORK | ChatGPT Work Local/Desktop | Task 0 filesystem/ZIP primitive probe | RUNTIME VERIFIED |
| RUNTIME-CODEX-APPLICATION | Codex installed Plugin Builder | Representative T1–T7 execution from the generated artifact | NOT VERIFIED |
| RUNTIME-WORK-APPLICATION | ChatGPT Work Local/Desktop Plugin Builder | Representative T1–T7 execution from the generated artifact | NOT VERIFIED |
| RUNTIME-OPENCLAW | OpenClaw | Excluded phase-one runtime | NOT APPLICABLE |
| RUNTIME-CLAUDE | Claude | Excluded phase-one runtime | NOT APPLICABLE |
| STRUCT-SKILLS | Four portable skill contracts | Discovery, frontmatter, direct-reference closure, and semantic contract parser tests | STATICALLY VERIFIED |
| BEHAVIOR-SCENARIOS | T1–T7 local fixtures | Repository-local and standalone generated-artifact forward execution | RUNTIME VERIFIED |
| CONTRACT-SESSION | W1/W2, hashes, evidence, paths, and failure gates | Deterministic API and subprocess CLI tests | STATICALLY VERIFIED |
| CONTRACT-DISTRIBUTION | Deny-by-default content contract | Schema-v3 validation, product audit, exact selection, and two-build package identity | STATICALLY VERIFIED |
| ARTIFACT-CODEX | Generated local Codex artifact | Exact manifest closure, plugin validation, exclusions, and two-build manifest identity | STATICALLY VERIFIED |
| REPOSITORY-DISCOVERY | Application configuration | Repository discovery and configured command-path tests | STATICALLY VERIFIED |
