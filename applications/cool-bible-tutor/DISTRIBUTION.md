# Distribution

`cool-bible-tutor` v2.4.6 is published as a fully bundled Codex artifact and a generated lightweight OpenClaw artifact. Install either whole artifact so its manifest, `assets/`, `skills/`, `scripts/`, and `vendor/` remain together.

The plugin uses native inline skill execution. Its orchestrator routes work among the eight bundled skills in the current task. It requires no shared Bible-text service and makes no machine-specific path assumption. RAG discovery is an optional local supporting layer, not a ninth user-facing skill.

## Bundled Scripture sources

The plugin owner represents the following Chinese Union Version PDFs as public-domain content and authorizes their redistribution in this package:

- `assets/scripture/Bible 舊約聖經和合本.pdf` — SHA-256 `2740A6F824F96374CB127D78C3D646B489963898DACC252B842D9A8894A91125`
- `assets/scripture/Bible 新約聖經和合本.pdf` — SHA-256 `4F0F9EF4C4A78B83F918C74E8F368A7E0EAE515C17866C7767C310CA75786490`

The files visibly identify International Bible Society / 國際聖經協會 as their source. This notice records provenance and the owner's public-domain representation; it does not imply affiliation or endorsement. The distribution audit rejects a missing, moved, renamed, modified, or additional PDF.

The PDFs are immutable source assets. The release also contains `assets/scripture/cuv.sqlite3`, a normalized, immutable 31,008-row runtime database, plus its approved-gap and runtime manifests. Its 71 owner-confirmed source discontinuities are accepted only when the source hashes, authoring digest, runtime digest, structure digest, row count, table allowlist, and exact event list match. The database is opened read-only and enables exact verified retrieval immediately after installation.

Review history, backups, OCR output, build state, user corrections, machine paths, and every other generated database remain private and external. A bundled row is changed only by reviewing an external authoring corpus and publishing a new hash-locked release snapshot.

## Immediate retrieval and optional authoring corpus

Ordinary retrieval needs no Poppler, Tesseract, OCR run, corpus build, or network request:

```text
python scripts/cool_bible_tutor.py status --json
python scripts/cool_bible_tutor.py passage "約 3:16" --format json
```

Install Poppler (`pdfinfo`, `pdftotext`, and `pdftoppm`), Tesseract, and the Traditional Chinese `chi_tra` language data only for optional authoring and review workflows.

From `skills/retrieving-chinese-union-version-scripture/`, the bundled PDFs are the default sources:

```text
python scripts/build_cuv_index.py --data-dir <私有資料目錄> [--tessdata-dir <語言資料目錄>] [--scratch-dir <純 ASCII 暫存目錄>]
python scripts/verify_cuv_index.py <私有資料目錄>/cuv.sqlite3 --json
python scripts/get_passage.py --reference "太 5:3-4" --data-dir <私有資料目錄> --format json
python scripts/review_cuv_index.py --data-dir <私有資料目錄> --port 0
```

Authorized external replacements remain supported. Supply both `--old-testament <舊約.pdf>` and `--new-testament <新約.pdf>` to the builder; supply repeated `--source-pdf` arguments to verification or review. For review, `COOL_BIBLE_TUTOR_SOURCE_PDFS` is the environment override. Explicit CLI paths take precedence over environment paths, which take precedence over the bundled pair.

Keep `--data-dir` outside the plugin. It overrides `COOL_BIBLE_TUTOR_DATA_DIR`. Only verifier-clean rows and `get_passage.py` exit code `0` may be labeled as verified exact quotation; exit code `3` remains unverified OCR. The localhost review tool binds only `127.0.0.1`, validates source hashes against the database, backs up before the first write, records separate audit history, and never verifies text automatically.

Review mutations mark RAG discovery stale. With the JSON vector backend, the reviewer can reuse existing embeddings and synchronize only trust metadata when the last full ingestion recorded matching corpus-structure, actual item-count, and chunk-identity baselines and every present chunk's text and provenance still match. It takes the project JSON-writer lock, backs up, and atomically validates the vector file before clearing stale state. Full ingestion also rechecks that the corpus did not change while it ran. Text, source, structure, chunk-count, identity, unsupported-backend, or validation changes still require a successful full `scripts/ingest_bible_rag.py --data-dir <私有資料目錄>` run.

## Managed optional RAG discovery

The Codex artifact includes the manifest-bound 9,942-chunk, 1,024-dimensional `assets/rag/cuv-rag-index.sqlite3` and the two public-domain PDFs. The lightweight OpenClaw artifact excludes those large files but includes their immutable release manifest. Both artifacts include the pinned MIT `rag_subsystem` wheel, dependency lock, model manifest, launcher, exact `cuv.sqlite3`, and vendored generic bootstrap. Framework source is build-time tooling and is not a separately installed plugin.

After explicit consent, `python scripts/cool_bible_tutor.py setup-rag --accept-downloads` installs the CPU-only hash-locked runtime and downloads the exact pinned model revision into per-user application data. The OpenClaw artifact additionally downloads the plugin-owned index and PDFs from the immutable GitHub Release URLs. The operation verifies every digest, loads the model offline, runs a Traditional Chinese semantic smoke query, and activates `config.json` last. Topic queries remain local.

Execution dependencies are content-addressed and reusable at `ObviousOne/shared-rag/runtimes/<digest>` and `ObviousOne/shared-rag/models/<digest>`. Content is isolated at `ObviousOne/plugins/cool-bible-tutor/indexes` and `ObviousOne/plugins/cool-bible-tutor/source-assets`. There is no shared Bible content pack: a future plugin carries or downloads its own copy, even when build-time compatibility checks permit reuse of existing vector values to derive an independently identified index.

Advanced users may still override the managed runtime with `COOL_BIBLE_TUTOR_RAG_ROOT` and `COOL_BIBLE_TUTOR_RAG_PYTHON`. Discovery returns references and trust/provenance metadata only; the selected reference still passes through `get_passage.py`, so semantic retrieval never authorizes exact quotation.

Except for the exact manifest-bound corpus and compact RAG index, the redistributable plugin 不得包含 embedding model weights, writable/private vector stores, generated databases, review-history databases, backups, rendered pages, OCR output, user corrections, credentials, caches, or machine-specific configuration.

The package covers the full Bible Tutor v2.4 teaching behavior. The church ministry prompt-template module is intentionally excluded.

Before sharing, run:

```text
python -B scripts/distribution_audit.py .
```

The audit allows only the two hash-matching PDFs, exact public corpus, and exact compact index named above. It validates the vendored runtime manifests and rejects every other database, vector/model file, PDF, private runtime artifact, cache, absolute user path, scaffold marker, and broken local Markdown link. Build the clean public tree with:

```text
python -B scripts/build_marketplace_release.py --source . --destination <marketplace-root> --version 2.4.6
```
