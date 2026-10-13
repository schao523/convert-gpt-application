# RM-P02 — Portable Production Package Standard
## Provider-Neutral Professional Reference for Human-Readable and Machine-Readable Production Handoff

**Reference ID:** RM-P02  
**Version:** 1.0-DRAFT  
**Status:** Professional Knowledge Reference — awaiting owner approval  
**Primary behavioral users:** WF-05/L1; IM-09; supporting IM-07, IM-08, IM-15  
**Depends on:** RM-P01 Canonical Production Specification Standard  
**Authority scope:** Semantic requirements for a portable production package that can be handed to humans, external tools, automation, websites, or future target adapters  
**Out of scope:** Provider-specific request formats, volatile target capabilities, authentication, runtime bindings, exact folder layout, archive technology

---

# 1. Purpose

RM-P02 defines the professional standard for packaging an approved Director Project and its canonical Production Specification into a **portable production package**.

The package must serve two audiences at the same time:

1. **Humans** — directors, editors, producers, collaborators, reviewers, and creators who need understandable production documents.
2. **Machines** — external applications, websites, scripts, adapters, automation, or future runtime capabilities that need structured production data.

The package must therefore be:

- human-readable;
- machine-readable;
- self-describing;
- traceable;
- asset-aware;
- version-aware;
- provider-neutral;
- resilient when some assets are external rather than embedded.

The package is the canonical **L1 production handoff**.

It must remain useful even if:

- no direct API exists;
- no target provider is selected;
- target providers change;
- the project is moved to another runtime;
- production continues manually.

---

# 2. Core Principle

A Portable Production Package is not merely:

> a folder containing Markdown files

and it is not merely:

> a serialized API request.

It is a **portable representation of the approved production project**, containing enough structured meaning and human-readable context to support downstream production without depending on one target platform.

The package must preserve:

> **creative intent + canonical production meaning + assets/dependencies + provenance + project state**

---

# 3. Package Roles

A complete portable production package should conceptually contain five artifact classes:

1. **Canonical project artifacts**
2. **Human-readable creative/production documents**
3. **Structured scene production artifacts**
4. **Assets and asset references**
5. **Package metadata and provenance**

Derived target-specific exports may also be included, but they must remain clearly separated from canonical artifacts.

---

# 4. Required Package Artifact Roles

The following roles are required for a complete L1 package.

The implementation may choose filenames and folders, but each semantic role must be represented.

---

## 4.1 Package Manifest

A package manifest is mandatory.

Its purpose is to answer:

- What is this package?
- Which project/version does it represent?
- What artifacts are included?
- Which artifacts are canonical?
- Which are derived?
- Which assets are embedded?
- Which are external?
- Which items are missing or pending?
- Which version of the specification produced the package?
- What is the package completeness state?

Minimum semantics should include:

- package identity;
- package version;
- project identity;
- project revision;
- package creation time;
- canonical Production Specification reference;
- artifact inventory;
- asset inventory or asset-manifest reference;
- provenance;
- package completeness state;
- optional validation result.

---

## 4.2 Canonical Project Representation

The package must contain or reference the canonical Director Project state sufficient to preserve:

- approved story/creative intent;
- approved storyboard state;
- style intent;
- current project revision;
- approval state;
- relationship to the Production Specification.

This may be represented as one or multiple artifacts.

The package must not rely only on derived target exports to reconstruct canonical intent.

---

## 4.3 Canonical Production Specification

A complete L1 package must contain the canonical Production Specification governed by RM-P01.

This is the machine-readable production source of truth.

It should include project-level production semantics and per-scene production semantics.

The package should not require a downstream consumer to reconstruct canonical meaning from prose prompts alone.

---

## 4.4 Scene Production Records

Each production-ready scene should have a structured, independently addressable scene production record.

A scene record should preserve at least:

- scene identity;
- scene revision;
- source Director Project revision;
- scene purpose;
- visual intent;
- motion intent;
- camera intent;
- performance intent;
- dialogue/narration intent;
- audio intent;
- duration;
- aspect ratio;
- generation-mode preference;
- Start Frame / End Frame references;
- reference assets;
- continuity requirements;
- dependencies;
- production-readiness state.

The physical representation may be:

- one file per scene;
- one structured collection;
- database export;
- another portable representation.

RM-P02 defines the semantics, not the exact storage format.

---

## 4.5 Human-Readable Production Guide

The package must include a human-readable overview that allows a producer or creator to understand how to use the package without inspecting machine-readable internals.

It should explain:

- project title and purpose;
- project revision;
- current approval/production state;
- scene count;
- visual style;
- expected delivery format;
- assets included;
- assets missing/pending;
- production path options;
- how canonical artifacts differ from target-specific exports;
- known limitations;
- how to proceed manually if no adapter/runtime capability is available.

This role may be fulfilled by a README, production guide, or equivalent artifact.

---

# 5. Recommended Human-Readable Creative Artifacts

Where relevant, a portable package should include readable creative documents such as:

- Storyboard;
- Cinematic Plan;
- Dialogue/Narration Script;
- Lighting/Mood Notes;
- Character Acting Notes;
- Sound/Music Notes;
- Visual Style Summary;
- Quality/Rubric Review;
- Revision Notes;
- Director Approval Summary.

These documents support human production workflows and creative review.

They are not substitutes for the canonical structured Production Specification.

---

# 6. Asset Manifest

A package containing or referencing assets must maintain an asset manifest or equivalent structured inventory.

Each asset record should conceptually identify:

- `asset_id`;
- asset role;
- media type;
- source/provenance;
- current revision/version;
- embedded/external/pending status;
- location reference;
- required/optional status;
- checksum or integrity identity when appropriate;
- usage constraints;
- related scenes;
- readiness state.

Common asset roles include:

- Start Frame;
- End Frame;
- character reference;
- location reference;
- prop/object reference;
- style reference;
- audio reference;
- voice reference;
- music;
- ambience;
- sound effect;
- subtitle file;
- generated intermediate;
- prior scene output.

---

# 7. Embedded vs External Assets

The portable package must support both embedded and externally referenced assets.

## 7.1 Embedded asset

An embedded asset physically travels with the package.

The package should preserve:

- stable asset identity;
- path/location;
- integrity information when appropriate;
- source/provenance.

## 7.2 External asset

An external asset is intentionally not included in the package.

Examples:

- cloud-hosted file;
- provider-hosted media;
- shared-drive file;
- licensed library content;
- large media stored separately.

The package must not pretend an external asset is embedded.

An external asset record should preserve enough information to identify or retrieve the asset where authorized.

## 7.3 Pending asset

A pending asset is required or desired but not yet available.

The package should explicitly represent pending state rather than omitting the dependency.

Recommended states:

- `EMBEDDED`
- `EXTERNAL`
- `PENDING`
- `MISSING`
- `STALE`
- `INVALID`

---

# 8. Dependency Manifest

The package should represent dependencies between scenes, assets, and production states.

A dependency record should conceptually identify:

- dependent scene/artifact;
- required resource;
- dependency type;
- required/optional status;
- current readiness;
- fallback if any.

Examples:

- Scene S04 requires the final frame of Scene S03.
- Scene S07 requires character reference CHAR-01.
- Scene S02 requires approved narration audio.
- Scene S05 cannot enter target adaptation until Start Frame IMG-S05-START exists.

Dependencies must not be inferred only from filenames.

---

# 9. Canonical and Derived Artifact Separation

A portable production package must distinguish:

## 9.1 Canonical artifacts

Examples:

- canonical Director Project;
- canonical Production Specification;
- canonical scene records;
- canonical style profile;
- canonical asset/dependency records.

## 9.2 Derived artifacts

Examples:

- Runway request;
- Veo target export;
- provider-specific prompt;
- provider-specific model parameters;
- delivery-specific resized asset;
- generated target preview;
- external job record.

Derived artifacts may be included for convenience, but must be clearly labeled as derived.

They must identify:

- source canonical project revision;
- source scene revision;
- target/provider/capability context;
- export creation time/version;
- current/stale status.

A derived artifact must never silently replace canonical production data.

---

# 10. Package Versioning

A portable production package must have an explicit version identity.

Recommended semantics include:

- `package_id`
- `package_revision`
- `project_revision`
- `production_spec_revision`
- package creation timestamp

A new package revision should be created when changes materially affect:

- canonical creative intent;
- canonical Production Specification;
- required assets;
- scene dependencies;
- production state;
- canonical provenance.

Minor cosmetic documentation edits may not require semantic project revision if they do not affect production meaning.

---

# 11. Package Completeness States

A package should expose a visible completeness state.

Recommended semantic states:

## 11.1 COMPLETE

All required canonical artifacts and required embedded/external asset references are present and valid for the intended L1 handoff.

## 11.2 COMPLETE_WITH_EXTERNAL_DEPENDENCIES

The package is usable, but some required assets are intentionally external and are correctly referenced.

## 11.3 PARTIAL

Canonical structure exists, but one or more required production dependencies are pending or missing.

## 11.4 INVALID

The package fails one or more structural or integrity requirements and should not be treated as a valid production handoff.

The completeness state is distinct from whether the project is ready for L2 or L3.

---

# 12. Minimum L1 Package Contract

A valid L1 package must include, at minimum:

1. package manifest;
2. project identity and revision;
3. canonical Production Specification;
4. structured scene production records;
5. human-readable production overview;
6. asset inventory;
7. dependency information;
8. provenance/version information;
9. package completeness state.

Creative documents should also be included when available and relevant.

---

# 13. Machine-Readable Manifest Semantics

The package manifest should be suitable for automated inspection.

An illustrative semantic example:

```yaml
package:
  package_id: PKG-001
  package_revision: 3
  created_at: 2026-10-06T18:00:00+08:00
  status: COMPLETE_WITH_EXTERNAL_DEPENDENCIES

project:
  project_id: PROJECT-001
  project_title: "The Returning Father"
  project_revision: 1.4
  production_spec_revision: 1.2
  approval_state: APPROVED_FOR_PRODUCTION

canonical_artifacts:
  production_spec: canonical/production-spec.yaml
  scene_records:
    - scenes/S01.yaml
    - scenes/S02.yaml
    - scenes/S03.yaml

human_readable:
  production_guide: README.md
  storyboard: creative/storyboard.md
  dialogue: creative/dialogue.md

assets:
  manifest: assets/asset-manifest.yaml

dependencies:
  manifest: dependencies.yaml

derived_outputs:
  - target: runway
    path: exports/runway/
    state: CURRENT
  - target: veo
    path: exports/veo/
    state: STALE
```

This example illustrates semantics only.

Implementations may use other structured formats.

---

# 14. Asset Integrity

Where technically appropriate, portable packages should preserve asset integrity.

Possible integrity mechanisms include:

- checksum;
- content hash;
- stable asset ID;
- immutable source identifier.

Integrity data is particularly useful when:

- the same asset is referenced across multiple scenes;
- external tools consume the package;
- project revisions may replace assets;
- generated outputs must be traced back to exact inputs.

RM-P02 does not mandate a particular hash algorithm.

---

# 15. Provenance Requirements

Each canonical artifact should preserve enough provenance to answer:

- Where did this come from?
- Which approved project revision produced it?
- Was it authored, imported, generated, or derived?
- Has it been modified since approval?
- Is it canonical or derived?

At package level, provenance should include:

- source project;
- source revision;
- producing application/specification version;
- package revision;
- creation time.

At asset level, provenance may additionally include:

- uploaded by user;
- generated by application;
- externally referenced;
- transformed from another asset.

---

# 16. Rights and Usage Metadata

When known and relevant, an asset record may preserve:

- rights owner;
- license;
- redistribution status;
- attribution requirement;
- usage restriction;
- privacy/confidentiality classification.

RM-P02 does not infer rights.

Unknown rights should remain unknown rather than being silently converted into permission.

The package should support carrying rights metadata forward into downstream production.

---

# 17. Missing Asset Behavior

A package must not silently omit a required asset dependency.

If a required asset is unavailable:

1. preserve the asset record;
2. mark readiness as `MISSING` or `PENDING`;
3. identify affected scene(s);
4. lower package or scene readiness appropriately;
5. provide recovery information where available.

Example:

```yaml
asset_id: IMG-S05-START
role: start_frame
status: MISSING
required: true
affects:
  - scene_id: S05
effect:
  l1_package: PARTIAL
  target_adaptation: BLOCKED_FOR_IMAGE_TO_VIDEO
```

---

# 18. External Reference Behavior

When external asset references are used, the package should distinguish between:

- human navigation reference;
- machine-retrievable reference;
- opaque provider asset ID;
- unavailable/private reference.

The package must not claim portability that depends on credentials or locations the recipient cannot access.

If access is environment-specific, that should be visible.

---

# 19. Package Validation Rules

The following validation rules are normative.

## PV-01 — Manifest presence

Every valid L1 package must include a package manifest or equivalent self-description.

## PV-02 — Canonical Production Specification presence

The package must contain or validly reference the canonical Production Specification.

## PV-03 — Scene addressability

Every production-ready scene must be addressable independently.

## PV-04 — Canonical/derived distinction

Canonical and target-derived artifacts must be distinguishable.

## PV-05 — Asset inventory

Every production-significant asset referenced by canonical scene records must appear in the asset inventory.

## PV-06 — Dependency integrity

Every required dependency must be represented explicitly.

## PV-07 — Missing-state honesty

Missing/pending assets must not be represented as ready.

## PV-08 — Revision/provenance

The package must expose enough revision/provenance information to identify its canonical source.

## PV-09 — Human usability

A producer should be able to understand how to use the package without reverse-engineering machine files.

## PV-10 — Machine usability

A downstream tool should be able to enumerate project, scenes, assets, dependencies, and canonical production semantics without parsing free-form prose as the sole source of truth.

---

# 20. Recommended Logical Package Structure

This is a recommended logical model, not a mandatory physical folder layout.

```text
ProductionPackage/
├── package-manifest
├── README / production-guide
│
├── canonical/
│   ├── project
│   ├── production-spec
│   └── scenes/
│
├── creative/
│   ├── storyboard
│   ├── dialogue
│   ├── cinematic-plan
│   ├── style
│   └── review-notes
│
├── assets/
│   ├── asset-manifest
│   ├── images/
│   ├── audio/
│   └── references/
│
├── dependencies/
│   └── dependency-manifest
│
└── exports/
    ├── target-A/
    └── target-B/
```

The implementation may choose another layout if the semantic roles remain intact.

---

# 21. Human Handoff Requirements

The package should support manual production even when no structured adapter is available.

A human producer should be able to determine:

- what each scene is supposed to achieve;
- what assets are required;
- which scenes are ready;
- what is missing;
- what the intended visual style is;
- where canonical information is located;
- which artifacts are target-specific;
- whether a target export is current or stale;
- how to continue production manually.

---

# 22. Machine Handoff Requirements

A downstream tool should be able to:

1. identify the project;
2. identify the current package revision;
3. enumerate scenes;
4. read canonical scene semantics;
5. enumerate assets;
6. resolve dependencies;
7. determine package completeness;
8. distinguish canonical vs derived outputs;
9. identify target-derived exports when present;
10. preserve provenance when creating new derived artifacts.

A machine consumer should not be forced to extract critical production semantics from Markdown prose using heuristic parsing.

---

# 23. Generic / Manual Production Export

A portable package should remain useful to production tools or websites without a formal adapter.

Therefore, an L1 package should support a generic/manual production view.

This may include:

- scene-by-scene production cards;
- Start Frame references;
- End Frame references;
- target-neutral motion instructions;
- target-neutral camera instructions;
- dialogue;
- audio cues;
- duration;
- aspect ratio;
- required assets;
- compatibility notes.

This allows the user to manually transfer scene inputs into a website while preserving the canonical project.

---

# 24. Relationship to L2 Target Exports

L2 target exports are **derived package artifacts**.

An L2 export should not require duplication of the entire canonical project.

Instead, it should reference:

- source project revision;
- source scene revision;
- target capability profile;
- target adaptation result;
- semantic degradation report;
- provider-specific assets/parameters where applicable.

If the canonical project changes, L2 outputs may become stale.

RM-P05 governs detailed stale/superseded state semantics.

---

# 25. Relationship to L3 Direct Execution

The L1 package is a prerequisite foundation for L3 but not dependent on it.

A direct-execution runtime may consume:

- canonical production scene;
- asset references;
- target adaptation output;
- user approval state.

The package itself should not embed secrets or authentication credentials.

External execution records belong to RM-P04/RM-P05 semantics.

---

# 26. Package Portability Levels

A useful professional distinction is:

## Level P1 — Human Portable

The package can be understood and manually used by another person.

## Level P2 — Machine Portable

The package exposes structured project, scene, asset, dependency, and provenance information.

## Level P3 — Adapter Ready

The package contains sufficient canonical production semantics for target-aware transformation.

## Level P4 — Execution Ready

The package plus required target/runtime capabilities and assets are sufficient for direct execution.

A good L1 Portable Production Package should normally satisfy at least:

> **P1 + P2 + P3**

P4 depends on runtime/external capability and is therefore not required for L1 completeness.

---

# 27. Anti-Patterns

## 27.1 Markdown-only package

Bad:

A ZIP containing only storyboard, dialogue, and generic prompts.

Why it fails:

- machine consumers cannot reliably identify canonical semantics;
- dependencies and state are implicit;
- provenance is weak.

## 27.2 Prompt archive

Bad:

One text file per scene containing provider-style prompts.

Why it fails:

- target coupling;
- no canonical production representation;
- poor portability.

## 27.3 Asset dumping

Bad:

A folder of images/audio without an asset manifest.

Why it fails:

- roles and scene relationships are ambiguous;
- versioning is unclear.

## 27.4 Hidden missing dependencies

Bad:

A package omits Start Frame S05 but still declares itself complete.

Correct:

Mark asset missing and reduce completeness/readiness.

## 27.5 Derived output as source of truth

Bad:

A Runway export becomes the only surviving scene representation.

Correct:

Keep the canonical Production Specification authoritative.

## 27.6 Credentials inside package

Bad:

API keys or provider secrets embedded in the portable archive.

Correct:

Keep authentication external to the portable package.

---

# 28. Recommended Package Completeness Example

```yaml
package_id: PKG-PROJECT-001-R4
status: COMPLETE_WITH_EXTERNAL_DEPENDENCIES

canonical:
  project_revision: 1.4
  production_spec_revision: 1.2
  scene_count: 8

assets:
  total: 14
  embedded: 9
  external: 4
  pending: 1

dependencies:
  required_total: 11
  ready: 10
  missing: 1

readiness:
  human_handoff: READY
  machine_handoff: READY
  target_adaptation:
    S01: READY
    S02: READY
    S03: READY
    S04: READY
    S05: BLOCKED_MISSING_START_FRAME
```

The package may still be valuable and valid even when one scene is not target-ready, provided the incomplete state is explicit.

---

# 29. Relationship to Other Production References

## RM-P01 — Canonical Production Specification Standard

RM-P01 defines the canonical production meaning.

RM-P02 packages that meaning for portable handoff.

## RM-P03 — Target Capability & Adaptation Standard

RM-P03 consumes canonical Production Specifications from the package and produces target-derived outputs.

## RM-P04 — Production Execution & Result Contract

RM-P04 defines direct execution lifecycle and result handling.

## RM-P05 — Project State, Asset & Provenance Standard

RM-P05 defines detailed identity, version, state, provenance, staleness, and asset lineage across canonical and derived artifacts.

---

# 30. Consultation Guidance for the Application

Consult RM-P02 whenever the application:

- generates `/export_package`;
- creates an L1 Portable Production Package;
- evaluates package completeness;
- determines whether assets should be embedded, external, pending, or missing;
- prepares a project for handoff;
- prepares canonical data for future adapters;
- validates whether a package is both human-readable and machine-readable;
- adds target-derived exports into a portable project archive.

Do not use RM-P02 as authority for:

- current provider capabilities;
- target-specific parameter syntax;
- API authentication;
- provider execution lifecycle.

Those belong to RM-P03/RM-P04 and current capability evidence.

---

# 31. Professional Standard Summary

A professional Portable Production Package should be:

- **self-describing**
- **human-readable**
- **machine-readable**
- **canonical-source preserving**
- **scene-addressable**
- **asset-aware**
- **dependency-aware**
- **version-aware**
- **provenance-aware**
- **rights-aware when metadata is available**
- **honest about missing resources**
- **provider-neutral**
- **adapter-ready**
- **portable without credentials**

The canonical question is not:

> “Did we put all the files into a ZIP?”

It is:

> **“Can another human or system correctly understand, validate, continue, adapt, and trace this production project without guessing what the files mean?”**
