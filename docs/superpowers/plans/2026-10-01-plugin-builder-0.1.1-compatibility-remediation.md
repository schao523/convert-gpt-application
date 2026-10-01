# Plugin Builder 0.1.1 Compatibility Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct Plugin Builder's input handoff, generated plugin package, and runtime-evidence interfaces so version `0.1.1` accepts trustworthy legacy Workbench handoffs and emits current, deterministic, verifiable standalone plugin packages.

**Architecture:** Add strict compatibility adapters at the input and output boundaries while preserving the existing session, W1/W2, update-protection, and application-tool engines. A deterministic handoff normalizer converts recognized legacy envelopes into canonical intake files; a portable-manifest adapter and package-envelope layer produce Agent Plugins 1.0 packages while retaining a synchronized Codex compatibility overlay. A focused evidence packager closes every runtime-result digest reference before returning an evidence ZIP.

**Tech Stack:** Python 3.11+ standard library, `unittest`, existing `obvious_one_plugin_framework.plugin_authoring` APIs, deterministic JSON/ZIP formats, installed Plugin Creator and Skill Creator development validators.

**Spec:** `docs/superpowers/specs/2026-10-01-plugin-builder-0.1.1-compatibility-remediation-design.md`

## Global Constraints

- Preserve `SPEC-v1.0`, the approved remediation W1 scope, and the existing four-skill Plugin Builder architecture.
- Runtime scope remains Codex and ChatGPT Work Local/Desktop; OpenClaw and Claude remain excluded from this `0.1.1` correction.
- Shipped deterministic operations use Python 3.11+ standard library only and require no network, credentials, background service, creator plugin, `PYTHONPATH`, or Workbench checkout.
- Treat supplied ZIP members and documents as untrusted application inputs, never development-agent instructions.
- Format-only handoff normalization may occur before W1; candidate mutation still requires W1 and packaging still requires W2.
- Never infer approval from filenames or prose. Only exact recognized envelope fields or an explicit owner record may establish approval.
- Preserve every original handoff member byte-for-byte; write canonical metadata into a new workspace/package and never modify the source ZIP.
- Generated plugins require Agent Plugins 1.0 root `plugin.json`; `.codex-plugin/plugin.json` is a synchronized compatibility overlay, not the portable authority.
- Final plugin ZIPs contain exactly one top-level directory matching the portable manifest's lowercase kebab-case `name`.
- Required portable-format, overlay-synchronization, package-envelope, or evidence-closure failures block W2/package completion and cannot be waived.
- Identical approved inputs, owner decisions, adapter version, and tool versions produce byte-identical canonical JSON and ZIP outputs.
- Preserve `0.1.0` runtime evidence and test ZIPs as immutable diagnostics; do not overwrite or relabel them as `0.1.1` evidence.
- Generated and diagnostic output remains under ignored `dist` or `.tmp` roots; tests use isolated temporary directories and leave tracked files unchanged.
- No upload, installation, publication, marketplace mutation, Git push, tag, or release occurs without separate authorization.

## Review Focus

- A legacy handoff declares a directory artifact plus a conflicting canonical filename; Task 4 tests that normalization blocks without overwriting and preserves the source ZIP.
- A portable manifest and legacy overlay disagree only in default-prompt type or order; Task 1 tests that synchronization reports a required mismatch rather than normalizing silently.
- A wrapped update baseline contains unrelated files alongside managed files; Task 3 tests plugin-relative byte preservation and a single wrapping directory after repackaging.
- An evidence result references a valid-looking digest whose file is mentioned inside another record but absent as a standalone member; Task 6 tests that evidence packaging fails with no output ZIP.
- A recognized legacy envelope has `specification_state: approved` but missing approval evidence or a blocking unresolved decision; Task 4 tests that it remains F1 and never becomes approved.

---

### Task 1: Agent Plugins 1.0 manifest and compatibility-overlay primitives

**Files:**
- Create: `src/obvious_one_plugin_framework/plugin_authoring/manifests.py`
- Modify: `src/obvious_one_plugin_framework/plugin_authoring/validation.py`
- Modify: `src/obvious_one_plugin_framework/plugin_authoring/__init__.py`
- Create: `tests/framework/test_plugin_authoring_manifests.py`
- Modify: `tests/framework/test_plugin_authoring_validation.py`

**Interfaces:**
- Consumes: JSON-compatible portable or legacy manifest objects and a plugin root.
- Produces: `PORTABLE_PLUGIN_SCHEMA`, `portable_manifest_from_legacy(payload)`, `legacy_overlay_from_portable(payload)`, `materialize_manifest_pair(root)`, `validate_portable_manifest(root)`, `validate_manifest_pair(root)`, and updated `validate_plugin_tree(root)`.

- [ ] **Step 1: Write failing portable-manifest shape tests**

Add tests named `test_portable_manifest_requires_agent_plugins_schema_and_openai_extension`, `test_portable_manifest_rejects_legacy_root_keys`, `test_short_description_is_at_most_thirty_characters`, and `test_portable_discovery_uses_fixed_skills_and_mcp_locations`. Assert exact `ValidationIssue` codes and paths for root `plugin.json`.

- [ ] **Step 2: Write failing conversion and synchronization tests**

Add tests named `test_legacy_manifest_converts_to_portable_without_losing_identity`, `test_portable_manifest_generates_legacy_overlay`, `test_manifest_pair_rejects_identity_presentation_and_prompt_order_drift`, and `test_materialize_manifest_pair_is_deterministic`. Include string and ordered-array `defaultPrompt` fixtures.

- [ ] **Step 3: Run Task 1 tests and verify RED**

Run: `python -B -m unittest tests.framework.test_plugin_authoring_manifests tests.framework.test_plugin_authoring_validation -v`

Expected: FAIL because `plugin_authoring.manifests` and portable-root validation do not exist.

- [ ] **Step 4: Implement manifest conversion and materialization**

Implement the exact interfaces above. Portable manifests use `$schema: "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"`, fixed root discovery locations, and `extensions.com.openai.interface`. Legacy conversion removes portable-forbidden root keys and maps their supported values into the OpenAI extension. Materialization writes canonical sorted JSON transactionally and derives only the missing side of a pair; an existing mismatch remains an error.

- [ ] **Step 5: Replace legacy-only plugin validation**

Make `validate_plugin_tree(root)` require root `plugin.json`, validate skills/references as before, and call `validate_manifest_pair(root)` when the overlay exists. Retain stable legacy issue codes only where existing tests or stored evidence depend on them; introduce explicit `portable_manifest_*` and `manifest_pair_*` codes for new failures.

- [ ] **Step 6: Run Task 1 tests and existing framework regression tests**

Run: `python -B -m unittest tests.framework.test_plugin_authoring_manifests tests.framework.test_plugin_authoring_validation tests.framework.test_plugin_authoring_materialize -v`

Expected: PASS.

- [ ] **Step 7: Commit Task 1**

```powershell
git add src/obvious_one_plugin_framework/plugin_authoring tests/framework/test_plugin_authoring_manifests.py tests/framework/test_plugin_authoring_validation.py
git commit -m "fix: validate portable plugin manifest pairs"
```

---

### Task 2: Plan and candidate integration for dual manifests

**Files:**
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/implementation_plan.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/candidate.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/update_candidate.py`
- Modify: `applications/plugin-builder/tests/fixtures/plan-create.json`
- Modify: `applications/plugin-builder/tests/test_planning_workflow.py`
- Modify: `applications/plugin-builder/tests/test_create_candidate.py`
- Modify: `applications/plugin-builder/tests/test_update_candidate.py`
- Modify: `applications/plugin-builder/tests/test_review_regressions.py`

**Interfaces:**
- Consumes: Task 1 `materialize_manifest_pair`, existing semantic plan proposals, and W1-bound plan hashes.
- Produces: canonical plan expected members containing both manifests, candidate trees containing a valid synchronized pair, and update candidates that preserve or deliberately migrate the pair.

- [ ] **Step 1: Write failing plan-normalization tests**

Add `test_plan_requires_portable_manifest_and_declares_compatibility_overlay`, `test_legacy_overlay_only_proposal_is_adapted_before_w1`, and `test_manifest_pair_is_part_of_plan_and_tools_hash_invalidation`. Assert that W1 summaries expose the portable authority and overlay decision.

- [ ] **Step 2: Write failing create/update candidate tests**

Add `test_create_candidate_materializes_portable_and_legacy_manifests`, `test_update_adds_portable_manifest_to_legacy_baseline`, and `test_update_rejects_unapproved_manifest_identity_change`. Compare names, versions, interface fields, and exact unaffected bytes.

- [ ] **Step 3: Run Task 2 tests and verify RED**

Run: `python -B -m unittest applications.plugin-builder.tests.test_planning_workflow applications.plugin-builder.tests.test_create_candidate applications.plugin-builder.tests.test_update_candidate applications.plugin-builder.tests.test_review_regressions -v`

Expected: FAIL because plans and candidates still treat only `.codex-plugin/plugin.json` as authoritative.

- [ ] **Step 4: Canonicalize manifest intent during plan compilation**

Update `compile_plan(inspection, proposal, output)` so `expected_members` always closes over root `plugin.json` plus the compatibility overlay. Accept an old overlay-only proposal only through Task 1's deterministic adapter, record `ADAPT` in implementation decisions, and include the resulting identities in the canonical plan bytes before W1 hashing.

- [ ] **Step 5: Materialize and verify the pair during create/update**

After approved file recipes are materialized or overlaid, call `materialize_manifest_pair(candidate)`, then fail candidate construction if `validate_manifest_pair(candidate)` returns issues. Ensure candidate manifest `expected_members`, member records, content-tree identity, and update change records include both files.

- [ ] **Step 6: Migrate the shared plan fixture to portable authority**

Replace the fixture's legacy-only manifest recipe with root Agent Plugins 1.0 `plugin.json`, retain the overlay as a derived expected member, and update literal hashes/member lists in affected tests. Keep one dedicated legacy-proposal fixture inside the adaptation test rather than making it the normal path.

- [ ] **Step 7: Run Task 2 suites**

Run: `python -B -m unittest applications.plugin-builder.tests.test_planning_workflow applications.plugin-builder.tests.test_create_candidate applications.plugin-builder.tests.test_update_candidate applications.plugin-builder.tests.test_review_regressions -v`

Expected: PASS.

- [ ] **Step 8: Commit Task 2**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core applications/plugin-builder/tests/fixtures/plan-create.json applications/plugin-builder/tests/test_planning_workflow.py applications/plugin-builder/tests/test_create_candidate.py applications/plugin-builder/tests/test_update_candidate.py applications/plugin-builder/tests/test_review_regressions.py
git commit -m "fix: generate synchronized plugin manifests"
```

---

### Task 3: Single-directory plugin ZIPs and update-baseline compatibility

**Files:**
- Modify: `src/obvious_one_plugin_framework/plugin_authoring/identity.py`
- Modify: `src/obvious_one_plugin_framework/plugin_authoring/archive.py`
- Modify: `src/obvious_one_plugin_framework/plugin_authoring/__init__.py`
- Modify: `tests/framework/test_plugin_authoring_archive.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/inspection.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/packaging.py`
- Modify: `applications/plugin-builder/tests/test_inspection.py`
- Modify: `applications/plugin-builder/tests/test_update_candidate.py`
- Modify: `applications/plugin-builder/tests/test_final_packaging.py`

**Interfaces:**
- Consumes: Task 1 portable manifest identity, safe archive inventory/extraction, and a W2-approved candidate tree.
- Produces: `write_deterministic_zip(root, destination, *, prefix=None)`, `locate_plugin_archive_root(extracted_root)`, logical plugin-relative update baselines, and final ZIPs rooted at `<plugin-name>/`.

- [ ] **Step 1: Write failing prefixed-ZIP and root-location tests**

Add `test_deterministic_zip_can_prefix_every_member`, `test_locate_plugin_archive_root_accepts_portable_single_directory`, `test_locate_plugin_archive_root_accepts_legacy_flat_tree_for_update_only`, and `test_locate_plugin_archive_root_rejects_multiple_top_level_directories`. Assert sorted member names and repeatable ZIP hashes.

- [ ] **Step 2: Write failing packaging and update tests**

Change packaging expectations to `<name>/plugin.json`, `<name>/.codex-plugin/plugin.json`, and other candidate members below one directory. Add `test_wrapped_update_baseline_preserves_unrelated_plugin_relative_bytes` and `test_legacy_flat_baseline_is_migrated_to_wrapped_output`.

- [ ] **Step 3: Run Task 3 tests and verify RED**

Run: `python -B -m unittest tests.framework.test_plugin_authoring_archive applications.plugin-builder.tests.test_inspection applications.plugin-builder.tests.test_update_candidate applications.plugin-builder.tests.test_final_packaging -v`

Expected: FAIL because the ZIP writer emits flat member paths and baseline extraction assumes a flat tree.

- [ ] **Step 4: Add deterministic member prefixing and archive-root detection**

Extend `write_deterministic_zip` with a validated lowercase kebab-case `prefix`. Add `locate_plugin_archive_root` that returns the logical plugin root after safe extraction and reports whether the envelope was `PORTABLE_SINGLE_DIRECTORY` or `LEGACY_FLAT` without accepting ambiguous mixed roots.

- [ ] **Step 5: Normalize update baselines to plugin-relative workspace layout**

During update inspection, extract into a temporary raw root, locate the logical plugin root, then transactionally install its children at `workspace/baseline`. Record source archive envelope/profile and original archive hash in inspection/session evidence. Preserve byte identities and unrelated members.

- [ ] **Step 6: Package and validate the wrapped artifact**

Read the plugin name from root `plugin.json`, write the final ZIP with that prefix, extract it into a temporary validation root, locate the enclosed plugin directory, and run plugin, skill, tool-binding, and safety validation there. Package metadata must distinguish candidate tree identity from final archive member identity.

- [ ] **Step 7: Run Task 3 suites**

Run: `python -B -m unittest tests.framework.test_plugin_authoring_archive applications.plugin-builder.tests.test_inspection applications.plugin-builder.tests.test_update_candidate applications.plugin-builder.tests.test_final_packaging -v`

Expected: PASS, including two-build byte equality.

- [ ] **Step 8: Commit Task 3**

```powershell
git add src/obvious_one_plugin_framework/plugin_authoring applications/plugin-builder/scripts/plugin_builder_core/inspection.py applications/plugin-builder/scripts/plugin_builder_core/packaging.py tests/framework/test_plugin_authoring_archive.py applications/plugin-builder/tests/test_inspection.py applications/plugin-builder/tests/test_update_candidate.py applications/plugin-builder/tests/test_final_packaging.py
git commit -m "fix: package plugins in portable zip envelopes"
```

---

### Task 4: Deterministic canonical handoff normalization

**Files:**
- Create: `applications/plugin-builder/scripts/plugin_builder_core/handoff_normalization.py`
- Create: `applications/plugin-builder/tests/fixtures/design-package-legacy/WORKBENCH_HANDOFF.md`
- Create: `applications/plugin-builder/tests/fixtures/design-package-legacy/workbench_handoff_manifest.json`
- Create: `applications/plugin-builder/tests/fixtures/design-package-legacy/Sample_Application_Spec_v1.1_APPROVED.md`
- Create: `applications/plugin-builder/tests/fixtures/design-package-legacy/professional_knowledge/reference.md`
- Create: `applications/plugin-builder/tests/test_handoff_normalization.py`

**Interfaces:**
- Consumes: a source ZIP path, a destination input tree, optional normalized ZIP destination, and approved runtime scope.
- Produces: `HandoffNormalizationOutcome`, `classify_handoff_profile(inventory, extracted_root)`, and `normalize_handoff_archive(source, destination_root, normalized_zip=None, runtime_scope="OPENAI_ONLY_PHASE_ONE")` with report schema `plugin-builder-handoff-normalization-v1`.

- [ ] **Step 1: Write failing profile-classification tests**

Add `test_canonical_v1_profile_is_detected`, `test_legacy_workbench_v1_profile_is_detected_from_structure_and_fields`, `test_unknown_profile_blocks`, and `test_multiple_authoritative_specs_are_ambiguous`. Do not classify solely from filenames.

- [ ] **Step 2: Write failing trust and mapping tests**

Add `test_legacy_profile_maps_exact_fields_and_expands_directory_artifact`, `test_missing_approval_evidence_remains_pending`, `test_blocking_owner_decision_prevents_approval`, `test_filename_approved_does_not_establish_approval`, and `test_confirmed_by_is_a_role_not_a_fabricated_person`.

- [ ] **Step 3: Write failing preservation, collision, and determinism tests**

Add `test_original_members_are_byte_identical_after_normalization`, `test_canonical_filename_collision_blocks_without_overwrite`, `test_empty_or_escaping_declared_prefix_blocks`, and `test_repeated_normalization_is_byte_identical`. Verify source ZIP bytes remain unchanged after every outcome.

- [ ] **Step 4: Run normalization tests and verify RED**

Run: `python -B -m unittest applications.plugin-builder.tests.test_handoff_normalization -v`

Expected: FAIL because `handoff_normalization.py` does not exist.

- [ ] **Step 5: Implement exact profile and field mapping**

Implement the design's `CANONICAL_V1`, `LEGACY_WORKBENCH_V1`, `UNKNOWN`, and `AMBIGUOUS` outcomes. Expand declared directory prefixes in sorted POSIX order; create canonical artifact IDs as `<artifact_id>/<relative-descendant-path>`; copy only explicit requirements; and mark every canonical field `COPIED`, `MECHANICALLY_DERIVED`, `OWNER_SUPPLIED`, or `UNRESOLVED`.

- [ ] **Step 6: Implement transactional canonical sidecar and ZIP output**

Preserve extracted original bytes, add canonical files only after collision checks, write canonical ASCII-safe sorted JSON, optionally write a deterministic normalized ZIP, and emit source/output archive and tree identities. No failure may leave a partial destination or overwrite a previous valid normalized package.

- [ ] **Step 7: Run normalization tests**

Run: `python -B -m unittest applications.plugin-builder.tests.test_handoff_normalization -v`

Expected: PASS.

- [ ] **Step 8: Commit Task 4**

```powershell
git add applications/plugin-builder/scripts/plugin_builder_core/handoff_normalization.py applications/plugin-builder/tests/fixtures/design-package-legacy applications/plugin-builder/tests/test_handoff_normalization.py
git commit -m "feat: normalize legacy workbench handoffs"
```

---

### Task 5: Integrate normalization with inspect, sessions, CLI, and skills

**Files:**
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/inspection.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/session_contract.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder.py`
- Modify: `applications/plugin-builder/tests/test_inspection.py`
- Modify: `applications/plugin-builder/tests/test_tool_contracts.py`
- Modify: `applications/plugin-builder/skills/guiding-plugin-builder-sessions/SKILL.md`
- Modify: `applications/plugin-builder/skills/guiding-plugin-builder-sessions/references/session-workflow.md`
- Modify: `applications/plugin-builder/skills/planning-plugin-implementations/references/input-and-plan-contract.md`
- Modify: `applications/plugin-builder/tests/test_skill_contracts.py`

**Interfaces:**
- Consumes: Task 4 normalizer and the existing `inspect DESIGN_PACKAGE` command.
- Produces: automatic canonical/legacy intake, optional `inspect --normalized-package PATH`, persisted normalization identity, and one-question recovery for unknown/ambiguous inputs.

- [ ] **Step 1: Write failing inspect/CLI integration tests**

Add `test_inspect_accepts_legacy_package_and_persists_normalization_report`, `test_inspect_writes_requested_normalized_package`, `test_unknown_package_stays_f1_with_one_decision`, `test_ambiguous_package_lists_conflicts_without_selecting`, and `test_normalized_package_passes_fresh_canonical_inspection`.

- [ ] **Step 2: Write failing session and skill-contract tests**

Require session v2 inspection identity to include source hash, profile, normalized tree/archive hash, and report hash using only relative paths. Require the session skill to explain canonical pass-through, legacy adaptation, blocked ambiguity, and non-inference of approval.

- [ ] **Step 3: Run Task 5 tests and verify RED**

Run: `python -B -m unittest applications.plugin-builder.tests.test_inspection applications.plugin-builder.tests.test_tool_contracts applications.plugin-builder.tests.test_skill_contracts -v`

Expected: FAIL because inspection directly requires canonical files and the CLI has no normalized-package option.

- [ ] **Step 4: Route inspect through normalization**

Call `normalize_handoff_archive` inside the existing transactional inspection staging root. Validate the generated canonical files with current intake rules, store `normalization-report.json` and `normalized-input.zip`, and bind the session to both source and normalized identities. Unknown/ambiguous inputs produce F1 workspaces and reports without planning authority.

- [ ] **Step 5: Extend CLI and session validation**

Add optional `--normalized-package PATH` to `inspect`; reject destinations equal to the source, inside the source archive, or escaping the caller-selected location. Extend `_validate_v2` with an exact normalization object while keeping existing v1 and canonical-v2 sessions readable or migrating them deterministically.

- [ ] **Step 6: Update portable skills and routing references**

Use `skill-creator` guidance while editing skills. Keep routing in `SKILL.md`, detailed mapping/recovery in the referenced workflow, and make clear that normalization does not constitute W1 candidate mutation.

- [ ] **Step 7: Run Task 5 suites**

Run: `python -B -m unittest applications.plugin-builder.tests.test_inspection applications.plugin-builder.tests.test_tool_contracts applications.plugin-builder.tests.test_skill_contracts -v`

Expected: PASS.

- [ ] **Step 8: Commit Task 5**

```powershell
git add applications/plugin-builder/scripts/plugin_builder.py applications/plugin-builder/scripts/plugin_builder_core/inspection.py applications/plugin-builder/scripts/plugin_builder_core/session_contract.py applications/plugin-builder/skills applications/plugin-builder/tests/test_inspection.py applications/plugin-builder/tests/test_tool_contracts.py applications/plugin-builder/tests/test_skill_contracts.py
git commit -m "feat: route intake through handoff normalization"
```

---

### Task 6: Digest-addressed runtime evidence closure

**Files:**
- Create: `applications/plugin-builder/scripts/plugin_builder_core/evidence.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder.py`
- Create: `applications/plugin-builder/tests/test_runtime_evidence_packaging.py`
- Modify: `applications/plugin-builder/tests/test_runtime_evidence_contract.py`
- Modify: `applications/plugin-builder/tests/runtime/T1-T7-runtime-scenarios.md`
- Modify: `applications/plugin-builder/tests/runtime/runtime-result-schema.json`

**Interfaces:**
- Consumes: one runtime-result JSON, an evidence root containing digest-named files, and an output ZIP path.
- Produces: `EvidenceBundleOutcome`, `validate_runtime_result(payload)`, `build_runtime_evidence_bundle(result_path, evidence_root, destination)`, and CLI `package-runtime-evidence --result RESULT --evidence-root ROOT --output ZIP --json`.

- [ ] **Step 1: Write failing result-validation and closure tests**

Add `test_every_non_null_scenario_digest_requires_exactly_one_member`, `test_mentioned_but_absent_digest_is_rejected`, `test_wrong_digest_or_size_is_rejected`, `test_unindexed_extra_evidence_is_rejected`, and `test_tool_contract_identity_is_not_mistaken_for_scenario_evidence`.

- [ ] **Step 2: Write failing deterministic-bundle tests**

Add `test_bundle_contains_digest_named_result_evidence_and_index`, `test_two_evidence_bundles_are_byte_identical`, and `test_failed_rebuild_preserves_previous_valid_bundle`. Assert the attached result document is itself stored under its actual SHA-256.

- [ ] **Step 3: Run Task 6 tests and verify RED**

Run: `python -B -m unittest applications.plugin-builder.tests.test_runtime_evidence_packaging applications.plugin-builder.tests.test_runtime_evidence_contract -v`

Expected: FAIL because evidence packaging and closure validation do not exist.

- [ ] **Step 4: Implement focused standard-library result validation**

Validate the exact runtime-result keys, T1–T7 uniqueness/completeness, evidence-state and test-result enums, SHA-256 syntax, runtime identity, and tool rows needed by the shipped runtime kit. Keep the JSON Schema as the normative document and ensure tests compare the focused validator with representative schema-valid and schema-invalid fixtures.

- [ ] **Step 5: Implement transactional evidence bundling**

Resolve every non-null scenario digest to exactly one regular file whose stem and bytes match, include all and only indexed digest-addressed evidence, add the digest-named result JSON, write `evidence-index.json`, and create a deterministic ZIP. Emit no new ZIP when closure fails and preserve a previous valid bundle.

- [ ] **Step 6: Add the CLI and runtime instructions**

Add the exact parser arguments above, one ASCII-safe result envelope, and runtime instructions that require this command rather than manually constructing an evidence ZIP. Keep network and credential prohibitions explicit.

- [ ] **Step 7: Run Task 6 suites**

Run: `python -B -m unittest applications.plugin-builder.tests.test_runtime_evidence_packaging applications.plugin-builder.tests.test_runtime_evidence_contract -v`

Expected: PASS.

- [ ] **Step 8: Commit Task 6**

```powershell
git add applications/plugin-builder/scripts/plugin_builder.py applications/plugin-builder/scripts/plugin_builder_core/evidence.py applications/plugin-builder/tests/test_runtime_evidence_packaging.py applications/plugin-builder/tests/test_runtime_evidence_contract.py applications/plugin-builder/tests/runtime
git commit -m "feat: enforce runtime evidence closure"
```

---

### Task 7: Make Plugin Builder 0.1.1 itself portable and rebuildable

**Files:**
- Create: `applications/plugin-builder/plugin.json`
- Modify: `applications/plugin-builder/.codex-plugin/plugin.json`
- Modify: `applications/plugin-builder/openclaw/distribution.json`
- Modify: `applications/plugin-builder/scripts/build_marketplace_release.py`
- Modify: `applications/plugin-builder/scripts/distribution_audit.py`
- Modify: `applications/plugin-builder/tests/test_conversion_contract.py`
- Modify: `applications/plugin-builder/tests/test_distribution.py`
- Modify: `applications/plugin-builder/tests/test_marketplace_release.py`
- Modify: `applications/plugin-builder/tests/test_standalone_artifact.py`
- Modify: `applications/plugin-builder/README.md`
- Modify: `applications/plugin-builder/DISTRIBUTION.md`
- Modify: `applications/plugin-builder/docs/runtime-compatibility.md`
- Modify: `applications/plugin-builder/tests/coverage-matrix.md`

**Interfaces:**
- Consumes: Tasks 1–6 public framework and product APIs.
- Produces: a Plugin Builder `0.1.1` source/release manifest pair, vendored standalone artifact, updated deny-by-default distribution boundary, and runtime kit containing normalization and evidence-closure support.

- [ ] **Step 1: Write failing Plugin Builder source/release contract tests**

Require root `plugin.json`, synchronized identity with `.codex-plugin/plugin.json`, version `0.1.1`, current portable extension fields, distribution inclusion, and release output containing both manifests. Require release validation against the extracted installed artifact.

- [ ] **Step 2: Extend standalone T7 repository test expectations**

Run create from a legacy design handoff, generate a wrapped plugin ZIP with both manifests, use that ZIP as the update baseline, preserve unrelated bytes, execute the bundled tool, and package a closure-valid evidence bundle with the repository path absent from environment and working directory.

- [ ] **Step 3: Run Task 7 tests and verify RED**

Run: `python -B -m unittest applications.plugin-builder.tests.test_conversion_contract applications.plugin-builder.tests.test_distribution applications.plugin-builder.tests.test_marketplace_release applications.plugin-builder.tests.test_standalone_artifact -v`

Expected: FAIL because Plugin Builder itself lacks a portable root manifest and the release builder does not include new modules/contracts.

- [ ] **Step 4: Add and synchronize Plugin Builder manifests**

Create Agent Plugins 1.0 root `plugin.json`, update the overlay to `0.1.1`, and apply the same Task 1 pair validation used for generated plugins. Do not add an app dependency, external server, or publication metadata outside the approved private/local scope.

- [ ] **Step 5: Update release, vendoring, and distribution boundaries**

Include the portable manifest, new handoff/evidence modules, updated skills/references, schemas, and runtime instructions. Keep approved-design documents and development tests outside the installed runtime artifact unless the existing runtime-kit boundary explicitly includes a fixture copy.

- [ ] **Step 6: Update product documentation and evidence states**

Describe canonical/legacy intake, portable output layout, evidence command, and the exact remaining `NOT VERIFIED` runtime/application-behavior gates. Do not change readiness to `READY` based on repository-local tests.

- [ ] **Step 7: Run Task 7 suites**

Run: `python -B -m unittest applications.plugin-builder.tests.test_conversion_contract applications.plugin-builder.tests.test_distribution applications.plugin-builder.tests.test_marketplace_release applications.plugin-builder.tests.test_standalone_artifact -v`

Expected: PASS.

- [ ] **Step 8: Commit Task 7**

```powershell
git add applications/plugin-builder
git commit -m "chore: prepare Plugin Builder 0.1.1 artifact"
```

---

### Task 8: Full regression, installed-artifact generation, and release evidence

**Files:**
- Modify as failures require: only files already owned by Tasks 1–7
- Generate ignored output: `dist/plugin-builder/`

**Interfaces:**
- Consumes: completed Tasks 1–7.
- Produces: passing repository evidence, two byte-identical Plugin Builder `0.1.1` builds, verified runtime kit, and an exact remaining-gates report.

- [ ] **Step 1: Run the complete Plugin Builder product suite**

Run: `python -B -m unittest discover -s applications/plugin-builder/tests -v`

Expected: PASS with only documented platform skips.

- [ ] **Step 2: Run the complete generic framework suite**

Run: `python -B -m unittest discover -s tests/framework -v`

Expected: PASS with only documented platform skips.

- [ ] **Step 3: Run repository discovery and extraction verification**

Run: `python -B -m unittest tests.test_application_config tests.test_agents_contract -v`

Run: `python -B scripts/verify_extraction.py --application plugin-builder`

Expected: PASS and one valid machine-readable verification result where applicable.

- [ ] **Step 4: Run installed creator validations**

Validate Plugin Builder source, each of its four skills, the generated installed artifact, and each extracted generated test plugin using the currently installed Plugin Creator and Skill Creator validation contracts. Record exact tool versions and distinguish static contract review from executable validator evidence.

- [ ] **Step 5: Build twice and compare identities**

Build Plugin Builder `0.1.1` and its runtime kit into two isolated ignored roots. Assert byte equality for installable ZIPs, normalized handoff fixture ZIPs, runtime-kit members, content manifests, and result documents.

- [ ] **Step 6: Verify Git and repository cleanliness**

Run: `git diff --check`

Run: `git status --short`

Expected: no unintended changes, generated files, nested Git metadata, source ZIPs, credentials, or private paths.

- [ ] **Step 7: Commit any documentation-only evidence updates**

```powershell
git add applications/plugin-builder/docs applications/plugin-builder/tests/coverage-matrix.md
git commit -m "test: record Plugin Builder 0.1.1 local evidence"
```

Skip the commit when Task 8 produces no tracked evidence change.

---

### Task 9: Target-runtime replay and application-behavior boundary

**Files:**
- Input/output only: generated `dist/plugin-builder/` runtime kit and decision-owner returned runtime evidence
- Modify after returned evidence is independently verified: `applications/plugin-builder/docs/runtime-compatibility.md`
- Modify after returned evidence is independently verified: `applications/plugin-builder/tests/coverage-matrix.md`

**Interfaces:**
- Consumes: Task 8 byte-verified Plugin Builder `0.1.1` ZIP/runtime kit.
- Produces: schema-valid, closure-valid T1–T7 results for ChatGPT Work Local/Desktop and Codex, generated plugin ZIPs, and an honest compatibility/readiness classification.

- [ ] **Step 1: Run T1–T7 in ChatGPT Work Local/Desktop**

Install the exact Task 8 artifact in a clean task with the repository absent. Run the supplied scenarios, including legacy handoff normalization, create, update, required failure, optional unavailable capability, wrapped package validation, bundled tool execution, and evidence packaging.

- [ ] **Step 2: Run T1–T7 in Codex**

Repeat against the same artifact hash in a clean Codex task. Discovery, execution, and generated artifacts require separate direct observations.

- [ ] **Step 3: Independently verify returned evidence**

Check runtime-result schema, artifact hash, all evidence-member hashes and closure, generated plugin manifest pairs, single-directory archive envelopes, tool bindings, update preservation, and absence of network/credential/source-repository use.

- [ ] **Step 4: Run representative Cool Sermon Coach conversations separately**

Exercise normal routing, four checkpoints, missing-input behavior, professional-reference routing, bundled sermon-state tool use, required-tool failure, optional-source limitation, direct-answer pressure, and explicit exclusions in both runtimes. Do not count structural or T1–T7 pipeline evidence as application-conversation evidence.

- [ ] **Step 5: Update readiness evidence without overclaiming**

Record each gate as `PASS`, `FAIL`, `NOT VERIFIED`, or `NOT APPLICABLE` and each evidence layer as `EXPECTED`, `STATICALLY VERIFIED`, `RUNTIME VERIFIED`, or `NOT VERIFIED`. If either runtime or required behavior remains unverified, retain:

```text
CONVERSION COMPLETE — RUNTIME VALIDATION PENDING
```

Do not report `READY` until all applicable mandatory gates pass.

- [ ] **Step 6: Commit verified runtime evidence summaries**

```powershell
git add applications/plugin-builder/docs/runtime-compatibility.md applications/plugin-builder/tests/coverage-matrix.md
git commit -m "test: record Plugin Builder 0.1.1 runtime evidence"
```

Do not commit private raw logs, user content, generated plugin ZIPs, or external absolute paths.

## Plan self-review result

- **Spec coverage:** Tasks 1–3 cover PB-COMPAT-001; Tasks 4–5 cover PB-COMPAT-002; Task 6 covers PB-EVID-001; Tasks 7–9 cover product integration, deterministic delivery, runtime replay, and readiness boundaries.
- **Step scan:** Every implementation task follows RED, minimal implementation, GREEN, and reviewable commit boundaries. Task 8 is aggregate verification; Task 9 is external runtime evidence, not product code.
- **Type consistency:** Manifest, normalization, archive-root, and evidence APIs are introduced once in their owning tasks and consumed by named later tasks.
- **Review focus:** Each of the five high-risk inputs has an explicit named test in Tasks 1, 3, 4, or 6.
- **Scope:** The plan modifies only Plugin Builder and reusable plugin-authoring primitives required by the approved compatibility correction. Producer-side Design Assistant changes and publication remain out of scope.
