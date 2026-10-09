# Growing with Children 1.0.2 Reference Handoff and Publication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deterministically derive, validate, install-test, stage, and publish Growing with Children 1.0.2 with explicit cross-skill RM-04A/RM-04B handoffs while preserving the 1.0.1 archive as immutable evidence.

**Architecture:** Add a product-neutral delegated-reference validator and deterministic repair contract to the existing Plugin ZIP onboarding boundary. A small product-owned contract supplies the exact source identity, reference owner, non-owner skills, and target version; the framework produces a repaired ZIP plus Workbench-owned metadata without fabricating Plugin Builder v2/v3 evidence. The existing separate-tree marketplace preparation and verification pipeline then stages the Codex-only Obvious One release.

**Tech Stack:** Python 3.11+, standard-library `zipfile`, `json`, `hashlib`, `tempfile`, `pathlib`, `unittest`, existing `obvious_one_plugin_framework` CLI and marketplace verifier, Git and Codex marketplace CLI.

**Spec:** `docs/superpowers/specs/2026-10-09-growing-with-children-1.0.2-reference-handoff-and-publication-design.md`

## Global Constraints

- Preserve source ZIP SHA-256 `e20ab7f970565dde1d2bfa8529d82da12366dfbed6a6672aed9dc51eedb6d1f1`; never overwrite the source.
- Target plugin ID is `growing-with-children`; source version is 1.0.1 and repaired version is 1.0.2.
- Preserve the five-skill architecture and approved application behavior.
- RM-04A and RM-04B remain packaged only below `skills/guiding-biblical-study`.
- Four non-owner skills use per-reference `HANDOFF` records with `local_copy: false`.
- Never relabel Workbench-derived evidence as Plugin Builder v2/v3 producer evidence.
- Preserve strict hashes, confined paths, deterministic output, fail-closed validation, and exact publication authority.
- Use genuine system temporary storage for archive, filesystem, Git, and packaging fixtures; do not redirect `TEMP` or `TMP` into the repository.
- Force UTF-8 for Python subprocesses and classify failures as implementation, fixture, environment, or transient before changing product code.
- Publish only to the Obvious One Codex marketplace. OpenClaw, ClawHub, and the OpenAI universal directory remain out of scope and `NOT VERIFIED` or `NOT APPLICABLE` as appropriate.
- Do not claim runtime verification from static validation, installation, or discovery alone.

## Review Focus

- A handoff points to a missing skill or an owner that does not package/index the reference: reject with a stable delegated-reference diagnostic in Task 1.
- A malicious or malformed legacy archive uses traversal, duplicate, link, case-collision, unsupported compression, or digest-conflicting members: reject before extraction in Task 3.
- A repair contract targets the wrong source digest, plugin ID, source version, owner, or reference bytes: fail without leaving a candidate in Task 2.
- A repair leaves a stale direct PDF link/index record or duplicates a PDF outside the owner skill: fail candidate validation in Tasks 1 and 4.
- A marketplace baseline already contains the plugin or changes between staging and publication: require explicit update design or rebuild/reverify the exact delta in Tasks 6 and 7.

---

### Task 1: Validate delegated professional-reference handoffs

**Files:**
- Create: `src/obvious_one_plugin_framework/plugin_authoring/delegated_references.py`
- Modify: `src/obvious_one_plugin_framework/plugin_authoring/validation.py`
- Modify: `src/obvious_one_plugin_framework/plugin_authoring/__init__.py`
- Create: `tests/framework/test_delegated_reference_validation.py`

**Interfaces:**
- Consumes: a plugin root containing sibling `skills/*`, `SKILL.md`, `assets/reference-profile.json`, and `assets/knowledge-index.json` files.
- Produces: `validate_delegated_references(root: Path) -> tuple[ValidationIssue, ...]`, integrated into `validate_plugin_tree(root)`.

- [ ] **Step 1: Write failing valid-contract tests**

Create fixtures with owner `guiding-biblical-study`, RM-04A/RM-04B owner files and index records, and one non-owner `skill-reference-profile-v2`. Assert zero findings when `delegated_references` contains exact per-reference records and the non-owner `SKILL.md` names the trigger, owner, return behavior, and unavailable-owner fallback.

- [ ] **Step 2: Write failing malformed-contract tests**

Add table-driven tests for unknown profile keys, duplicate reference IDs, missing owner skill, unsupported access mode, `local_copy: true`, non-owner local index entries, non-owner direct links, missing owner assets/index records/direct links, missing handoff prose, and duplicate owner PDFs. Assert stable `delegated_reference_*` issue codes and confined relative paths.

- [ ] **Step 3: Run the focused tests and confirm RED**

Run: `python -B -m unittest tests.framework.test_delegated_reference_validation -v`  
Expected: FAIL because `validate_delegated_references` does not exist.

- [ ] **Step 4: Implement the strict v2 profile validator**

Implement `validate_delegated_references(root: Path) -> tuple[ValidationIssue, ...]`. Accept `skill-reference-profile-v1` unchanged; for v2 require the existing profile fields plus `delegated_references`, with each record containing exactly `reference_id`, `owner_skill`, `access_mode`, and `local_copy`. Resolve owner assets through its local index and direct Markdown links; never follow paths outside the owner skill.

- [ ] **Step 5: Integrate and verify GREEN**

Append delegated-reference findings in `validate_plugin_tree`. Export the validator through `plugin_authoring.__init__`. Run the focused test and `tests.framework.test_plugin_authoring_validation`; expect PASS.

- [ ] **Step 6: Commit Task 1**

```powershell
git add src/obvious_one_plugin_framework/plugin_authoring tests/framework/test_delegated_reference_validation.py
git commit -m "feat: validate delegated skill references"
```

### Task 2: Add a deterministic, evidence-bound repair contract

**Files:**
- Create: `src/obvious_one_plugin_framework/plugin_onboarding/repair_contract.py`
- Create: `src/obvious_one_plugin_framework/plugin_onboarding/repair.py`
- Modify: `src/obvious_one_plugin_framework/plugin_onboarding/__init__.py`
- Create: `tests/framework/test_plugin_onboarding_repair_contract.py`
- Create: `tests/framework/test_plugin_onboarding_repair.py`
- Modify: `tests/framework/plugin_onboarding_fixtures.py`

**Interfaces:**
- Consumes: `load_repair_contract(path: Path) -> DelegatedReferenceRepair` and an exact safe source archive.
- Produces: `repair_delegated_reference_archive(archive: Path, contract: DelegatedReferenceRepair, output_archive: Path, output_metadata: Path) -> RepairResult`.

- [ ] **Step 1: Write failing strict-contract tests**

Define schema `plugin-delegated-reference-repair-v1` with exact keys: `schema`, `plugin_id`, `source_version`, `target_version`, `source_archive_sha256`, `owner_skill`, `non_owner_skills`, `references`, `source_manifest_path`, and `approval_record`. Each reference contains exact `reference_id`, `owner_relative_path`, and `sha256`. Test unknown/missing keys, unsafe paths, invalid IDs/versions/digests, duplicate skills/references, owner in non-owner list, and absent approval.

- [ ] **Step 2: Write failing deterministic transformation tests**

Build a compact legacy Plugin Builder v1 fixture. Assert that the repair:

- verifies the archive before extraction;
- preserves unmodified member bytes;
- removes the two non-owner PDF index records and Markdown links;
- writes v2 profiles with two handoff records;
- appends one canonical handoff section to each non-owner `SKILL.md`;
- retains owner PDFs byte-for-byte and nowhere else;
- updates both plugin manifests to 1.0.2;
- moves the original producer manifest to `docs/provenance/source-PLUGIN-BUILDER-MANIFEST.json` instead of presenting stale W1/W2 claims as current;
- creates `WORKBENCH-REPAIR-MANIFEST.json` and external `package-metadata.json` with Workbench ownership and all runtime states `NOT VERIFIED`;
- cleans partial output after any failure; and
- produces byte-identical ZIP and metadata outputs from two clean system-temp roots.

- [ ] **Step 3: Run focused tests and confirm RED**

Run: `python -B -m unittest tests.framework.test_plugin_onboarding_repair_contract tests.framework.test_plugin_onboarding_repair -v`  
Expected: FAIL because the repair interfaces do not exist.

- [ ] **Step 4: Implement the strict repair contract**

Add frozen dataclasses `RepairReference`, `DelegatedReferenceRepair`, and `RepairResult`. Parse exact JSON, freeze collections, and use stable `OnboardingError` codes prefixed `onboarding.repair_contract`.

- [ ] **Step 5: Implement the archive transformer**

Reuse `plugin_authoring.inspect_archive` and safe extraction. Perform changes only in a genuine `TemporaryDirectory`; normalize generated text to UTF-8 LF; preserve untouched bytes; write ZIP entries in ordinal path order with fixed timestamps, permissions, and compression; publish outputs atomically only after `validate_plugin_tree` reports no findings and both manifests agree.

- [ ] **Step 6: Verify GREEN and commit Task 2**

Run the two focused suites and `tests.framework.test_plugin_onboarding_inspection`; expect PASS.

```powershell
git add src/obvious_one_plugin_framework/plugin_onboarding tests/framework
git commit -m "feat: add deterministic delegated-reference repair"
```

### Task 3: Recognize legacy v1 and Workbench-repaired onboarding evidence

**Files:**
- Modify: `src/obvious_one_plugin_framework/plugin_onboarding/contract.py`
- Modify: `src/obvious_one_plugin_framework/plugin_onboarding/inspection.py`
- Modify: `src/obvious_one_plugin_framework/plugin_onboarding/proposal.py`
- Modify: `src/obvious_one_plugin_framework/plugin_onboarding/materialize.py`
- Modify: `src/obvious_one_plugin_framework/cli.py`
- Modify: `tests/framework/test_plugin_onboarding_contract.py`
- Modify: `tests/framework/test_plugin_onboarding_inspection.py`
- Modify: `tests/framework/test_plugin_onboarding_proposal.py`
- Modify: `tests/framework/test_plugin_onboarding_materialize.py`
- Modify: `tests/framework/test_plugin_onboarding_cli.py`

**Interfaces:**
- Consumes: existing Plugin Builder v2/v3 metadata unchanged, or schema `workbench-repaired-plugin-v1` emitted by Task 2; inspection-only mode consumes a legacy flat ZIP with `PLUGIN-BUILDER-MANIFEST.json` schema `plugin-builder-candidate-manifest-v1`.
- Produces: `load_onboarding_metadata(path: Path) -> PackageMetadata | WorkbenchRepairMetadata`, `inspect_legacy_plugin_archive(archive: Path) -> OnboardingInspection`, and updated `prepare-plugin-zip-marketplace` compatibility.

- [ ] **Step 1: Write failing evidence-separation tests**

Assert that legacy inspection reports `input_profile=PLUGIN_BUILDER_CANDIDATE_V1`, hashes the exact archive and members itself, records producer W1/W2 values only under `producer_claims`, and marks producer verification and all installed-runtime layers `NOT VERIFIED`. Assert that repaired metadata uses `input_profile=WORKBENCH_REPAIRED_PLUGIN_V1` and never sets v2/v3 candidate, verification, or runtime evidence fields.

- [ ] **Step 2: Write failing archive-abuse and ambiguity tests**

Cover traversal, absolute paths, links, duplicate names, case collisions, unsupported compression, member-count/size/ratio limits, malformed legacy manifests, mixed producer authorities, and mismatched repaired metadata. All must fail before materialization with stable codes.

- [ ] **Step 3: Run focused tests and confirm RED**

Run the five onboarding suites listed above; expect failures for unsupported schemas and missing legacy inspection.

- [ ] **Step 4: Implement metadata union and inspection-only command**

Keep `load_package_metadata` as the strict v2/v3 compatibility API. Add `load_onboarding_metadata`. Add CLI command `inspect-plugin-zip --archive <zip> --output <json> --json` for legacy/Workbench profiles; it performs no repair, application creation, or marketplace mutation.

- [ ] **Step 5: Extend proposal/materialization for repaired metadata only**

Allow `prepare-plugin-zip-marketplace` to materialize a repaired archive only when Workbench metadata, plugin identity, publication decisions, and current extracted validation all match. Legacy v1 inspection alone remains non-publishable and returns `BLOCKED` until an approved repair creates a valid derivative.

- [ ] **Step 6: Verify existing v2/v3 behavior remains unchanged**

Run all `test_plugin_onboarding_*` suites. Assert existing deterministic outputs, collision protection, evidence handling, and marketplace compatibility tests still pass unchanged.

- [ ] **Step 7: Commit Task 3**

```powershell
git add src/obvious_one_plugin_framework tests/framework
git commit -m "feat: onboard verified legacy plugin repairs"
```

### Task 4: Add the Growing with Children product repair configuration

**Files:**
- Create: `applications/growing-with-children/conversion.json`
- Create: `applications/growing-with-children/repair/delegated-reference-repair-v1.json`
- Create: `applications/growing-with-children/scripts/build_repaired_release.py`
- Create: `applications/growing-with-children/tests/test_repair_contract.py`
- Create: `applications/growing-with-children/tests/test_release_builder.py`
- Create: `applications/growing-with-children/tests/coverage-matrix.md`
- Create: `applications/growing-with-children/docs/source-decisions.md`

**Interfaces:**
- Consumes: the immutable externally supplied 1.0.1 ZIP path and Task 2 repair API.
- Produces: `build_repaired_release(source: Path, output_root: Path) -> RepairResult`; no machine-specific source path is committed.

- [ ] **Step 1: Write the product contract test**

Assert exact product ID, source/target versions, source SHA-256, five named skills, four non-owner skills, two RM references, owner-relative paths, expected reference digests, Codex-only publication scope, and owner-approved behavior-preservation decision.

- [ ] **Step 2: Write the product release-builder test**

Use the compact fixture through the product launcher. Assert the launcher delegates to the generic repair API, refuses a wrong source digest, writes only below the supplied output root, and emits an ASCII-safe machine result.

- [ ] **Step 3: Run product tests and confirm RED**

Run: `python -B -m unittest discover -s .\applications\growing-with-children\tests -v`  
Expected: FAIL because the product launcher and contract do not exist.

- [ ] **Step 4: Implement the minimum product-owned files**

Keep domain decisions in the repair JSON and `source-decisions.md`; keep transformation logic in the generic framework. The launcher accepts `--source`, `--output`, and `--json`, imports only public framework APIs, and does not infer source locations.

- [ ] **Step 5: Verify GREEN and commit Task 4**

Run product tests and `git diff --check`; expect PASS.

```powershell
git add applications/growing-with-children
git commit -m "feat: define growing with children repair release"
```

### Task 5: Document and verify the operational workflow

**Files:**
- Modify: `docs/PLUGIN_SKILLS_TECHNICAL_REFERENCE.md`
- Modify: `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`
- Modify: `docs/GPT_TO_PLUGIN_USER_GUIDE.md`
- Modify: `README.md`
- Modify: `tests/test_agent_contract.py`
- Modify: `tests/test_repo_contract.py`

**Interfaces:**
- Consumes: Tasks 1-4 public APIs and CLI commands.
- Produces: owner-facing legacy inspection, repair, evidence-state, staging, runtime-test, and publication instructions.

- [ ] **Step 1: Write failing documentation-contract assertions**

Require the technical reference to define delegated-reference ownership and response ownership; require the command reference to show legacy inspection and repair without calling legacy claims v2/v3 evidence; require the user guide to separate repair approval, local readiness, runtime evidence, and publication authority.

- [ ] **Step 2: Run contract tests and confirm RED**

Run: `python -B -m unittest tests.test_agent_contract tests.test_repo_contract -v`  
Expected: FAIL on missing delegated-reference and repair workflow text.

- [ ] **Step 3: Update the routed documentation**

Document exact commands, schemas, state language, failure behavior, system-temp discipline, and the distinction between the immutable source ZIP and derived 1.0.2 ZIP. Do not add OpenClaw claims.

- [ ] **Step 4: Verify GREEN and commit Task 5**

Run the two contract suites and `git diff --check`; expect PASS.

```powershell
git add README.md docs tests/test_agent_contract.py tests/test_repo_contract.py
git commit -m "docs: explain delegated reference repair onboarding"
```

### Task 6: Build and fully verify the exact 1.0.2 candidate

**Files:**
- Generate only below ignored `dist/growing-with-children-1.0.2/` and genuine system temp roots.
- Do not commit the user-supplied source ZIP or generated release artifacts.

**Interfaces:**
- Consumes: the exact source ZIP, product repair contract, completed framework, and an owner publication-decision record with no invented identity or attestations.
- Produces: repaired ZIP, Workbench metadata, inspection report, application staging tree, deterministic evidence report, and exact digests.

- [ ] **Step 1: Establish the Windows test environment**

Record Python version, system temp path, UTF-8 settings, long-path/hard-link/archive capability probes, repository root/branch/status, and source digest once. Keep probe output below ignored `dist/growing-with-children-1.0.2/evidence`.

- [ ] **Step 2: Run the complete repository verification before product build**

Run with `PYTHONUTF8=1`:

```powershell
python -B -m unittest discover -s .\tests\framework -v
python -B -m unittest discover -s .\applications\plugin-builder\tests -v
python -B -m unittest discover -s .\applications\cool-plugin-design-assistant\tests -v
python -B -m unittest discover -s .\applications\growing-with-children\tests -v
python -B -m unittest tests.test_agent_contract tests.test_repo_contract tests.test_windows_test_environment -v
git diff --check
```

Expected: all applicable tests PASS; documented platform skips only.

- [ ] **Step 3: Build twice from clean roots**

Invoke `build_repaired_release.py` twice against the exact 1.0.1 ZIP. Assert identical repaired ZIP and metadata SHA-256 values, and recheck that the source digest is unchanged.

- [ ] **Step 4: Inspect the exact ZIP contents**

Assert five skills; version 1.0.2 in both plugin manifests; two and only two Bible PDFs under the owner; eight non-owner handoff records; no stale non-owner RM-04A/B local paths/index entries; valid JSON; no secrets/private paths; and complete notices/provenance.

- [ ] **Step 5: Materialize the onboarding proposal**

Run `prepare-plugin-zip-marketplace` with the repaired ZIP, Workbench metadata, exact publication decisions, repository root, and a fresh output. Require `PASS` and inspect the generated application, catalog, proposal, distribution contract, and result.

- [ ] **Step 6: Commit only tracked implementation/evidence summaries**

Do not commit generated ZIPs. Commit a redacted, machine-independent verification summary under `applications/growing-with-children/docs/` only if all preceding checks pass.

### Task 7: Stage and locally validate the Obvious One marketplace delta

**Files:**
- Generate: ignored `dist/marketplace-delta/growing-with-children-1.0.2/`
- Mutate later, after verification: separate marketplace repository paths scoped to `plugins/growing-with-children` and required catalog/index files.

**Interfaces:**
- Consumes: Task 6 generated application/catalog, clean `D:\GitHub\obvious-one-plugins` baseline, and the exact repaired ZIP identity.
- Produces: separate staged marketplace tree, verifier evidence, local install evidence, and exact Git delta.

- [ ] **Step 1: Verify the marketplace baseline**

Confirm root, remote, branch, clean status, authentication, absence of the target plugin, and current baseline commit. If the target exists, stop with `BLOCKED` and prepare an update design instead of overwriting it.

- [ ] **Step 2: Prepare without mutating the baseline**

Run `prepare-marketplace` using the generated catalog and application source into the ignored staging root. Require a complete generated verifier and a delta limited to the target plugin plus required index/catalog entries.

- [ ] **Step 3: Verify staged filesystem and Git evidence**

Run `verify-marketplace` for staged filesystem, external Git stage/index, exact commit, and fresh checkout. Require every applicable state to be `PASS`.

- [ ] **Step 4: Install from the staged local marketplace**

Add or refresh the staged marketplace with the Codex marketplace CLI in a disposable configuration where supported. Verify discovery as `STATICALLY VERIFIED`; do not call it behavioral evidence.

- [ ] **Step 5: Execute installed-runtime handoff scenarios**

Exercise exact-CUV and formal-study handoffs from each of the four non-owner skills, plus the unavailable-owner fallback. Record installation, skill invocation, owner routing, reference use, result return, and conversation behavior separately. Any unobserved layer remains `NOT VERIFIED` and blocks publication under this specification.

- [ ] **Step 6: Reverify the exact staged delta after runtime testing**

Ensure runtime testing changed no staged files. Re-run exact digest and fresh-checkout verification and report the release ZIP SHA-256, staged commit SHA, and remaining gates.

### Task 8: Publish only the verified Obvious One delta

**Files:**
- Modify in the separate marketplace checkout only: the exact Task 7 verified paths.

**Interfaces:**
- Consumes: all-PASS Task 7 evidence and the owner's already granted publication instruction for this corrected 1.0.2 target.
- Produces: a scoped marketplace commit/branch, pull request or authorized direct integration, remote-main verification, and post-publication installation evidence.

- [ ] **Step 1: Reconfirm exact mutation scope**

Report source ZIP digest, repaired ZIP digest, staged baseline commit, staged delta, license/notices, runtime evidence, and destination. Stop if any digest or baseline changed.

- [ ] **Step 2: Apply the verified delta to a publication branch**

Copy only the verified generated delta into the clean marketplace checkout using one PowerShell process and literal resolved paths. Confirm no unrelated changes.

- [ ] **Step 3: Run marketplace tests and commit**

Run the marketplace's own validation and generated verifier. Commit the exact passing delta with a release-specific message.

- [ ] **Step 4: Push and integrate through the repository's authorized workflow**

Push the scoped branch, create/attach a pull request when required, verify checks, and merge only the exact reviewed commit. Do not create tags, GitHub Releases, ClawHub publications, or OpenAI-directory submissions.

- [ ] **Step 5: Verify remote main and fresh GitHub installation**

Fetch remote main, verify it contains the exact commit and plugin bytes, install/upgrade from `schao523/obvious-one-plugins --ref main`, and repeat representative installed-runtime behavior in a fresh task.

- [ ] **Step 6: Produce the completion report**

Report source preservation, repaired ZIP and manifest identities, requirement/invariant coverage, structural and deterministic results, installed Codex results, exact marketplace commit/PR, publication state, and OpenClaw/universal-directory `NOT VERIFIED` state. Never report `READY` for untested runtimes.

## Self-Review Record

- **Spec coverage:** Sections 1-10 map to Tasks 1-8; source preservation, handoff semantics, repair provenance, legacy evidence separation, verification, and publication boundaries all have an owning task.
- **Step scan:** Each step creates one test, implementation unit, verification result, or commit; product decisions remain declarative rather than hardcoded in generic framework code.
- **Type consistency:** `DelegatedReferenceRepair` and `RepairResult` originate in Task 2; the product launcher and onboarding metadata use those exact interfaces in Tasks 4 and 6.
- **Review focus:** All five high-risk conditions have explicit tests or gates in Tasks 1-3, 6, and 7.
- **Proportion:** The plan specifies public signatures, exact evidence states, commands, and fail-closed decisions without transcribing function bodies.
