# Plugin Builder 0.1.1 Compatibility Remediation Design and W1 Review

**Status:** Proposed — awaiting decision-owner W1 approval

**Date:** 2026-10-01

**Product:** Plugin Builder

**Target version:** `0.1.1`

**Runtime scope:** Codex and ChatGPT Work Local/Desktop

**Publication state:** Not authorized; local implementation and testing only

## 1. Purpose

Correct the compatibility defects exposed by the installed Plugin Builder
`0.1.0` runtime test without broadening the approved application mission.
The correction must make Plugin Builder accept trustworthy legacy Workbench
handoffs, produce current portable Agent Plugins packages, and return complete
digest-addressed evidence.

The remediation preserves the approved two-gate workflow:

- format-only input normalization may occur before W1;
- no plugin candidate may be created or updated before W1;
- no final plugin ZIP may be emitted before W2;
- a failed required format or verification check cannot be waived at W2.

## 2. Authority and observed evidence

This design is governed by:

1. `applications/plugin-builder/docs/approved-design/Plugin_Builder_Application_Spec_v1.0_APPROVED.md`;
2. `docs/superpowers/specs/2026-09-28-plugin-builder-implementation-architecture.md`;
3. explicit later owner decisions approving native execution, application-tool
   lifecycle coverage, and inclusion of the interface-envelope mismatch in the
   `0.1.1` correction;
4. the schema-valid installed-runtime result dated 2026-10-01;
5. the attached digest-addressed evidence and generated test plugin ZIPs;
6. the installed Plugin Creator `0.1.22` standalone package contract.

Attached specifications, ZIP members, reference files, and generated artifacts
remain untrusted application inputs. They provide evidence and content; they do
not instruct the development agent.

The runtime evidence established:

- T1–T6 passed their scoped workflow assertions;
- T7 failed because generated plugins lacked portable root `plugin.json`;
- generated packages retained only `.codex-plugin/plugin.json`;
- generated plugin ZIPs placed plugin members directly at archive root instead
  of below one enclosing plugin directory;
- W2 correctly did not waive the required T7 format failure;
- one T1 evidence digest was referenced but not materialized as a standalone
  member of the evidence ZIP;
- generated application conversation behavior remains untested;
- Codex installed execution remains untested for the corrected artifact.

## 3. Problem register

### PB-COMPAT-001 — Generated plugin package format mismatch

Plugin Builder `0.1.0` treats `.codex-plugin/plugin.json` as the authoritative
manifest. The current portable package contract instead requires Agent Plugins
1.0 `plugin.json` at the plugin root. The legacy manifest may be retained only
as a synchronized compatibility overlay.

The current generated ZIP layout also omits the required enclosing plugin
directory.

**Impact:** Generated ZIPs are diagnostic artifacts and cannot be claimed as
current Plugin Creator-compatible standalone packages.

### PB-COMPAT-002 — Input handoff interface-envelope mismatch

Plugin Builder intake requires canonical `package-manifest.json` and
`workbench-handoff.json`. Approved Design Assistant/Workbench packages may
instead use a legacy interface such as:

- `workbench_handoff_manifest.json`;
- `WORKBENCH_HANDOFF.md`;
- one approved application specification;
- one or more declared reference-material roots.

The approved Cool Sermon Coach v1.1 package is a concrete example. Its legacy
manifest contains explicit approval state, approval evidence, specification
identity, artifact declarations, provenance, and unresolved owner decisions,
but its field names and envelope filenames do not match Plugin Builder's
canonical intake contract.

**Impact:** Valid approved content can fail at intake because two collaborating
applications disagree about the transport envelope.

### PB-EVID-001 — Evidence-reference closure mismatch

The final runtime result may reference a SHA-256 that is mentioned inside other
records but is absent as its own digest-addressed evidence member.

**Impact:** The result is schema-valid but the evidence package is not fully
self-resolving.

## 4. Goals

Plugin Builder `0.1.1` will:

1. accept an already-canonical approved handoff without changing its content;
2. deterministically normalize a recognized legacy handoff profile into the
   canonical envelope;
3. refuse to invent approval, rights, behavioral authority, or unresolved
   decisions when the source package lacks equivalent evidence;
4. preserve every original source member byte-for-byte in normalized output;
5. produce portable root `plugin.json` using Agent Plugins 1.0;
6. retain and synchronize `.codex-plugin/plugin.json` when compatibility
   requires it;
7. package one lowercase kebab-case plugin directory whose name matches the
   portable manifest;
8. enforce portable format, compatibility-overlay synchronization, exact
   member closure, and evidence closure as required pre-W2 checks;
9. retain deterministic output for identical approved inputs, decisions, and
   tool versions;
10. rerun all T1–T7 scenarios against the corrected installed artifact in both
    target runtimes before readiness changes.

## 5. Non-goals

This remediation does not:

- change the approved Plugin Builder mission or two-gate interaction model;
- infer a behavioral specification from arbitrary documents;
- treat a filename containing `APPROVED` as sufficient approval evidence;
- silently select among multiple plausible authoritative specifications;
- rewrite source specifications or reference materials;
- publish, upload, install, submit, or mutate a marketplace;
- add OpenClaw or Claude to the approved `0.1.1` runtime scope;
- claim generated application conversation behavior without executing it;
- make an optional unavailable runtime-native or MCP capability appear
  verified.

## 6. Selected architecture

Use explicit compatibility adapters at the two external boundaries while
keeping the existing session engine and portable skills unchanged.

```text
Input handoff ZIP
      |
      v
Safe archive inventory
      |
      +--> canonical profile ---------+
      |                               |
      +--> recognized legacy adapter -+--> canonical intake workspace
      |                               |
      `--> unknown/ambiguous -----------> F1 blocked normalization proposal

Canonical intake workspace
      -> plan -> W1 -> build/update -> verify
      -> portable package validator -> W2 -> deterministic package
                                             |
                                             v
                            plugin-name/plugin.json
                            plugin-name/.codex-plugin/plugin.json
                            plugin-name/skills/...
                            plugin-name/[approved tools and assets]
```

The adapters are deterministic engine capabilities. Skills explain results,
route owner decisions, and request approval; they do not fabricate canonical
metadata or rewrite ZIPs themselves.

## 7. Considered approaches

### A. Boundary adapters with explicit profiles — selected

Recognize canonical and approved legacy envelopes through strict profiles,
map equivalent fields with provenance, and block ambiguity.

**Advantages:** backward compatible, auditable, deterministic, and consistent
with the existing architecture rule that runtime/interface variation belongs
at integration boundaries.

### B. Keep strict canonical-only intake — rejected

Require the Design Assistant or a human to rebuild every legacy handoff before
Plugin Builder can inspect it.

**Reason rejected:** preserves the observed interface failure and makes valid
approved content unusable despite containing equivalent evidence.

### C. Heuristically synthesize approval from arbitrary ZIP contents — rejected

Guess the specification, approval state, and artifact roles from filenames and
document prose.

**Reason rejected:** nondeterministic and violates the decision-owner boundary.

## 8. Input normalization contract

### 8.1 Profile classification

Every source ZIP receives exactly one classification:

| Classification | Required behavior |
| --- | --- |
| `CANONICAL_V1` | Validate existing canonical files and proceed without semantic remapping. |
| `LEGACY_WORKBENCH_V1` | Apply the strict legacy mapping below and generate canonical sidecars. |
| `UNKNOWN` | Return F1 with an auditable normalization proposal; do not claim approval. |
| `AMBIGUOUS` | Return F1 and identify the conflicting candidate authorities. |

Profile detection must use exact structural predicates and declared metadata,
not application-specific filenames alone.

The first supported legacy profile is `LEGACY_WORKBENCH_V1`, demonstrated by
the approved Cool Sermon Coach v1.1 handoff:

- exactly one `workbench_handoff_manifest.json` object;
- explicit `specification_state`, `approval_evidence`, `gate_result`, and
  `specification_version` fields;
- an `included_artifacts` array identifying the authoritative specification
  and reference-material roots;
- optional `unresolved_owner_decisions` records;
- every declared artifact resolvable to safe archive members.

### 8.2 Trust and approval rules

Normalization may copy an approved state only when the recognized legacy
profile provides all of the following:

- an explicit approved specification state;
- non-empty approval evidence;
- a gate result beginning with `APPROVED`;
- exactly one authoritative specification artifact;
- a matching specification version and safe archive member;
- no unresolved decision marked blocking.

If any condition is absent or contradictory, the generated canonical handoff
must use an unapproved/pending state and intake must remain at F1. The engine
must never promote an input merely because a filename contains `APPROVED`.

### 8.3 Canonical `package-manifest.json`

For `LEGACY_WORKBENCH_V1`, mapping is exact:

| Canonical field | Legacy source or rule | Provenance class |
| --- | --- | --- |
| `application` | `application_name` | `COPIED` |
| `spec_version` | `specification_version` | `COPIED` |
| `gate` | `gate_result` | `COPIED` |
| `runtime_scope` | Plugin Builder's approved `OPENAI_ONLY_PHASE_ONE` scope | `OWNER_SUPPLIED` |
| approved specification ID | authoritative `included_artifacts[].artifact_id` | `COPIED` |
| approved specification file | authoritative `included_artifacts[].path` | `COPIED` |
| artifact version/state/provenance | corresponding legacy artifact fields | `COPIED` |
| artifact role | exact normalized value derived from the artifact's declared `relation` | `MECHANICALLY_DERIVED` |
| file SHA-256 and size | streamed from the source ZIP member bytes | `MECHANICALLY_DERIVED` |
| source archive SHA-256 | streamed from the original ZIP bytes | `MECHANICALLY_DERIVED` |

An `included_artifacts[].path` ending in `/` is a declared member prefix, not a
file. The adapter expands it into every descendant regular-file member in
sorted POSIX order. Each expanded record retains the parent artifact's state,
version, provenance, and relation; its stable ID is
`<artifact_id>/<relative-descendant-path>`. An empty prefix, escaping path,
case-fold collision, or non-regular member blocks normalization.

Legacy `requirements` are copied only when the legacy artifact explicitly
declares them. Absence means “not declared by this envelope,” not an empty or
invented requirement set; requirement extraction may still occur later from
the approved specification under the normal planning workflow.

The generated manifest will contain:

- `package_schema_version: 1`;
- `package_kind: "normalized-workbench-handoff"`;
- application and specification identity;
- normalized gate and runtime scope;
- `source_archive_sha256`;
- a `normalization` object containing profile ID, adapter version, and field
  provenance;
- one record per authoritative artifact with stable ID, role, state, version,
  provenance, requirements when explicitly available, SHA-256, and size;
- one record per supporting file not represented as an authoritative artifact;
- `canonical_handoff` with file, SHA-256, and size.

Every declared file must exist and match its recorded digest and byte size.
The manifest itself is not allowed to declare requirements, rights, or roles
that cannot be traced to source metadata or an explicit decision-owner record.

### 8.4 Canonical `workbench-handoff.json`

For `LEGACY_WORKBENCH_V1`, approval mapping is exact:

| Canonical field | Legacy source or rule | Provenance class |
| --- | --- | --- |
| `approval.state` | `approved` only when all Section 8.2 predicates pass; otherwise `pending` | `MECHANICALLY_DERIVED` |
| `approval.confirmed_by` | literal role `decision owner recorded by legacy handoff` | `MECHANICALLY_DERIVED` |
| `approval.evidence` | `approval_evidence` | `COPIED` |
| `approval.specification_version` | `specification_version` | `COPIED` |
| `approved_specification.*` | the single authoritative legacy artifact plus `specification_state` | `COPIED` |
| `unresolved_owner_decisions[]` | same-named legacy array with normalized field order | `COPIED` |

The normalized confirmer is a role label, not a fabricated personal identity.
The original approval-evidence text remains authoritative and unmodified.

The generated handoff will contain:

- approval state, confirmer/evidence text, specification version, and the
  source field that supplied each value;
- exactly one approved-specification record;
- normalized unresolved owner decisions with blocking, ID, owner, summary,
  and impact when supplied;
- source profile and source archive identity;
- a field-provenance map distinguishing `COPIED`, `MECHANICALLY_DERIVED`,
  `OWNER_SUPPLIED`, and `UNRESOLVED` values.

No private absolute path is persisted.

### 8.5 Preservation and output

Normalization creates a new package. It never modifies the source ZIP.
All original regular-file members are copied byte-for-byte. The two canonical
files are added at package root. Legacy envelope members remain present as
supporting evidence unless an exact path collision makes safe normalization
impossible; a collision blocks rather than overwrites.

The normalizer emits:

- canonicalized workspace input;
- optional deterministic normalized ZIP for audit and reuse;
- `plugin-builder-handoff-normalization-v1` report with source/output hashes,
  profile decision, mappings, unresolved fields, and diagnostics.

Identical source bytes, adapter version, and owner-supplied decisions must
produce byte-identical JSON and ZIP output.

## 9. Generated plugin package contract

### 9.1 Portable manifest

Every generated plugin must contain root `plugin.json` conforming to Agent
Plugins 1.0. It must include:

- the Agent Plugins 1.0 `$schema` URI;
- lowercase kebab-case `name` of at most 64 characters;
- strict semantic `version`;
- non-empty description and author;
- `extensions.com.openai.interface` containing supported presentation fields;
- a short description no longer than 30 characters;
- only supported root keys.

Portable discovery uses fixed `skills/` and `mcp.json` locations. The portable
manifest must not add legacy top-level `skills`, `mcpServers`, `apps`, or
`interface` keys.

### 9.2 Compatibility overlay

When the target requires `.codex-plugin/plugin.json`, Plugin Builder retains
it as an overlay. The validator must prove that root and overlay manifests have
the same:

- plugin name;
- version;
- author/developer identity;
- display name and descriptions;
- default prompt values and order;
- declared capabilities after the documented representation mapping.

A mismatch is a required failure.

### 9.3 Archive envelope

The final ZIP contains exactly one top-level directory named after the
portable manifest's `name`. All package members, including hidden compatibility
files, live below it. The ZIP is written outside that directory with fixed
timestamps, permissions, ordering, path separators, and compression settings.

The package validator must inspect both the candidate tree and the extracted
final ZIP. Passing development-source validation alone is insufficient.

## 10. Evidence closure contract

Every non-null `evidence_sha256` in the final runtime result must resolve to an
attached evidence member named by that digest and extension. Every indexed
evidence member must match its filename digest, byte size, and index record.

The evidence packager must fail when:

- a referenced digest is absent;
- a member's bytes do not match its digest;
- two logical records claim the same path with different bytes;
- an evidence index omits a packaged member;
- the result JSON references evidence outside the package without an explicit
  external-evidence classification allowed by the schema.

The current schema has no external-evidence classification; therefore `0.1.1`
requires full local closure.

## 11. Failure and recovery behavior

| Condition | Required outcome |
| --- | --- |
| Canonical package valid | Proceed to S2 with canonical bytes recorded. |
| Recognized legacy package fully maps | Normalize, validate, then proceed to S2. |
| Approval evidence incomplete | F1; emit proposal and one owner decision request. |
| Multiple authoritative specifications | F1; list conflicting members without selecting one. |
| Canonical filename collision | F1; preserve source and emit no normalized ZIP. |
| Root portable manifest missing or invalid | Required `FAIL`; W2 and package blocked. |
| Overlay identity differs from portable manifest | Required `FAIL`; W2 and package blocked. |
| ZIP lacks single enclosing directory | Required `FAIL`; W2 and package blocked. |
| Evidence digest reference unresolved | Required `FAIL`; final evidence bundle not emitted. |

Failures preserve the source package and prior valid session evidence. A retry
uses a newly generated canonical identity and invalidates approvals bound to
older plan, candidate, verification, or package hashes as applicable.

## 12. Component and file responsibility map

The detailed implementation plan may refine line ranges but must retain these
boundaries:

| Responsibility | Expected location |
| --- | --- |
| Profile detection and canonical handoff construction | `applications/plugin-builder/scripts/plugin_builder_core/handoff_normalization.py` |
| Intake orchestration and F1/S2 result mapping | `applications/plugin-builder/scripts/plugin_builder_core/inspection.py` |
| Portable and overlay manifest validation | `src/obvious_one_plugin_framework/plugin_authoring/validation.py` |
| Portable/overlay manifest materialization | `src/obvious_one_plugin_framework/plugin_authoring/materialize.py` and Plugin Builder candidate orchestration |
| Single-directory deterministic ZIP construction | `src/obvious_one_plugin_framework/plugin_authoring/archive.py` and Plugin Builder packaging orchestration |
| Evidence reference closure | Plugin Builder runtime-kit/evidence packaging module introduced by the implementation plan |
| Product CLI surface | `applications/plugin-builder/scripts/plugin_builder.py` |
| Input-normalization tests | `applications/plugin-builder/tests/test_handoff_normalization.py` and `test_inspection.py` |
| Portable package tests | framework validation/archive tests plus Plugin Builder create, update, verification, and packaging tests |
| Runtime contract and evidence tests | `applications/plugin-builder/tests/runtime/` and product runtime-kit tests |

The implementation should extend focused modules instead of expanding
`inspection.py` or `packaging.py` into mixed-responsibility files.

## 13. Requirement-to-implementation-to-evidence map

| Requirement | Preserved observable outcome | Implementation owner | Required evidence before release |
| --- | --- | --- | --- |
| PB-COMPAT-001A | Generated plugin has valid portable root manifest. | Generic plugin validation plus candidate materializer | Unit tests, extracted-ZIP Plugin Creator contract validation, T2/T7 |
| PB-COMPAT-001B | Legacy overlay is retained only as a synchronized adapter. | Manifest identity synchronizer | Mismatch fixtures and passing create/update artifact checks |
| PB-COMPAT-001C | ZIP has exactly one correctly named top-level directory. | Deterministic packager | Archive member assertions and repeated-build digest equality |
| PB-COMPAT-002A | Canonical handoffs continue to pass unchanged. | Inspection plus canonical profile | Regression fixture and byte-identity assertion |
| PB-COMPAT-002B | Recognized legacy handoffs produce canonical sidecars. | Legacy profile adapter | Cool Sermon Coach-shaped fixture and deterministic normalized ZIP test |
| PB-COMPAT-002C | Missing or ambiguous authority never becomes approved. | Normalization trust gate | Missing evidence, conflicting specification, and filename-only approval fixtures |
| PB-COMPAT-002D | Original members remain byte-identical. | Safe archive copier | Per-member digest comparison before and after normalization |
| PB-COMPAT-002E | Canonical output passes the existing repository intake gate. | Normalizer plus inspection | Normalizer-to-inspector integration test |
| PB-EVID-001 | Every result evidence digest resolves inside the evidence bundle. | Evidence closure validator | Missing-member RED/GREEN test and complete T1–T7 bundle verification |
| AC3 / INV-PB-002 | W1 precedes candidate mutation; W2 precedes packaging. | Existing approvals/session engine | Full regression suite and T1/T2/T5/T7 |
| AC5 / INV-PB-005 | Required format failure cannot be waived. | Verification and W2 guards | Portable-manifest and evidence-closure failure scenarios |
| AC7 / INV-PB-006 | Updates preserve unaffected members and wait on unexplained content. | Existing update engine plus dual-manifest preservation | T4 create/update baseline comparison |
| AC8 / INV-PB-011 | Returned ZIP is manually installable; no automatic deployment. | Package boundary and documentation | Extracted package validation; publication state `NOT PERFORMED` |
| AC1/AC9/AC10 | Corrected standalone artifact works without repository imports. | Generated Plugin Builder artifact | T7 in ChatGPT Work Local/Desktop and Codex |

Initial evidence state for every new remediation row is `EXPECTED`. Existing
`0.1.0` evidence remains historical and must not be relabeled as `0.1.1`
runtime evidence.

## 14. Testing strategy

Implementation is test-first. Required layers are:

1. unit tests for profile detection, mapping, trust rules, deterministic JSON,
   portable manifest shape, overlay synchronization, and evidence closure;
2. malicious and ambiguous input fixtures covering traversal, collisions,
   multiple specifications, missing approval, and inconsistent versions;
3. integration tests proving normalized legacy output passes current intake;
4. create and update tests proving both manifests and unrelated baseline bytes
   survive correctly;
5. candidate and extracted-final-ZIP validation against the current installed
   Plugin Creator and Skill Creator contracts;
6. two-build byte equality for normalized handoff and final plugin ZIP;
7. complete product, framework, extraction, distribution, and `git diff
   --check` verification;
8. a rebuilt `0.1.1` runtime kit and full T1–T7 replay in ChatGPT Work
   Local/Desktop and Codex;
9. separate representative Cool Sermon Coach conversation scenarios in both
   runtimes, including checkpoints, reference routing, tool use, failure
   behavior, and exclusions.

Because the installed artifact hash changes, all T1–T7 scenarios must be rerun.
The `0.1.0` results remain diagnostic history, not release evidence for
`0.1.1`.

## 15. Distribution and versioning

`0.1.1` is a compatibility correction to the unreleased `0.1.0` foundation.
The correction does not authorize publication or account upload. Build output
remains below ignored `dist/plugin-builder` roots.

The `0.1.0` runtime result, generated test ZIPs, and digest-addressed evidence
must be preserved as immutable historical diagnostics. They must not be
silently replaced by corrected artifacts.

## 16. W1 review package

### Intended user-visible change

Plugin Builder accepts a trustworthy legacy Workbench handoff without asking a
non-developer to manufacture canonical metadata, while still stopping when
approval or authority is ambiguous. Generated plugin ZIPs use the current
portable format and retain the older Codex overlay only for compatibility.

### Capability decisions

| Capability | Decision | Evidence and reason |
| --- | --- | --- |
| Safe ZIP inventory/extraction | `REUSE` | Existing `plugin_authoring.archive` already enforces confinement and deterministic identity. |
| Canonical handoff validation | `ADAPT` | Existing inspection validates canonical files but cannot synthesize them from legacy envelopes. |
| Legacy Workbench profile mapping | `BUNDLE` | New deterministic local adapter; no network, credentials, or external service required. |
| Portable Agent Plugins manifest validation | `ADAPT` | Extend existing validator to the current root-manifest contract. |
| Legacy Codex overlay support | `ADAPT` | Retain compatibility file and add explicit identity synchronization. |
| Deterministic ZIP writer | `ADAPT` | Reuse byte-stable writer while adding the single enclosing directory contract. |
| Evidence bundle closure | `BUNDLE` | Add a focused deterministic validator/packager because current evidence can reference an absent member. |
| Plugin Creator/Skill Creator development checks | `REUSE` | Use installed contract guidance/validators as development evidence; shipped runtime remains self-contained. |

### Dependencies and permissions

- Python 3.11+ standard library only for shipped deterministic operations.
- Local read access to the supplied ZIP and local write access to the caller's
  workspace/output path.
- No network, credentials, MCP server, background process, or Workbench source
  checkout at installed runtime.
- No new redistribution rights decision: normalized packages preserve supplied
  content and add project-authored metadata only.

### Candidate delta boundary

The implementation plan may modify only Plugin Builder, generic reusable
plugin-authoring primitives required by the correction, relevant tests,
runtime-kit generation, and Plugin Builder documentation. It must not modify
the Cool Plugin Design Assistant, approved source handoff, generated Cool
Sermon Coach content, marketplace repositories, or unrelated applications.

### Risks presented for W1

1. **False approval promotion:** controlled by exact trust predicates and
   filename-only rejection tests.
2. **Legacy-profile overfitting:** controlled by a named/versioned profile and
   `UNKNOWN`/`AMBIGUOUS` blocked outcomes.
3. **Manifest drift:** controlled by cross-manifest identity comparison.
4. **Update regressions:** controlled by byte-preservation tests spanning both
   manifests and unrelated baseline members.
5. **Evidence overclaiming:** controlled by bundle closure and full runtime
   replay under the new artifact hash.

### W1 decision requested

Approve the following exact scope for implementation planning:

- implement PB-COMPAT-001, PB-COMPAT-002, and PB-EVID-001 as specified;
- support `CANONICAL_V1` and `LEGACY_WORKBENCH_V1` in `0.1.1`;
- block unknown or ambiguous packages rather than guessing;
- emit Agent Plugins 1.0 root `plugin.json` plus a synchronized legacy overlay;
- require one enclosing plugin directory in final ZIPs;
- require complete digest-addressed evidence closure;
- rerun repository gates and full T1–T7 in both approved runtimes;
- keep publication, upload, marketplace mutation, and external release out of
  scope.

**Current W1 state:** `AWAITING_OWNER_APPROVAL`

**Mutation allowed:** No

**Next action after approval:** Write the detailed test-first implementation
plan; do not begin implementation in the same approval turn.

## 17. Readiness boundary

The remediation is not complete merely when local tests pass. Until corrected
artifacts are installed and executed in both target runtimes, report:

```text
CONVERSION COMPLETE — RUNTIME VALIDATION PENDING
```

Do not report `READY` while any required format, T1–T7, installed execution,
application-behavior, or cross-runtime-equivalence gate lacks passing evidence.
