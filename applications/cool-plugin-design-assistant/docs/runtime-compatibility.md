# Runtime Compatibility

## Current classification

`CONDITIONALLY PORTABLE`

`CONVERSION COMPLETE — RUNTIME VALIDATION PENDING`

The Codex and OpenClaw distributions contain the same seven portable Skills,
maintained references, and deterministic validators. No runtime adapter, RAG
subsystem, model, corpus, database, external service, or credential is required.

## Evidence state

| Gate | Codex | OpenClaw |
| --- | --- | --- |
| Shared source and deterministic build | STATICALLY VERIFIED | STATICALLY VERIFIED |
| Installed discovery | NOT VERIFIED | NOT VERIFIED |
| Representative execution | NOT VERIFIED | NOT VERIFIED |
| Cross-runtime behavioral equivalence | NOT VERIFIED | NOT VERIFIED |

## Local verification evidence

On 2026-09-24, all seven Skills and the plugin manifest passed their installed
creator validators. The product suite passed 25 tests, the framework suite
passed 179 tests, and the complete repository suite passed 217 tests.

The application-aware verifier reported PASS for provenance, product tests, all
six configured commands, the Codex build, two OpenClaw builds, OpenClaw package
verification, and byte-for-byte OpenClaw determinism. The generated identities
were captured in the ignored verifier report rather than embedded here, because
this document is itself part of both artifact identities.

Both completed artifacts passed their packaged distribution audit. Explicit
searches found no raw document/image/database/model assets, private absolute
paths, or credential patterns. The verifier recorded marketplace comparison as
`NOT VERIFIED` because no marketplace path was supplied.

The classification can become `PORTABLE` only after installed artifacts are
discovered and representative commands execute successfully in both runtimes.
No marketplace mutation, release, or publication has been performed.
