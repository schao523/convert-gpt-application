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

## Runtime realization evidence

Separate `operation_execution` from each target's installed `runtime_realization`. A passing direct-argv or `BUILD_HOST_LOCAL_MCP` check proves only the named build-host operation. It never proves installed Skill invocation, capability discovery, result delivery, or Skill behavior. An approved behavior-preserving fallback may satisfy its preserved requirement IDs only when the alternative operation actually passes; retain the primary tool's observed state and record the activation.

For installed claims, use `runtime-result-v3` with the exact ZIP/member-manifest identity, target runtime, installation channel, tool/operation/adapter/capability IDs, and digest-addressed evidence for structural validation, installation, Skill invocation, capability discovery, operation execution, result delivery, and Skill behavior. A realization is `RUNTIME VERIFIED` only when all seven layers and the structured result are directly observed and their digests validate. `DEFERRED_ALLOWED` remains `NOT VERIFIED` in W2/package metadata until then; `REQUIRED_BEFORE_W2` blocks W2. Older v1/v2 results remain historical and cannot close this gate.
