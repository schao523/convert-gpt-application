# Runtime Compatibility

## Current classification

`PORTABLE`

`READY`

The Codex and OpenClaw distributions contain the same seven portable Skills,
maintained references, and deterministic validators. No runtime adapter, RAG
subsystem, model, corpus, database, external service, or credential is required.

## Evidence state

| Gate | Codex | OpenClaw |
| --- | --- | --- |
| Shared source and deterministic build | STATICALLY VERIFIED | STATICALLY VERIFIED |
| Installed discovery | RUNTIME VERIFIED | RUNTIME VERIFIED |
| Packaged deterministic commands | RUNTIME VERIFIED | RUNTIME VERIFIED |
| Representative execution | RUNTIME VERIFIED | RUNTIME VERIFIED |
| Cross-runtime behavioral equivalence | RUNTIME VERIFIED | RUNTIME VERIFIED |

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

## Runtime observations

On 2026-09-24, Codex CLI 0.146.0 installed version 1.0.0 from an isolated local
marketplace built from the pull-request artifact. `plugin list` discovered and
enabled the plugin. All seven packaged deterministic commands passed against
the installed artifact. An ephemeral representative execution loaded the
installed `creating-design-statements` Skill and, when the desired outcome was
missing, asked one focused question in Traditional Chinese without inferring an
inverse.

OpenClaw 2026.9.4 installed the same generated bundle. The plugin was enabled at
version 1.0.0, and all seven Skills were eligible, model-visible,
user-invocable, command-visible, and free of missing requirements. The installed
launcher returned PASS for status, design, workflow, Instruction Module,
handoff, coverage, and distribution-audit checks. An authenticated
representative conversation loaded the same Skill and preserved the same
missing-outcome behavior: it identified the unresolved field, asked exactly one
focused question in Traditional Chinese, and did not invent the answer.

The two representative executions used the same user scenario and the same
portable Skill implementation. Their verbosity differed, but the routing,
question count, language, evidence handling, and wait behavior were
behaviorally equivalent. No runtime adapter or application-level fork was
required.

## Marketplace staging

The baseline marketplace was clean at commit
`49237aba246857c9112809bc03eb71bf32a21c98`. Full catalog staging stopped with
`content_manifest_mismatch` before creating an output tree: the pre-existing
Cool Bible Tutor legacy manifest does not match 24 committed files. The baseline
was not modified, and this failure is not reclassified as evidence for the new
plugin. An isolated single-plugin staging harness passed, but it is not the
approved full-marketplace delta.

A final application-aware comparison against that baseline passed every shared,
product, command, build, verification, and determinism gate. Its marketplace
gate correctly failed because both unpublished plugin destinations are absent
and `marketplace-approved-delta.json` approves no missing files. This remains an
unverified publication boundary, not a plugin behavior failure.

Marketplace publication remains a separate authorization boundary. No public
marketplace mutation, release, or publication has been performed.
