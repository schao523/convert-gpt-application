# Plugin and Framework Command Reference

This guide lists the command-line entry points used while converting a GPT application into a plugin of skills, testing an individual plugin, producing public artifacts, and publishing those artifacts through the Obvious One GitHub marketplace.

Commands are shown for PowerShell. Run them from the repository named in each section. Replace values inside angle brackets with the paths, plugin IDs, and versions for the application being converted.

## 1. Interface boundary

There are three command surfaces:

1. **Product launcher commands** operate one converted plugin. They are intended for plugin users and product-level tests.
2. **Framework commands** build, verify, and prepare reusable distribution artifacts. They are intended for plugin developers and release automation.
3. **Marketplace commands** register, install, refresh, and publish the resulting plugin.

A product may provide a local browser interface for review or administration, but PowerShell remains the stable entry point that starts it.

## 2. Product launcher commands

The launcher lives at `plugins/<plugin-id>/scripts/<launcher>.py` in the public marketplace repository. Cool Bible Tutor currently provides the reference implementation.

From `D:\GitHub\obvious-one-plugins`:

```powershell
python .\plugins\cool-bible-tutor\scripts\cool_bible_tutor.py doctor
python .\plugins\cool-bible-tutor\scripts\cool_bible_tutor.py status
python .\plugins\cool-bible-tutor\scripts\cool_bible_tutor.py verify
```

Exact retrieval:

```powershell
python .\plugins\cool-bible-tutor\scripts\cool_bible_tutor.py passage "約 3:16"
```

Explicit semantic-RAG setup and discovery:

```powershell
python .\plugins\cool-bible-tutor\scripts\cool_bible_tutor.py setup-rag --accept-downloads
python .\plugins\cool-bible-tutor\scripts\cool_bible_tutor.py rag-discover "神的愛與救恩" --top-k 5
```

Local browser review interface:

```powershell
python .\plugins\cool-bible-tutor\scripts\cool_bible_tutor.py review
```

The product launcher pattern is reusable, but every plugin implements only the commands its domain requires. A future plugin must not inherit Bible-specific commands or assets merely because Cool Bible Tutor is its reference implementation.

## 3. Generic distribution-framework commands

Run these from `D:\GitHub\convert-gpt-application` after the controlled repository extraction is complete.

Build deterministic remote asset archives and their immutable manifest:

```powershell
python -B -m obvious_one_plugin_framework.cli build-assets `
  --contract .\applications\<plugin-id>\openclaw\distribution.json `
  --output .\dist\openclaw-assets\<plugin-id> `
  --manifest .\applications\<plugin-id>\assets\openclaw\remote-assets.json
```

Build a lightweight OpenClaw-compatible package:

```powershell
python -B -m obvious_one_plugin_framework.cli build-package `
  --contract .\applications\<plugin-id>\openclaw\distribution.json `
  --output .\dist\openclaw\<plugin-id>
```

Verify a generated package without rebuilding it:

```powershell
python -B -m obvious_one_plugin_framework.cli verify `
  --contract .\applications\<plugin-id>\openclaw\distribution.json `
  --output .\dist\openclaw\<plugin-id>
```

Check whether an existing vector index can be reused:

```powershell
python -B -m obvious_one_plugin_framework.cli check-index-reuse `
  --source-manifest .\path\source-index-manifest.json `
  --target-manifest .\path\target-index-manifest.json `
  --source-index .\path\source-index.sqlite3
```

Create an independent target index from compatible vectors:

```powershell
python -B -m obvious_one_plugin_framework.cli derive-index `
  --source-manifest .\path\source-index-manifest.json `
  --target-manifest .\path\target-index-manifest.json `
  --source-index .\path\source-index.sqlite3 `
  --destination .\applications\<plugin-id>\assets\rag\target-index.sqlite3
```

`derive-index` preserves compatible vector blobs but rewrites application and namespace identity. It does not create a runtime-shared content index.

## 4. Framework and product tests

### Multi-application verification

The top-level verifier discovers `applications/*/conversion.json` and validates
the generic framework once before running the selected application-owned test,
audit, smoke, Codex-build, and deterministic OpenClaw-build gates. Every
converted plugin targets both Codex and OpenClaw by default.

Verify every discovered application (also the default when no selector is
given):

```powershell
python -B .\scripts\verify_extraction.py --all
```

Verify one application:

```powershell
python -B .\scripts\verify_extraction.py `
  --application <plugin-id>
```

Compare generated Codex and OpenClaw artifacts with a clean, read-only local
marketplace checkout:

```powershell
python -B .\scripts\verify_extraction.py `
  --all `
  --marketplace D:\GitHub\obvious-one-plugins
```

The migration-compatible single-application form remains accepted:

```powershell
python -B .\scripts\verify_extraction.py `
  --marketplace D:\GitHub\obvious-one-plugins `
  --provenance .\docs\provenance\source-extraction.json
```

`--all` and `--application` are mutually exclusive. `--provenance` may override
the configured source inventory only when exactly one application is selected.
Verification never installs dependencies, downloads models or corpora, writes
to a marketplace, publishes, or pushes.

Reports are written below `.tmp/verification/` and use four states:

- `PASS`: a required gate succeeded;
- `FAIL`: a required gate failed;
- `NOT VERIFIED`: an evidence source was configured but not evaluated, or a
  prerequisite failed;
- `NOT APPLICABLE`: the application does not declare that evidence source.

A local run may return success when marketplace evidence is `NOT VERIFIED`.
That result is not release-readiness evidence. A release-readiness claim needs
the explicitly supplied marketplace comparison and all declared application
invariants.

Application configuration uses `"schema_version": 2`. Its required
`verification` object declares `test_directory`, ordered command objects with
unique `id` and direct `argv` arrays, and a `codex_build` command plus artifact
path. A previously published application also declares `marketplace.codex_path`,
`marketplace.openclaw_path`, and `marketplace.approved_delta`. Supported command
placeholders are `{python}`, `{repository_root}`, `{application_root}`,
`{diagnostics}`, `{plugin_id}`, `{application_id}`, and `{version}`. The version
is always taken from the validated OpenClaw distribution contract.

### Individual suites

Run the generic, network-free framework suite:

```powershell
python -B -m unittest discover -s .\tests\framework -v
```

Run one product suite:

```powershell
python -B -m unittest discover -s .\applications\<plugin-id>\tests -v
```

Validate every skill and the plugin manifest with the installed `skill-creator` and `plugin-creator` helpers. Resolve their installed paths through Codex instead of embedding a developer-specific absolute path in automation.

## 5. Local marketplace installation

From any PowerShell directory:

```powershell
codex plugin marketplace add D:\GitHub\obvious-one-plugins
codex plugin marketplace list
codex plugin add <plugin-id>@obvious-one
```

After changing a published marketplace artifact:

```powershell
codex plugin marketplace upgrade obvious-one
codex plugin add <plugin-id>@obvious-one
```

Always test the installed marketplace copy in a new Codex task. Testing only the development source does not verify the released artifact.

## 6. GitHub marketplace installation

After the marketplace repository has been pushed:

```powershell
codex plugin marketplace add schao523/obvious-one-plugins --ref main
codex plugin marketplace list
codex plugin add <plugin-id>@obvious-one
```

The GitHub repository is a Git-backed Codex marketplace source. Publishing it does not automatically submit a plugin to a universal OpenAI directory.

## 7. GitHub release and workflow commands

Inspect validation runs:

```powershell
gh run list --repo schao523/obvious-one-plugins
gh run view <run-id> --repo schao523/obvious-one-plugins --log-failed
```

Start a configured release workflow:

```powershell
gh workflow run release-openclaw.yml `
  --repo schao523/obvious-one-plugins `
  -f run_managed_rag_gate=true `
  -f publish=false
```

Use `publish=true` only after reviewing the exact release version, generated artifacts, license notices, and Git diff.

## 8. ClawHub retry command

After an immutable GitHub Release already exists, the ClawHub-only workflow may retry publication without rebuilding or replacing that release:

```powershell
gh workflow run retry-clawhub.yml `
  --repo schao523/obvious-one-plugins `
  -f version=<version>
```

The repository secret `CLAWHUB_TOKEN` must be configured. ClawHub admission is a separate distribution channel and may remain unavailable even while direct GitHub marketplace installation works.

## 9. Commands that require explicit approval

Automation should pause before:

- installing large model or PyTorch dependencies;
- downloading external corpora or release assets;
- modifying an existing marketplace entry;
- creating a GitHub Release or immutable tag;
- pushing commits;
- publishing to ClawHub or another external registry;
- deleting the original GPT source or an earlier generated artifact.

Read-only validation, deterministic local builds, and tests may run without publication approval.
