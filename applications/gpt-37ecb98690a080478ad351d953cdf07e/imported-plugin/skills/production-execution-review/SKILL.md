---
name: production-execution-review
description: Govern optional direct L3 production execution and review generated results against canonical scene intent, with explicit authorization, evidence-based status, provenance, and L2 fallback. Use for external generation actions, execution failures, job/result association, or production-result review.
---

# Production Execution & Result Review

L3 is optional and capability-dependent. Never represent a skill, static file, or local deterministic helper as an external production provider. Use a runtime-native or connected production tool only when it is actually available and authorized.

## Required gate
Before paid/credit-consuming generation, user-asset upload, or external job creation, explain the consequential action and obtain explicit approval. Authentication remains runtime/provider-owned; never ask the user to paste secrets into plugin files or outputs.

## Required references
Read RM-P04 and RM-P05 before execution-state or result-association decisions. Read RM-P03 when target capability is relevant. Result review requires RM-P01 and the creative references relevant to the dimensions being judged.

## Fallback and evidence
If L3 is unavailable, preserve L1 and offer L2. If execution fails, preserve canonical source, target export, known job metadata, and failure state. Never call partial generation complete. Never claim success without actual runtime evidence. Associate results to canonical scene + derived target request + external job ID when the runtime exposes identifiers.

Review generated results against canonical scene intent, including composition, camera, lighting, character performance, sound, continuity, and material production constraints.

## Requirement ownership
REQ-009, REQ-010, REQ-016, REQ-020, REQ-021, REQ-022, REQ-023, REQ-024, REQ-025, REQ-026, REQ-027


## Runtime-resolvable professional reference bindings
- `RM-P01` → `references/RM-P01_canonical_production_specification_standard.md`
- `RM-P03` → `references/RM-P03_target_capability_adaptation_standard.md`
- `RM-P04` → `references/RM-P04_production_execution_result_contract.md`
- `RM-P05` → `references/RM-P05_project_state_asset_provenance_standard.md`

Before making a claim governed by any required professional reference above, consult the exact bound file. If a required file cannot be accessed or its operational semantics cannot be consulted, surface `REFERENCE_CONSULTATION_UNVERIFIED`, identify the affected reference ID, preserve safe non-reference-dependent work, and do not claim reference-grounded conformance.
