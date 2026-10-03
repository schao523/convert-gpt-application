# Obvious One Target-Aware Marketplace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Obvious One marketplace preparation and verification support Codex-only Plugin Builder 0.1.3 while preserving dual-runtime Cool Plugin Design Assistant publication.

**Architecture:** Preparation-catalog schema v2 models Codex and OpenClaw as explicit `PreparationTarget` values. Every build, catalog, registry, verifier, Git-evidence, and exact-byte operation enumerates only applicable targets; schema v1 is translated into the same internal model for compatibility.

**Tech Stack:** Python 3.11+, standard-library `dataclasses`, `json`, `pathlib`, `subprocess`, and `unittest`; deterministic repository marketplace framework and generated verifier template.

**Spec:** `docs/superpowers/specs/2026-10-03-obvious-one-target-aware-marketplace-design.md`

## Global Constraints

- Plugin Builder 0.1.3 is Codex-only; OpenClaw and ClawHub are `NOT APPLICABLE`.
- Cool Plugin Design Assistant remains applicable to both Codex and OpenClaw.
- Schema-v1 marketplace catalogs retain their exact existing meaning.
- New or modified marketplace catalogs use schema v2.
- Preserve transactional staging, safe paths, link/reparse rejection, exact hashes, and deterministic bytes.
- Do not mutate `D:\GitHub\obvious-one-plugins`, push, tag, publish, create a release, submit to ClawHub, or submit to the OpenAI directory.
- Preserve the unrelated untracked Vibe Coding Designer files.
- Use `python -B` for every Python command.

## Review Focus

- A `not_applicable` target already present in the baseline catalog must block without deleting it; Task 2 owns the test.
- A command that names a non-applicable target must be rejected instead of silently skipped; Task 3 owns the test.
- A target-specific path duplicated or nested under any other applicable destination must fail at catalog load; Task 1 owns the test.
- Git evidence and exact-byte attributes must contain no phantom OpenClaw scope for Plugin Builder; Task 4 owns the test.
- Schema-v1 fixtures and existing dual-runtime product tests must retain identical observable behavior; Tasks 1 and 5 own the tests.

---

### Task 1: Parse and validate preparation-catalog schema v2

**Files:**
- Modify: `src/obvious_one_plugin_framework/marketplace.py`
- Modify: `tests/framework/test_marketplace.py`
- Modify: `applications/cool-plugin-design-assistant/tests/test_marketplace_release.py`
- Modify: `applications/vibe-coding-designer/tests/test_marketplace_release.py`

**Interfaces:**
- Produces: `PreparationTarget(mode: str, destination: str | None)`.
- Produces: `PreparationEntry(application, contract, codex, openclaw)`.
- Produces: `PreparationEntry.target(name: str) -> PreparationTarget` and `PreparationEntry.applicable_targets() -> tuple[tuple[str, PreparationTarget], ...]`.
- Preserves: `load_preparation_catalog(path: Path, repository_root: Path) -> PreparationCatalog`.

- [ ] **Step 1: Add failing schema-v2 model tests**

Add tests named:

```python
def test_v2_catalog_accepts_codex_only_and_dual_runtime_targets(): ...
def test_v2_target_shapes_and_no_applicable_targets_are_rejected(): ...
def test_v2_destinations_are_unique_safe_and_non_overlapping_across_targets(): ...
def test_v1_catalog_translates_to_two_targets_without_behavior_change(): ...
def test_codex_only_target_requires_disabled_clawhub(): ...
```

Assert the exact modes/destinations and the diagnostics fixed by the spec.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -B -m unittest tests.framework.test_marketplace applications.cool-plugin-design-assistant.tests.test_marketplace_release applications.vibe-coding-designer.tests.test_marketplace_release -v`

Expected: the new schema-v2 tests fail because `targets` and `PreparationTarget` are unsupported; existing schema-v1 tests still describe the compatibility baseline.

- [ ] **Step 3: Implement the internal target model and schema dispatch**

Support schema versions 1 and 2. Parse v1 shared fields into two targets. Parse v2 exact `targets` keys and modes, validate destinations globally, require at least one applicable target, and reject enabled ClawHub when OpenClaw is not applicable.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run the Step 2 command. Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/obvious_one_plugin_framework/marketplace.py tests/framework/test_marketplace.py applications/cool-plugin-design-assistant/tests/test_marketplace_release.py applications/vibe-coding-designer/tests/test_marketplace_release.py
git commit -m "feat: model target-aware marketplace catalogs"
```

### Task 2: Make staging target-aware and transactional

**Files:**
- Modify: `src/obvious_one_plugin_framework/marketplace.py`
- Modify: `tests/framework/test_marketplace.py`

**Interfaces:**
- Consumes: `PreparationEntry.applicable_targets()` from Task 1.
- Produces: target-specific build and verify-existing orchestration used by catalog and registry generation.

- [ ] **Step 1: Add failing preparation tests**

```python
def test_codex_only_build_emits_no_openclaw_artifact(): ...
def test_dual_runtime_build_still_emits_both_artifacts(): ...
def test_not_applicable_catalog_entry_blocks_without_deleting_or_replacing_output(): ...
def test_repeated_target_aware_preparation_is_byte_identical(): ...
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -B -m unittest tests.framework.test_marketplace -v`

Expected: Codex-only preparation attempts to build or address an OpenClaw destination.

- [ ] **Step 3: Implement per-target build and verify-existing paths**

Split the current combined `_build_entry` and `_verify_existing_entry` behavior by target. Enumerate only applicable destinations for committed-byte materialization, delta calculation, and artifact replacement. Before generating controls, block when a not-applicable target already has a runtime-catalog entry.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run the Step 2 command. Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/obvious_one_plugin_framework/marketplace.py tests/framework/test_marketplace.py
git commit -m "feat: prepare only applicable marketplace targets"
```

### Task 3: Generate and verify asymmetric runtime catalogs

**Files:**
- Modify: `src/obvious_one_plugin_framework/marketplace_ci.py`
- Modify: `src/obvious_one_plugin_framework/marketplace.py`
- Modify: `src/obvious_one_plugin_framework/templates/marketplace/verify_marketplace.py.template`
- Modify: `tests/framework/test_marketplace_ci.py`
- Modify: `tests/framework/test_marketplace.py`

**Interfaces:**
- Consumes: target-aware `PreparationCatalog` from Task 1.
- Produces: validation registry schema v2 with `targets.codex` and `targets.openclaw` records.
- Preserves: one result-schema-v1 document from the generated verifier.

- [ ] **Step 1: Add failing registry and verifier tests**

```python
def test_registry_accepts_codex_only_and_dual_runtime_plugin_sets(): ...
def test_registry_marks_excluded_target_not_applicable_without_path_or_artifact(): ...
def test_missing_unexpected_duplicate_wrong_path_or_wrong_version_target_entry_fails(): ...
def test_command_for_not_applicable_target_is_rejected(): ...
def test_generated_verifier_runs_only_applicable_targets(): ...
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -B -m unittest tests.framework.test_marketplace_ci tests.framework.test_marketplace -v`

Expected: registry construction fails on unequal catalog sets and the template requires both paths.

- [ ] **Step 3: Implement target-aware catalogs and registry schema v2**

Update only applicable build records, preserve unrelated runtime-catalog metadata, require exact per-target plugin sets, record target state/path/artifact independently, and require command targets to be applicable.

- [ ] **Step 4: Update the standalone verifier template**

Validate exact artifacts, manifests, ClawHub, and commands only for target records with `state: "STATICALLY VERIFIED"`; require excluded targets to be exactly `{"state": "NOT APPLICABLE"}`.

- [ ] **Step 5: Run the focused tests and verify GREEN**

Run the Step 2 command. Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/obvious_one_plugin_framework/marketplace.py src/obvious_one_plugin_framework/marketplace_ci.py src/obvious_one_plugin_framework/templates/marketplace/verify_marketplace.py.template tests/framework/test_marketplace.py tests/framework/test_marketplace_ci.py
git commit -m "feat: verify asymmetric marketplace targets"
```

### Task 4: Scope Git evidence and exact-byte policy to applicable targets

**Files:**
- Modify: `src/obvious_one_plugin_framework/marketplace.py`
- Modify: `tests/framework/test_marketplace.py`
- Modify: `tests/framework/test_git_evidence.py`

**Interfaces:**
- Consumes: applicable destination enumeration from Task 1.
- Preserves: `verify_git_evidence(repository, scopes, ...)` and `exact_byte_attributes(scopes)`.

- [ ] **Step 1: Add failing target-aware Git tests**

```python
def test_codex_only_index_commit_and_fresh_checkout_use_only_codex_scope(): ...
def test_exact_byte_attributes_omit_not_applicable_destination(): ...
def test_dual_runtime_git_evidence_still_checks_both_scopes(): ...
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -B -m unittest tests.framework.test_marketplace tests.framework.test_git_evidence -v`

Expected: marketplace verification still constructs two scopes per application.

- [ ] **Step 3: Route applicable destinations into Git and attribute checks**

Do not weaken `verify_git_evidence`; change only the marketplace caller's scope construction and generated `.gitattributes` merge.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run the Step 2 command. Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/obvious_one_plugin_framework/marketplace.py tests/framework/test_marketplace.py tests/framework/test_git_evidence.py
git commit -m "fix: scope marketplace Git evidence by target"
```

### Task 5: Migrate the Obvious One preparation catalog

**Files:**
- Modify: `marketplaces/obvious-one.json`
- Modify: `tests/test_application_config.py`
- Modify: `applications/plugin-builder/tests/test_conversion_contract.py`
- Modify: `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`
- Modify: `docs/GPT_TO_PLUGIN_USER_GUIDE.md`

**Interfaces:**
- Consumes: schema-v2 catalog loader and target semantics from Tasks 1–4.
- Produces: dual-runtime entries for existing products and Cool Plugin Design Assistant; Codex-only entry for Plugin Builder.

- [ ] **Step 1: Add failing repository contract tests**

```python
def test_obvious_one_catalog_declares_plugin_builder_codex_only(): ...
def test_design_assistant_remains_dual_runtime(): ...
def test_all_cataloged_target_destinations_match_application_identity(): ...
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -B -m unittest tests.test_application_config applications.plugin-builder.tests.test_conversion_contract -v`

Expected: Plugin Builder is absent and the catalog is schema v1.

- [ ] **Step 3: Convert the catalog to schema v2 and add Plugin Builder**

Keep the three existing products dual-runtime `build`; add Plugin Builder with Codex `build` at `plugins/plugin-builder` and OpenClaw `not_applicable`.

- [ ] **Step 4: Update operational documentation**

Document schema-v1 compatibility, schema-v2 target records, asymmetric catalogs, `NOT APPLICABLE`, and the unchanged publication-authorization boundary.

- [ ] **Step 5: Run the focused tests and verify GREEN**

Run the Step 2 command. Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add marketplaces/obvious-one.json tests/test_application_config.py applications/plugin-builder/tests/test_conversion_contract.py docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md docs/GPT_TO_PLUGIN_USER_GUIDE.md
git commit -m "chore: register Plugin Builder for Codex marketplace"
```

### Task 6: Complete local verification and non-destructive marketplace proof

**Files:**
- Modify only if observed evidence changes: `applications/plugin-builder/docs/runtime-compatibility.md`
- Generated only below ignored `.tmp/`: marketplace stages and Git-evidence repositories

**Interfaces:**
- Consumes: complete implementation from Tasks 1–5.
- Produces: deterministic local preparation/verification evidence; no published artifact.

- [ ] **Step 1: Run complete framework and affected product suites**

```powershell
python -B -m unittest discover -s tests/framework -v
python -B -m unittest discover -s applications/plugin-builder/tests -v
python -B -m unittest discover -s applications/cool-plugin-design-assistant/tests -v
python -B -m unittest tests.test_application_config tests.test_agents_contract tests.test_workbench_handoff_interoperability -v
```

Expected: all applicable tests PASS; only documented platform skips remain.

- [ ] **Step 2: Run both repository verifiers**

```powershell
python -B scripts/verify_extraction.py --application plugin-builder
python -B scripts/verify_extraction.py --application cool-plugin-design-assistant
```

Expected: both result documents report PASS for applicable local gates.

- [ ] **Step 3: Prepare twice from the read-only current Obvious One baseline**

Use two unused ignored output roots and run `prepare-marketplace` twice. Compare tree identities, complete member manifests, runtime catalogs, and validation registries. Expected: byte-identical stages; Plugin Builder appears only in the Codex catalog/tree; Cool Plugin Design Assistant appears in both.

- [ ] **Step 4: Verify filesystem and external Git evidence**

Run `verify-marketplace` on the stage, then in an external disposable Git repository run `--index`, `--commit HEAD`, and `--fresh-checkout`. Expected: every requested gate PASS and no marketplace checkout mutation.

- [ ] **Step 5: Audit repository boundaries**

```powershell
git diff --check
git status --short
git log --oneline --decorate -12
```

Expected: only planned target-aware changes are committed; the unrelated Vibe files remain untracked and untouched.

- [ ] **Step 6: Record evidence only if observed results differ**

Update the runtime-compatibility document with exact commands/counts only when needed, rerun its owning contract tests, and commit with `docs: record target-aware marketplace evidence`.

## Completion report

Report the approved target topology, schema compatibility, test and verifier results, deterministic stage identities, exact unverified installed-runtime gates, Git state, marketplace mutation state, and publication state. The final state must remain `NOT_PERFORMED` for apply, push, merge, OpenAI-directory submission, GitHub Release, tag, and ClawHub publication.
