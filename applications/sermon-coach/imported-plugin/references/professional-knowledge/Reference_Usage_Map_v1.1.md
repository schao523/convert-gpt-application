# Reference Material Usage Map v1.1

Application: 講章優化教練  
State: APPROVED — Phase 2

| Material ID | Knowledge supplied | Supported behavior | Stage / triggering intent | Necessity | Consultation condition | Use mode | Limitations / precedence |
|---|---|---|---|---|---|---|---|
| RM-01 | Existing role, workflows, tone, triggers, boundaries | WF-01–WF-04; IM-01–IM-10 | Migration/design normalization | required | When preserving inherited GPT behavior | behavioral baseline | Normalized behavior governs; not a theological source |
| RM-02 | Vertical/horizontal/cross-point integration | IM-02 | Theology/exegesis review | required | Sermon review includes theological focus | advisory | Does not override Scripture or RM-04 |
| RM-02 | Structural integration | IM-03 | Structure review | required | Reviewing unity, flow, opening/body/conclusion | advisory | Use as homiletical lens |
| RM-02 | Emotional/applied integration | IM-04 | Application and audience | required | Evaluating truth entering lived context | advisory | Use as homiletical lens |
| RM-02 | Four-dimension integration | IM-07 | Integrated evaluation | required | Producing overall sermon assessment | advisory | No verbatim book quotation |
| RM-03 | Purpose/theme/call to action | IM-03 | Structure review | required | Reviewing focus, opening/body/landing | advisory | Does not determine exegesis |
| RM-03 | Stories, rhetoric, passion, delivery, memorability | IM-05 | Expression review | required | Reviewing engagement, rhetoric, emotional resonance | advisory | No verbatim book quotation |
| RM-03 | Memorability and closure | IM-07 | Priority guidance | optional | When final recommendations include expression/memory issues | advisory | Only when relevant |
| RM-04-SOURCE | Canonical ten-step method | IM-02 | Exegetical review | required | Sermon makes interpretive or application claims from a passage | advisory/source authority | Governs RM-04A–E on conflict |
| RM-04-SOURCE | Canonical ten-step method | IM-10 | Full inductive study | required | User requests full inductive study | advisory/source authority | Must preserve sequence and distinctions |
| RM-04A | Method orientation and ten-step map | IM-01 | Route to inductive mode | required | User requests Bible study or exegesis workflow | advisory | Derivative of RM-04-SOURCE |
| RM-04A | Observation→interpretation→application model | IM-02 | Exegesis review | required | Assessing whether sermon interpretation follows a valid progression | advisory | Derivative |
| RM-04B | 17 observation categories | IM-10 | Steps 1–3 | required | Full inductive study enters observation | advisory | Ask selectively, not all at once |
| RM-04B | Relationship/structure criteria | IM-02 | Scripture review | required | Sermon depends on textual relationship/structure | advisory | Distinguish observation from interpretation |
| RM-04C | Three question types | IM-10 | Step 4 | required | Full study enters question formation | advisory | Questions must emerge from passage |
| RM-04C | Interpretive principles | IM-02 | Exegesis review | required | Evaluating explanation of Scripture | advisory | General knowledge may not silently replace |
| RM-04C | Synthesis and theme | IM-10 | Steps 6–7 | required | Moving from answers to total meaning/theme | advisory | Theme must be a complete theological proposition |
| RM-04D | Principle as bridge from interpretation to application | IM-04 | Application review | required | Sermon applies ancient text to modern hearers | advisory | Flag direct jumps that bypass principle |
| RM-04D | Cultural-gap and whole-Bible checks | IM-10 | Step 8 | required | Deriving theological principle | advisory | Preserve source tests |
| RM-04D | SMART and concrete action | IM-10 | Step 9 | required | Turning principle into practice | advisory | Keep application faithful to passage |
| RM-04D | Embodiment/reminder/accountability | IM-10 | Step 10 | required | Completing full inductive study | advisory | User owns response |
| RM-04E | Step-aligned coaching questions | IM-10 | Full inductive interactive mode | required | AI is guiding rather than merely explaining | advisory | RM-04-SOURCE governs any conflict |
| RM-05 | Exact Old Testament CUV text | IM-02 | OT sermon passage review | required | Sermon cites/interprets OT text | exact-structured-retrieval / exact quotation | Verify verse reference |
| RM-05 | Exact Old Testament CUV text | IM-10 | OT Bible study | required | Study passage is OT | exact-structured-retrieval / exact quotation | Do not invent missing wording |
| RM-06 | Exact New Testament CUV text | IM-02 | NT sermon passage review | required | Sermon cites/interprets NT text | exact-structured-retrieval / exact quotation | Verify verse reference |
| RM-06 | Exact New Testament CUV text | IM-10 | NT Bible study | required | Study passage is NT | exact-structured-retrieval / exact quotation | Do not invent missing wording |

## Fallback behavior

- If RM-02 or RM-03 is temporarily unavailable, the affected homiletical dimension must be marked as limited rather than silently substituted.
- If RM-04A–E is unavailable but RM-04-SOURCE is available, consult the source PDF directly.
- If RM-04-SOURCE is unavailable, do not claim to be following the supplied full inductive method.
- If the relevant Bible text source is unavailable, do not fabricate exact CUV wording.
- Model knowledge may provide clearly labeled supplementary explanation only after required reference use has been satisfied or its absence disclosed.

## Workbench boundary

This map defines **where and why** knowledge must be consulted. It does not prescribe:
- Skill count or names;
- file paths;
- RAG/vector technology;
- loading architecture;
- runtime storage;
- adapters;
- reference-to-Skill bindings.

Those implementation choices belong to the Application Workbench.
