# W1 — v1.0.2 runtime compatibility fix

Status: APPROVED by owner in chat.

Scope: implementation-only. Replace fixed `python3` application-tool bindings with platform-specific Python 3 launcher resolution for `sermon-control` and `packaged-reference-access`.

Preserved: WF/IM/UIP, Skill decomposition, reference authority, v1.0.1 consultation trace, structured CUV retrieval, canonical references, user-visible behavior.

Required behavior:
- Windows: prefer `py -3`, then `python`, only after a Python-3 probe succeeds.
- POSIX: prefer `python3`, then `python`, only after a Python-3 probe succeeds.
- If no verified Python 3 interpreter exists, BLOCK the deterministic operation.
