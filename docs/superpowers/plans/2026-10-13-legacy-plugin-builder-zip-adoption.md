# Legacy Plugin Builder ZIP Adoption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed Workbench adoption path that onboards an exact historical Plugin Builder deterministic-content-v2 ZIP without changing its imported members or relabeling its evidence.

**Architecture:** Add a strict `LegacyPluginBuilderAdoption` contract beside the current Plugin Builder and repair metadata contracts. A dedicated inspector closes the external owner record against the historical archive and maps only independently observed facts into the existing `OnboardingInspection`; the existing proposal and marketplace pipeline then remain product-neutral, with small explicit extensions for owner-approved executable and dependency paths.

**Tech Stack:** Python 3.11+, standard-library `dataclasses`, `json`, `hashlib`, `pathlib`, `tempfile`, `zipfile`, `unittest`, the existing `obvious_one_plugin_framework` APIs, and the canonical Windows test-environment runner.

**Spec:** `docs/superpowers/specs/2026-10-13-legacy-plugin-builder-zip-adoption-design.md`

## Global Constraints

- Keep `Vibe_StorySpirit_Director_v1.0.2.zip` immutable; its SHA-256 is `01284edd379ed97e09e8d6bac08d2009d9b2f460ea3654d03f167a1d31305633`.
- Recognize only explicit schema `workbench-legacy-plugin-builder-adoption-v1` with input profile `PLUGIN_BUILDER_DETERMINISTIC_CONTENT_V2`.
- Never classify the adoption record as Plugin Builder v2/v3 metadata or authenticate the historical producer.
- Preserve strict archive safety, SHA-256 closure, manifest authority, exact imported bytes, transactionality, and fail-closed behavior.
- Keep current Plugin Builder v2/v3, candidate-v1, versioned-legacy, and Workbench-repaired paths behaviorally unchanged.
- Keep installed-runtime layers `NOT VERIFIED`; successful intake is at most `STATICALLY VERIFIED`.
- Keep OpenClaw and ClawHub `NOT APPLICABLE` for this bounded Codex-only adoption profile.
- Do not infer MIT licensing, redistribution, third-party-content disposition, or public-marketplace authority.
- Do not mutate tracked applications, marketplace baselines, Git remotes, tags, releases, or external registries.
- Run filesystem, Git, hard-link, archive, and packaging tests through `scripts/invoke_windows_test_environment.ps1` using genuine system temp storage and forced UTF-8.

## File Structure

- `src/obvious_one_plugin_framework/plugin_onboarding/contract.py`: strict adoption dataclass and loader.
- `src/obvious_one_plugin_framework/plugin_onboarding/inspection.py`: historical deterministic-content-v2 recognition and closure.
- `src/obvious_one_plugin_framework/plugin_onboarding/proposal.py`: explicit adoption-authorized executable/dependency audit behavior.
- `src/obvious_one_plugin_framework/plugin_onboarding/materialize.py`: select exactly one metadata authority and materialize the unchanged imported tree.
- `src/obvious_one_plugin_framework/plugin_onboarding/__init__.py`: public exports.
- `src/obvious_one_plugin_framework/cli.py`: mutually exclusive `--package-metadata` / `--legacy-adoption` interface.
- `tests/framework/plugin_onboarding_fixtures.py`: deterministic historical Plugin Builder fixture and adoption record writer.
- `tests/framework/test_plugin_onboarding_contract.py`: schema and owner-authority tests.
- `tests/framework/test_plugin_onboarding_inspection.py`: authority, manifest, archive, evidence, and audit tests.
- `tests/framework/test_plugin_onboarding_materialize.py`: exact-byte proposal and compatibility tests.
- `tests/framework/test_plugin_onboarding_cli.py`: CLI selection and result-schema tests.
- `tests/test_agents_contract.py` and `tests/test_documentation_contract.py`: tracked guidance contract coverage.
- `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md` and `AGENTS.md`: operator and repository instructions.

## Review Focus

- A ZIP that contains both the historical manifest set and any current/repair authority must fail with `onboarding.inspection.authority_ambiguous` (Task 2).
- A content manifest that is internally correct but omits an archive member must fail rather than letting the adoption member list substitute for producer closure (Task 2).
- A historical portable manifest may omit later-only interface fields, but any overlapping manifest-pair value must match exactly (Task 2).
- An approved executable or dependency list must match the observed set exactly; neither an undeclared observed path nor a stale approved path may pass (Tasks 2 and 3).
- Supplying both authority options, neither option, or legacy adoption plus runtime evidence must fail deterministically before output mutation (Task 4).

---

### Task 1: Strict Legacy Adoption Contract

**Files:**
- Modify: `src/obvious_one_plugin_framework/plugin_onboarding/contract.py`
- Modify: `src/obvious_one_plugin_framework/plugin_onboarding/__init__.py`
- Modify: `tests/framework/plugin_onboarding_fixtures.py`
- Modify: `tests/framework/test_plugin_onboarding_contract.py`

**Interfaces:**
- Consumes: existing `PackageMember`, `_members`, digest, text, exact-key, plugin-ID, semantic-version, and timestamp validators.
- Produces: `LegacyPluginBuilderAdoption`, `load_legacy_plugin_builder_adoption(path: Path) -> LegacyPluginBuilderAdoption`, `LegacyPluginBuilderFixture`, `write_legacy_plugin_builder_fixture(root: Path, *, files: Mapping[str, bytes] | None = None) -> LegacyPluginBuilderFixture`, and `write_legacy_adoption(path: Path, fixture: LegacyPluginBuilderFixture, *, overrides: Mapping[str, object] | None = None) -> Path`.

- [ ] **Step 1: Write failing contract tests and deterministic fixtures**

Add tests that assert the valid fixture loads every field from Section 5 of the spec, preserves ordered members, and exposes an `identity_payload()` that excludes only `decision_recorded_at`. Add table-driven failures for unknown/missing fields, uppercase or malformed digests, invalid plugin ID/version, wrong fixed paths/profile/purpose, duplicate or unsafe member paths, mismatched executable/dependency member paths, false `adoption_approved`, empty confirmer, and timezone-naive timestamps.

- [ ] **Step 2: Run the contract tests and verify RED**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 `
  -Executable python `
  -CommandArgument @("-B", "-m", "unittest", "tests.framework.test_plugin_onboarding_contract", "-v")
```

Expected: FAIL because `LegacyPluginBuilderAdoption`, its loader, and fixture writers do not exist.

- [ ] **Step 3: Implement the strict contract**

Add frozen dataclass `LegacyPluginBuilderAdoption` with the exact spec fields and method `identity_payload(self) -> dict[str, object]`. Implement `load_legacy_plugin_builder_adoption()` with prefix `onboarding.legacy_adoption`, exact keys, safe unique POSIX member paths, fixed profile/path/purpose values, exact executable/dependency subsets, approval state, and aware ISO-8601 timestamp validation. Export the dataclass and loader from the package.

- [ ] **Step 4: Run the contract tests and verify GREEN**

Run the Step 2 command. Expected: all `test_plugin_onboarding_contract` tests pass.

- [ ] **Step 5: Commit Task 1**

```powershell
git add src/obvious_one_plugin_framework/plugin_onboarding/contract.py src/obvious_one_plugin_framework/plugin_onboarding/__init__.py tests/framework/plugin_onboarding_fixtures.py tests/framework/test_plugin_onboarding_contract.py
git commit -m "feat: define legacy Plugin Builder adoption contract"
```

### Task 2: Historical Plugin Builder Inspection and Evidence Separation

**Files:**
- Modify: `src/obvious_one_plugin_framework/plugin_onboarding/inspection.py`
- Modify: `tests/framework/test_plugin_onboarding_inspection.py`
- Modify: `tests/framework/plugin_onboarding_fixtures.py`

**Interfaces:**
- Consumes: `LegacyPluginBuilderAdoption`, safe archive inventory/extraction, `_scan_public_content()`, and `OnboardingInspection`.
- Produces: `inspect_legacy_plugin_builder_package(archive: Path, adoption: LegacyPluginBuilderAdoption) -> OnboardingInspection`; new `OnboardingInspection.approved_executable_files` and `.approved_dependency_files` tuples, empty for every existing profile.

- [ ] **Step 1: Write failing recognition, closure, and evidence tests**

Add focused tests for the valid historical profile and for archive/member/tree digest tampering; missing, extra, duplicate, or stale content-manifest entries; candidate-manifest exclusion violations; verification identity mismatch; adoption internal-file hash mismatch; mixed authority; unknown format; unsafe members; secret/development import findings; executable/dependency exact-set mismatch; later-only portable interface omissions; and contradictory overlapping manifest values. Assert `producer_claims` retains historical statements, `package_state` is `STATICALLY VERIFIED`, every installed-runtime evidence layer is `NOT VERIFIED`, and no v2/v3 candidate or verification digest is fabricated.

- [ ] **Step 2: Run the inspection tests and verify RED**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 `
  -Executable python `
  -CommandArgument @("-B", "-m", "unittest", "tests.framework.test_plugin_onboarding_inspection", "-v")
```

Expected: FAIL because the dedicated legacy Plugin Builder inspector and approved-content fields do not exist.

- [ ] **Step 3: Implement archive and internal-manifest closure**

Implement `inspect_legacy_plugin_builder_package()` plus private focused helpers for authority exclusion, overlapping manifest identity, deterministic-content-v2 closure, candidate-content-v2 exclusions, and verification-report claim capture. Compare the adoption member list, member digest, tree digest, fixed internal paths/hashes, executable set, and dependency set to current observations. Do not call the current v2/v3 manifest validator and do not relax it.

- [ ] **Step 4: Populate evidence without promotion**

Set the new approved path tuples from the adoption record; keep tool contracts, runtime realizations, optional evidence, and installed-runtime states empty or `NOT VERIFIED`. Store internal historical values only under `producer_claims`, with Workbench-computed hashes under the normal inspection identity fields.

- [ ] **Step 5: Run focused inspection and compatibility tests**

Run the Step 2 command, then:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 `
  -Executable python `
  -CommandArgument @("-B", "-m", "unittest", "tests.framework.test_plugin_onboarding_versioned_legacy_profile", "tests.framework.test_plugin_onboarding_workbench_repair_v2", "-v")
```

Expected: all selected tests pass and existing profiles retain their prior evidence states.

- [ ] **Step 6: Commit Task 2**

```powershell
git add src/obvious_one_plugin_framework/plugin_onboarding/inspection.py tests/framework/plugin_onboarding_fixtures.py tests/framework/test_plugin_onboarding_inspection.py
git commit -m "feat: inspect deterministic legacy Plugin Builder packages"
```

### Task 3: Proposal Audit and Exact-Byte Materialization

**Files:**
- Modify: `src/obvious_one_plugin_framework/plugin_onboarding/proposal.py`
- Modify: `src/obvious_one_plugin_framework/plugin_onboarding/materialize.py`
- Modify: `src/obvious_one_plugin_framework/plugin_onboarding/templates.py`
- Modify: `tests/framework/test_plugin_onboarding_materialize.py`
- Modify: `tests/framework/test_plugin_onboarding_proposal.py`

**Interfaces:**
- Consumes: `inspect_legacy_plugin_builder_package()`, `LegacyPluginBuilderAdoption`, existing `build_onboarding_proposal()`, templates, and transactional materializer.
- Produces: `prepare_plugin_zip_marketplace(..., package_metadata: Path | None, ..., legacy_adoption: Path | None = None, evidence: Path | None = None) -> OperationResult` with exactly one authority input; proposal evidence carrying the adoption identity; generated application tests that preserve source members and distinguish generated overlays.

- [ ] **Step 1: Write failing proposal and materialization tests**

Assert that a valid legacy adoption produces the normal Codex-only catalog entry and proposal, imports every archive member byte-for-byte, records the adoption digest and input profile, leaves runtime states `NOT VERIFIED`, and produces deterministic independent outputs. Add negative tests for executable/dependency set mismatch, imported/generated path collision, existing application/catalog ID, output rollback, legacy runtime evidence, both/no authority inputs, and a changed source archive after approval.

- [ ] **Step 2: Run proposal and materialization tests and verify RED**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 `
  -Executable python `
  -CommandArgument @("-B", "-m", "unittest", "tests.framework.test_plugin_onboarding_proposal", "tests.framework.test_plugin_onboarding_materialize", "-v")
```

Expected: FAIL because the proposal audit does not recognize adoption-approved paths and the materializer cannot select the new authority.

- [ ] **Step 3: Extend declared-content auditing**

Update `_audit_declared_content()` so executable and dependency paths explicitly approved by the legacy adoption inspection satisfy publication declaration only for that profile. Preserve MCP, remote asset, credential, tool-contract, and current-package behavior unchanged; stale or extra approval paths already fail inspection.

- [ ] **Step 4: Extend transactional materialization**

Update `prepare_plugin_zip_marketplace()` to require exactly one of `package_metadata` and `legacy_adoption`, load and inspect the selected authority, reject evidence with legacy adoption, include every supplied authority path in output-boundary checks, and select `LEGACY_FLAT` without heuristic fallback. Include the adoption identity in proposal evidence without embedding absolute paths or the observation timestamp in deterministic identity.

- [ ] **Step 5: Extend generated exact-byte tests and overlays**

Keep `imported-plugin/` identical to the extracted archive tree. Ensure generated marketplace-owned `LICENSE` and policy files remain outside that tree, reject collisions, and make generated application tests assert both imported tree identity and published-copy preservation before any permitted overlay is added.

- [ ] **Step 6: Run focused tests and verify GREEN**

Run the Step 2 command. Expected: all proposal and materialization tests pass.

- [ ] **Step 7: Commit Task 3**

```powershell
git add src/obvious_one_plugin_framework/plugin_onboarding/proposal.py src/obvious_one_plugin_framework/plugin_onboarding/materialize.py src/obvious_one_plugin_framework/plugin_onboarding/templates.py tests/framework/test_plugin_onboarding_proposal.py tests/framework/test_plugin_onboarding_materialize.py
git commit -m "feat: materialize exact legacy Plugin Builder proposals"
```

### Task 4: CLI Authority Selection and Result Semantics

**Files:**
- Modify: `src/obvious_one_plugin_framework/cli.py`
- Modify: `tests/framework/test_plugin_onboarding_cli.py`

**Interfaces:**
- Consumes: extended `prepare_plugin_zip_marketplace()` API.
- Produces: mutually exclusive CLI options `--package-metadata` and `--legacy-adoption`; unchanged single-document `result-schema-v1` output and exit meanings.

- [ ] **Step 1: Write failing CLI tests**

Add tests for successful `--legacy-adoption`, current `--package-metadata` regression, both options, neither option, legacy plus `--evidence`, false adoption approval, tampered archive, Unicode paths, pre-existing output, and single ASCII-safe result output. Assert exit 0 for `PASS`, 2 for `BLOCKED`, 3 for validation `FAIL`, and no output mutation on failure.

- [ ] **Step 2: Run CLI tests and verify RED**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 `
  -Executable python `
  -CommandArgument @("-B", "-m", "unittest", "tests.framework.test_plugin_onboarding_cli", "-v")
```

Expected: FAIL because the parser requires `--package-metadata` and has no `--legacy-adoption` option.

- [ ] **Step 3: Implement parser and dispatch changes**

Use an argparse mutually exclusive group requiring one authority option. Forward `package_metadata` or `legacy_adoption` without changing error adaptation. Keep `inspect-plugin-zip` behavior unchanged; the new adoption path is explicit and must not make unknown legacy inspection succeed heuristically.

- [ ] **Step 4: Run CLI and complete onboarding-focused tests**

Run the Step 2 command, then:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 `
  -Executable python `
  -CommandArgument @("-B", "-m", "unittest", "discover", "-s", ".\tests\framework", "-p", "test_plugin_onboarding*.py", "-v")
```

Expected: all onboarding tests pass.

- [ ] **Step 5: Commit Task 4**

```powershell
git add src/obvious_one_plugin_framework/cli.py tests/framework/test_plugin_onboarding_cli.py
git commit -m "feat: expose legacy Plugin Builder adoption intake"
```

### Task 5: Repository Guidance and Documentation Contracts

**Files:**
- Modify: `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`
- Modify: `AGENTS.md`
- Modify: `tests/test_documentation_contract.py`
- Modify: `tests/test_agents_contract.py`

**Interfaces:**
- Consumes: final CLI and evidence semantics from Tasks 1–4.
- Produces: operator guidance that separates current metadata, legacy Plugin Builder adoption, publication decisions, proposal adoption, marketplace mutation, and runtime evidence.

- [ ] **Step 1: Write failing documentation contract tests**

Require the command reference and `AGENTS.md` to name `workbench-legacy-plugin-builder-adoption-v1`, `--legacy-adoption`, immutable imported bytes, explicit owner authority, unsupported legacy runtime evidence, and the rule that this profile is not Plugin Builder v2/v3 evidence.

- [ ] **Step 2: Run documentation tests and verify RED**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 `
  -Executable python `
  -CommandArgument @("-B", "-m", "unittest", "tests.test_documentation_contract", "tests.test_agents_contract", "-v")
```

Expected: FAIL because the new contract and option are not documented.

- [ ] **Step 3: Update operator and repository documentation**

Add the legacy Plugin Builder adoption command form, exact evidence states, failure semantics, required separate publication decisions, and follow-on marketplace sequence. Keep the current v2/v3 command form and warn that arbitrary legacy ZIPs remain unsupported.

- [ ] **Step 4: Run documentation tests and verify GREEN**

Run the Step 2 command. Expected: all selected documentation tests pass.

- [ ] **Step 5: Commit Task 5**

```powershell
git add docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md AGENTS.md tests/test_documentation_contract.py tests/test_agents_contract.py
git commit -m "docs: explain legacy Plugin Builder ZIP adoption"
```

### Task 6: Complete Verification and StorySpirit Pre-Publication Evidence

**Files:**
- Generated only below ignored `.tmp/storyspirit-director-1.0.2-onboarding/`
- No tracked production changes unless a verified regression requires a preceding red-green task amendment.

**Interfaces:**
- Consumes: completed feature, approved spec, immutable StorySpirit ZIP, and repository verification commands.
- Produces: complete local verification evidence and an exact draft adoption record; publication decisions and marketplace mutation remain pending.

- [ ] **Step 1: Probe the canonical Windows environment**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 -ProbeOnly
```

Expected: `status: PASS`, genuine system temp outside the repository, and `PASS` for filesystem, hard link, atomic replace, Git, and packaging.

- [ ] **Step 2: Run the complete framework suite**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 `
  -Executable python `
  -CommandArgument @("-B", "-m", "unittest", "discover", "-s", ".\tests\framework", "-v")
```

Expected: all framework tests pass, with only explicitly documented environment skips.

- [ ] **Step 3: Run all top-level repository contract suites**

Run:

```powershell
& .\scripts\invoke_windows_test_environment.ps1 `
  -Executable python `
  -CommandArgument @(
    "-B", "-m", "unittest",
    "tests.test_agents_contract",
    "tests.test_application_config",
    "tests.test_distribution_equivalence",
    "tests.test_documentation_contract",
    "tests.test_extraction_boundary",
    "tests.test_repo_contract",
    "tests.test_repository_layout",
    "tests.test_templates",
    "tests.test_verify_extraction",
    "tests.test_windows_test_environment",
    "tests.test_workbench_handoff_interoperability",
    "-v"
  )
```

Expected: all top-level repository, documentation, boundary, layout, template, handoff, and environment tests pass.

- [ ] **Step 4: Verify repository text and Git state**

Run:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors and no uncommitted tracked changes after task commits.

- [ ] **Step 5: Create and validate the draft StorySpirit adoption record**

Use a temporary, non-production helper below `.tmp/` that calls the public `plugin_authoring.inventory_archive()`, `extract_archive()`, `tree_manifest()`, and `tree_sha256()` APIs to write the draft record. Bind it to archive SHA-256 `01284edd379ed97e09e8d6bac08d2009d9b2f460ea3654d03f167a1d31305633`, the observed inventory, internal manifest hashes, and exact executable/dependency lists. Load the record with `load_legacy_plugin_builder_adoption()` and run `inspect_legacy_plugin_builder_package()`; require the expected `STATICALLY VERIFIED` / runtime `NOT VERIFIED` split. Do not create publication decisions or an onboarding proposal yet, and do not promote the temporary helper into production code.

- [ ] **Step 6: Record the remaining owner gate**

Report the exact detected author, third-party notice state, executable/dependency inventory, adoption-record SHA-256, and required publication-decision fields. Stop before proposal generation until the owner explicitly confirms MIT licensing, redistribution approval, third-party-content disposition, and public Obvious One approval.

## Plan Self-Review

- Spec coverage: Tasks 1–5 implement the contract, authority, inspection, exact-byte, CLI, compatibility, documentation, and failure requirements; Task 6 covers complete verification and the initial artifact without crossing publication authority.
- Type consistency: `LegacyPluginBuilderAdoption`, `inspect_legacy_plugin_builder_package()`, the approved path tuples, and `legacy_adoption` are named consistently across producers and consumers.
- Review focus: all five identified high-risk input classes have explicit tests in Tasks 2–4.
- Proportion: the plan specifies interfaces, test assertions, commands, and task boundaries without transcribing implementation bodies.
- Publication boundary: no task creates publication decisions, adopts the proposal, pushes, merges, tags, releases, or publishes externally.
