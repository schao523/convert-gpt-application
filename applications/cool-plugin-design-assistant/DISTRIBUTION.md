# Distribution

The Codex artifact and generated lightweight OpenClaw bundle contain the same
portable application Skills, maintained references, deterministic scripts, and
public policy documents. Tests, conversion state, raw source exports, local
configuration, private paths, caches, diagnostics, and marketplace review state
are excluded.

Local builds and staging do not mutate or publish the Obvious One marketplace.
Pushing, tagging, releasing, marketplace mutation, and registry submission need
separate explicit authorization.

Validate and build from the repository root:

```powershell
python -B -m obvious_one_plugin_framework.cli validate-contract --contract applications/cool-plugin-design-assistant/openclaw/distribution.json
python -B -m obvious_one_plugin_framework.cli build-package --contract applications/cool-plugin-design-assistant/openclaw/distribution.json --output .tmp/cool-plugin-design-assistant/openclaw
python -B -m obvious_one_plugin_framework.cli verify --contract applications/cool-plugin-design-assistant/openclaw/distribution.json --output .tmp/cool-plugin-design-assistant/openclaw
```

Build the Codex marketplace tree separately with
`scripts/build_marketplace_release.py`. These commands only create local
artifacts; none performs publication.
