# Reference Application Decoupling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove Cool Bible Tutor as an operational prerequisite of generic provenance and verification while preserving it as the first reference application and preserving the configured Obvious One marketplace.

**Architecture:** Extend schema-v2 application configuration with declarative provenance rules, implement generic provenance generation and validation in the framework, and move provenance evaluation into each selected application's gate sequence. Shared gates retain only repository-wide checks, while application-specific assertions live below the owning application.

**Tech Stack:** Python 3.11+, `dataclasses`, `pathlib`, `json`, `hashlib`, `subprocess`, `unittest`, Git worktrees.

**Spec:** `docs/superpowers/specs/2026-09-14-reference-application-decoupling-design.md`

## Global Constraints

- Cool Bible Tutor remains the reference application, not a required framework fixture.
- `schao523/obvious-one-plugins` remains its configured marketplace.
- Application-specific values belong in `applications/<plugin-id>/conversion.json` or application-owned tests.
- Generic tools must reject escaping paths, symlink inventory entries, malformed hashes, duplicate paths, and identity mismatches.
- The marketplace and ClawHub remain read-only.
- Production changes follow red-green-refactor and preserve Python 3.11 compatibility.

---

### Task 1: Declare and validate generic provenance profiles

**Files:**
- Modify: `src/obvious_one_plugin_framework/verification.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`
- Modify: `tests/framework/test_verification_config.py`

**Interfaces:**
- Produces: `ProvenanceInventoryRule(root: PurePosixPath, classification: str, include: tuple[str, ...])`.
- Produces: `ProvenanceProfile(source_repository: str, incorporated_branches: tuple[str, ...], inventory_rules: tuple[ProvenanceInventoryRule, ...])`.
- Extends: `ApplicationConfig.provenance: ProvenanceProfile`.

- [ ] **Step 1: Write failing configuration tests**

Add a valid `provenance` object to `_make_application()` and tests proving it loads literal values. Add table-driven failures for absolute/escaping roots, empty include lists, absolute/parent-traversing include patterns, duplicate rules, and missing provenance.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
python -B -m unittest tests.framework.test_verification_config -v
```

Expected: failure because `provenance` is an unknown root field and `ApplicationConfig` has no provenance attribute.

- [ ] **Step 3: Implement minimal profile parsing**

Add `_PROVENANCE_KEYS`, `_INVENTORY_RULE_KEYS`, the two frozen dataclasses, safe POSIX-relative rule parsing, duplicate-rule rejection, and `_load_provenance()`. Require `provenance` in schema v2 and export the public types.

- [ ] **Step 4: Run focused and framework tests**

Run the focused module and `python -B -m unittest discover -s tests/framework`. Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/obvious_one_plugin_framework/verification.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_verification_config.py
git commit -m "feat: declare generic provenance profiles"
```

### Task 2: Implement generic provenance generation and validation

**Files:**
- Create: `src/obvious_one_plugin_framework/provenance.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`
- Rewrite: `scripts/write_extraction_provenance.py`
- Create: `tests/framework/test_provenance.py`

**Interfaces:**
- Produces: `inventory_source(source: Path, rules: Sequence[ProvenanceInventoryRule]) -> tuple[dict[str, str], ...]`.
- Produces: `build_provenance(config: ApplicationConfig, source_repo: Path, marketplace_repo: Path) -> dict[str, object]`.
- Produces: `validate_provenance(payload: Mapping[str, object], config: ApplicationConfig) -> None` raising `ProvenanceError`.
- CLI: `write_extraction_provenance.py --application ID --source PATH --marketplace PATH [--output PATH]`.

- [ ] **Step 1: Write failing behavior tests**

Use temporary Git repositories and literal files to prove rule-driven inventory, stable sorting, SHA-256 values, configured identities, Git commits, marketplace label reuse, safe CLI output, rejection of escaping output, malformed records, duplicate inventory paths, and identity mismatch.

- [ ] **Step 2: Run tests and verify RED**

Run `python -B -m unittest tests.framework.test_provenance -v`. Expected: import failure because the provenance module does not exist.

- [ ] **Step 3: Implement the framework module and CLI**

Implement safe source-root resolution, glob evaluation confined to the supplied source repository, symlink exclusion, deterministic records, schema-v2 construction, and strict validation. Load applications through `discover_applications()` and select through `select_applications()`; default output to `config.source_inventory` and require overrides to remain within the development repository.

- [ ] **Step 4: Run focused and framework tests**

Run the new module and all framework tests. Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/obvious_one_plugin_framework/provenance.py src/obvious_one_plugin_framework/__init__.py scripts/write_extraction_provenance.py tests/framework/test_provenance.py
git commit -m "feat: generalize application provenance"
```

### Task 3: Decouple shared verification gates

**Files:**
- Modify: `scripts/verify_extraction.py`
- Modify: `tests/test_verify_extraction.py`
- Modify: `tests/framework/fixtures/plugin-alpha/conversion.json`
- Modify: `tests/framework/fixtures/plugin-beta/conversion.json`
- Modify: `tests/fixtures/verification/plugin-alpha/conversion.json`
- Modify: `tests/fixtures/verification/plugin-beta/conversion.json`
- Modify: corresponding synthetic `docs/source.json` fixtures created by tests.

**Interfaces:**
- Produces: application gate `provenance`, evaluated with `validate_provenance()` before product tests.
- Changes: `run_shared_gates()` no longer invokes `tests.test_provenance` or application-specific assertions.

- [ ] **Step 1: Write failing isolation tests**

Add a real temporary-repository test that contains only synthetic applications, patches only external build execution, selects `plugin-beta`, and asserts no `plugin-alpha` product marker executes. Assert shared gate commands contain no application ID. Assert malformed provenance fails only the selected owning application.

- [ ] **Step 2: Run tests and verify RED**

Run `python -B -m unittest tests.test_verify_extraction -v`. Expected: failure because provenance is still shared and application provenance is not evaluated.

- [ ] **Step 3: Implement per-application provenance gates**

Remove the top-level provenance test command from shared gates, keep generic application configuration discovery, add `_provenance_gate(config, context)`, honor the existing single-application `--provenance` override, and continue unrelated applications after one provenance failure.

- [ ] **Step 4: Run verifier tests and framework tests**

Expected: PASS with no Cool Bible Tutor dependency in synthetic repositories.

- [ ] **Step 5: Commit**

```powershell
git add scripts/verify_extraction.py tests/test_verify_extraction.py tests/framework/fixtures tests/fixtures/verification
git commit -m "feat: isolate application verification gates"
```

### Task 4: Move Cool Bible Tutor contracts into its workspace

**Files:**
- Modify: `applications/cool-bible-tutor/conversion.json`
- Modify: `docs/provenance/source-extraction.json`
- Create: `applications/cool-bible-tutor/tests/test_conversion_contract.py`
- Delete: `tests/test_provenance.py`
- Rewrite: `tests/test_application_config.py`
- Modify: `tests/test_repository_layout.py`
- Modify: `tests/test_templates.py`

**Interfaces:**
- Cool Bible Tutor owns its exact version, command IDs, local-source ignore rule, provenance identities, branch labels, and template-leakage assertions.
- Top-level configuration tests iterate discovered applications and assert only generic schema/path behavior.

- [ ] **Step 1: Write/move failing ownership tests**

Create the application-owned test module with the existing literal Cool Bible Tutor assertions plus schema-v2 provenance identity checks. Change generic tests to require `applications/`, dynamically discover configurations, and validate template placeholders without named product strings.

- [ ] **Step 2: Run generic and application-focused tests and verify RED**

Expected: failure until configuration and provenance records carry the new generic provenance profile and schema-v2 identity.

- [ ] **Step 3: Migrate Cool Bible Tutor data**

Declare its source repository label, historical branch labels, and two inventory rules in `conversion.json`. Upgrade the checked-in source inventory to schema v2 by adding matching application ID, plugin ID, and marketplace repository without changing recorded commits or hashes.

- [ ] **Step 4: Run generic and application suites**

Run both complete suites. Expected: 0 failures; the two existing documented application skips remain.

- [ ] **Step 5: Commit**

```powershell
git add applications/cool-bible-tutor/conversion.json applications/cool-bible-tutor/tests/test_conversion_contract.py docs/provenance/source-extraction.json tests
git commit -m "test: move reference contracts to application"
```

### Task 5: Neutralize generic documentation and Unicode fixtures

**Files:**
- Modify: `tests/framework/README.md`
- Rename: `tests/framework/fixtures/plugin-alpha/source/assets/經文.txt` to `tests/framework/fixtures/plugin-alpha/source/assets/繁體中文資料.txt`
- Modify: `tests/framework/fixtures/plugin-alpha/distribution.json`
- Modify: `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`
- Modify: `docs/GPT_TO_PLUGIN_USER_GUIDE.md`

**Interfaces:**
- Documentation exposes the application-aware provenance command and shared/per-application gate model.

- [ ] **Step 1: Add a failing documentation contract assertion**

Extend `tests/test_documentation_contract.py` to require the `--application` provenance form and independence wording.

- [ ] **Step 2: Run it and verify RED**

Run `python -B -m unittest tests.test_documentation_contract -v`. Expected: failure because the new command is absent.

- [ ] **Step 3: Update documentation and fixture names**

Document the generic command and replace Bible-specific generic wording and fixture data with domain-neutral Unicode examples.

- [ ] **Step 4: Run documentation and framework asset tests**

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add docs tests/framework tests/test_documentation_contract.py
git commit -m "docs: explain application-independent verification"
```

### Task 6: Complete independence and regression verification

**Files:**
- Modify only if a failing test exposes a defect, following a new red-green cycle.

- [ ] **Step 1: Scan generic paths for case-study leakage**

Run case-insensitive searches for Cool Bible Tutor identities, versions, Bible-domain terms, commands, and asset paths under `src`, `scripts`, `templates`, and generic tests. Only intentionally application-owned paths may match.

- [ ] **Step 2: Run complete suites serially**

```powershell
python -B -m unittest discover -s tests
python -B -m unittest discover -s applications/cool-bible-tutor/tests
```

- [ ] **Step 3: Run complete read-only verifier**

```powershell
python -B .\scripts\verify_extraction.py --all --marketplace D:\GitHub\obvious-one-plugins
```

Expected: all shared and application gates PASS; Codex and OpenClaw artifacts build; OpenClaw builds are byte-identical; marketplace delta matches the approved boundary.

- [ ] **Step 4: Check repository boundaries**

Run `git diff --check`, inspect the report for private absolute paths, and confirm both development and marketplace Git status. Do not publish or mutate the marketplace.

- [ ] **Step 5: Commit any final verified metadata adjustment**

Only if the approved marketplace delta or documentation evidence legitimately changes, commit the minimal audited update with `chore: refresh decoupling verification evidence`.
