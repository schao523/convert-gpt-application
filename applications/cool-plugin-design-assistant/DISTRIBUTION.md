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

## Handoff delivery contract

| Key | Outcome |
| --- | --- |
| FINAL_ZIP_SHA256 | REPORT_EXACT_RETURNED_BYTES |
| REOPEN_CANONICAL_VALIDATION | REQUIRED_BEFORE_DELIVERY |
| ONE_SEMANTIC_AUTHORITY | WORKBENCH_HANDOFF_JSON |

Version 1.0.2 applies this digest-bound final-ZIP contract to chat and CLI normalization. It does not reopen approved design behavior, infer approval from normalization, or authorize publication.

Version 1.0.3 adds read-only Source Contract Preflight and the Chat-to-Work
Source Handoff route. A preflight PASS covers the source input contract only;
official normalization and reopened canonical validation remain required.
This 1.0.3 tree is a local candidate until separately approved publication.
The OpenClaw schema-v3 contract declares the two shared Python framework
packages required by the handoff commands; the package builder vendors and
manifest-binds them without adding RAG or an external dependency.
