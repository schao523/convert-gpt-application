# Plugin Builder

Plugin Builder converts an approved application-plugin design package into a locally validated OpenAI plugin workspace and deterministic candidate artifact. Version 0.1.0 establishes the phase-one identity, four portable workflow skills, deterministic session gates, and deny-by-default local packaging boundary.

Phase one targets Codex and ChatGPT Work Local/Desktop. OpenClaw and Claude are explicitly out of scope. No marketplace publication, external release, account deployment, credential handling, semantic RAG, or network service is authorized.

Approved design files are internal implementation inputs and are not selected for distribution.

The local distribution contract explicitly selects the plugin manifest, root policy files, portable skills, deterministic scripts, application invariants, and runtime compatibility record. It rejects secrets, private paths, links or reparse points, unsafe attachments, caches, broken relative documentation links, and unfinished scaffold markers.

## Foundation status

Repository discovery, plugin and skill structure, session-state contracts, deny-by-default distribution, and deterministic local artifact construction are statically verified. The implemented product CLI is intentionally limited to `status --json` and `validate-session <session.json> --json`.

Representative create/update behavior, candidate construction, final ZIP generation through the Plugin Builder workflow, and installed execution in Codex and ChatGPT Work Local/Desktop remain `NOT VERIFIED`. This foundation is not `READY`, is not classified as `PORTABLE`, and has not been published.
