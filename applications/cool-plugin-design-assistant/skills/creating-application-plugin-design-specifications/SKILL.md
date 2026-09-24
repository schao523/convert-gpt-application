---
name: creating-application-plugin-design-specifications
description: Use when confirmed AI Application design decisions are ready to become a complete specification or an approval-gated Application Workbench handoff.
---

# Create Application Plugin Design Specifications

Require the Design Statement, behavioral workflows, Instruction Module
contracts, user-interaction protocols, Reference Material Usage Map, and
decision ledger. Read [the specification contract](references/specification-contract.md)
and produce its 21 sections.

Keep requirements, confirmed decisions, assumptions, recommendations, and
unresolved questions distinct. Present the result as a draft, allow revision,
and require explicit user confirmation before changing its state to approved.
Never hide an unresolved rights, scope, safety, distribution, or architecture
decision inside prose or silently convert it to an assumption.

Only after approval, read
[the Workbench handoff contract](references/workbench-handoff-contract.md) and
package the approved artifacts. The handoff must not prescribe Skill count,
Skill names, Skill collaboration, runtime adapters, storage, RAG, or Reference
Material-to-Skill bindings; the Application Workbench determines them.

If an unresolved owner decision blocks lawful or faithful implementation, keep
the handoff blocked and name the decision, owner, impact, and required evidence.
Do not implement or publish the designed application.

Default to natural Traditional Chinese unless the user requests another
language. Check Traditional character forms before sending.
