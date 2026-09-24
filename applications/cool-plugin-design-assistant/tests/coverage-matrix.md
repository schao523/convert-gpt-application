# Cool Plugin Design Assistant coverage matrix

| Requirement | Owner | Structural evidence | Behavior evidence | Status |
| --- | --- | --- | --- | --- |
| INV-001 | `guiding-ai-application-design-sessions` | Skill routing contract and five-phase session reference | BEH-001 clean-context scenario | STATICALLY VERIFIED |
| INV-002 | `guiding-ai-application-design-sessions` | One-question waiting rule in Skill and session reference | BEH-001 clean-context scenario, BEH-011 contract | STATICALLY VERIFIED |
| INV-003 | `guiding-ai-application-design-sessions` | Explicit revise, pause, resume, and stop contract | BEH-007 contract | STATICALLY VERIFIED |
| INV-004 | `guiding-ai-application-design-sessions` | Earliest consequential unresolved-decision rule | BEH-007 contract | STATICALLY VERIFIED |
| INV-005 | `guiding-ai-application-design-sessions` | Four exclusive decision-ledger states | BEH-002 contract | STATICALLY VERIFIED |
| INV-006 | `guiding-ai-application-design-sessions` | Draft/approval and handoff gates | BEH-001 clean-context scenario, BEH-011 contract | STATICALLY VERIFIED |
| INV-007 | `creating-design-statements` | Versioned artifact schema, provenance rule, and specification separation | BEH-003 five-sample clean-context evaluation | STATICALLY VERIFIED |
| INV-008 | `designing-application-workflows-and-instruction-modules` | Workflow, module, interaction, and Workbench-boundary contracts | BEH-006 five-sample clean-context evaluation | STATICALLY VERIFIED |
| INV-009 | Review and testing Skills | Planned input contracts | BEH-009, BEH-010 | EXPECTED |
| INV-010 | `guiding-ai-application-design-sessions` | Session state and decision-ledger ownership | BEH-002 contract | STATICALLY VERIFIED |
| INV-011 | All Skills and validators | Planned evidence contract | BEH-013 | EXPECTED |
| INV-012 | `creating-application-plugin-design-specifications` | Planned handoff gate | BEH-011 | EXPECTED |
| INV-013 | All Skills | Traditional Chinese rules in three implemented Skills; remaining Skills pending | BEH-001 five-sample clean-context evaluation | EXPECTED |
| INV-014 | `guiding-ai-application-design-sessions` | Explicit illegal-or-harmful design refusal | BEH-014 contract | STATICALLY VERIFIED |
| INV-015 | All synthesis Skills | Planned revision points | BEH-003, BEH-007 | EXPECTED |
