# Source and distribution decisions

The approved behavioral authority is `SPEC-v1.0`. The original owner-approved handoff ZIP has SHA-256 `8edde15b6bd0e658990c3a354b85ea90b93bfa1c17216c7b11928f8284c3f497`; its normalized, repository-gate-compatible form has SHA-256 `953747ad9f92d05dc29a049359fa06227fc2f8cc8590242cd4d1f09e17f82b21`.

The ten inventoried design files are internal implementation inputs. They are not selected for a public artifact. Phase one authorizes local implementation and verification for ChatGPT Work Local/Desktop and Codex only; it does not authorize marketplace mutation, publication, a GitHub release, ClawHub submission, or another external registry.

The application-authored manifest, root policy files, portable skills, deterministic scripts, `docs/application-invariants.md`, and `docs/runtime-compatibility.md` are approved for local packaging under the repository license. Those two documentation paths are the complete phase-one public documentation allowlist. The other files below `docs/` remain internal. Third-party runtime resources remain unresolved per build and are excluded unless a later explicit rights decision approves them.

`NOT_AUTHORIZED_PHASE_ONE` and the all-zero marketplace commit in the provenance record are explicit schema sentinels: no marketplace baseline, mapping, delta, commit, or publication has been approved or performed.
