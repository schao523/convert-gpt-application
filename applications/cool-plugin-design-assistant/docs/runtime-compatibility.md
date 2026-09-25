# Runtime Compatibility

## Current classification

`PORTABLE`

The Codex and OpenClaw distributions contain the same seven portable Skills,
maintained references, and deterministic validators. No runtime adapter, RAG
subsystem, model, corpus, database, external service, or credential is required.

## Evidence state

| Gate | Codex | OpenClaw |
| --- | --- | --- |
| Shared source and deterministic build | STATICALLY VERIFIED | STATICALLY VERIFIED |
| Installed discovery | RUNTIME VERIFIED | RUNTIME VERIFIED |
| Packaged deterministic commands | RUNTIME VERIFIED | RUNTIME VERIFIED |
| Approved representative-scenario suite | RUNTIME VERIFIED | RUNTIME VERIFIED |
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

The two completed representative executions used the same user scenario and the same
portable Skill implementation. Their verbosity differed, but the routing,
question count, language, evidence handling, and wait behavior were
behaviorally equivalent. No runtime adapter or application-level fork was
required for that scenario.

On 2026-09-25, the remaining approved scenarios were executed against exact
commit `0699c0055361f742a24fa033be3957d86cc6aefb` in both installed runtimes.
Codex and OpenClaw passed BEH-006, BEH-008, BEH-011, and BEH-013 as well as the
previously completed BEH-001 scenario. OpenClaw used the generated bundle whose
content SHA-256 was
`974ceb052c42f97a1bf3fb9ce620f680984bc5540764cb00cc26455bb8609a46`.

| Compared behavior | Codex | OpenClaw | Result |
| --- | --- | --- | --- |
| Missing-outcome question count and wait behavior | One focused question, then wait | One focused question, then wait | Equivalent |
| Draft and complete-version approval gates | Preserved | Preserved | Equivalent |
| Instruction Module versus Skill boundary | Preserved | Preserved | Equivalent |
| Behavioral reference usage versus technical binding | Preserved | Preserved | Equivalent |
| Unsupported coverage claims | Rejected as `NOT VERIFIED` | Rejected as `NOT VERIFIED` | Equivalent |
| Packaged launcher outputs | All seven checks passed | All seven checks passed | Equivalent |
| Installed Skill discovery | Seven portable Skills | Seven portable Skills | Equivalent |

Differences were limited to response length and formatting. The same portable
Skill implementations preserved the required decisions, gates, evidence
states, interaction rules, and Workbench boundaries without a runtime adapter
or application-level fork.

## Marketplace staging

The marketplace baseline began at commit
`49237aba246857c9112809bc03eb71bf32a21c98`. The first full catalog staging run
correctly rejected stale committed-byte identities in the pre-existing Cool
Bible Tutor legacy artifact. The isolated marketplace branch was repaired by
preserving the audited nested artifact bytes and regenerating its outer content
manifest from Git blobs; the baseline and public marketplace were not mutated.

After that repair, full catalog preparation and filesystem verification passed
with no diagnostic plugins. The verified stage identity was
`c4edf693401d559a40cc627176144a6c02f1526c7c665bc9a44c04a6e01236f0`.
It includes both Cool Plugin Design Assistant artifacts, the catalog entries,
the generated verifier and workflow, the legacy verification target, and the
schema-v3 Vibe Coding Designer build canary.

Git index, commit, fresh-checkout, publication, and post-publication install
verification remain separate gates. No public marketplace mutation, release,
or registry submission had been performed when this artifact was built.
