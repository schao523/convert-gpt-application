# T8 — approved MCP operation and installed realization

Use the exact reviewed Plugin Builder installation ZIP and the generated `t8-local-mcp-plan.json` in a fresh Codex or ChatGPT Work Local/Desktop task. Do not use repository code, inherit developer `PYTHONPATH`, contact an unapproved service, or install credentials.

## Build-host operation check

Inspect the approved sample handoff, compile the T8 proposal, and obtain explicit W1 for its exact hash. Build the candidate. The proposal declares a small deterministic `normalize-input` operation and a direct-argv loopback MCP test server. Run the local verifier only with explicit `allow_loopback=True`. Check initialize, `tools/list`, invalid-input rejection, valid structured output, bounded timeout, and process cleanup. Record the local result as `BUILD_HOST_LOCAL_MCP`; do not label any installed layer `RUNTIME VERIFIED` from this result.

The generated T8 proposal also contains remote HTTPS MCP configuration as a separate installed realization. The local loopback fixture does not prove that endpoint is deployed, authorized, reachable, or invoked by an installed Skill. If the approved candidate cannot pass W2, do not force a ZIP or waive the failure.

## Installed Skill-to-result check

Only if a separately approved and configured installed plugin exposes the exact capability, invoke the owning Skill in the named runtime and observe its call to `normalize-input`, deterministic result, delivery back to the Skill, and resulting behavior. Record the exact installed ZIP SHA-256, member-manifest SHA-256, plugin version, runtime version, OS, and `OPENAI_PORTABLE_PLUGIN` channel. Keep sanitized input and structured output as digests, not raw private payloads. Store each observation under its SHA-256 filename.

Use `runtime-result-v3-schema.json` and `runtime-result-v3-template.json`; complete all T1–T8 rows. The `operation_execution.environment` is `INSTALLED_RUNTIME` only for directly observed installed execution. For a local-only T8 run, leave installation, Skill invocation, capability discovery, result delivery, and Skill behavior `NOT VERIFIED`, and keep overall state `NOT VERIFIED`. Package the completed result with `plugin_builder.py package-runtime-evidence`; a missing or mismatched layer digest blocks the bundle. Return the validated JSON and digest-addressed ZIP without publishing anything.
