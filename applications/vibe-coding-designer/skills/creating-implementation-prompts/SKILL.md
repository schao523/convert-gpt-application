---
name: creating-implementation-prompts
description: Use when an approved software design must be converted into a self-contained, implementation-agent handoff prompt with constraints, deliverables, validation, and traceable references.
---

# Create Implementation Prompts

Create the prompt from an approved specification; do not use the prompt to change product requirements. Read [references/prompt-contract.md](references/prompt-contract.md).

Target the selected software form and implementation environment. A CLI prompt asks for commands, outputs, exit codes, and packaging; a library prompt asks for its public API; a worker prompt asks for triggers and failure semantics. Request HTML, Tailwind, responsive behavior, WCAG, or SEO only for a Web interface that needs them.

Preserve exact identifiers, schemas, workflow state IDs, and service bindings. Reference a canonical workflow execution map without rewriting it. End with verification commands or acceptance evidence and a concise assumptions/TODO list.

Never include credentials or hidden local configuration. Do not claim that tests, coverage, builds, or runtime behavior have been verified unless evidence is supplied.
