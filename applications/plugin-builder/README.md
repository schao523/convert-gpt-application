# Plugin Builder

Plugin Builder converts an approved application-plugin design package into a locally validated OpenAI plugin workspace and deterministic candidate artifact. Version 0.1.1 adds deterministic legacy-handoff normalization, an Agent Plugins 1.0 root manifest, synchronized Codex compatibility metadata, single-directory plugin ZIPs, and digest-closed runtime evidence packaging.

Phase one targets Codex and ChatGPT Work Local/Desktop. OpenClaw and Claude are explicitly out of scope. No marketplace publication, external release, account deployment, credential handling, semantic RAG, or network service is authorized.

Approved design files are internal implementation inputs and are not selected for distribution.

The local distribution contract explicitly selects the plugin manifest, root policy files, portable skills, deterministic scripts, application invariants, and runtime compatibility record. It rejects secrets, private paths, links or reparse points, unsafe attachments, caches, broken relative documentation links, and unfinished scaffold markers.

## Implementation status

The product CLI now implements canonical pass-through and strict recognized-legacy intake, planning, W1 approval, create/update candidate construction, explicit update resolution, deterministic verification, W2 approval, wrapped final ZIP packaging, runtime-evidence closure, and thin pause/resume/cancel operations. Use `inspect --normalized-package PATH` to retain a normalized handoff and `package-runtime-evidence` to build the evidence ZIP; neither operation grants W1, W2, publication, credential, or network authority.

Repository-local T1–T6 scenarios and T7 execution from a generated standalone Codex artifact are runtime verified. The generated artifact vendors only the portable authoring runtime it needs and runs create and update workflows without repository imports. Installed Plugin Builder discovery and representative execution in Codex and ChatGPT Work Local/Desktop remain `NOT VERIFIED`; therefore this implementation is not `READY` and has not been published.
