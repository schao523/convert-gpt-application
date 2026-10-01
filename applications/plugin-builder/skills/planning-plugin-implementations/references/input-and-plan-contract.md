# Input and plan contract

## Planning contract

| Key | Outcome |
| --- | --- |
| INPUT_AUTHORITY | APPROVED_SPEC_REQUIRED |
| OUTPUT | REQUIREMENT_COVERAGE_PLAN |
| BEHAVIOR_CHANGE | RETURN_FOR_NEW_APPROVAL |

Run `plan` only from a valid inspected session. Classify each application capability as bundled local, framework adapter, runtime native, MCP adapter, or unresolved; include permissions, configuration, fallback, files, bindings, fixtures, and evidence targets. Present these decisions at W1 and use `approve-w1` only after explicit owner confirmation.

Handoff normalization does not establish approval. Plan only when the canonical handoff records sufficient explicit approval evidence; a filename containing `APPROVED`, a generated sidecar, or a successful format conversion is not planning authority.

The plan identifies each behavioral requirement, application invariant, skill owner, reference need, deterministic operation, dependency, runtime adapter, acceptance scenario, and unresolved decision. An existing plugin ZIP is mandatory for update mode; store only its digest and a relative workspace identity.

Evaluate available framework and creator capabilities before proposing new code. Record one decision for each required capability: `REUSE`, `ADAPT`, `BUNDLE`, or `UNRESOLVED`, plus the inspected evidence. Do not replace required retrieval or deterministic processing with model memory.

The W1 review package is plain language: intended skill responsibilities, reused or bundled capabilities, planned files, requirement coverage, risks, and decisions still needed. It is not permission to publish or deploy.
