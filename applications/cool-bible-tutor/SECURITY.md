# Security

Report security issues privately to the repository owner before public disclosure. Include the affected plugin version, platform, reproduction steps, and relevant non-sensitive logs.

The release security boundary is enforced by `scripts/distribution_audit.py`, the generic distribution contract, and deterministic package manifests. Bundled or remote databases, PDFs, the compact index, dependency lock, subsystem wheel, and model manifest are digest-bound. `setup-rag` uses explicit consent, argument-array subprocess execution, hash-locked Python packages, HTTPS URLs, safe archive extraction, content-addressed shared caches, plugin-private staging, offline smoke verification, and config-last atomic activation.

Never add credentials, private review data, authoring databases, unapproved PDFs, model weights, caches, or machine-specific paths to the plugin tree. Do not disable TLS or digest verification to work around a setup failure.

Supported releases receive fixes on the latest tagged `cool-bible-tutor-v2.4.x` line. Users should verify release tags and rerun `python scripts/cool_bible_tutor.py status --json` after an upgrade.
