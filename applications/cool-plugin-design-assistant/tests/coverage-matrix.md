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
| INV-009 | Review and testing Skills | Approved-specification and inspectable/supplied-evidence gates in both post-Workbench Skills | BEH-009 and BEH-010 five-sample clean-context evaluations | STATICALLY VERIFIED |
| INV-010 | `guiding-ai-application-design-sessions` | Session state and decision-ledger ownership | BEH-002 contract | STATICALLY VERIFIED |
| INV-011 | All Skills and validators | Reference, specification, review, test, launcher, and distribution contracts require explicit evidence states and prohibit invented rights or execution evidence | BEH-013 contracts plus parsed verifier and artifact-audit results | STATICALLY VERIFIED |
| INV-012 | `creating-application-plugin-design-specifications` | Complete-version approval gate and blocked/ready handoff states | BEH-011 five-sample clean-context evaluation | STATICALLY VERIFIED |
| INV-013 | All Skills | Traditional Chinese rule present in all seven Skills | BEH-001 five-sample clean-context evaluation | STATICALLY VERIFIED |
| INV-014 | `guiding-ai-application-design-sessions` | Explicit illegal-or-harmful design refusal | BEH-014 contract | STATICALLY VERIFIED |
| INV-015 | All synthesis Skills | Planned revision points | BEH-003, BEH-007 | EXPECTED |
| SPEC-REF-001 | `evaluating-reference-materials` | Evaluation inventory and behavior-level usage-map contracts with Workbench binding boundary | Reference pressure scenario, five clean-context samples | STATICALLY VERIFIED |
| SPEC-HANDOFF-001 | `creating-application-plugin-design-specifications` | Ordered 21-section specification and Workbench-reserved decision contract | Premature-handoff pressure scenario, five clean-context samples | STATICALLY VERIFIED |
| SPEC-REVIEW-001 | `reviewing-application-implementations` | Two-input review gate, evidence states, and four finding classifications | Missing-specification pressure scenario, five clean-context samples | STATICALLY VERIFIED |
| SPEC-TEST-001 | `planning-application-tests-and-improvements` | Traceable scenario schema, coverage evidence rules, and versioned patch contract | Unsupported-coverage pressure scenario, five clean-context samples | STATICALLY VERIFIED |
| DIST-001 | Schema-v3 contract and deterministic builders | Text-only allowlist, product audit hook, no-RAG contract, and catalog registration | Two byte-identical OpenClaw builds plus completed Codex/OpenClaw artifact audits | STATICALLY VERIFIED |
| RUNTIME-001 | Codex and OpenClaw runtime validation | Both artifacts contain the same seven portable Skills and deterministic commands | Codex and OpenClaw installed discovery, packaged commands, matched missing-outcome conversations, and cross-runtime comparison | RUNTIME VERIFIED |
