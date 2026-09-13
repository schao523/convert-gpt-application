---
name: retrieving-chinese-union-version-scripture
description: Use when a request contains a Bible reference, asks for exact Chinese Union Version quotation or a verse range, or another Bible Tutor phase requires verified passage text.
---

# Retrieve Chinese Union Version Scripture

Use the hash-validated bundled immutable corpus by default, or an explicitly selected verifier-clean external corpus; never reconstruct exact wording from model memory. Ordinary exact retrieval is ready immediately and does not require rebuilding the PDFs.

For setup, diagnostics, status, review, retrieval tests, and optional RAG operations, prefer the stable launcher at `<plugin-root>/scripts/cool_bible_tutor.py`; locate `<plugin-root>` from this skill's installed path. It delegates to the named supporting scripts below and preserves their exit codes. Read [setup Scripture data](references/setup-scripture-data.md) when setup or repair is needed.

## Discover references when needed

If a calling Tutor skill supplies a topic but no Bible reference, run launcher command `rag-discover "<主題>"`; it delegates to `scripts/discover_bible_references.py`. Its successful output is a ranked list of 候選引用 with corpus trust and RAG index status. It is a discovery layer only: **不可把 RAG chunk 當作精確引文**, and do not expose chunk text, scores, embeddings, or raw diagnostics. On discovery exit code 4, return control with RAG unavailable so the caller can request a reference or pasted passage. A known reference goes directly to retrieval without discovery.

## Route corpus review to the human reviewer

When the user asks to inspect gaps, correct OCR text, or verify private-corpus rows, read [setup Scripture data](references/setup-scripture-data.md) and run launcher command `review`; it delegates to the supporting localhost tool `scripts/review_cuv_index.py`. This is not a ninth Tutor skill. It uses the bundled PDFs by default, displays only sources whose hashes match the corpus, and uses backup, audit history, explicit confirmations, and optimistic concurrency for writes.

**Human comparison with the displayed PDF is the only verification authority.** RAG results, OCR confidence, existing text, and model memory **不可自動核實** a row. Never infer or fill Scripture wording. Browser review also does not change the quotation gate below: after review, only `get_passage.py` exit code 0 authorizes exact CUV quotation. Corpus changes mark RAG discovery stale. For verification-only changes, the reviewer may offer metadata-only synchronization when the JSON vector store's text and provenance still match the corpus; otherwise advise a successful full, unfiltered `ingest_bible_rag.py` run before describing discovery as current.

## Retrieve before quoting

1. Run launcher command `passage "<引用>" --format json`; it delegates to `scripts/get_passage.py`. Pass `--data-dir <目錄>` only when the user or workspace explicitly selects an external corpus; otherwise the launcher uses the bundled read-only runtime database.
2. Read [corpus and verification](references/corpus-and-verification.md) and honor the process result:
   - **退出碼 0**: all returned records are verified and meet the stored confidence threshold. Present the canonical reference, verse-separated text, trust status, source filename, page, and confidence. It may be identified as an exact quotation from this verified local CUV corpus.
   - **退出碼 2**: reference, setup, database, or lookup failed. Do not guess. Give concise guidance from [setup Scripture data](references/setup-scripture-data.md), or ask the learner to paste and identify the passage.
   - **退出碼 3**: one or more rows are unverified or below threshold. Clearly label the result as 待核 OCR 文字；**不可當作精確引文**. Offer provenance for human checking or ask the learner to paste verified text.
3. Return the passage and trust information to the calling observation, interpretation, theology, or application skill. Retrieval itself does not settle interpretation.

For a discovered candidate, `get_passage.py` **只有退出碼 0** can establish verified exact CUV wording. RAG trust metadata never replaces this retrieval gate.

## Quotation contract

- Preserve verse boundaries and canonical order; do not silently correct, modernize, merge, or complete OCR text.
- Distinguish verified quotation, unverified OCR, learner-supplied text, paraphrase, interpretation, and inference.
- Show only the requested range plus minimal context needed by the calling skill.
- Never expose local absolute paths in ordinary output; show the source filename and page only.
- Never copy the private database, page images, OCR output, extracted Scripture, review history, backups, or RAG data into the plugin or a shared package. Only the two package-managed, hash-allowlisted PDFs under `assets/scripture/` are redistributable source assets.

If the learner disputes a verified row, treat it as contested, display provenance, and recommend checking the source PDF rather than defending the index as infallible.
