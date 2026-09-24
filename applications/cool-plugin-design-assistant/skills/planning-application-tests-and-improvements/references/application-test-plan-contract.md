# Application test plan contract

## Required inputs

- approved specification identifier, version, and approval evidence;
- intended user, context, runtime scope, and material constraints;
- explicit requirement IDs with acceptance criteria; and
- when assessing execution, caller-supplied results with provenance.

If the specification or requirement IDs are missing, test design and coverage
are `NOT VERIFIED`; request the missing inputs. A representative scenario can
be proposed only against an explicit requirement, not an inferred preference.

## Scenario record

Every scenario contains:

| Field | Meaning |
| --- | --- |
| `test_id` | Stable identifier. |
| `requirement_ids` | One or more explicit approved requirement IDs. |
| `preconditions` | Required state, configuration, actors, and evidence setup. |
| `input` | Exact request, data, event, or artifact supplied. |
| `steps` | Reproducible actions without hidden decisions. |
| `observable_result` | User-visible or machine-observable success/failure boundary. |
| `evidence_state` | One approved evidence state below. |
| `result` | `PASS`, `FAIL`, `NOT VERIFIED`, or `NOT APPLICABLE` for the layer evaluated. |

Use evidence states precisely:

- `EXPECTED` — specified behavior with no direct inspection or execution;
- `STATICALLY VERIFIED` — directly supported by inspectable static artifacts;
- `RUNTIME VERIFIED` — directly supported by supplied, attributable execution
  evidence for the stated environment; or
- `NOT VERIFIED` — evidence is missing, insufficient, inaccessible, or does not
  evaluate the claimed layer.

Planned scenarios are `EXPECTED`, not `RUNTIME VERIFIED`. Static inspection is
not execution. A caller's summary may be assessed as supplied evidence, but its
provenance and limits must stay visible.

## Coverage reporting

Create a requirement-to-test matrix before reporting coverage. Distinguish
scenario coverage, executed-result coverage, invariant coverage, and target
runtime coverage. A percentage requires an explicit denominator, mapped
requirements, applicability decisions, and attributable results for the layer
claimed. Otherwise state `NOT VERIFIED` and list the missing mapping or evidence.

Never infer `PASS` from test existence, process exit code alone, installation,
discovery, or another runtime's result.
