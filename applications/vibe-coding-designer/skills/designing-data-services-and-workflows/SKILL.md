---
name: designing-data-services-and-workflows
description: Use when software design requires precise data models, persistence decisions, API or tool contracts, external-service bindings, state transitions, retries, or compensation behavior.
---

# Design Data, Services, and Workflows

Define contracts that an implementation agent can follow without guessing. Start from confirmed requirements and select only the necessary layers; explicitly state when persistence, a backend, or an integration is not needed.

For data and service patterns, read [references/data-and-service-contracts.md](references/data-and-service-contracts.md). For a multi-step or failure-sensitive process, read [references/workflow-execution-map.md](references/workflow-execution-map.md) and emit JSON so the bundled validator can check identifiers and graph integrity. YAML may accompany the JSON for presentation, but JSON is canonical.

Validate the final workflow with the packaged deterministic tool when it is
available. If it is not available, perform the reference's equivalent
shape-and-graph self-check and report the workflow as `NOT VERIFIED` if any
check cannot be completed.

Separate internal components from external services. Define validation, authorization expectations, errors, timeouts, idempotency, retries, and compensation in the contract rather than relying on an example stack. Never include credentials; identify secrets by logical environment-variable name only.

All output is non-executable design material. Do not call live services or create a production database.
