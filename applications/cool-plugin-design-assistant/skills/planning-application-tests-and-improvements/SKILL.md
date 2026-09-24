---
name: planning-application-tests-and-improvements
description: Use when an approved AI Application specification needs traceable test scenarios, supplied result assessment, or versioned improvement proposals.
---

# Plan Application Tests and Improvements

Require the approved specification and intended context. Require every explicit
requirement ID. Read [the test-plan contract](references/application-test-plan-contract.md)
and create scenarios with preconditions, inputs, steps, observable results,
evidence state, and result.

Use only EXPECTED, STATICALLY VERIFIED, RUNTIME VERIFIED, or NOT VERIFIED for
evidence. Assess execution only from supplied results. Without explicit
requirement-to-test mappings, report coverage as NOT VERIFIED and name the
missing evidence; never invent a percentage, scenario result, or execution.

When supplied evidence shows a gap, read
[the improvement-patch contract](references/improvement-patch-contract.md) and
propose a versioned, scoped correction with impact and approval state. Do not
silently change the approved specification, implementation, tests, or owner
decisions.

Default to natural Traditional Chinese unless the user requests another
language. Check Traditional character forms before sending.
