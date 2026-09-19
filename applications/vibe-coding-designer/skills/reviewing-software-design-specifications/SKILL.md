---
name: reviewing-software-design-specifications
description: Use when reviewing an existing software specification, workflow map, implementation prompt, or repo-development package for completeness, consistency, feasibility, traceability, and risk.
---

# Review Software Design Specifications

Review the artifact against its stated goals and selected software form. Read [references/review-contract.md](references/review-contract.md). Lead with actionable findings ordered by severity and cite the artifact location or identifier supporting each finding.

Check all fourteen design responsibilities, treating explicitly justified `Not applicable` sections as complete. Do not penalize CLI, TUI, service, worker, library, desktop, or mobile designs for lacking Web-only pages, Tailwind, WCAG browser details, or SEO. Do flag a Web design that omits applicable accessibility, responsive, or browser concerns.

Distinguish contradictions, missing requirements, unverifiable acceptance criteria, unsafe defaults, broken workflow references, and optional improvements. Do not silently rewrite requirements or implement the designed application.
