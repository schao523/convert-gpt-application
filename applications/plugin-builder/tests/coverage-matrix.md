# Plugin Builder coverage matrix

Each approved requirement and representative test appears exactly once in the ID column. An evidence target is a planned observable check unless the state says otherwise.

| ID | Owner | Evidence target | State |
| --- | --- | --- | --- |
| RQ1 | guiding-plugin-builder-sessions + building-and-updating-plugins | Create/update state scenarios T1 and T7 | NOT VERIFIED |
| RQ2 | planning-plugin-implementations | Derived skill/responsibility coverage in T1 and T2 | NOT VERIFIED |
| RQ3 | guiding-plugin-builder-sessions | W1/W2 transition assertions in T1–T3 | NOT VERIFIED |
| RQ4 | verifying-and-packaging-plugins + session-validator | Required-failure and unexecuted-test evidence in T5/T6 | NOT VERIFIED |
| RQ5 | building-and-updating-plugins | Baseline member preservation and unresolved-member wait in T4 | NOT VERIFIED |
| RQ6 | verifying-and-packaging-plugins | Deterministic ZIP and manual-return boundary in T2 | NOT VERIFIED |
| RQ7 | planning-plugin-implementations + runtime adapters | Reuse evidence and clean-runtime end-to-end execution in T7 | NOT VERIFIED |
| AC1 | guiding-plugin-builder-sessions | New and update flows without the Workbench repository in T7 | NOT VERIFIED |
| AC2 | planning-plugin-implementations | Skills responsibility plan from behavior-only input in T1 | NOT VERIFIED |
| AC3 | session-validator | W1 blocks mutation and W2 blocks packaging in T1–T3 | NOT VERIFIED |
| AC4 | planning-plugin-implementations | Requirement-to-implementation-to-result trace in T2 | NOT VERIFIED |
| AC5 | verifying-and-packaging-plugins | Required failure suppresses artifact in T5 | NOT VERIFIED |
| AC6 | verifying-and-packaging-plugins | Unexecuted tests remain individually visible in T6 | NOT VERIFIED |
| AC7 | building-and-updating-plugins | Unaffected and unexplained update members in T4 | NOT VERIFIED |
| AC8 | verifying-and-packaging-plugins | Returned manual-upload ZIP with no deployment action in T2 | NOT VERIFIED |
| AC9 | planning-plugin-implementations | Recorded reuse/adapt/bundle decision evidence in T7 | NOT VERIFIED |
| AC10 | guiding-plugin-builder-sessions | Understandable create/update end-to-end results in T7 | NOT VERIFIED |
| T1 | guiding-plugin-builder-sessions + planning-plugin-implementations | Behavior-only input reaches W1 without mutation | NOT VERIFIED |
| T2 | verifying-and-packaging-plugins | Successful create trace, W2, and ZIP checks | NOT VERIFIED |
| T3 | guiding-plugin-builder-sessions | Missing/conflicting behavior waits for newly approved design | NOT VERIFIED |
| T4 | building-and-updating-plugins | Unspecified baseline content waits and is not deleted | NOT VERIFIED |
| T5 | verifying-and-packaging-plugins | Persistent required failure yields no artifact | NOT VERIFIED |
| T6 | verifying-and-packaging-plugins | Environmental limitation remains NOT VERIFIED and requires W2 | NOT VERIFIED |
| T7 | guiding-plugin-builder-sessions + runtime adapters | Clean Codex and Work Local/Desktop create/update demonstration | NOT VERIFIED |
| RUNTIME-CODEX | Codex | Task 0 filesystem/ZIP primitive probe | RUNTIME VERIFIED |
| RUNTIME-WORK | ChatGPT Work Local/Desktop | Task 0 filesystem/ZIP primitive probe | RUNTIME VERIFIED |
| RUNTIME-OPENCLAW | OpenClaw | Excluded phase-one runtime | NOT APPLICABLE |
| RUNTIME-CLAUDE | Claude | Excluded phase-one runtime | NOT APPLICABLE |
| STRUCT-SKILLS | Four portable skill contracts | Discovery, frontmatter, direct-reference closure, and semantic contract parser tests | STATICALLY VERIFIED |
| BEHAVIOR-SCENARIOS | T1/T3, T4, and T5/T6 planned inputs | Target-runtime forward execution | NOT VERIFIED |
