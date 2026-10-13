---
name: production-spec-packaging
description: Convert an approved Director Project into a provider-neutral canonical Production Specification, plan assets/dependencies, and generate or validate a portable L1 production package. Use for production readiness, /export_package, canonical specs, asset planning, or package completeness.
---

# Production Specification & Packaging

Only create a canonical Production Specification from an identifiable approved Director Project. The specification is provider-neutral and records scene intent, continuity, assets, visual/camera/performance/audio requirements, constraints, acceptance intent, and provenance without choosing a provider.

## Required consultation
- Canonical Production Specification and asset planning: read RM-P01 and RM-P05.
- L1 portable production package: read RM-P02 and RM-P05.
- Consult RM-C08 or other creative references only when preserving an approved creative parameter requires it.

## L1 behavior
`/export_package` defaults to L1: produce a human-readable package plus machine-readable structured artifacts when file creation is available. L1 must not require provider APIs, credentials, or target selection. Validate completeness against RM-P02. Preserve canonical source/version identifiers in every derived package.

## Deterministic helper
When executable runtime is available, use the bundled engine for asset, package-completeness, staleness, and provenance checks. Otherwise report those runtime checks as NOT VERIFIED; do not invent a pass.

## Requirement ownership
REQ-005, REQ-006, REQ-007, REQ-011, REQ-014, REQ-015, REQ-018, REQ-021, REQ-022, REQ-023, REQ-024, REQ-025, REQ-027


## Runtime-resolvable professional reference bindings
- `RM-P01` → `references/RM-P01_canonical_production_specification_standard.md`
- `RM-P02` → `references/RM-P02_portable_production_package_standard.md`
- `RM-P05` → `references/RM-P05_project_state_asset_provenance_standard.md`

Before making a claim governed by any required professional reference above, consult the exact bound file. If a required file cannot be accessed or its operational semantics cannot be consulted, surface `REFERENCE_CONSULTATION_UNVERIFIED`, identify the affected reference ID, preserve safe non-reference-dependent work, and do not claim reference-grounded conformance.
