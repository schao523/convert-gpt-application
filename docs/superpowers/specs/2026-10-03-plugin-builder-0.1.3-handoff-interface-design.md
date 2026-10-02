# Plugin Builder 0.1.3 Handoff Interface Design

Status: **APPROVED**  
Date: 2026-10-03  
Runtime scope: `OPENAI_ONLY_PHASE_ONE`  
Affected applications: Cool Plugin Design Assistant and Plugin Builder

Approval evidence: the decision owner explicitly approved this written
specification in the originating Codex conversation on 2026-10-03.

## 1. Purpose

Define one versioned, deterministic interface by which Cool Plugin Design
Assistant hands an approved full or delta application-plugin design to Plugin
Builder 0.1.3. The interface must preserve approved source bytes, requirement
identities, approval evidence, baseline identity, unresolved decisions, and
runtime scope without asking Plugin Builder to infer product authority.

Success means:

- a conforming Design Assistant package passes Plugin Builder intake directly;
- arbitrary requirement IDs retain their exact spelling, source binding, and
  approved text;
- both create and update handoffs use the same canonical envelope;
- previously observed full and delta envelopes have explicit, fail-closed
  compatibility behavior;
- identical inputs produce byte-identical normalized ZIPs; and
- W1 and W2 remain mandatory and unchanged.

## 2. Approved product constraints

This design preserves these owner decisions:

- formal Plugin Builder release version: `0.1.3`;
- target runtimes: Codex and ChatGPT Work Local/Desktop;
- excluded runtimes: OpenClaw and Claude;
- release targets: private/local ZIP, public GitHub-hosted Codex marketplace,
  and the OpenAI universal plugin directory; and
- preparation of release artifacts does not authorize a Git push, marketplace
  mutation, directory upload, review submission, or publication.

The handoff interface changes distribution compatibility, not application
behavior and not the approved runtime scope.

## 3. Design decision

Use a **producer-canonical, consumer-compatible** architecture.

Cool Plugin Design Assistant owns creation of new canonical packages. Plugin
Builder treats the canonical package as the primary authority and keeps narrow,
named adapters only for already observed legacy packages. A shared contract,
validator, canonical serializer, and fixture corpus prevent the two products
from evolving incompatible meanings of “canonical.”

Rejected alternatives:

1. **Prompt-generated sidecars in Plugin Builder.** Rejected because model
   interpretation could invent requirement text, baseline authority, approval,
   or source bindings.
2. **A delta-only third envelope.** Rejected because create and update would
   drift into separate trust models.
3. **Consumer-only compatibility patches.** Rejected because every new Design
   Assistant package would continue requiring repair downstream.

## 4. Canonical contract identity

The interface identity is `WORKBENCH_HANDOFF_V1_1`.

Every new package is a flat-root ZIP containing these two root files:

- `package-manifest.json`, the complete physical inventory and integrity
  authority; and
- `workbench-handoff.json`, the approved semantic authority.

`package-manifest.json` retains:

```json
{
  "package_schema_version": 1,
  "package_kind": "normalized-workbench-handoff",
  "handoff_contract": "WORKBENCH_HANDOFF_V1_1",
  "operation": "create",
  "runtime_scope": "OPENAI_ONLY_PHASE_ONE"
}
```

`workbench-handoff.json` adds the same contract and operation identity:

```json
{
  "schema": "workbench-handoff-v1.1",
  "operation": "create"
}
```

The duplicated identities must agree. A mismatch is an intake failure, not a
profile-selection prompt.

## 5. Archive and manifest rules

The archive may contain regular files below safe POSIX-relative paths. It must
reject absolute paths, traversal, backslashes, case-fold collisions, duplicate
members, links or reparse points, encryption, unsupported compression, and
undeclared files. Size and member-count limits remain product-owned defensive
limits and must be equal to or stricter than the existing implementations.

`package-manifest.json` must declare every package member exactly once through:

- `artifacts`, for approved or approved-derived design authorities;
- `supporting_files`, for non-authoritative packaged material; and
- `canonical_handoff`, for `workbench-handoff.json`.

Each declaration carries `file`, SHA-256, and byte size. Artifact declarations
also carry stable ID, role, version, state, provenance, and requirement IDs.
The manifest records the source archive SHA-256 whenever normalization occurred.

Canonical JSON uses UTF-8-compatible ASCII output, sorted keys, two-space
indentation, and one terminal newline. Deterministic ZIPs use sorted members,
the fixed DOS epoch timestamp, fixed regular-file modes, DEFLATE level 9, and
no environment-specific metadata.

## 6. Semantic handoff rules

The semantic handoff retains the existing approved design statement,
specification, workflows, instruction modules, reference-material map,
invariants, HITL checkpoints, deterministic-operation candidates, tool/data/
runtime/service requirements, acceptance scenarios, rights decisions,
exclusions, approval, and unresolved-owner-decision fields.

It additionally requires:

- `schema`;
- `operation`;
- `requirements`; and
- `baseline` plus `baseline_preservation` when `operation` is `update`.

The approval state and approved specification state must both be `approved`.
Every unresolved owner decision retains a stable ID, owner, summary, impact,
and boolean blocking state. A blocking decision stops intake at F1.

## 7. Canonical requirement records

`requirements` is a non-empty array for both create and update packages. Each
record requires:

| Field | Contract |
| --- | --- |
| `id` | Non-empty, whitespace-stable, package-unique identifier preserved exactly |
| `source` | Declared UTF-8 artifact path, optionally followed by a fragment |
| `verbatim` | Non-empty exact text occurring in the referenced artifact |
| `change` | `add`, `modify`, `remove`, or `preserve`; required for update, omitted for create |

Additional owner-supplied fields are retained unchanged. Plugin Builder must
not rename IDs, generate aliases, normalize punctuation, or derive behavioral
meaning from ID syntax. The source path before `#` must be a declared artifact.
The exact `verbatim` bytes, decoded as UTF-8 without newline translation, must
occur in that artifact.

Artifact-level `requirements` becomes an array of exact IDs and is an index,
not an alternate authority. Every indexed ID must exist in the semantic
requirement records, and every semantic requirement must be indexed by at least
one authoritative artifact. Regex discovery of `RQ`, `AC`, or `T` identifiers
is limited to legacy compatibility and cannot satisfy the v1.1 contract.

## 8. Create operation

For `operation: "create"`:

- `baseline` and `baseline_preservation` are absent;
- every requirement record omits `change`;
- the package represents the complete approved design authority; and
- Plugin Builder still produces a plan and waits for W1 before mutation.

## 9. Update operation

For `operation: "update"`, `baseline` requires:

```json
{
  "plugin_id": "cool-sermon-coach",
  "version": "1.1.0",
  "archive_sha256": "<64 lowercase hex characters>"
}
```

`baseline_preservation` requires:

```json
{
  "preserve_unaffected_members": true,
  "removal_requires_requirement": true,
  "identity_must_match": true
}
```

Plugin Builder compares this identity with the separately supplied baseline ZIP
before planning. A missing baseline, plugin/version mismatch, or digest mismatch
blocks at F1. `remove` requirements authorize only the explicitly bound removal;
silence never authorizes deletion. `preserve` makes an approved preservation
obligation explicit. Unaffected and unexplained baseline members remain subject
to the existing update-resolution and W1 controls.

## 10. Normalization authority

Normalization may copy fields, derive hashes/sizes, classify an explicitly
identified artifact role, and serialize deterministically. It may not:

- invent or paraphrase requirement text;
- select between multiple possible approved specifications;
- convert a non-approved state to approved;
- infer a missing baseline identity;
- resolve an owner decision;
- grant redistribution rights; or
- change runtime scope.

If a legacy package lacks enough evidence to produce a required v1.1 field,
the adapter returns `BLOCKED` with one deterministic diagnostic and leaves the
source unchanged. It does not emit a package that merely looks canonical.

## 11. Compatibility matrix

| Input profile | Recognizer | 0.1.3 behavior | Requirement authority | Result |
| --- | --- | --- | --- | --- |
| `WORKBENCH_HANDOFF_V1_1` create | Canonical pair, matching schema/operation | Pass through after full validation | Explicit canonical records | Supported |
| `WORKBENCH_HANDOFF_V1_1` update | Canonical pair plus baseline contract | Validate against supplied baseline, then pass through | Explicit canonical records with `change` | Supported |
| Existing `CANONICAL_V1` | Canonical pair without v1.1 identity | Preserve and validate under 0.1.2 rules | Canonical records when present; legacy discovery otherwise | Supported legacy; planning blocks if no requirements are discovered |
| `LEGACY_WORKBENCH_V1` | `workbench_handoff_manifest.json` with existing required keys | Existing deterministic adapter | Existing legacy RQ/AC/T discovery | Supported legacy |
| `COOL_DESIGN_ASSISTANT_FULL_V1` | `handoff_manifest.json` with the Design Assistant artifact-role contract | Deterministically adapt to v1.1 only when exact requirement records are supplied or provable | Exact legacy records; no ID guessing | Supported compatibility profile |
| `COOL_DESIGN_ASSISTANT_DELTA_V1` | `delta_handoff_manifest.json` with approved delta, baseline, and preservation fields | Deterministically adapt to v1.1 update | Exact delta records and baseline binding | Supported compatibility profile |
| Mixed canonical and legacy authorities | More than one recognized semantic authority | Do not select one | None selected | `AMBIGUOUS`, blocked at F1 |
| Unknown envelope | No exact recognizer | Do not infer | None | `UNKNOWN`, blocked at F1 |

Legacy support is transitional. New Design Assistant output must be v1.1.

## 12. Producer changes

Cool Plugin Design Assistant will:

1. add a shared v1.1 contract validator and canonical serializer;
2. emit explicit requirement records and artifact requirement arrays;
3. emit `operation`, contract identity, and runtime scope in both authorities;
4. represent deltas as canonical update handoffs;
5. validate baseline and preservation fields before emission;
6. preserve approved artifact bytes and record source archive identity;
7. keep old `handoff_manifest.json` normalization as a named compatibility
   path; and
8. add full, delta, malformed, ambiguous, and deterministic fixtures.

The Design Assistant must continue to avoid selecting Skill architecture,
tools, storage, RAG, adapters, or packaging on Plugin Builder's behalf.

## 13. Consumer changes

Plugin Builder 0.1.3 will:

1. recognize and validate `WORKBENCH_HANDOFF_V1_1`;
2. use canonical requirement records as the only v1.1 requirement authority;
3. validate artifact-to-requirement closure;
4. validate update baseline identity before planning;
5. add the two exact Design Assistant compatibility profiles;
6. preserve existing canonical and legacy profiles;
7. reject mixed authorities deterministically;
8. retain complete requirement records in inspection evidence;
9. keep W1, candidate construction, verification, W2, and packaging gates
   unchanged; and
10. update session-profile validation, skills, documentation, and runtime-kit
    fixtures without adding network, credential, or publication capability.

## 14. Shared implementation boundary

Generic schema, validation, canonical JSON, profile detection, and fixture
helpers belong in `src/obvious_one_plugin_framework`. Product scripts call the
public shared API and retain only product-specific CLI mapping and diagnostics.
No application-domain content enters the generic framework.

The shared API must remain non-interactive, accept explicit paths and owner
values, return structured outcomes, and never write outside the caller-supplied
destination. New distribution builds continue using schema v3; this handoff
schema is a separate contract and does not change distribution-schema rules.

## 15. Diagnostics

Diagnostics are stable machine-readable identifiers. At minimum:

- `handoff.contract_mismatch`
- `handoff.operation_mismatch`
- `requirements.explicit_records_required`
- `requirements.duplicate_id:<id>`
- `requirements.source_missing:<id>`
- `requirements.text_mismatch:<id>`
- `requirements.artifact_binding_missing:<id>`
- `baseline.required_for_update`
- `baseline.identity_mismatch`
- `baseline.archive_sha256_mismatch`
- `profile.multiple_authorities`
- `profile.unrecognized`

Errors in supplied bytes or schema return `FAIL`; missing owner authority or an
unresolvable legacy mapping returns `BLOCKED`. No failing or blocked operation
replaces an existing output.

## 16. Verification plan

Implementation is test-first. Each production change begins with a failing
unit or contract test. Required evidence includes:

- framework contract tests for schema, paths, hashes, requirement closure,
  baseline identity, deterministic bytes, and fail-closed publication;
- Design Assistant product tests for v1.1 create/update emission and both legacy
  inputs;
- Plugin Builder product tests for every compatibility-matrix row;
- a cross-product test that feeds the Design Assistant's generated ZIP directly
  to Plugin Builder without repair;
- a real full-design fixture and a real delta-style fixture with arbitrary IDs;
- unchanged-source and no-partial-output assertions;
- full framework and both product suites;
- plugin and skill structural validation;
- two clean deterministic builds with matching hashes;
- extracted-artifact verification; and
- `git diff --check` in each affected checkout.

Installed conversational execution remains a separate runtime-evidence gate.
Interface tests cannot change it from `NOT VERIFIED` to `RUNTIME VERIFIED`.

## 17. Release boundary

After implementation and local verification, Plugin Builder may be labeled a
`0.1.3` release candidate. Formal release still requires the remaining product,
installed-runtime, listing, legal, marketplace, and publication gates. No part
of this design authorizes external release actions.

## 18. Owner-review checklist

Approval of this document confirms:

- canonical v1.1 is the only format for new Design Assistant output;
- both full and delta handoffs use the same envelope;
- exact requirement records are mandatory;
- update handoffs bind an exact baseline archive;
- the named legacy profiles remain supported only through deterministic
  adapters;
- insufficient legacy evidence blocks instead of being inferred;
- W1 and W2 remain unchanged; and
- runtime and publication authority remain as stated above.
