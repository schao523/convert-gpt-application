# Requirement coverage contract

Create one row per approved requirement with these fields:

| Field | Meaning |
| --- | --- |
| requirement_id | Stable ID from the approved design |
| behavior | Preserved observable outcome |
| implementation_owner | Skill, reference, deterministic contract, or adapter |
| evidence_target | Specific static check, scenario, or runtime observation |
| evidence_state | Current honest state |
| notes | Constraint, dependency, or unresolved decision |

Do not merge IDs, omit inconvenient requirements, or count a reference link as behavior evidence. Use `EXPECTED` for a defined future outcome, `STATICALLY VERIFIED` for inspected structure/content, `RUNTIME VERIFIED` only for directly observed execution, and `NOT VERIFIED` when no applicable test ran. Runtime exclusions are recorded separately as `NOT APPLICABLE`.

Each implementation owner must trace back to at least one requirement, and every required dependency must have an availability/rights decision before packaging.
