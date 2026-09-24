---
name: creating-design-statements
description: Use when a user wants to create, compare, or revise the concise intent statement for an AI Application before detailed specification.
---

# Create Design Statements

Read [the Design Statement contract](references/design-statement-contract.md).
Use confirmed audience, context, problem, application role or method, desired
outcome, and material style or tone decisions. Ask one focused question and
wait when a missing field would change the statement materially. If the user
requires a draft without answering, label any reversible assumption explicitly
and keep the affected field unresolved.
Do not treat a restatement or the obvious inverse of the problem as a confirmed
desired outcome. Ask what success changes or makes possible, or label that
derived outcome as an assumption inside the artifact.

Produce a concise versioned artifact with state `draft` or `approved`. When
comparison helps, offer two or three materially different versions and explain
the differences. Let the user select, combine, reject, or revise them.

Keep the Design Statement separate from the Application Plugin Design
Specification. Never mark it approved without explicit confirmation. Do not
add workflows, Instruction Modules, reference bindings, tools, tests, runtime
architecture, or publication decisions to this artifact.

Default to natural Traditional Chinese unless the user requests another
language. Before sending Traditional Chinese, check that character forms remain
Traditional rather than Simplified.
