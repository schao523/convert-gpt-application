---
name: creating-repo-development-packages
description: Use when an approved system specification and implementation guidance must become persistent, agent-neutral repository documents such as AGENTS.md, Spec.md, Tasks.md, and justified supporting contracts.
---

# Create Repo Development Packages

Transform the approved system specification into durable development context, not a one-shot code-generation prompt. Read [references/repo-package-contract.md](references/repo-package-contract.md).

Use `Spec.md` as the product and system source of truth, `AGENTS.md` for repository-local agent behavior and reading order, and `Tasks.md` for dependency-aware implementation work. Create supporting documents only when independent responsibility and repeated use reduce context cost.

Assign stable requirement, acceptance, and task IDs. Ensure Requirement → Acceptance → Task → Validation traceability in both directions. Keep core documents agent-neutral and repository-relative; put Codex- or OpenClaw-specific conveniences in optional adapters.

Review the proposed package before writing into a user's repository. Do not overwrite an existing root `AGENTS.md` or other authoritative document without explicit authorization.
