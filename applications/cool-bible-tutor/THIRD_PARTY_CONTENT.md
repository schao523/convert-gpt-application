# Third-party content boundary

## Bundled Chinese Union Version PDFs

The plugin owner represents these two source files as public domain and authorizes their redistribution with `cool-bible-tutor`:

- `assets/scripture/Bible 舊約聖經和合本.pdf`, SHA-256 `2740A6F824F96374CB127D78C3D646B489963898DACC252B842D9A8894A91125`
- `assets/scripture/Bible 新約聖經和合本.pdf`, SHA-256 `4F0F9EF4C4A78B83F918C74E8F368A7E0EAE515C17866C7767C310CA75786490`

The files identify International Bible Society / 國際聖經協會 in their metadata or visible pages. That attribution is preserved for provenance. The plugin is not affiliated with or endorsed by International Bible Society, and this repository does not independently certify the owner's public-domain conclusion.

The representation applies only to the two exact hash-matching PDFs. It does not apply to a different Chinese Union Version edition, a same-named replacement, or user-generated corpus, review, OCR, or RAG data.

## External software and generated data

Poppler, Tesseract, and Tesseract language data are external tools with their own licenses and distribution terms. They are not bundled by this plugin.

Both editions bundle a pinned MIT-licensed `rag_subsystem` wheel. The Codex edition bundles the compact public semantic index and PDFs; the OpenClaw edition downloads exact hash-bound copies after consent. Neither bundles RAGenius source, private vector data, the embedding model, or heavyweight dependencies. Those dependencies and the exact MIT-licensed model revision are downloaded into user storage only after consent; see `THIRD_PARTY_NOTICES.md`.

There is no shared Bible content pack. Each plugin owns its corpus and vector-index copies under its plugin-private directory. Build tooling may derive a separately identified index from compatible vectors only when source, chunk, model, dimensions, normalization, schema, ordering, and integrity all match; otherwise it requires re-embedding.

Review history, backups, OCR output, rendered pages, private vector stores, model caches, and user corrections remain each user's external private state. Only the two manifest-bound public runtime databases are allowed in a redistributed plugin archive.
