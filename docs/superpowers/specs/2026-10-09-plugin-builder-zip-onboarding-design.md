# Plugin Builder ZIP-to-Workbench Onboarding Design

**Status:** Proposed for owner approval

**Date:** 2026-10-09

**Repository:** `convert-gpt-application`

**Scope:** Plugin Builder output to Obvious One Codex marketplace preparation

## 1. Purpose

Add a formal, fail-closed Workbench intake layer for a plugin ZIP produced by
Plugin Builder. The layer reuses the Builder's digest-bound package evidence,
collects only the publication decisions the Builder cannot establish, creates
a reviewable Workbench application registration, and hands that registration
to the existing marketplace preparation and verification pipeline.

The intended user is an owner who already has a final Plugin Builder ZIP and
wants to publish that plugin to the Obvious One GitHub Codex marketplace
without manually reconstructing Workbench contracts or repeating the Builder's
semantic implementation workflow.

Success means that one non-interactive command produces a deterministic,
unapproved onboarding proposal and marketplace-ready Workbench registration.
It must not mutate either repository, publish, push, or claim runtime evidence
that was not supplied.

## 2. Selected Design Direction

The first release is a strict Plugin Builder adapter, not a generic arbitrary
plugin importer. It implements this five-step flow:

1. verify the Plugin Builder ZIP and its package metadata;
2. validate one owner publication-decision record;
3. generate a complete Workbench registration proposal;
4. run only incremental publication and marketplace checks; and
5. leave marketplace review and publication behind a separate authorization.

Plugin Builder remains responsible for specification realization, W1/W2,
candidate construction, verification, update preservation, and final ZIP
packaging. Workbench must reuse that evidence rather than reenact the Builder
session.

## 3. Scope

### 3.1 Included

- Plugin Builder package schemas `plugin-builder-package-v2` and
  `plugin-builder-package-v3`.
- Plugin Builder's portable single-directory ZIP envelope.
- Codex-only registration in the Obvious One marketplace.
- Safe archive inspection and exact member verification.
- Portable and OpenAI compatibility manifest validation.
- Skill, reference, tool, MCP, dependency, asset, secret, and rights inventory.
- Deterministic proposal and application-registration generation.
- Schema-v3 distribution contract generation with ClawHub disabled.
- Obvious One preparation-catalog proposal generation.
- Reuse of existing `prepare-marketplace` and `verify-marketplace` commands.
- New-plugin onboarding and explicit detection of an existing plugin ID.

### 3.2 Excluded

- Generic ZIPs without recognized Plugin Builder package metadata.
- Automatic repair of plugin contents, manifests, skills, or tools.
- Automatic installation or installed-runtime testing.
- OpenClaw or ClawHub enablement.
- OpenAI universal-directory submission.
- Marketplace mutation, Git commit, push, pull request, merge, tag, or release.
- License or redistribution-rights inference.
- Silent replacement or update of an existing Workbench or marketplace plugin.

Supporting generic ZIP intake later requires a separate design. This design
must not grow compatibility heuristics for unrecognized producers.

## 4. Authorities and Evidence

The inputs have separate authority roles:

| Input | Authority |
| --- | --- |
| Plugin ZIP | Exact plugin bytes proposed for publication |
| `package-metadata.json` | Plugin Builder package identity, member closure, candidate and verification digests, preflight evidence, and tool/runtime evidence states |
| Optional evidence bundle | Additional supplied runtime observations; never upgrades an unobserved layer |
| Publication decisions | Owner authority for redistribution, license, author, target, and marketplace intent |
| Workbench proposal | Derived registration only; it has no authority to change plugin behavior |

The layer validates consistency, not producer authenticity. A locally supplied
JSON file is not a signature. A valid metadata closure is reported as
`STATICALLY VERIFIED`; installed behavior is `RUNTIME VERIFIED` only when a
matching accepted evidence bundle directly records that observation.

No filename, ZIP origin, caller identity, or prior publication implies owner
approval or redistribution authority.

## 5. Input Contract

The command requires:

- `--archive <plugin.zip>`;
- `--package-metadata <package-metadata.json>`;
- `--publication-decisions <publication-decisions.json>`;
- `--repository <workbench-repository-root>`; and
- `--output <empty-or-owned-proposal-directory>`.

It optionally accepts:

- `--evidence <plugin-builder-runtime-evidence.zip>`.

The publication-decision document uses schema
`plugin-publication-decisions-v1` and contains exactly:

- `plugin_id`;
- `version`;
- `author`;
- `license`, fixed to `MIT` in this version;
- `copyright_year`;
- `redistribution_approved`;
- `third_party_content_reviewed`;
- `third_party_content`, either `NONE` or
  `INCLUDED_WITH_PLUGIN_NOTICES`;
- `public_marketplace_approved`;
- `target_runtime`, fixed to `CODEX` in this version;
- `marketplace_id`, fixed to `obvious-one`;
- `codex_destination`, fixed to `plugins/<plugin_id>`;
- `confirmed_by`; and
- `decision_recorded_at`, retained as evidence but excluded from deterministic
  identity so equivalent decisions produce the same proposal identity.

The three approval booleans must be `true`. Missing or false authority is
`BLOCKED`, not a validation failure and not an invitation to infer consent.
When third-party content is included, the plugin must already contain a
nonempty root `THIRD_PARTY_NOTICES.md`; onboarding preserves it exactly.
Other license choices require a later contract revision rather than inferred
or downloaded license text. For MIT, Workbench generates the repository's
standard MIT text from the recorded author and copyright year.

## 6. Command Contract

Add one command:

```powershell
python -B -m obvious_one_plugin_framework.cli prepare-plugin-zip-marketplace `
  --archive <plugin.zip> `
  --package-metadata <package-metadata.json> `
  --publication-decisions <publication-decisions.json> `
  [--evidence <runtime-evidence.zip>] `
  --repository <workbench-repository-root> `
  --output <proposal-directory> `
  --json
```

The command is non-interactive and emits exactly one ASCII-safe
`result-schema-v1` document. Exit and status behavior matches the framework:

- `PASS` / exit 0: deterministic proposal written;
- `BLOCKED` / exit 2: owner decision or recognized evidence prerequisite is
  absent or unresolved;
- `FAIL` / exit 3: unsafe, inconsistent, tampered, or unsupported input; and
- local I/O failure / exit 4.

The command never edits `applications/`, `marketplaces/`, the marketplace
checkout, or Git. It writes only within its owned output transaction.

## 7. Processing Pipeline

### 7.1 Archive and metadata closure

Reuse the public plugin-authoring archive APIs. Enforce member, size,
compression, path, alias, case-folding, link, and reparse-point protections.
Require one portable single-directory plugin root whose directory name equals
the manifest plugin ID.

Validate all of the following:

- metadata schema is supported;
- archive SHA-256 equals `archive_sha256`;
- archive members equal the metadata member inventory by path, size, and hash;
- the extracted tree equals `candidate_members` after removing the one allowed
  envelope prefix;
- `member_manifest_sha256` is correct;
- `envelope_profile` is `PORTABLE_SINGLE_DIRECTORY`;
- root `plugin.json` and `.codex-plugin/plugin.json` exist;
- manifest name, version, author, description, and OpenAI interface agree;
- plugin ID and version equal the publication decisions;
- every skill and referenced local file passes existing structural validation;
- declared application tools and MCP projections pass existing validators; and
- no development-only imports, credentials, or unsafe paths are present.

Unknown metadata schemas, flat archives, ambiguous roots, metadata omissions,
and attempted content repair fail closed.

### 7.2 Evidence reuse

Do not repeat Plugin Builder planning, W1, building, W2, or semantic
requirement compilation. Preserve these metadata identities in the proposal:

- candidate SHA-256;
- verification SHA-256;
- preflight-evidence SHA-256;
- tool-contract and binding identities;
- capability, realization, adapter-registry, and generated-runtime identities
  when present; and
- all original evidence states and fallback activations.

If no optional evidence bundle is supplied, installed capability discovery,
Skill invocation, result delivery, and conversational behavior remain
`NOT VERIFIED`. Supplying a bundle may populate only observations whose ZIP,
plan/session, candidate, verification, and operation identities close against
the package metadata.

### 7.3 Publication-only audit

Run incremental checks not established by Plugin Builder packaging:

- owner redistribution and public-marketplace authority;
- license and third-party-content decision completeness;
- plugin ID and version collision against the Workbench application tree,
  preparation catalog, and supplied marketplace baseline when later staged;
- marketplace destination safety and uniqueness;
- public-content and secret audit;
- undeclared external services, credentials, runtime dependencies, executable
  requirements, remote assets, and corpora;
- Codex-only target declaration with OpenClaw and ClawHub disabled; and
- exact-byte policy for files whose hashes are externally bound.

An existing plugin ID produces `BLOCKED` with an explicit update-onboarding
decision requirement. Version comparison alone never authorizes replacement.
Update onboarding is excluded from automatic materialization in v1.

### 7.4 Deterministic registration proposal

On `PASS`, create this proposal tree without modifying tracked source:

```text
<output>/
  onboarding-result.json
  onboarding-proposal.json
  application/
    conversion.json
    plugin.json
    .codex-plugin/plugin.json
    DISTRIBUTION.md
    LICENSE
    PRIVACY.md
    SECURITY.md
    THIRD_PARTY_CONTENT.md
    THIRD_PARTY_NOTICES.md
    docs/
      application-invariants.md
      imported-package-inventory.json
      publication-decisions.json
      runtime-compatibility.md
      source-decisions.md
    imported-plugin/
      <exact extracted plugin contents>
    openclaw/
      distribution.json
    scripts/
      build_marketplace_release.py
      distribution_audit.py
    tests/
      test_imported_package.py
      test_marketplace_release.py
  catalog-entry.json
```

`imported-plugin/` is the immutable publication source. Generated wrappers
must not modify its contents. The generated build script copies its exact
allowlisted contents to `plugins/<plugin_id>`, validates both manifest forms,
and writes deterministic release evidence.

The proposal records the intended final Workbench path
`applications/<plugin_id>` and the exact catalog insertion but does not apply
either change. Byte-identical inputs produce identical proposal content;
filesystem paths are excluded from deterministic identities, and
`decision_recorded_at` is preserved as evidence but excluded from the proposal
identity digest. Result artifact paths are proposal-relative so the output does
not embed the caller's machine-specific root.

### 7.5 Existing marketplace pipeline

After the owner separately approves the proposal, an implementation agent may
copy the reviewed `application/` tree to `applications/<plugin_id>` and add the
exact catalog entry in a normal Workbench branch. That repository mutation is
outside the onboarding command.

The existing commands then remain authoritative:

1. `validate-contract`;
2. product tests and generated verification commands;
3. `prepare-marketplace` into a separate staging root;
4. `verify-marketplace` for filesystem evidence;
5. `verify-marketplace --index`;
6. `verify-marketplace --commit <commit>`; and
7. `verify-marketplace --fresh-checkout`.

Successful onboarding or staging grants no publication authority. Marketplace
commit, push, pull request, merge, tag, release, ClawHub publication, and
OpenAI-directory submission remain separate owner-authorized actions.

## 8. Internal Components

Add a focused `plugin_onboarding` package below
`src/obvious_one_plugin_framework/`:

- `contract.py`: strict metadata and publication-decision parsing;
- `inspection.py`: archive, manifest, member, dependency, and evidence closure;
- `proposal.py`: deterministic proposal model and identities;
- `materialize.py`: transactional proposal-tree generation; and
- `templates.py`: product-neutral generated document and test templates.

Expose only typed public entry points from the framework package. The CLI
adapts exceptions to existing result and exit-code conventions. Marketplace
code consumes the generated normal application registration and needs no
special ZIP-aware branch.

Product-specific language or assumptions must not enter generic templates.

## 9. Failure and Transaction Semantics

- Parse and inspect all inputs before creating the output parent where
  practical.
- Write to an owned sibling staging directory and atomically replace only a
  missing or previously marked onboarding output.
- Never overwrite an unmarked nonempty destination.
- A failure preserves any previous valid proposal byte-for-byte.
- Diagnostics are stable, deterministic, path-redacted codes.
- Report all independent static diagnostics in stable order.
- Treat ambiguous authority as `BLOCKED`; treat tampering and unsafe content as
  `FAIL`.
- Never execute imported plugin scripts during intake.
- Post-approval verification commands execute only through the existing
  bounded verification profile and Windows environment discipline.

## 10. Testing Strategy

Use test-driven implementation with isolated genuine system-temp roots. Cover:

1. valid v2 and v3 Plugin Builder packages;
2. Unicode plugin content and Windows checkout behavior;
3. identical input producing identical proposal trees and hashes;
4. archive, member-manifest, candidate-member, and manifest-pair tampering;
5. unsafe paths, aliases, case collisions, links, reparse points, compression
   limits, and file/directory collisions;
6. missing or false publication authority;
7. license, third-party-content, dependency, secret, remote-asset, executable,
   and external-service diagnostics;
8. unrecognized producer, schema, or envelope;
9. absent versus matching versus mismatched optional evidence bundle;
10. existing Workbench, catalog, or marketplace plugin collisions;
11. output collision and transactional rollback;
12. Codex-only catalog and schema-v3 contract generation;
13. generated product tests and exact-byte marketplace build;
14. end-to-end onboarding followed by unchanged `prepare-marketplace` and all
    four verification modes; and
15. confirmation that no command mutates either source or marketplace baseline.

Classify failures as implementation, test/fixture, environment, or transient
before changing production behavior. Environment-only failures receive the
smallest affected regression rerun before a full-suite rerun.

## 11. Acceptance Criteria

The feature is complete when:

- a real Plugin Builder v2 or v3 ZIP plus valid metadata and owner decisions
  produces one deterministic, reviewable proposal;
- the proposal preserves every plugin byte and Builder identity;
- Builder semantic tests are not redundantly reenacted;
- missing runtime evidence remains `NOT VERIFIED`;
- missing rights or publication authority blocks without mutation;
- an existing plugin ID cannot be replaced implicitly;
- generated registration passes framework, product, contract, distribution,
  secret, and deterministic-build tests;
- the unchanged marketplace pipeline prepares and verifies the plugin in a
  separate staging tree;
- repeated Windows and non-Windows CI runs preserve exact hash-bound bytes;
- all existing framework and product suites remain green; and
- no test or successful command publishes, pushes, or mutates the marketplace.

## 12. Compatibility and Readiness

This feature changes neither Plugin Builder's approved behavior nor the
generated plugin. It consumes existing v2/v3 package metadata and therefore
does not require a Plugin Builder release merely to support initial onboarding.
A future compact publication-evidence sidecar may reduce optional evidence
inputs, but it is not required by this design.

Onboarding success means `STATICALLY VERIFIED` registration readiness, not
installed runtime readiness. The plugin remains
`CONVERSION COMPLETE — RUNTIME VALIDATION PENDING` wherever required runtime
evidence is absent. Publication to Obvious One does not imply OpenAI universal
directory publication or cross-runtime portability.
