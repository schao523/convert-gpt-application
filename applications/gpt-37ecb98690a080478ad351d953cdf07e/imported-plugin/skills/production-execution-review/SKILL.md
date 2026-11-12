---
name: production-execution-review
description: Govern optional direct L3 production execution and review generated results, rough cuts, audience comprehension evidence, and final cuts against canonical scene intent. Use for external generation actions, execution failures, job/result association, rough-cut review, or final-film acceptance.
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

## Rough cut and final cut review
The Director workflow's R5 Preproduction Acceptance uses **Narrative Clarity Review** of screenplay, storyboard, blocking, and optional low-fidelity previs to judge whether cause and effect can be communicated. A hypothetical viewer response at R5 is a design judgment, not an Audience Comprehension Test. Do not fail R5 solely because actual viewers have not seen a produced video. Escalate unresolved narrative clarity, blocking, prop, or voice-timing feasibility to R5 as actual preproduction issues.

At **Video Production — Rough Cut Review**, require a watchable cut with actual picture, edit, sound, and relevant subtitles. Inspect intended scene causality, action, emotion, pacing, voice, continuity, and message on the intended viewing device where applicable. Run an **Audience Comprehension Test** with real viewers who did not participate in production: let them watch independently, ask what happened, why, what they felt and understood, and record observations or misunderstandings against cut revision and scene/timecode. Give special attention to a project's critical rescue/action sequence, kindness or other causal chain, and ending message when present; use project-specific scene IDs rather than assuming SC06/SC08 exist in every project. Record sample and method, issues, and revision decisions. If no real viewers have watched the cut, label audience comprehension `NOT_TESTED` and keep rough-cut review open; do not substitute creator predictions or static storyboard review.

At **Final Cut Acceptance**, compare the revised film with canonical intent and the accepted production specification, check picture, sound, subtitles, continuity, rights and outstanding risks, and trace every material rough-cut and audience finding to a correction or an explicit reasoned retention. If evidence or disposition is missing, mark `HOLD` or `NEEDS_EVIDENCE`. Present the actual final cut and its evidence for the owner's separate acceptance; do not claim acceptance from an R6 project approval, a completed generation job, or an internal review alone. Publishing or sharing outside the project requires its own authorization.

Keep these stage records distinct: R5 feasibility/clarity evidence, R6 owner project approval, rough-cut viewer observations and decisions, final-cut quality/disposition and owner acceptance. Cite the exact revision and actual evidence behind each status; never invent a viewing, viewer count, tool run, or approval. Continue to consult the bound RM-P04/RM-P05 and relevant creative references for their governed decisions; these stage rules do not replace those reads.

## Requirement ownership
REQ-009, REQ-010, REQ-016, REQ-020, REQ-021, REQ-022, REQ-023, REQ-024, REQ-025, REQ-026, REQ-027


## Runtime-resolvable professional reference bindings
- `RM-P01` → `references/RM-P01_canonical_production_specification_standard.md`
- `RM-P03` → `references/RM-P03_target_capability_adaptation_standard.md`
- `RM-P04` → `references/RM-P04_production_execution_result_contract.md`
- `RM-P05` → `references/RM-P05_project_state_asset_provenance_standard.md`

Before making a claim governed by any required professional reference above, consult the exact bound file. If a required file cannot be accessed or its operational semantics cannot be consulted, surface `REFERENCE_CONSULTATION_UNVERIFIED`, identify the affected reference ID, preserve safe non-reference-dependent work, and do not claim reference-grounded conformance.

## Exact local reference paths
- [RM-C02](references/RM-C02_camera_techniques_glossary.md): read for camera movement, technique or viewpoint selection/review. Record actual access and task-specific application; if a required read fails, report `REFERENCE_CONSULTATION_UNVERIFIED` and block only its dependent claim.
- [RM-C03](references/RM-C03_storyboard_composition_reference.md): read for shot composition, framing or storyboard spatial design. Record actual access and task-specific application; if a required read fails, report `REFERENCE_CONSULTATION_UNVERIFIED` and block only its dependent claim.
- [RM-C04](references/RM-C04_cinematic_lighting_mood_reference.md): read for lighting, exposure or expressive mood-lighting design/review. Record actual access and task-specific application; if a required read fails, report `REFERENCE_CONSULTATION_UNVERIFIED` and block only its dependent claim.
- [RM-C05](references/RM-C05_character_acting_reference.md): read for gesture, expression or acting performance direction/review. Record actual access and task-specific application; if a required read fails, report `REFERENCE_CONSULTATION_UNVERIFIED` and block only its dependent claim.
- [RM-C06](references/RM-C06_sound_music_cues_reference.md): read for sound layer, music cue or sonic storytelling design/review. Record actual access and task-specific application; if a required read fails, report `REFERENCE_CONSULTATION_UNVERIFIED` and block only its dependent claim.
- [RM-P01](references/RM-P01_canonical_production_specification_standard.md): read for canonical scene/production semantics, including professional P8 bridge; consult without forcing L1 export. Record actual access and task-specific application; if a required read fails, report `REFERENCE_CONSULTATION_UNVERIFIED` and block only its dependent claim.
- [RM-P03](references/RM-P03_target_capability_adaptation_standard.md): read for L2/L3 target capability, adaptation or degradation judgment; verify current provider evidence separately. Record actual access and task-specific application; if a required read fails, report `REFERENCE_CONSULTATION_UNVERIFIED` and block only its dependent claim.
- [RM-P04](references/RM-P04_production_execution_result_contract.md): read for L3 external job lifecycle, execution-state evidence or generated result review. Record actual access and task-specific application; if a required read fails, report `REFERENCE_CONSULTATION_UNVERIFIED` and block only its dependent claim.
- [RM-P05](references/RM-P05_project_state_asset_provenance_standard.md): read for approval, provenance, canonical revision, dependency staleness or professional P7/P8. Record actual access and task-specific application; if a required read fails, report `REFERENCE_CONSULTATION_UNVERIFIED` and block only its dependent claim.
