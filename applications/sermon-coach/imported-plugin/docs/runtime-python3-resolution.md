# Python 3 runtime resolution — v1.0.2

This plugin has two `BUNDLED_LOCAL` Python tools: `sermon-control` and `packaged-reference-access`.

Do not assume the command name `python3` exists on every declared runtime. Before invoking either tool, resolve a Python 3 launcher using the platform profile below.

## Windows

1. Probe `py -3`. Use it only if the probe confirms Python major version 3.
2. Otherwise probe `python`. Use it only if the probe confirms Python major version 3.
3. If neither candidate is a verified Python 3 interpreter, mark the tool unavailable and **BLOCK** the affected deterministic operation. Do not silently fall back to model reasoning.

## POSIX (Linux/macOS)

1. Probe `python3`. Use it only if the probe confirms Python major version 3.
2. Otherwise probe `python`. Use it only if the probe confirms Python major version 3.
3. If neither candidate is a verified Python 3 interpreter, mark the tool unavailable and **BLOCK** the affected deterministic operation.

## Execution

After resolution, execute the selected launcher followed by the declared script path and tool arguments/stdin. The same resolved launcher policy applies to verification.

This is an implementation-only runtime compatibility rule. It does not change WF/IM/UIP behavior, Skill responsibilities, reference authority, or user-visible product behavior.
