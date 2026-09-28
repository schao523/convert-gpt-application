# Runtime compatibility evidence

Phase-one runtime scope is `OPENAI_ONLY_PHASE_ONE`.

| Runtime | Evidence state | Environment identity |
| --- | --- | --- |
| Codex | RUNTIME VERIFIED | Codex Desktop local projectless task; codex-cli 0.146.0 |
| ChatGPT Work Local/Desktop | RUNTIME VERIFIED | User-confirmed native local execution; returned artifact independently inspected |
| OpenClaw | NOT APPLICABLE | Explicitly excluded from phase one |
| Claude | NOT APPLICABLE | Explicitly excluded from phase one |

## Feasibility capabilities

| Capability | Codex | ChatGPT Work Local/Desktop |
| --- | --- | --- |
| Read the approved normalized package | PASS | PASS |
| Create an isolated workspace | PASS | PASS |
| Write a minimal plugin | PASS | PASS |
| Execute the bundled deterministic validator | PASS | PASS |
| Generate and return a ZIP | PASS | PASS |

Both returned ZIPs were independently checked for their reported SHA-256, exact member closure, safe paths, valid manifest, embedded PASS result, approved input identity, and absence of Workbench imports. This evidence proves required runtime primitives only; it does not prove the Plugin Builder acceptance scenarios end to end.

No marketplace installation, publication, or release is authorized or recorded for Plugin Builder.
