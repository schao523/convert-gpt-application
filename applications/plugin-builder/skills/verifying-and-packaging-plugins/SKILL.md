---
name: verifying-and-packaging-plugins
description: Verify a Plugin Builder candidate, report evidence honestly, enforce W2, and create a deterministic ZIP for manual upload.
---

# Verifying and packaging plugins

Verify the candidate against every approved requirement and the declared structural, dependency, safety, and behavior checks. Read [the evidence and package contract](references/evidence-and-package-contract.md) before classifying results or creating an artifact.

For executable, runtime-native, framework, and MCP-backed capabilities, apply [the tool evidence contract](references/tool-evidence-contract.md). Never convert an unavailable runtime or missing authorization into a passing check.

Treat BUILD_HOST_LOCAL_MCP as local operation evidence only. The installed Skill invocation, capability discovery, result delivery, and behavior layers require digest-closed `runtime-result-v3` evidence for the exact artifact, runtime, and channel. Keep approved `DEFERRED_ALLOWED` gaps visible; enforce `REQUIRED_BEFORE_W2` at W2.

Distinguish expected behavior, static evidence, directly observed runtime evidence, and work not executed. A zero exit code alone is not proof of a valid artifact. Any required failure blocks packaging; repair and rerun when authorized, otherwise return the failure without a ZIP.

Present the exact delta, results, unexecuted checks, and limitations for W2. Package only after explicit W2 approval. Build deterministically, inspect the generated ZIP independently, and return it for manual upload. Do not mutate a marketplace, release, account, or external registry without separate authorization.

Run `verify`, present its plain-language evidence summary, record explicit owner acceptance with `approve-w2`, and only then run `package`.
