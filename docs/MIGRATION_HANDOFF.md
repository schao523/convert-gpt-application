# Controlled Extraction Handoff

## Result

The reusable GPT-application conversion framework and the Cool Bible Tutor
development workspace were extracted into a fresh, independent Git repository
at `D:\GitHub\convert-gpt-application`.

## Provenance

- Integrated source snapshot: `103839c8655706b47fe747f16abf617c774e4e50`
- Verified extracted-content commit: `f77347eee3c92243eddd53febede8811d23d1c10`
- Unchanged marketplace baseline: `e5fd82419ecf52dcb708a35f5b9c453616380822`
- Incorporated source branch: `codex/openclaw-compat-evaluation`
- Source inventory and hashes: `docs/provenance/source-extraction.json`
- Approved unpublished marketplace delta: `docs/provenance/marketplace-approved-delta.json`

The extracted repository has fresh Git history. It does not contain the source
repository's `.git` directory or any developer-specific `conversion.local.json`.

## Verification Evidence

The top-level verifier completed every gate:

- repository layout and source provenance tests: passed
- extraction-boundary tests: 4 passed
- generic framework tests: 29 passed
- application configuration tests: 2 passed
- Cool Bible Tutor product suite: 222 passed, 2 skipped
- distribution audit: passed
- exact CUV retrieval smoke test: John 3:16 returned verified text
- bundled corpus: `core_ready`, 31,008 rows, 0 unverified rows, 71 approved
  source-text gaps
- semantic RAG: explicitly optional and reported `rag_setup_required` until the
  user installs the model/runtime; bundled core retrieval remains ready
- deterministic OpenClaw build: two independently generated trees matched
  byte-for-byte and the generated content manifest verified
- public marketplace: clean at the recorded baseline commit; no files changed

Run the same evidence gate with:

```powershell
python -B .\scripts\verify_extraction.py `
  --marketplace D:\GitHub\obvious-one-plugins `
  --provenance .\docs\provenance\source-extraction.json
```

## Developer Guides

- `docs/GPT_TO_PLUGIN_USER_GUIDE.md`
- `docs/PLUGIN_SKILLS_TECHNICAL_REFERENCE.md`
- `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`

## Repository Boundaries and Side Effects

- Git remote configured for this extracted repository: no
- Commit pushed: no
- Marketplace updated or published: no
- Original GPT source/reference files moved or deleted: no
- Original development repository cleaned up: no
- Separate `rag_subsystem` repository modified by extraction: no

The separate RAG repository currently has a pre-existing untracked
`.cool-bible-tutor-openclaw-livecheck.zip`; the extraction did not create,
modify, stage, or remove it.

## Deferred Original-Repository Cleanup

No cleanup was performed. A future, separately approved cleanup may review the
now-extracted `tools`, `tests/framework`, `cool-bible-tutor` development tree,
`.worktrees`, and source Git metadata. Exact targets must be resolved and backed
up before any deletion. Original GPT instructions and reference files are not
cleanup candidates and remain the source archive.
