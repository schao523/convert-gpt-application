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
| 1.0.3 Source Handoff representative scenario | RUNTIME VERIFIED | RUNTIME VERIFIED |
| 1.0.3 cross-runtime behavioral equivalence | RUNTIME VERIFIED | RUNTIME VERIFIED |

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
with no diagnostic plugins. The generated identity is retained in the external
verification report rather than embedded here because this document is itself
part of that identity. The stage includes both Cool Plugin Design Assistant
artifacts, the catalog entries, the generated verifier and workflow, the legacy
verification target, and the schema-v3 Vibe Coding Designer build canary.

Git index, commit, and fresh-checkout verification passed before publication.
Marketplace PR #1 was merged as
`4b4a4f4a9dc48b2a089a76bb1cf8763c56788dff`. Post-publication Codex installation
then exposed a missing local-source discriminator in the catalog entry; the
regression-tested correction was published through marketplace PR #2 as
`5daa24e7f38e05c16aa4254fa296c5381eab4e97`. GitHub-source installation,
seven-Skill discovery, and all packaged validation commands subsequently passed
in both Codex and OpenClaw. No GitHub Release or external registry submission
was performed.

Version 1.0.2 was subsequently published for Codex and OpenClaw through
marketplace PR #5 at commit
`5deedc580acb9afa276f81abeca15e91ce20a56c`. The source repository records
that immutable marketplace binding after publication; no GitHub Release,
ClawHub publication, or OpenAI universal-directory submission was performed.

## Version 1.0.3 publication and runtime evidence

The Source Handoff preflight and Chat-to-Work routing were merged in source PR
#23 at `2426cdb09e27830ac6451cb8994f6375cb73dbd3` and published for Codex
and OpenClaw in marketplace PR #15 at
`ff4fe36679783462136d1fa7af845ae6967d1ebe`. That release commit and a fresh
checkout passed catalog verification for 1,118 files. Marketplace PR #16
corrected the Codex vendored validator and its digest record to match the
hardened source at `d0f560e4f7b3c6017dfb942844a2d048757b563f`.
The corrected artifact passed its generated verifier, source equivalence gate,
and all 32 marketplace CI checks. No GitHub Release, ClawHub publication,
or universal directory submission was performed.

Codex CLI 0.146.0 installed the staged 1.0.3 package from an isolated local
marketplace, then installed the published 1.0.3 package from the registered
GitHub marketplace. A fresh representative Codex session used the installed
Skills to require a Source Handoff ZIP in Chat mode and an observed preflight,
normalization, and final canonical validation in Work mode. It did not claim an
unrun tool operation.

OpenClaw 2026.10.6 installed the same 1.0.3 bundle in isolated state and then
reinstalled it from the published marketplace checkout. All seven Skills were
eligible and model-visible. A DeepSeek-backed representative session read the
installed Skill and references and preserved the same Source-versus-Canonical
handoff boundary, approval gate, exact-byte checks, and Workbench-reserved
decisions as Codex. The two runtimes differed in detail and formatting, not in
the required route or failure behavior.

The post-publication installed trees matched the published marketplace
artifacts byte-for-byte: 68 Codex files and 70 OpenClaw files.

All six configured deterministic commands passed from each installed package.
The installed OpenClaw launcher returned PASS for PF01–PF10 on the approved
Source Handoff fixture, then normalized it to `WORKBENCH_HANDOFF_V1_1`. Codex
and OpenClaw produced the same Canonical ZIP SHA-256:
`d311e7786e36d574dcb3ecc9e155af686ade243cf18b64c0306150a039b25ee1`.
The Source ZIP SHA-256 was
`3048f72528bea2e9983ddfd9689ced7aa655759292eb9bca7cf37e29a3342255`.
The portable Skills and deterministic contracts need no application-level
runtime fork or adapter, so the 1.0.3 classification is `PORTABLE`.
