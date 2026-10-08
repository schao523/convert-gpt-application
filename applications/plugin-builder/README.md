# Plugin Builder

Plugin Builder converts an approved application-plugin design package into a locally validated OpenAI plugin workspace and deterministic candidate artifact. Version 1.0.1 retains the shared `WORKBENCH_HANDOFF_V1_1` interface and adds whole-tree pre-W1 compilation: semantic content roles, knowledge ownership, deterministic duplicate evidence, path validation, explicit runtime adapters, and target-aware manifest profiles are checked before an approvable W1 identity exists.

Phase one targets Codex and ChatGPT Work Local/Desktop. OpenClaw and Claude are explicitly out of scope. Private/local ZIP, the public GitHub Codex marketplace, and the OpenAI universal directory are approved release targets, but no upload, marketplace mutation, external release, account deployment, or directory submission has been performed or authorized by this implementation run.

Approved design files are internal implementation inputs and are not selected for distribution.

The local distribution contract explicitly selects the plugin manifest, root policy files, portable skills, deterministic scripts, application invariants, and runtime compatibility record. It rejects secrets, private paths, links or reparse points, unsafe attachments, caches, broken relative documentation links, and unfinished scaffold markers.

## Implementation status

The product CLI implements canonical v1.1 pass-through, retained canonical-v1 compatibility, strict recognized-legacy full/delta intake, planning, W1 approval, create/update candidate construction, explicit update resolution, deterministic verification, W2 approval, wrapped final ZIP packaging, runtime-evidence closure, and thin pause/resume/cancel operations. Verification and the external package sidecar preserve the exact approved preflight evidence, declared and observed commands, manifest profile, and independent structural, installation, tool-execution, reference-consultation, and conversation states. Use `inspect --normalized-package PATH` to retain a normalized handoff and `package-runtime-evidence` to build the evidence ZIP; neither operation grants W1, W2, publication, credential, or network authority.

Repository-local T1–T6 scenarios and T7 execution from a generated standalone Codex artifact are runtime verified. The generated artifact vendors only the portable authoring runtime it needs and runs create and update workflows without repository imports. Installed Plugin Builder discovery and representative execution in Codex and ChatGPT Work Local/Desktop remain `NOT VERIFIED`; therefore this implementation is not `READY` and has not been published.

The runtime-realization-v2 extension identifies required capabilities and target-specific Skill-to-operation routes before W1, supports an explicitly approved local MCP operation check, and packages a separate T8 contract with a v3 digest-addressed evidence template. Build-host loopback success is not installed Skill execution. The reviewed standalone kit supports replay; no installed T8 observation or external-service authorization is implied.

For owner replay, build the separate deterministic T1–T8 kit with `tests/runtime/build-runtime-kit.py --source applications/plugin-builder --release <reviewed-release-root> --plugin-zip <exact-upload-zip> --output <kit.zip>`. It contains both sample handoff ZIPs, the exact install artifact and release inventory, generated scenario inputs, and v2/v3 schemas. A v3 evidence bundle requires that exact reviewed ZIP plus the matching W1-approved plan and session; it cannot promote a local operation test to installed-runtime proof.
