# Test-plan contract

For every scenario record:

- stable test ID and title;
- requirement and acceptance IDs;
- test level and execution boundary;
- preconditions and fixture identity;
- inputs and ordered actions;
- expected outputs, state changes, errors, logs, or other evidence;
- determinism controls and cleanup;
- automation state: planned, implemented, passing, failing, or not verified.

Maintain two-way traceability: every implementation-relevant requirement maps to at least one test, and every test maps to a requirement, acceptance criterion, or justified technical prerequisite.

Coverage percentage is `covered distinct requirements / all explicit distinct requirements × 100`, rounded to two decimals. A requirement is covered only when at least one declared test references its exact ID. This measures mapped requirements, not executed pass rate or code coverage.
