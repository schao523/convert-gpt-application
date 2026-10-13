---
name: director-orchestrator-state
description: Route Vibe StorySpirit Director requests, maintain canonical/derived project state, enforce human approvals, pause/resume continuity, and coordinate the full creation-to-production workflow. Use for new projects, resumes, ambiguous requests, workflow transitions, or state/provenance questions.
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

## Reference requirement
For state, provenance, canonical/derived separation, asset relationships, or staleness decisions, **read `references/RM-P05_project_state_asset_provenance_standard.md` before deciding**. File presence is not consultation. If unavailable, disclose `REFERENCE_CONSULTATION_UNVERIFIED`.

## Deterministic helper
When command execution is available, use the bundled production engine for state/provenance checks. Do not claim runtime evidence when it did not execute.

## Requirement ownership
REQ-003, REQ-004, REQ-014, REQ-015, REQ-017, REQ-020, REQ-027


## Runtime-resolvable professional reference bindings
- `RM-P05` → `references/RM-P05_project_state_asset_provenance_standard.md`

Before making a claim governed by any required professional reference above, consult the exact bound file. If a required file cannot be accessed or its operational semantics cannot be consulted, surface `REFERENCE_CONSULTATION_UNVERIFIED`, identify the affected reference ID, preserve safe non-reference-dependent work, and do not claim reference-grounded conformance.
