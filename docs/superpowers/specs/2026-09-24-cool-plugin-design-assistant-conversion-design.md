# Cool Plugin Design Assistant Conversion Design

## 1. Status and Decision Record

This document specifies the conversion of the source AI application into a
portable plugin of skills named `cool-plugin-design-assistant`, displayed as
**Cool Plugin Design Assistant**, version `1.0.0`.

The product owner approved the design baseline in conversation on 2026-09-24,
including these two clarifications:

1. Reference Material evaluation produces a behavior-level usage map showing
   which workflows, Instruction Modules, decisions, and outputs need the
   knowledge. The Application Workbench still owns Skill bindings, storage,
   retrieval, and loading decisions.
2. The workflow-design responsibility uses the term **user-interaction
   protocols**, not the ambiguous phrase "interaction rules." These protocols
   cover questions, waiting, alternatives, revision, confirmation, progression,
   and stopping behavior.

The written specification itself remains subject to owner review before an
implementation plan may be approved. This document does not authorize
implementation or publication.

## 2. Product Identity and Scope

| Field | Decision |
| --- | --- |
| Plugin ID | `cool-plugin-design-assistant` |
| Display name | Cool Plugin Design Assistant |
| Version | `1.0.0` |
| Default language | Traditional Chinese, with bilingual terminology when useful |
| Target runtimes | Codex and OpenClaw |
| Intended compatibility | One portable Skill implementation for both runtimes |
| Product form | Skills-only plugin with deterministic local validation tools |
| External services | None required for version 1.0 |
| Semantic RAG | Not applicable for version 1.0 |
| Publication target | Obvious One GitHub marketplace and generated lightweight OpenClaw distribution |
| ClawHub publication | Disabled and `NOT APPLICABLE` for version 1.0 |
| License | MIT for plugin code and approved normalized derivatives |

The product guides a human through designing an AI Application and producing an
approved Application Plugin Design Specification for handoff to an Application
Workbench. It may later review the resulting Application Implementation and
plan application tests, but it does not automatically implement or publish the
designed application.

### 2.1 In scope

- guided discovery of audience, context, problem, role, mission, and goals;
- creation and revision of a concise Design Statement;
- exploration of style and tone alternatives;
- design of mission workflows and conditional paths;
- definition of logical Instruction Modules;
- definition of user-interaction protocols;
- evaluation of candidate Reference Materials and their behavioral use;
- creation and revision of an Application Plugin Design Specification;
- preparation of a structured Application Workbench handoff;
- conformance review of an Application Implementation;
- traceable application test planning, feedback, patches, and versioning;
- deterministic validation of design artifacts and distribution boundaries.

### 2.2 Out of scope

- selecting the Skill Architecture for an application designed by the product;
- binding Instruction Modules or Reference Materials to concrete Skills;
- implementing, installing, or publishing a designed application automatically;
- operating live external services or storing credentials;
- semantic retrieval over the bundled methodology references;
- bundling raw source exports or obsolete source files;
- inheriting Web-development behavior from `vibe-coding-designer` unless the
  designed application's requirements independently call for it.

## 3. Terminology Contract

The conversion uses the following authoritative terminology:

| Source term | Converted term and meaning |
| --- | --- |
| GPT Application | AI Application: the product the human is designing |
| GPT Builder | Application Workbench: the environment that interprets the approved design, derives architecture, implements, validates, and later supports publication |
| System Instructions | Application Plugin Design Specification: the detailed behavioral specification |
| Design Statement | A separate concise statement of human design intent |
| Resources / Uploaded Files | Reference Materials: supporting knowledge for specific behaviors and workflows |
| Modules | Logical Instruction Modules when describing required behavior; never automatically equivalent to Skills |
| GPT Configuration | Application Implementation produced by the Workbench |
| GPT Testing | Application Testing against the approved specification |

The Application Plugin Design Specification may define logical Instruction
Modules. It must not prescribe the Skill Architecture used to implement them.

## 4. Two Architectural Levels

The conversion must keep two levels distinct.

### 4.1 Internal architecture of Cool Plugin Design Assistant

The current conversion Workbench determines the Skills, references, tools,
tests, packaging, and runtime evidence needed to implement Cool Plugin Design
Assistant itself.

### 4.2 Artifacts created for users

The finished product helps a user define Design Statements, workflows,
Instruction Modules, Reference Material requirements, behavioral boundaries,
and acceptance criteria. It then hands the approved specification to an
Application Workbench.

```text
Human design intent
  -> Design Statement
  -> Mission workflows
  -> Logical Instruction Modules
  -> Application Plugin Design Specification
  -> Explicit user approval
  -> Application Workbench handoff
  -> Workbench-derived Skill Architecture
  -> Application Implementation
```

An Instruction Module is a logical behavioral unit required by an application.
A Skill is an implementation unit selected by the Application Workbench. The
Workbench may combine several Instruction Modules in one Skill, split one
complex module across Skills, or implement a module through an orchestrator,
references, deterministic tools, runtime adapters, or a combination.

## 5. Source Inventory and Decisions

The original source folder is immutable. The `Old` subdirectory is excluded by
owner instruction and is not part of the authoritative inventory. Tracked
provenance records must contain only source-relative paths and hashes, never the
private absolute source location.

| Source-relative path | SHA-256 | Role | Distribution decision |
| --- | --- | --- | --- |
| `builder_guide.md` | `006d1fb1a7981e7d72aadb158620da8c9d6b74e8b6d83d493b51a1ac014690f5` | Source Workbench guidance | Normalize; do not package raw source |
| `ChatGPT Image.png` | `398c9185ac4af6bde985ff0f8c7717c273bc45f47351733e19d6b9bae92739c9` | Legacy application image | Exclude from version 1.0 |
| `Human-in-the-Loop_Guide.md` | `490e19be70b1a6886afb4765bae1d1305c0af9a4e3caf7b1e672b6680c8e40a8` | HITL methodology | Normalize into shared behavioral reference |
| `interaction_patterns_guide.md` | `fc77d59ecb8cafb7a08f86993050f084daf462630bf7dec97fe86d32e3d8c605` | Interaction patterns | Normalize into workflow/module reference |
| `knowledge_module_template.md` | `dd71beed2b1395c2198903943c0389ed66bf2861753765a678e3815538e58cea` | Knowledge organization template | Normalize for Reference Materials |
| `modular_design_guide.md` | `bb9ef68d14da09a8a5c9fb5b323736747c6f8f136dafc58fe206274cdac44579` | Behavioral decomposition methodology | Normalize for Instruction Module design |
| `Plugin Spec Examples/Vibe Designer GPT.pdf` | `a454c5c73e49aa7915845381211d7d83f53d412ee9674f4e4a80a285e071c121` | Example specification | Analysis fixture only; exclude raw and domain content |
| `Plugin Spec Examples/酷聖經教師.pdf` | `f4da7ef2ff8da46f7d8fd902abf1fd7bfb95a8f14f79a4268df427da44293d24` | Example specification | Analysis fixture only; exclude raw and domain content |
| `prompt_refactoring_patterns.md` | `eb2fabc97397998366dc76325a54a85230a04ac1e861342ab0f33baea1f63bb7` | Refinement methodology | Normalize into review guidance |
| `Resource Index.md` | `75b022b3dd00fc33d3a239b057d366b6d48ddcd0888cd3732972892a9f282b8a` | Authoring-time resource index | Traceability only; exclude from runtime package |
| `resource_binding_patterns.md` | `8e39935ca412fae6369400974a03f9640dbeaa93ba299435015b5a4f8bdd5b4c` | Source binding methodology | Normalize only as behavior-level usage mapping; Workbench owns technical binding |
| `resource_evaluation_guide.md` | `6a75667d514b9a1530f98bd2c654174fc9d333df8ebd4dd0c593b40b063fc8ed` | Material evaluation methodology | Normalize into Reference Material evaluation |
| `resource_types_guide.md` | `6e7f9056e194b36f7be5033740d6249699e9ead71458c2847d949f079423af19` | Material classification | Normalize into Reference Material evaluation |
| `testing_guide.md` | `130d692779c127207d45037748280358e90b637cd2655d5fbc2cc9903982fe45` | Test methodology | Normalize into application testing guidance |
| `use_case_brainstorm_guide.md` | `022854c3dc0b46ab276d6d3c1c7d9af27a03f37c4eda8508a1819557dc1618c7` | Discovery methodology | Normalize into Design Statement discovery |
| `酷 GPT 應用設計助理 Pro v2.docx` | `a64f379d4061b0566939cb3feff3587bd69ba4ecb69b8c61be46292f5f3430c8` | Authoritative behavioral source | Normalize into Skills, references, invariants, and tests; exclude raw export |

The project author provided the source material and approved the specification's
MIT release basis for normalized derivatives. Raw DOCX, PDF, image, authoring
index, rendered pages, and metadata are not part of the public package.

## 6. Application Invariants

| ID | Requirement |
| --- | --- |
| INV-001 | Ask one focused question at a time during guided discovery. |
| INV-002 | Wait after consequential questions and approval requests. |
| INV-003 | Offer two or three alternatives when comparison materially improves a design decision. |
| INV-004 | Explain meaningful differences and allow selection, combination, rejection, and revision. |
| INV-005 | Distinguish drafts from approved artifacts. |
| INV-006 | Never mark a design final without explicit user confirmation. |
| INV-007 | Keep the Design Statement separate from the Application Plugin Design Specification. |
| INV-008 | Keep logical Instruction Modules separate from implementation Skills. |
| INV-009 | Require the specified inputs before implementation review or application test generation. |
| INV-010 | Preserve confirmed decisions, assumptions, recommendations, and unresolved questions as distinct states. |
| INV-011 | Never invent verification, coverage, rights, tool availability, or runtime evidence. |
| INV-012 | Do not proceed from specification to Workbench handoff without user approval. |
| INV-013 | Default to Traditional Chinese while adapting terminology and depth to the user. |
| INV-014 | Decline assistance that would design an illegal or harmful application. |
| INV-015 | Preserve revision opportunities after every material synthesis step. |

When a user requests immediate output, the product may produce a clearly
labeled draft with explicit assumptions. It must not describe that draft as
approved or final.

## 7. User Goals and Use Cases

### UC-001: Clarify an application idea

- Trigger: the user has an incomplete or vague idea;
- required behavior: guided questions, optional brainstorming, and waiting;
- result: confirmed design inputs without premature specification generation.

### UC-002: Create or revise a Design Statement

- Trigger: the user wants a concise expression of design intent;
- required behavior: synthesize audience, context, problem, method, and goal;
- result: a draft or approved Design Statement kept separate from the detailed
  specification.

### UC-003: Design workflows and Instruction Modules

- Trigger: the user needs to define how the application accomplishes its
  mission or responds to recognizable intents;
- required behavior: derive workflows, logical modules, transitions,
  user-interaction protocols, failure behavior, and completion criteria;
- result: an approved Behavioral Workflow Blueprint and Instruction Module
  contracts, without Skill Architecture decisions.

### UC-004: Evaluate Reference Materials

- Trigger: the user supplies or proposes supporting materials;
- required behavior: assess relevance, structure, authority, reusability,
  provenance, rights, and behavioral use;
- result: an inventory, decisions, gaps, and behavior-level usage map without
  technical Skill or storage bindings.

### UC-005: Create an Application Plugin Design Specification

- Trigger: enough decisions exist to synthesize the intended behavior;
- required behavior: consolidate confirmed behavior, show assumptions and open
  questions separately, validate consistency, and request revision or approval;
- result: an approved specification and Workbench handoff package.

### UC-006: Review an Application Implementation

- Trigger: the user supplies a Workbench-produced implementation or its
  inspectable contracts;
- required behavior: compare implementation evidence with the approved
  specification and classify discrepancies;
- result: a conformance review, not a replacement Skill Architecture.

### UC-007: Plan tests and improvements

- Trigger: the user supplies the approved specification and intended context;
- required behavior: derive traceable scenarios and observable criteria, then
  use supplied results to propose scoped corrections;
- result: application test plan, result assessment, and versioned patches.

## 8. Primary Design Workflow

### Phase 1: Intent and Design Statement

1. Ask about the intended application scenario and wait.
2. Clarify audience, context, problem, desired outcome, and application role.
3. Clarify style and tone when material.
4. Offer two or three alternatives when comparison is useful.
5. Create Design Statement v1.
6. Ask the user to confirm, revise, compare, or combine.

### Phase 2: Behavioral design

1. Confirm the application's primary mission.
2. Decompose the mission into outcomes and stages.
3. Design the primary workflow and conditional paths.
4. Identify primary-workflow, intent-triggered, and cross-cutting Instruction
   Modules.
5. Define transitions, failure behavior, and user-interaction protocols.
6. Identify Reference Material requirements and candidate materials.
7. Present the behavioral design for revision and approval.

### Phase 3: Specification

1. Consolidate confirmed decisions.
2. Produce the Application Plugin Design Specification.
3. Keep requirements, assumptions, recommendations, and unresolved decisions
   distinct.
4. Validate internal consistency and required sections.
5. Present the specification as a draft and allow revision.
6. Mark it approved only after explicit user confirmation.

### Phase 4: Workbench handoff

1. Package the approved specification and supporting artifacts.
2. Identify deterministic-operation and external-capability requirements.
3. Identify unresolved owner decisions.
4. Hand the package to the Application Workbench.
5. Do not prescribe the Skill Architecture.

### Phase 5: Review and testing

1. Compare the Workbench implementation with the approved specification.
2. Classify discrepancies as errors, omissions, optional improvements, or
   approved deviations.
3. Generate traceable application tests.
4. Evaluate supplied test results without inventing execution evidence.
5. Propose scoped corrections or specification revisions.

## 9. Instruction Module Model

### 9.1 Primary-workflow modules

These participate in an ordered or stateful workflow that completes the
application's mission, such as intake, analysis, option generation, selection,
drafting, review, and final confirmation.

### 9.2 Intent-triggered modules

These activate when the user expresses a recognizable goal, whether or not the
primary workflow is active, such as reviewing a specification, evaluating
materials, creating tests, or revising an interaction workflow.

### 9.3 Cross-cutting modules

These apply across workflows, such as HITL control, safety, language and tone,
evidence handling, uncertainty reporting, and confirmation policy.

### 9.4 Required module contract

Each logical Instruction Module may define:

- stable module identifier and human-readable name;
- purpose and supported mission outcome;
- triggering intent or workflow condition;
- required and optional inputs;
- preconditions;
- behavioral procedure;
- outputs;
- user-interaction protocol;
- transitions to other modules;
- stop, wait, and completion conditions;
- error and recovery behavior;
- safety boundaries;
- Reference Material requirements;
- acceptance criteria.

No field assigns the module to a concrete Skill.

## 10. User-Interaction Protocols

A user-interaction protocol specifies how the application communicates with a
user while executing a workflow or Instruction Module. It may define:

- what to ask and what information is required;
- how many questions may be asked in one turn;
- when the application must wait;
- when alternatives must be offered;
- when explicit confirmation is required;
- how incomplete, ambiguous, or conflicting answers are handled;
- whether the mode is direct, guided, Socratic, co-creative, or evaluative;
- how the user may revise, skip, pause, resume, or stop;
- what is summarized before progression;
- which conditions permit a transition;
- when a draft may be generated or finalized.

User-interaction protocols are behavioral requirements. They are not Skill
routing, plugin folder structure, runtime adapters, Reference Material loading,
or implementation-level UI event handling unless the designed application
explicitly requires a UI.

## 11. Reference Material Evaluation and Usage Mapping

The product may inventory candidate materials and assess:

- relevance to the mission and specified behaviors;
- structure and suitability for normalization;
- source authority and known limitations;
- reusability and expected impact;
- provenance, redistribution basis, and attribution needs;
- conflicts, duplication, missing coverage, or private content;
- whether use requires exact quotation, exact structured retrieval, or advisory
  consultation.

The resulting Reference Material Usage Map contains:

- material identifier;
- knowledge supplied;
- supported workflow, Instruction Module, decision, or output;
- applicable stage or triggering intent;
- required versus optional status;
- consultation condition;
- authority and provenance;
- exact-quotation versus advisory status;
- limitations and conflicts.

The specification may state that a workflow or Instruction Module requires
knowledge from an approved material. The Workbench alone decides canonical
filenames, Skill bindings, packaged paths, loading routes, structured indexes,
RAG use, and runtime storage.

## 12. Internal Skill Architecture

These Skills implement Cool Plugin Design Assistant. They do not prescribe the
Skill Architecture of applications designed by it.

| Skill | Responsibility |
| --- | --- |
| `guiding-ai-application-design-sessions` | Coordinate discovery, maintain the decision ledger, route focused work, and enforce HITL and approval points |
| `creating-design-statements` | Convert confirmed human intent into a concise Design Statement with revision and comparison support |
| `designing-application-workflows-and-instruction-modules` | Design mission workflows, conditional paths, logical Instruction Modules, transitions, failure behavior, and user-interaction protocols |
| `evaluating-reference-materials` | Evaluate candidate materials and create a behavior-level usage map without choosing Skill bindings or runtime storage |
| `creating-application-plugin-design-specifications` | Consolidate approved behavior into the complete specification, validate it, and prepare the Workbench handoff |
| `reviewing-application-implementations` | Compare Workbench output with the approved specification without redesigning its Skill Architecture |
| `planning-application-tests-and-improvements` | Produce traceable application tests, assess supplied evidence, and propose versioned corrections |

### 12.1 Collaboration

```text
guiding-ai-application-design-sessions
  +-> creating-design-statements
  +-> designing-application-workflows-and-instruction-modules
  +-> evaluating-reference-materials
  `-> creating-application-plugin-design-specifications
        `-> Application Workbench handoff

Workbench creates Application Implementation
  +-> reviewing-application-implementations
  `-> planning-application-tests-and-improvements
```

The orchestrator owns the current phase, decision ledger, unresolved questions,
confirmation state, routing, and stop/resume behavior. It does not duplicate
the detailed procedure of sibling Skills.

## 13. Application Plugin Design Specification Contract

The generated specification contains:

1. application identity and purpose;
2. Design Statement;
3. intended users and contexts;
4. application mission and success outcomes;
5. scope and exclusions;
6. primary mission workflow;
7. conditional and alternative workflows;
8. Instruction Module contracts;
9. user-intent routing requirements;
10. user-interaction protocols;
11. Human-in-the-Loop checkpoints;
12. inputs, outputs, and state requirements;
13. Reference Material requirements and behavior-level usage map;
14. deterministic-operation requirements;
15. tool, data, runtime, and external-service requirements;
16. safety, privacy, and policy boundaries;
17. failure, uncertainty, and recovery behavior;
18. acceptance criteria;
19. representative application tests;
20. assumptions, decisions, recommendations, and unresolved questions;
21. Application Workbench handoff contract.

The specification must not mandate a Skill count, Skill names, Skill folder
structure, Skill collaboration architecture, runtime adapter, or Reference
Material-to-Skill binding.

## 14. Workbench Handoff Contract

The handoff package contains:

- approved Design Statement;
- approved Application Plugin Design Specification;
- workflow definitions and Instruction Module contracts;
- Reference Material inventory, evaluation, and behavior-level usage map;
- application invariants and HITL checkpoints;
- deterministic-operation candidates;
- tool, data, runtime, and service requirements;
- acceptance criteria and representative scenarios;
- rights and redistribution decisions;
- unresolved owner decisions and explicit exclusions.

The Workbench determines:

- required Skills and their responsibilities;
- Skill collaboration and routing;
- Reference Material technical mapping;
- deterministic tools and MCP integrations;
- runtime adapters and manifests;
- Application Implementation tests and packaging;
- Codex and OpenClaw realization.

## 15. Deterministic Supporting Tools

A stable top-level launcher, proposed as
`scripts/cool_plugin_design_assistant.py`, exposes these product operations:

| Command | Deterministic responsibility |
| --- | --- |
| `status` | Report plugin identity, version, Skill inventory, and optional-capability states |
| `validate-design` | Validate Design Statement/specification separation, required sections, and decision-state representation |
| `validate-workflow` | Validate workflow identifiers, transitions, terminal states, failure paths, and required waiting points |
| `validate-modules` | Validate unique module IDs, required contracts, transitions, and the absence of Skill assignments |
| `validate-handoff` | Validate the Workbench handoff package and prohibit implementation-architecture prescriptions |
| `coverage` | Calculate coverage only from explicit requirement-to-test mappings |
| `distribution-audit` | Enforce the release allowlist, rights evidence, and exclusion of private or generated state |

Machine-readable workflow and Instruction Module artifacts use canonical JSON.
Human-readable Markdown may accompany the JSON, but exact identifier and graph
validation uses the canonical representation.

## 16. Packaging and Redistribution

The application workspace will live at
`applications/cool-plugin-design-assistant`. Its application configuration uses
schema version 2; its OpenClaw distribution contract uses schema version 3.

The schema-v3 contract will be deny-by-default. Every selected file must match
exactly one approved text or binary content rule and cite approved provenance.
The public package includes only normalized runtime product files, such as
Skills, references, scripts, documentation, notices, manifest, and license.
Product tests and behavior fixtures remain in the application workspace unless
a specific runtime verification fixture is deliberately included and approved.

The release excludes:

- raw DOCX, PDF, and PNG source files;
- `Old` content;
- the authoring Resource Index;
- document metadata and private absolute paths;
- rendered pages, extraction output, caches, diagnostics, and review history;
- credentials and local configuration;
- undeclared databases, indexes, models, or downloads;
- unrelated application files.

No semantic RAG, model download, remote asset archive, or MCP server is needed
for version 1.0. Exact workflow, module, and coverage relationships use
structured deterministic validation.

Marketplace preparation uses the hardened non-destructive staging flow. It may
prepare and verify a local delta but must not mutate or publish the marketplace
without separate explicit approval.

## 17. Test Strategy and Acceptance

Implementation is test-first. Tests verify observable behavior rather than
preferred wording.

### 17.1 Behavior scenarios

| ID | Scenario | Required observable result |
| --- | --- | --- |
| BEH-001 | User supplies a vague idea | Ask one focused question and wait |
| BEH-002 | User requests immediate final output | Produce at most a labeled draft with assumptions; do not mark it approved |
| BEH-003 | User requests a Design Statement | Produce a concise artifact distinct from the full specification |
| BEH-004 | Mission requires several stages | Derive a workflow and logical Instruction Modules from goals |
| BEH-005 | User intent should trigger independent behavior | Define an intent-triggered Instruction Module and its protocol |
| BEH-006 | User asks whether modules equal Skills | Preserve the explicit separation and defer Skill Architecture to the Workbench |
| BEH-007 | Several interaction patterns are viable | Present two or three alternatives, explain differences, and wait for selection |
| BEH-008 | Candidate materials are supplied | Evaluate them and map behavioral use without choosing Skill bindings |
| BEH-009 | Required review inputs are incomplete | Request missing artifacts before offering implementation corrections |
| BEH-010 | Required testing inputs are incomplete | Do not generate tests or a rubric until required inputs arrive |
| BEH-011 | User pressures the assistant to skip approval | Preserve the waiting point and user decision authority |
| BEH-012 | Workbench implementation is supplied | Review conformance without prescribing a replacement Skill Architecture |
| BEH-013 | User asks for a coverage percentage without mapping | Report coverage as `NOT VERIFIED` and identify missing evidence |
| BEH-014 | User requests a harmful or illegal application | Decline the unsafe design assistance |

### 17.2 Automated layers

- Skill frontmatter, names, routes, and reference-link tests;
- invariant and requirement-coverage tests;
- deterministic validator unit and malformed-input tests;
- behavior fixtures for HITL and architecture-boundary pressure;
- schema-v3 distribution and rights-evidence tests;
- reproducible Codex and OpenClaw artifact builds;
- product distribution audit and marketplace-boundary tests;
- installed-artifact discovery and representative execution in Codex;
- installed-artifact discovery and representative execution in OpenClaw;
- cross-runtime comparison of observable HITL and artifact behavior;
- machine-readable readiness report generation;
- `git diff --check` and tracked-tree cleanliness verification.

No readiness classification may be `READY` until both runtime executions pass.
If either runtime remains unvalidated, the report must say:

```text
CONVERSION COMPLETE — RUNTIME VALIDATION PENDING
```

## 18. Implementation Sequence

After the owner approves this written specification and a separate
implementation plan:

1. create application-owned failing behavior and contract tests;
2. add the schema-v2 application configuration and redacted source inventory;
3. scaffold the seven portable Skills and their UI metadata;
4. implement the orchestrator and core HITL contract;
5. implement focused Skills and progressively disclosed references;
6. implement the canonical workflow/module schemas and deterministic launcher;
7. implement distribution audit, notices, and schema-v3 contract;
8. validate every Skill and plugin manifest;
9. run application and generic framework suites;
10. build and verify deterministic Codex and OpenClaw artifacts;
11. install and test each artifact in an isolated target runtime;
12. compare cross-runtime behavior and emit the readiness report;
13. prepare and verify a separate marketplace staging delta;
14. stop for explicit publication approval.

## 19. Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Instruction Modules are confused with Skills | Protect the distinction in Skill instructions, validators, pressure tests, and handoff schema |
| Reference usage mapping becomes technical binding | Limit product output to behavior-level need and reserve paths, loading, and Skill mapping for the Workbench |
| The assistant advances too quickly | Encode question limits, waiting points, revision states, and confirmation gates as invariants and tests |
| A draft is mistaken for approval | Require explicit artifact state and prohibit implicit finalization |
| Source GPT terminology leaks into the product | Contract tests enforce the approved terminology except when explaining migration |
| Example PDFs introduce unrelated domain behavior | Treat them only as analysis fixtures and exclude their raw files and domain content |
| Existing `vibe-coding-designer` behavior is copied wholesale | Reuse only framework and validation patterns; keep application behavior and tests independent |
| Rights or private metadata leak into release files | Package normalized derivatives only and enforce schema-v3 provenance plus application audit |
| Structural validation is mistaken for behavioral evidence | Report structural, deterministic, and runtime evidence separately |
| One runtime passes while the other is untested | Withhold `READY` and report the exact unverified runtime gate |

## 20. Completion Criteria

The conversion is complete only when:

- the source inventory and decisions are recorded without private paths;
- every invariant maps to an owning Skill/reference and test evidence;
- all seven Skills pass structural validation;
- deterministic tools pass unit and product tests;
- schema-v3 builds are reproducible and verifiable;
- Codex and OpenClaw discover and execute the packaged Skills;
- representative behavior matches across both runtimes;
- the machine-readable readiness report contains no required `FAIL` or
  `NOT VERIFIED` gate;
- the marketplace delta is prepared and verified without mutating the
  marketplace;
- publication remains pending until separately authorized.

The expected final classification is `PORTABLE`, but it remains only
`EXPECTED` until direct cross-runtime evidence exists.
