# Reference Material Usage Map contract

The map recommends where approved knowledge supports application behavior. It
does not choose how a runtime stores, retrieves, loads, packages, or binds the
material.

Create one row for each materially distinct use with these fields:

| Field | Meaning |
| --- | --- |
| `material_id` | Stable identifier matching the evaluation inventory. |
| `knowledge_supplied` | Specific knowledge element, not merely a filename or broad topic. |
| `supported_behavior` | Named workflow, Instruction Module, decision, or output. |
| `stage_or_triggering_intent` | Workflow stage or recognizable intent where consultation occurs. |
| `necessity` | `required` or `optional`, with consequence when unavailable. |
| `consultation_condition` | Exact condition that causes the knowledge to be used. |
| `authority_and_provenance` | Verified authority/provenance facts and unresolved claims. |
| `use_mode` | `exact-quotation`, `exact-structured-retrieval`, or `advisory`. |
| `limitations_and_conflicts` | Scope limits, conflicts, duplication, staleness, and uncertainty. |
| `rights_decision` | Applicable confirmed, unresolved, or prohibited rights for this use. |

Recommend the narrowest behavioral location that explains why the knowledge is
needed. A source may support several rows when different knowledge elements are
used at different stages. Several sources may support one behavior; preserve
their distinct authority, conflicts, and fallback consequences.

The Application Workbench alone decides canonical filenames, Skill bindings,
packaged paths, loading routes, structured indexes, RAG use, vector technology,
and runtime storage. Carry behavior-level need, exactness, rights, and fallback
requirements into the handoff without prescribing those implementation choices.
