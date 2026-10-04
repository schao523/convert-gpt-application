# Design Assistant and Plugin Builder Preflight Remediation Design

Status: **APPROVED**

Date: 2026-10-04

Affected applications: Cool Plugin Design Assistant and Plugin Builder

Plugin Builder runtime scope: `OPENAI_ONLY_PHASE_ONE`

Approval evidence: the decision owner explicitly approved this written
specification in the originating Codex conversation on 2026-10-04.

## 1. Purpose

Correct three observed workflow defects without changing approved application
behavior, canonical requirement authority, or the W1/W2 approval model:

1. Cool Plugin Design Assistant 1.0.1 chat mode reported successful canonical
   normalization even though the delivered archive lacked required canonical
   package fields.
2. Plugin Builder allowed a W1 proposal whose generated `plugin.json` was
   missing required author and interface metadata.
3. Plugin Builder allowed a W1 proposal whose Skill references escaped their
   owning Skill through paths such as `../../resources/`.

Success means the Design Assistant cannot report a canonical package without a
digest-bound deterministic validation result, and Plugin Builder finds all
predictable manifest, Skill, reference, membership, and requirement-path
failures before calculating the W1 plan hash.

This remediation improves interface reliability and approval efficiency. It
does not reopen or modify any approved designed-application behavior.

## 2. Preserved decisions and boundaries

The implementation must preserve:

- `WORKBENCH_HANDOFF_V1_1` as the canonical producer/consumer contract;
- exact requirement `id`, `source`, `verbatim`, and update `change` values;
- strict SHA-256 verification and byte preservation;
- one semantic authority per handoff package;
- fail-closed handling of unknown, ambiguous, incomplete, or conflicting
  envelopes;
- baseline identity and preservation rules for updates;
- W1 as the only approval permitting candidate mutation;
- W2 as the only approval permitting final packaging;
- deterministic archive generation;
- Plugin Builder's approved `OPENAI_ONLY_PHASE_ONE` runtime scope; and
- the existing publication authorization boundary.

The remediation must not weaken validation, infer missing approval authority,
invent requirement content, silently repair a candidate after W1, publish an
artifact, or mutate an external marketplace.

## 3. Evidence finding

The reported Design Assistant chat transcript said canonical validation passed,
but Plugin Builder inspected the returned ZIP and found that
`package_schema_version` and `package_kind` were absent. The shared canonical
validator rejects an archive with either field missing. Therefore the transcript
is not validation evidence for the delivered bytes.

At least one evidence boundary failed:

- the chat workflow did not invoke `normalize-handoff-package`;
- it invoked only semantic `validate-handoff` validation;
- it validated a representation other than the delivered ZIP; or
- it stated an expected result without executing the deterministic operation.

The exact historical conversational action may remain unavailable. The
remediation does not depend on choosing among those cases: all successful chat
packaging must be bound to one deterministic operation result and the digest of
the archive actually returned.

Plugin Builder correctly rejected the incomplete envelope at F1. Its later
manifest and reference-layout failures are separate planning/preflight defects.

## 4. Chosen architecture

Use two complementary controls:

1. **Producer execution binding.** The Design Assistant's chat-facing Skill
   routes legacy-to-canonical transformation through the existing deterministic
   `normalize-handoff-package` operation and reports only its structured result.
2. **Consumer non-mutating preflight.** Plugin Builder compiles and validates a
   temporary proposed plugin tree before producing an approvable W1 plan.

This is preferred to a documentation-only change because prose alone cannot
prove which bytes were validated. It is preferred to a new MCP service because
the existing local deterministic normalizer and validator already implement the
required operation without network access, credentials, or a new service
boundary.

## 5. Design Assistant chat packaging contract

When a user asks Cool Plugin Design Assistant to create or regenerate a
Workbench handoff package, the chat-facing workflow must distinguish between
semantic authoring and physical packaging.

For legacy-to-canonical transformation it must:

1. preserve the approved source archive unchanged;
2. invoke `normalize-handoff-package` with explicit source, destination,
   confirming owner, and runtime scope;
3. treat only a structured `PASS` result as successful packaging;
4. require the result to identify the recognized input profile, output path,
   source archive SHA-256, output archive SHA-256, gate state, and diagnostics;
5. re-open and inventory the final output archive;
6. confirm that the re-opened archive digest equals the reported output digest;
7. confirm that the final archive classifies as `WORKBENCH_HANDOFF_V1_1` and
   passes full canonical validation; and
8. return the exact validated archive to the user.

The workflow must not manually construct `package-manifest.json` or
`workbench-handoff.json` as a substitute for deterministic normalization. It
may author approved semantic source artifacts before packaging, but canonical
package authorities are emitted only by the deterministic operation.

If deterministic execution is unavailable, fails, or cannot prove the final
archive digest, the workflow reports `HANDOFF BLOCKED`. It may explain the
missing capability and provide the command needed for an authorized local
caller, but it must not claim a canonical package or validation `PASS`.

## 6. Digest-bound result contract

A successful normalization result must expose at least:

```json
{
  "operation": "normalize-handoff-package",
  "status": "PASS",
  "input_profile": "COOL_DESIGN_ASSISTANT_FULL_V1",
  "output_profile": "WORKBENCH_HANDOFF_V1_1",
  "source_archive_sha256": "<64 lowercase hexadecimal characters>",
  "output_archive_sha256": "<64 lowercase hexadecimal characters>",
  "gate_state": "READY FOR WORKBENCH",
  "diagnostics": []
}
```

Field names may follow the existing public result-schema conventions, but the
semantics above are mandatory. The digest is calculated from the final ZIP
bytes, not an extracted tree, temporary file, or pre-publication in-memory
object. A result describing one digest must never be paired with another file.

`READY FOR WORKBENCH` remains handoff readiness only. It is not implementation,
runtime, installation, packaging, or publication evidence.

## 7. Plugin Builder pre-W1 compilation sandbox

Plugin Builder must perform a non-mutating static compilation before it creates
an approvable W1 plan or calculates the W1 plan hash.

The preflight operates in an isolated temporary directory and must not write to
the candidate workspace. It must:

1. materialize all proposed file recipes;
2. create the root `plugin.json` and synchronized
   `.codex-plugin/plugin.json` compatibility overlay;
3. validate required manifest fields, types, identities, author data, interface
   metadata, and manifest-pair synchronization;
4. validate every Skill's structure and direct local links;
5. reject absolute paths, backslashes, empty segments, and `.` or `..` path
   segments;
6. require professional references to be stored below and directly linked from
   their owning Skill;
7. apply the application-specific consultation-skill and
   `knowledge-index.json` rule only when the approved plan adopts general
   knowledge under the repository policy;
8. compare the materialized tree with `expected_members`;
9. confirm that every planned requirement implementation path and evidence
   target resolves to a declared output or check; and
10. run any additional deterministic static checks that candidate creation
    would otherwise discover before executing application behavior.

The sandbox is discarded after validation. Passing preflight does not create a
candidate and does not bypass W1.

## 8. Failure aggregation and W1 identity

All deterministic static failures found during one preflight run are returned
together in stable sorted order. The plan remains non-approvable while any such
failure exists.

The W1 review package and plan hash are produced only after preflight passes.
Consequently, repairs to manifest completeness or reference layout happen
before the first W1 approval rather than producing successive W1 revisions.

If an approved W1 is later changed for another reason, the existing hash-bound
reapproval requirement remains unchanged.

Stable diagnostics must distinguish at least:

- missing or invalid manifest fields;
- manifest-pair mismatch;
- unsafe or escaping reference paths;
- missing referenced files;
- invalid Skill structure;
- expected-member differences;
- unresolved requirement implementation paths; and
- unresolved evidence targets.

## 9. Reference-layout policy

Plugin Builder must not solve path confinement by copying every reference into
every Skill. It must plan reference ownership deliberately:

- professional knowledge belongs in the owning Skill's `references/`
  directory and is directly linked from that Skill's `SKILL.md`;
- a professional reference shared by multiple Skills is duplicated only when
  the plan records why independent ownership is required, otherwise one owning
  Skill provides the relevant response responsibility;
- general knowledge, when explicitly adopted by the application, belongs in one
  application-specific consultation Skill with one
  `references/knowledge-index.json`; and
- no Skill link may traverse outside its Skill directory.

This preserves the repository knowledge policy and avoids treating broad
reference duplication as the default compatibility repair.

## 10. Regression tests

Implementation begins with tests that fail against the current behavior for the
expected reason.

### 10.1 Producer chat-routing regression

The Design Assistant Skill contract test must prove that chat-facing handoff
packaging:

- names the deterministic normalization command;
- prohibits manual canonical-pair construction;
- requires full final-archive validation;
- requires source and output archive digests; and
- blocks rather than claiming success when execution is unavailable.

A product integration test must transform a representative approved legacy
package, re-open the returned ZIP, validate the canonical pair, and compare the
reported output digest with the returned bytes.

This automated test verifies the packaged execution contract. Direct installed
LLM conversation behavior remains `NOT VERIFIED` until separately exercised by
the owner.

### 10.2 Manifest-completeness regression

A Plugin Builder planning test supplies a proposal whose manifest recipe lacks
required author and interface fields. Current behavior reaches W1 and later
fails during candidate creation; the regression must require planning to stop
before an approvable W1 and return manifest diagnostics without candidate
mutation.

### 10.3 Reference-confinement regression

A Plugin Builder planning test supplies a Skill link such as
`../../resources/reference.md`. Current behavior reaches W1 and later fails
during candidate creation; the regression must require planning to stop before
an approvable W1 and return the unsafe-path diagnostic without candidate
mutation.

### 10.4 Combined-error regression

A proposal containing both manifest and reference defects must return both
diagnostics in deterministic order. This proves the preflight aggregates
predictable failures instead of forcing sequential W1 revisions.

## 11. Cross-product verification

The complete verification matrix includes:

1. legacy full handoff -> Design Assistant normalization -> Plugin Builder
   create intake;
2. legacy delta handoff -> Design Assistant normalization -> Plugin Builder
   update intake with an exact baseline;
3. canonical create handoff -> Plugin Builder planning;
4. canonical update handoff -> Plugin Builder planning with baseline
   preservation;
5. malformed purported-canonical input -> fail closed without output;
6. missing manifest metadata -> fail before approvable W1;
7. escaping Skill reference -> fail before approvable W1;
8. combined static defects -> one deterministic aggregated result;
9. two identical successful runs -> byte-identical normalized and packaged
   outputs; and
10. blocked or failed runs -> source, existing destinations, and candidate
    workspace remain unchanged.

Required local evidence includes the full framework suite, both product suites,
cross-product interoperability tests, deterministic-build comparisons,
extracted-artifact validation, and `git diff --check`.

## 12. Evidence and readiness

Repository and artifact tests may establish `STATICALLY VERIFIED` evidence for
the revised interface and preflight. They do not establish installed
conversation behavior.

The owner will independently test the generated application plugins. Separately,
the corrected Design Assistant and Plugin Builder release candidates require
installed-runtime tests for:

- Design Assistant chat-triggered legacy normalization;
- digest equality between the report and downloaded ZIP;
- direct Plugin Builder acceptance without repair;
- one representative create flow through W1 and W2; and
- one representative update flow with baseline preservation.

Until those tests pass, report chat execution as `NOT VERIFIED`; do not report
the affected workflow as `READY` merely because the ZIP installs or static
tests pass.

## 13. Versioning and release boundary

Reasonable patch-release candidates are:

- Cool Plugin Design Assistant `1.0.2`; and
- Plugin Builder `1.0.1`.

These version assignments are proposed for the later release plan and do not
authorize publication. Local implementation and deterministic release-candidate
builds are permitted only after approval of this written specification and its
implementation plan. Git push, tags, marketplace changes, directory submission,
and publication remain separately authorized actions.

## 14. Exclusions

This remediation does not:

- independently verify the two generated application plugins; the owner has
  retained that task;
- change approved designed-application behavior;
- change Plugin Builder's runtime scope;
- add an MCP server, network dependency, credential, database, RAG system, or
  external service;
- remove legacy compatibility profiles;
- bypass W1 or W2;
- automatically repair unknown or ambiguous authority; or
- publish any plugin or marketplace artifact.

## 15. Owner-review checklist

Approval of this written specification confirms:

- deterministic normalization, not conversational JSON construction, is the
  only successful chat packaging path;
- successful reports are bound to the digest of the returned ZIP;
- unavailable deterministic execution blocks rather than degrading silently;
- Plugin Builder performs full non-mutating static preflight before W1 hashing;
- predictable static failures are aggregated before the first W1 approval;
- reference ownership follows the repository knowledge policy rather than
  unconditional duplication;
- W1, W2, strict hashes, exact requirement authority, and fail-closed behavior
  remain unchanged; and
- installed runtime verification and all publication actions remain separate.
