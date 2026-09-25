# Hosted OpenAI Plugin Update Workflow Design

## 1. Executive Summary

The Conversion Workbench can convert a GPT source application into a portable
Obvious One plugin for Codex and OpenClaw, but it does not yet have a generic
workflow for updating the separately hosted OpenAI plugin produced from the
same GPT. A successful Vibe Coding Designer experiment established that an
exported hosted-plugin ZIP can serve as a baseline and that a deterministic
update ZIP can add the enhanced Obvious One skills while preserving the hosted
package identity.

This design adds a separate, application-owned `hosted-update-contract-v1` and
four non-interactive framework commands for planning, validating, building,
and verifying an upload-ready hosted update ZIP. The verifier simulates the
hosted overlay operation because omitted baseline files are preserved and file
deletion is unavailable. The contract also declares application capabilities,
their required or optional status, packaged providers, local verification, and
unavailability policy. The first version stops at a locally verified ZIP. It
does not authenticate to OpenAI, upload, install, or claim hosted runtime
validation; local execution evidence never upgrades hosted execution evidence.

The new workflow is independent of distribution-contract schema v3. It reuses
schema-v3 content classification and redistribution evidence for enhanced
application files without mixing hosted overlay semantics into Codex/OpenClaw
distribution rules.

## 2. Goals and Non-goals

### Goals

- **HOU-001:** Accept an exported hosted-plugin ZIP and an enhanced Obvious One
  application that are approved descendants of the same GPT source.
- **HOU-002:** Require explicit, application-owned lineage evidence instead of
  inferring common origin from names or folder proximity.
- **HOU-003:** Inventory and hash the hosted baseline safely without recording
  its private absolute path.
- **HOU-004:** Generate a deterministic proposal that assigns every relevant
  enhanced, overlay, and baseline path an explicit disposition.
- **HOU-005:** Keep owner decisions in a separate strict
  `hosted-update-contract-v1` rather than extending distribution schema v3.
- **HOU-006:** Build a deterministic ZIP that preserves the hosted package
  identity, advances its version, and uses the hosted archive's root layout.
- **HOU-007:** Simulate the effective release as the baseline overlaid by the
  update ZIP and verify the effective configuration and skill inventory.
- **HOU-008:** Represent undeletable obsolete files explicitly and prove that
  every deactivated file is no longer routed, indexed, declared, or referenced.
- **HOU-009:** Return one ASCII-safe `result-schema-v1` document for every
  success, blocked decision, validation failure, and I/O failure.
- **HOU-010:** Preserve the last verified ZIP when planning, validation,
  building, or verification fails.
- **HOU-011:** Keep the framework application-neutral while making Vibe Coding
  Designer the first product canary.
- **HOU-012:** Remain non-interactive so a future Workbench plugin or other
  client can guide decisions without embedding interaction in the framework.
- **HOU-013:** Declare every application capability that depends on packaged
  executables, structured data, hosted-native facilities, or external adapters,
  including whether it is required or optional and what happens when it is
  unavailable.
- **HOU-014:** Keep package-static, local-execution, and hosted-execution
  evidence separate so local verification cannot imply hosted capability.

### Non-goals

- Uploading, installing, publishing, or updating a hosted OpenAI plugin.
- Authenticating a caller or proving the legal authority of a decision owner.
- Deleting a file from an existing hosted release.
- Treating a locally verified ZIP as hosted runtime evidence or `READY`.
- Changing distribution-contract schema v3, marketplace preparation, Codex
  packaging, OpenClaw packaging, ClawHub behavior, or RAG contracts.
- Inferring a skill merge, router, rename, compatibility layer, rights,
  lineage, capability requirement, provider, or fallback decision.
- Committing a downloaded hosted ZIP unless its redistribution has been
  separately approved.
- Converting the Conversion Workbench itself into a plugin.

## 3. Users and Actors

- **Conversion caller:** invokes the public Python API or CLI with explicit
  application, contract, baseline, and output paths. It may be an agent,
  script, CI job, future client, or human.
- **Decision owner:** approves same-source lineage, hosted scope, path
  mappings, rights, compatibility behavior, deactivation, target version, and
  any intentional metadata or prompt changes.
- **Application workspace:** owns the hosted-update contract, lineage record,
  overlay content, product invariants, and application regression tests.
- **Generic framework:** inspects, validates, maps, canonicalizes, builds,
  simulates, verifies, and reports. It does not make product decisions.
- **Downloaded hosted baseline:** is an untrusted, read-only input until archive
  safety, manifest identity, version, and digest checks pass.
- **Enhanced Obvious One application:** supplies approved portable skills,
  references, metadata, and application behavior.
- **Future client or Workbench plugin:** may translate structured diagnostics
  into guided interaction, but must record approved answers in the contract
  before rerunning the framework.
- **OpenAI hosted service:** is outside the first-version system boundary.

The framework verifies the presence and shape of decision evidence. It cannot
infer human identity or legal authority from the conversion caller.

## 4. Use Cases and Flows

### Plan an update

The conversion caller supplies an application configuration, enhanced
distribution contract, and downloaded hosted ZIP. The planner validates the
baseline archive, records a redacted inventory, checks declared lineage, and
compares the baseline with enhanced and overlay content. It writes a
transactional proposal containing suggested mappings and every unresolved
decision. Suggestions do not constitute approval.

### Recover from missing decisions

When lineage, classification, rights, mapping, baseline disposition,
deactivation, capability, fallback, or manifest-change approval is missing,
the command returns `BLOCKED`. Diagnostics contain safe relative paths, stable
codes, and candidate decisions. The decision owner approves a choice, a
conversion caller records it in application-owned files, and validation
restarts from the beginning.

### Validate without building

The validator parses the approved contract, verifies the exact baseline
digest and identity, resolves every mapping and disposition, checks referenced
schema-v3 redistribution evidence, validates target manifests, capability
contracts, provider artifacts, local-test references, version ordering, and
preflights the complete update. It writes no ZIP.

### Build an update ZIP

After validation, the builder canonicalizes approved text, preserves binary
bytes, writes deterministic ZIP metadata, and atomically replaces the output
only after the archive passes its structural audit. It never mutates the
baseline or application source.

### Verify the effective release

The verifier extracts neither archive over untrusted paths. It models the
effective hosted release by applying update members over baseline members in a
confined temporary root. It checks manifests, presentation metadata, prompts,
skills, references, indexes, active and dormant paths, application invariants,
declared capability artifacts, local verification commands, and deterministic
rebuild evidence. Success reports an upload-ready local artifact while upload,
installation, and every hosted capability remain `NOT VERIFIED`.

### Replan after a baseline change

If the hosted baseline version, digest, inventory, or manifest changes, the
existing update contract no longer applies. The caller must download the new
baseline and regenerate the proposal. Merely editing the expected digest or
version is prohibited.

## 5. Software Form and System Boundaries

The enhancement remains part of the Python 3.11+
`obvious_one_plugin_framework` library and its non-interactive CLI. It adds no
Web, desktop, TUI, daemon, database, or required network service.

Generic production modules live under:

```text
src/obvious_one_plugin_framework/
  hosted_update_contract.py
  hosted_update_inventory.py
  hosted_update_planner.py
  hosted_update_builder.py
  hosted_update_verifier.py
```

Application-owned declarations live under:

```text
applications/<plugin-id>/hosted-openai/
  update.json
  lineage-decision.json
  overlay/
    plugin.json
    .codex-plugin/plugin.json
    skills/...
```

The downloaded baseline path is supplied explicitly on the CLI or recorded
only in ignored `conversion.local.json`. Generated proposals, ZIPs, effective
release stages, and reports remain below ignored `dist` or `.tmp` roots.

The framework does not write to the installed plugin cache, OpenAI service,
marketplace repository, original GPT source archive, or enhanced application
source.

## 6. Interface Specification

### CLI commands

Plan a hosted update:

```powershell
python -B -m obvious_one_plugin_framework.cli plan-hosted-update `
  --application .\applications\<plugin-id>\conversion.json `
  --baseline-zip <downloaded-hosted-plugin.zip> `
  --output .\.tmp\<plugin-id>-hosted-update-proposal.json `
  --json
```

Validate an approved contract:

```powershell
python -B -m obvious_one_plugin_framework.cli validate-hosted-update `
  --contract .\applications\<plugin-id>\hosted-openai\update.json `
  --baseline-zip <downloaded-hosted-plugin.zip> `
  --json
```

Build the ZIP:

```powershell
python -B -m obvious_one_plugin_framework.cli build-hosted-update `
  --contract .\applications\<plugin-id>\hosted-openai\update.json `
  --baseline-zip <downloaded-hosted-plugin.zip> `
  --output .\dist\hosted-openai\<plugin-id>-<version>.zip `
  --json
```

Verify the ZIP and simulated effective release:

```powershell
python -B -m obvious_one_plugin_framework.cli verify-hosted-update `
  --contract .\applications\<plugin-id>\hosted-openai\update.json `
  --baseline-zip <downloaded-hosted-plugin.zip> `
  --update-zip .\dist\hosted-openai\<plugin-id>-<version>.zip `
  --json
```

Every command emits exactly one `result-schema-v1` JSON document. Status and
exit-code meanings remain compatible with the existing CLI:

- exit `0`: `PASS`;
- exit `2`: `BLOCKED` or invocation/contract error, distinguished by JSON;
- exit `3`: deterministic build or verification `FAIL`;
- exit `4`: local I/O or environment failure.

Planning may transactionally create or replace only its proposal destination.
Validation and verification perform no persistent mutation. Building may
transactionally replace only the requested ZIP.

### Public Python API

Public immutable models and functions mirror the CLI:

- `load_hosted_update_contract`;
- `inventory_hosted_baseline`;
- `plan_hosted_update`;
- `validate_hosted_update`;
- `build_hosted_update`;
- `verify_hosted_update`.

Public functions return typed results or raise framework errors with stable
codes. Product code and private underscore-prefixed helpers are not public
dependencies.

## 7. Component Architecture

### Hosted update contract

Strictly parses schema v1, rejects unknown keys, confines relative paths, and
loads referenced application, distribution, lineage, manifest, overlay, and
test declarations. It does not share a version number or migration path with
the OpenClaw distribution contract.

### Baseline inventory

Streams ZIP members, rejects traversal, absolute paths, duplicate names,
case-fold collisions, encrypted entries, unsupported compression, and entries
encoded as links. It hashes each member and the complete archive, then parses
known manifests and discovers skills and referenced resources. Reports contain
relative member names and hashes, never the caller's baseline path.

### Planner

Compares baseline members, enhanced application content, and application-owned
overlay content. Every relevant file receives one proposed disposition. The
planner may suggest but never approve mappings, compatibility behavior,
deactivation, or rights.

### Builder

Resolves approved mappings, reuses existing canonical content policies,
creates sorted ZIP members with fixed timestamp and permissions, and writes
through a sibling temporary file. It copies application-owned overlay content;
it does not generate application prompt or routing text.

### Effective-release verifier

Computes the logical union of baseline and update members, with update bytes
winning on identical paths. It validates the effective result rather than
assuming omitted files disappeared. It verifies manifest precedence, active
skill discovery, explicit-only policy, references, indexes, assets, dormant
paths, audits, and product commands.

Generic modules contain no Vibe-specific identifiers or expected skills. Vibe
requirements remain in its application contract and tests.

## 8. Data and Persistence

### Hosted-update contract schema v1

The tracked contract has this top-level shape:

```json
{
  "schema_version": 1,
  "application_id": "vibe-coding-designer",
  "lineage": {
    "source_inventory": "../docs/source-inventory.json",
    "enhanced_distribution_contract": "../openclaw/distribution.json",
    "hosted_identity_decision": "lineage-decision.json"
  },
  "baseline": {
    "package_name": "gpt-e9ed8a960ed122e05ddb75f341a810a5",
    "version": "0.8.1+bundle.1c331dbb28ba4816e6d8dfde085642c5",
    "archive_sha256": "83d8f4ec407a658ad18abb7e536430d4976362a87617e71261427014e7f61fdd"
  },
  "target": {
    "version": "0.9.0",
    "portable_manifest": "overlay/plugin.json",
    "legacy_manifest": "overlay/.codex-plugin/plugin.json",
    "max_archive_bytes": 10000000
  },
  "content": {
    "enhanced_mappings": [],
    "overlay_mappings": [],
    "baseline_dispositions": []
  },
  "effective_release": {
    "expected_skills": [],
    "explicit_only_skills": [],
    "dormant_paths": [],
    "required_application_tests": [],
    "capabilities": []
  }
}
```

All paths are safe POSIX-relative values resolved from the contract or
application root. The application configuration identifies the application;
the hosted contract identifies the exact baseline and target.

### Enhanced and overlay mappings

Each mapping has a stable ID, source kind, source path, target path, copy mode,
classification, and redistribution reference. Source kinds are
`enhanced_application` and `hosted_overlay`. Copy modes are `copy_file` and
`copy_tree`. Renames require distinct explicit source and target paths.

Enhanced files must be selected and approved by the referenced schema-v3
distribution contract. Hosted-only overlay files carry hosted-specific content
rules and provenance. The same enhanced file's rights decision is referenced,
not duplicated.

### Baseline dispositions

Every baseline member resolves to exactly one action:

- `preserve`: omit it from the update and retain it unchanged;
- `replace`: require a replacement at the same effective path;
- `deactivate`: retain the bytes but require specified replacement controls
  that remove every active route, declaration, index, and reference.

A deactivation record includes the baseline path, controlling replacement
paths, approved reason, and evidence rule. If safe deactivation cannot be
proven, the update remains blocked.

### Effective-release declaration

The contract records the exact expected active skill names, explicit-only
skills, dormant paths, required product-test identifiers, and capability
contracts. Physical archive membership, local executability, and hosted
behavior are therefore separate declared concepts.

### Capability contracts

A capability contract is required when application behavior depends on more
than portable skill instructions: packaged executable code, exact structured
data, a hosted-native facility, or an external adapter. Each capability has:

- a unique stable `id`;
- `requirement`, either `required` or `optional`;
- `provider_kind`, one of `packaged_executable`, `hosted_native`, or
  `external_adapter`;
- `artifact_paths`, listing every file that must exist in the effective release
  for the declared provider;
- `local_verification_test`, referencing one declared product-test identifier,
  or `null` only when no local execution is possible;
- `hosted_verification`, fixed to `required_after_install` in schema v1; and
- `on_unavailable`, either `block` or `use_declared_fallback`.

For example, an application whose exact structured retrieval depends on a
packaged launcher and database can declare:

```json
{
  "id": "exact-structured-retrieval",
  "requirement": "required",
  "provider_kind": "packaged_executable",
  "artifact_paths": [
    "scripts/retrieve.py",
    "assets/exact-data.sqlite3"
  ],
  "local_verification_test": "exact-retrieval-smoke",
  "hosted_verification": "required_after_install",
  "on_unavailable": "block"
}
```

An optional capability using `use_declared_fallback` also contains a
`fallback` object with an owner-approved behavior statement and any required
effective-release paths. A required capability must use `block`; a fallback
cannot silently substitute for a required invariant. An external adapter must
name only an application-facing contract here; provider credentials, URLs, and
machine-specific configuration remain outside the portable contract.

Every declared artifact path must be supplied by an approved mapping or
preserved baseline member, pass redistribution and secret checks, and remain
reachable in the effective release. `packaged_executable` requires at least
one artifact path; provider kinds with no package-owned files use an empty
array. A named local verification test must be included in
`required_application_tests`. Missing provider decisions return
`capability_decision_required`; missing required artifacts return
`required_capability_artifact_missing`; and a failed local capability test
returns `capability_local_verification_failed`.

Local verification proves only that the staged effective release can provide
the capability in the conversion environment. The v1 verifier always reports
the corresponding hosted capability as `NOT VERIFIED`. A later authenticated
runtime phase must report an observed unavailable required capability as
`required_hosted_capability_unavailable`; it may apply a fallback only for an
optional capability whose exact fallback was approved in this contract.

No database or durable framework state is introduced. Proposals, reports, and
artifacts are immutable files in caller-selected ignored output roots.

## 9. Services and Integrations

No network service is required. Python 3.11 or newer and ZIP support from the
standard library are sufficient. Existing product validation commands may
require their already declared local dependencies. These conversion-host
requirements do not assert that the hosted runtime provides the same
executables, libraries, filesystem access, or services.

The first version has no OpenAI API, browser automation, plugin-creator API,
credential, upload, install, or read-back integration. A future authenticated
adapter would require a separate design and explicit authorization boundary.

The Agent Plugins manifest schema is an external format. The framework
validates the supported schema identifier and application-owned manifest
content but does not download schemas at build time.

## 10. Workflow Specification

The canonical state progression is:

```text
BASELINE_INSPECTED
    -> LINEAGE_CONFIRMED
    -> UPDATE_PLANNED
    -> OWNER_DECISIONS_RECORDED
    -> CONTRACT_VALIDATED
    -> UPDATE_BUILT
    -> EFFECTIVE_RELEASE_VERIFIED
    -> READY_FOR_UPLOAD_REVIEW
```

Any stage terminates as `BLOCKED` when an approved owner decision is missing
or as `FAIL` when input or generated bytes violate a deterministic rule.
Downstream gates are `NOT VERIFIED` when their prerequisite did not pass.

Detailed workflow:

1. Inspect and hash the baseline without extracting unsafe entries.
2. Validate the declared baseline identity, version, and digest.
3. Validate the enhanced application's source inventory and schema-v3
   distribution contract.
4. Validate the application-owned same-source lineage decision.
5. Inventory enhanced and overlay candidates.
6. Produce or validate exact mappings, baseline dispositions, capability
   contracts, and optional fallback decisions.
7. Validate manifests, version ordering, prompts, presentation metadata,
   rights, classification, expected skills, capability artifact closure,
   local-test references, and size limits.
8. Create the deterministic update archive in a sibling temporary file.
9. Audit and atomically replace the requested output.
10. Overlay update members over baseline members in an isolated stage.
11. Verify the complete effective release, run declared local product commands,
    and report every hosted capability as `NOT VERIFIED`.
12. Rebuild independently and compare bytes when deterministic evidence is
    required.
13. Emit the artifact hash, exact delta, preserved and dormant inventory,
    gates, and `upload_status: NOT_PERFORMED`.

There are no automatic retries for deterministic failures. A changed baseline
requires a new plan and renewed decision review.

## 11. Quality Attributes

- **Determinism:** identical logical inputs yield byte-identical ZIPs,
  inventories, and reports regardless of enumeration order or host OS.
- **Reliability:** output replacement is atomic; failed work cannot invalidate
  the last verified ZIP.
- **Security:** every path is confined, archives are treated as untrusted, and
  links, collisions, encrypted entries, secrets, and private-path leakage are
  rejected.
- **Maintainability:** contract, inventory, planning, building, and verifying
  remain separate modules with public typed boundaries.
- **Observability:** results include stable status, code, diagnostics,
  artifacts, mutations, and separate package-static, local-execution, and
  hosted-execution evidence for each capability.
- **Performance:** ZIP inspection and hashing stream members and are linear in
  total input bytes. Configurable byte and member-count limits prevent archive
  expansion abuse.
- **Cross-platform compatibility:** member names are POSIX relative; text is
  canonical UTF-8 LF; binary bytes are exact; case-fold collisions are
  rejected.
- **Compatibility:** existing framework commands and schema-v3 behavior remain
  unchanged. The hosted contract starts at schema v1 with no legacy formats.
- **Accessibility and localization:** not applicable because the framework has
  no user interface. Stable codes remain locale-neutral for future clients.

## 12. Security and Privacy

- Baseline, contract, application, overlay, temporary, and output paths are
  explicitly supplied and confined before access.
- ZIP traversal, absolute paths, duplicate members, case-fold collisions,
  encrypted entries, links, unsupported compression, excessive members, and
  excessive expansion are rejected.
- Reports reject Windows and POSIX absolute paths and never serialize the
  caller's downloaded ZIP location.
- Text canonicalization and existing secret audits apply to every packaged
  text file; binary classification cannot be used to evade forbidden-name or
  size checks.
- Rights and lineage are explicit approved evidence, not inferred from
  ownership, names, file types, or locations.
- Application-owned hooks or commands run only when explicitly declared and
  remain confined to isolated writable roots.
- No credential is required or accepted by the first-version contract.
- The framework never uploads, installs, publishes, pushes, tags, or changes
  sharing or visibility.

## 13. Validation and Acceptance

Implementation is test-first. Each behavior begins with a focused failing test
whose failure is caused by the missing behavior rather than fixture or sandbox
errors.

### Contract and recovery acceptance

- **HOU-A01 / HOU-001, HOU-003:** a valid exported baseline is inventoried with
  exact archive and member hashes and no serialized private path.
- **HOU-A02 / HOU-002:** absent or inconsistent lineage returns
  `hosted_lineage_unresolved` before build output mutation.
- **HOU-A03 / HOU-004, HOU-005:** the proposal lists every candidate path and
  unresolved decision without modifying the approved contract.
- **HOU-A04 / HOU-004:** zero or multiple mapping matches return
  `unclassified_update_file` or `ambiguous_update_mapping`.
- **HOU-A05 / HOU-008:** every baseline member requires one disposition;
  incomplete coverage returns `baseline_disposition_required`.
- **HOU-A06 / HOU-008:** unsafe deactivation returns
  `baseline_file_cannot_be_deactivated`.
- **HOU-A07 / HOU-009, HOU-012:** every command returns one valid
  result-schema-v1 document for pass, blocked, invalid, unsafe, build,
  verification, and I/O outcomes, requires no interactive prompt or human
  identity, and behaves identically for identical explicit inputs regardless
  of caller type.

### Archive and manifest acceptance

- **HOU-A08 / HOU-003:** traversal, absolute paths, duplicate names,
  case-fold collisions, links, encryption, and archive-limit violations fail
  baseline inspection.
- **HOU-A09 / HOU-006:** target package identity exactly equals the baseline
  identity and target version is greater than the baseline version.
- **HOU-A10 / HOU-006:** canonical and legacy manifests agree on name,
  version, complete interface metadata, and the entire ordered starter-prompt
  value.
- **HOU-A11 / HOU-006:** two isolated builds from identical inputs have
  byte-identical ZIPs and SHA-256 identities.
- **HOU-A12 / HOU-010:** blocked, audit, size, manifest, and verification
  failures leave a prior verified output byte-identical.

### Effective-release acceptance

- **HOU-A13 / HOU-007:** verification overlays update members over baseline
  members and detects failures that are invisible when checking the update ZIP
  alone.
- **HOU-A14 / HOU-007:** effective skill discovery exactly matches the
  contract's ordered-independent expected set.
- **HOU-A15 / HOU-007:** every explicit-only skill has
  `allow_implicit_invocation: false`.
- **HOU-A16 / HOU-008:** a dormant file has no active manifest, skill, reference,
  route, or knowledge-index edge.
- **HOU-A17 / HOU-008:** an active edge to a dormant path fails verification.
- **HOU-A18 / HOU-011:** no generic production module contains a Vibe-specific
  identity, skill name, or behavior assertion.

### Vibe canary acceptance

- **HOU-A19 / HOU-011:** the Vibe application contract builds seven native
  enhanced skills plus one explicit-only compatibility skill.
- **HOU-A20 / HOU-011:** the simulated effective release preserves general
  software scope and does not force a Web GUI.
- **HOU-A21 / HOU-011:** the old Web-only references are declared dormant and
  have no active edge.
- **HOU-A22 / HOU-006:** the hosted package identity and approved icon are
  preserved while the hosted version advances.

### Capability-contract acceptance

- **HOU-A23 / HOU-013:** each non-instruction capability has one strict
  application-owned declaration with a stable identifier, requirement,
  provider kind, artifact closure, local-test reference, hosted-verification
  requirement, and unavailability policy.
- **HOU-A24 / HOU-013:** an unresolved provider or fallback returns
  `capability_decision_required`, while a missing required provider artifact
  returns `required_capability_artifact_missing` before output mutation.
- **HOU-A25 / HOU-013:** a required capability can only block when unavailable;
  an optional capability can use only its exact approved fallback.
- **HOU-A26 / HOU-014:** passing a local capability test records local execution
  evidence without changing hosted execution from `NOT VERIFIED`.
- **HOU-A27 / HOU-013, HOU-014:** failing a declared local capability test
  returns `capability_local_verification_failed`, preserves the previous ZIP,
  and does not emit hosted execution evidence.

### Required verification

The implementation plan must include:

- focused framework tests for HOU-A01 through HOU-A18 and HOU-A23 through
  HOU-A27;
- Vibe application tests for HOU-A19 through HOU-A22;
- `python -B -m unittest discover -s .\tests\framework -v`;
- affected repository-contract tests;
- `python -B -m unittest discover -s .\applications\vibe-coding-designer\tests -v`;
- two isolated hosted-update builds and an exact byte comparison;
- verification of a simulated effective release;
- `git diff --check` and proof that tests leave tracked files unchanged.

The first-version completion report uses these evidence states:

```text
contract                         STATICALLY VERIFIED
update ZIP build                 STATICALLY VERIFIED
effective-release simulation     STATICALLY VERIFIED
local capability execution       STATICALLY VERIFIED or NOT APPLICABLE
hosted capability execution      NOT VERIFIED
deterministic bytes              STATICALLY VERIFIED
hosted upload                    NOT VERIFIED
hosted installation              NOT VERIFIED
```

Local success is `hosted_update_verified`; it is not `READY` and not hosted
behavioral equivalence.

## 14. Assumptions and Open Questions

### Confirmed decisions

- The hosted update uses a separate contract rather than extending
  distribution schema v3.
- The contract and compatibility overlay are application-owned.
- The generic framework remains non-interactive and machine-readable.
- The first version stops at a verified ZIP and performs no upload.
- Every baseline file has an explicit disposition.
- Effective-release overlay simulation is mandatory.
- Capabilities beyond portable instructions have explicit required or optional
  contracts, provider artifacts, and unavailability policies.
- Local capability execution and hosted capability execution are separate
  evidence gates.
- Decision-related gaps are `BLOCKED`; unsafe or inconsistent bytes are
  `FAIL`.
- Vibe Coding Designer is the first product canary.

### Assumptions

- Current hosted updates overlay files and do not delete omitted files.
- The successful Vibe experiment is evidence that the hosted platform accepts
  the portable root manifest, synchronized legacy manifest, multiple skills,
  and an explicit-only compatibility skill.
- Python 3.11+ remains available to conversion callers.
- Schema-v3 redistribution evidence remains the authority for enhanced files.
- Local reference and index analysis can prove package-level dormancy but
  cannot prove undocumented hosted indexing behavior.

### Open questions

None block implementation planning. Exact Python type names and private helper
placement may be refined without changing the public commands, contract
semantics, result codes, application ownership, overlay model, acceptance
criteria, or publication boundary. Any change to those approved contracts
requires renewed decision-owner approval.
