# Cool Plugin Design Assistant

Version 1.0.3 adds a Source Handoff route for Chat sessions that cannot execute normalization. A Work session preflights the source ZIP, runs official normalization, and validates the final Canonical Handoff ZIP. Version 1.0.2 established digest-bound canonical delivery.

Cool Plugin Design Assistant 1.0 guides a human from an AI Application idea to
an approval-gated Application Plugin Design Specification and structured
Application Workbench handoff. It also supports implementation conformance
review and traceable Application Testing planning.

The plugin is skills-only. It contains no MCP server, external service, corpus,
database, model, semantic RAG, telemetry, credential requirement, or automatic
publication behavior.

## Product launcher

Run the standard-library launcher from the plugin root:

```powershell
python -B scripts/cool_plugin_design_assistant.py status --json
```

Commands:

- `status`
- `validate-design <design-statement.md> <design-specification.md>`
- `validate-workflow <workflow.json>`
- `validate-modules <modules.json>`
- `validate-handoff <handoff.json>`
- `normalize-handoff-package <approved.zip> <normalized.zip> --confirmed-by <owner> [--runtime-scope OPENAI_ONLY_PHASE_ONE]`
- `preflight-source-handoff <source.zip> --json`
- `coverage <coverage.json>`
- `distribution-audit [stage]`

`normalize-handoff-package` emits `WORKBENCH_HANDOFF_V1_1` for approved full and
delta Design Assistant packages. It preserves approved artifact bytes, exact
requirement IDs/source bindings/text, approval evidence, and update baseline
contracts; validates the canonical pair; and writes a byte-deterministic ZIP.
Legacy input without exact semantic authority remains blocked. It refuses to
overwrite an existing destination. Phase one accepts only the explicitly
approved `OPENAI_ONLY_PHASE_ONE` runtime scope.

`preflight-source-handoff` accepts the existing full and delta Design Assistant
source envelopes and returns `PASS`, `BLOCKED`, or `INCOMPLETE` with structured
PF01–PF10 checks. It reads the source ZIP without producing a canonical ZIP.
If Chat cannot execute preflight, it may transfer the source with the label
`SOURCE HANDOFF — PREFLIGHT NOT VERIFIED`; Work must preflight it before
normalization. See the owning Skill's source-handoff guide.

Every operation emits one ASCII-safe JSON document with `status`, `operation`,
and `errors`. Exit code `0` means the operation passed, `2` means required input
or evidence is blocked, and `3` means validation failed or preflight is
`INCOMPLETE`. A successful static
validation is not runtime execution evidence.
