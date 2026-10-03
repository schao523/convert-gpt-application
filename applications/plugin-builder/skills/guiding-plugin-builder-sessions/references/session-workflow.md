# Session workflow

## Routing contract

| Key | Outcome |
| --- | --- |
| CREATE | PLAN |
| UPDATE | REQUIRE_BASELINE_THEN_PLAN |
| PAUSE | H1_PAUSED |
| RESUME | RESTORE_AND_SUMMARIZE |
| CANCEL | E2_CANCELLED |

Inspection and validation requests report current state without advancing it. A revision at W1 returns to planning; a non-behavioral revision at W2 returns to the affected plan or build stage. A behavioral revision always returns for a newly approved specification.

## Gate contract

| Key | Outcome |
| --- | --- |
| W1 | BLOCK_MUTATION_UNTIL_APPROVED |
| W2 | BLOCK_PACKAGING_UNTIL_APPROVED |

## CLI routing

Use `inspect` to create a v2 session, `pause` and `resume` to preserve the current stage, and `cancel` to enter `E2`. Route planning, building, verification, and packaging to their owning skills; never reproduce those mutations by editing session JSON.

`inspect` records exactly one of seven profiles. `WORKBENCH_HANDOFF_V1_1` is the shared canonical Design Assistant-to-Builder contract. `CANONICAL_V1` is retained canonical compatibility input. `LEGACY_WORKBENCH_V1`, `COOL_DESIGN_ASSISTANT_FULL_V1`, and `COOL_DESIGN_ASSISTANT_DELTA_V1` use narrow legacy adaptation that may emit validated canonical sidecars while preserving approved source bytes. `UNKNOWN` asks for one supported handoff authority. `AMBIGUOUS` lists the conflicting authorities and does not select one. Normalization is format-only intake work: it neither authorizes candidate mutation nor replaces W1.

Canonical v1.1 create input advances only after semantic and physical validation succeeds. Canonical v1.1 update input also requires a separately supplied baseline ZIP whose plugin identity, version, and exact archive SHA-256 match the approved handoff. Failure remains at F1; Plugin Builder never chooses among authorities or repairs approval evidence implicitly.

The successful path is intake → planning → W1 → candidate build/update → verification → W2 → deterministic packaging → manual return. No alternate success path may omit W1 or W2.

Required inputs missing at intake produce a wait state. A required validation failure produces a repair-or-stop state. Cancellation is terminal for the active session and does not imply deletion of user inputs.
