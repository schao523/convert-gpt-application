# Runtime Compatibility Contract

Cool Bible Tutor is distributed to OpenClaw as a native-free, Codex-format compatible bundle. It is not a native OpenClaw code plugin and must not contain `openclaw.plugin.json`.

## Execution boundary

The eight skills contain the teaching workflow. Supporting execution uses the package-local Python launcher:

```text
skill instruction
  -> scripts/cool_bible_tutor.py <command>
  -> package-local Scripture or RAG adapter
  -> immutable corpus or managed local runtime
```

`rag_subsystem` is a pinned Python dependency imported by `rag_runtime.py`. It is not an OpenClaw-registered agent tool. The discovery adapter calls `retrieve_data(query, top_k, filters, config)`, validates `app_id` and namespace isolation, and returns candidate references only. Exact wording always passes through `passage`/`get_passage.py`.

## Readiness layers

| Layer | Ready when | Failure effect |
|---|---|---|
| Package | Host detects the Codex bundle | Plugin unavailable |
| Skills | Eight `SKILL.md` files are model-visible | Teaching capability incomplete |
| Exact retrieval | Frozen `cuv.sqlite3` and manifests validate | Exact quotation disabled |
| Semantic RAG | Explicit managed setup reports `rag_ready` | Topic discovery unavailable; referenced study continues |
| Review | Writable authoring data, PDFs, Poppler, Tesseract, `chi_tra`, and localhost browser access are available | Authoring/review unavailable; runtime corpus remains immutable |
| Publication | The selected marketplace accepts the native-free bundle | Distribution channel unavailable; installed/local package behavior is unchanged |

## Stable commands

```text
python scripts/cool_bible_tutor.py status --json
python scripts/cool_bible_tutor.py verify --json
python scripts/cool_bible_tutor.py passage "約翰福音 3:16" --format json
python scripts/cool_bible_tutor.py setup-rag --accept-downloads
python scripts/cool_bible_tutor.py rag-check --json
python scripts/cool_bible_tutor.py rag-discover "神的愛與救恩" --top-k 5
python scripts/cool_bible_tutor.py doctor --json
python scripts/cool_bible_tutor.py init
python scripts/cool_bible_tutor.py review
```

Exit code `0` from `passage` is the only exact-quotation authorization. RAG exit code `4` means optional discovery is unavailable and must not interrupt a study that already has a passage.

## Host requirements

Core commands require Python and permission to execute package-local scripts. Managed RAG supports CPython 3.10 through 3.13 on the platforms listed in `vendor/rag-runtime/runtime-lock.json`. Setup requires explicit download consent, network access during installation, and the declared disk space. Semantic queries run locally after activation.

Skill-referenced scripts, subprocess execution, and consent-gated downloads are executable surfaces even though OpenClaw exposes this bundle's declared capability as `skills` only.
