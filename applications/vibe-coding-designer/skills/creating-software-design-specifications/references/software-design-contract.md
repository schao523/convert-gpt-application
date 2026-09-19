# Software design contract

Use this stable fourteen-section structure. Tailor the content—not the accountability—to the selected software form.

1. **Executive Summary** — problem, proposed outcome, and software form.
2. **Goals and Non-goals** — measurable goals and explicit boundaries.
3. **Users and Actors** — people, systems, roles, trust, and permissions.
4. **Use Cases and Flows** — triggers, normal paths, alternatives, and failures.
5. **Software Form and System Boundaries** — components, ownership, and external systems.
6. **Interface Specification** — CLI/TUI commands, library API, service endpoints, events, files, screens, or combinations.
7. **Component Architecture** — responsibilities, dependencies, and prohibited coupling.
8. **Data and Persistence** — entities, validation, relationships, lifecycle, retention, storage, or no persistence.
9. **Services and Integrations** — internal/external contracts, authentication expectations, errors, and timeouts.
10. **Workflow Specification** — states, triggers, guards, retries, compensation, and terminal outcomes.
11. **Quality Attributes** — performance, reliability, compatibility, observability, accessibility, localization, and maintainability.
12. **Security and Privacy** — threats, authorization, data minimization, secrets policy, and abuse controls.
13. **Validation and Acceptance** — requirement IDs, acceptance IDs, test levels, fixtures, and evidence.
14. **Assumptions and Open Questions** — labeled decisions still requiring confirmation.

## Conditional interface rules

- CLI/TUI: specify commands, arguments, standard input/output/error, exit codes, interactive states, scripting behavior, and terminal compatibility.
- Library/package: specify public symbols, types, errors, compatibility, lifecycle, and examples.
- API/service: specify operations, schemas, validation, errors, auth boundaries, idempotency, rate limits, health, and observability.
- Worker/automation: specify triggers, schedules, queues, concurrency, retries, idempotency, compensation, and dead-letter/manual recovery.
- Desktop/mobile: specify navigation, platform conventions, permissions, offline behavior, accessibility, and packaging.
- Web GUI: specify pages/routes, components/states, responsive behavior, keyboard and focus behavior, forms and ARIA, WCAG AA contrast, asset loading, browser support, and SEO when public discovery matters.

Web GUI is only when explicitly requested or clearly required. Web-only rules are conditional and must not leak into a non-Web design.
