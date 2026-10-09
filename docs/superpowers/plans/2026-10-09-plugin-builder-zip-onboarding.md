# Plugin Builder ZIP-to-Workbench Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fail-closed Workbench adapter that turns an evidence-bound Plugin Builder ZIP into a deterministic, unapproved Codex marketplace registration proposal without mutating either repository.

**Architecture:** Add a focused `plugin_onboarding` framework package that parses strict contracts, verifies archive and Plugin Builder metadata closure, derives publication-only decisions and diagnostics, and transactionally materializes a normal Workbench application proposal. Expose one `prepare-plugin-zip-marketplace` CLI command; after owner approval, the generated registration uses the unchanged catalog-driven marketplace pipeline.

**Tech Stack:** Python 3.11+, standard library dataclasses/JSON/ZIP/filesystem APIs, existing `plugin_authoring`, distribution-contract, marketplace, result-schema, and Windows test-environment APIs, `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-09-plugin-builder-zip-onboarding-design.md`

## Global Constraints

- Accept only `plugin-builder-package-v2` and `plugin-builder-package-v3` metadata with the `PORTABLE_SINGLE_DIRECTORY` envelope.
- Require the Plugin Builder ZIP, `package-metadata.json`, `plugin-publication-decisions-v1`, an explicit Workbench repository root, and an owned output root; runtime evidence remains optional.
- First-version publication target is Codex in marketplace `obvious-one`; OpenClaw and ClawHub are `NOT APPLICABLE`.
- Reuse Plugin Builder evidence without rerunning planning, W1, building, W2, or semantic requirement compilation.
- Treat valid local metadata closure as `STATICALLY VERIFIED`, never as producer authentication or installed-runtime proof.
- Missing authority is `BLOCKED`; tampering, unsafe content, and unsupported input are `FAIL`.
- Never execute imported plugin code during intake.
- Never edit `applications/`, `marketplaces/`, the marketplace checkout, or Git from the onboarding command.
- Preserve imported plugin bytes exactly; do not repair manifests, skills, tools, or references.
- Use transactional output replacement, stable path-redacted diagnostics, one ASCII-safe `result-schema-v1` document, and existing exit-code semantics.
- Generate only MIT registrations in v1 using the owner-recorded author and copyright year; other licenses are unsupported without a later contract revision.
- Use genuine Windows system temp, forced UTF-8, and the repository's capability probe for Windows tests.
- Every implementation task follows red-green TDD and ends in a focused commit.

## Review Focus

- A metadata file whose member list is correct but whose canonical member-manifest digest is stale must fail before output creation; Task 2 adds this test.
- An existing plugin ID in either `applications/` or the preparation catalog must block without treating a higher version as update authorization; Task 3 adds both tests.
- Mixed text/binary imported contents must generate complete schema-v3 content rules without classifying executable or secret material as publishable; Task 4 adds this test.
- A destination that is nonempty but lacks the onboarding ownership marker must remain byte-for-byte unchanged; Task 4 adds the rollback/collision test.
- Optional runtime evidence with a matching ZIP but stale candidate, plan/session, verification, or operation identities must not upgrade any runtime state; Task 2 adds parameterized mismatch tests.

---

## File Map

### New framework package

- `src/obvious_one_plugin_framework/plugin_onboarding/__init__.py`: public onboarding API exports.
- `src/obvious_one_plugin_framework/plugin_onboarding/contract.py`: strict package-metadata and owner-decision contracts plus stable errors.
- `src/obvious_one_plugin_framework/plugin_onboarding/inspection.py`: safe ZIP, manifest, member, tool, dependency, secret, and optional-evidence inspection.
- `src/obvious_one_plugin_framework/plugin_onboarding/proposal.py`: repository collision checks and deterministic proposal model.
- `src/obvious_one_plugin_framework/plugin_onboarding/templates.py`: product-neutral generated Workbench documents, scripts, tests, contract, and catalog entry.
- `src/obvious_one_plugin_framework/plugin_onboarding/materialize.py`: orchestration and transactional output publication.

### Modified framework surfaces

- `src/obvious_one_plugin_framework/__init__.py`: export stable onboarding types and entry point.
- `src/obvious_one_plugin_framework/cli.py`: parse and dispatch `prepare-plugin-zip-marketplace`, preserving result and exit-code conventions.
- `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`: document inputs, statuses, proposal review, and the unchanged publication boundary.

### New tests

- `tests/framework/plugin_onboarding_fixtures.py`: construct deterministic v2/v3 Plugin Builder packages and repositories in isolated test roots.
- `tests/framework/test_plugin_onboarding_contract.py`: strict input contracts and authority states.
- `tests/framework/test_plugin_onboarding_inspection.py`: archive, metadata, manifest, evidence, tool, secret, and safety closure.
- `tests/framework/test_plugin_onboarding_proposal.py`: collision checks, target rules, statuses, and proposal identity.
- `tests/framework/test_plugin_onboarding_materialize.py`: deterministic templates, exact imported bytes, transactions, and generated registration validity.
- `tests/framework/test_plugin_onboarding_cli.py`: one-result CLI and exit-code behavior.
- `tests/framework/test_plugin_onboarding_marketplace.py`: generated registration through unchanged marketplace preparation and verification.

## Task 1: Strict onboarding contracts

**Files:**
- Create: `src/obvious_one_plugin_framework/plugin_onboarding/__init__.py`
- Create: `src/obvious_one_plugin_framework/plugin_onboarding/contract.py`
- Create: `tests/framework/plugin_onboarding_fixtures.py`
- Create: `tests/framework/test_plugin_onboarding_contract.py`

**Interfaces:**
- Produces: `OnboardingError(code: str, status: Literal["BLOCKED", "FAIL"], detail: str = "")`.
- Produces: immutable `PackageMetadata`, `PublicationDecisions`, `PackageMember`, and `CandidateMember` dataclasses.
- Produces: `load_package_metadata(path: Path) -> PackageMetadata`.
- Produces: `load_publication_decisions(path: Path) -> PublicationDecisions`.
- Produces: fixture helpers `write_plugin_builder_fixture(root: Path, *, schema: str = "plugin-builder-package-v3", files: Mapping[str, bytes] | None = None) -> PluginBuilderFixture` and `write_publication_decisions(path: Path, *, overrides: Mapping[str, object] | None = None) -> Path`.

- [ ] **Step 1: Write failing contract tests**

Add tests named:

- `test_v2_and_v3_metadata_parse_to_typed_exact_contracts`;
- `test_unknown_missing_and_wrong_typed_metadata_fields_fail_closed`;
- `test_publication_decisions_require_exact_codex_obvious_one_values`;
- `test_missing_or_false_owner_authority_is_blocked`;
- `test_mit_author_year_and_third_party_notice_states_are_strict`; and
- `test_contract_diagnostics_do_not_expose_absolute_paths`.

Assert the exact schema names, fixed target values, allowed third-party enum,
three required approval booleans, and `BLOCKED` versus `FAIL` distinction.

- [ ] **Step 2: Run the contract tests and confirm the red state**

Run:

```powershell
python -B -m unittest tests.framework.test_plugin_onboarding_contract -v
```

Expected: import failure for the missing `plugin_onboarding.contract` API.

- [ ] **Step 3: Implement the strict dataclasses and parsers**

Implement the interfaces above. Reject unknown keys; canonicalize no input;
retain `decision_recorded_at` as evidence while excluding it from the decisions
identity payload. Use stable codes prefixed `onboarding.metadata.` and
`onboarding.decisions.`.

- [ ] **Step 4: Run Task 1 tests**

Run the command from Step 2. Expected: all Task 1 tests pass.

- [ ] **Step 5: Commit Task 1**

```powershell
git add src/obvious_one_plugin_framework/plugin_onboarding tests/framework/plugin_onboarding_fixtures.py tests/framework/test_plugin_onboarding_contract.py
git commit -m "feat: define plugin onboarding contracts"
```

## Task 2: Safe archive, metadata, and optional-evidence inspection

**Files:**
- Create: `src/obvious_one_plugin_framework/plugin_onboarding/inspection.py`
- Create: `tests/framework/test_plugin_onboarding_inspection.py`
- Modify: `tests/framework/plugin_onboarding_fixtures.py`

**Interfaces:**
- Consumes: Task 1 contracts and existing `plugin_authoring` archive, manifest, skill, tool, MCP, and tree validators.
- Produces: immutable `OnboardingInspection` with plugin identity, archive/package-metadata/tree identities, exact members, manifest profile, dependency/tool/runtime summaries, evidence states, and diagnostics.
- Produces: `inspect_plugin_builder_package(archive: Path, metadata: PackageMetadata, *, evidence: Path | None = None) -> OnboardingInspection`.

- [ ] **Step 1: Write failing happy-path and closure tests**

Add tests named:

- `test_v2_and_v3_packages_close_archive_members_candidate_and_manifests`;
- `test_member_manifest_digest_is_recomputed_canonically`;
- `test_manifest_identity_interface_and_decision_fields_are_preserved`;
- `test_tool_mcp_dependency_and_runtime_states_are_inventoried_without_execution`; and
- `test_no_evidence_keeps_all_installed_layers_not_verified`.

Assert that a valid fixture returns `STATICALLY VERIFIED` package structure,
the exact input hashes, and no upgraded installed-runtime evidence.

- [ ] **Step 2: Write failing adversarial archive tests**

Cover archive hash, size, member hash, candidate member, envelope, portable
manifest, compatibility manifest, duplicate, alias, case-fold, traversal,
link/reparse, compression, file/directory collision, development import,
credential-like content, and missing third-party notices. Assert no output or
source mutation occurs.

- [ ] **Step 3: Write failing optional-evidence identity tests**

Parameterize stale ZIP, plan/session, candidate, verification, and operation
bindings. Matching evidence may preserve only its directly observed states;
every mismatch returns `FAIL` and no state becomes `RUNTIME VERIFIED`.

- [ ] **Step 4: Run the inspection tests and confirm the red state**

```powershell
python -B -m unittest tests.framework.test_plugin_onboarding_inspection -v
```

Expected: import failure for `inspect_plugin_builder_package`.

- [ ] **Step 5: Implement inspection without executing imported code**

Use temporary extraction through `plugin_authoring.extract_archive`, require
`PORTABLE_SINGLE_DIRECTORY`, recompute all canonical identities, call existing
static validators, scan declared dependencies and public content, and discard
the temporary tree before returning the immutable report.

- [ ] **Step 6: Run Task 1 and Task 2 tests**

```powershell
python -B -m unittest tests.framework.test_plugin_onboarding_contract tests.framework.test_plugin_onboarding_inspection -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit Task 2**

```powershell
git add src/obvious_one_plugin_framework/plugin_onboarding/inspection.py tests/framework/plugin_onboarding_fixtures.py tests/framework/test_plugin_onboarding_inspection.py
git commit -m "feat: verify Plugin Builder package closure"
```

## Task 3: Publication audit and deterministic proposal model

**Files:**
- Create: `src/obvious_one_plugin_framework/plugin_onboarding/proposal.py`
- Create: `tests/framework/test_plugin_onboarding_proposal.py`
- Modify: `tests/framework/plugin_onboarding_fixtures.py`

**Interfaces:**
- Consumes: `OnboardingInspection` and `PublicationDecisions`.
- Produces: immutable `OnboardingProposal` with schema `plugin-onboarding-proposal-v1`, proposal SHA-256, relative application path, exact schema-v2 catalog entry, generated-file model, evidence states, and stable diagnostics.
- Produces: `build_onboarding_proposal(inspection: OnboardingInspection, decisions: PublicationDecisions, repository: Path) -> OnboardingProposal`.

- [ ] **Step 1: Write failing proposal and identity tests**

Add tests named:

- `test_proposal_is_path_independent_and_excludes_recorded_at_from_identity`;
- `test_proposal_is_codex_build_and_openclaw_not_applicable`;
- `test_proposal_preserves_builder_and_runtime_evidence_states`;
- `test_repository_paths_and_private_input_locations_never_enter_payload`; and
- `test_byte_identical_inputs_produce_identical_proposal_json_and_sha256`.

- [ ] **Step 2: Write failing publication-audit tests**

Cover unsupported license, missing rights, third-party notice mismatch,
undeclared executable/dependency/service/remote asset, destination escape or
collision, duplicate catalog destination, and secret findings. Pin stable
`BLOCKED` or `FAIL` codes from the spec.

- [ ] **Step 3: Write failing existing-plugin collision tests**

Add one fixture with `applications/<plugin-id>` and one with only an existing
catalog entry. Both must return
`onboarding.existing_plugin_requires_update_design` even when the proposed
version is higher. Assert neither source tree changes.

- [ ] **Step 4: Run the proposal tests and confirm the red state**

```powershell
python -B -m unittest tests.framework.test_plugin_onboarding_proposal -v
```

Expected: import failure for the missing proposal API.

- [ ] **Step 5: Implement publication audit and canonical proposal identity**

Read only the explicitly supplied repository. Parse its schema-v2 preparation
catalog through the public marketplace loader. Generate the exact Codex
`build` and OpenClaw `not_applicable` target record. Hash canonical JSON after
removing `decision_recorded_at` and all machine paths.

- [ ] **Step 6: Run Tasks 1–3 tests**

```powershell
python -B -m unittest tests.framework.test_plugin_onboarding_contract tests.framework.test_plugin_onboarding_inspection tests.framework.test_plugin_onboarding_proposal -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit Task 3**

```powershell
git add src/obvious_one_plugin_framework/plugin_onboarding/proposal.py tests/framework/plugin_onboarding_fixtures.py tests/framework/test_plugin_onboarding_proposal.py
git commit -m "feat: compile marketplace onboarding proposals"
```

## Task 4: Transactional Workbench registration materialization

**Files:**
- Create: `src/obvious_one_plugin_framework/plugin_onboarding/templates.py`
- Create: `src/obvious_one_plugin_framework/plugin_onboarding/materialize.py`
- Create: `tests/framework/test_plugin_onboarding_materialize.py`
- Modify: `src/obvious_one_plugin_framework/plugin_onboarding/__init__.py`

**Interfaces:**
- Consumes: Task 1 loaders, Task 2 inspection, Task 3 proposal.
- Produces: `prepare_plugin_zip_marketplace(archive: Path, package_metadata: Path, publication_decisions: Path, repository: Path, output: Path, *, evidence: Path | None = None) -> OperationResult`.
- Produces: output ownership marker `.obvious-one-plugin-onboarding` and the exact proposal tree from the specification.

- [ ] **Step 1: Write failing deterministic materialization tests**

Add tests named:

- `test_materialization_writes_exact_specified_tree_and_relative_result_paths`;
- `test_imported_plugin_bytes_equal_archive_candidate_members`;
- `test_two_independent_outputs_have_identical_files_and_tree_identity`;
- `test_generated_manifest_pair_and_arbitrary_skills_validate`;
- `test_mixed_text_and_binary_files_have_complete_v3_content_rules`; and
- `test_generated_mit_and_third_party_documents_follow_owner_decisions`.

- [ ] **Step 2: Write failing transaction tests**

Cover missing output, owned replacement, unmarked nonempty collision, staged
write failure at every replacement boundary, and prior-proposal preservation.
Assert no source or repository path is modified.

- [ ] **Step 3: Run the materialization tests and confirm the red state**

```powershell
python -B -m unittest tests.framework.test_plugin_onboarding_materialize -v
```

Expected: import failure for `prepare_plugin_zip_marketplace`.

- [ ] **Step 4: Implement product-neutral templates**

Generate canonical JSON and LF text. The application uses
`imported-plugin/` as immutable content authority. Generate:

- schema-v2 `conversion.json` with a Codex build command and bounded verification commands;
- schema-v3 `openclaw/distribution.json` with GitHub marketplace enabled, ClawHub disabled, exact text/binary paths, rights provenance, and a computed size limit;
- a deterministic standard-library Codex release builder that validates then copies imported bytes unchanged;
- a static distribution audit that imports no private framework APIs;
- invariant, inventory, decision, runtime-compatibility, security, privacy, distribution, and third-party documents; and
- self-contained generated tests for package identity and marketplace output.

- [ ] **Step 5: Implement transactional orchestration**

Load, inspect, build the proposal, safely re-extract and recheck the archive,
write a sibling staging tree, validate the complete generated registration,
write `onboarding-result.json` last, then atomically publish only to a missing
or owned output. Return relative `ArtifactRecord` and `MutationRecord` values.

- [ ] **Step 6: Run Tasks 1–4 tests**

```powershell
python -B -m unittest tests.framework.test_plugin_onboarding_contract tests.framework.test_plugin_onboarding_inspection tests.framework.test_plugin_onboarding_proposal tests.framework.test_plugin_onboarding_materialize -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit Task 4**

```powershell
git add src/obvious_one_plugin_framework/plugin_onboarding tests/framework/test_plugin_onboarding_materialize.py
git commit -m "feat: materialize onboarding registrations"
```

## Task 5: CLI and public framework integration

**Files:**
- Create: `tests/framework/test_plugin_onboarding_cli.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`
- Modify: `src/obvious_one_plugin_framework/cli.py`

**Interfaces:**
- Consumes: `prepare_plugin_zip_marketplace(...) -> OperationResult`.
- Produces: CLI command `prepare-plugin-zip-marketplace` with required `--archive`, `--package-metadata`, `--publication-decisions`, `--repository`, `--output`, optional `--evidence`, and accepted compatibility flag `--json`.

- [ ] **Step 1: Write failing CLI result tests**

Add tests named:

- `test_cli_success_emits_one_ascii_safe_pass_result`;
- `test_cli_missing_authority_is_blocked_exit_two`;
- `test_cli_tampering_is_fail_exit_three`;
- `test_cli_io_failure_is_exit_four`;
- `test_cli_invalid_arguments_create_no_output`;
- `test_cli_unicode_inputs_do_not_leak_absolute_paths`; and
- `test_cli_never_mutates_repository_or_marketplace`.

- [ ] **Step 2: Run the CLI tests and confirm the red state**

```powershell
python -B -m unittest tests.framework.test_plugin_onboarding_cli -v
```

Expected: parser rejects the missing command.

- [ ] **Step 3: Export the public API and wire CLI dispatch**

Map `OnboardingError.status` to the framework result without flattening
`BLOCKED` into `FAIL`. Add only recognized blocking codes to `BLOCKING_CODES`;
do not classify unsafe or tampered inputs as owner decisions.

- [ ] **Step 4: Run CLI and existing result-contract tests**

```powershell
python -B -m unittest tests.framework.test_plugin_onboarding_cli tests.framework.test_cli tests.framework.test_results -v
```

Expected: all tests pass and each invocation emits one result document.

- [ ] **Step 5: Commit Task 5**

```powershell
git add src/obvious_one_plugin_framework/__init__.py src/obvious_one_plugin_framework/cli.py tests/framework/test_plugin_onboarding_cli.py
git commit -m "feat: expose ZIP onboarding CLI"
```

## Task 6: End-to-end marketplace compatibility

**Files:**
- Create: `tests/framework/test_plugin_onboarding_marketplace.py`
- Modify: `tests/framework/plugin_onboarding_fixtures.py`
- Modify: `src/obvious_one_plugin_framework/plugin_onboarding/templates.py`
- Modify: `src/obvious_one_plugin_framework/plugin_onboarding/materialize.py`

**Interfaces:**
- Consumes: completed proposal tree and existing `load_contract`, `load_preparation_catalog`, `prepare_marketplace`, and `verify_marketplace` public APIs.
- Produces: evidence that an owner-approved copy of `application/` plus the exact `catalog-entry.json` works through the unchanged marketplace pipeline.

- [ ] **Step 1: Write the failing end-to-end onboarding test**

Test this sequence in an isolated repository and separate marketplace roots:

1. build a deterministic v3 Plugin Builder ZIP fixture;
2. prepare the onboarding proposal;
3. assert neither baseline changes;
4. simulate explicit owner application of only the generated application and catalog entry;
5. validate the schema-v3 distribution contract;
6. run generated application tests and verification commands;
7. call `prepare_marketplace` twice and compare full tree identities;
8. call filesystem and index verification;
9. commit the staged marketplace in a disposable Git root;
10. call commit and fresh-checkout verification; and
11. assert Codex catalog inclusion and OpenClaw absence.

- [ ] **Step 2: Write cross-platform byte and collision tests**

Add LF/CRLF, UTF-8, executable-bit normalization, binary asset, Windows
case-fold, immutable hash fixture, existing-marketplace destination, and
read-only baseline cases. Expected behavior must be identical on Windows,
Linux, and macOS.

- [ ] **Step 3: Run the end-to-end test and confirm the red state**

```powershell
python -B -m unittest tests.framework.test_plugin_onboarding_marketplace -v
```

Expected: failure at the first missing or incomplete generated-registration
contract.

- [ ] **Step 4: Complete only the templates and materialization required by the failing integration assertions**

Do not add a ZIP-specific branch to `marketplace.py`; the generated
registration must satisfy the existing public interfaces unchanged.

- [ ] **Step 5: Run the onboarding and marketplace regression set**

```powershell
python -B -m unittest tests.framework.test_plugin_onboarding_contract tests.framework.test_plugin_onboarding_inspection tests.framework.test_plugin_onboarding_proposal tests.framework.test_plugin_onboarding_materialize tests.framework.test_plugin_onboarding_cli tests.framework.test_plugin_onboarding_marketplace tests.framework.test_marketplace -v
```

Expected: all tests pass with only documented platform skips.

- [ ] **Step 6: Commit Task 6**

```powershell
git add src/obvious_one_plugin_framework/plugin_onboarding tests/framework/plugin_onboarding_fixtures.py tests/framework/test_plugin_onboarding_marketplace.py
git commit -m "test: prove onboarding marketplace compatibility"
```

## Task 7: Documentation and complete verification

**Files:**
- Modify: `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`
- Modify only if required by an actual new repository-wide gate: `scripts/verify_extraction.py`

**Interfaces:**
- Consumes: the finalized CLI and generated proposal contract.
- Produces: operator guidance that distinguishes proposal preparation, application adoption, marketplace staging, publication authorization, and runtime evidence.

- [ ] **Step 1: Document the command and approval boundary**

Add exact command syntax, required schemas, output tree, status and exit-code
meanings, owner-application step, marketplace commands, and explicit exclusions.
State that `PASS` means a static proposal, not publication or installed-runtime
readiness.

- [ ] **Step 2: Run the documentation and whitespace checks**

```powershell
rg -n "prepare-plugin-zip-marketplace|plugin-onboarding-proposal-v1|NOT VERIFIED" docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md
git diff --check
```

Expected: all three concepts are documented and `git diff --check` is silent.

- [ ] **Step 3: Establish the canonical Windows environment**

```powershell
& .\scripts\invoke_windows_test_environment.ps1 -ProbeOnly
```

Expected: `windows-test-environment-v1`, `PASS`, system temp outside the
repository, forced UTF-8, and PASS for filesystem, hard-link, atomic-replace,
Git, and packaging.

- [ ] **Step 4: Run the complete framework suite in that environment**

```powershell
& .\scripts\invoke_windows_test_environment.ps1 `
  -Executable python `
  -CommandArgument @('-B','-m','unittest','discover','-s','.\tests\framework','-v')
```

Expected: all framework tests pass with only documented platform skips.

- [ ] **Step 5: Run affected product and repository contract suites**

Run Plugin Builder, Cool Plugin Design Assistant, repository application
configuration, agent-contract, Windows-environment, and Workbench handoff
interoperability suites. Expected: all pass with only documented platform
skips and no tracked changes.

- [ ] **Step 6: Exercise a real Plugin Builder artifact locally**

Use an ignored `.tmp` root and a real v2 or v3 ZIP/metadata pair. Run the new
command twice, verify identical proposal identities and trees, manually inspect
the proposed catalog/application delta, and run the unchanged marketplace
filesystem verification against a separate staging root. Record static results
only; do not publish or mutate either repository.

- [ ] **Step 7: Run final repository checks**

```powershell
git diff --check
git status --short --branch
```

Expected: only intended tracked implementation and documentation changes; all
generated artifacts remain below ignored `.tmp` or `dist` roots.

- [ ] **Step 8: Commit Task 7**

```powershell
git add docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md
git commit -m "docs: document plugin ZIP onboarding"
```

If Step 5 proves a repository-wide gate change is necessary, stage
`scripts/verify_extraction.py` explicitly before the commit; otherwise leave it
untouched.

## Final Review Gate

After Task 7:

1. review every commit and the complete branch diff against the approved spec;
2. confirm all diagnostic statuses and runtime evidence language are exact;
3. confirm no generated template contains product-specific domain content;
4. confirm no marketplace or remote Git mutation occurred;
5. run the complete verification commands again after any review fix;
6. use a fresh whole-branch reviewer; and
7. present integration options without pushing, merging, publishing, tagging,
   or submitting unless the owner separately authorizes them.
