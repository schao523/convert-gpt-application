# Marketplace Publication Efficiency Stage One Design

Status: **APPROVED**
Date: 2026-10-12
Scope approval: Stage One approved by the owner in the development session on
2026-10-12
Written approval: confirmed by the owner in the development session on
2026-10-12  
Implementation authorization: **PLAN REVIEW PENDING**

## 1. Purpose

Reduce repeated marketplace publication work and agent-context consumption
without weakening artifact verification, exact-byte guarantees, cross-platform
coverage, repository separation, or publication authorization.

Stage One addresses only redundancies already proven by the current
implementation:

1. fresh-checkout verification already includes commit verification, so the
   separately documented `--commit HEAD` invocation is redundant;
2. the generated marketplace workflow currently runs the same validation
   matrix for both a feature-branch push and its pull request; and
3. complete machine-readable evidence must remain available, but routine agent
   updates do not need to reproduce every path and mutation record.

## 2. Preserved trust boundaries

Stage One does not change the meaning or implementation of any verification
gate. The following remain mandatory:

- deterministic marketplace preparation in a separate staging root;
- one complete staged-filesystem verification before marketplace mutation;
- Git index evidence before committing;
- commit and fresh-checkout evidence before publication;
- strict SHA-256, exact-byte attributes, link and reparse-point rejection, and
  catalog reconstruction;
- cross-platform validation on Windows, Linux, and macOS;
- an aggregate CI failure when any required plugin validation fails;
- separate owner authorization for applying a staged delta, committing,
  pushing, merging, or otherwise publishing marketplace state.

The Workbench repository and marketplace repository remain separate trust
domains. Nothing in Stage One publishes or mutates the Obvious One marketplace.

## 3. Documented local verification sequence

The command reference will specify this sequence:

1. run ordinary filesystem verification against the isolated marketplace
   stage;
2. copy the verified stage into an external disposable Git repository or the
   separately authorized marketplace checkout;
3. stage the exact delta and run `verify-marketplace --index`;
4. create the local commit; and
5. run `verify-marketplace --fresh-checkout`.

The standalone `verify-marketplace --commit HEAD` command will be removed from
the required sequence. No commit gate is removed: fresh-checkout mode resolves
`HEAD`, compares the committed scoped tree with the index, evaluates committed
exact-byte attributes, and then reproduces and compares checkout bytes.

The reference will state explicitly that a successful fresh-checkout result
must report all four gates as follows:

```text
filesystem: PASS
index: PASS
commit: PASS
fresh_checkout: PASS
```

The existing `--commit` interface remains supported for diagnostic and
standalone use. Stage One changes the recommended publication sequence, not
CLI compatibility.

## 4. Generated marketplace workflow triggers

The canonical generated marketplace workflow will use:

```yaml
on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:
```

This produces:

- one pre-merge validation run for a pull request;
- one post-merge validation run for the authoritative `main` state; and
- an explicit manual run when requested.

A feature-branch push without a pull request will not run the marketplace
matrix. Opening or updating its pull request will run the matrix. The plugin
matrix, three operating systems, fail-fast behavior, per-plugin verifier, and
aggregate job are otherwise unchanged.

The generator remains canonical. Tests must compare the generated workflow
with the exact approved trigger shape so a manually edited marketplace copy
cannot become the framework source of truth.

## 5. Concise evidence handling

Stage One does not alter `result-schema-v1`, remove evidence fields, or add a
second output format. Every framework command continues to emit exactly one
complete ASCII-safe result document.

Operational guidance will require callers to:

1. save the complete result document below ignored `.tmp` or `dist` storage;
2. retain its SHA-256 and path with the publication evidence;
3. inspect `operation`, `status`, `code`, gate states, artifact identities, and
   diagnostics before continuing; and
4. report only those decision-relevant fields in routine agent commentary,
   linking the complete saved evidence when detailed review is needed.

Callers must not infer success from process exit code alone. Concise reporting
does not permit truncating, rewriting, or discarding the authoritative result
document.

## 6. Files and responsibilities

Stage One is expected to modify only:

- `src/obvious_one_plugin_framework/marketplace_ci.py` — canonical generated
  workflow trigger definition;
- marketplace CI generator tests below `tests/framework/` — exact trigger and
  deterministic-generation coverage;
- `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md` — optimized command sequence
  and concise evidence-handling guidance.

No application product, distribution contract, preparation catalog, generated
plugin artifact, marketplace artifact, or marketplace repository file is part
of this implementation.

## 7. Verification requirements

Implementation must be test-first and provide all of the following evidence:

1. a failing test showing that the old generated workflow permits unrestricted
   push events;
2. a passing test proving the generated workflow contains `pull_request`,
   `push.branches: [main]`, and `workflow_dispatch`;
3. a passing test proving the plugin-by-OS matrix and aggregate failure job are
   unchanged;
4. deterministic repeated workflow generation with identical bytes;
5. focused marketplace CI and Git-evidence tests;
6. the complete generic framework suite;
7. `git diff --check`; and
8. a final diff audit proving no product or marketplace artifact changed.

Because the CLI behavior of `--commit` and `--fresh-checkout` is unchanged,
existing Git-evidence tests must remain green. No test may be weakened or
deleted merely to accept the new workflow.

## 8. Explicitly deferred work

The following reviewed improvements belong to Stage Two and are not authorized
by this specification:

- reusable identity-bound filesystem-verification receipts;
- affected-plugin CI matrix selection;
- automated `apply-marketplace-stage` behavior;
- release-descriptor or `build`/`verify_existing` lifecycle redesign;
- result-schema or CLI output-format changes;
- caching or skipping any SHA-256, filesystem, Git, or cross-platform gate.

## 9. Completion and publication boundary

Stage One implementation is complete when the canonical generator, tests, and
command reference satisfy this specification and the required local
verification passes.

Completion does not update `D:\GitHub\obvious-one-plugins`. Adopting the newly
generated workflow in that repository requires a separately reviewed exact
delta and explicit owner authorization to apply, commit, push, and merge it.
