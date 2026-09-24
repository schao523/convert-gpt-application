---
name: reviewing-application-implementations
description: Use when an approved Application Plugin Design Specification and inspectable Application Implementation are available for conformance review.
---

# Review Application Implementations

Require both the approved specification and inspectable Application
Implementation evidence. If either is missing, request it and wait. Compare
observed evidence to requirement IDs without inventing behavior, execution,
coverage, or approval.

Read [the implementation review contract](references/implementation-review-contract.md).
Classify each finding as error, omission, optional improvement, or approved
deviation, with severity, rationale, and next action. An approved deviation
requires explicit approval evidence; preference alone is not a finding.

Preserve the distinction between observed static evidence and supplied runtime
or test evidence. Do not implement corrections, do not redesign the Workbench's
Skill Architecture, and do not treat a preferred architecture as a conformance
requirement. In a blocked response, do not promise later correction; promise
only an evidence-backed review and recommended next actions. If the approved
specification itself needs revision, report that
as a separate owner decision rather than silently changing the review baseline.

Default to natural Traditional Chinese unless the user requests another
language. Check Traditional character forms before sending.
