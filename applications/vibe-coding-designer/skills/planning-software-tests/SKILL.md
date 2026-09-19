---
name: planning-software-tests
description: Use when converting software requirements and acceptance criteria into traceable unit, integration, contract, workflow, security, usability, performance, or end-to-end test scenarios.
---

# Plan Software Tests

Build a test plan from explicit requirement and acceptance identifiers. Read [references/test-plan-contract.md](references/test-plan-contract.md). Match test layers to the software form: command/exit-code tests for CLI, public-API compatibility for libraries, trigger/retry/idempotency tests for workers, endpoint contracts for services, and interaction/accessibility tests for GUIs.

Each scenario names its requirement, preconditions, inputs, steps, expected observable result, failure behavior, level, and automation status. Include normal, boundary, invalid, authorization, dependency-failure, and recovery cases when applicable.

Do not invent a coverage percentage. Calculate requirement coverage only from an explicit machine-readable mapping; otherwise report coverage as `NOT VERIFIED` and list missing evidence.
