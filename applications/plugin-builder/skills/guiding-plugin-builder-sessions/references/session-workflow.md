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

The successful path is intake → planning → W1 → candidate build/update → verification → W2 → deterministic packaging → manual return. No alternate success path may omit W1 or W2.

Required inputs missing at intake produce a wait state. A required validation failure produces a repair-or-stop state. Cancellation is terminal for the active session and does not imply deletion of user inputs.
