# Reference Application Decoupling Design

## Purpose

Make the conversion repository capable of generating provenance and verifying
any configured application without requiring Cool Bible Tutor to exist. Cool
Bible Tutor remains the first reference implementation, and
`schao523/obvious-one-plugins` remains its configured shared marketplace.

## Boundaries

- `src/obvious_one_plugin_framework` and top-level orchestration remain
  application-neutral.
- Application identities, source inventory rules, historical branches,
  commands, assets, versions, and acceptance assertions live under the owning
  `applications/<plugin-id>` configuration or tests.
- Repository policy may identify the Obvious One marketplace, but executable
  tools read the marketplace identity from application configuration so there
  is one authoritative value.
- The marketplace and ClawHub are read-only during this work.

## Provenance configuration

Schema-v2 `conversion.json` may declare a `provenance` object:

```json
{
  "source_repository": "source-repository-label",
  "incorporated_branches": ["branch-or-decision-label"],
  "inventory_rules": [
    {
      "root": ".",
      "classification": "source-only",
      "include": ["*.pdf", "*_guide.md"]
    },
    {
      "root": "application-assets",
      "classification": "public-product-asset",
      "include": ["**/*"]
    }
  ]
}
```

All roots and matches are confined to the supplied source repository. Rules
are ordered configuration data; output inventory records are sorted by
classification and relative path. Symlinks and non-files are excluded.

The generic provenance generator accepts an application ID, loads that
application's configuration, obtains the marketplace repository label from
`marketplace_repository`, and writes a schema-v2 record to the configured
`source_inventory` path unless an explicit in-repository output override is
given. It records application and plugin identity, source and marketplace Git
commits, configured branch labels, and SHA-256 inventory entries. It never
records private absolute paths.

## Provenance validation

The framework exposes a provenance parser/validator used by the verifier. A
schema-v2 record must contain matching application ID, plugin ID, marketplace
repository, 40-character Git commits, configured branch labels, and safe,
unique inventory paths with 64-character SHA-256 values and nonempty
classifications. Legacy schema-v1 parsing remains supported only for existing
records during migration; Cool Bible Tutor is migrated to schema v2 in this
change.

## Verification boundary

Shared gates run only repository-wide checks:

- generic repository layout;
- extraction/privacy boundary;
- framework tests;
- generic discovery and schema validation for every `conversion.json`.

Each selected application receives its own provenance gate before its product
tests and declared commands. A failure affects that application, not unrelated
applications. Application commands continue to be data-driven from
`conversion.json`.

Cool Bible Tutor-specific configuration, provenance, version, command, and
template-leakage assertions move beneath
`applications/cool-bible-tutor/tests`. No shared gate imports or executes them
unless Cool Bible Tutor is selected as an application.

## Repository and fixture cleanup

The repository layout requires the `applications` root rather than a named
application. Generic documentation uses domain-neutral terminology. Synthetic
framework fixtures retain Unicode-path coverage with a neutral filename.

## Acceptance criteria

1. A synthetic repository containing a valid application but no Cool Bible
   Tutor can load configuration, generate provenance, and complete all shared
   verification gates.
2. Selecting one application does not execute another application's tests or
   provenance assertions.
3. No generic production module or top-level orchestration script contains a
   Cool Bible Tutor identity, version, command, asset path, or Bible-domain
   term.
4. Cool Bible Tutor's full regression suite, provenance gate, Codex build,
   deterministic OpenClaw build, and read-only marketplace comparison pass.
5. Generic framework and repository tests pass, generated artifacts verify,
   `git diff --check` passes, and both development and marketplace working
   trees remain clean apart from the intended development changes.

## Non-goals

- Changing Cool Bible Tutor behavior or distribution assets.
- Changing the shared marketplace repository.
- Publishing, tagging, releasing, or submitting to ClawHub.
- Generalizing application-owned launchers, Bible retrieval, or review tools.
