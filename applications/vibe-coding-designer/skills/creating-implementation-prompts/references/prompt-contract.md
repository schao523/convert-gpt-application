# Implementation prompt contract

Use this shape:

1. `# SYSTEM CONTEXT` — role, repository context, and chosen software form.
2. `# INPUT` — concise authoritative specification and referenced files.
3. `# REQUIREMENTS` — functional, interface, data, workflow, security, and quality requirements that apply.
4. `# CONSTRAINTS` — technology choices, boundaries, prohibited changes, and compatibility needs.
5. `# DELIVERABLES` — files or observable outputs, without inventing implementation details.
6. `# VALIDATION` — acceptance IDs, test expectations, deterministic commands, and evidence format.
7. `# ASSUMPTIONS AND TODO` — only unresolved or explicitly assumed items.

When a canonical workflow exists, append it under `# EXECUTION_MAP` exactly. Large source material may be attached under `# REFERENCE` and must be labeled context-only. Omit empty optional blocks.
