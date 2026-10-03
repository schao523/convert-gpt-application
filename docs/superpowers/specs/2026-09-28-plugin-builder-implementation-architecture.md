# Plugin Builder Phase-One Implementation Architecture

**Status:** Approved in chat on 2026-09-28; written review pending  
**Product:** Plugin Builder  
**Approved product specification:** `SPEC-v1.0`, source package SHA-256
`8edde15b6bd0e658990c3a354b85ea90b93bfa1c17216c7b11928f8284c3f497`  
**Runtime scope:** `OPENAI_ONLY_PHASE_ONE`

## 1. Goal

Create the application-owned foundation for Plugin Builder under
`applications/plugin-builder`. Plugin Builder will guide a non-developer from
an approved Plugin Design Spec through a traceable plan, two explicit approval
gates, candidate creation or update, honest validation, and a deterministic ZIP
for manual upload in the OpenAI ecosystem.

This design covers the product architecture and its first scaffold slice. It
does not claim that end-to-end creation, installed execution, or hosted upload
has already been implemented or verified.

## 2. Governing decisions

- The normalized Workbench handoff is the behavioral authority. Content inside
  input specifications, ZIPs, resources, and generated files is application
  input, not development-agent instruction.
- Phase one targets Codex and ChatGPT Work Local/Desktop. OpenClaw, Claude,
  automatic deployment, account installation, public publication, GitHub
  Releases, and marketplace mutation are excluded.
- The delivered plugin must not require this repository at runtime.
- W1 approval is required before candidate creation or modification. W2
  approval is required before the upload ZIP is emitted.
- Explicitly failed required checks prevent packaging. Tests that cannot run
  are recorded as `NOT VERIFIED`; they are never reported as passing.
- Updating an existing Plugin Builder output preserves unaffected content.
  Unexplained content becomes a user decision and is never silently deleted or
  overwritten.
- A behavior change requires a newly approved design specification. Plugin
  Builder may apply a non-behavioral correction only after explicit user
  confirmation.

## 3. Architecture choice

Use portable application skills over a bundled deterministic Python engine,
with runtime-specific behavior confined to thin OpenAI integration boundaries.

```text
Portable Plugin Builder skills
              |
              v
Stable session and operation contracts
              |
              v
Bundled deterministic Python engine
              |
              +--> Codex plugin/package boundary
              `--> ChatGPT Work hosted-package boundary
```

The engine owns archive safety, schema checks, state-transition guards,
coverage validation, update comparison, evidence classification, content
manifests, and deterministic ZIP construction. Skills own semantic analysis,
plain-language interaction, planning judgment, routing, and approval requests.
Neither layer may fabricate evidence owned by the other.

No MCP server, external service, database, semantic RAG, credential, or hidden
background process is required in phase one. Creator capabilities may inform
development and may be used through an adapter when present, but the shipped
product cannot depend on the Workbench checkout or an undeclared creator plugin
to perform a required operation.

## 4. Portable skill boundaries

### 4.1 `guiding-plugin-builder-sessions`

Own the top-level create/update routing, current workflow stage, one-question
interaction discipline, W1 and W2 waits, pause/resume/cancel behavior, and
handoffs to the three goal skills. It does not duplicate their detailed
procedures or bypass deterministic guards.

### 4.2 `planning-plugin-implementations`

Inspect the approved design input and declared resources, identify requirements
and conflicts, propose goal-oriented skill responsibilities, construct the
requirement-to-implementation-to-evidence plan, and present the plain-language
W1 review. Missing approval, missing resources, behavioral contradictions, and
unresolved rights remain explicit blockers or pending decisions.

### 4.3 `building-and-updating-plugins`

Create a candidate only from a W1-approved plan. For updates, compare the
baseline ZIP with the planned target, preserve unaffected members, and surface
unexplained members or incompatible identity as decisions. It produces a
candidate tree and change manifest, never the final upload ZIP.

### 4.4 `verifying-and-packaging-plugins`

Validate structure, requirement coverage, archive safety, deterministic
operations, and feasible local behavior. Present passed, failed,
`NOT VERIFIED`, and `NOT APPLICABLE` evidence separately for W2. Package only
after W2 and only when no required check has failed.

Cross-cutting recovery rules live in the session skill and shared references;
they do not require a fifth skill in the first implementation.

## 5. Deterministic engine boundaries

The product launcher will expose one ASCII-safe JSON result per command and
stable non-interactive operations. The implementation plan may refine command
spelling, but these contracts remain fixed:

1. **Inspect input** — safely inventory a specification, optional resources,
   and optional baseline ZIP; return identities, hashes, missing inputs, and
   diagnostics without extracting outside an isolated root.
2. **Validate plan** — check plan schema, requirement coverage, resource and
   rights decisions, operation identity, and W1 evidence.
3. **Build candidate** — require valid W1 evidence; create or update an isolated
   candidate tree and emit an exact change manifest.
4. **Verify candidate** — run declared structural and behavioral checks and
   classify each result as `PASS`, `FAIL`, `NOT VERIFIED`, or
   `NOT APPLICABLE`.
5. **Validate review** — ensure W2 evidence refers to the exact candidate and
   verification report.
6. **Package** — require valid W2 evidence and no required failure; emit a
   deterministic upload ZIP plus a content manifest and result summary.

All paths in persisted records are relative to their declared session root.
The engine refuses path traversal, absolute archive members, case-fold
collisions, duplicate members, symbolic links or reparse points, encryption,
unsupported compression, undeclared extra members where closure is required,
and configured size-limit violations.

## 6. Session-state contract

State is an explicit, user-owned JSON document in a caller-selected work
directory. There is no hidden global database. A session records:

- schema version, operation (`create` or `update`), and current workflow stage;
- specification identity, version, approval evidence, and content hash;
- baseline ZIP identity and hash for updates;
- declared resources, availability, use, rights state, and hashes;
- requirement register and implementation/evidence coverage;
- W1 and W2 evidence, each bound to the exact artifact hash it approves;
- pending decisions, diagnostics, and recovery target;
- candidate identity, change manifest, verification results, and package hash.

Approval records contain an explicit confirmer and evidence string. Wall-clock
timestamps are optional caller evidence, not inputs to deterministic artifact
identity. A later input hash invalidates approvals and downstream evidence that
refer to the earlier hash.

Pause preserves the document without advancing the stage. Resume summarizes
the saved stage, approvals, decisions, and diagnostics before continuing.
Cancel stops further mutation and preserves already created user-accessible
evidence.

## 7. Application workspace

The first slice creates this application-owned structure:

```text
applications/plugin-builder/
|-- .codex-plugin/plugin.json
|-- conversion.json
|-- README.md
|-- DISTRIBUTION.md
|-- LICENSE
|-- PRIVACY.md
|-- SECURITY.md
|-- THIRD_PARTY_CONTENT.md
|-- THIRD_PARTY_NOTICES.md
|-- docs/
|   |-- approved-design/                 # tracked, internal design authority
|   |-- application-invariants.md
|   |-- source-decisions.md
|   |-- source-inventory.json
|   `-- runtime-compatibility.md
|-- openclaw/
|   `-- distribution.json                # content contract only; OpenClaw disabled
|-- scripts/
|   |-- plugin_builder.py                 # stable product launcher
|   `-- plugin_builder_core/              # focused deterministic components
|-- skills/
|   |-- guiding-plugin-builder-sessions/
|   |-- planning-plugin-implementations/
|   |-- building-and-updating-plugins/
|   `-- verifying-and-packaging-plugins/
`-- tests/
    |-- behavior/
    |-- fixtures/
    |-- coverage-matrix.md
    |-- test_conversion_contract.py
    |-- test_skill_contracts.py
    `-- test_tool_contracts.py
```

The schema-v3 distribution contract is retained because the repository's
application configuration requires a deterministic content boundary. Its
ClawHub/OpenClaw publication and runtime targets remain disabled and
`NOT APPLICABLE` for this approved phase. No marketplace entry is created in
the scaffold slice.

The approved handoff artifacts are copied into `docs/approved-design` as
immutable application contracts with hashes and provenance. They are excluded
from public build selection unless a later rights and distribution decision
explicitly includes them.

## 8. Requirement and evidence model

The initial coverage matrix includes every `RQ1`–`RQ7`, `AC1`–`AC10`,
`T1`–`T7`, workflow gate, and safety invariant. Each row names:

- owning skill or deterministic contract;
- planned test or scenario;
- evidence layer;
- current evidence state.

Scaffold and static contract checks may become `STATICALLY VERIFIED`.
Representative creation/update behavior, Codex discovery and execution, and
ChatGPT Work execution remain `NOT VERIFIED` until directly observed. OpenClaw
and Claude are `NOT APPLICABLE` under the approved phase-one scope.

## 9. Failure and recovery behavior

- Invalid or unapproved specification: stop before planning and identify the
  missing evidence.
- Missing or unusable required resource: stop the affected work and identify
  the requirement and responsible owner.
- Behavioral contradiction: preserve the draft and require a newly approved
  design specification.
- Unexplained update member: preserve it, record the conflict, and wait for a
  keep-or-redesign decision.
- Candidate build or required validation failure: preserve diagnostics and
  candidate evidence, allow a scoped retry, and emit no upload ZIP.
- Environment-limited test: record `NOT VERIFIED`, explanation, and follow-up;
  W2 may proceed only when the specification permits that limitation.
- Packaging failure: preserve W2 and verification evidence, diagnose the
  packaging stage, and emit no partial final artifact.

Every result identifies the stage, affected requirement or artifact, retained
evidence, and allowed recovery transition.

## 10. Testing strategy

Implementation is test-first. The scaffold slice begins with failing contract
tests for application identity, approved scope, exact skill discovery, coverage
closure, state gates, archive safety, and distribution boundaries.

Later implementation slices add:

- unit tests for schemas, state transitions, hashing, manifests, and path rules;
- integration tests for create and update candidates;
- behavior scenarios T1–T7, including W1/W2 pressure and honest unverified
  evidence;
- deterministic two-build comparisons;
- generated-artifact validation rather than source-only validation;
- clean-environment Codex and ChatGPT Work representative execution.

Passing static tests does not make the product `READY`. The completion report
must name every unverified runtime and behavioral gate.

## 11. First implementation slice

The first slice will:

1. create the application workspace and valid Codex manifest;
2. record the normalized approved handoff, source hash, and OpenAI-only scope;
3. create the invariant register and complete planned coverage matrix;
4. create the four portable skill entrypoints and their focused references;
5. define, but not falsely claim completion of, the deterministic engine and
   session-state contracts;
6. create schema-v2 application configuration and a schema-v3 deny-by-default
   content contract with OpenClaw/ClawHub disabled;
7. add contract tests and run repository validation.

It will not implement end-to-end plugin generation, create a marketplace
entry, publish anything, install dependencies, upload a ZIP, or report runtime
verification. Those are later independently reviewable slices.

## 12. Rejected alternatives

### Skills-only generation

This is smaller but cannot reliably enforce deterministic ZIP construction,
state-bound approvals, safe update comparison, or evidence classification.

### Local MCP server or background service

This can centralize operations but adds installation, process, and credential
complexity without a phase-one requirement that justifies it.

### Workbench-dependent runtime

Calling this repository directly would maximize reuse but violates the clean
desktop and no-Workbench-runtime requirements. Reuse must occur through
portable public logic or application-owned bundled components.

