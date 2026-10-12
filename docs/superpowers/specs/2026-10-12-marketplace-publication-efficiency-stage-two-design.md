# Marketplace Publication Efficiency Stage Two Design

**Date:** 2026-10-12  
**Status:** OWNER-APPROVED CONVERSATIONAL DESIGN; WRITTEN SPECIFICATION PENDING REVIEW  
**Scope:** Identity-bound filesystem-verification receipts and affected-plugin CI matrix selection

## 1. Purpose

Stage Two reduces repeated marketplace evidence handling and avoids unnecessary
cross-platform plugin validation jobs without weakening the marketplace trust
boundary. It adds two related capabilities:

1. deterministic, identity-bound receipts for successful marketplace filesystem
   verification; and
2. registry-driven selection of plugins affected by an explicit Git revision
   range.

The implementation must preserve strict SHA-256 verification, complete
per-plugin validation, catalog authority, deterministic output, fail-closed
behavior, and the existing `result-schema-v1` contract.

## 2. Scope boundaries

### 2.1 In scope

- A canonical filesystem-verification receipt schema.
- Public framework APIs and CLI options to write and validate receipts.
- A self-contained generated selector for marketplace CI.
- Deterministic mapping from changed marketplace paths to registered plugins.
- Full-matrix fallback whenever a narrower selection cannot be proved.
- Correct handling of a valid empty affected-plugin selection.
- Generated workflow integration for pull requests and pushes to `main`.
- Complete test, documentation, and deterministic-generation coverage.

### 2.2 Out of scope

- Automatic application of a prepared marketplace stage.
- Marketplace repository mutation or publication.
- Release-descriptor or `build`/`verify_existing` lifecycle redesign.
- Persistent or remote validation caches.
- Skipping required SHA-256 calculation, verification commands, Git evidence,
  installed-runtime checks, or cross-platform checks.
- Changing plugin behavior, application scope, target runtimes, or distribution
  rights.
- Changing the meaning of `PASS`, `FAIL`, `BLOCKED`, `NOT VERIFIED`, or
  `NOT APPLICABLE`.

## 3. Existing architecture and constraints

`prepare-marketplace` creates a separate marketplace stage and generates:

- `.obvious-one-validation.json` as the portable validation registry;
- `tools/verify_marketplace.py` as the standalone per-plugin verifier; and
- `.github/workflows/validate.yml` as the catalog-driven validation workflow.

`verify-marketplace` currently verifies the generated controls, invokes the
standalone verifier once per catalog plugin, optionally verifies Git index,
commit, and fresh-checkout evidence, and emits one complete ASCII-safe
`result-schema-v1` document.

Stage One restricted automatic workflow execution to pull requests, pushes to
`main`, and manual dispatch. It retained the full plugin-by-OS matrix and all
verification gates. Stage Two must build on those interfaces rather than create
a competing marketplace pipeline.

## 4. Architecture

The two new capabilities share the generated validation registry as their
authority:

```text
Preparation catalog + staged marketplace
                 |
                 v
      Generated validation registry
          |                    |
          v                    v
Filesystem verifier      Git change selector
          |                    |
          v                    v
Identity-bound receipt   Affected plugin IDs
          |                    |
          +----------+---------+
                     v
        Complete result evidence and CI matrix
```

Receipts carry compact, independently checkable evidence about a verification
that already happened. They are not permission to omit verification. The
selector narrows the set of plugin jobs only when the registry and Git delta
prove ownership unambiguously; otherwise it selects every registered plugin.

## 5. Filesystem-verification receipts

### 5.1 Receipt schema

The canonical schema identifier is
`marketplace-filesystem-verification-receipt-v1`. A receipt contains exactly:

- `schema`;
- `marketplace_id`;
- `operation`, fixed to `verify-marketplace`;
- `status`, fixed to `PASS`;
- `marketplace_identity` with `content_sha256`, `file_count`, and
  `total_bytes`;
- `controls` with SHA-256 values for the preparation catalog, generated
  validation registry, standalone verifier, and generated selector;
- `plugins`, sorted by `plugin_id`, with each plugin's version, applicable
  targets, target destinations, and recorded artifact content identities;
- `verification_profile` with the receipt schema version and portable verifier
  contract version; and
- `receipt_sha256`, calculated over the canonical payload with that field
  omitted.

All mappings use sorted keys, arrays have specified stable ordering, text is
UTF-8 with LF line endings, and the file ends with one newline. The receipt
must not contain timestamps, absolute paths, usernames, credentials, hostnames,
temporary paths, or other machine-specific state.

### 5.2 Production rules

- A receipt may be written only when the filesystem gate is `PASS`.
- Receipt writing is explicit; verification without the new option preserves
  existing behavior.
- The destination must be an explicitly supplied safe path. Repository-local
  generated output belongs below ignored `.tmp` or `dist` storage.
- Writing is transactional: a failed operation cannot replace an existing
  receipt with partial or invalid content.
- Repeated production from identical inputs yields byte-identical receipts.
- The normal operation result records the receipt as an artifact with its
  SHA-256 and size; it does not embed the complete receipt payload.

### 5.3 Validation and reuse rules

Receipt validation must:

1. validate the exact closed schema;
2. verify the receipt's own canonical SHA-256;
3. recalculate the current marketplace tree identity using SHA-256;
4. recalculate all control identities;
5. reconstruct and compare the sorted plugin and artifact identities; and
6. return explicit diagnostics for stale, foreign, malformed, or mismatched
   receipts.

A valid receipt may be referenced by deterministic reports or later evidence
collection as proof of the earlier successful filesystem operation. It must not
cause the framework or generated CI to skip current SHA-256 calculation,
per-plugin verification commands, Git evidence, or required OS jobs. Receipt
validation and filesystem verification remain separate evidence states.

An explicitly supplied invalid receipt fails receipt validation. It must not be
silently ignored, rewritten, or treated as `NOT VERIFIED` while claiming the
receipt gate passed.

### 5.4 Public interface

The framework will expose focused public receipt construction, loading, and
validation functions in a dedicated module. `verify-marketplace` will gain an
optional receipt-output argument. A receipt-validation CLI operation or
explicit validation argument will emit exactly one `result-schema-v1`
document. The implementation plan must select the smallest interface that keeps
receipt validation independently invocable without overloading unrelated Git
modes.

## 6. Affected-plugin selection

### 6.1 Generated selector

`prepare-marketplace` generates a standalone selector under `tools/` beside the
standalone verifier. It must run with Python 3.11 or newer and the standard
library only; the framework package is not required in the marketplace checkout.

The selector accepts:

- the validation registry path;
- an explicit base Git revision;
- an explicit head Git revision; and
- a JSON-output option.

It invokes Git without a shell, validates both revisions, reads changed paths
using an unambiguous machine-readable form, and emits exactly one ASCII-safe
`result-schema-v1` document. Its evidence includes:

- selection mode: `AFFECTED`, `ALL`, or `NONE`;
- sorted selected plugin IDs;
- base and head commit identities;
- changed-path count and a SHA-256 of the canonical sorted change records;
- the reason for a full-matrix fallback; and
- the GitHub matrix payload used by the workflow.

Routine output does not need to repeat the complete changed-path list, but the
selection must be reproducible from the named commits and evidence digest.

### 6.2 Ownership mapping

The validation registry remains the sole plugin ownership authority. Each
applicable Codex or OpenClaw destination belongs to exactly one plugin.

- A change wholly below a registered destination affects that plugin.
- Changes below several registered destinations affect their union.
- Plugin IDs are deduplicated and sorted.
- Both old and new paths of deletes, copies, and renames are evaluated.
- Overlapping destinations or duplicate ownership are invalid registry states,
  not selector tie-breakers.

### 6.3 Shared controls and fallback

Changes to any shared trust-boundary control select every registered plugin,
including:

- `.obvious-one-validation.json`;
- Codex and OpenClaw runtime catalogs;
- the generated verifier or selector;
- the generated validation workflow;
- exact-byte Git attribute policy; and
- another generated control declared by the registry contract.

The selector also selects all plugins when:

- either revision is missing, invalid, unavailable, or ambiguous;
- Git history is too shallow to resolve the requested range;
- a changed path cannot be attributed safely;
- a removed plugin or previous registry cannot be reconciled;
- a rename or copy has an unmapped endpoint;
- parsing, subprocess execution, or registry validation fails; or
- any other condition prevents proof of a narrower set.

Fallback-to-all is a successful conservative selection only when the current
registry itself is valid. An invalid current registry is a verification
failure and cannot safely supply a matrix.

### 6.4 Empty selection

If the Git delta is valid and contains no marketplace-controlled change, the
selector emits mode `NONE` and an empty plugin list. The workflow must treat
that as an intentional successful no-op, not as a malformed matrix or an
accidentally skipped validation job.

## 7. Workflow integration

The generated workflow retains the Stage One triggers:

- `pull_request`;
- `push` restricted to `main`; and
- `workflow_dispatch`.

For pull requests, the selector compares the pull-request base and head commit.
For pushes to `main`, it compares the event's before and current commit. The
checkout must fetch enough history to resolve these explicit commits. Missing
or zero event revisions cause full-matrix fallback.

Manual dispatch always selects all plugins unless a future separately approved
contract adds explicit revision inputs.

The workflow must preserve:

- `fail-fast: false`;
- Windows, Ubuntu, and macOS validation for every selected plugin;
- the existing standalone per-plugin verifier invocation;
- independent matrix results; and
- the aggregate failure gate.

The aggregate job accepts a skipped validation job only when selector evidence
shows a valid `NONE` selection. It fails if selection failed, any selected
plugin job failed, or validation was unexpectedly skipped.

## 8. Failure and status semantics

- Receipt production: `PASS` only after filesystem verification passes and the
  canonical receipt is written and revalidated.
- Receipt validation: `FAIL` for malformed, stale, foreign, or mismatched
  evidence; never `PASS` through fallback.
- Selector: `PASS` with mode `ALL` for a valid conservative fallback based on a
  valid current registry.
- Selector: `FAIL` when the current registry or required local control cannot be
  trusted enough to construct even a full matrix.
- Selector mode `NONE` is not evidence that plugins are ready; it means the
  explicit revision range did not affect marketplace-controlled content.
- Neither a receipt nor selection result changes installed-runtime evidence or
  readiness classifications.

Diagnostics use stable codes, safe relative paths where applicable, and no
private absolute paths.

## 9. Compatibility and migration

- Existing preparation catalogs remain valid.
- Existing callers that omit receipt options observe unchanged
  `prepare-marketplace` and `verify-marketplace` behavior.
- The validation registry may advance to a new schema only if the old generated
  verifier behavior remains explicitly migrated and tested. Prefer adding the
  minimum ownership/control metadata that the selector requires.
- Marketplace stages generated before Stage Two remain verifiable by the
  existing framework path; affected selection is available only after the
  stage is regenerated with the selector.
- No existing public result field changes meaning.
- Generated files remain byte-deterministic across repeated builds.

## 10. Security and integrity requirements

- Reject absolute, drive-relative, parent-traversal, empty, and link-mediated
  paths.
- Do not execute through a shell.
- Do not trust workflow event text as a path, command, plugin ID, or revision
  without strict validation.
- Do not accept a receipt merely because its embedded digest is internally
  consistent; all bound current identities must match.
- Do not allow a changed selector, verifier, registry, runtime catalog, or
  workflow to narrow its own validation set.
- Preserve exact-byte and line-ending protections on hash-bound fixtures and
  generated controls.
- Keep all generated diagnostics and evidence ASCII-safe where required by the
  existing result contract.

## 11. Verification requirements

Implementation is test-first and must provide evidence for all of the following:

1. deterministic receipt bytes and receipt SHA-256;
2. receipt rejection after any marketplace tree, preparation catalog,
   registry, verifier, selector, plugin identity, or artifact identity change;
3. rejection of unknown fields, unsafe paths, malformed digests, duplicate
   plugins, and non-`PASS` receipt states;
4. absence of timestamps and private or machine-specific paths;
5. exact one-plugin and multiple-plugin affected selections;
6. correct delete, rename, copy, shared-control, invalid-revision, shallow
   history, removed-plugin, unmapped-path, and invalid-registry behavior;
7. deterministic selector result and matrix ordering;
8. correct intentional empty-selection workflow behavior;
9. preservation of the three-OS matrix, per-plugin verifier, `fail-fast: false`,
   and aggregate failure semantics;
10. standalone selector and verifier execution without the framework package;
11. unchanged legacy caller behavior when new options are absent;
12. focused marketplace, CLI, result, Git-evidence, and generation tests;
13. the complete generic framework suite under the canonical Windows test
    environment discipline;
14. `git diff --check`; and
15. a final audit proving that no application product or marketplace repository
    artifact was mutated.

Tests use genuine system temporary storage and dedicated disposable roots for
Git, hard-link, filesystem, and packaging work. Environment-only failures are
classified and corrected without changing product behavior before rerunning the
smallest affected regression set.

## 12. Completion and authorization boundary

Stage Two implementation is complete when the public receipt interface,
generated selector, workflow integration, documentation, and all required
verification satisfy this specification.

Completion does not authorize:

- applying regenerated controls to `D:\GitHub\obvious-one-plugins`;
- pushing a branch;
- creating or merging a pull request;
- publishing or replacing a marketplace artifact; or
- changing any plugin's release or runtime status.

Those actions require separately reviewed exact deltas and explicit owner
authorization.
