# Obvious One plugin distribution framework

This build-time framework generates deterministic lightweight OpenClaw artifacts from plugin-owned contracts. It is repository tooling, not a plugin that end users install. Each generated package receives a small self-contained bootstrap under `vendor/obvious-one-runtime`.

## Add a future plugin

Create `<plugin>/openclaw/distribution.json` with a stable plugin/package identity, version, explicit file and prefix allowlists, excluded paths, size ceiling, release repository/tag, optional README overlay, and a product audit hook. If the plugin uses RAG, declare its `app_id`, owned namespace, runtime/model identities, index manifest, and asset groups. Every group names plugin-owned source files and a plugin-private install subdirectory.

Build and verify without product-specific framework code:

```text
python -B -m tools.obvious_one_plugin_framework.cli build-assets --contract <plugin>/openclaw/distribution.json --output dist/openclaw-assets --manifest <plugin>/assets/openclaw/remote-assets.json
python -B -m tools.obvious_one_plugin_framework.cli build-package --contract <plugin>/openclaw/distribution.json --output dist/openclaw/<plugin-id>
python -B -m tools.obvious_one_plugin_framework.cli verify --contract <plugin>/openclaw/distribution.json --output dist/openclaw/<plugin-id>
```

The generated package may share only content-addressed runtimes and embedding models. Corpora, PDFs, vector indexes, downloads, and authoring data remain below `ObviousOne/plugins/<plugin-id>`; there is no shared content-pack mechanism.

## Reuse compatible vectors at build time

`check-index-reuse` compares source hashes, normalized corpus and structure, ordered chunk identity/text, chunker configuration, model ID/revision/dimensions/normalization, vector schema/serialization, row counts, and source-index integrity. Any mismatch returns `reembedding_required`.

When eligible, `derive-index` copies the source into staging, preserves vector blobs, rewrites all app/namespace identity and provenance for the destination plugin, verifies SQLite integrity and absence of source identity, and atomically activates an independent target index. It never turns the original index into a runtime-shared application content asset.

Product audit hooks should enforce domain-specific provenance and behavior that the generic deny-by-default package audit cannot know. Tests in this directory use only synthetic fixture plugins and must remain network-free.
