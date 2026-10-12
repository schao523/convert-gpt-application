# Marketplace Publication Efficiency Stage One Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove proven marketplace-publication repetition while preserving every filesystem, Git, cross-platform, exact-byte, and authorization gate.

**Architecture:** Keep the existing marketplace generator and verification APIs intact. Narrow only the generated GitHub Actions push trigger, document fresh-checkout as the existing combined commit-and-checkout gate, and add contract tests that make the optimized workflow deterministic and reviewable.

**Tech Stack:** Python 3.11+, standard-library `unittest`, generated GitHub Actions YAML, and Markdown operational contracts.

**Spec:** `docs/superpowers/specs/2026-10-12-marketplace-publication-efficiency-stage-one-design.md`

## Global Constraints

- Do not change the meaning or implementation of any marketplace verification gate.
- Preserve deterministic staging, strict SHA-256, exact-byte attributes, link and reparse-point rejection, catalog reconstruction, and three-OS validation.
- Preserve `--commit` as a supported diagnostic and standalone CLI interface.
- Preserve the complete plugin-by-OS matrix, `fail-fast: false`, per-plugin verifier invocation, and aggregate failure job.
- Every framework command continues to emit exactly one complete ASCII-safe `result-schema-v1` document.
- Do not modify any application product, distribution contract, preparation catalog, generated plugin artifact, marketplace artifact, or marketplace repository file.
- Do not mutate `D:\GitHub\obvious-one-plugins`, push, merge, tag, release, or publish.
- Use `python -B` for Python verification commands.

## Review Focus

- A pull-request synchronization event must still run the complete marketplace matrix; Task 1 pins the `pull_request` trigger.
- A feature-branch push must not independently duplicate the matrix, while a `main` push must run it; Task 1 pins `push.branches: [main]`.
- Manual recovery must remain available; Task 1 pins `workflow_dispatch`.
- Removing the documented standalone commit command must not remove commit evidence; Task 2 pins the four expected fresh-checkout gate states and retains the existing Git-evidence regression suite.
- Concise reporting must not discard or rewrite authoritative evidence; Task 2 requires saved complete `result-schema-v1` output, its path and SHA-256, and inspection beyond exit status.

---

### Task 1: Narrow the generated marketplace workflow triggers

**Files:**
- Modify: `tests/framework/test_marketplace_ci.py`
- Modify: `src/obvious_one_plugin_framework/marketplace_ci.py`

**Interfaces:**
- Preserves: `render_validation_workflow() -> str`.
- Produces: canonical workflow bytes triggered by pull requests, pushes to `main`, and manual dispatch.
- Preserves: dynamic registry-driven plugin expansion, the Windows/Linux/macOS matrix, per-plugin verification, and aggregate failure semantics.

- [ ] **Step 1: Add failing workflow-contract tests**

Add these `MarketplaceCiTests` methods:

```python
def test_validation_workflow_uses_pr_main_and_manual_triggers(self) -> None: ...
def test_validation_workflow_preserves_plugin_os_matrix_and_aggregate_gate(self) -> None: ...
def test_validation_workflow_render_is_byte_deterministic(self) -> None: ...
```

The first test asserts the exact trigger block from the approved specification and rejects the old unrestricted `push` block. The second asserts `matrix.plugin`, all three current OS labels, `fail-fast: false`, the existing verifier command, and the aggregate dependency on `validate`. The third compares two UTF-8 encodings returned by separate render calls.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -B -m unittest tests.framework.test_marketplace_ci.MarketplaceCiTests.test_validation_workflow_uses_pr_main_and_manual_triggers tests.framework.test_marketplace_ci.MarketplaceCiTests.test_validation_workflow_preserves_plugin_os_matrix_and_aggregate_gate tests.framework.test_marketplace_ci.MarketplaceCiTests.test_validation_workflow_render_is_byte_deterministic -v`

Expected: the trigger test fails because `_WORKFLOW` still contains unrestricted `push`; preservation and determinism tests pass against the existing behavior.

- [ ] **Step 3: Implement the canonical trigger change**

Change only the `on` block of `_WORKFLOW` in `marketplace_ci.py` to:

```yaml
on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:
```

Do not change jobs, permissions, matrix construction, verifier arguments, or aggregation.

- [ ] **Step 4: Run the focused marketplace CI tests and verify GREEN**

Run: `python -B -m unittest tests.framework.test_marketplace_ci -v`

Expected: PASS.

- [ ] **Step 5: Commit the generator change**

```powershell
git add tests/framework/test_marketplace_ci.py src/obvious_one_plugin_framework/marketplace_ci.py
git commit -m "fix: avoid duplicate marketplace validation runs"
```

### Task 2: Document the optimized evidence sequence

**Files:**
- Modify: `tests/test_documentation_contract.py`
- Modify: `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`

**Interfaces:**
- Preserves: all existing `verify-marketplace` CLI modes.
- Produces: the required publication sequence `filesystem -> index -> local commit -> fresh checkout`.
- Produces: operational guidance for saving complete result evidence while reporting only decision-relevant fields in routine commentary.

- [ ] **Step 1: Add a failing documentation-contract test**

Add:

```python
def test_marketplace_publication_sequence_avoids_redundant_commit_run_and_preserves_evidence(self) -> None: ...
```

Assert that the command reference:

- retains the filesystem, `--index`, and `--fresh-checkout` commands;
- no longer contains the former required command ending in `--commit HEAD --json`;
- states that fresh-checkout success reports `filesystem`, `index`, `commit`, and `fresh_checkout` as `PASS`;
- states that `--commit` remains available for standalone diagnostics;
- requires saving the complete result document below ignored `.tmp` or `dist` storage with its path and SHA-256; and
- reiterates that exit code alone is not evidence.

- [ ] **Step 2: Run the documentation test and verify RED**

Run: `python -B -m unittest tests.test_documentation_contract.DocumentationContractTests.test_marketplace_publication_sequence_avoids_redundant_commit_run_and_preserves_evidence -v`

Expected: FAIL because the reference still lists the standalone commit command and lacks the approved concise-evidence guidance.

- [ ] **Step 3: Update the command reference**

In the local marketplace preparation section:

- remove the standalone `--commit HEAD` invocation from the required sequence;
- explain that fresh-checkout mode resolves `HEAD` and supplies commit plus checkout evidence;
- list the four required `PASS` gate values;
- retain `--commit` as an optional diagnostic interface;
- keep index and fresh-checkout mutually exclusive per invocation; and
- add the approved complete-evidence storage and concise-commentary rules without changing `result-schema-v1`.

- [ ] **Step 4: Run documentation and focused Git-evidence regressions**

Run: `python -B -m unittest tests.test_documentation_contract tests.framework.test_git_evidence tests.framework.test_marketplace_ci -v`

Expected: PASS.

- [ ] **Step 5: Run the complete generic framework suite**

Run: `python -B -m unittest discover -s .\tests\framework -v`

Expected: PASS with no skipped or weakened Stage One coverage.

- [ ] **Step 6: Run repository contract tests and final hygiene checks**

Run: `python -B -m unittest tests.test_documentation_contract tests.test_repo_contract tests.test_agents_contract -v`

Expected: PASS.

Run: `git diff --check`

Expected: no output and exit code 0.

Run: `git status --short` and `git diff --name-only main...HEAD`

Expected: only the Stage One generator, tests, command reference, specification, and plan are present across the feature branch; no application or marketplace artifact path appears.

- [ ] **Step 7: Commit the operational contract update**

```powershell
git add tests/test_documentation_contract.py docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md
git commit -m "docs: streamline marketplace publication verification"
```

- [ ] **Step 8: Record final verification evidence**

Re-run `python -B -m unittest discover -s .\tests\framework -v` and `git diff --check` after the final commit. Report the exact test count, commit IDs, clean/dirty worktree state, and the unchanged marketplace publication state. Do not push or update the marketplace repository.
