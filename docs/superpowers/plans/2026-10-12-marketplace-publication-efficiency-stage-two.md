# Marketplace Publication Efficiency Stage Two Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic identity-bound marketplace filesystem receipts and fail-closed affected-plugin CI selection without weakening any verification gate.

**Architecture:** Keep the preparation catalog and generated validation registry as the shared authority. Add a focused receipt module for canonical evidence and a self-contained generated selector for Git-delta mapping, then integrate both through the existing marketplace API, CLI, generated controls, and workflow.

**Tech Stack:** Python 3.11 standard library, `unittest`, Git, generated GitHub Actions YAML, deterministic JSON, SHA-256.

**Spec:** `docs/superpowers/specs/2026-10-12-marketplace-publication-efficiency-stage-two-design.md`

## Global Constraints

- Receipts carry evidence; they never authorize skipping current SHA-256 calculation, plugin verification commands, Git evidence, or required OS jobs.
- The current validation registry is the sole plugin-ownership authority.
- Any selection ambiguity expands to all registered plugins; an invalid current registry fails.
- Preserve `result-schema-v1`, strict path safety, deterministic bytes, fail-closed behavior, and the existing status vocabulary.
- Preserve the Windows, Ubuntu, and macOS matrix, `fail-fast: false`, standalone verifier invocation, and aggregate failure semantics.
- New standalone marketplace controls use Python 3.11 or newer and the standard library only.
- Do not mutate the marketplace repository, product applications, release versions, or external publication state.
- Use the canonical Windows test environment wrapper for tests that need filesystem, Git, hard-link, atomic-replace, or packaging capabilities.

## Review Focus

- A valid registry with a missing or shallow base revision must select `ALL`, not fail open to a partial matrix; Task 2 pins this behavior.
- Registry, verifier, selector, workflow, runtime-catalog, and exact-byte-policy changes must select `ALL`; Tasks 2 and 4 pin the shared-control boundary.
- Deletes, copies, and renames must evaluate every old and new endpoint, falling back to `ALL` when any endpoint is unmapped; Task 2 pins these cases.
- Receipt output inside the marketplace tree would create a self-referential identity and must be rejected before mutation; Task 3 pins path overlap and transactional preservation.
- Windows newline conversion must not change any hash-bound generated control or fixture; Tasks 1, 3, and 5 pin LF output and branch-range whitespace/hash checks.

---

### Task 1: Canonical marketplace identity and receipt contract

**Files:**
- Create: `src/obvious_one_plugin_framework/marketplace_receipt.py`
- Create: `tests/framework/test_marketplace_receipt.py`
- Modify: `src/obvious_one_plugin_framework/marketplace.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`

**Interfaces:**
- Produces: `build_marketplace_filesystem_receipt(catalog: PreparationCatalog, marketplace: Path, verification: OperationResult) -> dict[str, object]`.
- Produces: `write_marketplace_filesystem_receipt(catalog: PreparationCatalog, marketplace: Path, verification: OperationResult, output: Path) -> ArtifactRecord`.
- Produces: `verify_marketplace_filesystem_receipt(catalog: PreparationCatalog, marketplace: Path, receipt: Path) -> OperationResult`.
- Produces: one shared internal exact tree-identity implementation used by existing marketplace artifact summaries and receipts, excluding `.git` and rejecting links consistently.
- Consumes: existing `PreparationCatalog`, generated registry/artifact identities, `OperationResult`, `ArtifactRecord`, and canonical result path-safety rules.

- [ ] **Step 1: Write failing receipt contract tests**

Add tests that assert:

- the exact closed schema `marketplace-filesystem-verification-receipt-v1`;
- sorted plugin/target records and exact required control keys;
- deterministic LF-terminated ASCII-safe JSON bytes and `receipt_sha256` computed with that field omitted;
- identical inputs produce identical bytes;
- timestamps, absolute paths, host data, and unknown fields are absent or rejected;
- malformed digests, duplicate plugins, unsafe paths, non-`PASS` verification input, and a verification result whose marketplace artifact identity differs are rejected; and
- changing the tree, catalog, registry, verifier, selector, plugin identity, or recorded artifact identity makes validation return `FAIL` with a stable diagnostic.

- [ ] **Step 2: Run the focused tests and verify they fail for the missing module**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument @('-B','-m','unittest','tests.framework.test_marketplace_receipt','-v')
```

Expected: `FAIL` because `marketplace_receipt` and its public functions do not exist.

- [ ] **Step 3: Implement the minimal canonical receipt module and shared identity path**

Implement the three exact public signatures above. Use canonical sorted JSON, SHA-256, transactional replacement, strict closed-schema parsing, link rejection, and safe relative evidence. Require receipt output to be outside the marketplace root so it cannot alter the identity it records. Refactor the existing marketplace tree-summary call to use the same identity calculation without changing its returned aggregate or byte count.

- [ ] **Step 4: Export the public receipt API**

Add the three public functions to `src/obvious_one_plugin_framework/__init__.py`. Do not export private parsing or hashing helpers.

- [ ] **Step 5: Run receipt and existing marketplace identity regressions**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument @('-B','-m','unittest','tests.framework.test_marketplace_receipt','tests.framework.test_marketplace','tests.framework.test_results','-v')
```

Expected: all tests `PASS`, with only pre-existing environment capability skips if applicable.

- [ ] **Step 6: Commit the receipt contract**

```powershell
git add src/obvious_one_plugin_framework/marketplace_receipt.py src/obvious_one_plugin_framework/marketplace.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_marketplace_receipt.py
git commit -m "feat: add marketplace verification receipts"
```

### Task 2: Self-contained affected-plugin selector

**Files:**
- Create: `src/obvious_one_plugin_framework/templates/marketplace/select_marketplace_plugins.py.template`
- Create: `tests/framework/test_marketplace_selection.py`
- Modify: `src/obvious_one_plugin_framework/marketplace_ci.py`
- Modify: `src/obvious_one_plugin_framework/marketplace.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`
- Modify: `tests/framework/test_marketplace_ci.py`

**Interfaces:**
- Produces: `render_marketplace_selector() -> str`.
- Produces generated CLI: `python -B tools/select_marketplace_plugins.py --registry <path> (--base <rev> --head <rev> | --all <reason>) --json`.
- Produces one `result-schema-v1` document whose evidence contains `selection_mode`, sorted `selected_plugins`, resolved revisions when applicable, `changed_path_count`, `changed_paths_sha256`, `fallback_reason`, and `matrix`.
- Consumes: validation-registry schema v2 plugin IDs and target destination paths; no framework import at generated runtime.

- [ ] **Step 1: Write failing standalone-selector tests**

Using disposable Git repositories, assert:

- one destination change selects exactly its owner with mode `AFFECTED`;
- changes to several destinations return their sorted union;
- an empty revision delta returns mode `NONE` and `{"plugin": []}`;
- deletes, copies, and renames consider every endpoint;
- an unmapped endpoint, removed plugin, invalid revision, shallow history, Git error, or ambiguous parse returns `PASS` with mode `ALL` and all sorted plugins when the current registry is valid;
- invalid, duplicate, overlapping, unsafe, or non-v2 current registries return `FAIL` rather than a matrix;
- shared controls select `ALL`, including both runtime catalogs, registry, verifier, selector, workflow, and `.gitattributes`;
- `--all workflow_dispatch` returns all plugins without consulting a revision range;
- selector JSON and changed-record digest are byte-deterministic; and
- the generated script runs from a staged marketplace with the framework package unavailable.

- [ ] **Step 2: Run selector tests and verify they fail because the template and renderer are absent**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument @('-B','-m','unittest','tests.framework.test_marketplace_selection','tests.framework.test_marketplace_ci','-v')
```

Expected: new selector tests `FAIL` for missing interfaces.

- [ ] **Step 3: Implement the standalone selector template**

Parse `git diff --name-status -z --find-renames --find-copies <base> <head> --` without a shell. Validate the closed registry structure and non-overlapping safe destinations before resolving the delta. Use full-matrix fallback codes for every spec-defined ambiguity, but fail if the current registry cannot safely enumerate plugins.

- [ ] **Step 4: Render and stage the selector as a generated control**

Add `render_marketplace_selector()` using package resources. Update `_write_generated_controls` to write `tools/select_marketplace_plugins.py` deterministically. Update `_marketplace_controls_valid` to compare its exact generated bytes, and extend exact-byte attributes to cover all hash-bound generated controls without weakening existing destination coverage.

- [ ] **Step 5: Export the selector renderer and run focused regressions**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument @('-B','-m','unittest','tests.framework.test_marketplace_selection','tests.framework.test_marketplace_ci','tests.framework.test_marketplace','tests.framework.test_git_evidence','-v')
```

Expected: all tests `PASS`.

- [ ] **Step 6: Commit the selector**

```powershell
git add src/obvious_one_plugin_framework/templates/marketplace/select_marketplace_plugins.py.template src/obvious_one_plugin_framework/marketplace_ci.py src/obvious_one_plugin_framework/marketplace.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_marketplace_selection.py tests/framework/test_marketplace_ci.py
git commit -m "feat: select affected marketplace plugins"
```

### Task 3: Receipt API and CLI integration

**Files:**
- Modify: `src/obvious_one_plugin_framework/marketplace.py`
- Modify: `src/obvious_one_plugin_framework/cli.py`
- Modify: `tests/framework/test_marketplace.py`
- Modify: `tests/framework/test_cli.py`

**Interfaces:**
- Consumes: Task 1 receipt functions and Task 2 generated selector control.
- Produces: `verify_marketplace(..., receipt_output: Path | None = None) -> OperationResult` while preserving all existing call behavior when omitted.
- Produces: `verify-marketplace --receipt-output <path>`.
- Produces: `verify-marketplace-receipt --catalog <path> --marketplace <path> --receipt <path> --json`.

- [ ] **Step 1: Write failing API and CLI tests**

Add tests proving:

- a passing filesystem verification with `receipt_output` writes and revalidates one receipt, then reports it as an artifact;
- a failed filesystem gate writes no receipt and preserves any existing destination bytes;
- output equal to, inside, or containing the marketplace root is rejected before mutation;
- Git modes retain their existing gates when receipt output is requested;
- omission of the new option yields the exact existing result shape and behavior;
- `verify-marketplace-receipt` emits exactly one ASCII-safe `result-schema-v1` document and correct exit status for valid and invalid receipts; and
- unknown arguments and mutually exclusive Git modes remain rejected through the existing CLI error contract.

- [ ] **Step 2: Run the focused API and CLI tests and verify the new cases fail**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument @('-B','-m','unittest','tests.framework.test_marketplace','tests.framework.test_cli','-v')
```

Expected: new receipt integration tests `FAIL`; unrelated existing cases remain green.

- [ ] **Step 3: Integrate receipt production after successful verification**

Extend `verify_marketplace` with the exact optional parameter. Write only after all requested gates pass, revalidate the written receipt, and append its safe artifact record. A receipt failure makes the operation fail with a stable diagnostic and cannot replace pre-existing output.

- [ ] **Step 4: Add the independent receipt-validation command**

Extend `_parser()` and the marketplace dispatch branch in `cli.py` with the exact command and arguments above. Preserve one-result output behavior and existing exception-to-result semantics.

- [ ] **Step 5: Run API, CLI, result, and Git-evidence regressions**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument @('-B','-m','unittest','tests.framework.test_marketplace_receipt','tests.framework.test_marketplace','tests.framework.test_cli','tests.framework.test_results','tests.framework.test_git_evidence','-v')
```

Expected: all tests `PASS`.

- [ ] **Step 6: Commit receipt integration**

```powershell
git add src/obvious_one_plugin_framework/marketplace.py src/obvious_one_plugin_framework/cli.py tests/framework/test_marketplace.py tests/framework/test_cli.py
git commit -m "feat: expose marketplace receipt verification"
```

### Task 4: Generated workflow selection and aggregate safety

**Files:**
- Modify: `src/obvious_one_plugin_framework/marketplace_ci.py`
- Modify: `tests/framework/test_marketplace_ci.py`
- Modify: `tests/framework/test_marketplace_selection.py`

**Interfaces:**
- Consumes: Task 2 generated selector and its `matrix`, `selection_mode`, and result status.
- Produces: generated workflow matrix job outputs `matrix`, `selection_mode`, and `selection_status`.
- Preserves: the exact per-plugin verifier command and three-OS validation matrix for every selected plugin.

- [ ] **Step 1: Write failing workflow-contract tests**

Assert that the rendered workflow:

- retains `pull_request`, `push.branches: [main]`, and `workflow_dispatch`;
- checks out sufficient Git history for explicit revision resolution;
- invokes the selector with pull-request base/head, push before/head, and manual `--all workflow_dispatch` inputs without shell interpolation into commands;
- passes only the selector's validated matrix into the validation strategy;
- skips validation only for mode `NONE`;
- retains `fail-fast: false`, the three OS values, and the exact standalone verifier command;
- makes aggregate success conditional on either successful selected validation or an intentional `NONE`; and
- fails aggregation for selector failure, unexpected validation skip, or any selected validation failure.

- [ ] **Step 2: Run workflow tests and verify failure against the Stage One workflow**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument @('-B','-m','unittest','tests.framework.test_marketplace_ci','tests.framework.test_marketplace_selection','-v')
```

Expected: new workflow assertions `FAIL`; existing Stage One trigger assertions remain green.

- [ ] **Step 3: Render the selector-driven workflow**

Use an Ubuntu matrix-discovery job with full checkout history and a Python orchestration step that invokes the generated selector as an argument vector, parses its one result document, and writes validated compact outputs to `GITHUB_OUTPUT`. Do not duplicate ownership mapping in YAML.

- [ ] **Step 4: Implement explicit zero-selection and aggregate handling**

Guard the validation job with the selector mode. Make the aggregate job use `always()` and inspect both selection and validation outcomes so that only a valid `NONE` permits a skipped validation job.

- [ ] **Step 5: Run workflow, standalone control, and deterministic preparation tests**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument @('-B','-m','unittest','tests.framework.test_marketplace_ci','tests.framework.test_marketplace_selection','tests.framework.test_marketplace','tests.framework.test_plugin_onboarding_marketplace','-v')
```

Expected: all tests `PASS`; repeated preparation produces byte-identical generated controls.

- [ ] **Step 6: Commit workflow integration**

```powershell
git add src/obvious_one_plugin_framework/marketplace_ci.py tests/framework/test_marketplace_ci.py tests/framework/test_marketplace_selection.py
git commit -m "feat: narrow marketplace validation matrix safely"
```

### Task 5: Documentation, compatibility, and complete verification

**Files:**
- Modify: `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`
- Modify: `tests/test_documentation_contract.py`
- Modify: `tests/framework/README.md`
- Modify if required by installed packaging: `pyproject.toml`

**Interfaces:**
- Consumes: Tasks 1–4 public commands, receipt schema, selector status, and workflow behavior.
- Produces: authoritative operational guidance that distinguishes compact evidence reuse from verification bypass and affected selection from readiness.

- [ ] **Step 1: Write failing documentation and package-resource contract tests**

Add assertions that the command reference documents:

- receipt production and independent validation commands;
- safe output placement and transactional behavior;
- exact receipt identity and failure semantics;
- selector `AFFECTED`, `ALL`, and `NONE` meanings;
- conservative fallback and shared-control rules;
- preserved complete evidence and three-OS verification; and
- the unchanged publication authorization boundary.

Add a resource test proving both standalone templates are installed package resources.

- [ ] **Step 2: Run documentation and package-resource tests and verify they fail**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument @('-B','-m','unittest','tests.test_documentation_contract','tests.framework.test_marketplace_ci','-v')
```

Expected: new documentation assertions `FAIL` before the guide is updated.

- [ ] **Step 3: Document the Stage Two operational contract**

Update the command reference with exact command forms, receipt storage guidance, interpretation of selector modes, full-matrix fallback conditions, empty-selection behavior, evidence preservation, and explicit non-publication scope. Update the framework test README only with new focused-suite routing. Change packaging configuration only if the new template is not already included by the existing resource rule.

- [ ] **Step 4: Run focused documentation and marketplace suites**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument @('-B','-m','unittest','tests.test_documentation_contract','tests.framework.test_marketplace_receipt','tests.framework.test_marketplace_selection','tests.framework.test_marketplace_ci','tests.framework.test_marketplace','tests.framework.test_cli','-v')
```

Expected: all tests `PASS`.

- [ ] **Step 5: Commit documentation**

```powershell
git add docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md tests/test_documentation_contract.py tests/framework/README.md pyproject.toml
git commit -m "docs: explain marketplace receipts and CI selection"
```

- [ ] **Step 6: Run the complete generic framework suite**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument @('-B','-m','unittest','discover','-s','.\tests\framework','-v')
```

Expected: all applicable tests `PASS`; capability-dependent skips are reported precisely.

- [ ] **Step 7: Run repository documentation and contract suites**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 -Executable python -CommandArgument @('-B','-m','unittest','tests.test_documentation_contract','tests.test_repo_contract','tests.test_agents_contract','-v')
```

Expected: all tests `PASS`.

- [ ] **Step 8: Verify deterministic generation and Git hygiene**

Prepare the same marketplace fixture twice in separate disposable roots and compare the receipt, selector, verifier, registry, and workflow bytes. Then run:

```powershell
git diff --check main...HEAD
git status --short
```

Expected: deterministic bytes, no whitespace errors, and only intentional tracked changes.

- [ ] **Step 9: Audit scope and record evidence states**

Confirm that no file below `applications/` changed and no external marketplace repository was mutated. Record live GitHub Actions execution and marketplace adoption as `NOT VERIFIED` / `NOT PERFORMED` unless separately authorized and directly observed.

- [ ] **Step 10: Request whole-branch review before completion**

Use a fresh reviewer to inspect the complete branch against the approved specification, with special attention to receipt self-reference, selector fallback, rename/delete parsing, empty-matrix aggregation, Windows exact bytes, and unchanged legacy behavior. Resolve material findings and rerun the smallest affected set followed by the complete required verification.
