---
name: director-orchestrator-state
description: Route Vibe StorySpirit Director requests, maintain canonical/derived project state, enforce human approvals, pause/resume continuity, and coordinate R5 preproduction, R6 project approval, rough cut, and final cut transitions. Use for new projects, resumes, ambiguous requests, workflow transitions, or state/provenance questions.
---

# Director Orchestrator & Project State

Own workflow routing and project-state semantics. Preserve the approved principle: **create and approve the Director project first; select a production target only when realization begins.**

## Routing
- Creative setup / new story → story-and-creative-development.
- Storyboard/camera/lighting/acting/sound or quality refinement → cinematic-direction-quality.
- Approved project → production-spec-packaging.
- L2 target request → target-capability-adaptation.
- L3 execution or result review → production-execution-review.
- `/generate_video_prompt` means modern target-aware derived export, not an irreversible canonical rewrite.
- `/export_package` means L1 portable production package unless the user explicitly selects another path.

## Canonical state
Maintain five conceptual categories: Canonical Director Project; Canonical Production Specification; Derived Target Export; External Production Job; Generated Production Result. Never let a derived target artifact silently replace canonical source state.

Before production realization, require an identifiable approved-for-production state. If upstream canonical intent changes, mark dependent artifacts `STALE` or `SUPERSEDED`.

## HITL gates
Wait for the user at Director Project approval, consequential degradation choices, consequential external action approval, and canonical-source revision decisions. Explicit approval is required before paid/credit-consuming generation, uploading user assets, or creating external jobs.

## Production-stage state and decisions
Use these names for the **Director production workflow**; they do not rename or replace SW-01 screenplay P7/P8 or any screenplay revision gate. Record the project and artifact revision, evidence, unresolved issues, decision, and decision owner at each stage. A later artifact must trace to its approved upstream source; an upstream change stales its dependent evidence and approval as appropriate. A gate is never inferred from a prior gate or a generated file.

| Stage | Decision rule and transition |
| --- | --- |
| **R5 — Preproduction Acceptance** | Review the locked screenplay and storyboard provenance; narrative clarity of cause, motive, visible action and timing; feasible blocking and spatial/contact action; prop continuity; and dialogue/voice timing with reaction pauses. A low-fidelity animatic, blocking previs, or timing sample may support feasibility within its stated limits. Hold for material clarity, physical feasibility, continuity, or timing gaps. Record `PASS`, `HOLD`, or `NEEDS_EVIDENCE` with specific issues. Do not require a finished video, final voice performance, or real-audience comprehension test for R5. |
| **R6 — Director Project Approval** | After R5 `PASS`, present its evidence, remaining risks, production scope, rights, and proposed plan to the owner for an explicit decision to enter video production. If R5 is `HOLD` or `NEEDS_EVIDENCE`, R6 remains pending. R5 `PASS` does not itself grant R6. Record the owner's approval or hold against the exact project revision. Paid generation, asset upload, and external jobs retain separate action authorization. |
| **Video Production — Rough Cut Review** | Route a watchable rough cut to production-execution-review for actual edit and audience evidence. Keep the rough-cut result and revision decisions separate from R5 and R6. |
| **Final Cut Acceptance** | Route the revised final cut to production-execution-review; require a separate owner acceptance of the final film after feedback disposition and quality/rights checks. R6 approval and Final Cut Acceptance never imply publication permission. |

For requests about whether an incomplete R5 can advance, distinguish a missing real-audience test (deferred to rough cut) from an unresolved R5 feasibility or Narrative Clarity Review finding (still blocking). Do not change an existing project's recorded gate status without current evidence and a decision at that gate.

## Reference requirement
For state, provenance, canonical/derived separation, asset relationships, or staleness decisions, **read `references/RM-P05_project_state_asset_provenance_standard.md` before deciding**. File presence is not consultation. If unavailable, disclose `REFERENCE_CONSULTATION_UNVERIFIED`.

## Deterministic helper
When command execution is available, use the bundled production engine for state/provenance checks. Do not claim runtime evidence when it did not execute.

## Requirement ownership
REQ-003, REQ-004, REQ-014, REQ-015, REQ-017, REQ-020, REQ-027


## Runtime-resolvable professional reference bindings
- `RM-P05` → `references/RM-P05_project_state_asset_provenance_standard.md`

Before making a claim governed by any required professional reference above, consult the exact bound file. If a required file cannot be accessed or its operational semantics cannot be consulted, surface `REFERENCE_CONSULTATION_UNVERIFIED`, identify the affected reference ID, preserve safe non-reference-dependent work, and do not claim reference-grounded conformance.

## SW-01 screenplay route and transfer
For new narrative requests, recommend Professional Screenplay and offer direct Quick Storyboard. Honor explicit Quick selection without SW screenplay gate. Route Professional, Fast Draft screenplay, imported script critique/bridge and scoped screenplay edits to professional-screenwriting; non-narrative music remains optional to screenplay. The Director Project remains top-level canonical source. Before professional P7/P8 storyboard transfer read the existing RM-P05 exact file and obtain current screenplay ID/revision plus exact owner proof and map. P8 only follows P7; pause, failed bridge and resume of P8 must re-enter P7 and revalidate. A changed script stales only affected downstream dependencies. Existing Director Project and external-action approvals remain separate.
For local deterministic P7/P8 checks, route through professional-screenwriting to the installed the bundled guard entrypoint specified in the runtime contract with `p7-check`, `p8-entry-check`, and `p8-draft-check` (bound tool IDs: screenplay-guard-p7, screenplay-guard-p8-entry, screenplay-guard-p8-draft) at their respective stages. P7 source/scene/beat coverage precedes P8 shot coverage; only P7 enters P8. Recheck current evidence on every P8 entry or resume, inspect structured status and issues, and do not infer a PASS if direct execution is unavailable.

## Exact local reference paths
- [RM-P05](references/RM-P05_project_state_asset_provenance_standard.md): read for approval, provenance, canonical revision, dependency staleness or professional P7/P8. Record actual access and task-specific application; if a required read fails, report `REFERENCE_CONSULTATION_UNVERIFIED` and block only its dependent claim.
