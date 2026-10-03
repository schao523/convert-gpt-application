# Obvious One Target-Aware Marketplace Contract

Status: **PROPOSED — OWNER REVIEW REQUIRED**  
Date: 2026-10-03  
Scope: local marketplace preparation and verification only

## 1. Purpose

Allow the Obvious One marketplace to publish a plugin to only the runtimes in
its approved scope. The immediate release topology is:

- Plugin Builder 0.1.3: Codex marketplace only; OpenClaw and ClawHub are
  `NOT APPLICABLE` under `OPENAI_ONLY_PHASE_ONE`.
- Cool Plugin Design Assistant: Codex and OpenClaw marketplace artifacts remain
  applicable.

Publishing to the Obvious One GitHub marketplace does not submit either plugin
to the OpenAI universal directory. This contract authorizes no marketplace
mutation, Git push, tag, GitHub Release, ClawHub publication, or OpenAI
submission.

## 2. Selected approach

Introduce preparation-catalog schema v2 with explicit per-target records.
Retain schema v1 as a compatibility input by translating each v1 entry into
two applicable targets with the entry's existing shared mode.

Rejected alternatives:

1. Generate a placeholder OpenClaw Plugin Builder artifact. This would falsely
   advertise an excluded runtime and violate the approved phase-one scope.
2. Maintain separate hand-edited Codex and OpenClaw publication workflows.
   This would split the trust boundary and permit catalogs, validation
   registries, or Git evidence scopes to drift.
3. Remove OpenClaw support from the shared marketplace. Cool Plugin Design
   Assistant and the existing marketplace products still require dual-runtime
   preparation.

## 3. Catalog schema v2

The root remains:

```json
{
  "schema_version": 2,
  "marketplace_id": "obvious-one",
  "applications": []
}
```

Each application entry contains exactly:

```json
{
  "application_config": "applications/<plugin-id>/conversion.json",
  "distribution_contract": "applications/<plugin-id>/openclaw/distribution.json",
  "targets": {
    "codex": {
      "mode": "build",
      "destination": "plugins/<plugin-id>"
    },
    "openclaw": {
      "mode": "not_applicable"
    }
  }
}
```

Target keys are exactly `codex` and `openclaw`. Target modes are exactly
`build`, `verify_existing`, and `not_applicable`.

- `build` and `verify_existing` require one safe, non-overlapping relative
  `destination`.
- `not_applicable` forbids `destination` and any other target fields.
- At least one target must be applicable.
- Application identity, distribution identity, version, rights, and
  publication metadata continue to come from the existing application and
  distribution contracts; the target record does not override them.

Schema v1 remains accepted without changing its meaning. New or modified
catalogs use schema v2.

## 4. Internal model

`PreparationEntry` owns two `PreparationTarget` values rather than shared
destinations and one shared mode.

```text
PreparationTarget
  mode: build | verify_existing | not_applicable
  destination: relative path | null

PreparationEntry
  application
  contract
  codex: PreparationTarget
  openclaw: PreparationTarget
```

The framework exposes helpers for enumerating only applicable targets and
destinations. Build, verification, Git-evidence, exact-byte attributes, and
artifact-identity code must use those helpers rather than assuming two output
trees exist.

## 5. Preparation behavior

For each applicable target:

- Codex `build` invokes the application's declared Codex build and installs
  its verified artifact at the Codex destination.
- OpenClaw `build` invokes the schema-v3 package builder and verifier and
  installs the result at the OpenClaw destination.
- `verify_existing` reconstructs and verifies the exact committed destination
  without changing its bytes.

For `not_applicable`:

- no artifact is built;
- no destination is created, replaced, removed, or included in the delta;
- no runtime-catalog entry is generated;
- no Git-evidence or `.gitattributes` scope is added; and
- the validation registry records the target as `NOT APPLICABLE`.

If the baseline runtime catalog already contains the plugin for a target newly
declared `not_applicable`, preparation returns `BLOCKED` with a deterministic
diagnostic. It must not silently remove a previously published target.

All current transactional, link/reparse-point, path-containment,
deny-by-default, deterministic-build, and exact-byte guarantees remain.

## 6. Runtime catalogs and validation registry

Codex and OpenClaw catalogs no longer need identical plugin sets. Each catalog
must exactly match the applications applicable to that target in the trusted
preparation catalog.

Each generated registry plugin record contains explicit `targets` evidence:

```json
{
  "plugin_id": "plugin-builder",
  "targets": {
    "codex": {
      "state": "STATICALLY VERIFIED",
      "path": "plugins/plugin-builder",
      "artifact": {}
    },
    "openclaw": {
      "state": "NOT APPLICABLE"
    }
  }
}
```

The generated verifier evaluates only applicable targets, while still
rejecting a missing, duplicated, wrong-version, wrong-path, or unexpected
runtime-catalog entry. An application passes marketplace verification only
when every applicable target passes. `NOT APPLICABLE` is never treated as a
pass for an applicable target.

ClawHub remains governed by the distribution contract. A Codex-only
application must have ClawHub disabled; otherwise catalog loading fails.

## 7. Obvious One catalog topology

Convert `marketplaces/obvious-one.json` to schema v2.

- Cool Bible Tutor: Codex `build`, OpenClaw `build`.
- Vibe Coding Designer: Codex `build`, OpenClaw `build`.
- Cool Plugin Design Assistant: Codex `build`, OpenClaw `build`.
- Plugin Builder: Codex `build`, OpenClaw `not_applicable`.

This task registers Plugin Builder for deterministic local marketplace staging;
it does not apply that stage to `D:\GitHub\obvious-one-plugins`.

## 8. Failure behavior

Catalog/schema errors fail before staging. Representative deterministic
diagnostics include:

- `invalid_marketplace_catalog_target`
- `marketplace_target_destination_required`
- `marketplace_target_destination_forbidden`
- `marketplace_no_applicable_targets`
- `runtime_catalog_missing_entry`
- `runtime_catalog_unexpected_entry`
- `runtime_catalog_target_mismatch`
- `not_applicable_target_already_published`
- `clawhub_requires_openclaw_target`

No failure or block replaces a previous staged output.

## 9. Verification requirements

Implementation is test-first. Required evidence includes:

1. schema-v1 compatibility tests;
2. schema-v2 validation tests for every mode and invalid shape;
3. Codex-only preparation proving no OpenClaw tree or catalog entry is emitted;
4. dual-runtime preparation proving Cool Plugin Design Assistant remains in
   both catalogs;
5. pre-existing excluded-target catalog entry blocking without deletion;
6. target-aware generated-registry and verifier tests;
7. target-aware filesystem, index, commit, and fresh-checkout Git evidence;
8. deterministic repeated marketplace preparation;
9. complete framework and selected product suites;
10. non-destructive `prepare-marketplace` and `verify-marketplace` runs against
    the current Obvious One baseline.

## 10. Completion boundary

Completion means the conversion repository can deterministically prepare and
verify an Obvious One stage containing dual-runtime Cool Plugin Design
Assistant and Codex-only Plugin Builder entries without mutating the marketplace
repository.

Actual Obvious One publication still requires a separately reviewed exact
delta and explicit owner authorization to apply, commit, push, and merge it.
OpenAI universal-directory submission remains `NOT_PERFORMED`.
