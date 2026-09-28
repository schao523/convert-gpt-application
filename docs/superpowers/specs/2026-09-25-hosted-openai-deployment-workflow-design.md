# Hosted OpenAI Plugin Deployment Workflow Design

## 1. Executive Summary

The Conversion Workbench produces one canonical converted plugin whose
application behavior, skills, references, tools, capabilities, and invariants
remain authoritative across distribution targets. OpenAI hosted deployment,
Obvious-One marketplace distribution, and future OpenAI public submission are
separate channels generated from that canonical source. None is the source of
truth for the others.

This design adds a first-class OpenAI hosted archive target with two explicit
operations:

- `OPENAI_HOSTED_CREATE` builds a complete archive for adding a new manually
  uploaded plugin to an eligible OpenAI workspace.
- `OPENAI_HOSTED_UPDATE` builds a complete replacement archive for the existing
  hosted plugin identity and directs the user to upload it as a new version of
  that plugin rather than create a duplicate.

The framework uses an application-owned `hosted-deployment-contract-v1` and
non-interactive commands to plan, validate, build, and verify a complete hosted
archive. A previous hosted ZIP is not required for ordinary creation or update.
For an existing manually uploaded plugin whose identity has not yet been
recorded, an optional one-time identity-import command safely inspects an
exported ZIP and writes an unapproved proposal. A decision owner must approve
the resulting identity record before it can authorize an update.

The first version stops at deterministic, locally verified artifacts. It does
not authenticate, upload, install, publish, submit, or read back hosted state.
Local execution evidence never upgrades hosted execution evidence. Obvious-One
remains an independent pre-public distribution channel; hosted deployment does
not require or mutate a marketplace.

## 2. Goals and Non-goals

### Goals

- **HOD-001:** Build complete OpenAI hosted plugin archives directly from one
  canonical converted application without requiring marketplace publication.
- **HOD-002:** Support explicit `OPENAI_HOSTED_CREATE` and
  `OPENAI_HOSTED_UPDATE` operations with different identity prerequisites.
- **HOD-003:** Preserve approved application behavior and invariants while
  allowing thin target-specific manifests, metadata, and compatibility routing.
- **HOD-004:** Require explicit application-owned lineage, content mappings,
  rights, identity, capability, fallback, and channel-status decisions.
- **HOD-005:** Reuse schema-v3 content classification and redistribution
  evidence for canonical application files without changing Codex or OpenClaw
  distribution semantics.
- **HOD-006:** Build a deterministic complete ZIP and a deterministic
  machine-readable artifact set whose bytes are independent of host enumeration
  order and line-ending configuration.
- **HOD-007:** Verify the submitted archive as a complete package rather than
  modeling undocumented hosted overlay or deletion behavior.
- **HOD-008:** Optionally import identity from an existing hosted ZIP exactly
  once without copying unapproved content or treating the ZIP as canonical.
- **HOD-009:** Preserve an existing hosted identity during update and require a
  strictly newer target version than the last owner-confirmed hosted version.
- **HOD-010:** Declare every non-instruction capability, its required or
  optional status, provider, artifacts, local verification, hosted verification,
  and unavailability policy.
- **HOD-011:** Keep package-static, local-execution, hosted-execution, upload,
  installation, and publication evidence separate.
- **HOD-012:** Report OpenAI hosted, Obvious-One, and OpenAI public-submission
  channel status without mutating any channel.
- **HOD-013:** Emit exactly one ASCII-safe `result-schema-v1` document for every
  CLI success, block, deterministic failure, and environment failure.
- **HOD-014:** Preserve the last verified artifact directory when planning,
  validation, building, or verification fails.
- **HOD-015:** Remain non-interactive so an agent, script, CI job, future client,
  or human can call the same deterministic interface.
- **HOD-016:** Keep generic production modules application-neutral while using
  Vibe Coding Designer as the first create-and-update canary.

### Non-goals

- Uploading, installing, sharing, publishing, or updating a live OpenAI plugin.
- Authenticating a caller or inferring a decision owner's legal authority.
- Inferring whether a plugin already exists in a workspace.
- Guaranteeing that a user selects the correct existing plugin in the hosted UI.
- Claiming that omitted files are deleted or preserved by an undocumented
  hosted installation mechanism.
- Treating a locally verified archive as hosted runtime evidence or `READY`.
- Changing distribution-contract schema v3, marketplace preparation, Codex
  packaging, OpenClaw packaging, ClawHub behavior, or RAG contracts.
- Publishing or synchronizing Obvious-One, submitting to the public Plugins
  Directory, or implementing an OpenAI submission portal client.
- Generating application prompts, routers, capability fallbacks, rights,
  identity, or lineage decisions without decision-owner approval.
- Committing an exported hosted ZIP or importing its content wholesale.
- Converting the Conversion Workbench itself into a plugin.

## 3. Users, Actors, and Trust Boundaries

- **Conversion caller:** supplies explicit application, contract, optional
  identity-import source, and output paths. Caller identity is not approval.
- **Decision owner:** approves operation type, hosted identity, version,
  lineage, rights, mappings, target adapters, capabilities, fallbacks, and
  channel-status declarations.
- **Canonical application workspace:** owns portable application logic,
  distribution evidence, hosted-deployment declarations, target adapters,
  invariants, and application regression tests.
- **Generic framework:** parses, inventories, validates, canonicalizes, builds,
  verifies, and reports. It does not make product or publication decisions.
- **Hosted identity record:** application-owned evidence of an existing hosted
  package identity and the last owner-confirmed deployed version. It is not a
  credential and is not live platform state.
- **Exported hosted ZIP:** optional, untrusted, read-only input used only to
  propose an initial identity record for an existing hosted plugin.
- **Target adapter:** application-owned packaging metadata or compatibility
  routing required by OpenAI. It must not fork canonical application logic.
- **OpenAI hosted service:** outside the v1 execution boundary.
- **Obvious-One marketplace:** independent distribution boundary; read-only for
  channel reporting and unchanged by this workflow.
- **OpenAI public Plugins Directory:** independent future publication boundary.

The framework verifies evidence shape, content, and internal consistency. It
cannot infer whether a manual upload occurred or whether a person had authority
to approve lineage, rights, or deployment state.

## 4. Use Cases and Flows

### Create a new hosted plugin archive

The caller selects `OPENAI_HOSTED_CREATE`, supplies the canonical application
configuration, and plans the deployment. The target package identity and
version come from approved application-owned declarations. No previous hosted
ZIP, hosted identity record, GitHub marketplace, or Obvious-One publication is
required. Validation and build produce a complete archive and deterministic
reports with `openai_hosted: PENDING_ACTION`.

After local verification, a permitted workspace administrator may upload the
archive through the supported OpenAI UI. That manual action is outside v1. A
future caller may record owner-confirmed deployment evidence for later updates;
the framework does not infer it from a successful build.

### Update an existing hosted plugin archive

The caller selects `OPENAI_HOSTED_UPDATE` and references an approved hosted
identity record. The contract must preserve the exact package identity and use
a version strictly greater than the last owner-confirmed hosted version. The
framework builds a complete replacement archive from the current canonical
application and target adapter. It does not require or merge the previous ZIP.

The completion report instructs the user to open the existing hosted plugin and
use its new-version upload action. It never instructs the user to add a second
plugin for an update operation.

### Bootstrap identity for an existing hosted plugin

When an existing hosted plugin predates this workflow, the caller may supply an
exported ZIP to `import-hosted-identity`. The importer performs hostile-archive
checks, hashes the archive and relevant members, and extracts only approved
identity candidates such as package name, version, manifest metadata, and
declared presentation-asset hashes. It writes a new proposal in an ignored
output root.

The importer does not copy application content, overwrite a contract, approve
lineage, or assert that the archive is currently deployed. The decision owner
reviews the proposal and records a tracked `hosted-identity.json`. Ordinary
future updates use that identity record and no longer need the exported ZIP.

### Recover from unresolved decisions

Missing operation, lineage, classification, rights, target mapping, identity,
capability, fallback, or channel evidence returns `BLOCKED`. Diagnostics use
safe relative paths, stable codes, and candidate decisions. The framework never
prompts; a client may guide the decision owner and record the approved answer
before rerunning validation from the beginning.

### Coordinate channels without mutating them

The deployment manifest reports separately whether OpenAI hosted deployment,
Obvious-One distribution, and public submission are `UNPUBLISHED`,
`PENDING_ACTION`, `CURRENT_BY_DECLARATION`, `STALE`, or `UNKNOWN`. Every status
includes its evidence source and observation time when applicable. No status is
upgraded based only on a local build.

## 5. Software Form and System Boundaries

The enhancement remains part of the Python 3.11+
`obvious_one_plugin_framework` library and non-interactive CLI. It introduces
no Web, desktop, TUI, daemon, database, required network service, or credential.

Generic production modules live under:

```text
src/obvious_one_plugin_framework/
  hosted_deployment_contract.py
  hosted_identity.py
  hosted_deployment_planner.py
  hosted_deployment_builder.py
  hosted_deployment_verifier.py
```

Application-owned declarations live under:

```text
applications/<plugin-id>/hosted-openai/
  deployment.json
  lineage-decision.json
  hosted-identity.json           # required only for update
  adapter/
    plugin.json
    .codex-plugin/plugin.json
    skills/...                   # compatibility only when approved
```

Generated output lives below ignored roots:

```text
dist/openai/<plugin-id>/<version>/
  <plugin-id>-<version>.zip
  deployment-manifest.json
  validation-report.json
  deployment-report.json
```

Identity-import proposals and diagnostics remain below `.tmp` or another
caller-selected ignored output root. Machine-specific paths remain only in
ignored `conversion.local.json`.

The framework never writes to the OpenAI service, installed plugin cache,
marketplace repository, original GPT source archive, or canonical application
source.

## 6. Interface Specification

### CLI commands

Plan a create or update deployment:

```powershell
python -B -m obvious_one_plugin_framework.cli plan-hosted-deployment `
  --application .\applications\<plugin-id>\conversion.json `
  --operation OPENAI_HOSTED_CREATE `
  --output .\.tmp\<plugin-id>-hosted-deployment-proposal.json `
  --json
```

For update, use `--operation OPENAI_HOSTED_UPDATE`. Planning suggests mappings
and unresolved decisions but never approves them.

Optionally propose identity from an existing hosted archive:

```powershell
python -B -m obvious_one_plugin_framework.cli import-hosted-identity `
  --application .\applications\<plugin-id>\conversion.json `
  --archive <exported-hosted-plugin.zip> `
  --output .\.tmp\<plugin-id>-hosted-identity-proposal.json `
  --json
```

Validate an approved deployment contract:

```powershell
python -B -m obvious_one_plugin_framework.cli validate-hosted-deployment `
  --contract .\applications\<plugin-id>\hosted-openai\deployment.json `
  --json
```

Build the complete artifact set:

```powershell
python -B -m obvious_one_plugin_framework.cli build-hosted-deployment `
  --contract .\applications\<plugin-id>\hosted-openai\deployment.json `
  --output .\dist\openai\<plugin-id>\<version> `
  --json
```

Verify the artifact set and complete submitted archive:

```powershell
python -B -m obvious_one_plugin_framework.cli verify-hosted-deployment `
  --contract .\applications\<plugin-id>\hosted-openai\deployment.json `
  --artifact .\dist\openai\<plugin-id>\<version> `
  --json
```

Every command emits exactly one `result-schema-v1` document:

- exit `0`: `PASS`;
- exit `2`: `BLOCKED` or invocation/contract error, distinguished by JSON;
- exit `3`: deterministic build or verification `FAIL`;
- exit `4`: local I/O or environment failure.

Planning and identity import create only a new proposal destination and refuse
to overwrite it. Validation and verification perform no persistent mutation.
Building transactionally creates or replaces only the requested versioned
artifact directory and preserves the last verified directory on failure.

### Public Python API

Public immutable models and functions mirror the CLI:

- `load_hosted_deployment_contract`;
- `plan_hosted_deployment`;
- `inventory_hosted_identity_archive`;
- `propose_hosted_identity`;
- `validate_hosted_deployment`;
- `build_hosted_deployment`;
- `verify_hosted_deployment`.

Public functions return typed results or raise framework errors with stable
codes. Private underscore-prefixed helpers are not product dependencies.

## 7. Component Architecture

### Hosted deployment contract

Strictly parses schema v1, rejects unknown keys, confines relative paths, and
loads the application configuration, schema-v3 distribution contract, lineage,
identity, mappings, target adapter, expected skills, invariant tests,
capabilities, and channel declarations. Its schema version is independent of
the distribution-contract schema.

### Hosted identity importer

Streams an untrusted optional ZIP, rejecting traversal, absolute paths,
duplicates, case-fold collisions, encryption, links, unsupported compression,
and configured expansion limits. It hashes the archive and identity-bearing
members and emits an unapproved proposal without copying member bytes into the
application workspace. Generic reports never contain the caller's private
archive path.

### Planner

Enumerates the canonical application files selected by schema-v3 distribution
rules and approved target-adapter candidates. Every selected target path
receives one proposed mapping. The planner identifies operation-specific gaps,
including a missing identity record for update, but never approves decisions.

### Builder

Resolves approved mappings, applies existing canonical content policies,
creates a complete sorted ZIP with fixed metadata, and writes the ZIP and three
canonical JSON reports into a sibling staged directory. It audits the staged
artifact set before atomically replacing the requested output directory.

The builder copies portable application content and approved target adapters;
it does not generate application prompt text or fork portable behavior.

### Complete-archive verifier

Treats the built ZIP as the entire submitted package. It validates archive
safety, exact member allowlist, both manifests, identity and version,
presentation metadata, skill discovery, explicit-only policy, references,
indexes, assets, application invariants, capability artifacts, declared local
tests, report consistency, and deterministic rebuild evidence.

It does not simulate undocumented hosted retention or deletion. Any difference
between submitted archive behavior and installed hosted behavior remains a
post-upload runtime-validation concern.

Generic modules contain no Vibe- or Bible-specific identity, skill, content, or
acceptance assertion.

## 8. Data and Persistence

### Hosted-deployment contract schema v1

```json
{
  "schema_version": 1,
  "application_id": "vibe-coding-designer",
  "operation": "OPENAI_HOSTED_CREATE",
  "lineage": {
    "source_inventory": "../docs/source-inventory.json",
    "canonical_distribution_contract": "../openclaw/distribution.json",
    "hosted_lineage_decision": "lineage-decision.json"
  },
  "identity": {
    "package_name": "vibe-coding-designer",
    "record": null
  },
  "target": {
    "version": "1.1.0",
    "archive_name": "vibe-coding-designer-1.1.0.zip",
    "portable_manifest": "adapter/plugin.json",
    "legacy_manifest": "adapter/.codex-plugin/plugin.json",
    "max_archive_bytes": 10000000
  },
  "content": {
    "canonical_mappings": [],
    "adapter_mappings": []
  },
  "validation": {
    "expected_skills": [],
    "explicit_only_skills": [],
    "required_application_tests": [],
    "capabilities": []
  },
  "channels": {
    "openai_hosted": {
      "status": "UNPUBLISHED",
      "evidence": "decision-owner declaration"
    },
    "obvious_one": {
      "status": "CURRENT_BY_DECLARATION",
      "evidence": "approved marketplace release record"
    },
    "openai_public": {
      "status": "UNPUBLISHED",
      "evidence": "decision-owner declaration"
    }
  }
}
```

For `OPENAI_HOSTED_CREATE`, `identity.record` must be `null`; the approved
package name comes from the canonical or target manifest decision. For
`OPENAI_HOSTED_UPDATE`, `identity.record` must reference an approved
`hosted-identity.json`, its package name must match exactly, and the target
version must be strictly greater than `last_confirmed_version`.

### Hosted identity record schema v1

```json
{
  "schema_version": 1,
  "application_id": "vibe-coding-designer",
  "package_name": "gpt-e9ed8a960ed122e05ddb75f341a810a5",
  "last_confirmed_version": "0.9.0-experiment.1",
  "last_confirmed_archive_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "origin": "imported_hosted_archive",
  "deployment_confirmation": {
    "status": "owner_confirmed",
    "recorded_at": "2026-09-25T00:00:00Z",
    "evidence_reference": "docs/source-decisions.md"
  }
}
```

`origin` is `imported_hosted_archive` or `prior_verified_deployment`. The
identity record contains no credential, workspace identifier, private absolute
path, or copied source content. The framework validates owner-confirmed evidence
but cannot independently prove that the recorded upload occurred.

Identity import emits `hosted-identity-proposal-v1` with candidate values,
archive/member hashes, unresolved approval fields, and safe relative member
names. A proposal is never accepted as an identity record.

### Canonical and adapter mappings

Each mapping has a stable ID, source path, target path, copy mode,
classification, and redistribution reference. Source kinds are
`canonical_application` and `hosted_adapter`. Copy modes are `copy_file` and
`copy_tree`. Target paths are unique under case folding.

Canonical application files must be selected and approved by the referenced
schema-v3 distribution contract. Hosted-adapter files have application-owned
provenance and rights evidence. An adapter may contain manifests, presentation
metadata, and an approved compatibility router, but no duplicated portable
skill or tool implementation.

The complete archive member set is derived exclusively from approved mappings
and required generated metadata. Unmapped files are excluded, and every mapped
file must resolve to exactly one content rule.

### Capability contracts

A capability contract is required when application behavior depends on
packaged executable code, exact structured data, a hosted-native facility, or
an external adapter. Each capability has:

- unique stable `id`;
- `requirement`: `required` or `optional`;
- `provider_kind`: `packaged_executable`, `hosted_native`, or
  `external_adapter`;
- `artifact_paths`: all package-owned files required by the provider;
- `local_verification_test`: one declared product-test identifier or `null`;
- `hosted_verification`: `required_after_install`;
- `on_unavailable`: `block` or `use_declared_fallback`; and
- an owner-approved `fallback` only for an optional capability using
  `use_declared_fallback`.

A required capability must use `block`; no fallback may substitute for a
required invariant. `packaged_executable` requires at least one artifact.
Provider kinds without package-owned files use an empty artifact list. Every
declared artifact must exist in the complete archive and pass rights, secret,
and content-policy validation.

Local verification proves only execution in the conversion environment. The
v1 verifier always reports hosted capability execution as `NOT VERIFIED`. A
future runtime phase must report an observed missing required capability as
`required_hosted_capability_unavailable` and may apply only the exact approved
fallback for an optional capability.

### Channel-status records

The permitted status values are:

- `UNPUBLISHED`: explicitly declared not deployed or published;
- `PENDING_ACTION`: a verified artifact exists but external action is pending;
- `CURRENT_BY_DECLARATION`: explicit evidence says the channel carries the
  declared canonical version, without live read-back;
- `STALE`: explicit evidence identifies an older canonical version;
- `UNKNOWN`: evidence is absent or insufficient.

Every status has an evidence reference. Local build changes only the generated
deployment report to `PENDING_ACTION`; it does not mutate tracked channel
records or mark any external channel current.

No framework database is introduced. Contracts and approved evidence are
tracked application files. Proposals, reports, and artifacts are immutable
files in caller-selected ignored output roots.

## 9. Services and Integrations

The conversion host requires Python 3.11 or newer and standard-library ZIP
support. Existing application tests may require their already declared local
dependencies. These requirements do not assert that OpenAI hosted execution
provides the same binaries, libraries, filesystem access, apps, or services.

The first version uses no OpenAI API, browser automation, Plugin Creator API,
credential, upload, install, read-back, marketplace mutation, or submission
portal integration. A future authenticated adapter requires a separate design
and explicit authorization boundary.

OpenAI hosted archive upload, GitHub marketplace synchronization, and public
Plugins Directory submission are separate external mechanisms. The framework
may describe their declared status but cannot use one as evidence for another.

The Agent Plugins manifest schema is an external format. Validation uses the
supported schema identifier and application-owned manifest bytes without
downloading schemas during a build.

## 10. Workflow Specification

### Create state progression

```text
CANONICAL_SOURCE_VALIDATED
    -> CREATE_PLANNED
    -> OWNER_DECISIONS_RECORDED
    -> DEPLOYMENT_CONTRACT_VALIDATED
    -> COMPLETE_ARCHIVE_BUILT
    -> LOCAL_ARTIFACT_VERIFIED
    -> READY_FOR_UPLOAD_REVIEW
```

### Update state progression

```text
CANONICAL_SOURCE_VALIDATED
    -> HOSTED_IDENTITY_VALIDATED
    -> UPDATE_PLANNED
    -> OWNER_DECISIONS_RECORDED
    -> DEPLOYMENT_CONTRACT_VALIDATED
    -> COMPLETE_ARCHIVE_BUILT
    -> LOCAL_ARTIFACT_VERIFIED
    -> READY_FOR_UPLOAD_REVIEW
```

Optional bootstrap before update:

```text
EXPORTED_ARCHIVE_INSPECTED
    -> IDENTITY_PROPOSAL_WRITTEN
    -> OWNER_APPROVAL_REQUIRED
    -> HOSTED_IDENTITY_RECORDED
```

Any stage terminates as `BLOCKED` when an owner decision is missing and as
`FAIL` when input or generated bytes violate a deterministic rule. Downstream
gates are `NOT VERIFIED` when prerequisites do not pass.

Detailed create or update workflow:

1. Load the application configuration and schema-v3 distribution contract.
2. Validate source inventory, lineage, rights, and the explicit operation.
3. For update only, validate the approved hosted identity record and version
   progression.
4. Inventory canonical and adapter candidates.
5. Produce or validate exact mappings, capability contracts, fallbacks,
   expected skills, invariant tests, and channel evidence.
6. Validate both manifests, identity, version, interface metadata, starter
   prompts, content policy, secrets, dependency declarations, and archive size.
7. Materialize the complete archive from canonical and adapter mappings.
8. Write deterministic deployment, validation, and manifest JSON documents.
9. Audit the staged artifact directory and atomically replace only the requested
   output directory.
10. Verify the complete ZIP member set and run declared local product commands.
11. Rebuild independently and compare exact bytes when deterministic evidence
    is required.
12. Emit artifact hashes, exact member inventory, capability gates, channel
    declarations, and `upload_status: NOT_PERFORMED`.

There are no automatic retries for deterministic failures. A changed canonical
source, target adapter, identity record, operation, or owner decision requires
validation from the beginning.

## 11. Quality Attributes

- **Determinism:** identical logical inputs yield byte-identical ZIP and JSON
  artifacts across enumeration order and supported host operating systems.
- **Reliability:** a failed operation cannot invalidate the last verified
  versioned artifact directory.
- **Security:** paths are confined; optional imported ZIPs and built archives
  are checked for traversal, aliases, links, encryption, collisions, expansion,
  secrets, and private-path leakage.
- **Maintainability:** contract, identity, planning, building, and verification
  remain separate modules with public typed boundaries.
- **Observability:** reports contain stable status, code, diagnostics,
  artifacts, mutations, exact input identities, and per-gate evidence.
- **Performance:** file enumeration and hashing are linear in selected input
  bytes; configured member and byte limits bound archive work.
- **Cross-platform compatibility:** archive paths are POSIX-relative; text is
  canonical UTF-8 LF; binary bytes are exact; case-fold collisions fail.
- **Compatibility:** existing framework and schema-v3 commands remain
  unchanged. The hosted deployment contract begins at schema v1.
- **Accessibility and localization:** no framework UI exists. Stable codes are
  locale-neutral for future clients.

## 12. Security and Privacy

- Application, contract, adapter, identity, optional imported archive,
  temporary, and output paths are explicitly supplied and confined.
- Identity import rejects traversal, absolute paths, duplicates, case-fold
  collisions, encrypted members, links, unsupported compression, excessive
  members, and excessive expansion before reading candidate content.
- Import reports never serialize the caller's archive path and never copy
  member content into tracked application files.
- Text canonicalization and existing secret audits apply to every packaged text
  file. Binary classification cannot evade forbidden-name or size checks.
- Rights, identity, deployment confirmation, lineage, and channel status are
  explicit evidence, never inferred from caller identity or folder proximity.
- Application-owned commands run only when explicitly declared and within
  isolated writable roots.
- Credentials, workspace identifiers, authentication tokens, and private
  absolute paths are forbidden in contracts and reports.
- The framework never uploads, installs, publishes, submits, pushes, tags, or
  changes sharing or visibility.

## 13. Validation and Acceptance

Implementation is test-first. Each behavior starts with a focused failing test
whose failure is caused by missing behavior rather than fixture or sandbox
errors.

### Contract, planning, and recovery acceptance

- **HOD-A01 / HOD-001, HOD-002:** create planning requires no baseline archive,
  hosted identity record, or marketplace evidence.
- **HOD-A02 / HOD-002, HOD-009:** update validation requires an approved hosted
  identity record, exact package-name preservation, and a strictly newer target
  version.
- **HOD-A03 / HOD-003, HOD-004:** absent or inconsistent lineage returns
  `hosted_lineage_unresolved` before output mutation.
- **HOD-A04 / HOD-004:** proposals list every candidate path and unresolved
  decision without modifying an approved contract.
- **HOD-A05 / HOD-004, HOD-005:** zero or multiple content-rule matches return
  `unclassified_deployment_file` or `ambiguous_deployment_mapping`.
- **HOD-A06 / HOD-013, HOD-015:** every command emits one valid
  `result-schema-v1` document, never prompts, and behaves identically for
  identical explicit inputs regardless of caller type.

### Optional identity-import acceptance

- **HOD-A07 / HOD-008:** a valid exported archive produces exact archive and
  identity-member hashes without a serialized private path or copied content.
- **HOD-A08 / HOD-008:** traversal, absolute paths, duplicates, case-fold
  collisions, links, encryption, compression, and archive-limit violations fail
  before proposal mutation.
- **HOD-A09 / HOD-008:** the importer refuses an existing destination and never
  overwrites a tracked identity record or deployment contract.
- **HOD-A10 / HOD-008:** an identity proposal cannot satisfy update validation;
  only an approved `hosted-identity.json` can.

### Complete-archive and manifest acceptance

- **HOD-A11 / HOD-003, HOD-007:** the ZIP contains exactly the approved complete
  member set; no previous ZIP is merged and no undeclared member is included.
- **HOD-A12 / HOD-002, HOD-009:** create uses the approved new identity while
  update exactly preserves the recorded hosted identity.
- **HOD-A13 / HOD-006:** canonical and legacy manifests agree on package name,
  version, interface metadata, and the complete ordered starter-prompt value.
- **HOD-A14 / HOD-006:** two isolated builds from identical inputs produce
  byte-identical ZIPs, JSON reports, and SHA-256 identities.
- **HOD-A15 / HOD-014:** blocked, audit, size, manifest, local-test, and
  verification failures leave a prior verified artifact directory byte-identical.
- **HOD-A16 / HOD-007:** archive verification never asserts hosted deletion or
  retention semantics and reports hosted installation as `NOT VERIFIED`.

### Application and capability acceptance

- **HOD-A17 / HOD-003:** effective skill discovery exactly matches the declared
  ordered-independent expected set.
- **HOD-A18 / HOD-003:** every explicit-only skill has
  `allow_implicit_invocation: false`.
- **HOD-A19 / HOD-010:** every non-instruction capability has one strict
  application-owned declaration with requirement, provider, artifacts,
  local-test reference, hosted-verification requirement, and unavailable policy.
- **HOD-A20 / HOD-010:** unresolved providers or fallbacks return
  `capability_decision_required`; missing required artifacts return
  `required_capability_artifact_missing` before output mutation.
- **HOD-A21 / HOD-010:** a required capability can only block when unavailable;
  an optional capability can use only its exact approved fallback.
- **HOD-A22 / HOD-011:** passing a local capability test records local execution
  without changing hosted execution from `NOT VERIFIED`.
- **HOD-A23 / HOD-010, HOD-011:** a failed local capability test returns
  `capability_local_verification_failed`, preserves prior artifacts, and emits no
  hosted execution evidence.
- **HOD-A24 / HOD-016:** generic production modules contain no application-
  specific identity, skill name, prompt, content, or behavior assertion.

### Channel and Vibe canary acceptance

- **HOD-A25 / HOD-012:** channel states remain independent; a local hosted build
  changes only generated OpenAI status to `PENDING_ACTION` and cannot mark
  Obvious-One or public submission current.
- **HOD-A26 / HOD-012:** every `CURRENT_BY_DECLARATION` or `STALE` state cites
  explicit evidence and never claims live read-back.
- **HOD-A27 / HOD-016:** Vibe create builds seven native skills plus one
  explicit-only compatibility skill without a previous archive.
- **HOD-A28 / HOD-016:** Vibe update preserves its approved hosted identity,
  advances the version, and produces the same general-software behavior without
  forcing a Web GUI.
- **HOD-A29 / HOD-003, HOD-016:** Vibe's target adapter contains only approved
  manifests, presentation assets, and compatibility routing; its seven portable
  skills remain canonical application files.
- **HOD-A30 / HOD-002:** update output instructions say to upload a new version
  to the existing plugin and never instruct creation of a duplicate.

### Required verification

The implementation plan must include:

- focused framework tests for HOD-A01 through HOD-A26 and HOD-A30;
- Vibe application tests for HOD-A27 through HOD-A29;
- `python -B -m unittest discover -s .\tests\framework -v`;
- affected repository-contract tests;
- `python -B -m unittest discover -s .\applications\vibe-coding-designer\tests -v`;
- two isolated hosted-deployment builds and exact comparison of every artifact;
- verification of the complete submitted archive and report set;
- `git diff --check` and proof that tests leave tracked files unchanged.

The first-version completion report uses these evidence states:

```text
deployment contract              STATICALLY VERIFIED
complete archive build           STATICALLY VERIFIED
complete archive verification    STATICALLY VERIFIED
local capability execution       STATICALLY VERIFIED or NOT APPLICABLE
hosted capability execution      NOT VERIFIED
deterministic artifact set        STATICALLY VERIFIED
hosted upload                    NOT VERIFIED
hosted installation              NOT VERIFIED
marketplace synchronization      NOT PERFORMED
public submission                NOT PERFORMED
```

Local success is `hosted_deployment_verified`. It is not `READY`, proof of
hosted behavioral equivalence, or evidence that any external channel changed.

## 14. Confirmed Decisions, Assumptions, and Deferred Scope

### Confirmed decisions

- One canonical converted plugin is the source of truth for all channels.
- OpenAI hosted deployment and marketplace distribution are parallel channels.
- Direct hosted archive creation does not require Obvious-One publication.
- The first version supports both create and update artifact generation.
- Update builds a complete replacement archive and preserves hosted identity.
- Previous hosted ZIPs are optional one-time identity-import inputs, not regular
  build dependencies or canonical sources.
- Identity import writes an unapproved proposal and never silently changes the
  application.
- The hosted deployment contract is separate from distribution schema v3.
- Target adapters are application-owned and may not fork portable behavior.
- Capability contracts and package/local/hosted evidence separation are
  mandatory.
- All authoritative framework output is non-interactive and machine-readable.
- The first version stops at a locally verified artifact set and performs no
  upload, installation, marketplace mutation, or public submission.
- Vibe Coding Designer is the first create-and-update canary.

### Assumptions

- Supported OpenAI workspaces may expose manual plugin ZIP upload and a
  new-version upload action when the caller has appropriate permissions.
- The submitted ZIP is intended as a complete deployment package. Because the
  hosted installation mechanism is not locally observable, post-upload tests
  remain necessary to detect retained or transformed hosted state.
- Python 3.11+ remains available to conversion callers.
- Schema-v3 redistribution evidence remains authoritative for canonical files.
- Channel evidence is declarative until a future authenticated read-back design
  is separately approved.

### Deferred scope

- Recording deployment confirmation through an authenticated OpenAI API.
- Automating the hosted upload or new-version UI.
- Automatically publishing or synchronizing Obvious-One.
- Preparing or submitting a universal public Plugins Directory package.
- Migrating Cool Bible Tutor's legacy distribution contract to schema v3.
- Proving hosted execution of Cool Bible Tutor's required Python and SQLite
  exact-retrieval capability.

Exact private helper placement may be refined during implementation planning.
Any change to public commands, operation semantics, identity approval,
canonical-source ownership, capability policy, evidence states, artifact
boundaries, or publication boundaries requires renewed decision-owner approval.
