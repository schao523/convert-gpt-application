# 酷聖經教師 / Cool Bible Tutor for OpenClaw

This is the lightweight OpenClaw edition of Cool Bible Tutor v2.4.6. It includes all eight Bible Tutor skills and the immutable, fully verified public-domain Chinese Union Version verse database. Exact reference lookup works immediately after installation and does not require network access or RAG setup.

OpenClaw loads this package as a native-free, Codex-format compatible bundle, not as a native OpenClaw code plugin. Supporting capabilities run through the package-local Python launcher; `rag_subsystem` is an imported Python dependency behind that boundary, not a separately registered agent tool. Readiness is layered across package detection, skills, exact retrieval, optional RAG, review/authoring, and publication. See `docs/runtime-compatibility-contract.md`.

## Quick start

From this package directory:

```text
python scripts/cool_bible_tutor.py passage "約翰福音 3:16"
python scripts/cool_bible_tutor.py status
```

OpenClaw may invoke the same supporting scripts inline when a skill needs exact verse text.

## Optional semantic discovery

Topic-based discovery requires an embedding runtime, model, Bible vector index, and the two source PDFs. These bytes are deliberately not hidden inside the lightweight package. Review the download notice and give explicit consent:

```text
python scripts/cool_bible_tutor.py setup-rag --accept-downloads
python scripts/cool_bible_tutor.py rag-check
python scripts/cool_bible_tutor.py rag-discover "神的愛與救恩"
```

The setup verifies pinned hashes before activation. Compatible plugins may reuse only the content-addressed execution dependencies:

- `ObviousOne/shared-rag/runtimes/<runtime-lock-digest>`
- `ObviousOne/shared-rag/models/<model-digest>`

Bible content remains owned by this plugin and is never treated as a shared content pack:

- `ObviousOne/plugins/cool-bible-tutor/indexes`
- `ObviousOne/plugins/cool-bible-tutor/source-assets`

Use `setup-rag --accept-downloads --repair` to repeat verification and repair an incomplete setup. The setup can require several gigabytes of free disk space because PyTorch and the embedding model are substantial downloads.

## Local review tool

The bundled verse database is immutable. Authoring and review use a private writable copy outside the installed package:

```text
python scripts/cool_bible_tutor.py init
python scripts/cool_bible_tutor.py review
```

The review server binds to localhost. Review history and other authoring data remain under `ObviousOne/plugins/cool-bible-tutor/authoring-data` and are not included in public artifacts.

## Privacy, removal, and licensing

Exact lookup is local. Optional RAG setup contacts the pinned model host and the Obvious One GitHub release URLs declared in `assets/openclaw/remote-assets.json`. Semantic queries run locally after setup.

Removing this package does not automatically delete shared runtime/model caches, because another plugin may use the same digest. This plugin's private `indexes`, `source-assets`, `downloads`, and `authoring-data` directories may be removed separately when they are no longer needed.

Plugin code is MIT licensed. The bundled Chinese Union Version corpus and separately downloaded Bible PDFs are identified as public domain in `THIRD_PARTY_CONTENT.md`; dependency and model notices are in `THIRD_PARTY_NOTICES.md`.
