# Application tool contract

Application-oriented tools are explicit implementation units, never an implicit edge case. Every tool must identify its requirement owners, skill bindings, files, input and output schemas, side effects, permissions, runtime targets, dependencies, configuration, fallback, verification, redistribution evidence, and W1-bound contract hash.

## Implementation kinds

| Kind | Use |
| --- | --- |
| `BUNDLED_LOCAL` | Product-owned deterministic code shipped in the candidate. |
| `FRAMEWORK_ADAPTER` | Thin application binding to an approved portable framework interface. |
| `RUNTIME_NATIVE` | Capability supplied by a declared target runtime. |
| `MCP_ADAPTER` | Configuration and binding for an external MCP service boundary. |
| `UNRESOLVED` | Required design decision is missing; block W1 or build. |

Bundle no credentials. Keep authentication owner-configured, declare network and workspace permissions, and provide a behavior-preserving fallback only when the approved specification permits one. Tool files and bindings are part of the W1 identity; changing them requires renewed approval.

Local and framework tools use direct argument vectors, bounded execution, clean environments, and declared fixtures. Runtime-native and MCP tools require runtime evidence and must not be represented as locally executed when the capability or authorization is absent.

Application-tool v2 binds `capability_ids`, a schema-hashed operation, and one realization per declared target runtime. A realization names its adapter version, exposed capability, operation, dependency IDs, permission IDs, setup owner, feasibility state, and `DEFERRED_ALLOWED` or `REQUIRED_BEFORE_W2` evidence policy. Validate the target-aware adapter registry before W1. For `FEASIBLE_WITH_SETUP`, the setup contract must be complete; do not infer permission or dependency availability.

Generate `mcp.json` and the `.mcp.json` compatibility projection only from approved remote HTTPS MCP records. Never fabricate a local MCP server or endpoint because a tool is labeled `MCP_ADAPTER`. A W1-approved local MCP test command may exercise the deterministic operation over loopback, but the installed Skill-to-capability path remains unverified until directly observed.
