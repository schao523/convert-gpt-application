# Source and redistribution decisions

The project author stated that the source assets are author-provided and approved MIT redistribution for normalized plugin code and reference content.

## Included as normalized derivatives

- guided design behavior and safety boundaries;
- conditional Web design tokens and accessibility/performance guidance;
- non-executable data/API patterns;
- workflow execution-map structure;
- implementation-prompt structure;
- repository development methodology, document architecture, templates, and traceability rules.

## Excluded

- DOCX and PDF exports, because normalized Markdown is sufficient;
- the resource index, because it refers to absent PDF names and is authoring metadata;
- `Old/` concatenated files, because they are superseded duplicates;
- example credentials, private paths, review history, local configuration, generated diagnostics, databases, models, and indexes.

No semantic retrieval is needed: the maintained references are small, structured, and linked directly. Exact workflow identifiers and coverage mappings use deterministic JSON validation.

## OpenAI-hosted target adapter

The author-approved hosted adapter is a normalized MIT-licensed derivative of
the Vibe Coding Designer application. It contains only two target manifests and
an explicit-only compatibility router with a deterministic lookup index. The
seven focused skills remain byte-derived from the canonical `skills/` trees.

The create declaration uses the canonical `vibe-coding-designer` package
identity. Synthetic update identity under `tests/fixtures` is test-owned and is
not evidence of a live upload. A production hosted identity record may be added
only after a separately reviewed import proposal and decision-owner approval.
