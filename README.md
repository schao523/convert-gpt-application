# Obvious One GPT Application Conversion Framework

This repository converts existing GPT application instructions and reference files into tested, redistributable plugins of skills.

It is the development layer in a three-repository boundary:

- Original GPT application folders retain instructions and reference files.
- This repository owns reusable conversion tooling and active application workspaces.
- `schao523/obvious-one-plugins` contains audited public marketplace artifacts.

The `rag_subsystem` project remains an independently installable dependency. Runtime and embedding models may be cached compatibly, while each plugin owns its corpora, PDFs, structured databases, vector indexes, application identity, and namespace.

See `docs/GPT_TO_PLUGIN_USER_GUIDE.md`, `docs/PLUGIN_SKILLS_TECHNICAL_REFERENCE.md`, and `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md` after documentation extraction.

## Verify converted applications

The verifier discovers immediate application workspaces from
`applications/*/conversion.json`. Every converted plugin targets both Codex and
OpenClaw unless a narrower scope has been explicitly approved.

Run all discovered applications from PowerShell:

```powershell
python -B .\scripts\verify_extraction.py --all
```

Run one application:

```powershell
python -B .\scripts\verify_extraction.py --application cool-bible-tutor
```

Compare all generated artifacts with a clean local marketplace checkout:

```powershell
python -B .\scripts\verify_extraction.py `
  --all `
  --marketplace D:\GitHub\obvious-one-plugins
```

Each invocation writes ignored logs and a combined `report.json` below a unique
`.tmp/verification/` directory. `PASS` and `FAIL` are required-gate outcomes;
`NOT VERIFIED` means an optional evidence source was not evaluated, and
`NOT APPLICABLE` means the application does not declare that evidence source.
Local success with a configured but omitted marketplace comparison is not
release-readiness evidence.

Each application configuration uses schema version 2 and owns its product
commands:

```json
{
  "schema_version": 2,
  "application_id": "example-plugin",
  "plugin_id": "example-plugin",
  "verification": {
    "test_directory": "tests",
    "commands": [
      {"id": "smoke", "argv": ["{python}", "-B", "{application_root}/scripts/smoke.py"]}
    ],
    "codex_build": {
      "argv": ["{python}", "-B", "{application_root}/scripts/build.py"],
      "artifact_path": "plugins/{plugin_id}"
    }
  }
}
```

The full profile contract and legacy compatibility command are documented in
`docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`.

## Distribution contracts and local marketplace staging

New package builds use distribution-contract schema v3:

```json
{
  "schema_version": 3,
  "content_rules": [],
  "publication": {
    "github_marketplace": {"enabled": true},
    "clawhub": {"enabled": false, "family": null, "native_manifest": null}
  }
}
```

Both schema v1 and schema v2 remain readable legacy formats. They can be checked in
`verify_existing` marketplace mode but cannot be rebuilt; an attempted build
returns `legacy_contract_read_only`. Use `validate-contract` to inspect a
contract and preflight its selected files without writing build output. Missing
classifications and unresolved redistribution rights return actionable
`BLOCKED` results. Use `migrate-contract` to create a reviewable schema-v3
proposal.

Native ClawHub publication is an explicit, separate contract. Enabling it
requires an application-root `openclaw.plugin.json` plus a matching
`package.json` with declared `openclaw.extensions`. Those native files must be
selected and rights-classified, and the deterministic builder carries them
into the verified output; a bundle-only package does not satisfy that contract.

The generic `prepare-marketplace` command treats the marketplace as a read-only
baseline and writes a separate staged tree. It does not apply or publish the
delta. Use `verify-marketplace` to inspect filesystem, Git index, commit, and
fresh-checkout evidence before any separately approved publication action.
