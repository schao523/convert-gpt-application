# Cool Plugin Design Assistant

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
- `coverage <coverage.json>`
- `distribution-audit [stage]`

Every operation emits one ASCII-safe JSON document with `status`, `operation`,
and `errors`. Exit code `0` means the operation passed, `2` means required input
or evidence is blocked, and `3` means validation failed. A successful static
validation is not runtime execution evidence.
