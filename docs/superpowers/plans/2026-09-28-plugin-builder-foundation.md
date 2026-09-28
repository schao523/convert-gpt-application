# Plugin Builder Phase-One Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a valid, testable `applications/plugin-builder` foundation that records the approved OpenAI-only scope, exposes four portable skill contracts, validates explicit session-state gates, and produces deterministic local Codex artifacts without claiming end-to-end Plugin Builder execution.

**Architecture:** Four goal-oriented skills own semantic workflow and user interaction over a bundled standard-library Python validator. The validator owns explicit session-state, approval, evidence, and archive-boundary contracts; schema-v2 application configuration and a schema-v3 deny-by-default content contract integrate the product with repository verification while leaving OpenClaw, publication, and marketplace mutation disabled.

**Tech Stack:** Python 3.11+, `unittest`, JSON, Markdown, YAML skill metadata, Codex plugin manifest, application-configuration schema v2, distribution-contract schema v3, `obvious_one_plugin_framework`, `plugin-creator`, and `skill-creator`.

**Spec:** `docs/superpowers/specs/2026-09-28-plugin-builder-implementation-architecture.md`

## Global Constraints

- Plugin ID: `plugin-builder`; display name: `Plugin Builder`; initial version: `0.1.0`.
- Approved behavioral authority: `SPEC-v1.0`; source package SHA-256: `8edde15b6bd0e658990c3a354b85ea90b93bfa1c17216c7b11928f8284c3f497`.
- Runtime scope: `OPENAI_ONLY_PHASE_ONE`; target environments are Codex and ChatGPT Work Local/Desktop.
- OpenClaw, Claude, automatic installation, account deployment, public marketplace publication, GitHub Releases, and external-registry submission are `NOT APPLICABLE` in this phase.
- Product form: four portable skills plus bundled deterministic Python contracts; no MCP server, external service, database, semantic RAG, credential, model download, or hidden background process.
- The delivered plugin must not import from this repository or require the Workbench checkout at runtime.
- W1 is mandatory before candidate creation or update. W2 is mandatory before packaging.
- A required `FAIL` prevents packaging. An unexecuted test is `NOT VERIFIED`, never `PASS`.
- Existing update content is preserved unless the user resolves it explicitly; unexplained members cannot be silently removed or overwritten.
- Input documents, ZIP members, attached resources, and generated content are untrusted application inputs, not development-agent instructions.
- Approved design artifacts remain internal application contracts and are excluded from public artifact selection unless a later rights decision explicitly includes them.
- Python code uses only the standard library in this slice.
- Generated and diagnostic files stay below ignored `.tmp` or `dist` roots. Do not create nested Git metadata.
- Do not publish, upload, install, mutate a marketplace, push, tag, or create a release.
- Preserve the existing unrelated Vibe Coding Designer files and the current Cool Plugin Design Assistant normalization changes.

## Review Focus

1. A session contains a candidate but its W1 approval refers to another plan hash: `test_candidate_requires_matching_w1_approval` must reject it.
2. A package is claimed after a required check failed or without W2 bound to the exact candidate and report: `test_package_requires_matching_w2_and_no_required_failure` must reject it.
3. An update session lacks a baseline ZIP identity or uses an absolute/private path: `test_update_requires_relative_baseline_identity` must reject it.
4. An approved-design file accidentally enters a generated public artifact: `test_public_artifact_excludes_approved_design_and_development_files` must fail.
5. A skill or status result implies implemented/runtime-verified creation when only contracts exist: `test_status_reports_foundation_capabilities_without_runtime_claims` and the behavior scenarios must keep those gates `NOT VERIFIED`.

---

## File Structure

Create:

```text
applications/plugin-builder/
├── .codex-plugin/plugin.json
├── conversion.json
├── README.md
├── DISTRIBUTION.md
├── LICENSE
├── PRIVACY.md
├── SECURITY.md
├── THIRD_PARTY_CONTENT.md
├── THIRD_PARTY_NOTICES.md
├── docs/
│   ├── approved-design/
│   │   ├── Acceptance_and_Test_Scenarios_v1.0.md
│   │   ├── Behavioral_Workflows_and_Modules_v1.1_APPROVED.md
│   │   ├── Decisions_and_Exclusions_v1.0.md
│   │   ├── Design_Statement_v1_APPROVED.md
│   │   ├── Invariants_Capabilities_and_Gates_v1.0.md
│   │   ├── Plugin_Builder_Application_Spec_v1.0_APPROVED.md
│   │   ├── README.md
│   │   ├── Reference_Material_Usage_Map_v1.0.md
│   │   ├── package-manifest.json
│   │   └── workbench-handoff.json
│   ├── application-invariants.md
│   ├── phase-one-scope.json
│   ├── runtime-compatibility.md
│   ├── source-decisions.md
│   └── source-inventory.json
├── openclaw/
│   └── distribution.json
├── scripts/
│   ├── build_marketplace_release.py
│   ├── distribution_audit.py
│   ├── plugin_builder.py
│   └── plugin_builder_core/
│       ├── __init__.py
│       ├── result.py
│       └── session_contract.py
├── skills/
│   ├── guiding-plugin-builder-sessions/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/
│   │       ├── session-workflow.md
│   │       └── state-and-recovery.md
│   ├── planning-plugin-implementations/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/
│   │       ├── input-and-plan-contract.md
│   │       └── requirement-coverage-contract.md
│   ├── building-and-updating-plugins/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/candidate-and-update-contract.md
│   └── verifying-and-packaging-plugins/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       └── references/evidence-and-package-contract.md
└── tests/
    ├── __init__.py
    ├── behavior/
    │   ├── create-and-plan.md
    │   ├── update-protection.md
    │   └── verify-and-package.md
    ├── fixtures/session-valid.json
    ├── coverage-matrix.md
    ├── test_conversion_contract.py
    ├── test_distribution.py
    ├── test_marketplace_release.py
    ├── test_skill_contracts.py
    └── test_tool_contracts.py
```

Modify:

- `tests/test_application_config.py` — require discovery of `plugin-builder`, its Codex-only command targets, and absence of a marketplace mapping.

Local only, ignored, and never committed:

- `applications/plugin-builder/conversion.local.json` — current-machine source ZIP location when provenance regeneration is needed.
- `.tmp/plugin-builder-*` and `dist/plugin-builder-*` — extracted input, builds, and verification evidence.

## Requirement-to-Task Map

| Requirement group | Owning task |
| --- | --- |
| Approved scope, provenance, identity | Task 1 |
| RQ1–RQ7, AC1–AC10, T1–T7, workflow gates, safety invariants | Task 2 |
| M1–M6 semantic responsibilities, P1–P7 interaction, W1/W2 routing | Task 3 |
| Explicit session state, approval binding, evidence classification, recovery gates | Task 4 |
| Deterministic public artifact, internal-design exclusion, no publication | Task 5 |
| Repository discovery and complete static verification | Task 6 |

---

### Task 1: Application identity, approved scope, and provenance boundary

**Files:**
- Modify: `tests/test_application_config.py`
- Create: `applications/plugin-builder/tests/__init__.py`
- Create: `applications/plugin-builder/tests/test_conversion_contract.py`
- Create: `applications/plugin-builder/.codex-plugin/plugin.json`
- Create: `applications/plugin-builder/conversion.json`
- Create: `applications/plugin-builder/docs/phase-one-scope.json`
- Create: `applications/plugin-builder/docs/source-inventory.json`
- Create: `applications/plugin-builder/docs/source-decisions.md`
- Create: `applications/plugin-builder/docs/runtime-compatibility.md`
- Create: `applications/plugin-builder/openclaw/distribution.json`
- Create: `applications/plugin-builder/tests/coverage-matrix.md`
- Create: `applications/plugin-builder/README.md`
- Create: `applications/plugin-builder/DISTRIBUTION.md`
- Create: `applications/plugin-builder/LICENSE`
- Create: `applications/plugin-builder/PRIVACY.md`
- Create: `applications/plugin-builder/SECURITY.md`
- Create: `applications/plugin-builder/THIRD_PARTY_CONTENT.md`
- Create: `applications/plugin-builder/THIRD_PARTY_NOTICES.md`

**Interfaces:**
- Consumes: approved architecture, normalized package hash, repository application schema v2, distribution schema v3.
- Produces: discoverable application ID `plugin-builder`, version `0.1.0`, scope record `OPENAI_ONLY_PHASE_ONE`, and immutable provenance identities used by all later tasks.

- [ ] **Step 1: Write the failing repository discovery test**

Add `test_plugin_builder_phase_one_configuration_is_explicit` to `tests/test_application_config.py`. Assert literal values:

```python
builder = configs["plugin-builder"]
self.assertEqual(builder.version, "0.1.0")
self.assertIsNone(builder.verification.marketplace)
self.assertEqual(
    {command.command_id: command.marketplace_targets for command in builder.verification.commands},
    {"runtime-status": ("codex",), "session-validator": ("codex",)},
)
```

This catches a missing application, accidental OpenClaw target, or premature marketplace registration.

- [ ] **Step 2: Run the repository test and verify RED**

Run:

```powershell
$env:PYTHONPATH = "src"
python -B -m unittest tests.test_application_config.ApplicationConfigTests.test_plugin_builder_phase_one_configuration_is_explicit -v
```

Expected: `FAIL` or `ERROR` because `plugin-builder` is not discoverable.

- [ ] **Step 3: Scaffold the plugin boundary with Plugin Creator**

Run without marketplace, MCP, apps, hooks, or assets:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\plugin-creator\scripts\create_basic_plugin.py" plugin-builder --path applications --with-skills --with-scripts
```

Customize `.codex-plugin/plugin.json` to version `0.1.0`, display name `Plugin Builder`, category `Productivity`, and capability list `Interactive`, `Read`, `Write`. Do not add `mcpServers`, `apps`, or `hooks`.

- [ ] **Step 4: Write the failing product identity test**

In `test_conversion_contract.py`, assert:

- config and manifest identities are exactly `plugin-builder`;
- application schema is `2` and manifest version is `0.1.0`;
- `phase-one-scope.json` contains the exact approved source hash and scope;
- target runtimes are exactly `ChatGPT Work Local/Desktop` and `Codex`;
- excluded runtimes include `OpenClaw` and `Claude`;
- source inventory has no absolute/private paths;
- public/release state is `NOT_PERFORMED` and OpenClaw evidence is `NOT APPLICABLE`.

- [ ] **Step 5: Run the product identity test and verify RED**

Run:

```powershell
$env:PYTHONPATH = "src"
python -B -m unittest discover -s applications/plugin-builder/tests -p "test_conversion_contract.py" -v
```

Expected: `FAIL` because configuration, scope, provenance, and policy files are incomplete.

- [ ] **Step 6: Implement the minimal identity and scope contracts**

Create schema-v2 `conversion.json` with:

- source inventory `docs/source-inventory.json`;
- ignored source location `conversion.local.json`;
- coverage matrix `tests/coverage-matrix.md`;
- content contract `openclaw/distribution.json`;
- commands `status --json` and `validate-session <fixture> --json`, each targeted only to `codex`;
- Codex build command using `scripts/build_marketplace_release.py`;
- no `verification.marketplace` object.

Create schema-v3 `openclaw/distribution.json` as a syntactically valid deny-by-default text contract with both publication surfaces disabled. Use the existing framework schema; do not add an OpenClaw launcher or native manifest.

Record the approved source and normalized package identities in redacted source inventory and scope documents. Root policy documents must state that approved design artifacts are internal, third-party runtime resources remain unresolved per build, and no publication is authorized.

- [ ] **Step 7: Run Task 1 tests and verify GREEN**

Run the two commands from Steps 2 and 5. Expected: `PASS`.

- [ ] **Step 8: Commit Task 1**

```powershell
git add tests/test_application_config.py applications/plugin-builder
git commit -m "feat: scaffold Plugin Builder phase-one application"
```

---

### Task 2: Approved design snapshot, invariant register, and complete coverage matrix

**Files:**
- Create: `applications/plugin-builder/docs/approved-design/*` listed in File Structure
- Create: `applications/plugin-builder/docs/application-invariants.md`
- Modify: `applications/plugin-builder/docs/source-inventory.json`
- Modify: `applications/plugin-builder/tests/coverage-matrix.md`
- Modify: `applications/plugin-builder/tests/test_conversion_contract.py`

**Interfaces:**
- Consumes: normalized approved package, source package hash, scope record from Task 1.
- Produces: immutable design authority and traceability rows for `RQ1`–`RQ7`, `AC1`–`AC10`, `T1`–`T7`, W1/W2, archive safety, update preservation, and evidence honesty.

- [ ] **Step 1: Write the failing design-integrity and coverage tests**

Add tests that independently hash each approved-design file and compare it with `package-manifest.json`; verify the canonical handoff gate is `APPROVED WITH NONBLOCKING DECISIONS`; verify the source package hash literal; and verify the coverage matrix contains each literal ID `RQ1`–`RQ7`, `AC1`–`AC10`, and `T1`–`T7` exactly once in the ID column.

Also assert every row has an owner, evidence target, and one of `EXPECTED`, `STATICALLY VERIFIED`, `RUNTIME VERIFIED`, or `NOT VERIFIED`. Assert OpenClaw and Claude are recorded separately as `NOT APPLICABLE`, not as passing tests.

- [ ] **Step 2: Run the design-integrity tests and verify RED**

Run:

```powershell
$env:PYTHONPATH = "src"
python -B -m unittest discover -s applications/plugin-builder/tests -p "test_conversion_contract.py" -v
```

Expected: `FAIL` because the approved snapshot and complete matrix do not exist.

- [ ] **Step 3: Materialize the approved design snapshot without reinterpretation**

Copy the ten members of the final normalized archive into `docs/approved-design` byte-for-byte. Preserve `package-manifest.json` and `workbench-handoff.json`; do not restore the ambiguous legacy `handoff_manifest.json`. Verify each copied byte stream against the normalized package manifest before staging it.

Update source inventory with source-relative filenames, SHA-256 values, and classification `approved-design-internal`. Do not record the Desktop or `.tmp` path.

- [ ] **Step 4: Write the invariant register and coverage matrix**

Assign stable `INV-PB-001` identifiers covering at least:

- approved specification authority;
- W1 and W2 ordering;
- requirement traceability;
- honest evidence states;
- required-failure packaging block;
- update preservation and unresolved-member wait;
- behavioral-change return to design approval;
- archive confinement and duplicate/case-fold protection;
- relative persisted paths and minimal private-data retention;
- deterministic manifests and ZIPs;
- manual-upload boundary;
- OpenAI-only runtime scope.

Map each approved requirement/test to one skill or deterministic contract and a planned observable test. Mark only file/hash/schema checks actually exercised by Task 2 as `STATICALLY VERIFIED`; keep behavior and runtime claims `NOT VERIFIED`.

- [ ] **Step 5: Run Task 2 tests and verify GREEN**

Run the command from Step 2. Expected: `PASS`.

- [ ] **Step 6: Commit Task 2**

```powershell
git add applications/plugin-builder/docs applications/plugin-builder/tests/coverage-matrix.md applications/plugin-builder/tests/test_conversion_contract.py
git commit -m "docs: register Plugin Builder approved requirements"
```

---

### Task 3: Four portable skills and progressive-disclosure references

**Files:**
- Create: all four `skills/*` trees listed in File Structure
- Create: `applications/plugin-builder/tests/test_skill_contracts.py`
- Create: three behavior scenario files under `tests/behavior`
- Modify: `applications/plugin-builder/tests/coverage-matrix.md`

**Interfaces:**
- Consumes: invariant and coverage IDs from Task 2.
- Produces: discoverable skills named `guiding-plugin-builder-sessions`, `planning-plugin-implementations`, `building-and-updating-plugins`, and `verifying-and-packaging-plugins`; their references define semantic responsibilities while deterministic mutations stay behind Task 4 contracts.

- [ ] **Step 1: Write failing observable skill-contract tests**

Test parsed frontmatter, direct Markdown links, and routing outcomes rather than exact prose. The tests must prove:

- the session skill routes create/update/pause/resume/cancel and cannot route past W1/W2;
- planning requires an approved spec, produces requirement coverage, and treats behavior changes as requiring a new approval;
- building requires W1, distinguishes create/update, preserves unexplained update content, and produces a candidate rather than a final ZIP;
- verification distinguishes four evidence states, blocks required failures, requires W2, and keeps upload manual;
- every referenced file exists and no skill claims OpenClaw support, deployment, publication, or runtime verification.

Name the concrete mutations each test catches in a short comment immediately above the test.

- [ ] **Step 2: Run skill-contract tests and verify RED**

Run:

```powershell
$env:PYTHONPATH = "src"
python -B -m unittest discover -s applications/plugin-builder/tests -p "test_skill_contracts.py" -v
```

Expected: `FAIL` because the four skills do not exist.

- [ ] **Step 3: Initialize the four skill directories with Skill Creator**

For each skill name, run:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\init_skill.py" <skill-name> --path applications/plugin-builder/skills --resources references
```

Do not use `--examples`. Keep implicit discovery enabled.

- [ ] **Step 4: Implement concise skill entrypoints and focused references**

Keep routing, non-negotiable gates, interaction ownership, and failure transitions in each `SKILL.md`. Put state tables, schemas, update rules, evidence definitions, and packaging details in the reference files named in File Structure. Every reference must be directly linked at the point where it is required.

Create behavior scenarios for T1/T3, T4, and T5/T6 pressure. Label them planned/static inputs; do not claim agent execution.

- [ ] **Step 5: Validate each skill and run tests GREEN**

Run `quick_validate.py` once per skill, then rerun Step 2. Expected: every validator and test passes with no scaffold placeholders.

- [ ] **Step 6: Update coverage evidence and commit Task 3**

Mark only structural discovery/reference closure as `STATICALLY VERIFIED`. Behavior scenarios remain `EXPECTED` or `NOT VERIFIED` until executed by the target runtime.

```powershell
git add applications/plugin-builder/skills applications/plugin-builder/tests
git commit -m "feat: add Plugin Builder portable skill contracts"
```

---

### Task 4: Explicit session-state validator and stable product CLI

**Files:**
- Create: `applications/plugin-builder/scripts/plugin_builder_core/__init__.py`
- Create: `applications/plugin-builder/scripts/plugin_builder_core/result.py`
- Create: `applications/plugin-builder/scripts/plugin_builder_core/session_contract.py`
- Create: `applications/plugin-builder/scripts/plugin_builder.py`
- Create: `applications/plugin-builder/tests/fixtures/session-valid.json`
- Create: `applications/plugin-builder/tests/test_tool_contracts.py`
- Modify: `applications/plugin-builder/tests/coverage-matrix.md`

**Interfaces:**
- Consumes: W1/W2 and evidence invariants from Tasks 2–3.
- Produces:
  - `validate_session(payload: object) -> list[str]`
  - `session_gate_state(payload: object) -> str`
  - `operation_document(operation: str, status: str, errors: list[str], **data: object) -> dict[str, object]`
  - CLI commands `status --json` and `validate-session <session.json> --json`.

- [ ] **Step 1: Write failing tests for the public validator API**

Use hand-authored JSON literals. Cover:

- a valid W1-waiting create session;
- update without relative baseline identity;
- candidate without W1 or with mismatched plan hash;
- package without W2, mismatched candidate/report hashes, or any required `FAIL`;
- `NOT VERIFIED` preserved separately from `PASS`;
- absolute paths, traversal paths, duplicate requirement IDs, unsupported evidence states, and malformed approval objects;
- deterministic sorted errors.

- [ ] **Step 2: Run API tests and verify RED**

Run:

```powershell
$env:PYTHONPATH = "src"
python -B -m unittest discover -s applications/plugin-builder/tests -p "test_tool_contracts.py" -v
```

Expected: `FAIL` because `plugin_builder_core` and the launcher do not exist.

- [ ] **Step 3: Implement the minimal result and session contracts**

Use exact allowed values:

- operations: `create`, `update`;
- stages: `S0`, `S1`, `S2`, `W1`, `S3`, `S4`, `W2`, `S5`, `F1`, `F2`, `F3`, `H1`, `E1`, `E2`, `E3`;
- evidence: `PASS`, `FAIL`, `NOT VERIFIED`, `NOT APPLICABLE`;
- SHA-256: 64 lowercase hexadecimal characters;
- persisted paths: non-empty relative POSIX paths with no `.` or `..` segment and no drive prefix.

Bind W1 to `plan_sha256`. Bind W2 to both `candidate_sha256` and `verification_sha256`. A package requires matching W1/W2, no required `FAIL`, stage `S5` or `E1`, and its own SHA-256 identity. Return all deterministic errors rather than stopping at the first.

- [ ] **Step 4: Write failing CLI integration tests**

Run the real launcher in subprocesses. Assert one ASCII-safe JSON document, exit `0` for valid/status, exit `3` for invalid session, exact operation names, and status capabilities:

```json
{
  "session_contract": "STATICALLY VERIFIED",
  "candidate_build": "NOT VERIFIED",
  "package_build": "NOT VERIFIED",
  "codex_execution": "NOT VERIFIED",
  "chatgpt_work_execution": "NOT VERIFIED",
  "openclaw_execution": "NOT APPLICABLE"
}
```

- [ ] **Step 5: Run CLI tests and verify RED, then implement the launcher**

Add `status` and `validate-session`; do not add inspect/build/verify/package commands in this slice. Rerun the CLI tests and expect `PASS`.

- [ ] **Step 6: Run all Task 4 tests and commit**

```powershell
$env:PYTHONPATH = "src"
python -B -m unittest discover -s applications/plugin-builder/tests -p "test_tool_contracts.py" -v
git add applications/plugin-builder/scripts applications/plugin-builder/tests
git commit -m "feat: validate Plugin Builder session gates"
```

---

### Task 5: Deny-by-default distribution and deterministic Codex artifact

**Files:**
- Create: `applications/plugin-builder/scripts/distribution_audit.py`
- Create: `applications/plugin-builder/scripts/build_marketplace_release.py`
- Create: `applications/plugin-builder/tests/test_distribution.py`
- Create: `applications/plugin-builder/tests/test_marketplace_release.py`
- Modify: `applications/plugin-builder/openclaw/distribution.json`
- Modify: `applications/plugin-builder/docs/source-decisions.md`
- Modify: `applications/plugin-builder/README.md`
- Modify: `applications/plugin-builder/DISTRIBUTION.md`

**Interfaces:**
- Consumes: public files from Tasks 1, 3, and 4.
- Produces: `audit_public_source(root: Path) -> list[str]`, `audit_tree(root: Path) -> list[str]`, package-builder hook `audit_distribution(stage: Path, contract: object) -> list[str]`, and `build_release(source: Path, destination: Path, version: str) -> ReleaseReport`.

- [ ] **Step 1: Write failing distribution-boundary tests**

Assert:

- schema v3, `rag: null`, text-only rules, and both publication surfaces disabled;
- selected public content includes manifest, root policy files, skills, scripts, and only explicitly approved public docs;
- selected content excludes `conversion.json`, tests, `docs/approved-design`, source inventory, scope decision records not intended for distribution, caches, private paths, binary/source attachments, and diagnostics;
- audit blocks secrets, links/reparse points, unsafe suffixes, broken relative Markdown links, and scaffold markers;
- two package builds have the same content identity and no remote assets.

- [ ] **Step 2: Run distribution tests and verify RED**

Run:

```powershell
$env:PYTHONPATH = "src"
python -B -m unittest discover -s applications/plugin-builder/tests -p "test_distribution.py" -v
```

Expected: `FAIL` because audit and final content rules are missing.

- [ ] **Step 3: Implement the minimal audit and final content contract**

Adapt only generic, non-domain-specific patterns from Cool Plugin Design Assistant. Do not inherit its plugin ID, marketplace decisions, or documentation selection. Use explicit public-doc paths rather than a broad `docs` prefix so approved design inputs cannot enter the artifact.

- [ ] **Step 4: Write failing deterministic Codex release tests**

Test a real build into isolated temporary roots. Assert exact allowlisted paths, plugin identity/version enforcement, refusal to replace a nonempty unmarked destination, previous-artifact preservation on failure, deterministic manifests, and absence of approved-design files.

- [ ] **Step 5: Run release tests RED, implement builder, and verify GREEN**

Run:

```powershell
$env:PYTHONPATH = "src"
python -B -m unittest discover -s applications/plugin-builder/tests -p "test_marketplace_release.py" -v
```

Implement `build_release` transactionally with a private staging directory and marker-protected destination. The builder creates a local artifact only; it never edits marketplace configuration or publishes.

Rerun both Task 5 test files. Expected: `PASS`.

- [ ] **Step 6: Validate a generated framework package and commit**

Run `validate-contract`, `build-package`, and `verify` against isolated `.tmp/plugin-builder-foundation` outputs. Confirm `result-schema-v1` success and exact artifact verification.

```powershell
git add applications/plugin-builder/openclaw applications/plugin-builder/scripts applications/plugin-builder/tests applications/plugin-builder/docs/source-decisions.md applications/plugin-builder/README.md applications/plugin-builder/DISTRIBUTION.md
git commit -m "feat: package Plugin Builder foundation deterministically"
```

---

### Task 6: Repository registration and complete foundation verification

**Files:**
- Modify: `tests/test_application_config.py` only if Task 1's assertions need final command-path adjustment
- Modify: `applications/plugin-builder/docs/runtime-compatibility.md`
- Modify: `applications/plugin-builder/tests/coverage-matrix.md`
- Modify: `applications/plugin-builder/README.md`

**Interfaces:**
- Consumes: complete application foundation from Tasks 1–5.
- Produces: repository-discovered configuration, validated source and generated artifact, and an evidence report that does not overstate behavior or runtime readiness.

- [ ] **Step 1: Run product and repository discovery suites**

```powershell
$env:PYTHONPATH = "src"
python -B -m unittest discover -s applications/plugin-builder/tests -v
python -B -m unittest tests.test_application_config -v
```

Expected: all tests pass. Any failure gets a focused failing regression test before its fix.

- [ ] **Step 2: Run creator validators**

```powershell
python "$env:USERPROFILE\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py" applications/plugin-builder
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" applications/plugin-builder/skills/guiding-plugin-builder-sessions
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" applications/plugin-builder/skills/planning-plugin-implementations
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" applications/plugin-builder/skills/building-and-updating-plugins
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" applications/plugin-builder/skills/verifying-and-packaging-plugins
```

Expected: every validator passes with no placeholders.

- [ ] **Step 3: Run framework and configured application verification**

```powershell
$env:PYTHONPATH = "src"
python -B -m unittest discover -s tests/framework -v
python -B scripts/verify_extraction.py --application plugin-builder
```

Expected: framework suite passes; configured verification reports local structural/package gates truthfully. Codex installed execution and ChatGPT Work execution remain `NOT VERIFIED`; OpenClaw remains `NOT APPLICABLE`.

- [ ] **Step 4: Inspect the generated artifact, not only development source**

Confirm the artifact has exactly the manifest-listed members, validates as a plugin, excludes internal approved-design files and test/configuration files, and yields the same content hash on a second build.

- [ ] **Step 5: Update evidence documents without upgrading unsupported gates**

Record commands and observed outcomes in `runtime-compatibility.md`. Update only the coverage rows directly exercised. Use:

- `STATICALLY VERIFIED` for validated structure/contracts;
- `NOT VERIFIED` for T1–T7 agent behavior, Codex installed execution, ChatGPT Work execution, create/update E2E, and clean-desktop operation;
- `NOT APPLICABLE` for OpenClaw and Claude in phase one.

Do not report `READY`, `PORTABLE`, or conversion completion.

- [ ] **Step 6: Run final hygiene checks**

```powershell
git diff --check
git status --short --branch
```

Confirm no `.tmp`, `dist`, cache, local source path, credential, approved source ZIP, or unrelated user file is staged.

- [ ] **Step 7: Commit Task 6**

```powershell
git add applications/plugin-builder tests/test_application_config.py
git commit -m "test: verify Plugin Builder foundation contracts"
```

## Completion Report for This Plan

Report:

- approved source package and normalized handoff hashes;
- application identity, preserved phase-one scope, and excluded runtimes;
- invariant and requirement coverage counts;
- four portable skill packages and their reference closure;
- deterministic session-validator interface and exact unimplemented commands;
- product, framework, creator-validator, package, and generated-artifact results;
- Codex and ChatGPT Work runtime gates as `NOT VERIFIED` unless directly executed;
- OpenClaw and Claude as `NOT APPLICABLE` for phase one;
- generated artifact paths and hashes;
- Git commits/status and confirmation that marketplace/publication state is `NOT_PERFORMED`.
