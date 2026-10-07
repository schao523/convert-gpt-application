# Tool evidence contract

Verify each declared application tool independently and preserve its contract hash, fixture hash, requirement bindings, skill bindings, implementation kind, execution state, and diagnostics in the W2 report.

## Command evidence

| Key | Outcome |
| --- | --- |
| DECLARED_ARGV | PRESERVE_EXACTLY |
| OBSERVED_ARGV | RECORD_ACTUAL_EXECUTION |
| ADAPTER | EXPLICIT_OR_NULL |

For `BUNDLED_LOCAL` and `FRAMEWORK_ADAPTER`, execute only an approved direct argument vector with `shell=false`, a bounded timeout, a clean environment, and network disabled unless separately authorized. Record return state plus SHA-256 digests of stdout and stderr; do not embed potentially sensitive process output.

For `RUNTIME_NATIVE` and `MCP_ADAPTER`, report `NOT VERIFIED` when the target capability, user configuration, credentials, or authorized service connection is unavailable. Never synthesize a runtime pass from static configuration.

A required tool with a blocking fallback must pass before W2 can be approved or a ZIP emitted. An approved optional tool may remain `NOT VERIFIED` when the owning requirement has other passing required evidence, but its limitation must remain visible through W2 and packaging.
