---
name: target-capability-adaptation
description: Resolve current production-target capabilities and derive target-aware L2 exports without modifying the canonical Vibe StorySpirit project. Use for Runway, Pika, Veo, Kaiber, or other target-specific export, compatibility, degradation, or provider comparison requests.
---

# Target Capability & Adaptation

Operate only after the canonical Director Project / Production Specification exists. Target adaptation creates a **derived** artifact; it never becomes canonical merely because it is provider-ready.

## Capability-oriented adapter
Resolve requirements by capability class (image/video input, reference conditioning, camera controls, duration, audio, seed/consistency, edit/extend, resolution/aspect ratio, etc.) before applying provider-specific syntax. Avoid hard-coded provider assumptions.

## Required consultation and current evidence
Read RM-P03 for every target capability/adaptation/compatibility decision. Use RM-P01 when mapping canonical production intent and RM-P05 for provenance/state. Static packaged references are **not** current provider capability evidence. When target-specific facts matter, use an available current authoritative/provider/runtime source. If current evidence cannot be established, return `TARGET_CAPABILITY_UNVERIFIED` and avoid fabricated transformations.

Classify each material requirement as `FULLY_SUPPORTED`, `PARTIALLY_SUPPORTED`, or `UNSUPPORTED`. If degradation materially changes approved intent, explain the consequence and wait for user choice. Preserve target-export provenance.

When executable runtime is available, use the bundled compatibility/provenance helpers for deterministic classification plumbing after capability evidence has been established.

## Requirement ownership
REQ-008, REQ-011, REQ-012, REQ-013, REQ-018, REQ-021, REQ-022, REQ-023, REQ-024, REQ-025, REQ-026, REQ-027, REQ-028


## Runtime-resolvable professional reference bindings
- `RM-P01` → `references/RM-P01_canonical_production_specification_standard.md`
- `RM-P03` → `references/RM-P03_target_capability_adaptation_standard.md`
- `RM-P05` → `references/RM-P05_project_state_asset_provenance_standard.md`

Before making a claim governed by any required professional reference above, consult the exact bound file. If a required file cannot be accessed or its operational semantics cannot be consulted, surface `REFERENCE_CONSULTATION_UNVERIFIED`, identify the affected reference ID, preserve safe non-reference-dependent work, and do not claim reference-grounded conformance.
