# Product scripts

This directory contains deterministic launchers and validation tools owned by
Cool Plugin Design Assistant. The implementation tasks add those tools without
changing the distribution boundary declared in `openclaw/distribution.json`.

Run `python -B scripts/cool_plugin_design_assistant.py preflight-source-handoff
SOURCE.zip --json` to inspect a Chat-produced source package before official
normalization. It returns PASS (exit 0), BLOCKED (exit 2), or INCOMPLETE
(exit 3) and never creates canonical output. Source ZIP bytes remain unchanged.
