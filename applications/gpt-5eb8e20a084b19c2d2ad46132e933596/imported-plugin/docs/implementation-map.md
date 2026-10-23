# Implementation Map

This document records technical bindings only. The approved specification Section 13 remains the canonical behavior-level reference mapping authority. The approved delta v1.0-delta-01 clarifies that **specific workflow-stage or trigger-condition mappings govern activation**; module-level dependency summaries do not make conditional references universally required. Technical placement below does not change those behavior-level mappings.

| Skill | Primary behavior ownership | Key technical reference bindings |
|---|---|---|
| pedagogy-orchestrator | IM-01; coordination of IM-02/09/10; workflow state; forward skip | RM-01; RM-14 metadata |
| course-design | WF-01; IM-03 | RM-01/02/03; RM-04-New via integrity skill when capability routing triggers; prompt references only on trigger |
| ai-practice-design | WF-02; IM-04 | RM-01 required; RM-06 only when generating/reviewing/materially revising an AI-facing Teaching Prompt; RM-04-New via integrity skill on capability routing |
| course-content-generation | WF-03; IM-05 | RM-01/05; RM-04-New via integrity skill on capability routing; RM-06/11/12 only on trigger |
| application-practice-design | WF-04; IM-06 | RM-01/07/08/09; RM-10 optional; RM-04-New via integrity skill on capability routing; prompt references only on trigger |
| teaching-prompt-design | IM-07 | RM-01/06; RM-11/12 conditional |
| thinking-first-reference-integrity | IM-08/09/10 | RM-04-New + active inventory for grounding; RM-04-Legacy provenance only |

## Capability decisions

- Workflow state: bundled in conversation/session behavioral context.
- Structured artifact generation: reuse model/runtime capability.
- External application routing: capability-first adaptation governed by RM-04-New.
- No RAG, MCP, external database, external account, or network dependency is required for approved behavior.
