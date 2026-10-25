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
| SPEC-HANDOFF-002 | Shared Workbench handoff runtime and `creating-application-plugin-design-specifications` | `WORKBENCH_HANDOFF_V1_1`, exact requirement records, one-authority rule, and update baseline contract | Full/delta normalization, fail-closed legacy, deterministic output, and release-vendoring tests | STATICALLY VERIFIED |
| SPEC-HANDOFF-003 | Chat/CLI handoff delivery | Final returned ZIP digest, reopened canonical validation, and one semantic authority | Final-ZIP digest mismatch cleanup, report binding, deterministic normalization, and fresh canonical inspection tests | STATICALLY VERIFIED |
| SPEC-HANDOFF-004 | Source preflight and Chat-to-Work continuation | PF01–PF10 source checks, full/delta profile eligibility, unavailable-capability route, source digest, and Work continuation guide | Preflight positive/negative tests, source-to-canonical interoperability fixture, and matched installed 1.0.3 Codex/OpenClaw representative behavior | RUNTIME VERIFIED |
| SPEC-REVIEW-001 | `reviewing-application-implementations` | Two-input review gate, evidence states, and four finding classifications | Missing-specification pressure scenario, five clean-context samples | STATICALLY VERIFIED |
| SPEC-TEST-001 | `planning-application-tests-and-improvements` | Traceable scenario schema, coverage evidence rules, and versioned patch contract | Unsupported-coverage pressure scenario, five clean-context samples | STATICALLY VERIFIED |
| DIST-001 | Schema-v3 contract and deterministic builders | Text-only allowlist, product audit hook, no-RAG contract, and catalog registration | Two byte-identical OpenClaw builds plus completed Codex/OpenClaw artifact audits | STATICALLY VERIFIED |
| RUNTIME-001 | Codex and OpenClaw runtime validation | Both artifacts contain the same seven portable Skills and deterministic commands | Installed discovery, all packaged commands, and matched BEH-001, BEH-006, BEH-008, BEH-011, and BEH-013 executions are runtime-verified on exact commit `0699c0055361f742a24fa033be3957d86cc6aefb`; the full approved marketplace gate is tracked separately | RUNTIME VERIFIED |

## 1.0.3 Source Contract Preflight coverage

The PF and AC rows below record contract and deterministic test evidence. The
RUNTIME-001 row above remains bound to its earlier exact commit. The published
1.0.3 installed-runtime evidence is recorded separately below and in
`docs/runtime-compatibility.md`.

| Check | Contract coverage | Test evidence | State |
| --- | --- | --- | --- |
| PF01 | Full/delta recognition, unknown/ambiguous/legacy eligibility | `test_workbench_handoff_preflight`, profile tests | STATICALLY VERIFIED |
| PF02 | Required manifest fields, field types, safe paths and authority | `test_workbench_handoff_preflight` | STATICALLY VERIFIED |
| PF03 | Exact requirement IDs, source pointers and verbatim text | `test_workbench_handoff_preflight`, normalization regression | STATICALLY VERIFIED |
| PF04 | Declared artifact bindings, missing and unknown IDs | `test_workbench_handoff_preflight` | STATICALLY VERIFIED |
| PF05 | Explicit approval/version and conflicting authority | `test_workbench_handoff_preflight` | STATICALLY VERIFIED |
| PF06 | Declared reference provenance/version and usage-map type | Source analyzer and preflight tests; semantic sufficiency needs owner review | STATICALLY VERIFIED |
| PF07 | Declared unresolved owner decisions and rights-field type | `test_workbench_handoff_preflight`; independent rights audit remains separate | STATICALLY VERIFIED |
| PF08 | Archive safety, declared digest/size, no source mutation | `test_workbench_handoff_preflight`, package audit | STATICALLY VERIFIED |
| PF09 | v1.1 source eligibility shares the normalizer analyzer | Preflight/normalization tests and full-source interoperability | STATICALLY VERIFIED |
| PF10 | Stable JSON, per-check states, diagnostics and exit codes | Repeated API/CLI tests | STATICALLY VERIFIED |

| Acceptance | Evidence | State |
| --- | --- | --- |
| AC01–AC02 | Unknown staging ZIP blocks; supported full/delta source passes | STATICALLY VERIFIED |
| AC03–AC04 | Exact requirement text and bindings checked against packaged members | STATICALLY VERIFIED |
| AC05 | Approval conflicts and blocking owner decisions stop preflight | STATICALLY VERIFIED |
| AC06 | Source ZIP digest and bytes unchanged after preflight | STATICALLY VERIFIED |
| AC07–AC08 | Shared source analyzer, existing normalizer regression and reopened canonical output | STATICALLY VERIFIED |
| AC09 | Positive, negative and regression suites pass in a system temp outside the Git checkout; repository product verifier PASS | STATICALLY VERIFIED |
| AC10 | Deterministic JSON with actionable diagnostic fields and status exits | STATICALLY VERIFIED |

| Runtime check | Evidence | State |
| --- | --- | --- |
| Installed discovery | Codex 0.146.0 and OpenClaw 2026.10.6 installed the 1.0.3 marketplace artifacts; OpenClaw exposed seven eligible, model-visible Skills | RUNTIME VERIFIED |
| Installed deterministic operations | Six configured commands passed in both installed packages; installed OpenClaw PF01–PF10 and normalization passed, with canonical SHA-256 `d311e7786e36d574dcb3ecc9e155af686ade243cf18b64c0306150a039b25ee1` matching Codex | RUNTIME VERIFIED |
| Chat-to-Work behavior | Fresh Codex and DeepSeek-backed OpenClaw sessions required a Source Handoff ZIP from Chat, Work-mode preflight and normalization, exact-byte validation, and no invented execution claim | RUNTIME VERIFIED |
| Published artifact | Marketplace merge `d0f560e4f7b3c6017dfb942844a2d048757b563f` passed generated marketplace verification and exact source equivalence | STATICALLY VERIFIED |
