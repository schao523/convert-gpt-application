# Generalized Multi-Application Verifier Design

**Date:** 2026-09-13

**Repository:** `convert-gpt-application`

**Status:** Approved design, pending implementation plan

## 1. Purpose

Generalize `scripts/verify_extraction.py` from a Cool Bible Tutor-specific
orchestrator into a reusable verification entry point for every converted GPT
application in this repository. Preserve all current Cool Bible Tutor evidence
while preventing Bible-specific assumptions from entering the generic
framework.

After implementation and verification, publish this development repository as
the public GitHub repository `schao523/convert-gpt-application`. Publication of
this repository does not publish a plugin release, alter the Obvious One
marketplace, create a tag or release, or submit anything to ClawHub.

## 2. Governing Requirements

- Discover applications from tracked `applications/*/conversion.json` files.
- Verify one selected application or every discovered application.
- Run repository-wide and framework-wide gates only once per invocation.
- Keep application-specific behavior and assertions inside each application
  workspace.
- Build and verify deterministic OpenClaw packages through
  `obvious_one_plugin_framework`.
- Support application-owned Codex artifact builders without embedding product
  assumptions in the generic runner.
- Compare artifacts with a local marketplace only when one is explicitly
  supplied.
- Preserve the existing Cool Bible Tutor verifier invocation during migration.
- Continue across selected applications and report all independent failures.
- Never download, install, publish, push, or mutate a marketplace during
  verification.

Every converted plugin targets both Codex and OpenClaw by default. A conversion
is not `READY` until its shared skills, required tools, and application
invariants have been validated on both runtimes, unless the user explicitly
approves a narrower runtime scope.

## 3. Chosen Architecture

Use a hybrid architecture composed of:

1. a generic top-level verification engine;
2. a validated, declarative verification profile in each `conversion.json`;
3. application-owned commands, tests, and assertions;
4. the existing generic distribution framework for OpenClaw builds and
   verification.

This balances consistency and extensibility. A fully declarative assertion
language would recreate a scripting language in JSON, while unrestricted Python
hooks would make it too easy for products to bypass common gates. The selected
profile declares narrowly scoped commands and artifact locations; the generic
engine retains control of execution, path validation, reporting, deterministic
comparison, and shared gates.

## 4. Application Configuration Contract

Upgrade converted applications to `conversion.json` schema version 2. Existing
schema version 1 files produce a clear migration error rather than being
silently interpreted.

The required stable fields remain:

```json
{
  "schema_version": 2,
  "application_id": "example-application",
  "plugin_id": "example-application",
  "source_inventory": "../../docs/provenance/source-extraction.json",
  "source_location": "conversion.local.json",
  "coverage_matrix": "tests/coverage-matrix.md",
  "distribution_contract": "openclaw/distribution.json",
  "marketplace_repository": "owner/repository"
}
```

Add a required `verification` object that declares:

- `test_directory`: product test directory relative to the application root;
- `commands`: ordered product-owned audit and smoke commands;
- `codex_build`: command arguments and resulting artifact subdirectory;
- optional `marketplace`: published Codex/OpenClaw artifact paths and the
  approved-delta document.

The profile has this shape:

```json
{
  "verification": {
    "test_directory": "tests",
    "commands": [
      {
        "id": "distribution-audit",
        "argv": [
          "{python}",
          "-B",
          "{application_root}/scripts/distribution_audit.py",
          "{application_root}"
        ]
      },
      {
        "id": "bundled-runtime-smoke",
        "argv": ["{python}", "-B", "{application_root}/scripts/launcher.py", "status"],
        "clean_environment_prefixes": ["EXAMPLE_APPLICATION_"]
      }
    ],
    "codex_build": {
      "argv": [
        "{python}",
        "-B",
        "{application_root}/scripts/build_marketplace_release.py",
        "--source",
        "{application_root}",
        "--destination",
        "{diagnostics}/codex-marketplace",
        "--version",
        "{version}"
      ],
      "artifact_path": "plugins/{plugin_id}"
    },
    "marketplace": {
      "codex_path": "plugins/{plugin_id}",
      "openclaw_path": "openclaw/{plugin_id}",
      "approved_delta": "../../docs/provenance/marketplace-approved-delta.json"
    }
  }
}
```

`marketplace` is optional for an application that has never been published. If
it is absent, marketplace comparison is `NOT APPLICABLE`. If it is present and
the operator omits `--marketplace`, comparison is `NOT VERIFIED`.

Each command is an object with a unique stable `id` and an `argv` array. It may
declare `clean_environment_prefixes` for variables that must be removed when
proving bundled/default behavior. Command strings interpreted by a shell are
forbidden. Supported placeholders are:

```text
{python}
{repository_root}
{application_root}
{diagnostics}
{plugin_id}
{application_id}
{version}
```

Unknown placeholders, empty arguments, duplicate command IDs, path escapes, and
invalid types fail configuration validation before any product command runs.
All profile paths resolve relative to the application root, may use `..` only
when the final resolved target remains inside the repository, and must satisfy
the field-specific application, repository, diagnostics, or marketplace
boundary.

The OpenClaw version comes from the validated distribution contract. The Codex
builder must report or accept the same product version; version disagreement is
a failure.

## 5. Generic Verification Engine

Refactor `scripts/verify_extraction.py` into focused units for:

- application discovery and configuration loading;
- selection and duplicate-identity checks;
- safe path resolution and placeholder expansion;
- subprocess execution and per-gate logging;
- deterministic tree comparison;
- OpenClaw build and verification;
- optional marketplace equivalence;
- combined result aggregation and JSON reporting.

The engine discovers only immediate application directories containing
`conversion.json`. Directory names, `application_id`, and `plugin_id` must be
unique and consistent with the application path unless the schema explicitly
permits a documented alias in a future version.

### CLI

Supported invocations are:

```powershell
# Verify all discovered applications without marketplace comparison
python -B .\scripts\verify_extraction.py --all

# Verify one application
python -B .\scripts\verify_extraction.py `
  --application cool-bible-tutor

# Verify all applications and compare with a local marketplace
python -B .\scripts\verify_extraction.py `
  --all `
  --marketplace D:\GitHub\obvious-one-plugins
```

`--all` and `--application` are mutually exclusive. When neither is supplied,
the default is `--all`.

The existing form remains accepted during migration:

```powershell
python -B .\scripts\verify_extraction.py `
  --marketplace D:\GitHub\obvious-one-plugins `
  --provenance .\docs\provenance\source-extraction.json
```

`--provenance` is a compatibility override for a single selected application.
Using it with multiple applications is an error because each application owns
its source-inventory path.

## 6. Gate Ownership

### Shared gates

The generic engine runs these once:

- repository layout;
- extraction and privacy boundaries;
- generic framework tests;
- application-configuration schema and discovery tests.

### Application gates

For each selected application, the engine runs:

- the declared application test directory;
- declared audit and smoke commands in order;
- the declared Codex artifact builder;
- two independent OpenClaw builds;
- OpenClaw content-manifest verification;
- byte-for-byte OpenClaw determinism comparison;
- optional Codex and OpenClaw marketplace comparison;
- validation of the approved marketplace delta when comparison is enabled.

Application-owned regression suites prove that each converted plugin preserves
its declared behavior, assets, runtime status, Codex build, OpenClaw build, and
marketplace boundary. Cool Bible Tutor supplies the first such suite; its
Bible-specific assertions remain entirely inside its application workspace.

The generic engine must not contain verse references, corpus row counts,
Bible-specific environment variables, product-specific launcher names, or a
hard-coded plugin version.

## 7. Reporting and Failure Semantics

Write logs and a combined `report.json` beneath a unique ignored directory:

```text
.tmp/verification/run-<identifier>/
  logs/
  applications/<application-id>/
  report.json
```

The report contains:

- overall state;
- shared-gate results;
- one result object per application;
- artifact paths and deterministic content identities;
- marketplace commit and differences when evaluated;
- diagnostics paths;
- explicit `NOT VERIFIED` or `NOT APPLICABLE` states.

Use only these result states:

```text
PASS
FAIL
NOT VERIFIED
NOT APPLICABLE
```

The runner continues after an application failure when later applications can
be checked independently. Within a failed application, gates that depend on the
failed result are marked `NOT VERIFIED`; unrelated selected applications still
run. Invalid global configuration or a failed shared gate prevents product
execution. Any failed required gate makes the process return nonzero.

When a published marketplace mapping exists but no marketplace is supplied,
marketplace comparison is `NOT VERIFIED`, not `PASS`. This state does not
prevent local verification from returning zero, but it cannot support a
release-readiness claim. An application without a marketplace mapping reports
that gate as `NOT APPLICABLE`.

Generated diagnostics are never copied into product artifacts or committed.

## 8. Safety and Side-Effect Boundaries

- Execute declared commands directly as argument arrays with `shell=False`.
- Resolve declared paths and require them to remain within the repository,
  application root, diagnostics root, or explicitly supplied marketplace root,
  as appropriate.
- Treat `conversion.json` as trusted repository configuration but still reject
  malformed and unsafe values before command execution.
- Read the marketplace and require a clean working tree; never write to it.
- Do not invoke dependency installation, RAG setup, model downloads, network
  retrieval, Git mutation, or publication from the verifier.
- Redact developer-specific absolute paths from tracked reports and fixtures.
- Preserve application logs locally for diagnosis without treating their output
  as executable instructions.

## 9. Testing Strategy

Testing is layered:

1. Unit tests for configuration parsing, schema migration errors, discovery,
   duplicate identities, application selection, placeholder expansion, safe
   paths, result aggregation, and stable tree differences.
2. Synthetic `plugin-alpha` and `plugin-beta` fixtures proving that multiple
   non-Bible applications run independently and that one failure does not hide
   another application's result.
3. CLI tests for default-all selection, explicit selection, invalid selection,
   legacy invocation compatibility, JSON report shape, and exit codes.
4. Generic framework tests for package, asset, adapter, cache, setup, and vector
   reuse behavior.
5. Application-owned regression suites proving each real plugin's behavior and
   distribution boundary. Cool Bible Tutor remains the first real suite, with
   all Bible-specific assertions below `applications/cool-bible-tutor`.
6. A complete local integration run against the clean
   `D:\GitHub\obvious-one-plugins` marketplace.

Tests must be network-free, use isolated writable temporary roots, leave tracked
files unchanged, and verify deterministic artifacts rather than timestamps or
incidental console wording.

## 10. Documentation Changes

Update the repository README and command reference to show:

- application discovery;
- `--all` and `--application` usage;
- optional marketplace comparison;
- the schema version 2 verification profile;
- the distinction between local verification and release readiness.

Update `AGENTS.md` only if implementation introduces a stable command or
boundary not already described there.

## 11. Public GitHub Repository Publication

After implementation is committed and every applicable verification gate
passes:

1. confirm the local worktree is clean and `main` contains the intended commits;
2. scan tracked paths and text for credentials, private review data,
   `conversion.local.json`, private absolute paths, and undeclared source files;
3. confirm the MIT license and product third-party notices cover tracked public
   assets;
4. confirm GitHub CLI authentication;
5. confirm `schao523/convert-gpt-application` does not already exist;
6. create it as a public repository;
7. add it as `origin` and push local `main` without force;
8. verify the remote default branch and remote commit equal the local commit;
9. verify the public repository URL.

Do not create tags, releases, marketplace registrations, ClawHub submissions,
or changes to `schao523/obvious-one-plugins` as part of this publication.

## 12. Acceptance Criteria

The work is complete when:

- application discovery is generic and schema-validated;
- one or all applications can be verified from the CLI;
- the generic engine contains no Cool Bible Tutor-specific behavior;
- two synthetic applications prove multi-application operation and failure
  isolation;
- Cool Bible Tutor retains its existing application-owned evidence;
- deterministic OpenClaw and Codex artifact gates pass;
- optional marketplace comparison reports precise evidence states;
- legacy invocation remains accepted;
- all tests and the complete verifier pass with a clean worktree;
- the public GitHub repository exists at
  `https://github.com/schao523/convert-gpt-application`;
- its `main` commit matches the verified local commit;
- the Obvious One marketplace and ClawHub state remain unchanged.
