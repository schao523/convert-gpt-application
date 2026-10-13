# RM-P05 — Project State, Asset & Provenance Standard
## Provider-Neutral Professional Reference for Canonical State, Asset Identity, Revision Lineage, Staleness, and Production Provenance

**Reference ID:** RM-P05  
**Version:** 1.0-DRAFT  
**Status:** Professional Knowledge Reference — awaiting owner approval  
**Primary behavioral users:** WF-04, WF-05, WF-06; IM-07, IM-08, IM-09, IM-13, IM-15  
**Depends on:** RM-P01 Canonical Production Specification Standard; RM-P02 Portable Production Package Standard; RM-P03 Target Capability & Adaptation Standard; RM-P04 Production Execution & Result Contract  
**Authority scope:** Project identity, revision lineage, canonical/derived state, asset identity, provenance chains, stale/superseded rules, dependency lineage, execution/result association, lifecycle integrity  
**Out of scope:** Exact storage technology, database schema, provider API schema, authentication, file-system layout, runtime-specific persistence implementation

---

# 1. Purpose

RM-P05 defines the professional state-management and provenance standard for **酷 Vibe 動畫故事導演 Vibe StorySpirit Director**.

Its purpose is to make every important production artifact answerable in terms of:

- **what it is;**
- **which canonical source it came from;**
- **which revision it represents;**
- **whether it is still current;**
- **which assets and dependencies it used;**
- **what transformations occurred;**
- **which external execution or result it belongs to;**
- **whether it has been superseded, invalidated, or accepted.**

RM-P05 prevents the production system from collapsing into a set of loosely related files with unclear version relationships.

---

# 2. Core Principle

The project must maintain a clear distinction between:

> **canonical source state**  
> and  
> **derived production state**

The lineage must remain traceable across:

> **Director Project**  
> → **Canonical Production Specification**  
> → **Portable Production Package**  
> → **Target Export**  
> → **Execution Request**  
> → **External Job**  
> → **Generated Result**  
> → **Production Review Decision**

Every downstream artifact must be traceable back to the canonical source revision that produced it.

---

# 3. Canonical vs Derived State

## 3.1 Canonical state

Canonical state represents approved or authoritative project meaning.

Canonical artifacts may include:

- Director Project;
- Canonical Production Specification;
- canonical scene records;
- canonical style profile;
- canonical continuity requirements;
- canonical asset/dependency records.

Canonical state should only change through an explicit project revision path.

## 3.2 Derived state

Derived state is created from canonical state for a specific production purpose.

Derived artifacts may include:

- Portable Production Package;
- target-specific export;
- provider-specific prompt;
- execution request;
- external job record;
- generated media result;
- post-production derivative;
- review artifact.

Derived artifacts must not silently become canonical.

---

# 4. Stable Identity

Every major project entity should have a stable identity that does not depend solely on filename or current location.

Recommended identities include:

- `project_id`
- `scene_id`
- `asset_id`
- `production_spec_id`
- `package_id`
- `target_export_id`
- `execution_request_id`
- `external_job_id`
- `result_id`

The physical representation is implementation-specific.

Stable identity enables lineage across:

- renames;
- folder moves;
- target exports;
- retries;
- regenerated outputs;
- package revisions.

---

# 5. Revision Identity

Identity and revision are different.

Example:

```text
scene_id = S03
scene_revision = 4
```

This means:

> the same logical scene, fourth canonical revision.

A new revision should not receive a new logical identity merely because its content changed.

A new identity is appropriate when the entity is logically distinct.

---

# 6. Revision Semantics

A revision should be created when a change materially affects production meaning.

Examples:

- dialogue changed;
- camera direction changed;
- scene purpose changed;
- Start Frame changed;
- character continuity changed;
- duration changed;
- canonical asset changed;
- production requirement changed.

A revision may not be necessary for:

- spelling correction in explanatory prose;
- formatting-only changes;
- filename cleanup that preserves semantic identity.

---

# 7. Canonical Project State

Recommended project-level semantic states:

## 7.1 DRAFT

Creative/production content remains under development.

## 7.2 REVIEWED

The project has undergone review but is not yet approved for production.

## 7.3 APPROVED_FOR_PRODUCTION

The project is approved as the canonical source for production realization.

## 7.4 REVISED_AFTER_APPROVAL

The approved source has changed after approval.

Downstream derived artifacts based on the earlier revision may now be stale.

## 7.5 SUPERSEDED

A newer canonical revision has replaced this revision for active production.

## 7.6 ARCHIVED

Retained for history, not current production.

These states may be represented differently by implementation, but the semantics should be preserved.

---

# 8. Canonical Production Specification State

The canonical Production Specification should track:

- project revision;
- production-spec revision;
- source Director Project revision;
- approval relationship;
- currentness.

Recommended states:

- `DRAFT`
- `CURRENT`
- `STALE`
- `SUPERSEDED`
- `INVALID`

A Production Specification becomes `STALE` when its source Director Project changes materially.

---

# 9. Derived Artifact State

Target exports, packages, and similar artifacts should use derived-state semantics.

Recommended values:

- `CURRENT`
- `STALE`
- `SUPERSEDED`
- `INVALID`
- `FAILED`
- `PARTIAL`

The implementation may add other states, but should not collapse stale and invalid into one concept.

---

# 10. Stale vs Superseded

These terms have distinct meanings.

## 10.1 STALE

The artifact was valid when created, but its upstream source changed.

Example:

> Runway Export R2 was created from Scene S03 revision 2.  
> Scene S03 is now revision 3.

R2 is stale.

## 10.2 SUPERSEDED

A newer derived artifact intentionally replaces an older one.

Example:

> Runway Export R3 replaces R2.

R2 may be marked superseded.

A stale artifact is not automatically superseded until a replacement exists.

---

# 11. Invalid State

An artifact is `INVALID` when it cannot be considered a valid production artifact.

Examples:

- required fields missing;
- checksum mismatch;
- broken asset reference;
- malformed package;
- source relationship cannot be established.

Invalid is stronger than stale.

A stale artifact may still be useful for history.

An invalid artifact may not be safe to use.

---

# 12. Provenance Chain

Every significant derived artifact should preserve a provenance chain.

Minimum lineage:

```text
Project
→ Scene
→ Production Specification
→ Target Export
→ Execution Request
→ External Job
→ Result
```

A portable package may fit between Production Specification and Target Export.

Each link should preserve:

- source identity;
- source revision;
- transformation type;
- timestamp;
- producer/application;
- target context when applicable.

---

# 13. Provenance Record

A provenance record should conceptually include:

- artifact identity;
- artifact revision;
- source artifact identity;
- source revision;
- transformation type;
- producing component/application;
- timestamp;
- target identity if applicable;
- approval or review state if relevant.

Illustrative:

```yaml
artifact:
  id: EXP-S03-RUNWAY-R3
  type: target_export
  revision: 3

source:
  project_id: PROJECT-01
  project_revision: 1.4
  scene_id: S03
  scene_revision: 4
  production_spec_revision: 2

transformation:
  type: target_adaptation
  target: runway
  capability_profile_revision: 2026-10-06

state:
  currentness: CURRENT
```

---

# 14. Asset Identity

Every production-significant asset should have a stable asset identity.

Asset identity should be independent from:

- filename;
- folder;
- URL;
- temporary provider location.

Recommended conceptual fields:

- `asset_id`
- media type;
- logical role;
- revision;
- source;
- current location/reference;
- integrity information;
- state.

---

# 15. Asset Roles

Common asset roles include:

- Start Frame;
- End Frame;
- character reference;
- location reference;
- prop reference;
- style reference;
- source video;
- motion reference;
- voice reference;
- dialogue audio;
- ambience;
- music;
- sound effect;
- generated clip;
- intermediate render;
- subtitle track;
- final composite.

An asset may have multiple roles, but roles should be explicit.

---

# 16. Asset Revision

Assets should support revision semantics.

Example:

```text
asset_id = IMG-S03-START
revision = 2
```

If Start Frame revision 2 replaces revision 1, downstream target exports using revision 1 may become stale.

The asset identity remains stable if it represents the same logical production role.

---

# 17. Asset State

Recommended asset states:

- `READY`
- `PENDING`
- `MISSING`
- `STALE`
- `SUPERSEDED`
- `INVALID`
- `UNRESOLVABLE`
- `EXTERNAL`
- `ARCHIVED`

The exact representation is implementation-specific.

---

# 18. Asset Integrity

Where appropriate, asset provenance should preserve integrity information.

Possible mechanisms:

- content hash;
- checksum;
- provider asset ID;
- immutable storage identifier.

Integrity is useful when:

- external execution depends on exact media;
- the same asset is used across scenes;
- asset replacement can invalidate downstream work;
- package validation is required.

RM-P05 does not require a specific hash algorithm.

---

# 19. Asset Provenance

An asset provenance record should answer:

- who/what created it;
- whether it was uploaded, generated, imported, transformed, or externally referenced;
- source asset if derived;
- source revision;
- creation time;
- current revision;
- rights/usage metadata when known.

---

# 20. Derived Asset Lineage

Generated or transformed assets should preserve parent relationships.

Example:

```text
IMG-S03-START
→ VIDEO-S03-RUNWAY-01
→ VIDEO-S03-UPSCALED-01
→ VIDEO-S03-FINAL-COLOR-01
```

Each derivative should identify its parent.

---

# 21. Dependency Lineage

A dependency is a relationship between production entities.

Examples:

- Scene S05 depends on Start Frame IMG-S05-START.
- Scene S04 depends on prior result VIDEO-S03-ACCEPTED.
- Target export EXP-S07 depends on character reference CHAR-01-R3.

Dependencies should identify:

- source;
- target;
- dependency type;
- required/optional status;
- revision;
- readiness.

---

# 22. Dependency Invalidations

If an upstream dependency changes, downstream entities may become stale.

Example:

```text
CHAR-01 revision 2 → revision 3
```

Affected:

- Scene S02 target export using revision 2
- Scene S03 execution request using revision 2
- Generated clip derived from revision 2

These are not necessarily invalid, but may be stale relative to current canonical state.

---

# 23. Invalidation Rules

A professional implementation should establish deterministic invalidation rules.

Typical invalidation triggers:

- canonical scene revision changes;
- Start Frame changes;
- character reference changes;
- required dialogue changes;
- target capability profile materially changes;
- accepted degradation decision changes;
- target export regenerated.

The implementation may define precise rules, but they should be explicit and traceable.

---

# 24. Currentness

An artifact is `CURRENT` only if all required upstream dependencies match the revisions it was derived from.

Conceptually:

```text
current(artifact) =
  all required upstream identities/revisions still match
```

If any material upstream source changes, currentness should be re-evaluated.

---

# 25. Staleness Propagation

Staleness should propagate downstream.

Example:

```text
Scene S03 revision 2 → revision 3

Production Spec S03-R2 → STALE
Target Export E03-R2 → STALE
Execution Request X03-R2 → STALE
Result VIDEO03-R2 → historical result, not current canonical production
```

The existing result may still be playable, but it no longer represents the current source state.

---

# 26. Selective Staleness

Not every upstream change invalidates every downstream artifact.

Example:

A typo correction in a human-readable README may not stale video output.

A changed camera move should.

Therefore staleness should be based on semantic dependencies, not merely file modification time.

---

# 27. Target Export State

A target export should track:

- source project revision;
- source scene revision;
- capability profile revision;
- accepted degradation set;
- export revision;
- currentness.

Recommended states:

- `DRAFT`
- `CURRENT`
- `STALE`
- `SUPERSEDED`
- `BLOCKED`
- `TARGET_CAPABILITY_UNVERIFIED`

---

# 28. Execution Request State Relationship

An execution request should be traceable to one specific target export revision.

If the target export becomes stale before submission, the execution request should also become stale or invalid for submission.

If already submitted, the external job remains historical evidence but should no longer be treated as current production output.

---

# 29. External Job Lineage

An external job record should identify:

- execution request ID;
- target identity;
- provider job ID;
- submission time;
- current job state;
- result IDs;
- retry relationships if applicable.

A provider job ID alone is not sufficient project provenance.

---

# 30. Retry Lineage

Retries should preserve parent-child relationships.

Example:

```text
EX-S03-001
├── attempt 1 → timeout / ambiguous
└── attempt 2 → submitted
```

If a new execution request changes inputs materially, it should not be represented as the same attempt.

---

# 31. Result Lineage

Every generated result should identify:

- source execution request;
- external job;
- target export revision;
- canonical scene revision;
- asset inputs;
- result revision if post-processed;
- review/acceptance state.

---

# 32. Accepted Production Result

A result may be marked `ACCEPTED_FOR_PRODUCTION` only after appropriate production review.

Acceptance should identify:

- result ID;
- scene ID;
- accepted revision;
- review decision;
- reviewer/owner where relevant;
- acceptance time.

Acceptance does not make the generated result canonical creative intent.

It makes it the accepted realization of that intent.

---

# 33. Multiple Accepted Variants

A project may intentionally retain multiple accepted variants.

Examples:

- 16:9 landscape;
- 9:16 vertical;
- silent master;
- dubbed version;
- alternate language version.

These should be distinguished by delivery role rather than treated as conflicting results.

---

# 34. Production Master vs Variant

Where useful, distinguish:

- `MASTER`
- `DELIVERY_VARIANT`
- `ALTERNATE`
- `ARCHIVE`

This helps avoid treating every generated clip as equally authoritative.

---

# 35. Package Lineage

A portable package should identify:

- package ID;
- package revision;
- source project revision;
- production-spec revision;
- included asset revisions;
- included target exports;
- package completeness state.

If any included canonical artifact changes, the package may become stale.

---

# 36. Package Snapshot Semantics

A package represents a **snapshot** of project state at a particular revision.

A valid older package is not necessarily invalid.

It may simply be:

- historical;
- stale;
- superseded.

This distinction is important for auditability and rollback.

---

# 37. Rollback

The system may allow returning to a previous canonical revision.

Rollback should create or activate an explicit revision state rather than silently deleting history.

Example:

```text
Project v1.5 rejected
Project v1.4 restored as active baseline
```

Downstream artifacts should be re-evaluated for currentness.

---

# 38. Branching

Advanced workflows may create branches.

Example:

```text
Scene S03
├── revision 4A — emotional restraint
└── revision 4B — stronger reaction
```

RM-P05 does not require branching support, but if implemented, branch lineage should be explicit.

---

# 39. Merge

If branches are merged, provenance should identify source branches and resulting canonical revision.

Do not hide branch history.

---

# 40. State Transition Integrity

State transitions should be valid and explainable.

Example transitions:

```text
DRAFT → REVIEWED → APPROVED_FOR_PRODUCTION
APPROVED_FOR_PRODUCTION → REVISED_AFTER_APPROVAL
CURRENT → STALE
STALE → SUPERSEDED
```

Invalid transitions should be avoided.

Example:

```text
MISSING → ACCEPTED_FOR_PRODUCTION
```

without an intermediate ready/generated state is semantically incoherent.

---

# 41. Project Event Log

A professional implementation should preserve key state-changing events.

Possible events:

- project approved;
- canonical scene revised;
- asset replaced;
- package generated;
- target export generated;
- degradation approved;
- execution submitted;
- job succeeded;
- result accepted;
- result rejected;
- artifact superseded.

An event log supports auditability.

RM-P05 does not require one specific logging technology.

---

# 42. Event Semantics

A project event should conceptually include:

- event ID;
- timestamp;
- event type;
- affected entity;
- prior state;
- new state;
- actor/system;
- reason or source action.

---

# 43. Provenance Confidence

Some provenance information may be incomplete.

Recommended confidence states:

- `VERIFIED`
- `DECLARED`
- `INFERRED`
- `UNKNOWN`

Do not represent inferred provenance as verified fact.

---

# 44. Imported Projects

When importing an existing project, preserve known provenance and mark unknown portions explicitly.

Do not fabricate:

- original creation time;
- exact prior version;
- rights;
- source asset identity.

The imported project may establish a new canonical baseline.

---

# 45. External Assets

External assets should preserve:

- stable logical asset ID;
- external reference;
- access context if material;
- current availability;
- provenance;
- whether the external reference is durable or temporary.

Temporary URLs should not be treated as permanent asset identities.

---

# 46. Rights Metadata

When available, rights metadata should remain attached to asset identity across revisions and derivatives.

Potential metadata:

- rights owner;
- license;
- attribution;
- redistribution permission;
- usage restrictions.

Derived assets do not automatically acquire broader rights than their sources.

---

# 47. Privacy Metadata

Where relevant, assets may carry privacy sensitivity metadata.

Examples:

- public;
- private;
- confidential;
- personal data;
- voice/face reference.

This metadata can inform L3 external-transfer approval.

RM-P05 does not define the privacy policy itself; it preserves the relevant state.

---

# 48. Deletion and Retention

If an asset or record is deleted, lineage should not become misleading.

Possible states:

- `DELETED`
- `REDACTED`
- `UNAVAILABLE`

Historical references may preserve identity without exposing removed content.

---

# 49. Provider-Hosted Result Expiration

If a provider-hosted result is temporary, provenance should record:

- result identity;
- provider reference;
- known expiration;
- whether copied locally;
- current accessibility.

A temporary URL becoming inaccessible should not erase the historical job/result record.

---

# 50. Canonical Scene Example

Illustrative:

```yaml
project:
  id: PROJECT-01
  revision: 1.4
  state: APPROVED_FOR_PRODUCTION

scene:
  id: S03
  revision: 4
  state: CURRENT

production_spec:
  id: PS-S03
  revision: 2
  source_scene_revision: 4
  state: CURRENT

assets:
  - id: IMG-S03-START
    revision: 2
    state: READY
```

---

# 51. Derived Export Example

```yaml
target_export:
  id: EXP-S03-RUNWAY
  revision: 3

source:
  project_revision: 1.4
  scene_revision: 4
  production_spec_revision: 2

target_profile_revision: 2026-10-06

state: CURRENT
```

If Scene S03 becomes revision 5:

```yaml
target_export:
  id: EXP-S03-RUNWAY
  revision: 3
  state: STALE
```

---

# 52. Result Example

```yaml
result:
  id: RES-S03-07
  type: video
  state: AVAILABLE

source:
  execution_request_id: EX-S03-06
  target_export_revision: 3
  scene_revision: 4

review:
  decision: ACCEPTED_FOR_PRODUCTION
```

If canonical Scene S03 later changes to revision 5, the result remains historical but should no longer be treated as current realization of the canonical scene.

---

# 53. State Reconciliation

When the application resumes a prior project, it should reconcile state.

Recommended checks:

1. current canonical project revision;
2. current scene revisions;
3. current Production Specification revisions;
4. package versions;
5. asset readiness;
6. target-export currentness;
7. execution-job state;
8. result availability;
9. review/acceptance state.

This prevents stale derived work from being reused unknowingly.

---

# 54. Cross-Session Continuity

Project continuity across chat/session/runtime boundaries should rely on explicit project artifacts/state where available, not solely on conversational memory.

The application should be able to reconstruct:

- project identity;
- current revision;
- approved state;
- current scene versions;
- relevant assets;
- active production path;
- pending external jobs;
- accepted results.

---

# 55. State Recovery

If state is incomplete, the application should distinguish:

- known;
- missing;
- inferred;
- unverified.

It should not silently invent revision relationships.

---

# 56. Provenance Validation Rules

The following are normative.

## PR-01 — Stable identity

Every major canonical/derived entity must have a stable identity.

## PR-02 — Revision visibility

Materially changed canonical entities must expose revision change.

## PR-03 — Source traceability

Every derived production artifact must identify its canonical source revision.

## PR-04 — Asset traceability

Every production-significant asset must preserve identity and role.

## PR-05 — Stale detection

Downstream artifacts must be capable of becoming stale when material upstream dependencies change.

## PR-06 — Supersession distinction

Stale and superseded must remain semantically distinct.

## PR-07 — Result lineage

Generated results must be traceable to the execution request and canonical scene.

## PR-08 — Acceptance distinction

Generated result availability must remain distinct from production acceptance.

## PR-09 — No provenance fabrication

Unknown provenance must remain unknown.

## PR-10 — Canonical protection

Derived artifacts must not overwrite canonical source state without explicit revision.

---

# 57. Anti-Patterns

## 57.1 Filename-as-identity

Bad:

`scene3-final-final2.mp4`

used as the only identity.

Correct:

Stable logical ID + revision + role.

---

## 57.2 No source revision

Bad:

A target export does not record which scene revision produced it.

Correct:

Preserve source revision.

---

## 57.3 Overwriting history

Bad:

Regenerated result replaces prior clip with no lineage.

Correct:

Create new result revision/identity and preserve relationship.

---

## 57.4 Silent stale reuse

Bad:

Old target export is used after canonical scene changed.

Correct:

Mark stale and require regeneration/revalidation.

---

## 57.5 Provider ID as canonical ID

Bad:

Provider job ID becomes the project entity identity.

Correct:

Provider ID is external metadata linked to stable local identity.

---

## 57.6 Acceptance collapse

Bad:

Generated clip is automatically treated as accepted final.

Correct:

Preserve review/acceptance state.

---

## 57.7 Provenance guessing

Bad:

Imported asset is labeled “generated by project” because source is unknown.

Correct:

Mark provenance UNKNOWN or DECLARED.

---

# 58. Relationship to RM-P01

RM-P01 defines canonical production semantics.

RM-P05 defines how those semantics are versioned, identified, and related over time.

---

# 59. Relationship to RM-P02

RM-P02 packages project state.

RM-P05 defines how package snapshots relate to project revisions and currentness.

---

# 60. Relationship to RM-P03

RM-P03 creates target-derived artifacts.

RM-P05 tracks their source revision, capability-profile revision, currentness, staleness, and supersession.

---

# 61. Relationship to RM-P04

RM-P04 creates execution requests, jobs, and results.

RM-P05 provides long-lived lineage and provenance across those entities.

---

# 62. Consultation Guidance for the Application

Consult RM-P05 whenever the application:

- creates or updates project state;
- creates a canonical Production Specification;
- assigns scene or asset identities;
- replaces an asset;
- generates an L1 package;
- creates an L2 target export;
- evaluates whether an export is stale;
- creates an execution request;
- records an external job;
- records or retrieves a generated result;
- retries execution;
- accepts/rejects a result;
- resumes a prior production session;
- reconciles project state;
- determines whether a downstream artifact is current, stale, superseded, or invalid.

---

# 63. Professional Standard Summary

A professional production state system must be:

- **identity-stable**
- **revision-aware**
- **canonical-source preserving**
- **derived-artifact aware**
- **asset-aware**
- **dependency-aware**
- **staleness-aware**
- **supersession-aware**
- **provenance-preserving**
- **execution-aware**
- **result-aware**
- **acceptance-aware**
- **cross-session recoverable**
- **honest about unknown lineage**

The canonical question is not:

> “Which file is the latest?”

It is:

> **“Which canonical revision is authoritative, what downstream artifacts were derived from it, which assets and capabilities they depended on, what changed afterward, and which outputs are still current and trustworthy?”**
