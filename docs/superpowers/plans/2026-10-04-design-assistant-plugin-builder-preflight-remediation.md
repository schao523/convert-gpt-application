# Design Assistant and Plugin Builder Preflight Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind Design Assistant chat handoff packaging to the deterministic final ZIP and make Plugin Builder reject predictable manifest, Skill, reference, membership, and requirement-path defects before producing an approvable W1 plan.

**Architecture:** Extend the shared Workbench handoff normalization report with explicit input/output profile evidence and make the Design Assistant chat contract depend on that digest-bound operation. Add one shared Plugin Builder proposed-tree materializer used by planning and candidate construction; planning runs it in an isolated temporary directory and validates the resulting complete plugin tree before hashing W1.

**Tech Stack:** Python 3.11+, standard-library `dataclasses`, `hashlib`, `json`, `pathlib`, `tempfile`, and `zipfile`; `unittest`; repository `plugin_authoring` and `workbench_handoff` APIs; Markdown Skill contracts; deterministic ZIP builders.

**Spec:** `docs/superpowers/specs/2026-10-04-design-assistant-plugin-builder-preflight-remediation-design.md`

## Global Constraints

- Preserve `WORKBENCH_HANDOFF_V1_1`, exact requirement `id`, `source`, `verbatim`, and update `change` values.
- Preserve strict SHA-256 checks, source bytes, one semantic authority, update baseline identity, and deterministic output.
- Plugin Builder runtime scope remains exactly `OPENAI_ONLY_PHASE_ONE`.
- W1 remains the only approval permitting candidate mutation; W2 remains the only approval permitting final packaging.
- Planning preflight may write only below a temporary directory and must not create or modify `candidate/`.
- Unknown, ambiguous, incomplete, or conflicting authority remains fail-closed.
- Do not infer approval, requirement text, rights, baseline identity, reference ownership, or removal authority.
- Do not add a network dependency, MCP server, credential, database, RAG system, or external service.
- Preserve the unrelated untracked Vibe Coding Designer files.
- Use `python -B` for Python commands so verification does not create `__pycache__` artifacts.
- No dependency installation, Git push, tag, release, marketplace mutation, directory submission, or publication.

## Review Focus

- A successful normalization report whose output digest does not match the returned ZIP must fail and leave no purported successful output; Task 1 owns the test.
- A plan with both incomplete manifest metadata and an escaping Markdown link must return both diagnostics in stable order before W1; Task 3 owns the test.
- An update preflight must validate the overlaid final tree while preserving the baseline and without treating planned removal as owner authorization; Task 4 owns the test.
- Two Skill-local copies sourced from the same professional reference must require an explicit reference-ownership rationale; Task 4 owns the test.
- Temporary preflight failure must preserve an existing candidate and remove every `.plan-preflight-*` directory; Task 3 owns the test.

---

### Task 1: Bind Design Assistant chat packaging to the final normalized ZIP

**Files:**
- Modify: `src/obvious_one_plugin_framework/workbench_handoff/normalization.py`
- Modify: `applications/cool-plugin-design-assistant/scripts/cool_plugin_design_assistant.py`
- Modify: `applications/cool-plugin-design-assistant/skills/creating-application-plugin-design-specifications/SKILL.md`
- Modify: `applications/cool-plugin-design-assistant/skills/creating-application-plugin-design-specifications/references/workbench-handoff-contract.md`
- Modify: `applications/cool-plugin-design-assistant/tests/test_tools.py`
- Modify: `applications/cool-plugin-design-assistant/tests/test_skill_contracts.py`
- Modify: `tests/test_workbench_handoff_interoperability.py`

**Interfaces:**
- Consumes: `normalize_handoff_archive(source, destination_root, normalized_zip, *, runtime_scope) -> HandoffNormalizationOutcome`.
- Produces: normalization reports containing `input_profile`, `output_profile`, `source_archive_sha256`, and `output_archive_sha256`; `output_profile` is `WORKBENCH_HANDOFF_V1_1` only for a successful canonical output.

- [ ] **Step 1: Write the failing result-binding tests**

Add `test_normalization_report_binds_input_output_profiles_and_final_zip_digest` to `test_tools.py`. Assert that the report:

```python
self.assertEqual(report["input_profile"], "COOL_DESIGN_ASSISTANT_FULL_V1")
self.assertEqual(report["output_profile"], "WORKBENCH_HANDOFF_V1_1")
self.assertEqual(report["source_archive_sha256"], sha256(source.read_bytes()).hexdigest())
self.assertEqual(report["output_archive_sha256"], sha256(output.read_bytes()).hexdigest())
```

Add a digest-mismatch test by substituting a normalization outcome whose reported output digest differs from the produced destination bytes. Assert `status == "FAIL"`, diagnostic `handoff.output_archive_sha256_mismatch`, no successful output profile, and no returned destination ZIP.

- [ ] **Step 2: Write the failing chat-routing contract test**

Extend `test_skill_contracts.py` with `test_handoff_packaging_requires_deterministic_digest_bound_normalization`. Require the Skill and handoff contract to name `normalize-handoff-package`, prohibit manual construction of the canonical pair, require final-ZIP SHA-256 equality and full canonical validation, and require `HANDOFF BLOCKED` when deterministic execution is unavailable.

- [ ] **Step 3: Run the focused tests and verify RED**

Run:

```powershell
python -B -m unittest applications.cool-plugin-design-assistant.tests.test_tools applications.cool-plugin-design-assistant.tests.test_skill_contracts -v
```

Expected: FAIL because the report exposes only `profile`, does not detect a post-operation digest mismatch at the product boundary, and the chat Skill does not route packaging through the command.

- [ ] **Step 4: Extend the shared report contract**

Change `_report(...) -> dict[str, Any]` and `_outcome(...) -> HandoffNormalizationOutcome` in `normalization.py` so every result retains `input_profile`; successful results also set `output_profile` to `WORKBENCH_HANDOFF_V1_1`, while failed or blocked results set it to `None`. Retain the existing `profile` key as a compatibility alias during this patch release.

- [ ] **Step 5: Verify the delivered archive digest in the product wrapper**

In `normalize_handoff_package(...) -> dict[str, Any]`, after a reported `PASS`, calculate SHA-256 from `destination_path.read_bytes()` and compare it with `outcome.output_archive_sha256`. On mismatch, remove only the newly created destination, return structured `FAIL` with `handoff.output_archive_sha256_mismatch`, clear output identity fields, and do not report a ready gate. On equality, re-open the ZIP, require both canonical root authorities, and report the exact digest.

- [ ] **Step 6: Strengthen the chat-facing Skill contract**

Update the specification Skill and handoff reference so chat-mode transformation must invoke `normalize-handoff-package`, return its structured digest-bound result, never manually synthesize canonical authorities, and stop as `HANDOFF BLOCKED` if deterministic execution or final-archive validation is unavailable.

- [ ] **Step 7: Extend the cross-product digest assertion**

In `test_workbench_handoff_interoperability.py`, make `_produce(...)` assert that the report output profile is canonical and the output digest equals the bytes passed directly into Plugin Builder.

- [ ] **Step 8: Run focused tests and verify GREEN**

Run:

```powershell
python -B -m unittest applications.cool-plugin-design-assistant.tests.test_tools applications.cool-plugin-design-assistant.tests.test_skill_contracts tests.test_workbench_handoff_interoperability -v
```

Expected: all tests PASS; malformed or digest-mismatched output is not returned as successful.

- [ ] **Step 9: Commit Task 1**

```powershell
git add src/obvious_one_plugin_framework/workbench_handoff/normalization.py applications/cool-plugin-design-assistant/scripts/cool_plugin_design_assistant.py applications/cool-plugin-design-assistant/skills/creating-application-plugin-design-specifications applications/cool-plugin-design-assistant/tests/test_tools.py applications/cool-plugin-design-assistant/tests/test_skill_contracts.py tests/test_workbench_handoff_interoperability.py
git commit -m "fix: bind handoff chat output to normalized zip"
```

---

### Task 2: Create one proposed-tree materialization boundary

**Files:**
- Create: `applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/candidate.py`
- Test: `applications/plugin-builder/tests/test_create_candidate.py`

**Interfaces:**
- Consumes: canonical plan/proposal dictionaries, workspace-relative approved source paths, and `plugin_authoring` materialization APIs.
- Produces: `agent_yaml(skill: dict[str, Any]) -> bytes` and `materialize_proposed_tree(proposal: dict[str, Any], workspace_root: Path, destination: Path) -> None` for create operations; update overlay support is added in Task 4.

- [ ] **Step 1: Add a failing parity test**

Add `test_shared_materializer_matches_created_candidate_before_control_manifest` to `test_create_candidate.py`. Materialize the approved create plan through the wished-for `materialize_proposed_tree`, build the candidate normally, and assert byte equality for every member except `PLUGIN-BUILDER-MANIFEST.json`.

- [ ] **Step 2: Run the parity test and verify RED**

Run:

```powershell
python -B -m unittest applications.plugin-builder.tests.test_create_candidate.CreateCandidateTests.test_shared_materializer_matches_created_candidate_before_control_manifest -v
```

Expected: ERROR because `plugin_builder_core.proposed_tree` does not exist.

- [ ] **Step 3: Implement the shared create materializer**

Create `proposed_tree.py` with:

```python
def agent_yaml(skill: dict[str, Any]) -> bytes: ...

def materialize_proposed_tree(
    proposal: dict[str, Any],
    workspace_root: Path,
    destination: Path,
) -> None: ...
```

For `operation == "create"`, call `plugin_authoring.materialize_files`, generate each declared Skill's `agents/openai.yaml`, and call `plugin_authoring.materialize_manifest_pair`. Reject unsupported operations with `PluginAuthoringError("proposal_operation_unsupported")`.

- [ ] **Step 4: Refactor create candidate construction to use the shared boundary**

Remove `_agent_yaml` from `candidate.py`, import the two new functions, and replace its recipe/agent/manifest materialization block with `materialize_proposed_tree(plan, root, stage)`. Keep candidate manifest generation, W1 binding, validation, transactional replacement, and diagnostics unchanged.

- [ ] **Step 5: Run create-candidate tests and verify GREEN**

Run:

```powershell
python -B -m unittest applications.plugin-builder.tests.test_create_candidate -v
```

Expected: all tests PASS and repeated create output remains byte-identical.

- [ ] **Step 6: Commit Task 2**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py applications/plugin-builder/scripts/plugin_builder_core/candidate.py applications/plugin-builder/tests/test_create_candidate.py
git commit -m "refactor: share proposed plugin tree materialization"
```

---

### Task 3: Fail manifest and reference defects before W1

**Files:**
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/implementation_plan.py`
- Modify: `applications/plugin-builder/tests/test_planning_workflow.py`

**Interfaces:**
- Consumes: `materialize_proposed_tree(...)` from Task 2 and `plugin_authoring.validate_plugin_tree(root)`.
- Produces: `preflight_proposed_tree(proposal: dict[str, Any], workspace_root: Path) -> tuple[str, ...]`, returning stable `plan.preflight.<validation-code>:<path>[:<detail>]` diagnostics without persistent filesystem mutation.

- [ ] **Step 1: Write the failing manifest-completeness regression**

Add `test_plan_preflight_rejects_missing_author_and_interface_before_w1`. Remove `author` and `extensions.com.openai.interface` from the root manifest recipe, run `plan`, and assert:

- return code `3`;
- manifest diagnostics include `portable_manifest_required_key_missing` or the more specific portable author/interface diagnostics;
- no implementation plan is written;
- session remains before an approvable W1; and
- `candidate/` does not exist.

- [ ] **Step 2: Write the failing escaping-reference regression**

Add `test_plan_preflight_rejects_escaping_skill_reference_before_w1`. Replace a valid Skill link with `../../resources/Reference.md`; assert a `reference_path_invalid` preflight diagnostic, no plan identity, and no candidate mutation.

- [ ] **Step 3: Write the failing combined-error and cleanup regression**

Add `test_plan_preflight_aggregates_static_failures_and_cleans_temporary_tree`. Combine the missing manifest metadata and escaping link. Pre-create a sentinel `candidate/owner.txt`, run `plan`, and assert both diagnostics appear in sorted order, the sentinel is unchanged, and no `.plan-preflight-*` directory remains.

- [ ] **Step 4: Run the three tests and verify RED**

Run:

```powershell
python -B -m unittest applications.plugin-builder.tests.test_planning_workflow.PlanningWorkflowTests.test_plan_preflight_rejects_missing_author_and_interface_before_w1 applications.plugin-builder.tests.test_planning_workflow.PlanningWorkflowTests.test_plan_preflight_rejects_escaping_skill_reference_before_w1 applications.plugin-builder.tests.test_planning_workflow.PlanningWorkflowTests.test_plan_preflight_aggregates_static_failures_and_cleans_temporary_tree -v
```

Expected: FAIL because planning currently validates neither the complete materialized manifest nor Markdown path confinement.

- [ ] **Step 5: Implement non-mutating create preflight**

Add:

```python
def preflight_proposed_tree(
    proposal: dict[str, Any],
    workspace_root: Path,
) -> tuple[str, ...]: ...
```

Use `TemporaryDirectory(dir=workspace_root, prefix=".plan-preflight-")`, materialize into its child `plugin`, run `validate_plugin_tree`, and convert each `ValidationIssue` to a stable plan diagnostic. Catch `PluginAuthoringError` and `OSError` as stable preflight diagnostics. Never catch and discard validation failures.

- [ ] **Step 6: Invoke preflight before plan hashing**

In `compile_plan(...)`, call preflight only after proposal structure, file recipes, paths, source files, Skill declarations, and expected-member shapes are safe to materialize. Append its complete diagnostics to the existing error collection before the `if errors` return. Do not write `implementation-plan.json` or update W1 identity on failure.

- [ ] **Step 7: Run planning and create suites and verify GREEN**

Run:

```powershell
python -B -m unittest applications.plugin-builder.tests.test_planning_workflow applications.plugin-builder.tests.test_create_candidate -v
```

Expected: all tests PASS; combined defects appear in one deterministic result before W1.

- [ ] **Step 8: Commit Task 3**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py applications/plugin-builder/scripts/plugin_builder_core/implementation_plan.py applications/plugin-builder/tests/test_planning_workflow.py
git commit -m "fix: preflight proposed plugin tree before w1"
```

---

### Task 4: Cover update overlays and explicit reference ownership

**Files:**
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/implementation_plan.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/update_candidate.py`
- Modify: `applications/plugin-builder/tests/test_planning_workflow.py`
- Modify: `applications/plugin-builder/tests/test_update_candidate.py`

**Interfaces:**
- Consumes: Task 3 preflight and the inspected `baseline/` tree.
- Produces: update support in `materialize_proposed_tree(...)`; `_reference_ownership_errors(proposal: dict[str, Any]) -> tuple[str, ...]` requiring rationale for duplicated professional source bindings.

- [ ] **Step 1: Write the failing update-overlay preflight test**

Add `test_update_plan_preflight_validates_overlaid_final_tree_without_mutation`. Prepare a baseline, submit an update recipe whose changed Skill contains an escaping reference, and assert planning fails before W1, the baseline digest is unchanged, no candidate exists, and no owner update decision is invented.

- [ ] **Step 2: Write the failing duplicated-reference ownership tests**

Add two tests to `test_planning_workflow.py`:

- `test_plan_rejects_duplicated_professional_source_without_ownership_rationale` copies one `source_path` into two Skill-local `references/` destinations and expects `plan.reference_duplication_unjustified:<source_path>`.
- `test_plan_accepts_duplicated_professional_source_with_ownership_rationale` adds a non-empty `implementation_decisions.reference_ownership.<source_path>` explanation and expects planning to proceed when all other checks pass.

- [ ] **Step 3: Run the focused tests and verify RED**

Run:

```powershell
python -B -m unittest applications.plugin-builder.tests.test_planning_workflow applications.plugin-builder.tests.test_update_candidate -v
```

Expected: the new tests FAIL because preflight supports only create and duplicate ownership is not evaluated.

- [ ] **Step 4: Implement update proposed-tree materialization**

For `operation == "update"`, require `workspace_root / "baseline"`, calculate planned removals as baseline members absent from `expected_members` excluding Plugin Builder control files, call `plugin_authoring.overlay_files`, remove stale control manifests, generate declared agent YAML, and materialize the manifest pair. This simulates the planned final tree only; it must not write an update decision or authorize removal.

- [ ] **Step 5: Add reference-ownership validation**

Implement `_reference_ownership_errors(...)`. Group professional reference recipes by identical `source_path`; when one source feeds more than one Skill prefix, require a non-empty rationale under `implementation_decisions["reference_ownership"][source_path]`. Keep one-copy references and general-knowledge index handling unchanged.

- [ ] **Step 6: Refactor update candidate construction to the shared boundary**

Import `agent_yaml` and `materialize_proposed_tree` into `update_candidate.py`. After existing baseline identity and explicit update-decision gates pass, use the shared materializer for the baseline overlay, agent metadata, and manifest pair. Keep change-manifest calculation and transactional candidate replacement unchanged.

- [ ] **Step 7: Run planning, create, and update suites and verify GREEN**

Run:

```powershell
python -B -m unittest applications.plugin-builder.tests.test_planning_workflow applications.plugin-builder.tests.test_create_candidate applications.plugin-builder.tests.test_update_candidate -v
```

Expected: all tests PASS; update preflight validates the projected tree without changing baseline, decisions, or candidate.

- [ ] **Step 8: Commit Task 4**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py applications/plugin-builder/scripts/plugin_builder_core/implementation_plan.py applications/plugin-builder/scripts/plugin_builder_core/update_candidate.py applications/plugin-builder/tests/test_planning_workflow.py applications/plugin-builder/tests/test_update_candidate.py
git commit -m "fix: preflight updates and reference ownership"
```

---

### Task 5: Update product contracts, traceability, and patch versions

**Files:**
- Modify: `applications/cool-plugin-design-assistant/.codex-plugin/plugin.json`
- Modify: `applications/cool-plugin-design-assistant/openclaw/distribution.json`
- Modify: `applications/cool-plugin-design-assistant/scripts/cool_plugin_design_assistant.py`
- Modify: `applications/cool-plugin-design-assistant/README.md`
- Modify: `applications/cool-plugin-design-assistant/DISTRIBUTION.md`
- Modify: `applications/cool-plugin-design-assistant/tests/test_conversion_contract.py`
- Modify: `applications/cool-plugin-design-assistant/tests/test_tools.py`
- Modify: `applications/cool-plugin-design-assistant/tests/coverage-matrix.md`
- Modify: `applications/plugin-builder/plugin.json`
- Modify: `applications/plugin-builder/.codex-plugin/plugin.json`
- Modify: `applications/plugin-builder/openclaw/distribution.json`
- Modify: `applications/plugin-builder/docs/phase-one-scope.json`
- Modify: `applications/plugin-builder/README.md`
- Modify: `applications/plugin-builder/DISTRIBUTION.md`
- Modify: `applications/plugin-builder/skills/planning-plugin-implementations/SKILL.md`
- Modify: `applications/plugin-builder/skills/planning-plugin-implementations/references/input-and-plan-contract.md`
- Modify: `applications/plugin-builder/tests/test_conversion_contract.py`
- Modify: `applications/plugin-builder/tests/test_distribution.py`
- Modify: `applications/plugin-builder/tests/test_skill_contracts.py`
- Modify: `applications/plugin-builder/tests/coverage-matrix.md`
- Modify as discovered by exact-version search: product-owned release metadata and tests only

**Interfaces:**
- Consumes: completed behavior from Tasks 1-4.
- Produces: Cool Plugin Design Assistant `1.0.2` and Plugin Builder `1.0.1` local release-candidate metadata, with no publication action.

- [ ] **Step 1: Write failing version and contract assertions**

Update product contract tests to require Design Assistant `1.0.2`, Plugin Builder `1.0.1`, digest-bound chat packaging language, and pre-W1 static compilation language. Keep Plugin Builder `OPENAI_ONLY_PHASE_ONE` assertions unchanged.

- [ ] **Step 2: Run product contract tests and verify RED**

Run:

```powershell
python -B -m unittest applications.cool-plugin-design-assistant.tests.test_conversion_contract applications.cool-plugin-design-assistant.tests.test_tools applications.plugin-builder.tests.test_conversion_contract applications.plugin-builder.tests.test_distribution applications.plugin-builder.tests.test_skill_contracts -v
```

Expected: FAIL on old versions and missing contract language.

- [ ] **Step 3: Update synchronized product metadata**

Set every product-owned Design Assistant release identity to `1.0.2` and every product-owned Plugin Builder release identity to `1.0.1`. Do not change sample-plugin fixtures, approved design specification versions, application-tool provenance fixtures, or historical evidence records merely because they contain another version string.

- [ ] **Step 4: Update documentation and Skill contracts**

Document the digest-bound normalization evidence, non-mutating pre-W1 sandbox, aggregated diagnostics, reference-ownership rule, unchanged W1/W2 gates, and runtime-evidence limitation. Update each coverage matrix with the exact new tests and evidence state; installed chat behavior remains `NOT VERIFIED`.

- [ ] **Step 5: Run product contract tests and verify GREEN**

Run the Step 2 command again.

Expected: all tests PASS and manifest/distribution versions agree within each product.

- [ ] **Step 6: Commit Task 5**

Stage only the files identified above after reviewing `git diff --name-only`, then run:

```powershell
git commit -m "chore: prepare handoff remediation patch versions"
```

---

### Task 6: Run complete verification and build deterministic local release candidates

**Files:**
- Generated only below ignored `.tmp/` or `dist/`
- Modify only if a verified test failure identifies an in-scope root cause; return to the owning task's RED/GREEN cycle before editing

**Interfaces:**
- Consumes: the complete implementation and product distribution contracts.
- Produces: local test reports and deterministic release-candidate artifacts; no marketplace mutation or publication.

- [ ] **Step 1: Run framework tests**

```powershell
python -B -m unittest discover -s .\tests\framework -v
```

Expected: all tests PASS.

- [ ] **Step 2: Run the cross-product interoperability suite**

```powershell
python -B -m unittest tests.test_workbench_handoff_interoperability -v
```

Expected: all full/create, delta/update, preservation, digest, and deterministic tests PASS.

- [ ] **Step 3: Run both complete product suites**

```powershell
python -B -m unittest discover -s .\applications\cool-plugin-design-assistant\tests -v
python -B -m unittest discover -s .\applications\plugin-builder\tests -v
```

Expected: both suites PASS with no candidate mutation from negative planning tests.

- [ ] **Step 4: Validate both distribution contracts**

```powershell
python -B -m obvious_one_plugin_framework.cli validate-contract --contract applications/cool-plugin-design-assistant/openclaw/distribution.json
python -B -m obvious_one_plugin_framework.cli validate-contract --contract applications/plugin-builder/openclaw/distribution.json
```

Expected: each command emits one `result-schema-v1` document with a passing status; exit code alone is not accepted as evidence.

- [ ] **Step 5: Build and verify Design Assistant twice**

Build to two distinct ignored roots with `build-package`, verify both with `verify`, and compare the generated bundle and content-manifest hashes. Build the Codex release tree twice with `applications/cool-plugin-design-assistant/scripts/build_marketplace_release.py --version 1.0.2`; assert byte-identical corresponding files and equivalent inventories.

Expected: both OpenClaw and Codex local builds are deterministic and independently verified. This is build evidence, not installed conversation evidence.

- [ ] **Step 6: Build and verify Plugin Builder twice**

Build to two distinct ignored roots with `build-package`, verify both with `verify`, and compare hashes. Build the Codex release tree twice with `applications/plugin-builder/scripts/build_marketplace_release.py --version 1.0.1`; assert byte-identical corresponding files and equivalent inventories.

Expected: both local builds are deterministic. OpenClaw execution remains outside Plugin Builder's `OPENAI_ONLY_PHASE_ONE`; building or validating a distribution representation does not change that runtime classification.

- [ ] **Step 7: Validate extracted artifacts and run declared smoke commands**

Run each product's `conversion.json` verification commands against the generated or extracted artifact where applicable. For Plugin Builder, include create, update, and bundled-local-tool smoke tests. For Design Assistant, include normalization through the packaged script and verify the report digest equals the returned ZIP.

Expected: all declared static and executable local checks PASS; installed chat interaction remains `NOT VERIFIED` until the owner's separate test.

- [ ] **Step 8: Audit repository state**

```powershell
git diff --check
git status --short
git diff --stat HEAD~5..HEAD
```

Expected: no whitespace errors, no generated artifacts outside ignored roots, no changes to source archives, and the two unrelated Vibe Coding Designer files remain untracked and untouched.

- [ ] **Step 9: Commit any verification-only tracked updates**

If coverage or deterministic manifests legitimately changed during verification, first add a failing contract test or explain the deterministic regeneration requirement, update only the owned files, rerun the affected suites, then commit:

```powershell
git commit -m "test: verify handoff remediation release candidates"
```

If no tracked update is required, do not create an empty commit.

---

## Completion report requirements

Report:

- regression tests and their original RED failure reasons;
- Design Assistant digest-bound normalization evidence;
- Plugin Builder create/update preflight and combined-diagnostic evidence;
- exact requirement and reference-ownership preservation;
- framework, product, cross-product, deterministic-build, and extracted-artifact results;
- generated local release-candidate paths and SHA-256 values;
- Codex and ChatGPT Work Local/Desktop installed-runtime state;
- all `NOT VERIFIED` or `NOT APPLICABLE` gates;
- Git branch, commits, and remaining unrelated working-tree entries; and
- publication state as `NOT_PERFORMED`.

Do not report either remediation as `READY` until the applicable installed-runtime evidence exists. If repository and artifact checks pass but installed chat testing has not occurred, use `CONVERSION COMPLETE — RUNTIME VALIDATION PENDING`.
