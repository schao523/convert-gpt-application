# Privacy

Cool Bible Tutor performs exact Scripture retrieval and semantic discovery locally. The bundled corpus and compact index are read-only. Topic queries, selected references, study answers, and review activity are not sent to the publisher.

`setup-rag --accept-downloads` performs network access only after explicit consent. It contacts the Python package indexes and immutable model-file URLs listed in the runtime manifests. In the lightweight edition it also contacts the immutable GitHub Release URLs in `assets/openclaw/remote-assets.json` for this plugin's index and public-domain PDFs. It sends download requests only; it does not send Bible-study queries.

The managed runtime and model are stored under `ObviousOne/shared-rag/runtimes` and `ObviousOne/shared-rag/models`. This plugin's index, PDFs, downloads, configuration, and authoring data remain under `ObviousOne/plugins/cool-bible-tutor`. `config.json` contains only identities, paths, versions, digests, and a completion timestamp; it contains no credentials or prompts.

Optional authoring/review data, OCR output, corrections, review history, backups, and private vector stores stay outside the plugin and are never included by the marketplace release builder.
