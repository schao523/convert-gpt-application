# Runtime compatibility

Classification: `PORTABLE`.

Codex and OpenClaw consume the same seven skill directories without application-level forks. Codex uses `.codex-plugin/plugin.json`; OpenClaw receives a generated `bundle-plugin` package with `package.json` and `CONTENT-MANIFEST.json`. No runtime adapter, MCP server, external service, setup download, model, or RAG subsystem is required.

## Runtime evidence

Runtime verification was performed on 2026-09-19 from generated version
`1.0.0` artifacts:

- Codex 0.146.0 discovered the local marketplace entry, installed the packaged
  plugin, exposed all seven skills, loaded every `SKILL.md` and required
  reference, and completed the representative non-Web CLI design scenario in
  an ephemeral read-only run.
- OpenClaw 2026.9.4 installed all seven generated skills, reported each as
  eligible and model-visible, and completed the same representative scenario.
- Both executions preserved the no-Web decision, produced all fourteen design
  sections, included a workflow with failure paths, reviewed the result,
  derived traceable tests, and supplied implementation-prompt and repository-
  package handoffs.
- The packaged deterministic support tool passed status, design validation,
  workflow validation, and exact coverage calculation from both artifacts.

The temporary Codex marketplace/plugin registration and temporary OpenClaw
workspace installation were removed after verification. Publication remains
not applicable until separately approved.
