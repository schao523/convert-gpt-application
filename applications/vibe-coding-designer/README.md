# Vibe Coding Designer

Vibe Coding Designer 1.0 turns product ideas into implementation-ready software designs. It supports Web, desktop, mobile, CLI, TUI, services and APIs, workers and automations, libraries, packages, and developer tools. A Web GUI is used only when requested or required.

The plugin provides seven portable skills for guided discovery, specifications, data/services/workflows, implementation prompts, review, testing, and repository development packages. It contains no MCP server, corpus, model, vector index, semantic RAG, telemetry, or credential requirement.

## Deterministic tools

Run from this plugin root:

```powershell
python -B scripts/vibe_designer.py status --json
python -B scripts/vibe_designer.py validate-design path/to/spec.md --json
python -B scripts/vibe_designer.py validate-workflow path/to/workflow.json --json
python -B scripts/vibe_designer.py coverage path/to/coverage-map.json --json
```

These tools validate structure and exact identifiers. They do not implement or execute the designed application.

## Runtime support

The same `skills/` tree is packaged for Codex and OpenClaw. See [DISTRIBUTION.md](DISTRIBUTION.md) and [docs/runtime-compatibility.md](docs/runtime-compatibility.md).
