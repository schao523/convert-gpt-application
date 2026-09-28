# Cool Bible Tutor Schema-v3 Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate Cool Bible Tutor's application-owned OpenClaw distribution contract to schema v3, move its preparation-catalog entry from legacy verification to deterministic build mode, and restore a green repository-wide test state before pushing `main`.

**Architecture:** Preserve the existing selected-file and RAG boundaries while adding explicit, non-overlapping text and binary content rules backed by the product's tracked licensing and provenance records. Keep ClawHub disabled because the package remains a bundle plugin, enable the existing GitHub marketplace surface, and exercise the unchanged builder and verifier rather than adding product-specific framework behavior.

**Tech Stack:** Python 3.11+, JSON distribution contracts, `unittest`, Obvious One schema-v3 package builder and marketplace catalog.

**Spec:** `docs/superpowers/specs/2026-09-20-framework-marketplace-hardening-design.md`

## Global Constraints

- Distribution schema v3 is required for builds; schema v1/v2 remain read-only legacy formats.
- Preserve all current Cool Bible Tutor selected files, RAG identities, asset groups, audit hook, version, and runtime behavior.
- Every packaged application-owned file must match exactly one approved text or binary content rule.
- Use existing `LICENSE`, `THIRD_PARTY_CONTENT.md`, `THIRD_PARTY_NOTICES.md`, and `DISTRIBUTION.md` as the rights and provenance record; do not infer new rights.
- GitHub marketplace publication is enabled; ClawHub remains disabled and `NOT APPLICABLE`.
- Do not mutate the marketplace repository, download assets, publish releases, or change another product's application behavior.

## Review Focus

- A selected path missing or matching multiple content rules must block validation before output mutation; covered by the real Cool package build.
- Binary SQLite and wheel bytes must remain exact; covered by repeated package-build manifest comparisons.
- Overlay `openclaw/README.md` must have an approved text rule and remain confined; covered by the real package build.
- Marketplace preparation must rebuild Cool rather than silently retaining legacy bytes; covered by catalog mode and repository verification tests.
- Existing exact retrieval and layered runtime behavior must survive the contract-only migration; covered by the Cool product suite.

---

### Task 1: Pin the approved schema-v3 and marketplace behavior

**Files:**
- Modify: `applications/cool-bible-tutor/tests/test_distribution.py`
- Modify: `applications/vibe-coding-designer/tests/test_marketplace_release.py`
- Modify: `applications/cool-plugin-design-assistant/tests/test_marketplace_release.py`

**Interfaces:**
- Consumes: `load_contract(Path) -> DistributionContract` and `load_preparation_catalog(Path, Path) -> PreparationCatalog`.
- Produces: regression expectations for build-capable Cool schema v3, explicit publication settings, complete classifications, and `build` catalog mode.

- [ ] **Step 1: Write failing behavioral tests**

Assert that the real Cool contract is schema v3, validates/builds with separate text and binary rules, keeps GitHub enabled and ClawHub disabled, and that every product observes Cool in `build` mode.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -B -m unittest applications.cool-bible-tutor.tests.test_distribution.DistributionAuditTests.test_approved_openclaw_distribution_identity applications.vibe-coding-designer.tests.test_marketplace_release.MarketplaceReleaseTests.test_obvious_one_catalog_preserves_vibe_and_legacy_modes applications.cool-plugin-design-assistant.tests.test_marketplace_release.MarketplaceReleaseTests.test_obvious_one_catalog_registers_this_application_and_preserves_existing_modes -v`

Expected: FAIL because Cool is schema v1 and `verify_existing`.

- [ ] **Step 3: Commit the failing tests**

Commit: `test: require buildable Cool schema v3 contract`

### Task 2: Migrate the application-owned contract and catalog

**Files:**
- Modify: `applications/cool-bible-tutor/openclaw/distribution.json`
- Modify: `marketplaces/obvious-one.json`
- Modify: `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`

**Interfaces:**
- Consumes: Task 1 expectations and the schema-v3 `content_rules` / `publication` contract.
- Produces: one buildable Cool contract with exhaustive text/binary classification and a catalog `build` entry.

- [ ] **Step 1: Add minimal schema-v3 fields**

Keep the legacy selectors and RAG block unchanged. Add non-overlapping product-text, asset-text, and binary rules. Cite `LICENSE` for application text and `THIRD_PARTY_CONTENT.md` for bundled data/dependency assets. Enable GitHub marketplace and disable ClawHub.

- [ ] **Step 2: Change only Cool's catalog mode to `build` and update operational documentation**

Remove the statement that Cool remains a legacy entry; document it as a schema-v3 build entry while retaining generic `verify_existing` support.

- [ ] **Step 3: Run focused tests and the five formerly failing OpenClaw tests**

Run: `python -B -m unittest applications.cool-bible-tutor.tests.test_distribution applications.cool-bible-tutor.tests.test_openclaw_release applications.vibe-coding-designer.tests.test_marketplace_release applications.cool-plugin-design-assistant.tests.test_marketplace_release -v`

Expected: PASS.

- [ ] **Step 4: Validate, build twice, verify, and compare deterministic manifests**

Run the framework `validate-contract`, two isolated `build-package` operations, and `verify`; compare their generated content manifests and packaged file hashes.

Expected: every command returns `PASS`, and both builds are byte-equivalent.

- [ ] **Step 5: Commit the migration**

Commit: `fix: migrate Cool Bible Tutor distribution to schema v3`

### Task 3: Verify and integrate the green repository

**Files:**
- No production files expected beyond Tasks 1-2.

**Interfaces:**
- Consumes: the complete migration branch.
- Produces: full local verification evidence suitable for merging into local `main` and the already authorized push.

- [ ] **Step 1: Run framework, repository, and all product suites**

Run the generic framework suite, top-level repository suite, Cool Bible Tutor suite, Vibe Coding Designer suite, and Cool Plugin Design Assistant suite.

Expected: PASS, with only documented platform/release-only skips.

- [ ] **Step 2: Run the selected application verifier for Cool Bible Tutor**

Run: `python -B .\scripts\verify_extraction.py --application cool-bible-tutor`

Expected: local gates PASS; marketplace evidence may remain `NOT VERIFIED` when no marketplace checkout is supplied.

- [ ] **Step 3: Run `git diff --check` and confirm no unrelated tracked changes**

Expected: no whitespace errors and no changes outside the plan's declared files.

- [ ] **Step 4: Review the whole branch, merge into local `main`, rerun the full gates, and push**

Push only after the merged `main` retains the same green evidence.
