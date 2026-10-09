# Growing with Children 1.0.2 Reference Handoff and Publication Design

**Status:** Owner-approved design recorded for written review  
**Date:** 2026-10-09  
**Source artifact:** `growing-with-children_v1.0.1 (1).zip`  
**Source SHA-256:** `e20ab7f970565dde1d2bfa8529d82da12366dfbed6a6672aed9dc51eedb6d1f1`  
**Target release:** `growing-with-children` 1.0.2  
**Target marketplace:** Obvious One Codex marketplace

## 1. Objective

Produce and publish a corrected 1.0.2 derivative of the valid legacy Plugin
Builder 1.0.1 archive without changing the application's five-skill
architecture or its approved behavior. The correction replaces invalid local
RM-04A/RM-04B paths in four non-owner skills with an explicit, validated
handoff to `guiding-biblical-study`, the sole owner of those two Bible PDFs.

The original 1.0.1 archive remains immutable source evidence. Publication is
permitted only after the derived archive, installed plugin, and staged
marketplace delta pass their applicable gates.

## 2. Existing defect

The legacy archive contains five skills and packages RM-04A/RM-04B only below
`skills/guiding-biblical-study`. Four other skills nevertheless link those PDFs
as if local copies existed below their own `assets/reference-material`
directories and list them as local assets in their knowledge indexes:

- `coaching-parenting-and-sensitive-conversations`;
- `designing-family-devotions`;
- `guiding-parenting-sessions`;
- `supporting-parent-reflection`.

Static closure therefore reports sixteen findings: two missing path bindings
and two missing links for each non-owner skill. The defect cannot be repaired
while preserving byte identity of the 1.0.1 archive.

## 3. Approved architecture

`guiding-biblical-study` is the only owner of RM-04A and RM-04B. It retains the
two PDFs, their local knowledge-index records, direct links, exact-text rules,
and formal Bible-study procedure.

The other four skills do not own or directly read those PDFs. When an exact CUV
quotation, verification, or formal Bible-study request is encountered, they
hand the Bible-specific work to `guiding-biblical-study`. The original skill or
the top-level session router remains the response owner and incorporates the
returned result into the ongoing user workflow.

The portable flow is:

```text
non-owner skill
    -> declared RM-04A/RM-04B HANDOFF
    -> guiding-biblical-study
    -> locally owned PDFs and Bible-study rules
    -> result returned to the response owner
```

This is application-level skill composition. It does not require an MCP tool,
network service, new provider, or duplicate PDF asset.

## 4. Delegated-reference contract

Each non-owner `reference-profile.json` advances to
`skill-reference-profile-v2` and declares one record per delegated reference:

```json
{
  "reference_id": "RM-04A",
  "owner_skill": "guiding-biblical-study",
  "access_mode": "HANDOFF",
  "local_copy": false
}
```

An equivalent record is required for RM-04B. The records live in a
`delegated_references` array so ownership is unambiguous per reference. A
profile-wide `owner_skill` field is insufficient because a skill may later
delegate different references to different owners.

For every `HANDOFF` record, validation requires:

1. `reference_id` is nonempty and unique within the profile;
2. `owner_skill` resolves to a packaged sibling skill;
3. `access_mode` is exactly `HANDOFF`;
4. `local_copy` is exactly `false`;
5. the non-owner knowledge index has no local record for the reference;
6. the non-owner skill has no direct local link to the reference;
7. the owner skill packages and indexes the reference;
8. the owner skill directly links the reference where it must be consulted;
9. the non-owner `SKILL.md` names the handoff trigger, destination, return
   behavior, and fail-closed fallback.

Unknown access modes, missing owners, missing owner assets, or contradictory
local declarations fail validation.

## 5. Skill behavior

The four non-owner skills must state all of the following:

- ordinary parenting, devotion, coaching, and reflection behavior remains
  local to the selected skill;
- an exact CUV quotation or verification request hands off to
  `guiding-biblical-study`;
- formal Bible study hands off to `guiding-biblical-study`;
- the handoff supplies the user's relevant passage, question, established
  session context, and requested output;
- the result returns to the response owner rather than producing a competing
  user-facing answer;
- if the owner skill or required PDFs are unavailable, exact text must not be
  fabricated; the limitation is disclosed and an approved paraphrase or
  non-exact alternative may be offered only where existing behavior permits.

No application requirement, safety behavior, interaction gate, Scripture
authority rule, or five-skill routing decision is removed or broadened.

## 6. Archive transformation and provenance

The repair is a deterministic, auditable derivation rather than an in-place
edit:

1. verify the exact source archive digest and safe member inventory;
2. extract to a genuine system-temporary disposable root;
3. update only the four non-owner `SKILL.md`, `knowledge-index.json`, and
   `reference-profile.json` files, plus release metadata and manifests required
   by the version change;
4. retain the two PDFs only under `guiding-biblical-study` and verify their
   bytes against the source archive;
5. update the plugin version from 1.0.1 to 1.0.2 consistently;
6. regenerate deterministic member hashes and package metadata;
7. record the source archive name and SHA-256 in non-private provenance;
8. build the same candidate twice from clean roots and require identical ZIP
   bytes.

The transformation must not add private paths, credentials, caches, review
history, or unrelated source documents.

## 7. Workbench legacy onboarding

The Workbench may recognize this exact legacy flat Plugin Builder manifest as
an input profile, but it must not relabel legacy producer claims as v2/v3
evidence. It records separately:

- immutable source archive identity;
- producer-declared legacy metadata;
- Workbench-derived static validation;
- the owner's approved repair decision;
- installed-runtime observations.

Generic legacy ZIPs remain fail-closed. Recognition is bounded by the declared
legacy manifest, exact archive inventory, confined paths, and strict hashes.
The adapter may propose or execute this approved repair, but it must never
silently repair an unapproved package or publish on the strength of intake
success alone.

## 8. Verification gates

The 1.0.2 candidate must pass:

1. safe archive and manifest validation;
2. JSON parsing and schema validation;
3. skill and plugin structural validation;
4. zero stale non-owner RM-04A/RM-04B paths or index entries;
5. delegated-reference closure and owner-asset verification;
6. requirement and invariant traceability;
7. license, provenance, redistribution, and secret audit;
8. deterministic two-build equality and archive verification;
9. Codex Desktop installation and discovery;
10. representative installed-runtime handoffs from each of the four non-owner
    skills, including an unavailable-owner failure case;
11. staged Obvious One marketplace preparation and exact-delta verification;
12. marketplace installation from the staged tree and representative execution.

Static success is reported as `STATICALLY VERIFIED`. Installed handoff behavior
is not `RUNTIME VERIFIED` until it is directly observed. Upload or discovery
alone is not behavioral evidence.

The current publication target is Codex through Obvious One. OpenClaw and any
OpenAI universal-directory submission are outside this publication action and
remain `NOT VERIFIED` unless separately implemented, tested, and authorized.

## 9. Publication boundary

Local implementation, testing, deterministic artifact generation, and separate
marketplace staging do not mutate the public marketplace. Before publication,
the exact staged delta, release version, license decision, and final ZIP digest
must be reported.

The owner's request authorizes publication of this corrected 1.0.2 release to
the Obvious One marketplace after every required gate passes. It does not
authorize publishing a failed candidate, replacing unrelated marketplace
content, creating an OpenAI-directory submission, or publishing to ClawHub.

Git changes to the marketplace must remain scoped to this plugin and required
catalog/index updates. Push, merge, or other remote mutation must use the exact
verified commit and be reported separately from package readiness.

## 10. Acceptance criteria

The work is complete only when:

- the original 1.0.1 archive remains unchanged and digest-identical;
- a deterministic 1.0.2 ZIP exists with complete provenance;
- RM-04A/RM-04B occur only under `guiding-biblical-study`;
- all four non-owner profiles declare valid per-reference handoffs;
- their indexes and Markdown contain no stale local PDF paths;
- the owner skill packages, indexes, links, and uses both PDFs;
- all applicable repository and product verification passes;
- installed Codex handoff scenarios have evidence;
- the exact Obvious One marketplace delta passes verification;
- only that verified delta is published; and
- remaining OpenClaw and universal-directory gates are reported precisely.
