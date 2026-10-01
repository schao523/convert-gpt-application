# Distribution

This phase authorizes deterministic local Codex artifact construction only. The schema-v3 content contract is deny-by-default and both publication surfaces are disabled.

The approved design package, development tests, provenance records, and internal design documents are excluded from public artifact selection. Publication, marketplace mutation, tags, releases, and external-registry submission require separate explicit owner approval and have not been performed.

The only distributable application documentation below `docs/` is `application-invariants.md` and `runtime-compatibility.md`. Local builds are audited before replacement and carry deterministic content manifests; successful construction does not change the publication state.

Version 0.1.1 distributes both root `plugin.json` (Agent Plugins 1.0 authority) and `.codex-plugin/plugin.json` (OpenAI compatibility overlay). The installed scripts include canonical/legacy handoff normalization and digest-addressed runtime-evidence packaging. Generated plugin ZIPs use one `<plugin-name>/` directory; development tests and approved source-design archives remain excluded.
