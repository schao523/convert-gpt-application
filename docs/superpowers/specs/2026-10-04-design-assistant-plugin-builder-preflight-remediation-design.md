# Design Assistant and Plugin Builder Preflight Remediation Design

Status: **APPROVED — REVISION 1**

Date: 2026-10-04

Affected applications: Cool Plugin Design Assistant and Plugin Builder

Plugin Builder runtime scope: `OPENAI_ONLY_PHASE_ONE`

Approval history: the decision owner explicitly approved the original written
specification in the originating Codex conversation on 2026-10-04. Revision 1
adds controls derived from independent inspection of two generated plugin ZIPs.
The decision owner explicitly approved Revision 1 in the originating Codex
conversation on 2026-10-04. That approval authorizes Revision 1 as the design
baseline; it does not authorize implementation, publication, or external
release actions.

Revision 1 also corrects one earlier assumption: both inspected ZIPs, although
wrapped in a plugin-name directory, were successfully uploaded to ChatGPT
Desktop. Wrapped archive layout therefore remains supported and is not a
compatibility defect.

## 1. Purpose

Correct the observed workflow defects without changing approved application
behavior, canonical requirement authority, or the W1/W2 approval model:

1. Cool Plugin Design Assistant 1.0.1 chat mode reported successful canonical
   normalization even though the delivered archive lacked required canonical
   package fields.
2. Plugin Builder allowed a W1 proposal whose generated `plugin.json` was
   missing required author and interface metadata.
3. Plugin Builder allowed a W1 proposal whose Skill references escaped their
   owning Skill through paths such as `../../resources/`.
4. Generated packages duplicated large knowledge sources across multiple
   Skills, placed professional/general knowledge under `assets/`, and routed
   every Skill to essentially the same broad reference set instead of applying
   deliberate ownership and progressive disclosure.
5. A generated package exposed direct `../../scripts/...` paths in plain text
   and backticks. The current closure validator checks Markdown links and did
   not detect those additional path-bearing forms.
6. Generated tool contracts declared `python3`, while the inspected Windows
   environment exposed `python` but not `python3`. The verifier silently
   replaced either command with its own interpreter, proving fixture behavior
   without proving that the declared installed-runtime command was executable.
7. Generated manifests contained useful descriptions, but metadata quality was
   inconsistent: create-operation identity was implicit, author information was
   minimal, and category/capability values were not checked against a declared
   target vocabulary.
8. Structural validation and successful Desktop upload were not separated
   clearly enough from installed tool execution, reference consultation, and
   conversational behavior evidence.

Success means the Design Assistant cannot report a canonical package without a
digest-bound deterministic validation result, and Plugin Builder finds all
predictable manifest, Skill, reference, membership, requirement-path,
duplicate-content, tool-routing, executable-portability, and metadata-quality
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

Independent inspection of the two owner-supplied generated application ZIPs,
combined with the owner's Desktop upload report, established additional
evidence. The upload result is owner-reported runtime evidence; the remaining
findings are local artifact evidence:

- both archives uploaded successfully to ChatGPT Desktop despite their wrapped
  plugin-name directory, so flattening is not required for Desktop intake;
- both archives passed the repository's current structural validators and their
  internal expected-member and SHA-256 inventories were consistent;
- their descriptive manifest fields were present and meaningful, disproving
  the narrower claim that the manifests contained no descriptive information;
- both archives contained substantial exact duplicate content, including large
  knowledge files repeated across Skills;
- one archive placed knowledge below each Skill's `assets/`; the other repeated
  shared references at the root and in every Skill;
- plain-text and backticked escaping script paths were not detected by the
  current Markdown-link-oriented validation;
- bundled deterministic tools passed when invoked through the development
  verifier, but the declared `python3` command was unavailable in the inspected
  Windows environment and verifier substitution masked that mismatch; and
- installed conversational behavior, installed tool routing, and actual
  reference consultation remain `NOT VERIFIED`.

## 4. Chosen architecture

Use three complementary controls:

1. **Producer execution binding.** The Design Assistant's chat-facing Skill
   routes legacy-to-canonical transformation through the existing deterministic
   `normalize-handoff-package` operation and reports only its structured result.
2. **Consumer non-mutating preflight.** Plugin Builder compiles and validates a
   temporary proposed plugin tree before producing an approvable W1 plan.
3. **Artifact-quality and runtime-binding evidence.** The same preflight audits
   knowledge ownership, exact-content duplication, all path-bearing bindings,
   manifest presentation metadata, and declared executable commands; later
   verification reports structural, installation, and behavioral evidence as
   distinct layers.

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
4. validate every Skill's structure and every local path-bearing reference,
   including Markdown links, inline code, plain command text, structured tool
   bindings, and generated launcher metadata;
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
10. require each applicable file recipe to declare professional knowledge,
    general knowledge, executable tool, or ordinary static-asset ownership and
    validate its policy-specific placement; ambiguous knowledge classification
    blocks rather than being inferred solely from a filename or directory;
11. group proposed files by SHA-256 and report exact duplicate groups, member
    counts, and duplicate byte totals;
12. validate stable tool identifiers, runtime adapters, and the availability or
    deterministic resolution of every declared executable command;
13. validate manifest presentation metadata against the selected target's
    declared vocabulary and release profile;
14. require the candidate manifest to state `operation` as `create` or `update`;
    and
15. run any additional deterministic static checks that candidate creation
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
- unresolved evidence targets;
- misplaced knowledge or ambiguous reference ownership;
- unjustified exact-content duplication;
- path-bearing text or tool bindings that escape their allowed root;
- unavailable or unbound runtime executables;
- silent verifier command substitution;
- missing or invalid operation identity; and
- target-specific metadata-quality failures.

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

`assets/` is reserved for non-knowledge static deliverables such as templates,
images, and user-facing output assets. It must not be used to bypass the
professional/general knowledge placement and linking rules.

Before W1, the plan must disclose every exact duplicate-content group, the
owning paths, and the avoidable duplicate bytes. Repeating the same professional
source across multiple Skills is allowed only when the W1 plan records an
application-specific independent-ownership reason. Large universal copies and
copy-to-every-Skill repairs fail preflight by default. This design intentionally
does not impose an arbitrary total ZIP-size limit; it enforces explainable
ownership and deterministic duplicate evidence instead.

This preserves the repository knowledge policy and avoids treating broad
reference duplication as the default compatibility repair.

## 10. Tool routing and executable portability

Portable Skills route deterministic operations through stable application-facing
tool identifiers. They must not expose direct `../` or `../../` filesystem
paths to root scripts, regardless of whether the path appears as a Markdown
link, inline code, plain prose, YAML/JSON, or a command example.

Runtime-specific script locations and interpreter selection belong in thin
adapters or launchers. A tool declaration must either name an executable proven
available in the selected target environment or use a documented adapter token
resolved by that runtime. Literal `python3` is not portable evidence on Windows.

Verification must record both the declared command and the command actually
executed. A verifier may resolve a declared adapter token to its own interpreter,
but it must not silently replace a literal executable and then report the
literal command as verified. Clean-environment checks must prove the packaged
adapter or executable path on every target runtime in scope.

## 11. Manifest presentation and operation identity

Both root and compatibility-overlay manifests must contain synchronized,
non-placeholder descriptive metadata coherent with the approved behavior.
Private/local structural acceptance requires at least the existing required
identity, description, author/developer, interface, and default-prompt fields,
plus an explicit `operation` value of `create` or `update` in the Builder
candidate manifest.

Target category and capability values must use a versioned, declared vocabulary
and casing. An unknown value is either rejected or explicitly declared as a
target extension; it must not pass solely because it is a non-empty string.

Homepage, repository, license, keywords, icons, and brand colors are evaluated
under a release-readiness profile. Their absence does not block a private/local
candidate unless the selected target requires them, but the W1 and final report
must mark each as supplied, not applicable, or unresolved. Human-readable UTF-8
JSON is preferred for review, provided deterministic serialization and hashes
remain stable; escaped Unicode is valid and is not itself a defect.

## 12. Packaging and evidence boundaries

Plugin Builder must retain support for a ZIP whose single top-level directory
contains the plugin tree, because both inspected wrapped packages were accepted
by ChatGPT Desktop. A flat-root archive may be offered as a separate target
profile only if a target contract requires it; preflight must not reject the
wrapped layout merely for being wrapped.

The final build report must bind the candidate ZIP digest to:

- member inventory and per-member hashes;
- exact duplicate-content groups and duplicate-byte totals;
- knowledge classification and ownership;
- declared and observed tool commands;
- manifest target/profile results; and
- structural, installation, tool-execution, reference-consultation, and
  conversational-behavior evidence as separate states.

A sidecar evidence report may carry this information so the installable plugin
format is not polluted with development-only material. The report and ZIP must
be digest-bound. `PASS` for archive integrity or Desktop upload must never be
reported as runtime-behavior verification.

## 13. Regression tests

Implementation begins with tests that fail against the current behavior for the
expected reason.

### 13.1 Producer chat-routing regression

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

### 13.2 Manifest-completeness regression

A Plugin Builder planning test supplies a proposal whose manifest recipe lacks
required author and interface fields. Current behavior reaches W1 and later
fails during candidate creation; the regression must require planning to stop
before an approvable W1 and return manifest diagnostics without candidate
mutation.

### 13.3 Reference-confinement regression

A Plugin Builder planning test supplies a Skill link such as
`../../resources/reference.md`. Current behavior reaches W1 and later fails
during candidate creation; the regression must require planning to stop before
an approvable W1 and return the unsafe-path diagnostic without candidate
mutation.

### 13.4 Knowledge ownership and duplication regressions

Representative proposals derived from the inspected packages must prove that:

- professional/general knowledge placed under `assets/` is rejected;
- one professional source copied into every Skill without an approved
  independent-ownership reason is rejected before W1;
- duplicate groups and duplicate byte totals are deterministic; and
- a policy-compliant owning Skill or consultation Skill passes without broad
  copying.

### 13.5 Path-bearing text and tool-routing regressions

Tests must reject escaping paths such as `../../scripts/tool.py` when they occur
in Markdown, inline code, plain text, structured bindings, or command examples.
A stable tool identifier bound through an allowed runtime adapter must pass.

### 13.6 Executable-portability regressions

A Windows-target fixture in which `python3` is unavailable must fail a literal
`python3` declaration. A documented interpreter adapter must pass and record
both declared and observed commands. A test must prove that silent verifier
substitution is detected rather than treated as installed-runtime evidence.

### 13.7 Manifest-quality regressions

Tests must require explicit create/update operation identity, synchronized
descriptive fields, and valid target category/capability values. Separate
private/local and release-readiness profiles must prove that optional listing
metadata is reported without becoming an unintended private-install blocker.

### 13.8 Wrapped-package compatibility regression

A valid wrapped package must remain accepted by the Desktop-target packaging
profile. This guards against reintroducing the disproved flat-root assumption.

### 13.9 Combined-error regression

A proposal containing both manifest and reference defects must return both
diagnostics in deterministic order. This proves the preflight aggregates
predictable failures instead of forcing sequential W1 revisions.

## 14. Cross-product verification

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
8. misplaced or universally copied knowledge -> fail before approvable W1 with
   deterministic ownership and duplicate evidence;
9. path traversal in Markdown, inline code, plain text, or tool binding -> fail
   before approvable W1;
10. unavailable literal executable or silent verifier substitution -> fail;
11. supported runtime adapter -> declared and observed commands recorded;
12. invalid operation/category/capability metadata -> target-profile failure;
13. valid wrapped Desktop package -> accepted without forced flattening;
14. combined static defects -> one deterministic aggregated result;
15. two identical successful runs -> byte-identical normalized and packaged
   outputs; and
16. blocked or failed runs -> source, existing destinations, and candidate
    workspace remain unchanged.

Required local evidence includes the full framework suite, both product suites,
cross-product interoperability tests, deterministic-build comparisons,
extracted-artifact validation, duplicate-content audit, declared-versus-observed
tool-command evidence, and `git diff --check`.

## 15. Evidence and readiness

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
- one representative update flow with baseline preservation;
- declared tool-command resolution in a clean target environment;
- representative packaged-tool execution without silent command substitution;
- actual consultation of one professional and, when adopted, one general
  knowledge reference; and
- wrapped-package upload and discovery, recorded separately from execution.

Until those tests pass, report chat execution as `NOT VERIFIED`; do not report
the affected workflow as `READY` merely because the ZIP installs or static
tests pass.

## 16. Versioning and release boundary

Reasonable patch-release candidates are:

- Cool Plugin Design Assistant `1.0.2`; and
- Plugin Builder `1.0.1`.

These version assignments are proposed for the later release plan and do not
authorize publication. Local implementation and deterministic release-candidate
builds are permitted only after approval of this written specification and its
implementation plan. Git push, tags, marketplace changes, directory submission,
and publication remain separately authorized actions.

## 17. Exclusions

This remediation does not:

- independently verify the two generated application plugins; the owner has
  retained that task, although their findings define regression fixtures for
  this remediation;
- change approved designed-application behavior;
- change Plugin Builder's runtime scope;
- add an MCP server, network dependency, credential, database, RAG system, or
  external service;
- remove legacy compatibility profiles;
- bypass W1 or W2;
- automatically repair unknown or ambiguous authority; or
- publish any plugin or marketplace artifact.

## 18. Owner-review checklist

Approval of this written specification confirms:

- deterministic normalization, not conversational JSON construction, is the
  only successful chat packaging path;
- successful reports are bound to the digest of the returned ZIP;
- unavailable deterministic execution blocks rather than degrading silently;
- Plugin Builder performs full non-mutating static preflight before W1 hashing;
- predictable static failures are aggregated before the first W1 approval;
- reference ownership follows the repository knowledge policy rather than
  unconditional duplication;
- exact-content duplication is measured and unjustified universal copying is
  blocked before W1;
- `assets/` cannot be used to bypass knowledge-reference policy;
- every path-bearing form and stable tool binding is validated, not only
  Markdown links;
- runtime adapters make executable selection explicit and verification records
  declared and observed commands without silent substitution;
- candidate operation identity and target metadata vocabularies are validated;
- wrapped plugin-name-directory ZIPs remain supported for Desktop upload;
- structural validity, successful installation, tool execution, reference use,
  and conversational behavior remain distinct evidence layers;
- W1, W2, strict hashes, exact requirement authority, and fail-closed behavior
  remain unchanged; and
- installed runtime verification and all publication actions remain separate.
