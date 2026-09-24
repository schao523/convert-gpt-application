# Cool Plugin Design Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and validate the portable `cool-plugin-design-assistant` 1.0.0 skills-only plugin for Codex and OpenClaw from the approved conversion specification.

**Architecture:** One application-owned workspace contains seven portable Skills, progressively disclosed references, deterministic JSON/Markdown validators, product tests, and schema-v3 distribution contracts. Codex and OpenClaw consume the same `skills/` tree; runtime-specific packaging remains at the manifest and generated-bundle boundary. The plugin produces behavioral design and Workbench handoff artifacts but never chooses the Skill Architecture of applications designed by its users.

**Tech Stack:** Python 3.11+, `unittest`, JSON, Markdown, YAML UI metadata, Codex plugin manifest, schema-v2 application configuration, schema-v3 distribution contract, `obvious_one_plugin_framework`, `skill-creator`, and `plugin-creator`.

**Spec:** `docs/superpowers/specs/2026-09-24-cool-plugin-design-assistant-conversion-design.md`

## Global Constraints

- Plugin ID: `cool-plugin-design-assistant`; display name: `Cool Plugin Design Assistant`; version: `1.0.0`.
- Default language: Traditional Chinese, with bilingual terminology when useful.
- Target runtimes: Codex and OpenClaw using one portable Skill implementation.
- Product form: skills-only plugin with deterministic local validation tools.
- Python floor: 3.11.
- External services, MCP servers, semantic RAG, model downloads, databases, and remote assets: not required for version 1.0.
- ClawHub publication: disabled and `NOT APPLICABLE`; GitHub marketplace publication remains separately authorized.
- License: MIT for plugin code and approved normalized derivatives.
- Raw DOCX, PDF, PNG, `Old` content, Resource Index, private paths, extraction output, caches, diagnostics, credentials, and local configuration never enter the public artifact.
- Application-configuration schema is version 2; distribution-contract schema is version 3 and deny-by-default.
- Ask one focused question at a time, wait at consequential decisions, preserve revisions, and never call a draft approved without explicit confirmation.
- Keep Design Statements distinct from Application Plugin Design Specifications.
- Keep logical Instruction Modules distinct from implementation Skills; reserve Skill Architecture and Reference Material technical bindings for the Application Workbench.
- Never invent verification, coverage, rights, tool availability, runtime evidence, or test results.
- Do not create nested Git worktrees or `.git` metadata anywhere below this repository.
- Do not publish, push, tag, create a release, mutate the marketplace, or submit to ClawHub without a later explicit approval.

## Review Focus

1. A user demands an immediate final specification from a vague idea: `test_guiding_session_preserves_draft_and_waiting_states` must prove the plugin asks one question or emits only a labeled draft with assumptions.
2. A workflow or module payload hides a Skill assignment under a nested key: `test_module_validator_rejects_implementation_architecture_at_any_depth` must reject it.
3. A Reference Material Usage Map mixes behavioral use with filenames, storage, RAG, or Skill bindings: `test_reference_material_skill_reserves_technical_binding_for_workbench` must protect the boundary.
4. A handoff looks complete but lacks explicit approval or contains unresolved owner decisions: `test_handoff_validator_requires_approval_and_reports_unresolved_decisions` must block it.
5. A caller asks for a coverage percentage without an explicit requirement-to-test mapping: `test_coverage_reports_not_verified_without_explicit_mapping` must return `NOT VERIFIED`, not a fabricated number.

---

## File Structure

Create the following application-owned tree. Every file has one responsibility.

```text
applications/cool-plugin-design-assistant/
├── .codex-plugin/plugin.json                         # Codex identity and UI metadata
├── conversion.json                                  # schema-v2 provenance and verification routing
├── README.md                                         # product usage and deterministic commands
├── DISTRIBUTION.md                                   # public artifact boundary
├── LICENSE                                           # MIT terms
├── PRIVACY.md                                        # no telemetry, credentials, or retained user data
├── SECURITY.md                                       # safe design and reporting boundary
├── THIRD_PARTY_CONTENT.md                            # normalized-source rights statement
├── THIRD_PARTY_NOTICES.md                            # required notices
├── docs/
│   ├── application-invariants.md                     # INV-001 through INV-015
│   ├── source-decisions.md                           # included derivatives and excluded raw sources
│   ├── source-inventory.json                         # redacted hashes and source-relative paths
│   ├── runtime-compatibility.md                      # expected, then observed runtime evidence
│   └── marketplace-approved-delta.json               # explicit marketplace comparison baseline
├── openclaw/
│   ├── distribution.json                             # schema-v3 allowlist and publication flags
│   └── README.md                                     # lightweight bundle notes
├── scripts/
│   ├── cool_plugin_design_assistant.py               # stable validator/status launcher
│   ├── distribution_audit.py                         # public-tree safety and rights audit hook
│   └── build_marketplace_release.py                  # deterministic Codex artifact builder
├── skills/
│   ├── guiding-ai-application-design-sessions/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/session-contract.md
│   ├── creating-design-statements/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/design-statement-contract.md
│   ├── designing-application-workflows-and-instruction-modules/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/
│   │       ├── workflow-blueprint-contract.md
│   │       ├── instruction-module-contract.md
│   │       └── user-interaction-protocols.md
│   ├── evaluating-reference-materials/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/
│   │       ├── reference-material-evaluation.md
│   │       └── reference-material-usage-map.md
│   ├── creating-application-plugin-design-specifications/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/
│   │       ├── specification-contract.md
│   │       └── workbench-handoff-contract.md
│   ├── reviewing-application-implementations/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/implementation-review-contract.md
│   └── planning-application-tests-and-improvements/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       └── references/
│           ├── application-test-plan-contract.md
│           └── improvement-patch-contract.md
└── tests/
    ├── __init__.py
    ├── coverage-matrix.md
    ├── behavior/
    │   ├── guiding-design-sessions.md
    │   ├── creating-design-statements.md
    │   ├── designing-workflows-and-modules.md
    │   ├── evaluating-reference-materials.md
    │   ├── creating-specifications.md
    │   ├── reviewing-implementations.md
    │   └── planning-tests-and-improvements.md
    ├── fixtures/
    │   ├── design-statement-valid.md
    │   ├── design-spec-valid.md
    │   ├── workflow-valid.json
    │   ├── modules-valid.json
    │   ├── handoff-valid.json
    │   └── coverage-valid.json
    ├── test_conversion_contract.py
    ├── test_skill_contracts.py
    ├── test_tools.py
    ├── test_distribution.py
    └── test_marketplace_release.py
```

Modify:

- `marketplaces/obvious-one.json` — register one new schema-v3 `build` entry after Vibe Coding Designer.
- `tests/test_application_config.py` — assert the new application’s command targets and marketplace paths.
- `scripts/verify_extraction.py` only if its current discovery-based behavior fails to include the new application; do not add a product-specific branch when discovery already works.

Generated output remains below ignored `dist/` or `.tmp/` and is never committed.

For creator commands, resolve the installed skill roots without writing a
machine-specific path into product contracts:

```powershell
$PluginCreatorRoot = Resolve-Path (Join-Path $env:USERPROFILE ".codex\skills\.system\plugin-creator")
$SkillCreatorRoot = Resolve-Path (Join-Path $env:USERPROFILE ".codex\skills\.system\skill-creator")
```

## Requirement-to-Task Map

| Approved requirement group | Owning task |
| --- | --- |
| UC-001; BEH-001, BEH-002, BEH-011, BEH-014; INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-010, INV-011, INV-012, INV-013, INV-014, INV-015 | Task 2 |
| UC-002; BEH-003; INV-003 through INV-007 and INV-015 | Task 3 |
| UC-003; BEH-004, BEH-005, BEH-006, BEH-007; INV-001, INV-002, INV-003, INV-004, INV-008, INV-015 | Task 4 |
| UC-004; BEH-008; INV-008, INV-010, INV-011, and INV-015 | Task 5 |
| UC-005; BEH-002, BEH-006, and BEH-011; INV-005 through INV-012 and INV-015 | Task 6 |
| UC-006; BEH-009 and BEH-012; INV-008 through INV-011 | Task 7 |
| UC-007; BEH-010 and BEH-013; INV-009 through INV-011 | Task 8 |
| Canonical workflow/module contracts and architecture-boundary enforcement | Task 9 |
| Design, handoff, coverage, status, and CLI contracts | Task 10 |
| Rights, allowlist, deterministic packages, and marketplace registration | Task 11 |
| Structural, product, framework, and artifact evidence | Task 12 |
| Codex/OpenClaw execution, cross-runtime comparison, and marketplace staging | Task 13 |

### Task 1: Establish the Application Contract Spine

**Files:**
- Create: `applications/cool-plugin-design-assistant/tests/__init__.py`
- Create: `applications/cool-plugin-design-assistant/tests/test_conversion_contract.py`
- Create: `applications/cool-plugin-design-assistant/conversion.json`
- Create: `applications/cool-plugin-design-assistant/.codex-plugin/plugin.json`
- Create: `applications/cool-plugin-design-assistant/docs/source-inventory.json`
- Create: `applications/cool-plugin-design-assistant/docs/source-decisions.md`
- Create: `applications/cool-plugin-design-assistant/docs/application-invariants.md`
- Create: `applications/cool-plugin-design-assistant/tests/coverage-matrix.md`
- Create: `applications/cool-plugin-design-assistant/openclaw/distribution.json`
- Create: `applications/cool-plugin-design-assistant/openclaw/README.md`
- Create: `applications/cool-plugin-design-assistant/LICENSE`
- Create: `applications/cool-plugin-design-assistant/README.md`
- Create: `applications/cool-plugin-design-assistant/DISTRIBUTION.md`
- Create: `applications/cool-plugin-design-assistant/PRIVACY.md`
- Create: `applications/cool-plugin-design-assistant/SECURITY.md`
- Create: `applications/cool-plugin-design-assistant/THIRD_PARTY_CONTENT.md`
- Create: `applications/cool-plugin-design-assistant/THIRD_PARTY_NOTICES.md`

**Interfaces:**
- Consumes: the approved specification and its 16-entry source inventory.
- Produces: schema-v2 `conversion.json`, an initially valid schema-v3 distribution contract, manifest identity, redacted provenance, invariant register, and product roots used by every later task.

- [ ] **Step 1: Write the failing contract test**

```python
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ConversionContractTests(unittest.TestCase):
    def test_identity_inventory_and_invariants_are_complete(self) -> None:
        config = json.loads((ROOT / "conversion.json").read_text(encoding="utf-8"))
        manifest = json.loads(
            (ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
        )
        inventory = json.loads(
            (ROOT / "docs/source-inventory.json").read_text(encoding="utf-8")
        )
        invariants = (ROOT / "docs/application-invariants.md").read_text(encoding="utf-8")
        self.assertEqual(config["schema_version"], 2)
        self.assertEqual(config["application_id"], "cool-plugin-design-assistant")
        self.assertEqual(manifest["name"], "cool-plugin-design-assistant")
        self.assertEqual(manifest["interface"]["displayName"], "Cool Plugin Design Assistant")
        self.assertEqual(manifest["version"], "1.0.0")
        self.assertEqual(len(inventory["source_inventory"]), 16)
        self.assertFalse(any(":\\Users\\" in item["path"] for item in inventory["source_inventory"]))
        for number in range(1, 16):
            self.assertIn(f"INV-{number:03d}", invariants)
```

- [ ] **Step 2: Run the test and verify the missing application files cause RED**

Run: `python -B -m unittest discover -s applications\cool-plugin-design-assistant\tests -p "test_conversion_contract.py" -v`

Expected: FAIL because `conversion.json` and the manifest do not exist.

- [ ] **Step 3: Scaffold only the plugin root and skills directory**

Run from the repository root after resolving `$PluginCreatorRoot`:

```powershell
python (Join-Path $PluginCreatorRoot "scripts\create_basic_plugin.py") cool-plugin-design-assistant `
  --path D:\GitHub\convert-gpt-application\applications `
  --with-skills
```

Do not add a personal marketplace entry. Replace the scaffold manifest through a reviewed patch with the approved identity, MIT license, `skills: "./skills/"`, Traditional Chinese default prompts, `capabilities: ["Interactive", "Read", "Write"]`, and no `apps` or `mcpServers` keys.

- [ ] **Step 4: Add the exact schema-v2 configuration**

Use these verification command IDs and targets:

```json
{
  "runtime-status": ["codex", "openclaw"],
  "design-validator": ["codex", "openclaw"],
  "workflow-validator": ["codex", "openclaw"],
  "module-validator": ["codex", "openclaw"],
  "handoff-validator": ["codex", "openclaw"],
  "distribution-audit": ["codex", "openclaw"]
}
```

Point `source_inventory` to `docs/source-inventory.json`, `coverage_matrix` to `tests/coverage-matrix.md`, `distribution_contract` to `openclaw/distribution.json`, and `source_location` to ignored `conversion.local.json`.

- [ ] **Step 5: Add the redacted inventory and decisions**

Copy the 16 source-relative paths and SHA-256 values exactly from specification section 5. Set classifications to `source-only`, with the two example PDFs marked `analysis-fixture-only` and `ChatGPT Image.png` marked `excluded-source-only`. State that normalized derivatives are MIT-approved and raw source exports are excluded.

- [ ] **Step 6: Add the invariant register and initial coverage matrix**

Copy INV-001 through INV-015 verbatim. Give every row columns `Requirement`, `Owner`, `Structural evidence`, `Behavior evidence`, and `Status`; initialize status to `EXPECTED`, never `PASS`.

- [ ] **Step 7: Add the public policy documents**

State that the plugin has no telemetry, credential storage, external services, model downloads, or RAG; the launcher reads only caller-supplied local artifacts; unsafe application design is declined; raw source files are not redistributed.

- [ ] **Step 8: Add an initially valid schema-v3 text-only distribution contract**

Set `family` to `bundle-plugin`, `rag` to `null`, GitHub marketplace publication to enabled, and ClawHub to disabled with null family/manifest. Allowlist the manifest, policy documents, `docs`, `scripts`, and `skills`; exclude tests, conversion files, and `docs/marketplace-approved-delta.json`. Use one approved text rule citing `docs/source-decisions.md`. Set `audit_hook` to null until Task 11 adds the tested product audit.

- [ ] **Step 9: Run the contract and repository configuration tests**

Run:

```powershell
python -B -m unittest discover -s applications\cool-plugin-design-assistant\tests -p "test_conversion_contract.py" -v
python -B -m unittest tests.test_application_config tests.test_repository_layout -v
```

Expected: every command PASS. The existing explicit application assertions do not yet require a catalog registration for this application.

- [ ] **Step 10: Validate the scaffolded manifest and distribution contract**

Run:

```powershell
python (Join-Path $PluginCreatorRoot "scripts\validate_plugin.py") `
  applications\cool-plugin-design-assistant
python -B -m obvious_one_plugin_framework.cli validate-contract `
  --contract applications\cool-plugin-design-assistant\openclaw\distribution.json `
  --json
```

Expected: plugin and contract PASS with an empty `skills/` directory permitted during this task.

- [ ] **Step 11: Commit the contract spine**

```powershell
git add applications/cool-plugin-design-assistant
git commit -m "feat: establish cool plugin design assistant contract"
```

### Task 2: Implement and Behavior-Test the Session Orchestrator Skill

**Files:**
- Create: `applications/cool-plugin-design-assistant/tests/test_skill_contracts.py`
- Create: `applications/cool-plugin-design-assistant/tests/behavior/guiding-design-sessions.md`
- Create: `applications/cool-plugin-design-assistant/skills/guiding-ai-application-design-sessions/SKILL.md`
- Create: `applications/cool-plugin-design-assistant/skills/guiding-ai-application-design-sessions/agents/openai.yaml`
- Create: `applications/cool-plugin-design-assistant/skills/guiding-ai-application-design-sessions/references/session-contract.md`
- Modify: `applications/cool-plugin-design-assistant/tests/coverage-matrix.md`

**Interfaces:**
- Consumes: INV-001 through INV-006, INV-010 through INV-015.
- Produces: decision ledger states `confirmed`, `assumption`, `recommendation`, `unresolved`; phase routing; approval and stop/resume contract used by all sibling Skills.

- [ ] **Step 1: Write the behavior scenario and failing structural test**

```python
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def read_reference(skill: str, filename: str) -> str:
    return (ROOT / "skills" / skill / "references" / filename).read_text(
        encoding="utf-8"
    )


class SkillContractTests(unittest.TestCase):
    def test_guiding_session_preserves_draft_and_waiting_states(self) -> None:
    text = read_skill("guiding-ai-application-design-sessions")
    for phrase in (
        "one focused question",
        "wait",
        "confirmed",
        "assumption",
        "recommendation",
        "unresolved",
        "draft",
        "explicit confirmation",
        "Traditional Chinese",
    ):
        self.assertIn(phrase, text)
```

The behavior fixture supplies: “I have a vague app idea. Skip questions and give me the final approved specification now.” Expected behavior: one focused question and wait, or a clearly labeled draft with assumptions; never an approved artifact or Workbench handoff.

- [ ] **Step 2: Run a clean-context baseline without the Skill**

Give a fresh evaluation agent only the behavior fixture. Save the transcript under `.tmp/cool-plugin-design-assistant/baselines/guiding.txt`, record observable failures in the local execution log, and do not commit the transcript.

- [ ] **Step 3: Run the structural test and verify RED**

Run: `python -B -m unittest discover -s applications\cool-plugin-design-assistant\tests -p "test_skill_contracts.py" -v`

Expected: FAIL because the Skill is absent.

- [ ] **Step 4: Create the minimal orchestrator Skill and reference**

The `SKILL.md` must route the current phase, ask one focused question, wait at consequential decisions, keep the four decision states separate, and route to sibling Skills by exact name. The session reference must define the five approved phases: intent/Design Statement, behavioral design, specification, Workbench handoff, and review/testing.

Use this operating-contract shape:

```markdown
---
name: guiding-ai-application-design-sessions
description: Use when a user has an AI application idea that needs guided discovery, phased design, approval tracking, or routing to a focused design task.
---

# Guide AI Application Design Sessions

Default to Traditional Chinese and adapt terminology to the user. Read
[the session contract](references/session-contract.md), identify the earliest
unresolved consequential decision, ask one focused question, and wait.

Maintain four distinct ledger states: confirmed, assumption, recommendation,
and unresolved. A draft is not approved. Require explicit confirmation before
specification handoff, and preserve revise, pause, resume, and stop choices.

Route focused work to `creating-design-statements`,
`designing-application-workflows-and-instruction-modules`,
`evaluating-reference-materials`, or
`creating-application-plugin-design-specifications`. After Workbench output,
route review and testing to their named sibling Skills.

Decline assistance that designs an illegal or harmful application. Do not
implement or publish the designed application.
```

- [ ] **Step 5: Add discoverable UI metadata**

Set `display_name: "Guide AI Application Design Sessions"`, a concise short description, a default prompt containing `$guiding-ai-application-design-sessions`, and `allow_implicit_invocation: true`.

- [ ] **Step 6: Validate structure and GREEN**

Run:

```powershell
python (Join-Path $SkillCreatorRoot "scripts\quick_validate.py") `
  applications\cool-plugin-design-assistant\skills\guiding-ai-application-design-sessions
python -B -m unittest discover -s applications\cool-plugin-design-assistant\tests -p "test_skill_contracts.py" -v
```

Expected: PASS.

- [ ] **Step 7: Re-run the same scenario with the Skill enabled**

The fresh evaluation agent must ask no more than one focused question, stop for the response, preserve draft/approval state, and decline harmful application design. Store temporary evidence below `.tmp`, update the coverage row to `STATICALLY VERIFIED`, and do not claim runtime verification.

- [ ] **Step 8: Commit the independently verified Skill**

```powershell
git add applications/cool-plugin-design-assistant/skills/guiding-ai-application-design-sessions applications/cool-plugin-design-assistant/tests
git commit -m "feat: guide AI application design sessions"
```

### Task 3: Implement and Behavior-Test Design Statement Creation

**Files:**
- Create: `applications/cool-plugin-design-assistant/tests/behavior/creating-design-statements.md`
- Create: `applications/cool-plugin-design-assistant/skills/creating-design-statements/SKILL.md`
- Create: `applications/cool-plugin-design-assistant/skills/creating-design-statements/agents/openai.yaml`
- Create: `applications/cool-plugin-design-assistant/skills/creating-design-statements/references/design-statement-contract.md`
- Modify: `applications/cool-plugin-design-assistant/tests/test_skill_contracts.py`
- Modify: `applications/cool-plugin-design-assistant/tests/coverage-matrix.md`

**Interfaces:**
- Consumes: confirmed audience, context, problem, application role/method, intended outcome, and style/tone choices.
- Produces: a versioned Design Statement with state `draft` or `approved`, comparison/revision options, and no embedded full specification.

- [ ] **Step 1: Add the failing contract test**

```python
def test_design_statement_is_concise_separate_and_revisable(self) -> None:
    text = read_skill("creating-design-statements")
    self.assertIn("audience", text)
    self.assertIn("context", text)
    self.assertIn("problem", text)
    self.assertIn("outcome", text)
    self.assertIn("draft", text)
    self.assertIn("approved", text)
    self.assertIn("separate", text)
    self.assertNotIn("choose the Skill Architecture", text)
```

- [ ] **Step 2: Capture RED behavior without the Skill**

Use a request that supplies audience and problem but omits desired outcome while demanding a final statement. Expected failure to detect: inventing the outcome or blending a full specification into the Design Statement.

- [ ] **Step 3: Verify RED structurally**

Run the new single test. Expected: FAIL because the Skill is absent.

- [ ] **Step 4: Author the minimal Skill and contract**

Define the artifact fields `audience`, `context`, `problem`, `application_role_or_method`, `desired_outcome`, `style_and_tone`, `version`, and `state`. Require one question for a consequential missing field, allow two or three alternatives when useful, and request confirm/revise/compare/combine after drafting.

Use this Skill entrypoint:

```markdown
---
name: creating-design-statements
description: Use when a user wants to create, compare, or revise the concise intent statement for an AI Application before detailed specification.
---

# Create Design Statements

Read [the Design Statement contract](references/design-statement-contract.md).
Use confirmed audience, context, problem, application role or method, desired
outcome, and material style or tone decisions. Ask one focused question and
wait when a missing field would change the statement materially.

Produce a concise versioned artifact with state `draft` or `approved`. When
comparison helps, offer two or three materially different versions and explain
the differences. Let the user select, combine, reject, or revise them.

Keep the Design Statement separate from the Application Plugin Design
Specification. Never mark it approved without explicit confirmation.
```

- [ ] **Step 5: Validate and run GREEN behavior**

Run `quick_validate.py`, the product skill-contract suite, and the same fresh-context scenario with the Skill. Expected: the evaluator asks for the missing outcome or labels a reversible assumption; the output stays concise and separate.

- [ ] **Step 6: Commit the Skill**

```powershell
git add applications/cool-plugin-design-assistant/skills/creating-design-statements applications/cool-plugin-design-assistant/tests
git commit -m "feat: create revisable design statements"
```

### Task 4: Implement and Behavior-Test Workflow and Instruction Module Design

**Files:**
- Create: `applications/cool-plugin-design-assistant/tests/behavior/designing-workflows-and-modules.md`
- Create: `applications/cool-plugin-design-assistant/skills/designing-application-workflows-and-instruction-modules/SKILL.md`
- Create: `applications/cool-plugin-design-assistant/skills/designing-application-workflows-and-instruction-modules/agents/openai.yaml`
- Create: `applications/cool-plugin-design-assistant/skills/designing-application-workflows-and-instruction-modules/references/workflow-blueprint-contract.md`
- Create: `applications/cool-plugin-design-assistant/skills/designing-application-workflows-and-instruction-modules/references/instruction-module-contract.md`
- Create: `applications/cool-plugin-design-assistant/skills/designing-application-workflows-and-instruction-modules/references/user-interaction-protocols.md`
- Modify: `applications/cool-plugin-design-assistant/tests/test_skill_contracts.py`
- Modify: `applications/cool-plugin-design-assistant/tests/coverage-matrix.md`

**Interfaces:**
- Consumes: approved mission, outcomes, actors, constraints, failure expectations, and interaction needs.
- Produces: Behavioral Workflow Blueprint plus primary-workflow, intent-triggered, and cross-cutting Instruction Module contracts; never Skill assignments.

- [ ] **Step 1: Add the failing architecture-boundary test**

```python
def test_workflow_skill_defines_modules_and_user_interaction_protocols_not_skills(self) -> None:
    text = read_skill("designing-application-workflows-and-instruction-modules")
    for phrase in (
        "primary-workflow",
        "intent-triggered",
        "cross-cutting",
        "user-interaction protocol",
        "transitions",
        "failure",
        "completion",
        "Application Workbench",
    ):
        self.assertIn(phrase, text)
    self.assertIn("Instruction Module is not a Skill", text)
```

- [ ] **Step 2: Capture baseline pressure behavior**

Ask the evaluator to turn a three-stage mission into modules and “make every module a Skill to save time.” Expected baseline failure to detect: one-to-one module/Skill mapping or missing wait/stop/recovery behavior.

- [ ] **Step 3: Verify RED**

Run the new test. Expected: FAIL because the Skill is absent.

- [ ] **Step 4: Author the workflow and module contracts**

The workflow contract must include workflow ID, mission outcome, actors, inputs, stages, conditional paths, transitions, terminal states, failure/recovery paths, HITL checkpoints, and completion criteria. The module contract must include all fields in specification section 9.4 and explicitly omit Skill assignment fields.

Use this Skill entrypoint:

```markdown
---
name: designing-application-workflows-and-instruction-modules
description: Use when an AI Application mission needs workflows, conditional paths, logical Instruction Modules, transitions, failure behavior, or user-interaction protocols.
---

# Design Application Workflows and Instruction Modules

Confirm the mission and success outcome. Read the workflow blueprint contract,
then design the primary path, conditional paths, transitions, terminal states,
failure/recovery behavior, and HITL checkpoints.

Read the Instruction Module contract and classify each logical module as
primary-workflow, intent-triggered, or cross-cutting. An Instruction Module is
not a Skill. Define behavioral responsibilities and Reference Material needs;
the Application Workbench owns Skill Architecture and technical bindings.

Read the user-interaction protocol reference for questions, waits,
alternatives, revisions, confirmation, progression, pause/resume, and stopping.
Present the blueprint for revision and explicit approval.
```

- [ ] **Step 5: Author the user-interaction protocol reference**

Define questions, per-turn question limit, waits, alternatives, explicit confirmation, ambiguity/conflict handling, direct/guided/Socratic/co-creative/evaluative modes, revise/skip/pause/resume/stop behavior, transition conditions, and draft/finalization rules.

- [ ] **Step 6: Validate and run GREEN behavior**

Run `quick_validate.py`, the full skill-contract suite, and the same pressure scenario. Expected: a mission workflow and logical modules with interaction protocols; explicit deferral of Skill Architecture to the Workbench.

- [ ] **Step 7: Commit the Skill**

```powershell
git add applications/cool-plugin-design-assistant/skills/designing-application-workflows-and-instruction-modules applications/cool-plugin-design-assistant/tests
git commit -m "feat: design workflows and instruction modules"
```

### Task 5: Implement and Behavior-Test Reference Material Evaluation

**Files:**
- Create: `applications/cool-plugin-design-assistant/tests/behavior/evaluating-reference-materials.md`
- Create: `applications/cool-plugin-design-assistant/skills/evaluating-reference-materials/SKILL.md`
- Create: `applications/cool-plugin-design-assistant/skills/evaluating-reference-materials/agents/openai.yaml`
- Create: `applications/cool-plugin-design-assistant/skills/evaluating-reference-materials/references/reference-material-evaluation.md`
- Create: `applications/cool-plugin-design-assistant/skills/evaluating-reference-materials/references/reference-material-usage-map.md`
- Modify: `applications/cool-plugin-design-assistant/tests/test_skill_contracts.py`
- Modify: `applications/cool-plugin-design-assistant/tests/coverage-matrix.md`

**Interfaces:**
- Consumes: candidate material metadata/content plus target workflows, modules, decisions, and outputs.
- Produces: evaluation inventory, conflicts/gaps, rights/provenance decision, and behavior-level Reference Material Usage Map.

- [ ] **Step 1: Add the failing boundary test**

```python
def test_reference_material_skill_reserves_technical_binding_for_workbench(self) -> None:
    text = read_skill("evaluating-reference-materials")
    for phrase in (
        "Reference Material Usage Map",
        "workflow",
        "Instruction Module",
        "decision",
        "output",
        "provenance",
        "rights",
        "exact quotation",
        "advisory",
    ):
        self.assertIn(phrase, text)
    for forbidden in ("assign to a Skill", "choose a RAG", "choose runtime storage"):
        self.assertNotIn(forbidden, text)
```

- [ ] **Step 2: Capture baseline pressure behavior**

Provide two overlapping reference files and demand an immediate mapping to Skill folders and a vector database. Expected failure to detect: technical binding instead of behavioral-use mapping, or invented redistribution rights.

- [ ] **Step 3: Verify RED**

Run the new test. Expected: FAIL because the Skill is absent.

- [ ] **Step 4: Author evaluation and usage-map contracts**

The evaluation reference must cover relevance, structure, authority, limitations, reusability, provenance, rights, conflicts, duplication, missing coverage, private content, and exact-quotation needs. The usage-map reference must contain every field from specification section 11 and state that the Workbench owns canonical filenames, packaged paths, loading routes, indexes, RAG, storage, and Skill bindings.

Use this Skill entrypoint:

```markdown
---
name: evaluating-reference-materials
description: Use when candidate Reference Materials need relevance, authority, provenance, rights, conflict, gap, or behavioral-use evaluation for an AI Application design.
---

# Evaluate Reference Materials

Read the evaluation reference and assess each supplied material without
inventing contents, authority, provenance, or redistribution rights. Identify
conflicts, duplication, missing coverage, private content, limitations, and
whether exact quotation or advisory consultation is required.

Read the usage-map reference and recommend where the knowledge is behaviorally
used: a workflow, Instruction Module, decision, or output, including its stage
or triggering intent and required/optional status.

Produce a Reference Material Usage Map. The Application Workbench owns
canonical filenames, packaged paths, loading routes, RAG/index choices,
runtime storage, and Skill bindings.
```

- [ ] **Step 5: Validate and run GREEN behavior**

Run structural validation, all skill tests, and the pressure scenario. Expected: material-specific behavioral recommendations and unresolved-rights flags; no technical binding.

- [ ] **Step 6: Commit the Skill**

```powershell
git add applications/cool-plugin-design-assistant/skills/evaluating-reference-materials applications/cool-plugin-design-assistant/tests
git commit -m "feat: evaluate reference material usage"
```

### Task 6: Implement and Behavior-Test Specification and Workbench Handoff Creation

**Files:**
- Create: `applications/cool-plugin-design-assistant/tests/behavior/creating-specifications.md`
- Create: `applications/cool-plugin-design-assistant/skills/creating-application-plugin-design-specifications/SKILL.md`
- Create: `applications/cool-plugin-design-assistant/skills/creating-application-plugin-design-specifications/agents/openai.yaml`
- Create: `applications/cool-plugin-design-assistant/skills/creating-application-plugin-design-specifications/references/specification-contract.md`
- Create: `applications/cool-plugin-design-assistant/skills/creating-application-plugin-design-specifications/references/workbench-handoff-contract.md`
- Modify: `applications/cool-plugin-design-assistant/tests/test_skill_contracts.py`
- Modify: `applications/cool-plugin-design-assistant/tests/coverage-matrix.md`

**Interfaces:**
- Consumes: approved Design Statement, workflows, module contracts, user-interaction protocols, Reference Material Usage Map, decisions, assumptions, recommendations, and unresolved questions.
- Produces: 21-section draft/approved Application Plugin Design Specification and an approval-gated Workbench handoff package.

- [ ] **Step 1: Add the failing specification contract test**

```python
def test_specification_has_approved_sections_and_handoff_gate(self) -> None:
    contract = read_reference(
        "creating-application-plugin-design-specifications",
        "specification-contract.md",
    )
    self.assertEqual(len(re.findall(r"(?m)^\d+\. \*\*", contract)), 21)
    skill = read_skill("creating-application-plugin-design-specifications")
    self.assertIn("explicit user confirmation", skill)
    self.assertIn("Application Workbench", skill)
    self.assertIn("must not prescribe", skill)
```

- [ ] **Step 2: Capture baseline pressure behavior**

Supply confirmed behavior but one unresolved rights decision; demand a final handoff and a seven-Skill architecture for the designed application. Expected failure to detect: handoff before approval, hidden unresolved decision, or prescribed architecture.

- [ ] **Step 3: Verify RED**

Run the new test. Expected: FAIL because the Skill is absent.

- [ ] **Step 4: Author the 21-section positive output contract**

List the 21 sections from specification section 13 in order. Define separate blocks for requirements, confirmed decisions, assumptions, recommendations, and unresolved questions. Require draft presentation and revision before explicit approval.

Use this Skill entrypoint:

```markdown
---
name: creating-application-plugin-design-specifications
description: Use when confirmed AI Application design decisions are ready to become a complete specification or an approval-gated Application Workbench handoff.
---

# Create Application Plugin Design Specifications

Require the Design Statement, behavioral workflows, Instruction Module
contracts, user-interaction protocols, Reference Material Usage Map, and
decision ledger. Read the specification contract and produce its 21 sections.

Keep requirements, confirmed decisions, assumptions, recommendations, and
unresolved questions distinct. Present the result as a draft, allow revision,
and require explicit user confirmation before changing its state to approved.

Only after approval, read the Workbench handoff contract and package the
approved artifacts. The handoff must not prescribe Skill count, Skill names,
Skill collaboration, runtime adapters, storage, RAG, or Reference
Material-to-Skill bindings; the Application Workbench determines them.
```

- [ ] **Step 5: Author the Workbench handoff contract**

Include every artifact in specification section 14. Reserve Skills, Skill collaboration, reference technical mapping, deterministic tools, MCP integrations, adapters, manifests, tests, packaging, and runtime realization for the Workbench.

- [ ] **Step 6: Validate and run GREEN behavior**

Run structural validation, all skill tests, and the pressure scenario. Expected: the unresolved rights decision stays visible, handoff is blocked pending approval, and no implementation architecture is prescribed.

- [ ] **Step 7: Commit the Skill**

```powershell
git add applications/cool-plugin-design-assistant/skills/creating-application-plugin-design-specifications applications/cool-plugin-design-assistant/tests
git commit -m "feat: create application plugin design specifications"
```

### Task 7: Implement and Behavior-Test Application Implementation Review

**Files:**
- Create: `applications/cool-plugin-design-assistant/tests/behavior/reviewing-implementations.md`
- Create: `applications/cool-plugin-design-assistant/skills/reviewing-application-implementations/SKILL.md`
- Create: `applications/cool-plugin-design-assistant/skills/reviewing-application-implementations/agents/openai.yaml`
- Create: `applications/cool-plugin-design-assistant/skills/reviewing-application-implementations/references/implementation-review-contract.md`
- Modify: `applications/cool-plugin-design-assistant/tests/test_skill_contracts.py`
- Modify: `applications/cool-plugin-design-assistant/tests/coverage-matrix.md`

**Interfaces:**
- Consumes: approved specification and inspectable Application Implementation evidence.
- Produces: traceable findings classified as error, omission, optional improvement, or approved deviation; no replacement Skill Architecture.

- [ ] **Step 1: Add the failing input and classification test**

```python
def test_implementation_review_requires_both_inputs_and_classifies_findings(self) -> None:
    text = read_skill("reviewing-application-implementations")
    self.assertIn("approved specification", text)
    self.assertIn("Application Implementation", text)
    for classification in ("error", "omission", "optional improvement", "approved deviation"):
        self.assertIn(classification, text)
    self.assertIn("do not redesign", text)
```

- [ ] **Step 2: Capture baseline pressure behavior**

Provide implementation snippets without the approved specification and request corrections. Expected failure to detect: guessed requirements, fabricated conformance, or redesign of Skills.

- [ ] **Step 3: Verify RED, implement, and validate**

Run the failing test, author the Skill/reference, run `quick_validate.py`, and re-run the full skill suite. The reference must define finding ID, requirement ID, observed evidence, classification, severity, rationale, and recommended next action.

Use this Skill entrypoint:

```markdown
---
name: reviewing-application-implementations
description: Use when an approved Application Plugin Design Specification and inspectable Application Implementation are available for conformance review.
---

# Review Application Implementations

Require both the approved specification and inspectable implementation
evidence. If either is missing, request it and wait. Compare observed evidence
to requirement IDs without inventing behavior or execution.

Read the implementation review contract. Classify each finding as error,
omission, optional improvement, or approved deviation, with severity,
rationale, and next action. Do not redesign the Workbench's Skill Architecture
or treat a preferred architecture as a conformance requirement.
```

- [ ] **Step 4: Run GREEN behavior and commit**

The evaluator must request the missing approved specification and stop. Then commit:

```powershell
git add applications/cool-plugin-design-assistant/skills/reviewing-application-implementations applications/cool-plugin-design-assistant/tests
git commit -m "feat: review application implementations"
```

### Task 8: Implement and Behavior-Test Application Test and Improvement Planning

**Files:**
- Create: `applications/cool-plugin-design-assistant/tests/behavior/planning-tests-and-improvements.md`
- Create: `applications/cool-plugin-design-assistant/skills/planning-application-tests-and-improvements/SKILL.md`
- Create: `applications/cool-plugin-design-assistant/skills/planning-application-tests-and-improvements/agents/openai.yaml`
- Create: `applications/cool-plugin-design-assistant/skills/planning-application-tests-and-improvements/references/application-test-plan-contract.md`
- Create: `applications/cool-plugin-design-assistant/skills/planning-application-tests-and-improvements/references/improvement-patch-contract.md`
- Modify: `applications/cool-plugin-design-assistant/tests/test_skill_contracts.py`
- Modify: `applications/cool-plugin-design-assistant/tests/coverage-matrix.md`

**Interfaces:**
- Consumes: approved specification, intended context, explicit requirement IDs, and caller-supplied test results when assessing execution.
- Produces: traceable scenarios and criteria, evidence-state assessment, and versioned corrections or specification patches.

- [ ] **Step 1: Add the failing truthfulness test**

```python
def test_test_planning_requires_inputs_and_never_invents_execution(self) -> None:
    text = read_skill("planning-application-tests-and-improvements")
    for phrase in (
        "approved specification",
        "requirement ID",
        "observable",
        "EXPECTED",
        "STATICALLY VERIFIED",
        "RUNTIME VERIFIED",
        "NOT VERIFIED",
        "supplied results",
        "versioned",
    ):
        self.assertIn(phrase, text)
```

- [ ] **Step 2: Capture baseline pressure behavior**

Ask for a 100% coverage claim without mappings or results. Expected failure to detect: invented tests, execution, or percentage.

- [ ] **Step 3: Verify RED, implement, and validate**

Author scenario fields `test_id`, `requirement_ids`, `preconditions`, `input`, `steps`, `observable_result`, `evidence_state`, and `result`. Define improvement patches with source requirement, observed gap, proposed change, impact, version, and approval state.

Use this Skill entrypoint:

```markdown
---
name: planning-application-tests-and-improvements
description: Use when an approved AI Application specification needs traceable test scenarios, supplied result assessment, or versioned improvement proposals.
---

# Plan Application Tests and Improvements

Require the approved specification, intended context, and explicit requirement
IDs. Read the test-plan contract and create scenarios with preconditions,
inputs, steps, observable results, evidence state, and result.

Use only EXPECTED, STATICALLY VERIFIED, RUNTIME VERIFIED, or NOT VERIFIED for
evidence. Assess execution only from supplied results. Without explicit
requirement-to-test mappings, report coverage as NOT VERIFIED and name the
missing evidence; never invent a percentage.

When evidence shows a gap, read the improvement-patch contract and propose a
versioned, scoped correction with impact and approval state. Do not silently
change the approved specification.
```

- [ ] **Step 4: Run GREEN behavior and commit**

The evaluator must report coverage as `NOT VERIFIED` and name the missing mapping/evidence. Commit:

```powershell
git add applications/cool-plugin-design-assistant/skills/planning-application-tests-and-improvements applications/cool-plugin-design-assistant/tests
git commit -m "feat: plan application tests and improvements"
```

### Task 9: Implement Canonical Workflow and Instruction Module Validators

**Files:**
- Create: `applications/cool-plugin-design-assistant/tests/test_tools.py`
- Create: `applications/cool-plugin-design-assistant/tests/fixtures/workflow-valid.json`
- Create: `applications/cool-plugin-design-assistant/tests/fixtures/modules-valid.json`
- Create: `applications/cool-plugin-design-assistant/scripts/cool_plugin_design_assistant.py`

**Interfaces:**
- Consumes: canonical JSON objects for workflow and module artifacts.
- Produces: `validate_workflow(payload: Any) -> list[str]` and `validate_modules(payload: Any) -> list[str]`, with sorted deterministic errors.

- [ ] **Step 1: Write failing validator tests**

```python
import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "cool_plugin_design_assistant.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("cool_plugin_design_assistant", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_fixture(name: str):
    return json.loads((ROOT / "tests" / "fixtures" / name).read_text(encoding="utf-8"))


tool = load_tool()


class ToolTests(unittest.TestCase):
    def test_workflow_validator_requires_reachable_terminal_and_failure_paths(self) -> None:
    valid = load_fixture("workflow-valid.json")
    self.assertEqual(tool.validate_workflow(valid), [])
    broken = copy.deepcopy(valid)
    broken["states"][1]["transitions"]["failure"] = "missing"
    self.assertIn("unknown state transition: analyze -> missing", tool.validate_workflow(broken))

def test_module_validator_rejects_implementation_architecture_at_any_depth(self) -> None:
    valid = load_fixture("modules-valid.json")
    self.assertEqual(tool.validate_modules(valid), [])
    broken = copy.deepcopy(valid)
    broken["modules"][0]["implementation"] = {"skill_assignment": "one-skill"}
    self.assertIn("implementation architecture forbidden", tool.validate_modules(broken))
```

- [ ] **Step 2: Run RED**

Run: `python -B -m unittest discover -s applications\cool-plugin-design-assistant\tests -p "test_tools.py" -v`

Expected: FAIL because the launcher and functions are absent.

- [ ] **Step 3: Add canonical valid fixtures**

The workflow fixture must declare one start, at least one end, an approval wait state, a failure path, and reachable transitions. The modules fixture must include one module of each approved type and every field in the module contract.

- [ ] **Step 4: Implement minimal deterministic graph validation**

Use pure Python standard library. Validate types, unique IDs, exactly one start, terminal reachability, transition targets, required waiting points, module-type enum, required fields, module transitions, and nested forbidden keys:

```python
FORBIDDEN_ARCHITECTURE_KEYS = {
    "skill", "skill_id", "skill_name", "skill_assignment", "skill_architecture",
    "runtime_adapter", "storage_path", "rag_index", "reference_binding",
}
```

Do not reject ordinary prose merely because it contains the word “skill”; reject explicit architecture fields.

- [ ] **Step 5: Run GREEN and malformed-input cases**

Add cases for duplicate IDs, missing terminal states, unreachable states, transitions to unknown modules, missing user-interaction protocols, and non-object JSON. Run the product tool suite until all pass.

- [ ] **Step 6: Commit the validators**

```powershell
git add applications/cool-plugin-design-assistant/scripts/cool_plugin_design_assistant.py applications/cool-plugin-design-assistant/tests
git commit -m "feat: validate workflows and instruction modules"
```

### Task 10: Complete the Product Launcher and Artifact Validators

**Files:**
- Create: `applications/cool-plugin-design-assistant/tests/fixtures/design-statement-valid.md`
- Create: `applications/cool-plugin-design-assistant/tests/fixtures/design-spec-valid.md`
- Create: `applications/cool-plugin-design-assistant/tests/fixtures/handoff-valid.json`
- Create: `applications/cool-plugin-design-assistant/tests/fixtures/coverage-valid.json`
- Modify: `applications/cool-plugin-design-assistant/tests/test_tools.py`
- Modify: `applications/cool-plugin-design-assistant/scripts/cool_plugin_design_assistant.py`
- Modify: `applications/cool-plugin-design-assistant/README.md`

**Interfaces:**
- Consumes: two distinct Markdown design artifacts plus handoff/coverage JSON.
- Produces: `validate_design_artifacts`, `validate_handoff`, `coverage_report`, `status`, and CLI commands `status`, `validate-design`, `validate-workflow`, `validate-modules`, `validate-handoff`, `coverage`, and `distribution-audit`.

- [ ] **Step 1: Write failing launcher tests**

```python
def test_handoff_validator_requires_approval_and_reports_unresolved_decisions(self) -> None:
    valid = load_fixture("handoff-valid.json")
    self.assertEqual(tool.validate_handoff(valid), [])
    broken = copy.deepcopy(valid)
    broken["approval"]["state"] = "draft"
    broken["unresolved_owner_decisions"] = ["redistribution"]
    errors = tool.validate_handoff(broken)
    self.assertIn("handoff requires explicit approval", errors)
    self.assertIn("unresolved owner decisions: redistribution", errors)

def test_coverage_reports_not_verified_without_explicit_mapping(self) -> None:
    self.assertEqual(
        tool.coverage_report({"requirements": ["INV-001"]})["status"],
        "NOT VERIFIED",
    )
```

- [ ] **Step 2: Run RED**

Run the product tool suite. Expected: FAIL because the new functions and commands are absent.

- [ ] **Step 3: Implement design separation validation**

Require two distinct readable files. The Design Statement must contain the six approved semantic fields and a visible artifact state. The specification must contain 21 numbered non-empty sections, decision-state headings, and an approval state. Reject using the same path for both inputs.

- [ ] **Step 4: Implement handoff and coverage validation**

Require every handoff field from specification section 14, `approval.state == "approved"`, and an empty `unresolved_owner_decisions` array before PASS. Recursively reject architecture fields. Coverage returns `NOT VERIFIED` unless requirements and test mappings are explicit; otherwise return covered, total, percentage, and uncovered IDs.

- [ ] **Step 5: Implement stable CLI result shapes**

Every command prints ASCII-safe JSON with `status`, `operation`, `errors`, and operation data. Exit 0 on PASS, 2 on invalid invocation/blocked evidence, and 3 on validation failure. `status` reports exactly seven Skill names, RAG as `NOT APPLICABLE`, ClawHub as `NOT APPLICABLE`, and runtime evidence as `NOT VERIFIED` until Task 13.

- [ ] **Step 6: Run every launcher command against valid fixtures**

```powershell
python -B applications\cool-plugin-design-assistant\scripts\cool_plugin_design_assistant.py status --json
python -B applications\cool-plugin-design-assistant\scripts\cool_plugin_design_assistant.py validate-design applications\cool-plugin-design-assistant\tests\fixtures\design-statement-valid.md applications\cool-plugin-design-assistant\tests\fixtures\design-spec-valid.md --json
python -B applications\cool-plugin-design-assistant\scripts\cool_plugin_design_assistant.py validate-workflow applications\cool-plugin-design-assistant\tests\fixtures\workflow-valid.json --json
python -B applications\cool-plugin-design-assistant\scripts\cool_plugin_design_assistant.py validate-modules applications\cool-plugin-design-assistant\tests\fixtures\modules-valid.json --json
python -B applications\cool-plugin-design-assistant\scripts\cool_plugin_design_assistant.py validate-handoff applications\cool-plugin-design-assistant\tests\fixtures\handoff-valid.json --json
python -B applications\cool-plugin-design-assistant\scripts\cool_plugin_design_assistant.py coverage applications\cool-plugin-design-assistant\tests\fixtures\coverage-valid.json --json
```

Expected: each returns one PASS document; malformed fixtures return deterministic FAIL/BLOCKED documents.

- [ ] **Step 7: Commit the completed launcher**

```powershell
git add applications/cool-plugin-design-assistant/scripts applications/cool-plugin-design-assistant/tests applications/cool-plugin-design-assistant/README.md
git commit -m "feat: complete design artifact validators"
```

### Task 11: Enforce the Distribution Boundary and Marketplace Build Contracts

**Files:**
- Create: `applications/cool-plugin-design-assistant/scripts/distribution_audit.py`
- Create: `applications/cool-plugin-design-assistant/scripts/build_marketplace_release.py`
- Modify: `applications/cool-plugin-design-assistant/openclaw/distribution.json`
- Modify: `applications/cool-plugin-design-assistant/openclaw/README.md`
- Create: `applications/cool-plugin-design-assistant/docs/marketplace-approved-delta.json`
- Create: `applications/cool-plugin-design-assistant/docs/runtime-compatibility.md`
- Create: `applications/cool-plugin-design-assistant/tests/test_distribution.py`
- Create: `applications/cool-plugin-design-assistant/tests/test_marketplace_release.py`
- Modify: `applications/cool-plugin-design-assistant/scripts/cool_plugin_design_assistant.py`
- Modify: `applications/cool-plugin-design-assistant/conversion.json`
- Modify: `applications/cool-plugin-design-assistant/DISTRIBUTION.md`
- Modify: `marketplaces/obvious-one.json`
- Modify: `tests/test_application_config.py`

**Interfaces:**
- Consumes: the finished normalized product tree and application identity.
- Produces: safe Codex artifact, deterministic OpenClaw bundle, schema-v3 contract, audit hook, and catalog-driven staging entry.

- [ ] **Step 1: Write failing distribution tests**

```python
import json
from pathlib import Path
import tempfile
import unittest

from obvious_one_plugin_framework.contract import load_contract
from obvious_one_plugin_framework.package_builder import build_package


ROOT = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def test_distribution_is_schema_v3_text_only_and_clawhub_disabled(self) -> None:
        contract = load_contract(ROOT / "openclaw/distribution.json")
    self.assertEqual(contract.schema_version, 3)
    self.assertIsNone(contract.rag)
    self.assertTrue(contract.publication.github_marketplace.enabled)
    self.assertFalse(contract.publication.clawhub.enabled)
    self.assertEqual(
        contract.audit_hook,
        "scripts/distribution_audit.py:audit_distribution",
    )

    def test_public_artifacts_exclude_tests_conversion_and_raw_sources(self) -> None:
        raw = json.loads(
            (ROOT / "openclaw/distribution.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("tests", raw["include_prefixes"])
        self.assertNotIn("conversion.json", raw["include_files"])
        with tempfile.TemporaryDirectory() as temp:
            result = build_package(
                load_contract(ROOT / "openclaw/distribution.json"),
                Path(temp) / "bundle",
            )
            public_files = [path for path in result.output.rglob("*") if path.is_file()]
        self.assertFalse(
            any(path.suffix.lower() in {".pdf", ".docx", ".png"} for path in public_files)
        )
```

- [ ] **Step 2: Run RED**

Run the distribution and marketplace release tests. Expected: FAIL because contracts and builders are absent.

- [ ] **Step 3: Implement the text-only distribution audit**

Reject symlinks/reparse points, `.git`, `.env`, caches, private absolute paths, secret patterns, raw-source suffixes, databases/models/indexes, scaffold markers, non-UTF-8 text, broken local Markdown links, and files outside the allowlist. Expose `audit_distribution(stage: Path, contract: object) -> list[str]` for the framework hook.

- [ ] **Step 4: Implement the deterministic Codex builder**

Copy only `.codex-plugin`, `docs`, `scripts`, `skills`, and approved root policy documents; exclude tests, `conversion.json`, `conversion.local.json`, `openclaw`, and `docs/marketplace-approved-delta.json`. Use a staging directory and atomic replacement. Emit sorted paths, SHA-256 hashes, and total bytes.

- [ ] **Step 5: Add the schema-v3 contract**

Set `family` to `bundle-plugin`, `rag` to `null`, `github_marketplace.enabled` to true, and `clawhub.enabled` to false with null family/manifest. Use one approved `redistributable-text` content rule whose provenance is `docs/source-decisions.md`. Select only normalized runtime files and use `scripts/distribution_audit.py:audit_distribution` as the hook.

- [ ] **Step 6: Register catalog and application verification**

Append one `build` entry to `marketplaces/obvious-one.json` with destinations `plugins/cool-plugin-design-assistant` and `openclaw/cool-plugin-design-assistant`. Update `tests/test_application_config.py` to expect all three applications and assert the six command target mappings from Task 1.

- [ ] **Step 7: Validate and build twice**

```powershell
python -B -m obvious_one_plugin_framework.cli validate-contract --contract applications\cool-plugin-design-assistant\openclaw\distribution.json --json
python -B -m obvious_one_plugin_framework.cli build-package --contract applications\cool-plugin-design-assistant\openclaw\distribution.json --output .tmp\cool-plugin-design-assistant\openclaw-one
python -B -m obvious_one_plugin_framework.cli build-package --contract applications\cool-plugin-design-assistant\openclaw\distribution.json --output .tmp\cool-plugin-design-assistant\openclaw-two
python -B -m obvious_one_plugin_framework.cli verify --contract applications\cool-plugin-design-assistant\openclaw\distribution.json --output .tmp\cool-plugin-design-assistant\openclaw-one
```

Parse the single `result-schema-v1` document from each command and compare bundle identities from both builds; do not treat exit code alone as evidence.

- [ ] **Step 8: Run all distribution tests and commit**

```powershell
python -B -m unittest discover -s applications\cool-plugin-design-assistant\tests -p "test_distribution.py" -v
python -B -m unittest discover -s applications\cool-plugin-design-assistant\tests -p "test_marketplace_release.py" -v
python -B -m unittest tests.test_application_config -v
git add applications/cool-plugin-design-assistant marketplaces/obvious-one.json tests/test_application_config.py
git commit -m "feat: package cool plugin design assistant"
```

### Task 12: Run Structural, Product, Framework, and Artifact Verification

**Files:**
- Modify: `applications/cool-plugin-design-assistant/tests/coverage-matrix.md`
- Modify: `applications/cool-plugin-design-assistant/docs/runtime-compatibility.md`
- Modify: `scripts/verify_extraction.py` only if discovery-based verification exposes a real product-independent defect.

**Interfaces:**
- Consumes: the complete development tree and built artifacts.
- Produces: fresh test evidence, deterministic artifact evidence, and exact remaining runtime gates.

- [ ] **Step 1: Validate every Skill independently**

```powershell
Get-ChildItem applications\cool-plugin-design-assistant\skills -Directory | ForEach-Object {
  python (Join-Path $SkillCreatorRoot "scripts\quick_validate.py") $_.FullName
  if ($LASTEXITCODE -ne 0) { throw "Skill validation failed: $($_.Name)" }
}
```

Expected: seven PASS results.

- [ ] **Step 2: Validate the plugin and product suite**

```powershell
python (Join-Path $PluginCreatorRoot "scripts\validate_plugin.py") applications\cool-plugin-design-assistant
python -B -m unittest discover -s applications\cool-plugin-design-assistant\tests -v
```

Expected: PASS with no warnings or leaked generated files.

- [ ] **Step 3: Run generic repository and framework suites**

```powershell
python -B -m unittest discover -s tests\framework -v
python -B -m unittest discover -s tests -t . -v
```

Expected: PASS. If Python temporary-directory permissions fail inside the sandbox, reproduce the permission error minimally, then rerun the unchanged tests with narrowly scoped approval; never reclassify a sandbox failure as a product failure.

- [ ] **Step 4: Run the application-aware verifier**

```powershell
python -B scripts\verify_extraction.py --application cool-plugin-design-assistant
```

Expected: product, audit, commands, Codex build, and OpenClaw build PASS; marketplace comparison may be `NOT VERIFIED` until a read-only marketplace path is supplied.

- [ ] **Step 5: Audit the tracked and generated trees**

Run the product `distribution-audit` command against both built artifacts, search for raw extensions/private paths/secrets, run `git diff --check`, and confirm generated output is ignored. Update coverage rows only to the evidence level actually established.

- [ ] **Step 6: Commit verification documentation only if evidence changed it**

```powershell
git add applications/cool-plugin-design-assistant/tests/coverage-matrix.md applications/cool-plugin-design-assistant/docs/runtime-compatibility.md
git commit -m "test: record static conversion evidence"
```

Do not create an empty commit.

### Task 13: Verify Both Runtimes and Prepare the Non-Destructive Marketplace Delta

**Files:**
- Modify: `applications/cool-plugin-design-assistant/docs/runtime-compatibility.md`
- Modify: `applications/cool-plugin-design-assistant/tests/coverage-matrix.md`
- Generated only: `dist/marketplace-delta/obvious-one/**`
- Generated only: `.tmp/verification/**`

**Interfaces:**
- Consumes: verified Codex and OpenClaw artifacts plus the read-only marketplace baseline at `D:\GitHub\obvious-one-plugins`.
- Produces: discovery/execution evidence for both runtimes, cross-runtime comparison, local staged marketplace delta, and final readiness classification.

- [ ] **Step 1: Inspect installed runtime interfaces before mutation**

Run:

```powershell
codex --version
codex plugin --help
openclaw --version
openclaw --help
```

Record versions and supported installation/discovery commands. If either CLI is absent or its required capability is unavailable, mark that runtime `NOT VERIFIED`, classify the conversion `CONDITIONALLY PORTABLE`, and use the exact phrase `CONVERSION COMPLETE — RUNTIME VALIDATION PENDING`.

- [ ] **Step 2: Prepare and verify the staged marketplace without mutating the baseline**

```powershell
python -B -m obvious_one_plugin_framework.cli prepare-marketplace --catalog marketplaces\obvious-one.json --marketplace D:\GitHub\obvious-one-plugins --output dist\marketplace-delta\obvious-one --json
python -B -m obvious_one_plugin_framework.cli verify-marketplace --catalog marketplaces\obvious-one.json --marketplace dist\marketplace-delta\obvious-one --json
```

Expected: one PASS `result-schema-v1` document from each command; only the declared Cool Plugin Design Assistant destinations and catalog entries differ.

- [ ] **Step 3: Verify Codex discovery in a new task**

First run `codex plugin marketplace list`. If `obvious-one` is not configured, use the documented local marketplace interface:

```powershell
codex plugin marketplace add D:\GitHub\convert-gpt-application\dist\marketplace-delta\obvious-one
codex plugin marketplace list
codex plugin add cool-plugin-design-assistant@obvious-one
codex plugin list
```

If `obvious-one` is already configured to a different root, do not remove or replace it. Use an isolated Codex profile only when the current `codex --help` documents one; otherwise report Codex runtime execution as `NOT VERIFIED` and request permission for a temporary configuration change.

Start a new Codex task, confirm all seven Skills are discoverable, and run BEH-001, BEH-006, BEH-008, BEH-011, and BEH-013. Record observed outcomes without copying private transcripts into Git.

- [ ] **Step 4: Verify OpenClaw discovery using its inspected current interface**

Install the generated bundle into an isolated temporary OpenClaw workspace using the exact command shown by the current `openclaw --help`; do not guess a deprecated command. Confirm all seven Skills are eligible/model-visible, run the same five scenarios, and invoke the packaged launcher’s status, design, workflow, module, handoff, and coverage commands.

- [ ] **Step 5: Compare observable behavior**

Create a comparison table in `docs/runtime-compatibility.md` for question count, wait behavior, draft/approval state, Instruction Module/Skill separation, Reference Material Usage Map boundary, coverage truthfulness, launcher outputs, and seven-Skill discovery. Use `RUNTIME VERIFIED` only where direct evidence exists.

- [ ] **Step 6: Run application-aware verification with marketplace evidence**

```powershell
python -B scripts\verify_extraction.py --application cool-plugin-design-assistant --marketplace D:\GitHub\obvious-one-plugins
```

If the baseline marketplace does not yet contain this unpublished plugin, preserve marketplace equivalence as `NOT VERIFIED`; the staged-delta verification is not publication evidence.

- [ ] **Step 7: Assign the compatibility classification and commit evidence**

Use `PORTABLE` only if the same Skill tree passed representative execution in both runtimes. Otherwise use the exact supported classification and list every missing gate. Commit only normalized evidence summaries:

```powershell
git add applications/cool-plugin-design-assistant/docs/runtime-compatibility.md applications/cool-plugin-design-assistant/tests/coverage-matrix.md
git commit -m "test: verify cool plugin design assistant runtimes"
```

- [ ] **Step 8: Run the final clean-tree gate and stop before publication**

```powershell
python -B -m unittest discover -s applications\cool-plugin-design-assistant\tests -v
python -B -m unittest discover -s tests\framework -v
python -B -m unittest discover -s tests -t . -v
git diff --check
git status --short
```

Report source inventory, invariant coverage, package paths, deterministic identities, Codex/OpenClaw evidence, cross-runtime classification, exact unverified gates, commits, staged marketplace delta, and publication state. Do not mutate `D:\GitHub\obvious-one-plugins`, push, tag, release, or publish.

## Plan Completion Gate

Before implementation begins, review this plan against all 20 specification sections and confirm:

- every INV, UC, BEH, Skill, validator command, package boundary, and runtime gate has an owning task;
- no retired architecture-design Skill is introduced;
- workflow language consistently uses `user-interaction protocols`;
- Reference Material evaluation recommends behavioral use while the Workbench owns technical binding;
- every Skill is created, tested, validated, and committed before the next Skill begins;
- ClawHub remains disabled and publication remains unauthorized.
