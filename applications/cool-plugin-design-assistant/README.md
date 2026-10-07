# Cool Plugin Design Assistant

Version 1.0.2 strengthens the Workbench handoff boundary without changing approved application behavior. Chat-driven handoff delivery now binds the returned canonical ZIP to its final SHA-256, reopens that exact ZIP for canonical validation, and reports one `workbench-handoff.json` semantic authority before delivery.

Cool Plugin Design Assistant 1.0 guides a human from an AI Application idea to
an approval-gated Application Plugin Design Specification and structured
Application Workbench handoff. It also supports implementation conformance
review and traceable Application Testing planning.

The plugin is skills-only. It contains no MCP server, external service, corpus,
database, model, semantic RAG, telemetry, credential requirement, or automatic
publication behavior.

## Product launcher

Run the standard-library launcher from the repository root:

```powershell
python -B applications\cool-plugin-design-assistant\scripts\cool_plugin_design_assistant.py status --json
```

Commands:

- `status`
- `validate-design <design-statement.md> <design-specification.md>`
- `validate-workflow <workflow.json>`
- `validate-modules <modules.json>`
- `validate-handoff <handoff.json>`
- `normalize-handoff-package <approved.zip> <normalized.zip> --confirmed-by <owner> [--runtime-scope OPENAI_ONLY_PHASE_ONE]`
- `coverage <coverage.json>`
- `distribution-audit [stage]`

`normalize-handoff-package` emits `WORKBENCH_HANDOFF_V1_1` for approved full and
delta Design Assistant packages. It preserves approved artifact bytes, exact
requirement IDs/source bindings/text, approval evidence, and update baseline
contracts; validates the canonical pair; and writes a byte-deterministic ZIP.
Legacy input without exact semantic authority remains blocked. It refuses to
overwrite an existing destination. Phase one accepts only the explicitly
approved `OPENAI_ONLY_PHASE_ONE` runtime scope.

Every operation emits one ASCII-safe JSON document with `status`, `operation`,
and `errors`. Exit code `0` means the operation passed, `2` means required input
or evidence is blocked, and `3` means validation failed. A successful static
validation is not runtime execution evidence.
