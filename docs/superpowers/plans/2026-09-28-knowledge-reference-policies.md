# Knowledge Reference Policies Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a small, deterministic framework capability that validates professional and general knowledge-reference conventions without changing existing applications until their decision owners explicitly adopt the policy.

**Architecture:** A focused `knowledge_policy` module discovers skill-local references, strictly parses the single optional general-knowledge topic guide, validates link and path closure, and reports static and traceability evidence without claiming runtime use. A non-interactive CLI command exposes the validator through the existing `result-schema-v1` boundary. Synthetic framework fixtures prove Codex-shaped and OpenClaw-package behavior; application-owned behavioral and installed-runtime verification remain later per-product adoption work.

**Tech Stack:** Python 3.11+, standard-library `dataclasses`, `json`, `pathlib`, `re`, and `unittest`; existing framework result, package, content-policy, and verification APIs.

**Spec:** `docs/superpowers/specs/2026-09-28-knowledge-reference-policies-design.md`

## Global Constraints

- Keep professional knowledge under its owning skill's `references/` directory.
- Keep general knowledge under one application-specific consultation skill's `references/` directory with one `knowledge-index.json`.
- Do not add a plugin-root `knowledge/` directory, a distribution-contract field, or a new application-configuration schema.
- Treat paths as POSIX relative paths, reject absolute, escaping, backslash, symlink, collision, and case-fold alias forms, and never follow a reference outside its owning directory.
- Validate static structure and deterministic discovery separately from runtime consultation and behavioral application.
- Static success may report only `STATICALLY VERIFIED`; Codex execution, OpenClaw execution, and behavioral application remain `NOT VERIFIED` unless supplied by application-owned runtime evidence.
- Reuse the application's existing coverage matrix for traceability; do not create a second behavior-evidence manifest.
- Preserve exact retrieval and optional RAG as separate capabilities.
- Keep the command non-interactive and emit exactly one ASCII-safe `result-schema-v1` document.
- Existing applications remain unchanged and continue to pass until their decision owners approve migration and add the new command to their verification profiles.
- Do not modify the two pre-existing untracked Vibe hosted-experiment files.

## Review Focus

- A professional reference must not pass when missing, escaping, symlinked, or not directly linked from its owning `SKILL.md`; Tasks 1 and 2 own these tests.
- A general index must not pass with duplicate indexes, unknown or missing fields, unsafe aliases, incomplete topic locators, invalid page ranges, unindexed files, or missing indexed files; Tasks 1 and 2 own these tests.
- Coverage-matrix traceability must remain distinct from behavioral proof, and omitted coverage must not be mislabeled as verified; Tasks 2 and 3 own these tests.
- Validating generated artifacts must prove reference-byte preservation without claiming that either runtime consulted the material; Task 4 owns these tests.
- Legacy applications must not acquire a new gate merely because the generic framework gains this capability; Tasks 3, 5, and 6 own this compatibility check.

---

### Task 1: Strict topic-guide model and parser

**Files:**
- Create: `src/obvious_one_plugin_framework/knowledge_policy.py`
- Create: `tests/framework/test_knowledge_policy.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`

**Interfaces:**
- Produces: `KnowledgePolicyError`, `KnowledgePageRange`, `KnowledgeTopic`, `GeneralKnowledgeFile`, `ProfessionalKnowledgeFile`, `KnowledgePolicy`, and `KnowledgePolicyEvidence`.
- Produces: `discover_knowledge_policy(plugin_root: Path) -> KnowledgePolicy`.
- `KnowledgePolicyError` exposes stable `code`, `detail`, and normalized `paths` fields so the CLI never parses exception prose.
- `KnowledgePolicyEvidence` keeps `package_structure`, `deterministic_discovery`, `coverage_traceability`, `behavior`, `codex_execution`, and `openclaw_execution` as separate states.

- [ ] **Step 1: Write failing strict-parser tests**

Add table-driven tests that create isolated plugin roots and assert:

```python
policy = discover_knowledge_policy(plugin_root)
self.assertEqual(policy.consultation_skill, "consulting-product-knowledge")
self.assertEqual(policy.general_files[0].topics[0].keywords, ("event-driven",))
```

Cover valid professional-only, valid general, and zero-knowledge plugins, plus
malformed UTF-8/JSON, unknown keys, unsupported `schema_version`, empty
purpose/topics/name/keywords, non-array locator fields, invalid page-range
types and bounds, duplicate/case-fold paths, absolute paths, `..`, `.`,
backslashes, and more than one index.

- [ ] **Step 2: Run the focused test and verify the missing-module failure**

Run:

```powershell
python -B -m unittest tests.framework.test_knowledge_policy -v
```

Expected: `FAIL` because `obvious_one_plugin_framework.knowledge_policy` does
not exist.

- [ ] **Step 3: Implement the immutable model and strict parser**

Implement frozen dataclasses and exact-key validation. Parse only
`skills/*/references/knowledge-index.json`; normalize stored paths to POSIX
form while retaining deterministic sorted order. Reject multiple indexes
before parsing any one as authoritative. Keep all error conditions stable and
machine-readable, including the spec's published failure codes.

- [ ] **Step 4: Export the public model and rerun the focused test**

Update `__init__.py` with public, non-underscore imports and `__all__` entries.
Run the Task 1 test command and expect `PASS`.

- [ ] **Step 5: Commit the parser slice**

```powershell
git add src/obvious_one_plugin_framework/knowledge_policy.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_knowledge_policy.py
git commit -m "feat: parse knowledge reference policies"
```

---

### Task 2: Structural closure and coverage traceability

**Files:**
- Modify: `src/obvious_one_plugin_framework/knowledge_policy.py`
- Modify: `tests/framework/test_knowledge_policy.py`

**Interfaces:**
- Produces: `validate_knowledge_policy(plugin_root: Path, coverage_matrix: Path | None = None, require_coverage: bool = False) -> KnowledgePolicyEvidence`.
- Direct-link recognition supports ordinary Markdown inline links and reference definitions; a bare filename or code span is not a direct link.
- Coverage checking requires each normalized knowledge path to appear in the existing matrix, but reports only traceability, never behavior execution.

- [ ] **Step 1: Write failing professional-reference closure tests**

Cover missing and unlinked professional files, nested reference paths, broken
local Markdown links, paths escaping the skill, symlinks, case-fold aliases,
and valid inline/reference-style direct links. Assert the stable codes
`professional_reference_unlinked` and `professional_reference_missing` where
specified.

- [ ] **Step 2: Write failing general-reference closure tests**

Cover an indexed path that is absent, a non-index sibling file omitted from the
index, a consultation `SKILL.md` that does not link the index, nested general
files, and a forbidden plugin-root `knowledge/` directory. Assert the spec's
published stable codes.

- [ ] **Step 3: Write failing coverage-traceability tests**

Verify all three cases:

```python
self.assertEqual(validate_knowledge_policy(root).coverage_traceability, "NOT VERIFIED")
self.assertEqual(validate_knowledge_policy(root, matrix).coverage_traceability, "STATICALLY VERIFIED")
with self.assertRaisesRegex(KnowledgePolicyError, "knowledge_behavior_evidence_missing"):
    validate_knowledge_policy(root, matrix, require_coverage=True)
```

The matrix test uses exact normalized file paths and does not infer behavioral
quality from prose, filenames, or scenario labels.

- [ ] **Step 4: Run the focused test and verify the new failures**

Run the Task 1 command. Expected: new closure and traceability cases fail.

- [ ] **Step 5: Implement confined-file, link, and matrix validation**

Walk reference directories deterministically, use `lstat`/resolved-boundary
checks, validate every local Markdown link, compare the general index with all
non-index regular files recursively, and reject a plugin-root `knowledge/`
directory. Return counts and evidence states; leave behavior and both runtime
execution states `NOT VERIFIED`.

- [ ] **Step 6: Rerun the focused test and commit**

```powershell
python -B -m unittest tests.framework.test_knowledge_policy -v
git add src/obvious_one_plugin_framework/knowledge_policy.py tests/framework/test_knowledge_policy.py
git commit -m "feat: validate knowledge reference closure"
```

Expected: `PASS`.

---

### Task 3: Non-interactive framework CLI

**Files:**
- Modify: `src/obvious_one_plugin_framework/cli.py`
- Modify: `tests/framework/test_cli.py`
- Modify: `tests/framework/README.md`

**Interfaces:**
- Adds: `validate-knowledge --plugin-root PATH [--coverage-matrix PATH] [--require-coverage]`.
- Success code: `knowledge_policy_validated`.
- Failure results preserve the validator's stable condition code and use the framework's established failure exit code.
- Evidence includes normalized counts, consultation-skill identity, and separate static/behavior/runtime states.

- [ ] **Step 1: Write failing CLI contract tests**

Test one valid professional/general fixture, invalid topic metadata, forbidden
root `knowledge/`, required coverage missing, non-ASCII paths, and paths outside
the supplied plugin boundary. Parse stdout and assert exactly one
`result-schema-v1` object with ASCII-safe serialization.

- [ ] **Step 2: Run the CLI tests and verify the missing-command failure**

```powershell
python -B -m unittest tests.framework.test_cli -v
```

Expected: `FAIL` because `validate-knowledge` is not registered.

- [ ] **Step 3: Implement command registration and result mapping**

Resolve optional matrix paths relative to the caller's current directory, keep
plugin-root confinement inside the validator, and map `KnowledgePolicyError`
directly into one deterministic failure result. Do not update application
configuration or automatically insert the command into any existing product.

- [ ] **Step 4: Document the framework-test ownership boundary**

In `tests/framework/README.md`, state that these tests prove parsing,
structure, deterministic discovery, and result contracts only. Product suites
own distinctive-content behavior, installed Codex/OpenClaw execution, and
cross-runtime equivalence.

- [ ] **Step 5: Rerun tests and commit**

```powershell
python -B -m unittest tests.framework.test_cli -v
python -B -m unittest tests.framework.test_knowledge_policy -v
git add src/obvious_one_plugin_framework/cli.py tests/framework/test_cli.py tests/framework/README.md
git commit -m "feat: expose knowledge policy validation"
```

Expected: both suites `PASS`.

---

### Task 4: Artifact and deterministic-package regression fixture

**Files:**
- Create: `tests/framework/fixtures/knowledge-policy-plugin/.codex-plugin/plugin.json`
- Create: `tests/framework/fixtures/knowledge-policy-plugin/README.md`
- Create: `tests/framework/fixtures/knowledge-policy-plugin/docs/source-decisions.md`
- Create: `tests/framework/fixtures/knowledge-policy-plugin/skills/designing-systems/SKILL.md`
- Create: `tests/framework/fixtures/knowledge-policy-plugin/skills/designing-systems/references/design-rules.md`
- Create: `tests/framework/fixtures/knowledge-policy-plugin/skills/consulting-system-knowledge/SKILL.md`
- Create: `tests/framework/fixtures/knowledge-policy-plugin/skills/consulting-system-knowledge/references/knowledge-index.json`
- Create: `tests/framework/fixtures/knowledge-policy-plugin/skills/consulting-system-knowledge/references/architecture-guide.md`
- Create: `tests/framework/fixtures/knowledge-policy-plugin/tests/coverage-matrix.md`
- Create: `tests/framework/fixtures/knowledge-policy-plugin/openclaw/distribution.json`
- Create: `tests/framework/test_knowledge_policy_artifacts.py`

**Interfaces:**
- Reuses: schema-v3 `load_contract`, `build_package`, `verify_bundle`, and `validate_knowledge_policy`.
- Produces no new runtime or distribution schema.

- [ ] **Step 1: Add the minimal rights-approved synthetic plugin fixture**

Keep the fixture domain-neutral. Its professional reference contains one
distinctive rule; its general file has indexed purpose, topics, chapters,
sections, keywords, and page ranges. Its distribution allowlist includes only
the fixture's required portable files and OpenClaw manifest data.

- [ ] **Step 2: Write failing artifact-preservation tests**

Test that the source/Codex-shaped plugin root validates, two OpenClaw builds
are byte-identical, the verified OpenClaw bundle contains both reference files
and the index with the expected hashes, and validating the unpacked bundle
reports static evidence while leaving behavior/Codex/OpenClaw execution
`NOT VERIFIED`.

- [ ] **Step 3: Run the artifact test and verify the fixture/integration failures**

```powershell
python -B -m unittest tests.framework.test_knowledge_policy_artifacts -v
```

Expected: `FAIL` until the fixture and any required artifact-root normalization
are complete.

- [ ] **Step 4: Make the smallest integration corrections**

Adjust only public path handling needed to validate both a Codex plugin root
and an unpacked lightweight OpenClaw bundle. Do not add runtime-specific skill
forks or change schema v3.

- [ ] **Step 5: Run focused framework suites and commit**

```powershell
python -B -m unittest tests.framework.test_knowledge_policy_artifacts -v
python -B -m unittest tests.framework.test_package_builder -v
python -B -m unittest tests.framework.test_package_verifier -v
git add tests/framework/fixtures/knowledge-policy-plugin tests/framework/test_knowledge_policy_artifacts.py src/obvious_one_plugin_framework/knowledge_policy.py
git commit -m "test: verify packaged knowledge references"
```

Expected: all focused suites `PASS` and generated data remains in isolated
temporary roots.

---

### Task 5: Operator, authoring, and template documentation

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `docs/GPT_TO_PLUGIN_USER_GUIDE.md`
- Modify: `docs/PLUGIN_SKILLS_TECHNICAL_REFERENCE.md`
- Modify: `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`
- Modify: `templates/skill/README.md`
- Modify: `tests/test_documentation_contract.py`
- Modify: `tests/test_templates.py`

- [ ] **Step 1: Write failing documentation-contract tests**

Require the command reference to name the exact CLI syntax and evidence limit;
the technical reference to define professional/general layouts, direct links,
topic-guide fields, one response owner, and no root `knowledge/`; the user
guide to identify decision-owner classification and migration approval; and the
skill template to route authors without creating placeholder indexes.

- [ ] **Step 2: Run documentation tests and verify failures**

```powershell
python -B -m unittest tests.test_documentation_contract tests.test_templates -v
```

Expected: `FAIL` for missing knowledge-policy guidance.

- [ ] **Step 3: Update the routed documentation**

Keep `AGENTS.md` concise: add only the non-negotiable placement, adoption, and
evidence rules, and route details to the technical reference. Add the new CLI
to the command reference as the operational authority. Explain in the user
guide that application owners must approve existing-reference classification
and supply behavior scenarios before adding the gate. Update the skill template
README without generating unused `references/` directories or indexes.

- [ ] **Step 4: Rerun documentation tests and commit**

```powershell
python -B -m unittest tests.test_documentation_contract tests.test_templates -v
git add AGENTS.md README.md docs/GPT_TO_PLUGIN_USER_GUIDE.md docs/PLUGIN_SKILLS_TECHNICAL_REFERENCE.md docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md templates/skill/README.md tests/test_documentation_contract.py tests/test_templates.py
git commit -m "docs: define knowledge reference workflow"
```

Expected: both suites `PASS`.

---

### Task 6: Full verification and application-adoption boundary audit

**Files:**
- Modify only if a failing generic regression requires a scoped correction to files already listed above.
- Generate diagnostics only below ignored `.tmp/knowledge-policy/` or `dist/knowledge-policy/`.

- [ ] **Step 1: Run generic framework and repository contract suites**

```powershell
python -B -m unittest discover -s .\tests\framework -v
python -B -m unittest discover -s .\tests -v
```

Expected: `PASS` with no tracked-file mutation.

- [ ] **Step 2: Run unchanged product suites as compatibility checks**

```powershell
python -B -m unittest discover -s .\applications\cool-bible-tutor\tests -v
python -B -m unittest discover -s .\applications\vibe-coding-designer\tests -v
python -B -m unittest discover -s .\applications\cool-plugin-design-assistant\tests -v
```

Expected: existing products retain their previous gates because none has yet
adopted the new policy.

- [ ] **Step 3: Exercise the CLI against the synthetic fixture**

```powershell
python -B -m obvious_one_plugin_framework.cli validate-knowledge --plugin-root .\tests\framework\fixtures\knowledge-policy-plugin --coverage-matrix .\tests\framework\fixtures\knowledge-policy-plugin\tests\coverage-matrix.md --require-coverage
```

Expected: one `PASS` result with package structure, deterministic discovery,
and coverage traceability `STATICALLY VERIFIED`; behavior and both runtime
execution states remain `NOT VERIFIED`.

- [ ] **Step 4: Verify repository hygiene and review the exact delta**

```powershell
git diff --check
git status --short
git diff --stat
git diff --name-only <implementation-base>..HEAD
```

Confirm the two pre-existing untracked hosted-experiment files remain unmodified
and uncommitted, no application `conversion.json` changed, no root
`knowledge/` exists, and no generated artifacts escaped ignored output roots.

- [ ] **Step 5: Perform a final self-review against the approved spec**

Review each KRP requirement and acceptance criterion. Record framework evidence
as `STATICALLY VERIFIED` or `NOT VERIFIED` precisely. Do not report the feature
as product runtime validation, cross-runtime behavioral equivalence, or plugin
`READY` evidence.

- [ ] **Step 6: Report the next separately approved product-adoption work**

For each product selected later, require a new product-specific plan that:

1. classifies existing references with decision-owner approval;
2. creates a general consultation skill only when general knowledge exists;
3. updates its existing coverage matrix and application-owned behavior tests;
4. adds `validate-knowledge --require-coverage` to its verification profile;
5. validates generated/installed Codex and OpenClaw artifacts; and
6. compares cross-runtime behavior before changing readiness evidence.

Do not include Vibe Coding Designer, Cool Bible Tutor, or another product in
this framework implementation merely to make the generic tests pass.
