---
name: building-and-updating-plugins
description: Create or update a local plugin candidate after W1 approval while preserving baseline content and enforcing archive/workspace safety.
---

# Building and updating plugins

Require recorded W1 approval and an explicit `CREATE` or `UPDATE` mode before any mutation. Read [the candidate and update contract](references/candidate-and-update-contract.md) before creating the isolated workspace or handling an archive.

In create mode, implement only the approved plan. In update mode, inventory the baseline first, preserve unaffected content, and stop for an explicit decision on every unexplained member. Never delete, overwrite, or reinterpret existing behavior merely because the new specification is silent.

Reject traversal, duplicate logical paths, case-fold collisions, escaping links, absolute persisted paths, and writes outside the isolated workspace. Keep provider, credential, account, and machine-specific details outside portable skill logic.

Return a candidate directory and change inventory for verification. Do not create the final ZIP; packaging belongs after verification and W2 approval.
