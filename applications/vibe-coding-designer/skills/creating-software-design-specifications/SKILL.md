---
name: creating-software-design-specifications
description: Use when turning confirmed product decisions into a complete implementation-ready specification for Web, desktop, mobile, CLI, TUI, service, worker, library, or developer-tool software.
---

# Create Software Design Specifications

Produce a precise design without implementing it. Read [references/software-design-contract.md](references/software-design-contract.md) and populate all fourteen sections; mark genuinely irrelevant sections `Not applicable` with a reason instead of inventing requirements.

Select the simplest software form that satisfies the goals. Describe interfaces appropriate to that form: commands and exit codes for a CLI, public symbols for a library, messages and schedules for a worker, endpoints for a service, or screens and interactions for a GUI.

Keep confirmed requirements, recommendations, assumptions, and open questions visibly distinct. Stable requirement and acceptance IDs should be testable and traceable. Use `designing-data-services-and-workflows` when exact data, API, or workflow contracts are substantial.

Web design is conditional. Apply responsive layout, WCAG accessibility, design tokens, Tailwind or another chosen styling system, browser performance, and SEO only when the selected form has a Web interface. PostgreSQL and Node.js are optional examples, never universal defaults.

Do not implement the designed application. Never include credentials, private configuration, or executable secrets. Backend examples are non-executable specification patterns.
