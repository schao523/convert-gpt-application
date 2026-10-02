# Plugin Builder 0.1.3 Handoff Interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved `WORKBENCH_HANDOFF_V1_1` contract so Cool Plugin Design Assistant emits canonical create/update packages and Plugin Builder 0.1.3 consumes them, while retaining narrow fail-closed compatibility for observed legacy full and delta envelopes.

**Architecture:** Add a reusable `obvious_one_plugin_framework.workbench_handoff` package for contract validation, profile detection, normalization, deterministic serialization, and baseline identity. Cool Plugin Design Assistant becomes the canonical producer; Plugin Builder wraps the shared implementation at its existing CLI/session boundary and preserves W1/W2. Work occurs on one integration branch created from the current main checkout and merged with the existing Plugin Builder foundation branch so both products and the framework are tested together.

**Tech Stack:** Python 3.11+, standard-library `json`, `hashlib`, `pathlib`, `tempfile`, and `zipfile`; repository `plugin_authoring` archive primitives; `unittest`; Markdown skill/reference contracts; deterministic ZIP builders.

**Spec:** `docs/superpowers/specs/2026-10-03-plugin-builder-0.1.3-handoff-interface-design.md`

## Global Constraints

- Runtime scope remains exactly `OPENAI_ONLY_PHASE_ONE`.
- Target runtimes remain Codex and ChatGPT Work Local/Desktop; OpenClaw and Claude remain `NOT APPLICABLE` for Plugin Builder phase one.
- Plugin Builder formal version is `0.1.3`; do not publish or mutate any marketplace.
- Cool Plugin Design Assistant receives the source compatibility change without a release-version or publication change; its next public version remains a separate owner decision.
- New Design Assistant output uses `WORKBENCH_HANDOFF_V1_1`; create and update share one canonical envelope.
- Canonical v1.1 requirement records use exact `id`, `source`, and `verbatim`; update records also use exact `change` in `add|modify|remove|preserve`.
- Normalization is format-only: never infer approval, requirement text, baseline identity, rights, owner decisions, or runtime scope.
- W1 still blocks mutation and W2 still blocks packaging.
- Preserve existing source archive bytes and all unrelated user changes. Do not touch the untracked Vibe Coding Designer files.
- Use `python -B` for test and validation commands so verification cannot create `__pycache__` artifacts.
- No dependency installation, network access, Git push, tag, release, directory upload, submission, or publication.

## Review Focus

- A ZIP containing both canonical and legacy authorities must return `AMBIGUOUS` and produce no normalized output; Task 3 owns the test.
- UTF-8 requirement text with CRLF/LF differences must not be newline-translated into a false match; Task 2 owns the test.
- A wrapped or flat baseline plugin must resolve the same plugin identity while the archive SHA-256 remains the supplied-byte identity; Task 5 owns the test.
- An update that marks one requirement both `remove` and `preserve`, or removes without a bound requirement, must fail before W1; Task 2 owns the test.
- A blocked normalization with an existing destination must preserve that destination byte-for-byte and leave no temporary files; Task 3 owns the test.

---

### Task 1: Establish the integration branch without disturbing current work

**Files:**
- Verify only: `applications/cool-plugin-design-assistant/**`
- Verify only: `applications/vibe-coding-designer/**`
- Merge source: branch `codex/plugin-builder-foundation`

**Interfaces:**
- Consumes: approved spec commits `fb4711c` and `69ca9b7`, current dirty Design Assistant normalization work, and branch `codex/plugin-builder-foundation`.
- Produces: branch `codex/plugin-builder-0.1.3-interface` containing the approved spec and Plugin Builder foundation, with the pre-existing Design Assistant changes still unstaged and the Vibe Coding Designer files untouched.

- [ ] **Step 1: Record the pre-existing working-tree boundary**

Run:

```powershell
git status --short
git diff -- applications/cool-plugin-design-assistant
git status --short -- applications/vibe-coding-designer
```

Expected: exactly the four known modified Design Assistant files and two untracked Vibe Coding Designer files; save the console evidence in the task log, not the repository.

- [ ] **Step 2: Create the integration branch from current main**

Run:

```powershell
git switch -c codex/plugin-builder-0.1.3-interface
```

Expected: branch creation succeeds and preserves the working tree.

- [ ] **Step 3: Merge the existing Plugin Builder foundation**

Run:

```powershell
git merge --no-ff codex/plugin-builder-foundation -m "merge: integrate Plugin Builder foundation"
```

Expected: merge succeeds without modifying Design Assistant or Vibe Coding Designer paths.

- [ ] **Step 4: Verify the boundary after the merge**

Run the Step 1 commands again and compare their output. Expected: the same dirty Design Assistant delta and untouched Vibe files, plus a clean merged Plugin Builder tree.

### Task 2: Add the shared v1.1 semantic contract and baseline validator

**Files:**
- Create: `src/obvious_one_plugin_framework/workbench_handoff/__init__.py`
- Create: `src/obvious_one_plugin_framework/workbench_handoff/contract.py`
- Create: `src/obvious_one_plugin_framework/workbench_handoff/identity.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`
- Create: `tests/framework/test_workbench_handoff_contract.py`

**Interfaces:**
- Consumes: `plugin_authoring.ArchiveInventory`, `inventory_archive`, and `locate_plugin_archive_root`.
- Produces: `HANDOFF_CONTRACT`, `HANDOFF_SCHEMA`, `HandoffValidation`, `BaselineIdentity`, `canonical_json_bytes(value)`, `validate_canonical_handoff(manifest, handoff, inventory, input_root, *, expected_operation=None)`, `baseline_identity_from_archive(path)`, and `validate_update_baseline(handoff, baseline)`.

- [ ] **Step 1: Write failing contract tests**

Add tests named:

```python
def test_v11_create_requires_matching_contract_operation_and_exact_requirements(): ...
def test_v11_requirement_keeps_arbitrary_id_and_matches_utf8_bytes_without_newline_translation(): ...
def test_v11_rejects_duplicate_missing_mismatched_and_unindexed_requirements(): ...
def test_v11_update_requires_change_baseline_and_preservation_contract(): ...
def test_v11_rejects_remove_preserve_conflict_and_unbound_removal(): ...
def test_baseline_identity_supports_flat_and_wrapped_plugins_but_hashes_supplied_archive(): ...
```

Assert the exact diagnostics from the specification, including `handoff.contract_mismatch`, `handoff.operation_mismatch`, `requirements.explicit_records_required`, `requirements.text_mismatch:<id>`, `requirements.artifact_binding_missing:<id>`, and the three baseline diagnostics.

- [ ] **Step 2: Run the focused tests and confirm RED**

Run:

```powershell
python -B -m unittest tests.framework.test_workbench_handoff_contract -v
```

Expected: import failure for the missing `workbench_handoff` package.

- [ ] **Step 3: Implement focused contract modules**

Create these signatures:

```python
HANDOFF_CONTRACT = "WORKBENCH_HANDOFF_V1_1"
HANDOFF_SCHEMA = "workbench-handoff-v1.1"

@dataclass(frozen=True)
class HandoffValidation:
    status: str
    diagnostics: tuple[str, ...]

@dataclass(frozen=True)
class BaselineIdentity:
    plugin_id: str
    version: str
    archive_sha256: str
    envelope_profile: str

def canonical_json_bytes(value: object) -> bytes: ...
def validate_canonical_handoff(
    manifest: dict[str, Any],
    handoff: dict[str, Any],
    inventory: ArchiveInventory,
    input_root: Path,
    *,
    expected_operation: str | None = None,
) -> HandoffValidation: ...
def baseline_identity_from_archive(path: Path) -> BaselineIdentity: ...
def validate_update_baseline(
    handoff: dict[str, Any], baseline: BaselineIdentity | None
) -> tuple[str, ...]: ...
```

Keep semantic validation in `contract.py` and plugin archive identity in `identity.py`. Read requirement sources with `input_root.joinpath(path).read_bytes().decode("utf-8")`, not text-mode file reads, after confirming the path is safe, declared, and confined to `input_root`.

- [ ] **Step 4: Run focused and adjacent framework tests**

Run:

```powershell
python -B -m unittest tests.framework.test_workbench_handoff_contract tests.framework.test_plugin_authoring_archive tests.framework.test_plugin_authoring_manifests -v
```

Expected: PASS.

- [ ] **Step 5: Commit the shared contract**

```powershell
git add src/obvious_one_plugin_framework/workbench_handoff src/obvious_one_plugin_framework/__init__.py tests/framework/test_workbench_handoff_contract.py
git commit -m "feat: define canonical Workbench handoff v1.1"
```

### Task 3: Add shared profile detection and deterministic normalization

**Files:**
- Create: `src/obvious_one_plugin_framework/workbench_handoff/profiles.py`
- Create: `src/obvious_one_plugin_framework/workbench_handoff/normalization.py`
- Modify: `src/obvious_one_plugin_framework/workbench_handoff/__init__.py`
- Create: `tests/framework/test_workbench_handoff_normalization.py`

**Interfaces:**
- Consumes: Task 2 contract functions and `plugin_authoring` archive/deterministic ZIP APIs.
- Produces: `HandoffProfile`, `HandoffNormalizationOutcome`, `classify_handoff_profile(root)`, and `normalize_handoff_archive(source, destination_root, normalized_zip=None, *, runtime_scope="OPENAI_ONLY_PHASE_ONE")`.

- [ ] **Step 1: Write failing profile and normalization tests**

Add one test for every compatibility-matrix row, plus:

```python
def test_mixed_canonical_and_legacy_authorities_is_ambiguous_without_output(): ...
def test_unknown_envelope_is_blocked_without_selecting_authority(): ...
def test_full_design_legacy_requires_exact_requirement_records(): ...
def test_delta_legacy_requires_approved_baseline_and_preservation_contract(): ...
def test_blocked_normalization_preserves_existing_destination_and_cleans_temporary_files(): ...
def test_identical_input_produces_identical_tree_and_zip_hashes(): ...
```

Profiles must be exactly `WORKBENCH_HANDOFF_V1_1`, `CANONICAL_V1`, `LEGACY_WORKBENCH_V1`, `COOL_DESIGN_ASSISTANT_FULL_V1`, `COOL_DESIGN_ASSISTANT_DELTA_V1`, `AMBIGUOUS`, or `UNKNOWN`.

- [ ] **Step 2: Run focused tests and confirm RED**

```powershell
python -B -m unittest tests.framework.test_workbench_handoff_normalization -v
```

Expected: imports or profile assertions fail because the modules do not exist.

- [ ] **Step 3: Implement exact recognizers and adapters**

Create:

```python
@dataclass(frozen=True)
class HandoffProfile:
    profile: str
    diagnostics: tuple[str, ...] = ()

@dataclass(frozen=True)
class HandoffNormalizationOutcome:
    status: str
    profile: str
    diagnostics: tuple[str, ...]
    report: dict[str, Any]
    source_archive_sha256: str | None = None
    output_archive_sha256: str | None = None
    output_tree_sha256: str | None = None

def classify_handoff_profile(root: Path) -> HandoffProfile: ...
def normalize_handoff_archive(
    source: Path,
    destination_root: Path,
    normalized_zip: Path | None = None,
    *,
    runtime_scope: str = "OPENAI_ONLY_PHASE_ONE",
) -> HandoffNormalizationOutcome: ...
```

Detect all present authorities before choosing a profile. Adapt only copied or mechanically derived fields, validate the resulting v1.1 package before publishing it, and replace output transactionally only on `PASS`.

- [ ] **Step 4: Run all shared handoff tests**

```powershell
python -B -m unittest tests.framework.test_workbench_handoff_contract tests.framework.test_workbench_handoff_normalization -v
```

Expected: PASS with byte-identical repeat output.

- [ ] **Step 5: Commit profile compatibility**

```powershell
git add src/obvious_one_plugin_framework/workbench_handoff tests/framework/test_workbench_handoff_normalization.py
git commit -m "feat: normalize Workbench handoff compatibility profiles"
```

### Task 4: Make Cool Plugin Design Assistant the canonical producer

**Files:**
- Modify: `applications/cool-plugin-design-assistant/scripts/cool_plugin_design_assistant.py`
- Create: `applications/cool-plugin-design-assistant/scripts/workbench_handoff_bootstrap.py`
- Modify: `applications/cool-plugin-design-assistant/scripts/build_marketplace_release.py`
- Modify: `applications/cool-plugin-design-assistant/tests/test_tools.py`
- Modify: `applications/cool-plugin-design-assistant/tests/test_marketplace_release.py`
- Modify: `applications/cool-plugin-design-assistant/README.md`
- Modify: `applications/cool-plugin-design-assistant/skills/creating-application-plugin-design-specifications/references/workbench-handoff-contract.md`
- Modify: `applications/cool-plugin-design-assistant/tests/coverage-matrix.md`

**Interfaces:**
- Consumes: Task 3 `normalize_handoff_archive` and Task 2 validator through the bootstrap module, preferring vendored runtime then repository source.
- Produces: `normalize-handoff-package` output conforming to v1.1 for full and delta inputs and a distributable Design Assistant artifact containing the shared runtime.

- [ ] **Step 1: Extend producer tests before changing production code**

Update fixture construction to supply exact records. Add tests:

```python
def test_normalizes_full_package_to_v11_with_exact_requirement_records(): ...
def test_normalizes_delta_package_to_v11_update_with_baseline_contract(): ...
def test_rejects_legacy_package_without_exact_requirement_authority(): ...
def test_cli_emits_one_ascii_safe_result_and_no_partial_output_on_block(): ...
def test_release_vendors_workbench_handoff_and_plugin_authoring_runtime(): ...
def test_handoff_reference_requires_canonical_records_and_one_envelope(): ...
```

- [ ] **Step 2: Run producer tests and confirm RED**

```powershell
python -B -m unittest applications.cool-plugin-design-assistant.tests.test_tools applications.cool-plugin-design-assistant.tests.test_marketplace_release -v
```

Expected: new schema, delta, vendoring, and reference assertions fail.

- [ ] **Step 3: Replace product-local normalization with the shared API**

Implement `load_workbench_handoff() -> ModuleType` in the bootstrap. Keep Design Assistant-specific argument parsing and result-document formatting in the product script. Remove duplicated archive/schema logic only after the shared tests and product tests cover it.

- [ ] **Step 4: Vendor the shared runtime in release builds**

Update `build_marketplace_release.py` to copy:

- `obvious_one_plugin_framework/workbench_handoff/*.py`; and
- its `plugin_authoring/*.py` dependency

under `scripts/vendor/obvious_one_plugin_framework/`, excluding caches and links and preserving deterministic bytes.

- [ ] **Step 5: Update the handoff reference and coverage trace**

State that new full and delta output is v1.1, exact requirement records are mandatory, and legacy normalization blocks when semantic authority is missing. Do not add Skill architecture choices to the handoff.

- [ ] **Step 6: Run the complete Design Assistant suite**

```powershell
python -B -m unittest discover -s applications/cool-plugin-design-assistant/tests -v
```

Expected: PASS; no source ZIP or prior destination is modified.

- [ ] **Step 7: Commit the producer**

```powershell
git add applications/cool-plugin-design-assistant
git commit -m "feat: emit canonical Workbench handoff v1.1"
```

Do not add the unrelated Vibe Coding Designer files.

### Task 5: Make Plugin Builder 0.1.3 consume the shared interface

**Files:**
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/bootstrap.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/handoff_normalization.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/inspection.py`
- Modify: `applications/plugin-builder/scripts/plugin_builder_core/session_contract.py`
- Modify: `applications/plugin-builder/scripts/build_marketplace_release.py`
- Create: `applications/plugin-builder/tests/test_canonical_requirements.py`
- Modify: `applications/plugin-builder/tests/test_handoff_normalization.py`
- Modify: `applications/plugin-builder/tests/test_inspection.py`
- Modify: `applications/plugin-builder/tests/test_marketplace_release.py`
- Modify: `applications/plugin-builder/tests/test_standalone_artifact.py`

**Interfaces:**
- Consumes: shared normalization, canonical validation, and baseline identity from Tasks 2–3.
- Produces: existing Plugin Builder CLI/session outcomes with v1.1 profiles and full requirement evidence; no change to W1/W2 APIs.

- [ ] **Step 1: Add failing consumer and baseline tests**

Port the independently exercised 0.1.2 canonical-requirement cases into repository tests, then add:

```python
def test_inspect_accepts_v11_create_and_registers_exact_ids(): ...
def test_inspect_accepts_v11_update_only_when_supplied_baseline_matches(): ...
def test_inspect_rejects_flat_or_wrapped_baseline_with_wrong_declared_identity(): ...
def test_inspect_records_design_assistant_full_and_delta_profiles(): ...
def test_session_contract_accepts_only_the_seven_named_profiles(): ...
def test_standalone_release_vendors_shared_handoff_runtime(): ...
```

For flat and wrapped forms, assert identical plugin ID/version resolution but distinct archive hashes when wrapper bytes differ.

- [ ] **Step 2: Run consumer tests and confirm RED**

```powershell
python -B -m unittest applications.plugin-builder.tests.test_canonical_requirements applications.plugin-builder.tests.test_handoff_normalization applications.plugin-builder.tests.test_inspection applications.plugin-builder.tests.test_standalone_artifact -v
```

Expected: v1.1 profile, baseline, and vendored-runtime assertions fail.

- [ ] **Step 3: Load and wrap the shared runtime**

Extend `bootstrap.py` with `load_workbench_handoff() -> ModuleType`. Keep `handoff_normalization.py` as a compatibility import surface that re-exports the shared dataclasses and functions so callers and existing tests do not depend on private framework paths.

- [ ] **Step 4: Enforce canonical requirement and baseline closure during inspection**

Update `inspect_design_package(...)` to:

- validate the v1.1 semantic and physical authorities;
- use exact canonical records without ID parsing;
- build `BaselineIdentity` from the separately supplied baseline;
- run `validate_update_baseline` before advancing to S2; and
- retain the complete records and profile in `inspection.json` and `session.json`.

Existing canonical and legacy behavior remains available only under the compatibility-matrix rules.

- [ ] **Step 5: Vendor the complete shared runtime**

Update the release builder so the flat upload ZIP and installed artifact contain `workbench_handoff` plus `plugin_authoring`. Assert the source and extracted artifact use the same shared files and exclude caches.

- [ ] **Step 6: Run the complete Plugin Builder suite**

```powershell
python -B -m unittest discover -s applications/plugin-builder/tests -v
```

Expected: PASS, with only documented platform skips.

- [ ] **Step 7: Commit the consumer**

```powershell
git add applications/plugin-builder src/obvious_one_plugin_framework/workbench_handoff
git commit -m "feat: consume canonical Design Assistant handoffs"
```

### Task 6: Prove direct producer-to-consumer interoperability

**Files:**
- Create: `tests/test_workbench_handoff_interoperability.py`
- Create: `tests/fixtures/workbench-handoff/full/**`
- Create: `tests/fixtures/workbench-handoff/delta/**`
- Modify: `scripts/verify_extraction.py`

**Interfaces:**
- Consumes: Design Assistant CLI/source functions and Plugin Builder `inspect_design_package` from Tasks 4–5.
- Produces: repository-level proof that no manual sidecar repair is required for create or update.

- [ ] **Step 1: Add failing end-to-end interface tests**

Add:

```python
def test_design_assistant_full_output_enters_plugin_builder_s2_without_repair(): ...
def test_design_assistant_delta_output_enters_plugin_builder_s2_with_matching_baseline(): ...
def test_cross_product_output_preserves_ids_sources_text_and_source_bytes(): ...
def test_cross_product_repeated_normalization_is_byte_deterministic(): ...
```

Fixtures must include arbitrary IDs such as `D-01`, `DAC-01`, and `IM-09`, UTF-8 text, a matching baseline ZIP, and one unaffected baseline member.

- [ ] **Step 2: Run the integration test and confirm RED**

```powershell
python -B -m unittest tests.test_workbench_handoff_interoperability -v
```

Expected: fail until both product entry points are fully wired.

- [ ] **Step 3: Make only the minimal integration fixes**

Resolve interface wiring, import, or fixture issues without duplicating shared contract logic in either product.

- [ ] **Step 4: Add the cross-product gate to repository verification**

Update the top-level verifier to run the interoperability test when either `cool-plugin-design-assistant` or `plugin-builder` is selected. Keep product-specific verification results separate.

- [ ] **Step 5: Run the integration and selected application verifiers**

```powershell
python -B -m unittest tests.test_workbench_handoff_interoperability -v
python -B scripts/verify_extraction.py --application cool-plugin-design-assistant
python -B scripts/verify_extraction.py --application plugin-builder
```

Expected: all applicable local gates PASS; installed conversation behavior remains `NOT VERIFIED`.

- [ ] **Step 6: Commit interoperability evidence**

```powershell
git add tests/test_workbench_handoff_interoperability.py tests/fixtures/workbench-handoff scripts/verify_extraction.py
git commit -m "test: prove Design Assistant handoff interoperability"
```

### Task 7: Update skill contracts, compatibility evidence, and version 0.1.3

**Files:**
- Modify: `applications/plugin-builder/plugin.json`
- Modify: `applications/plugin-builder/.codex-plugin/plugin.json`
- Modify: `applications/plugin-builder/conversion.json`
- Modify: `applications/plugin-builder/openclaw/distribution.json`
- Modify: `applications/plugin-builder/docs/phase-one-scope.json`
- Modify: `applications/plugin-builder/README.md`
- Modify: `applications/plugin-builder/DISTRIBUTION.md`
- Modify: `applications/plugin-builder/docs/source-decisions.md`
- Modify: `applications/plugin-builder/docs/runtime-compatibility.md`
- Modify: `applications/plugin-builder/docs/application-invariants.md`
- Modify: `applications/plugin-builder/tests/coverage-matrix.md`
- Modify: `applications/plugin-builder/skills/guiding-plugin-builder-sessions/references/session-workflow.md`
- Modify: `applications/plugin-builder/skills/planning-plugin-implementations/references/input-and-plan-contract.md`
- Modify: applicable Plugin Builder contract tests

**Interfaces:**
- Consumes: verified behavior and exact results from Tasks 2–6.
- Produces: synchronized 0.1.3 metadata and honest evidence language for all three approved release targets, without claiming publication or installed behavior.

- [ ] **Step 1: Write failing metadata and skill-contract assertions**

Assert:

- both manifests and the distribution contract say `0.1.3`;
- `OPENAI_ONLY_PHASE_ONE` and runtime exclusions are unchanged;
- the session reference names canonical v1.1 and all compatibility profiles;
- canonical records, baseline validation, W1, and W2 are stated;
- private ZIP, GitHub Codex marketplace, and OpenAI universal directory are approved targets; and
- actual publication state remains `NOT_PERFORMED`.

- [ ] **Step 2: Run focused tests and confirm RED**

```powershell
python -B -m unittest applications.plugin-builder.tests.test_conversion_contract applications.plugin-builder.tests.test_distribution applications.plugin-builder.tests.test_skill_contracts -v
```

Expected: fail on version and new contract text.

- [ ] **Step 3: Update metadata and evidence from observed results only**

Change version fields to `0.1.3`. Set `conversion.json.marketplace_repository` to the repository's existing approved Codex marketplace identity, `schao523/obvious-one-plugins`, and enable only the GitHub marketplace field in the schema-v3 distribution contract. Keep ClawHub disabled, all upload/submission/publication states `NOT_PERFORMED`, OpenClaw `NOT APPLICABLE`, and universal-directory acceptance unclaimed.

- [ ] **Step 4: Run skill and metadata validation**

Run the product contract tests, installed Skill Creator validation for all four Plugin Builder skills, and plugin-tree validation on source. Expected: PASS.

- [ ] **Step 5: Commit release-candidate metadata**

```powershell
git add applications/plugin-builder
git commit -m "chore: prepare Plugin Builder 0.1.3 interface candidate"
```

### Task 8: Run full verification and build deterministic release candidates

**Files:**
- Generated only below ignored `dist/` and `.tmp/`
- Modify evidence documents only if actual final results differ from Task 7 expectations

**Interfaces:**
- Consumes: complete source from Tasks 1–7.
- Produces: verified local Plugin Builder 0.1.3 ZIP candidate, Design Assistant source/build evidence, deterministic hashes, and an exact list of remaining runtime/publication gates.

- [ ] **Step 1: Run framework and product suites**

```powershell
python -B -m unittest discover -s tests/framework -v
python -B -m unittest discover -s applications/cool-plugin-design-assistant/tests -v
python -B -m unittest discover -s applications/plugin-builder/tests -v
python -B -m unittest tests.test_workbench_handoff_interoperability -v
```

Expected: PASS except explicitly documented platform skips.

- [ ] **Step 2: Run repository verification**

```powershell
python -B scripts/verify_extraction.py --application cool-plugin-design-assistant
python -B scripts/verify_extraction.py --application plugin-builder
```

Expected: both result documents report applicable local gates PASS and preserve honest runtime/publication states.

- [ ] **Step 3: Build Plugin Builder twice in isolated output roots**

Use `build_marketplace_release.py --version 0.1.3` twice, create the flat host-upload ZIP twice, and compare complete member manifests and SHA-256 values. Expected: byte-identical artifacts.

- [ ] **Step 4: Verify extracted artifacts**

Validate both Plugin Builder manifests, every skill, reference closure, vendored runtime closure, absence of caches/private paths, and standalone create/update execution using the canonical full and delta fixtures.

- [ ] **Step 5: Audit the Git boundary**

```powershell
git diff --check
git status --short
git log --oneline --decorate -12
```

Expected: only intended interface/release-candidate changes are committed; the two unrelated Vibe Coding Designer files remain untouched and uncommitted.

- [ ] **Step 6: Record final local evidence if counts or hashes changed**

Update runtime compatibility and coverage documents only with directly observed commands, counts, skips, and artifact identities. Re-run the affected tests after documentation changes.

- [ ] **Step 7: Commit final evidence**

```powershell
git add applications/plugin-builder/docs applications/plugin-builder/tests/coverage-matrix.md applications/cool-plugin-design-assistant/tests/coverage-matrix.md
git commit -m "docs: record Plugin Builder 0.1.3 interface evidence"
```

Do not commit if no tracked evidence changed.
