---
name: guiding-vibe-design-sessions
description: Use when a user wants guided software product discovery, iterative specification, or help choosing an appropriate application form before implementation.
---

# Guide Vibe Design Sessions

Turn an idea into an implementable, reviewable software design. Match the user's language; default to Traditional Chinese when their language is unclear.

First determine the simplest software form that satisfies the goal: CLI, TUI, desktop, mobile, API or backend service, worker or automation, library, developer tool, or Web GUI. Use a Web GUI only when the user requests it or the requirements clearly require it. Do not introduce frontend frameworks, routes, Tailwind, SEO, or design tokens for non-Web software.

## Session

Read [references/session-contract.md](references/session-contract.md). Ask the next focused question, maintain a concise decision ledger, and visibly distinguish confirmed decisions, assumptions, and open questions. Offer useful defaults with reasons; never silently decide a scope-changing issue.

Once sufficient decisions exist, use the focused skill matching the next deliverable:

- `creating-software-design-specifications` for the full specification.
- `designing-data-services-and-workflows` for data, APIs, integrations, or stateful flows.
- `creating-implementation-prompts` for a handoff prompt.
- `planning-software-tests` for test scenarios and traceability.
- `reviewing-software-design-specifications` for an existing design.
- `creating-repo-development-packages` for persistent coding-agent documents.

The output is design material. Do not implement the designed application, operate live services, or change the user's environment unless separately requested and authorized.
