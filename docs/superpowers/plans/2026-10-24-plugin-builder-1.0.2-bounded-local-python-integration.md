# Plugin Builder 1.0.2 Bounded Local-Python Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate conditional direct-local v2 and safe plugin-root path validation into the current Workbench Plugin Builder without importing the review ZIP's stale snapshot.

**Architecture:** Add v2 as a new immutable adapter identity while keeping v1 test-only and W1/W2 evidence rules unchanged. Change canonical framework path validation, then regenerate its vendored copy through the existing release process. Only after focused regressions pass, update 1.0.2 metadata and verify an extracted deterministic artifact.

**Tech Stack:** Python 3.11+, standard-library `unittest`, PowerShell Windows test runner, existing Plugin Builder release builder.

**Spec:** `docs/superpowers/specs/2026-10-23-plugin-builder-1.0.2-bounded-local-python-integration-design.md`

## Global Constraints

- Phase-one targets remain Codex and ChatGPT Work Local/Desktop (`OPENAI_ONLY_PHASE_ONE`); OpenClaw is not a new target.
- The review ZIP is test/design input only. Never apply its patch or copy its installed-source snapshot wholesale.
- Preserve `direct-local` v1 behavior, strict hashes and approval gates, delegated-reference validation, and current MCP timeout/listener/chunked-read safeguards.
- Installed execution remains `NOT VERIFIED` until observed in each named runtime. Local operation success cannot satisfy `REQUIRED_BEFORE_W2`.
- Use the canonical Windows probe/runner with genuine system temp and UTF-8. Classify failures before changing production code.
- No dependency installation, marketplace mutation, push, tag, or publication is in scope.

## Review Focus

1. A v1 plan targeting `OPENAI_PORTABLE_PLUGIN` must remain blocked even after v2 is added (Task 1).
2. A v2 declaration with an empty setup owner or a blank item among setup steps must fail rather than silently becoming installable (Task 1).
3. A `tools/...` path that exists through a symlink/reparse escape must be invalid even when its textual path is safe (Task 3).
4. Mentioning `tools/run.py` in a Skill without its stable tool ID and exposed capability must not satisfy tool routing (Task 3).
5. A successful build-host Python run must not promote installed realization, and `REQUIRED_BEFORE_W2` must still block packaging (Task 2).

## File map

- `applications/plugin-builder/scripts/plugin_builder_core/runtime_adapters.py`: registry identity and v2 declaration validation only.
- `applications/plugin-builder/tests/test_runtime_adapters.py`: adapter unit and fail-closed cases.
- `applications/plugin-builder/tests/test_candidate_verification.py`, `test_planning_workflow.py`: W1/W2 integration and evidence separation.
- `src/obvious_one_plugin_framework/plugin_authoring/validation.py`: canonical path-binding scope and containment.
- `tests/framework/test_plugin_authoring_path_bindings.py`: path cases; existing direct-route assertion must move to the tool-routing layer rather than being reinterpreted as a missing path.
- `applications/plugin-builder/tests/test_candidate_verification.py`: stable tool-ID/capability routing regression using existing verified-candidate helpers.
- Release output `plugins/plugin-builder/scripts/vendor/obvious_one_plugin_framework/plugin_authoring/validation.py`: generated artifact only; no corresponding tracked source file exists.
- `applications/plugin-builder/{plugin.json,.codex-plugin/plugin.json,openclaw/distribution.json,docs/phase-one-scope.json,README.md,DISTRIBUTION.md,THIRD_PARTY_NOTICES.md,docs/runtime-compatibility.md,docs/source-decisions.md}`: consistent version intent and accurate unreleased evidence state.
- Version-pinned tests in `applications/plugin-builder/tests/{test_conversion_contract.py,test_distribution.py,test_marketplace_release.py,test_runtime_kit_builder.py,test_standalone_artifact.py}`: update only assumptions tied to current product version; retain historical 1.0.1 fixtures where they are intentionally historical.

---

### Task 1: Register conditional direct-local v2

**Files:** Modify `applications/plugin-builder/scripts/plugin_builder_core/runtime_adapters.py`; test `applications/plugin-builder/tests/test_runtime_adapters.py`.

**Interfaces:** Preserve `adapter_registry() -> tuple[AdapterDefinition, ...]`, `adapter_registry_sha256() -> str`, and `validate_realization_against_registry(realization: dict[str, Any], *, installation_channel: str) -> tuple[tuple[str, ...], tuple[str, ...]]`. Produce `direct-local` / `2` with `DIRECT_LOCAL`, `DIRECT_ARGV`, `USER_DEVICE`, phase-one targets, and portable installation channel.

- [ ] **Step 1: Write failing registry tests.** Assert sorted registry contains both `("direct-local", "1")` and `("direct-local", "2")`; v1 portable channel still returns `channel_unsupported`; v2 with `FEASIBLE_WITH_SETUP`, named owner, nonblank setup steps, and `DEFERRED_ALLOWED` or `REQUIRED_BEFORE_W2` has no registry error/blocker for each phase-one target. Assert unknown target/channel and mismatched mechanism/transport/location fail.
- [ ] **Step 2: Write failing policy tests.** Assert exact v2 diagnostics for wrong feasibility state, missing/blank owner, absent/empty/blank/nonstring steps, and missing/unsupported evidence policy. Do not accept an implicit v1 upgrade.
- [ ] **Step 3: Run only `test_runtime_adapters` through `scripts/invoke_windows_test_environment.ps1`; record expected failing assertions.**
- [ ] **Step 4: Implement v2 definition and validation inside the existing registry function.** Leave v1 definition untouched; update the pinned registry SHA-256 test to the digest produced by canonical sorted records after the other assertions pass.
- [ ] **Step 5: Rerun focused adapter tests via the Windows runner; expect PASS. Commit this isolated adapter change.**

### Task 2: Verify W1/W2 semantics for v2

**Files:** Test `applications/plugin-builder/tests/test_planning_workflow.py`, `test_candidate_verification.py`; modify `applications/plugin-builder/scripts/plugin_builder_core/{implementation_plan.py,approvals.py,verification.py}` only if a focused test proves a genuine gap.

**Interfaces:** Consume Task 1's `validate_realization_against_registry`; preserve existing plan hash, W1 authorization, and W2 `REQUIRED_BEFORE_W2` behavior.

- [ ] **Step 1: Add a v2 plan fixture from existing generated proposal helpers.** Declare Python dependency, filesystem permissions, stable tool ID, exposed capability, explicit setup and fallback. Assert W1 plan captures these fields and changing them invalidates the approved plan hash.
- [ ] **Step 2: Add a candidate test for both evidence policies.** A build-host direct Python operation may pass while installed realization remains `NOT VERIFIED`; `REQUIRED_BEFORE_W2` blocks W2/package, whereas `DEFERRED_ALLOWED` retains the unverified state without claiming installed success.
- [ ] **Step 3: Run the two focused test modules through the Windows runner.** If they pass on existing implementation, make no production change; if not, correct the smallest responsible implementation path without weakening identity or approval checks.
- [ ] **Step 4: Rerun focused tests; expect PASS. Commit tests and any necessary minimal integration correction.**

### Task 3: Resolve explicit plugin-root paths safely

**Files:** Modify `src/obvious_one_plugin_framework/plugin_authoring/validation.py`; test `tests/framework/test_plugin_authoring_path_bindings.py` and `applications/plugin-builder/tests/test_candidate_verification.py`.

**Interfaces:** Preserve `validate_path_bindings(root: Path) -> tuple[ValidationIssue, ...]` and existing issue codes. In `SKILL.md` only, `tools/...` and `skills/...` resolve beneath plugin root for existence/containment; other safe relative tokens remain skill-relative. This validation does not authorize direct invocation.

- [ ] **Step 1: Replace the old “`tools/run.py` is missing from the Skill directory” assertion.** Assert a real root `tools/run.py` and a real `skills/other/SKILL.md` pass; nonexistent root members produce `path_binding_missing`; skill-local `references/method.md` remains skill-relative.
- [ ] **Step 2: Add negative path cases.** Assert traversal, absolute/drive, backslash, and symlink/reparse escape yield `path_binding_invalid`; record platform skip only for an unavailable native link capability and retain the non-link containment tests.
- [ ] **Step 3: Add the separate product routing regression using the verified-candidate fixture.** A Skill mentioning only `tools/normalize.py` must not satisfy the declared `normalize-input` tool ID and exposed capability; adding those strings does.
- [ ] **Step 4: Run the focused framework and product tests through the Windows runner; confirm the new positive/negative cases fail for the intended reason.**
- [ ] **Step 5: Implement the narrow scope selection and resolved-path containment in canonical validation only.** Keep reference closure and delegated-reference invocation unchanged.
- [ ] **Step 6: Rerun focused path/routing tests plus `test_mcp_local_verification`; expect PASS. Commit canonical source and tests.**

### Task 4: Set coherent 1.0.2 metadata and regenerate the release copy

**Files:** Modify only the version/accurate-status files named in the file map and their version-pinned tests; generated vendor path is output.

**Interfaces:** `build_marketplace_release.py` consumes source manifests with equal name/version and `skills: "./skills/"`; current version becomes `1.0.2`. Historical publication of 1.0.1 remains a fact, not a 1.0.2 publication claim.

- [ ] **Step 1: Update version-pinned tests to expect 1.0.2 where they assert the current product or release build; leave historical fixture assertions intact. Run focused conversion/distribution/release tests and confirm version-related failures.**
- [ ] **Step 2: Update both manifests, distribution and phase-one-scope metadata, and concise release/compatibility copy.** Keep `./skills/` in the Codex overlay; describe v2 as conditional and installed state as `NOT VERIFIED`. Do not claim 1.0.2 is published.
- [ ] **Step 3: Use the existing release builder to produce an isolated candidate and generate its vendored canonical validator.** Compare source and generated vendor content; ensure `delegated_references.py` stays included and the review ZIP's stale MCP file was not copied.
- [ ] **Step 4: Run focused conversion, distribution, marketplace-release, runtime-kit, standalone-artifact, and validator tests through the Windows runner; expect PASS. Commit metadata and version tests, not generated release output.**

### Task 5: Complete repository and artifact verification

**Files:** No intentional product changes; diagnostics under ignored `dist/` or `.tmp/` only.

**Interfaces:** Consume Tasks 1–4; produce evidence for a reviewed local 1.0.2 candidate, not a publication or installed-runtime claim.

- [ ] **Step 1: Run the canonical Windows environment probe once.** If blocked, classify `ENVIRONMENT` and correct the environment without changing product behavior.
- [ ] **Step 2: Run full Plugin Builder product tests, framework tests, handoff interoperability, and `python -B scripts/verify_extraction.py --application plugin-builder` through the Windows runner.** Triage any failure by first representative cause; rerun the smallest affected set before a full rerun.
- [ ] **Step 3: Build 1.0.2 twice in independent isolated roots, verify byte identity, manifest pair, member hashes, extracted tree, and standalone create/update/runtime-kit behavior.** Use the current release script; do not use the ZIP review snapshot as release input.
- [ ] **Step 4: Run `git diff --check`, review exact branch delta for only approved changes, and report Git status, test counts, skips, artifact paths/digests, and all unverified installed-runtime rows.** Commit any test/evidence-only correction separately.
- [ ] **Step 5: Stop before any push, marketplace mutation, tag, upload, or publication.** Installed Skill→Python→result trials in Codex and ChatGPT Work Local/Desktop remain a separate runtime-evidence step; do not infer PASS from repository tests.
