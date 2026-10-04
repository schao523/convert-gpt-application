# Design Assistant and Plugin Builder Preflight Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Plan status:** OWNER REVIEW — REVISION 1

**Revision note:** This plan supersedes the earlier six-task plan only after
owner approval. No checkbox from this revised plan is authorized for execution
by the specification approval alone.

**Goal:** Bind Design Assistant chat handoff packaging to the deterministic final ZIP and make Plugin Builder reject predictable structural, knowledge-ownership, duplicate-content, path-binding, executable-portability, manifest-profile, and evidence-boundary defects before producing an approvable W1 plan.

**Architecture:** Extend the shared handoff result with digest-bound producer evidence, then use one shared Plugin Builder proposed-tree materializer for planning and candidate creation. Planning runs that materializer in an isolated sandbox and composes focused validators for plugin structure, knowledge ownership, duplicate content, path bindings, runtime commands, and target metadata before W1 hashing. Candidate verification and packaging carry the same canonical preflight evidence forward into a digest-bound sidecar report while keeping installation and behavioral evidence distinct.

**Tech Stack:** Python 3.11+, standard-library `dataclasses`, `hashlib`, `json`, `pathlib`, `re`, `shutil`, `subprocess`, `tempfile`, and `zipfile`; `unittest`; repository `plugin_authoring` and `workbench_handoff` APIs; Markdown Skill contracts; deterministic ZIP builders.

**Spec:** `docs/superpowers/specs/2026-10-04-design-assistant-plugin-builder-preflight-remediation-design.md`

## Global Constraints

- Preserve `WORKBENCH_HANDOFF_V1_1`, exact requirement `id`, `source`, `verbatim`, and update `change` values.
- Preserve strict SHA-256 checks, approved source bytes, one semantic authority, update baseline identity, fail-closed behavior, and deterministic output.
- Plugin Builder runtime scope remains exactly `OPENAI_ONLY_PHASE_ONE`.
- W1 remains the only approval permitting candidate mutation; W2 remains the only approval permitting final packaging.
- Planning preflight may write only below an isolated temporary directory and must not create or modify `candidate/`, `baseline/`, approval records, or update decisions.
- Unknown, ambiguous, incomplete, or conflicting authority remains fail-closed.
- Do not infer approval, requirement text, rights, baseline identity, removal authority, knowledge classification, or reference ownership.
- Professional knowledge belongs in its owning Skill's `references/`; explicitly adopted general knowledge belongs in one consultation Skill with one `references/knowledge-index.json`; `assets/` cannot carry knowledge to bypass those rules.
- Measure exact duplicate groups and duplicate bytes; do not impose an arbitrary total ZIP-size limit.
- Portable Skills route tools by stable tool ID and never expose escaping filesystem paths in Markdown, inline code, prose, YAML, JSON, or command examples.
- Runtime command resolution must record declared and observed argv. Never silently substitute a literal executable.
- Keep wrapped single-plugin-directory ZIPs supported for the Desktop packaging profile; do not require flat-root packaging without a target contract.
- Keep structural validity, archive integrity, installation, tool execution, reference consultation, and conversational behavior as distinct evidence layers.
- Optional homepage, repository, license, keywords, icon, and brand metadata is release-readiness evidence, not an unintended private/local install blocker.
- Preserve the unrelated untracked Vibe Coding Designer files.
- Use `python -B` for Python commands so verification does not create `__pycache__` artifacts.
- Do not install dependencies, push, tag, publish, mutate a marketplace, submit to a directory, or perform any external release action.

## Review Focus

- A create proposal that labels knowledge as a static asset or places it under `assets/` must fail before W1, while a preserved legacy baseline remains unchanged and its inherited uncertainty is reported; Task 5 owns the tests.
- Exact professional-reference bytes copied into every Skill must fail without a digest-keyed ownership rationale and must report deterministic duplicate-byte totals; Task 5 owns the tests.
- Escaping paths hidden in inline code, prose, JSON/YAML, or tool argv must fail even when every Markdown link is valid; Task 6 owns the tests.
- Literal `python3` must be `NOT VERIFIED` when unavailable on Windows, while `{python}` must resolve explicitly and report both declared and observed argv; Task 6 owns the tests.
- A valid wrapped Desktop ZIP must remain accepted, and its sidecar must not promote archive/upload evidence into tool, reference, or conversation evidence; Task 8 owns the tests.

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
- Produces: reports with `input_profile`, `output_profile`, `source_archive_sha256`, and `output_archive_sha256`; only a validated final canonical archive may report `output_profile == "WORKBENCH_HANDOFF_V1_1"`.

- [ ] **Step 1: Write the failing result-binding tests**

Add `test_normalization_report_binds_input_output_profiles_and_final_zip_digest` and a post-operation digest-mismatch case to `test_tools.py`. Require the source digest, returned ZIP digest, canonical output profile, `handoff.output_archive_sha256_mismatch` on mismatch, and no successful destination on failure.

- [ ] **Step 2: Write the failing chat-routing contract test**

Add `test_handoff_packaging_requires_deterministic_digest_bound_normalization` to `test_skill_contracts.py`. Require `normalize-handoff-package`, prohibit manual canonical-pair construction, require final-ZIP digest equality and full canonical validation, and require `HANDOFF BLOCKED` when execution is unavailable.

- [ ] **Step 3: Run the focused tests and verify RED**

```powershell
python -B -m unittest applications.cool-plugin-design-assistant.tests.test_tools applications.cool-plugin-design-assistant.tests.test_skill_contracts -v
```

Expected: FAIL because the product boundary does not yet bind the reported result to the final returned bytes and the chat contract does not require the deterministic operation.

- [ ] **Step 4: Extend the shared and product result contracts**

Change `_report(...) -> dict[str, Any]` and `_outcome(...) -> HandoffNormalizationOutcome` in `normalization.py` to retain `input_profile`; successful results set `output_profile` to `WORKBENCH_HANDOFF_V1_1`, and failed/blocked results set it to `None`. Retain the existing `profile` key as a patch-release compatibility alias.

In `normalize_handoff_package(...) -> dict[str, Any]`, calculate the final destination ZIP SHA-256, compare it with the shared outcome, re-open the final ZIP, require both canonical authorities, and remove only the newly created destination on mismatch.

- [ ] **Step 5: Strengthen the chat-facing Skill contract**

Update the Skill and handoff reference to require the deterministic command and digest-bound structured result. A chat may author approved semantic inputs, but it may not manually synthesize the canonical pair or claim success without final-archive validation.

- [ ] **Step 6: Extend cross-product assertions and verify GREEN**

Make `_produce(...)` in `test_workbench_handoff_interoperability.py` assert the canonical output profile and exact digest of the bytes passed to Plugin Builder, then run:

```powershell
python -B -m unittest applications.cool-plugin-design-assistant.tests.test_tools applications.cool-plugin-design-assistant.tests.test_skill_contracts tests.test_workbench_handoff_interoperability -v
```

Expected: PASS, including fail-closed digest mismatch.

- [ ] **Step 7: Commit Task 1**

```powershell
git add src/obvious_one_plugin_framework/workbench_handoff/normalization.py applications/cool-plugin-design-assistant/scripts/cool_plugin_design_assistant.py applications/cool-plugin-design-assistant/skills/creating-application-plugin-design-specifications applications/cool-plugin-design-assistant/tests/test_tools.py applications/cool-plugin-design-assistant/tests/test_skill_contracts.py tests/test_workbench_handoff_interoperability.py
git commit -m "fix: bind handoff chat output to normalized zip"
```

---

### Task 2: Create one proposed-tree materialization boundary

**Files:**
- Create: `applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/candidate.py`
- Modify: `applications/plugin-builder/tests/test_create_candidate.py`

**Interfaces:**
- Consumes: canonical proposal/plan dictionaries, approved workspace-relative source paths, and `plugin_authoring` materialization APIs.
- Produces: `agent_yaml(skill: dict[str, Any]) -> bytes` and `materialize_proposed_tree(proposal: dict[str, Any], workspace_root: Path, destination: Path) -> None`; create support lands here and update support is added in Task 4.

- [ ] **Step 1: Add the failing create parity test**

Add `test_shared_materializer_matches_created_candidate_before_control_manifest`. Materialize the approved plan through `materialize_proposed_tree`, build normally, and assert byte equality for all members except `PLUGIN-BUILDER-MANIFEST.json`.

- [ ] **Step 2: Run the parity test and verify RED**

```powershell
python -B -m unittest applications.plugin-builder.tests.test_create_candidate.CreateCandidateTests.test_shared_materializer_matches_created_candidate_before_control_manifest -v
```

Expected: ERROR because `plugin_builder_core.proposed_tree` does not exist.

- [ ] **Step 3: Implement the shared create materializer**

Implement the two produced interfaces. For `operation == "create"`, call `plugin_authoring.materialize_files`, generate every declared Skill's `agents/openai.yaml`, and call `plugin_authoring.materialize_manifest_pair`. Reject unsupported operations with `PluginAuthoringError("proposal_operation_unsupported")`.

- [ ] **Step 4: Refactor create candidate construction**

Remove `_agent_yaml` from `candidate.py` and use the shared boundary. Preserve W1 binding, tool gates, control-manifest generation, validation, and transactional replacement.

- [ ] **Step 5: Run create tests and verify GREEN**

```powershell
python -B -m unittest applications.plugin-builder.tests.test_create_candidate -v
```

Expected: PASS with byte-identical repeated create output.

- [ ] **Step 6: Commit Task 2**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py applications/plugin-builder/scripts/plugin_builder_core/candidate.py applications/plugin-builder/tests/test_create_candidate.py
git commit -m "refactor: share proposed plugin tree materialization"
```

---

### Task 3: Fail basic structural defects before W1

**Files:**
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/implementation_plan.py`
- Modify: `applications/plugin-builder/tests/test_planning_workflow.py`

**Interfaces:**
- Consumes: `materialize_proposed_tree(...)` and `plugin_authoring.validate_plugin_tree(root)`.
- Produces: `ProposedTreePreflight(diagnostics: tuple[str, ...], evidence: dict[str, Any])` and `preflight_proposed_tree(proposal: dict[str, Any], workspace_root: Path) -> ProposedTreePreflight` without persistent mutation.
- Produces new plans as `plugin-builder-implementation-plan-v2`; an already approved v1 plan is never rewritten or treated as v2 and must return `build.plan_schema_upgrade_required` before candidate mutation so the owner can re-plan and approve the new hash.

- [ ] **Step 1: Write the failing manifest, Markdown-path, aggregation, and cleanup tests**

Add `test_plan_preflight_rejects_missing_author_and_interface_before_w1`, `test_plan_preflight_rejects_escaping_skill_reference_before_w1`, and `test_plan_preflight_aggregates_static_failures_and_cleans_temporary_tree`. Require return code `3`, stable `plan.preflight.*` diagnostics, no plan identity, no candidate mutation, preservation of a pre-existing sentinel candidate, and removal of every `.plan-preflight-*` directory.

- [ ] **Step 2: Run the tests and verify RED**

```powershell
python -B -m unittest applications.plugin-builder.tests.test_planning_workflow -v
```

Expected: the new cases FAIL because planning does not materialize or validate the complete proposal.

- [ ] **Step 3: Implement non-mutating create preflight**

Use `TemporaryDirectory(dir=workspace_root, prefix=".plan-preflight-")`, materialize into `plugin`, run `validate_plugin_tree`, and translate every issue into `plan.preflight.<code>:<path>[:<detail>]`. Return initial evidence containing `schema == "plugin-builder-preflight-v1"` and the materialized tree SHA-256. Convert `PluginAuthoringError` and `OSError` into stable diagnostics; never discard validator output.

- [ ] **Step 4: Invoke preflight before plan hashing**

Call preflight only after proposal shapes, source paths, and expected-member paths are safe to materialize. Aggregate diagnostics before the existing failure return. On success set the output schema to `plugin-builder-implementation-plan-v2` and add `preflight_evidence` before hashing; never accept either derived value from proposal input.

- [ ] **Step 5: Run planning and create suites GREEN**

```powershell
python -B -m unittest applications.plugin-builder.tests.test_planning_workflow applications.plugin-builder.tests.test_create_candidate -v
```

Expected: PASS; predictable structural failures occur before W1.

- [ ] **Step 6: Commit Task 3**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py applications/plugin-builder/scripts/plugin_builder_core/implementation_plan.py applications/plugin-builder/tests/test_planning_workflow.py
git commit -m "fix: preflight proposed plugin tree before w1"
```

---

### Task 4: Apply the same preflight to update overlays

**Files:**
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/update_candidate.py`
- Modify: `applications/plugin-builder/tests/test_planning_workflow.py`
- Modify: `applications/plugin-builder/tests/test_update_candidate.py`

**Interfaces:**
- Consumes: Task 3 preflight and the inspected `baseline/` tree.
- Produces: update support in `materialize_proposed_tree(...)`, simulating the final overlaid tree without granting removal authority.

- [ ] **Step 1: Write the failing update-overlay test**

Add `test_update_plan_preflight_validates_overlaid_final_tree_without_mutation`. Use a changed Skill with an escaping reference and assert pre-W1 failure, unchanged baseline digest, no candidate, no update decision, and no remaining temporary tree.

- [ ] **Step 2: Run update planning tests and verify RED**

```powershell
python -B -m unittest applications.plugin-builder.tests.test_planning_workflow applications.plugin-builder.tests.test_update_candidate -v
```

Expected: FAIL because preflight supports only create.

- [ ] **Step 3: Implement update proposed-tree materialization**

For `operation == "update"`, require `workspace_root / "baseline"`, calculate prospective removals from `expected_members`, call `plugin_authoring.overlay_files`, remove stale Builder control files, regenerate declared agent YAML, and materialize the manifest pair. Do not write `update-decisions.json`, approve removal, or mutate the baseline.

- [ ] **Step 4: Refactor update candidate construction**

After the existing W1, baseline-identity, and explicit update-decision gates pass, use the shared materializer in `update_candidate.py`. Preserve change-manifest calculation and transactional replacement.

- [ ] **Step 5: Run create/update/planning suites GREEN**

```powershell
python -B -m unittest applications.plugin-builder.tests.test_planning_workflow applications.plugin-builder.tests.test_create_candidate applications.plugin-builder.tests.test_update_candidate -v
```

Expected: PASS; update preflight proves the projected tree without changing authority or state.

- [ ] **Step 6: Commit Task 4**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py applications/plugin-builder/scripts/plugin_builder_core/update_candidate.py applications/plugin-builder/tests/test_planning_workflow.py applications/plugin-builder/tests/test_update_candidate.py
git commit -m "fix: preflight projected update trees"
```

---

### Task 5: Enforce knowledge ownership and exact-duplicate policy

**Files:**
- Create: `applications/plugin-builder/scripts/plugin_builder_core/artifact_quality.py`
- Create: `applications/plugin-builder/tests/test_preflight_artifact_quality.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/implementation_plan.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/candidate.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/update_candidate.py`
- Modify: `applications/plugin-builder/tests/fixtures/plan-create.json`
- Modify: product test helpers and proposal fixtures discovered by `rg '"classification"' applications/plugin-builder/tests`

**Interfaces:**
- Consumes: the materialized proposed tree and file recipes with origin `classification` plus new semantic `content_role`.
- Produces: `ArtifactQualityReport` and `audit_artifact_quality(proposal: dict[str, Any], materialized_root: Path, *, baseline_manifest: dict[str, Any] | None = None) -> ArtifactQualityReport`.
- `content_role` is exactly one of `PLUGIN_MANIFEST`, `SKILL_ENTRYPOINT`, `PROFESSIONAL_KNOWLEDGE`, `GENERAL_KNOWLEDGE`, `EXECUTABLE_TOOL`, `STATIC_ASSET`, `GENERATED_METADATA`, or `OTHER`.
- `implementation_decisions.knowledge_policy` is exactly `{ "adopt_general_knowledge": bool, "consultation_skill": str | null }`; `consultation_skill` is non-null only when adoption is true.
- `implementation_decisions.reference_ownership` is an object keyed by lowercase content SHA-256 with non-empty rationale strings.
- `ArtifactQualityReport.as_dict()` emits `schema == "plugin-builder-artifact-quality-v1"`, sorted `knowledge_ownership`, sorted `duplicate_groups`, and integer `duplicate_bytes`.

- [ ] **Step 1: Write failing role and placement tests**

Prove that missing/unknown `content_role`, knowledge under any Skill `assets/`, professional knowledge outside its owning Skill's `references/`, multiple general indexes, and general knowledge without an explicitly adopted consultation Skill all fail before W1. Add one passing professional case and one passing consultation-Skill case.

- [ ] **Step 2: Write failing digest-duplicate tests**

Create identical professional bytes under multiple Skills. Require a diagnostic keyed by content SHA-256, deterministic paths/count/size/duplicate-byte evidence, and failure without `implementation_decisions.reference_ownership[sha256]`. Require a non-empty application-specific rationale to pass. Prove unrelated identical generated files are reported but do not automatically fail.

- [ ] **Step 3: Write the preserved-baseline compatibility test**

Prepare an update baseline whose old control manifest lacks semantic file roles. Require preserved members to be reported as `INHERITED_UNCLASSIFIED` without rewriting them; any new/changed recipe still requires `content_role`, and copying inherited knowledge to a new Skill requires an explicit role and rationale.

Also add `test_build_blocks_approved_v1_plan_for_replanning`. Require
`build.plan_schema_upgrade_required`, unchanged W1/session bytes, and no
candidate; the implementation must not retrofit v2 evidence into the approved
v1 plan.

- [ ] **Step 4: Run focused tests and verify RED**

```powershell
python -B -m unittest applications.plugin-builder.tests.test_preflight_artifact_quality -v
```

Expected: FAIL because semantic roles, hash groups, and ownership policy are absent.

- [ ] **Step 5: Implement semantic roles and quality audit**

Extend the exact recipe schema with `content_role`. Assign derived
`.codex-plugin/plugin.json` and `skills/*/agents/openai.yaml` members
`GENERATED_METADATA`; control manifests are outside the application-role map.
Implement destination-policy checks, the exact knowledge-policy decision,
SHA-256 grouping of the final tree, and digest-keyed rationale validation.
Count duplicate bytes as `(member_count - 1) * size` per group and sort evidence
canonically.

- [ ] **Step 6: Bind quality evidence into plan and candidate identities**

Merge the quality report into `preflight_evidence` before W1 hashing. Emit
`plugin-builder-candidate-manifest-v2` with `file_roles`,
`preflight_evidence_sha256`, and explicit `operation` for create and update.
Read a v1 baseline control manifest only for preservation/update compatibility;
never rewrite it in place or present its absent roles as verified. Candidate
creation compares its materialized evidence digest with the approved plan and
never silently changes the policy result after W1.

- [ ] **Step 7: Update fixtures and run affected suites GREEN**

Give every proposal recipe an accurate role and add exact `implementation_decisions.knowledge_policy` and `reference_ownership` objects, then run:

```powershell
python -B -m unittest applications.plugin-builder.tests.test_preflight_artifact_quality applications.plugin-builder.tests.test_planning_workflow applications.plugin-builder.tests.test_create_candidate applications.plugin-builder.tests.test_update_candidate applications.plugin-builder.tests.test_review_regressions applications.plugin-builder.tests.test_standalone_artifact -v
```

Expected: PASS with deterministic quality evidence and no broad-copy fallback.

- [ ] **Step 8: Commit Task 5**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core/artifact_quality.py applications/plugin-builder/scripts/plugin_builder_core/implementation_plan.py applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py applications/plugin-builder/scripts/plugin_builder_core/candidate.py applications/plugin-builder/scripts/plugin_builder_core/update_candidate.py applications/plugin-builder/tests
git commit -m "fix: enforce plugin knowledge and duplicate policy"
```

---

### Task 6: Validate every path-bearing form and make command resolution explicit

**Files:**
- Modify: `src/obvious_one_plugin_framework/plugin_authoring/validation.py`
- Modify: `src/obvious_one_plugin_framework/plugin_authoring/__init__.py`
- Modify: `src/obvious_one_plugin_framework/plugin_authoring/tools.py`
- Create: `tests/framework/test_plugin_authoring_path_bindings.py`
- Create: `applications/plugin-builder/scripts/plugin_builder_core/runtime_commands.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/tool_contract.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/tool_verification.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/verification.py`
- Create: `applications/plugin-builder/tests/test_tool_execution_portability.py`
- Modify: `applications/plugin-builder/tests/fixtures/plan-create.json`
- Modify: affected tests found by `rg '"python"|"python3"' applications/plugin-builder/tests`

**Interfaces:**
- Produces: `validate_path_bindings(root: Path) -> tuple[ValidationIssue, ...]`, included by `validate_plugin_tree`.
- Produces: `CommandResolution(declared_argv: tuple[str, ...], observed_argv: tuple[str, ...] | None, adapter: str | None, diagnostic: str | None)` and `resolve_direct_argv(argv: list[str], candidate: Path, *, executable_lookup: Callable[[str], str | None] = shutil.which) -> CommandResolution`.
- `{python}` is the only interpreter adapter token introduced here. Literal commands remain literal; unavailable literals return `executable_unavailable` and are never replaced by `sys.executable`.
- Preflight command evidence declares `resolution_scope == "BUILD_HOST"` and is only `STATICALLY VERIFIED`; target-runtime proof is recorded later by runtime-result v2.

- [ ] **Step 1: Write failing path-binding tests**

Place `../../scripts/tool.py`, a Windows drive path, and backslash traversal separately in Markdown links, backticks, plain prose, YAML, JSON, and a command example. Require `path_binding_invalid`. Prove `references/method.md`, stable tool ID `normalize-input`, and `https://` URLs do not produce false positives. Prove `tools/run.py` is valid as a structured tool-contract file binding but invalid when a Skill uses it as a direct command route instead of the stable tool ID.

- [ ] **Step 2: Write failing command-resolution tests**

Inject an executable lookup returning `None` for literal `python3`; require no execution and `observed_argv is None`. Prove `{python}` resolves to the current interpreter with adapter `CURRENT_PYTHON`. Require verification results to retain compatibility `argv` as declared argv while adding `declared_argv`, `observed_argv`, and `adapter`.

- [ ] **Step 3: Write silent-substitution and binding regressions**

Require old literal-`python3` behavior to return `NOT VERIFIED`; require a Skill with a stable tool ID plus hidden `../../scripts/...` to fail preflight; require the same Skill with only the ID and `{python}` contract to pass.

- [ ] **Step 4: Run focused tests and verify RED**

```powershell
python -B -m unittest tests.framework.test_plugin_authoring_path_bindings applications.plugin-builder.tests.test_tool_execution_portability applications.plugin-builder.tests.test_candidate_verification -v
```

Expected: FAIL because validation is Markdown-link-only and `execute_direct` silently substitutes Python.

- [ ] **Step 5: Implement candidate-wide path validation**

Scan UTF-8 `.md`, `.json`, `.yaml`, and `.yml` candidate files for local
path-bearing tokens. Reject absolute, drive-qualified, backslash, empty-segment,
`.`-segment, and `..`-segment paths while ignoring URI schemes and ordinary
prose. Resolve path-like tokens in `SKILL.md` against that Skill directory and
report `path_binding_missing` when the safe target does not exist; evaluate
structured tool-contract file paths against the plugin root. This makes a real
Skill-local `scripts/helper.py` valid, a root `tools/run.py` valid in its tool
contract, and either an escaping or nonexistent direct Skill route invalid.
Export and include the validator in `validate_plugin_tree`.

- [ ] **Step 6: Implement explicit command resolution**

Resolve `{python}` to `sys.executable`; resolve an available literal through `executable_lookup` and record the absolute observed executable; leave unavailable literals unresolved. `execute_direct` executes only `observed_argv`, retains the restricted environment, and returns declared/observed argv and adapter on every outcome.

- [ ] **Step 7: Strengthen tool contracts and preflight**

Reject unknown adapter tokens and unsafe path-like values in `execution.argv` and `verification.argv`. During planning resolve both arrays without executing them and add sorted resolution evidence to `preflight_evidence`; any unresolved `BUNDLED_LOCAL` or `FRAMEWORK_ADAPTER` command fails preflight, while runtime-native and MCP contracts retain their existing honest `NOT VERIFIED` handling. Convert intended packaged-Python fixtures from literal `python`/`python3` to `{python}`.

- [ ] **Step 8: Run framework and product tests GREEN**

```powershell
python -B -m unittest tests.framework.test_plugin_authoring_path_bindings applications.plugin-builder.tests.test_tool_execution_portability applications.plugin-builder.tests.test_tool_contracts applications.plugin-builder.tests.test_candidate_verification applications.plugin-builder.tests.test_application_tools applications.plugin-builder.tests.test_planning_workflow -v
```

Expected: PASS; declared and observed commands are never conflated.

- [ ] **Step 9: Commit Task 6**

```powershell
git add src/obvious_one_plugin_framework/plugin_authoring applications/plugin-builder/scripts/plugin_builder_core applications/plugin-builder/tests tests/framework/test_plugin_authoring_path_bindings.py
git commit -m "fix: validate portable paths and runtime commands"
```

---

### Task 7: Add target-aware manifest profiles and explicit operation identity

**Files:**
- Create: `applications/plugin-builder/contracts/openai-interface-vocabulary-v1.json`
- Create: `applications/plugin-builder/scripts/plugin_builder_core/manifest_profile.py`
- Create: `applications/plugin-builder/tests/test_manifest_profiles.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/implementation_plan.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/candidate.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/update_candidate.py`
- Modify: `applications/plugin-builder/tests/fixtures/plan-create.json`
- Modify: affected planning/candidate tests

**Interfaces:**
- Produces: versioned vocabulary `obvious-one-openai-interface-v1` with categories `Business`, `Developer Tools`, `Education`, `Lifestyle`, `Productivity`, `Research`, and `Other`, and capabilities `Interactive`, `Read`, and `Write`.
- Produces: `ManifestProfileReport` and `validate_manifest_profile(root: Path, decision: dict[str, Any], vocabulary_path: Path) -> ManifestProfileReport`.
- The decision is exact: `target == "OPENAI_DESKTOP"`, `profile` is `PRIVATE_LOCAL` or `RELEASE_READY`, `vocabulary_version == "obvious-one-openai-interface-v1"`, and `extensions` contains sorted `categories` and `capabilities` arrays.

- [ ] **Step 1: Write failing private/local tests**

Require synchronized non-placeholder descriptions, author name, developer name, default prompt, and known category/capability casing. Prove lowercase `education` fails, `Education` passes, and an unknown value passes only when explicitly listed in the matching extension array.

- [ ] **Step 2: Write failing release-profile tests**

Require deterministic statuses for homepage, repository, license, keywords, icons, and brand colors: `SUPPLIED`, `NOT_APPLICABLE`, or `UNRESOLVED`. Prove unresolved optional listing metadata does not block `PRIVATE_LOCAL` but blocks `RELEASE_READY`; escaped Unicode remains valid and deterministic.

- [ ] **Step 3: Write explicit candidate-operation tests**

Require create/update control manifests to contain `operation == "create"` / `"update"`. Require operation and manifest-profile evidence to bind to the plan preflight-evidence digest.

- [ ] **Step 4: Write the cross-validator aggregation test**

Add `test_preflight_aggregates_quality_path_command_and_manifest_diagnostics`.
Combine one safe-to-materialize defect from each new validator and require every
diagnostic in stable sorted order, no plan file, no W1 identity, and no
candidate mutation. The preflight orchestrator must run all independent
validators after materialization rather than return after the first failure.

- [ ] **Step 5: Run focused tests and verify RED**

```powershell
python -B -m unittest applications.plugin-builder.tests.test_manifest_profiles applications.plugin-builder.tests.test_create_candidate applications.plugin-builder.tests.test_update_candidate -v
```

Expected: FAIL on absent vocabulary/profile evidence and missing create operation.

- [ ] **Step 6: Implement vocabulary-backed profiles**

Load the checked-in vocabulary by immutable schema/version, validate exact decision keys, merge explicit extensions without changing the base vocabulary, and produce canonical field statuses. Add the report to preflight diagnostics/evidence before W1 hashing.

- [ ] **Step 7: Bind operation and profile evidence**

Add explicit operation to create output, preserve update operation, and store manifest-profile evidence and SHA-256 in both candidate manifests. Candidate creation compares those values with the approved plan rather than regenerating different policy decisions.

- [ ] **Step 8: Run affected suites GREEN**

```powershell
python -B -m unittest applications.plugin-builder.tests.test_manifest_profiles applications.plugin-builder.tests.test_planning_workflow applications.plugin-builder.tests.test_create_candidate applications.plugin-builder.tests.test_update_candidate applications.plugin-builder.tests.test_review_regressions -v
```

Expected: PASS with private/local and release-readiness concerns distinct.

- [ ] **Step 9: Commit Task 7**

```powershell
git add applications/plugin-builder/contracts/openai-interface-vocabulary-v1.json applications/plugin-builder/scripts/plugin_builder_core/manifest_profile.py applications/plugin-builder/scripts/plugin_builder_core/implementation_plan.py applications/plugin-builder/scripts/plugin_builder_core/proposed_tree.py applications/plugin-builder/scripts/plugin_builder_core/candidate.py applications/plugin-builder/scripts/plugin_builder_core/update_candidate.py applications/plugin-builder/tests
git commit -m "fix: add target-aware plugin manifest profiles"
```

---

### Task 8: Carry quality evidence through verification and wrapped packaging

**Files:**
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/verification.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/packaging.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/session_contract.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/evidence.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/candidate.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/update_candidate.py`
- Create: `applications/plugin-builder/tests/test_package_quality_evidence.py`
- Modify: `applications/plugin-builder/tests/test_candidate_verification.py`
- Modify: `applications/plugin-builder/tests/test_final_packaging.py`
- Modify: `applications/plugin-builder/tests/test_tool_contracts.py`
- Modify: `applications/plugin-builder/tests/test_runtime_evidence_contract.py`
- Modify: `applications/plugin-builder/tests/test_runtime_evidence_packaging.py`
- Modify: `applications/plugin-builder/tests/runtime/runtime-result-schema.json`
- Modify: `applications/plugin-builder/tests/runtime/prepare-runtime-scenarios.py`
- Modify: `applications/plugin-builder/tests/runtime/T1-T7-runtime-scenarios.md`

**Interfaces:**
- Produces: `plugin-builder-verification-report-v2` with bound `preflight_evidence`, tool declared/observed argv and adapter, and separate evidence states.
- Produces: `plugin-builder-package-v2` sidecar metadata and `PackageOutcome(..., metadata_sha256: str | None)`.
- Produces: `plugin-builder-runtime-result-v2`, while continuing to validate existing v1 evidence bundles read-only. V2 adds exact declared/observed command records and structural, installation, tool-execution, reference-consultation, and conversational evidence-layer states.
- Session package identity gains `metadata_path == "dist/package-metadata.json"` and `metadata_sha256`; the installable ZIP continues to contain only the wrapped plugin tree.

- [ ] **Step 1: Write failing verification-evidence tests**

Require verification to compare plan/candidate preflight digests, preserve duplicate and knowledge evidence exactly, include declared/observed commands, and set structural, tool, reference, and conversation evidence independently. Reference consultation and conversation remain `NOT VERIFIED` without separate runtime evidence.

- [ ] **Step 2: Write failing sidecar-binding tests**

Require metadata to contain archive, candidate, verification, and member-manifest SHA-256 values; quality evidence; manifest profile; command evidence; and separate evidence states. Require session binding to the exact metadata digest and reject ZIP or sidecar tampering.

- [ ] **Step 3: Write wrapped-package compatibility regression**

Require `PORTABLE_SINGLE_DIRECTORY`, `<plugin-id>/plugin.json`, and exact extracted-member equivalence. Assert no flat-root-only diagnostic and prove the sidecar stays outside the installable ZIP.

- [ ] **Step 4: Write runtime-result v2 compatibility tests**

Require v2 installed-runtime evidence to record declared/observed argv, adapter,
wrapped upload/discovery separately, and the five evidence-layer states. Keep a
frozen v1 fixture valid for read-only historical evidence. Reject a v2 result
that marks reference consultation or conversation `RUNTIME VERIFIED` without a
digest-addressed scenario evidence record.

- [ ] **Step 5: Run focused tests and verify RED**

```powershell
python -B -m unittest applications.plugin-builder.tests.test_package_quality_evidence applications.plugin-builder.tests.test_candidate_verification applications.plugin-builder.tests.test_final_packaging applications.plugin-builder.tests.test_tool_contracts applications.plugin-builder.tests.test_runtime_evidence_contract applications.plugin-builder.tests.test_runtime_evidence_packaging -v
```

Expected: FAIL because current reports omit quality/profile evidence, conflate command identity, and do not bind the sidecar digest in session state.

- [ ] **Step 6: Implement verification report v2**

Load canonical preflight evidence from plan and candidate, verify matching hashes, add it without recomputation, and expose evidence states only for the evaluated layer. Never translate archive or structural success into installed behavior.

- [ ] **Step 7: Implement package metadata v2 and session binding**

Build the wrapped deterministic ZIP as before. Build the sidecar from the exact inventory, candidate, verification report, and preflight evidence; hash final sidecar bytes; publish ZIP and sidecar transactionally; and store both hashes in session state. Extend exact session validation and tamper tests.

- [ ] **Step 8: Extend the runtime kit without rewriting historical evidence**

Make `validate_runtime_result(...)` dispatch by schema, preserve exact v1
validation, and add exact v2 validation. Update the generated schema, scenario
preparer, and T1–T7 instructions so new runs capture command and evidence-layer
records. Evidence bundling remains digest-addressed and deterministic for both
versions.

- [ ] **Step 9: Run verification/packaging suites GREEN**

```powershell
python -B -m unittest applications.plugin-builder.tests.test_package_quality_evidence applications.plugin-builder.tests.test_candidate_verification applications.plugin-builder.tests.test_final_packaging applications.plugin-builder.tests.test_tool_contracts applications.plugin-builder.tests.test_runtime_evidence_contract applications.plugin-builder.tests.test_runtime_evidence_packaging -v
```

Expected: PASS; wrapped packaging remains supported and evidence layers remain honest.

- [ ] **Step 10: Commit Task 8**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core applications/plugin-builder/tests
git commit -m "fix: bind plugin quality evidence to packaged output"
```

---

### Task 9: Update product contracts, traceability, and patch versions

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
- Modify: `applications/plugin-builder/skills/building-and-updating-plugins/references/candidate-and-update-contract.md`
- Modify: `applications/plugin-builder/skills/verifying-and-packaging-plugins/references/evidence-and-package-contract.md`
- Modify: `applications/plugin-builder/skills/verifying-and-packaging-plugins/references/tool-evidence-contract.md`
- Modify: `applications/plugin-builder/tests/test_conversion_contract.py`
- Modify: `applications/plugin-builder/tests/test_distribution.py`
- Modify: `applications/plugin-builder/tests/test_skill_contracts.py`
- Modify: `applications/plugin-builder/tests/coverage-matrix.md`
- Modify as found by exact-version search: product-owned current release metadata/tests only

**Interfaces:**
- Consumes: Tasks 1–8.
- Produces: Cool Plugin Design Assistant `1.0.2` and Plugin Builder `1.0.1` local release-candidate metadata; no publication action.

- [ ] **Step 1: Write failing version and contract assertions**

Require both patch versions, digest-bound producer behavior, pre-W1 compilation, semantic roles, duplicate evidence, path validation, runtime adapters, manifest profiles, wrapped-package support, and separate evidence states. Keep `OPENAI_ONLY_PHASE_ONE` unchanged.

- [ ] **Step 2: Run contract tests and verify RED**

```powershell
python -B -m unittest applications.cool-plugin-design-assistant.tests.test_conversion_contract applications.cool-plugin-design-assistant.tests.test_tools applications.plugin-builder.tests.test_conversion_contract applications.plugin-builder.tests.test_distribution applications.plugin-builder.tests.test_skill_contracts -v
```

Expected: FAIL on old versions and missing Revision 1 language.

- [ ] **Step 3: Update synchronized metadata and contracts**

Set product-owned Design Assistant release identities to `1.0.2` and Plugin Builder identities to `1.0.1`. Do not rewrite approved design-spec versions, sample-plugin versions, historical evidence, or tool provenance merely because they contain another version string.

Document all gates and distinguish owner-reported upload evidence from directly verified installed-runtime evidence. Update coverage matrices with exact tests and honest states.

- [ ] **Step 4: Run contract tests and verify GREEN**

Run Step 2 again.

Expected: PASS with synchronized metadata and unchanged scope.

- [ ] **Step 5: Commit Task 9**

Review `git diff --name-only`, stage only owned files, then:

```powershell
git commit -m "chore: prepare expanded remediation patch versions"
```

---

### Task 10: Run complete verification and build deterministic local release candidates

**Files:**
- Generated only below ignored `.tmp/` or `dist/`
- Modify tracked files only by returning to the owning task's RED/GREEN cycle when a verified in-scope root cause requires it

**Interfaces:**
- Consumes: complete implementation and distribution contracts.
- Produces: local reports and deterministic release candidates; no installation, marketplace mutation, or publication.

- [ ] **Step 1: Run complete framework tests**

```powershell
python -B -m unittest discover -s .\tests\framework -v
```

Expected: PASS, including new path validators.

- [ ] **Step 2: Run cross-product interoperability**

```powershell
python -B -m unittest tests.test_workbench_handoff_interoperability -v
```

Expected: PASS for create/update, preservation, digest, malformed input, and determinism.

- [ ] **Step 3: Run both complete product suites**

```powershell
python -B -m unittest discover -s .\applications\cool-plugin-design-assistant\tests -v
python -B -m unittest discover -s .\applications\plugin-builder\tests -v
```

Expected: PASS without negative-test mutation.

- [ ] **Step 4: Run application-aware verification**

```powershell
python -B .\scripts\verify_extraction.py --application cool-plugin-design-assistant
python -B .\scripts\verify_extraction.py --application plugin-builder
```

Expected: required configured gates report `PASS`; marketplace and installed-runtime gates may remain `NOT VERIFIED` and must not be promoted.

- [ ] **Step 5: Validate distribution contracts**

```powershell
python -B -m obvious_one_plugin_framework.cli validate-contract --contract applications/cool-plugin-design-assistant/openclaw/distribution.json
python -B -m obvious_one_plugin_framework.cli validate-contract --contract applications/plugin-builder/openclaw/distribution.json
```

Expected: one passing `result-schema-v1` document per command; exit code alone is insufficient.

- [ ] **Step 6: Build and verify Design Assistant twice**

Run:

```powershell
python -B -m obvious_one_plugin_framework.cli build-package --contract applications/cool-plugin-design-assistant/openclaw/distribution.json --output .tmp/remediation/cpda-openclaw-a --json
python -B -m obvious_one_plugin_framework.cli verify --contract applications/cool-plugin-design-assistant/openclaw/distribution.json --output .tmp/remediation/cpda-openclaw-a --json
python -B -m obvious_one_plugin_framework.cli build-package --contract applications/cool-plugin-design-assistant/openclaw/distribution.json --output .tmp/remediation/cpda-openclaw-b --json
python -B -m obvious_one_plugin_framework.cli verify --contract applications/cool-plugin-design-assistant/openclaw/distribution.json --output .tmp/remediation/cpda-openclaw-b --json
python -B applications/cool-plugin-design-assistant/scripts/build_marketplace_release.py --source applications/cool-plugin-design-assistant --destination .tmp/remediation/cpda-codex-a --version 1.0.2
python -B applications/cool-plugin-design-assistant/scripts/build_marketplace_release.py --source applications/cool-plugin-design-assistant --destination .tmp/remediation/cpda-codex-b --version 1.0.2
```

Compare the two result documents, output inventories, tree hashes, and file
hashes.

Expected: byte-identical corresponding outputs. This is build evidence, not installed conversation evidence.

- [ ] **Step 7: Build and verify Plugin Builder twice**

Run:

```powershell
python -B -m obvious_one_plugin_framework.cli build-package --contract applications/plugin-builder/openclaw/distribution.json --output .tmp/remediation/plugin-builder-openclaw-a --json
python -B -m obvious_one_plugin_framework.cli verify --contract applications/plugin-builder/openclaw/distribution.json --output .tmp/remediation/plugin-builder-openclaw-a --json
python -B -m obvious_one_plugin_framework.cli build-package --contract applications/plugin-builder/openclaw/distribution.json --output .tmp/remediation/plugin-builder-openclaw-b --json
python -B -m obvious_one_plugin_framework.cli verify --contract applications/plugin-builder/openclaw/distribution.json --output .tmp/remediation/plugin-builder-openclaw-b --json
python -B applications/plugin-builder/scripts/build_marketplace_release.py --source applications/plugin-builder --destination .tmp/remediation/plugin-builder-codex-a --version 1.0.1
python -B applications/plugin-builder/scripts/build_marketplace_release.py --source applications/plugin-builder --destination .tmp/remediation/plugin-builder-codex-b --version 1.0.1
```

Compare both pairs, then exercise packaged create/update with `{python}` and
verify ZIP/sidecar hashes, duplicates, profiles, command evidence, and wrapped
envelope equivalence.

Expected: byte-identical outputs. OpenClaw execution remains `NOT APPLICABLE` under `OPENAI_ONLY_PHASE_ONE`; representation validation does not change it.

- [ ] **Step 8: Validate extracted artifacts and Creator structure**

Run every command declared by each `conversion.json` against generated/extracted artifacts where applicable. Use installed `skill-creator` and `plugin-creator` validation on source and extracted Codex artifacts. Do not treat Creator validation as behavior evidence.

Expected: structure, exact members, quality evidence, and packaged deterministic tools pass. Installed conversation/reference behavior remains `NOT VERIFIED` pending owner tests.

- [ ] **Step 9: Audit repository state**

```powershell
git diff --check
git status --short
git diff --stat HEAD~9..HEAD
```

Expected: no whitespace errors, generated files outside ignored roots, source-archive changes, or changes to the unrelated Vibe Coding Designer files.

- [ ] **Step 10: Commit only legitimate verification-owned changes**

If deterministic manifests or coverage evidence require a tracked update, return to the owning test cycle, rerun affected suites, and commit:

```powershell
git commit -m "test: verify expanded remediation release candidates"
```

Otherwise, do not create an empty commit.

---

## Completion report requirements

Report:

- regression tests and original RED reasons;
- Design Assistant digest-bound final-ZIP evidence;
- Plugin Builder create/update preflight and aggregated diagnostics;
- exact requirement, baseline, knowledge-role, and reference-ownership preservation;
- duplicate groups, duplicate bytes, and approved rationales;
- path results across Markdown, prose, inline code, YAML, JSON, and argv;
- declared/observed commands and unresolved executables;
- private/local and release manifest profiles;
- wrapped-package and digest-bound sidecar evidence;
- framework, product, cross-product, application-aware, deterministic-build, Creator, and extracted-artifact results;
- local release-candidate paths and SHA-256 values;
- installation, discovery, tool execution, reference consultation, and conversation states separately for Codex and ChatGPT Work Local/Desktop;
- all `NOT VERIFIED` and `NOT APPLICABLE` gates;
- Git branch, commits, unrelated entries; and
- publication state `NOT_PERFORMED`.

Do not report either remediation as `READY` until applicable installed-runtime evidence exists. If repository/artifact checks pass but installed chat testing has not occurred, use `CONVERSION COMPLETE — RUNTIME VALIDATION PENDING`.
