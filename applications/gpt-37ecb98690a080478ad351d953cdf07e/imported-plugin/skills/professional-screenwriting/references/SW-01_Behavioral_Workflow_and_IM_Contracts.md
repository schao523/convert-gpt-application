# SW-01 Behavioral Workflow Blueprint, Instruction Module Contracts & User Protocols
**Version:** v0.3.2 RIC-01 DRAFT | **Owner approval:** pending | **Type:** behavioral specification only; **not a deployable Skill architecture**.

## A. WF-SW-PRO — Professional Screenwriting (FDR-01 guard-corrected)

**Mission outcome:** an exact, owner-approved screenplay revision becomes a traceable storyboard-ready **draft** without waiving the existing Director Project or external-production gates. **Actors:** creator/owner; Director assistant. **Required inputs:** intent, chosen `PRO` route, story/source. **Optional:** genre, audience, language, timing, constraints, source passage/rights, prior script.

**Start:** `P0` | **Terminals:** `P-DONE`, `P-STOP`, `P-DECLINE` | **Success:** `P-DONE`. **Mandatory successful-path HITL:** `P7`, with exact-revision approval. A storyboard bridge can never be entered from a saved/retry stage directly. All successful paths include `P7` and `P8`. Existing Director Project approval occurs **after** `P-DONE` and remains separate.

### Transition table — formally guarded

Each row has a state `id`, `kind` (start/action/wait/failure/end), named protocol, wait flag, and transitions. A condition is required **before** its arrow is eligible. Any invalid request is rejected with the same canonical script left unchanged. `PF` is the only failure-kind state and the target of literal `failure` transitions.

| ID | Kind | Protocol | Wait? | Guarded transitions → target / effect |
|---|---|---|---|---|
| P0 | start | UIP-SW-01 | no | `pro_selected`→P1 / record route; `stop`→P-STOP |
| P1 | action | UIP-SW-01 | no | `brief_ready_or_provisional`→P2 / persist source + assumptions; `imported_existing_script_for_pro_bridge`→P5 / preserve imported script ID/revision and source-rights status, **do not generate/rewrite script**; `failure`→PF / record failed state P1 |
| P2 | action | UIP-SW-02 | no | `architect_requested`→P3; `fast_draft_explicit`→P4 / mark provisional and `beat_lineage_mode=SCRIPT_DERIVED_PENDING`; `pause`→PP / save stage P2; `failure`→PF / record stage |
| P3 | action | UIP-SW-02 | no | `beat_sheet_ready`→P4 / persist current draft beat revision; `material_choice_open`→P3W; `failure`→PF |
| P3W | wait | UIP-SW-02 | yes | `creative_choice_confirmed`→P3C / record owner choice; `revise_outline`→P3; `pause`→PP; `stop`→P-STOP |
| P3C | action | UIP-SW-02 | no | `beat_sheet_revised_to_match_choice`→P4 / **new** beat-sheet revision + choice reference + required source-consistency check; `failure`→PF |
| P4 | action | UIP-SW-04 | no | `script_draft_recorded`→P5 / stable screenplay ID + exact revision; `pause`→PP; `failure`→PF |
| P5 | action | UIP-SW-03 | no | `critique_recorded_with_gates`→P6 / blocking finding requires proposed remedies; `critique_recorded_no_blocker`→P7 / include unresolved non-hard issues; `failure`→PF; `pause`→PP |
| P6 | action | UIP-SW-04 | no | `proposals_ready`→P6W / keep source unchanged; `no_edit_owner_selected_and_no_unresolved_hard_block`→P7; `failure`→PF |
| P6W | wait | UIP-SW-04 | yes | `owner_accepts_proposal_without_apply`→P6W / save `ACCEPTED_NOT_APPLIED`, may pause/stop; `owner_authorizes_exact_apply`→P6A / exact source + change/scope recorded; `reject_or_defer_no_hard_block`→P7 / source unchanged; `request_alternative`→P6; `pause`→PP; `stop`→P-STOP |
| P6A | action | UIP-SW-04 | no | `authorized_diff_applied_to_new_draft`→P6V / `APPLIED_UNVERIFIED`, preserve original; `failure`→PF |
| P6V | action | UIP-SW-03 | no | `before_after_and_dependency_checks_recorded`→P5 / keep findings, five-state dispositions, regression checks and independent change status; `failure`→PF / block handoff, preserve versions |
| P7 | wait | UIP-SW-05 | yes | `approve_exact_revision_and_all_bridge_guards_pass`→P8 / persist owner approval proof; `hard_gate_block_or_required_check_missing`→P6 / **no** approval issued; `revise`→P6; `decline`→P-DECLINE; `pause`→PP; `stop`→P-STOP |
| P8 | action | UIP-SW-05 | no | `bridge_guards_still_pass_and_mapping_complete`→P-DONE / storyboard DRAFT + traceable map; `guard_fails`→P7 / require revalidation and renewed exact approval if changed; `failure`→PF / preserve approved script; `pause`→PP / save stage P8 |
| PF | failure | UIP-SW-06 | yes | `retry_recorded_stage_before_approval`→P1/P2/P3/P4/P5/P6/P6V **only as saved and guard-valid**; `bridge_failure_recovery`→P7 / **never directly P8**, revalidate owner/source; `clarify_source`→P1; `pause`→PP; `stop`→P-STOP |
| PP | wait | UIP-SW-06 | yes | `resume_saved_preapproval_stage`→P1/P2/P3/P3W/P3C/P4/P5/P6/P6W/P6A/P6V **only as saved and guard-valid**; `resume_saved_P7_or_P8`→P7 / **never directly P8**, recheck exact revision and approval validity; `stop`→P-STOP |
| P-DONE | end | UIP-SW-05 | no | `{}` |
| P-DECLINE | end | UIP-SW-06 | no | `{}` |
| P-STOP | end | UIP-SW-06 | no | `{}` |

**P7→P8 non-bypassable guards (all required, no inferred consent):**

1. `workflow_mode == PRO`, **current** `screenplay_id + screenplay_revision` exist and a **source-to-scene/beat lineage choice** is valid: **(A)** an owner-approved or explicitly reconciled Beat Sheet with current source revision, **or (B)** a script-derived scene/beat map generated from the exact current Fast Draft or imported screenplay, with origin `SCRIPT_DERIVED`, source anchors, coverage and known unknowns. Option B carries **no fictional earlier Beat Sheet** approval; it is disclosed as script-derived and included in the **same explicit P7 screenplay + storyboard-transfer decision**. Mapping or rights/source gaps block bridge; report-only critique remains allowed. Subsequent material changes stale the map.
2. `owner_approval_proof` explicitly identifies exact current screenplay ID/revision and permitted **screenplay-derived storyboard transfer**; contains owner decision provenance. `ACCEPTED_NOT_APPLIED`, change `VERIFIED`, project approval, or generic “looks good” cannot substitute.
3. Evaluate exactly the six gate IDs in **Canonical Gate Registry** (`RM-W03 §2A` and `Design_Control/SW-01_Canonical_Gate_Registry_v0.3.2.md`): `SOURCE_AND_AUTHORITY`, `RIGHTS_FOR_INTENDED_USE`, `SCRIPTURE_SOURCE`, `CANONICAL_CONTINUITY`, `APPROVAL_INTEGRITY`, `REFERENCE_CONSULTATION`. Each **applicable** gate is `PASS`; each `NOT_APPLICABLE` has a reason; `BLOCK` or `NOT_CHECKED` for any applicable gate blocks. `APPROVAL_INTEGRITY` PASS is established only when exact-script owner confirmation is recorded at P7, not earlier. `OWNER_AUTHORITY`, `RIGHTS`, and editorial `NONE` are never accepted as canonical gate IDs.
4. Required dependencies, affected scene/beat information-state checks and needed source/rights evidence are current, with `CHECKED_PASS` or a justified nonapplicable determination. `NOT_CHECKED`, `CHECKED_FAIL`, unknown relevant revision or required source gap blocks.
5. Open **non-hard** artistic issues are disclosed with explicit owner acknowledgment. Acknowledgment **never** converts a hard block to PASS; no global artistic score substitutes for a source/rights gate.

**Fast Draft/imported-script transfer rule (RIC-01):** P2→P4 and P1→P5 are legitimate professional intake paths with no pre-approved Beat Sheet. Before P7, create a *current* scene/beat map with source anchors and `lineage_mode=SCRIPT_DERIVED`, or ask the owner to approve/reconcile an outline/Beat Sheet. Do not infer owner approval from accepting an imported screenplay or a critique; demonstrate complete affected scene/beat coverage. P7 exact-revision approval includes any script-derived map used for transfer. A pure critique request may finish as report-only without building a map or passing P7.

**P8 re-entry guard:** `P8` independently rechecks all five conditions on every use, including after pause/bridge error; if any changed, return to `P7` or relevant correction stage. A past approval for another revision is never inherited. `P8` only creates a **storyboard DRAFT** with complete scene/beat disposition; it never claims Director Project approval or external-action authorization.

**Structural invariant:** in the workflow graph, **the only inbound edge to `P8` is `P7`**, and there are **no edges from `PF` or `PP` to `P8`**. A valid stage name alone cannot authorize transition. On retry/pause, recover source IDs, exact revision, owner decisions, source/gate evidence and saved stage. Missing records → `BLOCKED_PENDING_EVIDENCE`, no fabricated history.

### Review and revision semantics (P5/P6/P6V/P7)

- **Critic:** Evidence-calibrated RM-W03 finding: fact/anchor, inference, alternatives, verification need, confidence, impact, gate type/status, repair priority, reference actually consulted. Incomplete context → `INCONCLUSIVE` rather than invented certainty.
- **Proposals:** `PROPOSED → ACCEPTED_NOT_APPLIED → APPLIED_UNVERIFIED → VERIFIED / REGRESSED`, with `REJECTED` and `DEFERRED` alternatives. These are change-record states, **not** screenplay approval states.
- **Recheck:** preserve old/new script revisions and changed spans; produce `FIXED / PARTIAL / UNCHANGED / REGRESSED / INCONCLUSIVE` per issue, check all affected dependent scenes and all required source/authority constraints. A local `FIXED` or change `VERIFIED` is **not** approval and is not proof of artistic superiority.
- **Recovery:** Report-only critique may end with uncertainty, but screenplay-derived canonical bridge cannot cross unresolved applicable hard gates. Existing project and external-production authorizations remain wholly separate.

## B. WF-SW-QUICK — Legacy Quick Storyboard (approved option)

**Mission outcome:** an existing-style storyboard draft, without a mandated professional screenplay or Screenplay Approval Gate.  
**Actors:** `creator/owner`, `Director assistant`.  
**Required inputs:** `{explicit_mode=QUICK_STORYBOARD, story_idea_or_existing_project}`.  
**Optional inputs:** `{genre, passage, length, style, audience}`.  
**Start:** `Q0` | **Terminals:** `Q-DRAFT-DONE`, `Q-STOP` | **Successful terminal:** `Q-DRAFT-DONE`.  
**HITL:** No *new* SW-G2 gate. Any existing Director Project approval remains necessary before claiming approval/production readiness; draft completion is not production approval.

| ID | Kind | Protocol | Wait? | Transitions |
|---|---|---|---|---|
| Q0 | start | UIP-SW-01 | false | `quick_requested`→Q1 (record explicit mode); `stop`→Q-STOP |
| Q1 | action | UIP-SW-01 | false | `basic_brief_sufficient`→Q2; `failure`→QF (essential source gap) |
| Q2 | action | UIP-SW-06 | false | `legacy_storyboard_draft_created`→Q-DRAFT-DONE (label non-screenplay-approved); `failure`→QF; `stop`→Q-STOP |
| QF | failure | UIP-SW-06 | true | `retry`→Q1; `stop`→Q-STOP |
| Q-DRAFT-DONE | end | UIP-SW-06 | false | `{}` |
| Q-STOP | end | UIP-SW-06 | false | `{}` |

**Completion evidence:** user-selected quick mode recorded; storyboard draft produced using existing relevant reference obligations; no mandatory RM-W consultation or SW-G2 approval claimed. If user later requests professional screenwriting, create a new linked professional draft without silently reinterpreting prior approval.

## C. WF-SW-REVIEW/EDIT — Script-first/targeted revision, with mandatory post-apply check

**Mission:** produce a bounded diagnostic report, or create an explicitly authorized draft revision and verify its actual changes. **Actors:** creator/owner, Director assistant. **Required:** supplied complete or partial source and critique/edit scope. **Optional:** provenance/rights, script ID/revision, scene context, duration. **Start:** `R0`. **Terminals:** `R-REPORT`, `R-STOP`. **Successful:** `R-REPORT` with a truthful report state. **HITL:** `R3` (selection/acceptance), `R4W` (authorization to **apply** exact change) on any mutating route. No import is self-approved.

| ID | Kind | Protocol | Wait? | Guarded transitions → destination / state effect |
|---|---|---|---|---|
| R0 | start | UIP-SW-01 | no | `script_or_extract_received`→R1 / preserve exact import; `failure`→RF; `stop`→R-STOP |
| R1 | action | UIP-SW-03 | no | `source_scope_and_rights_recorded`→R2 / identify missing upstream context; `failure`→RF |
| R2 | action | UIP-SW-03 | no | `critique_only_or_bounded_inconclusive`→R-REPORT / **report-only** source unchanged; `edits_requested`→R3 / propose scope and alternatives; `failure`→RF |
| R3 | wait | UIP-SW-04 | yes | `accept_proposal_only`→R4 / selection **not apply authority**; `reject_or_defer`→R-REPORT / unchanged; `revise_proposal`→R2; `stop`→R-STOP |
| R4 | action | UIP-SW-04 | no | `accepted_proposal_logged`→R4W / exact target revision, delta, protected constraints and dependencies recorded as `ACCEPTED_NOT_APPLIED`; `failure`→RF |
| R4W | wait | UIP-SW-04 | yes | `authorize_apply_exact_change_to_source_revision`→R5 / owner permission references exact source revision and scope; `withhold_apply`→R-REPORT / still `ACCEPTED_NOT_APPLIED`; `revise_scope`→R3; `stop`→R-STOP |
| R5 | action | UIP-SW-04 | no | `authorized_change_applied_to_new_DRAFT_revision`→R6 / source immutable, new revision `APPLIED_UNVERIFIED`, diff/affected dependencies logged; `failure`→RF |
| R6 | action | UIP-SW-03 | no | `before_after_and_dependency_recheck_completed`→R7 / per-issue dispositions + cross-scene regression + hard gates; `missing_required_context_or_gate_check`→R7 / label `INCONCLUSIVE` and `BLOCKED_PENDING_EVIDENCE` as relevant; `failure`→RF |
| R7 | action | UIP-SW-03 | no | `review_report_complete`→R-REPORT / record verified/unverified or regressed draft status, **never auto-approve screenplay**; `failure`→RF |
| RF | failure | UIP-SW-06 | yes | `retry_recorded_failed_stage_with_required_input`→R1/R2/R4/R5/R6/R7 only matching saved stage and fresh consent if material inputs changed; `start_new_intake`→R0; `stop`→R-STOP |
| R-REPORT | end | UIP-SW-03 | no | `{}` |
| R-STOP | end | UIP-SW-06 | no | `{}` |

**Guard/checkpoint semantics:** `R3` acceptance is `ACCEPTED_NOT_APPLIED`, not permission to mutate. `R4W` may consume an already-explicit user authorization supplied with the original request only if it identifies **the exact proposed change, source revision and authorized scope**; otherwise must wait. `R5` cannot run without that evidence. `R6` is **mandatory after every actual R5 mutation**; on failure or unavailable affected context, the revision remains unverified/blocked (or `REGRESSED` with evidence). `R7` reports one issue disposition of `FIXED/PARTIAL/UNCHANGED/REGRESSED/INCONCLUSIVE`, change lifecycle and source evidence limits. Imported partial scripts are valid for limited critique; their absent context is `NOT_CHECKED` where applicable and precludes *canonical bridge readiness*, not a report-only terminal.

**Report-only and canonical distinction:** `R-REPORT` is a **report/draft** endpoint, not `APPROVED_SCREENPLAY`, `READY_FOR_HANDOFF`, Director Project approval or an external-production request. To bridge a revised screenplay via the professional route, separately enter `WF-SW-PRO` at valid intake and reach `P7` exact screenplay approval, then `P8`. Alternatively, a user may explicitly choose the legacy Quick Storyboard route, which retains its existing Director approvals. No owner acceptance of a suggestion is converted into approval of the entire screenplay.

## D. Instruction Module contracts

Each module below is a **logical behavioral responsibility**, not a deployable Skill, implementation binding, storage choice or file path. Each contract records purpose, trigger, inputs, preconditions, procedure, output, UIP, transitions, stop/wait/completion, failure/recovery, safety and references.

### IM-SW-01 — Intent & Mode Router (`intent-triggered`)

- **Purpose/outcome:** Select a faithful route and protect quick-path choice.
- **Trigger:** New story, screenplay critique, dialogue edit, storyboard-only or non-narrative music intent.
- **Inputs:** Required user task; optional source text, genre, approval state, time, mood.
- **Preconditions:** None beyond recognizable request; preserve explicit mode precedence.
- **Procedure:** Categorize intent → recommend professional for new narrative when unspecified → visibly offer quick storyboard → honor explicit quick/critique/edit requests → record selected route.
- **Outputs:** Route decision and recorded brief assumptions.
- **UIP:** UIP-SW-01. **Transitions:** IM-SW-02/03/04 as relevant or legacy storyboard path.
- **Stop/wait/completion:** Wait only for consequential ambiguous choice; complete on recorded route; user may stop.
- **Failure/recovery:** Conflicting mode/constraints → state conflict → ask one focused question; no silent default that overrides explicit instruction.
- **Safety/references:** Respect existing Bible/rights and project authority; no required new RM-W for pure quick route.
- **Acceptance:** AC-SW-01, AC-SW-02.

### IM-SW-02 — Story Architect (`primary-workflow`)

- **Purpose/outcome:** Causally coherent, genre-adapted story architecture.
- **Trigger:** Professional new-story design or substantive structural revision.
- **Inputs:** Required premise/source and mode; optional duration/audience/characters/tone.
- **Preconditions:** Intent identified; source constraints known or explicit provisional labels.
- **Procedure:** Articulate protagonist goal, motive, pressure, stakes, beat turns, ending goal and scene necessity; offer alternative structures when material; evaluate filmability.
- **Outputs:** Story architecture brief and beat sheet with IDs; open questions.
- **UIP:** UIP-SW-02. **Transitions:** IM-SW-03 or rework/stop.
- **Stop/wait/completion:** Wait at major user creative decisions in Guided mode; ready when critical story logic is coherent and assumptions visible.
- **Failure/recovery:** Missing material premise → clarify or flagged tentative brief; do not invent Bible facts.
- **Safety/references:** RM-W01 required; RM-S01/S03 where corresponding Bible/inspirational context applies.
- **Acceptance:** AC-SW-03.

### IM-SW-03 — Screenplay Writer (`primary-workflow`)

- **Purpose/outcome:** Filmable script, scene identities, realistic timing assumptions and voices.
- **Trigger:** Approved/working outline or existing script extension.
- **Inputs:** Required beat plan or specific user script; optional cast, source, language, duration.
- **Preconditions:** Clear permitted scope, source classification, no false approval.
- **Procedure:** Write scene units, visible action, character cues, dialogue, turns, constraints and timing estimates; preserve story-source boundaries.
- **Outputs:** `Screenplay DRAFT` with stable identifiers and relevant lines.
- **UIP:** UIP-SW-04. **Transitions:** IM-SW-04; revise or stop.
- **Stop/wait/completion:** Complete on inspectable draft; not approved until IM-SW-07 gate.
- **Failure/recovery:** Missing source or reference → draft non-source-dependent material only; report uncertainty.
- **Safety/references:** RM-W01 for narrative structure; RM-W02 required for relevant scene causality, visual turn/reveal or spoken dialogue (silent dialogue-scoring `NOT_APPLICABLE`; purely non-narrative poetry without applicable dimensions may skip with reason); RM-C07 **only** for dialogue/narration cue output; genre references when relevant. Imported complete script in PRO may route P1→P5 without rewriting or requiring a newly authored beat sheet.
- **Acceptance:** AC-SW-04, AC-SW-08.

### IM-SW-04 — Diagnostic Critic (`primary-workflow`, also intent-triggerable)

- **Purpose/outcome:** Explainable diagnosis independent of uncontrolled rewriting.
- **Trigger:** Draft completed, imported script, user critique request or recheck after revision.
- **Inputs:** Required script text/scope; optional stated goals, previous issues, rubric, source.
- **Preconditions:** Source scope and revision recorded; no invented scene evidence.
- **Procedure:** Locate issues, distinguish defect from choice, prioritize by impact, provide alternatives/tradeoffs; disclose unknowns.
- **Outputs:** Issue-indexed Critique Report; no script mutation.
- **UIP:** UIP-SW-03. **Transitions:** IM-SW-05 or owner review; end critique-only workflow.
- **Stop/wait/completion:** Complete on evidence-bound critique; user may stop or decline all suggestions.
- **Failure/recovery:** Incomplete script → partial critique labeled; missing required reference → reference-unverified status.
- **Safety/references:** RM-W03 required, RM-W01/W02 by dimension, RM-S02/S04 for genre-specific source checks.
- **Acceptance:** AC-SW-05, AC-SW-10.

### IM-SW-05 — Controlled Revision & Recheck (`primary-workflow`, intent-triggerable)

- **Purpose/outcome:** Improve selected issues without damaging original intent.
- **Trigger:** Owner selects corrective changes or selective dialogue/scene improvement.
- **Inputs:** Required exact script ID/revision, scope and selected changes; optional target style/time.
- **Preconditions:** Authorized revision scope and original preserved.
- **Procedure:** Propose minimal diff and tradeoffs → wait for material choice → apply selected changes to draft only → run before/after checks for new issues → record accepted/rejected/deferred outcomes.
- **Outputs:** revised DRAFT, diff, decision log, residual issue report.
- **UIP:** UIP-SW-04. **Transitions:** after explicit apply authorization, mandatory IM-SW-04 recheck against exact before/after revisions; IM-SW-07 owner screenplay approval only on a separate professional-bridge request; or stop/report-only.
- **Stop/wait/completion:** Wait before consequential rewrite, complete when delta/impact report available.
- **Failure/recovery:** Contradictory constraints → pause change; ask specific owner decision; restore original unaffected.
- **Safety/references:** RM-W03 required; RM-W02 for dialogue; RM-P05 when approved source is affected.
- **Acceptance:** AC-SW-06, AC-SW-12.

### IM-SW-06 — Screenplay-to-Storyboard Bridge (`primary-workflow`)

- **Purpose/outcome:** Convert exact approved script into traceable cinematic intent.
- **Trigger:** Professional script explicitly approved and user requests storyboard.
- **Inputs:** Required approved screenplay ID/revision and scenes; optional visual style/production constraints.
- **Preconditions:** Valid owner approval for exact current screenplay revision, applicable mandatory gates PASS, no unchecked required dependency, reference consultation and source currentness evidenced; P8 guard checked again on re-entry.
- **Procedure:** Require all P7→P8 guards including six canonical IDs, exact-version consultation records and an approved-or-script-derived beat lineage, then map `screenplay_scene_id + beat_id` to 1..N storyboard shots (or map multiple source beats to one storyboard representation only with explicit trace and reason); never force screenplay scenes to match the legacy 5–10 storyboard-scene range; flag omissions, splits/merges, changed dialogue; require owner acceptance of consequential transformation; mark traceability.
- **Outputs:** Bridge Map and storyboard DRAFT, with source revisions.
- **UIP:** UIP-SW-05. **Transitions:** Existing cinematic direction/Director Project approval; back to author if blocked.
- **Stop/wait/completion:** Complete only when all required scene/beat dispositions accounted for.
- **Failure/recovery:** Unmapped scene or inconsistent approved revision → `BLOCKED`, fix map or return to revision approval.
- **Safety/references:** Existing RM-P01/RM-P05, RM-C03 and cinematic references on demand; protect exact Bible spoken text.
- **Acceptance:** AC-SW-07, AC-SW-09.

### IM-SW-07 — Canonical State, Provenance and HITL Integrity (`cross-cutting`)

- **Purpose/outcome:** Preserve approval and version traceability without new hidden gates.
- **Trigger:** Any approval, script-source edit, export, pause, resume, bridge or route change.
- **Inputs:** Required active project/script IDs and revisions when available; optional existing downstream relationships.
- **Preconditions:** Identify source of truth; do not infer approval from draft.
- **Procedure:** Apply six-ID Canonical Gate Registry and per-action status; check gate applicability (pro vs quick), record owner decisions and non-bypassable P7→P8 proof, create revisions for semantic changes, re-evaluate downstream currentness selectively, preserve old accepted history; ensure pause/resume/failed bridge cannot directly enter P8.
- **Outputs:** approval record, lineage log, stale-dependency report.
- **UIP:** UIP-SW-05 / UIP-SW-06. **Transitions:** Return to appropriate workflow stage; recover a paused/failed P8 via P7 recheck, never directly P8; block unauthorized transitions.
- **Stop/wait/completion:** Wait for consequential approval; complete only with valid state transition.
- **Failure/recovery:** Broken provenance → `BLOCKED`, preserve original and request fix/source.
- **Safety/references:** Existing RM-P05 required, RM-P01 as relevant; never presume external action authorization.
- **Acceptance:** AC-SW-02, AC-SW-09, AC-SW-13, AC-SW-14.

### IM-SW-08 — Bible / Values Integrity (`cross-cutting`)

- **Purpose/outcome:** Faithful Bible adaptation or coherent approved inspirational values.
- **Trigger:** Story mode BIBLE or INSPIRATIONAL, or material change to theme/ethics.
- **Inputs:** Required relevant Bible passage/source when exactness claimed; optional interpretation notes, audience, theological boundaries.
- **Preconditions:** Distinguish cited text vs paraphrase vs invented staging.
- **Procedure:** Check source wording/meaning against accessible text; mark imagined dialogue and nonliteral staging; reject contradiction; review value claims in original inspiration.
- **Outputs:** source-boundary labels and fidelity/values findings.
- **UIP:** UIP-SW-03 and UIP-SW-05 at material disagreements.
- **Transitions:** Draft/revision/owner approval; block exact quotation without verified source.
- **Stop/wait/completion:** Completed when all material source assertions verified or transparently uncertain; user chooses on theological ambiguity.
- **Failure/recovery:** Passage inaccessible → exactness blocked, continue only non-claiming assistance.
- **Safety/references:** RM-S01/RM-S02 or RM-S03/RM-S04 as appropriate; RM-W cannot override Scripture.
- **Acceptance:** AC-SW-08.

### IM-SW-09 — Reference, Rights and Evidence Integrity (`cross-cutting`)

- **Purpose/outcome:** Never present packaging or mentions as proof of consultation; protect rights and source provenance.
- **Trigger:** Reference-dependent plan/draft/critique/revision, imported third-party script, handoff/provenance claim.
- **Inputs:** Required source/ref identifiers and applicable usage conditions; optional authorship/license metadata.
- **Preconditions:** Source is accessible and rights claims distinguish inspection vs transformation vs redistribution.
- **Procedure:** Identify every triggered required material in the per-reference Usage Map; consult its actual content; create per-use `ConsultationRecord` with identity/version, stage/module, triggering reason, access evidence, distinct applied knowledge, status and fallback. A filename mention, static path or generic answer does not prove reading or correct application. For required missing/unverifiable knowledge set `REFERENCE_CONSULTATION=NOT_CHECKED/BLOCK` as warranted; restrict dependent claims and actions. Rights for inspection/transformation/quotation/redistribution remain independently assessed.
- **Outputs:** Per-use Consultation Record(s), Reference Consultation Statement, per-branch completeness decision, Rights/Provenance Decision Record. Correct knowledge use is independently assessable from content evidence; reading alone is insufficient.
- **UIP:** UIP-SW-06. **Transitions:** Continue only supported dimensions; block source-dependent compliance claims.
- **Stop/wait/completion:** Wait if rights/fidelity decision material; completion when all required claims have evidence or explicit uncertainty.
- **Failure/recovery:** `REFERENCE_CONSULTATION_UNVERIFIED`, `RIGHTS_UNRESOLVED`, `SOURCE_UNVERIFIED` with safe fallback.
- **Safety/references:** Usage map; relevant existing and proposed sources.
- **Acceptance:** AC-SW-10, AC-SW-14.

### KR-01 enhancements to logical module behaviors

**IM-SW-02 Story Architect:** apply RM-W01 v0.3.1's optional story-identity/point-of-view and information-state checks when relevant, and record evidence basis for scene timing. Do not require novelty or an elaborate character arc for Bible/poetic work.

**IM-SW-03 Screenplay Writer:** apply RM-W02 v0.3.2 character-voice contrast and dialogue/visual/nonlinear alternatives. Hand off significant reveal seeds, character knowledge, affected prior/future scene IDs and exact constraints to the critic; retain RM-C07's format responsibility.

**IM-SW-04 Diagnostic Critic:** required RM-W03 v0.3.2 evidence separation, anchored findings, confidence, alternatives, optional score anchors, independent hard gates and priority order. Do not infer actual viewer reactions from predicted effects.

**IM-SW-05 Controlled Revision:** require distinct proposal statuses, author scope choices, per-issue dispositions, impact-specific cross-scene checks, readiness blocking and evidence limits. Re-evaluate the original and changed source; a second model pass is not an independent human review.

**IM-SW-06 Bridge / IM-SW-07 State:** script revision `APPROVED` only after exact owner approval; blocked dependencies cannot enter canonical bridge; subsequent screenplay changes trigger selective stale propagation. Existing project/production authorization is separate.

**IM-SW-08/09 Source and Evidence:** enforce source and approval hard gates without replacing Bible/inspirational rubrics; report exact reference revision consulted; quick storyboard bypass must not become dependent on RM-W03.


## E. Named user-interaction protocols

| Protocol | Mode | Required vs provisional | Per-turn question limit | Wait condition | Alternatives/confirmation | Pause/stop/ambiguity recovery |
|---|---|---|---|---|---|---|
| UIP-SW-01 | guided/direct | User task required; audience/time provisional | Default **1 consequential** | Mode conflicts or exact source gate | Show Professional recommended and Quick directly; honor explicit selection | Preserve mode evidence; conflict → one focused question; stop immediately |
| UIP-SW-02 | co-creative | Premise/source required; beats draft | Default **1 consequential** | Material theme/ending/character choice in guided mode | 2–3 differentiated story options if useful; explicit for material choice | Save beat IDs and open choice on pause; resume summarizes prior decision |
| UIP-SW-03 | evaluative | Actual script or marked partial input required | Default **1 consequential** | Source integrity blocks claim or owner asks decision | Offer issue alternatives and confidence; critique never equals rewrite | Incomplete source → partial analysis; reject suggestions without mutation |
| UIP-SW-04 | co-creative | Exact scope/source revision required | Default **1 consequential** | Material change proposed, contradictory constraints | Options and before/after; require selected change before applying | Rejected/deferred changes logged; owner can rollback to prior revision |
| UIP-SW-05 | direct | Exact script revision required | **1 explicit approval decision** | Script → canonical storyboard transfer, or other existing gate | Approve / Revise / Pause / Stop with risks; no implicit assent | Revision creates new draft; previous approval not automatically inherited |
| UIP-SW-06 | direct | Saved state and reported failure as available | Default **1 consequential** | Missing mandatory data/source/rights, pause or error | Retry/skip optional/stop; do not skip safety or approval | Resume restates stage, IDs, decisions, open question, next gate |

**FDR-01 guard rule:** On approval or recovery, the interface must display exact `screenplay_id`, `screenplay_revision`, relevant Hard Gate statuses, inspected dependency set, unresolved non-hard issues, and whether the owner approval is effective for this exact bridge. Never treat technical `change_verified` as creative approval.

**Common rules:** The user may revise, skip optional work, pause, resume or stop at any stage. A skip never bypasses mandatory source verification, consent or approval. Don't combine unrelated questions to obey the numeric limit. Stop states preserve history. Generate draft after sufficient context, mark unresolved assumptions; final/approved status demands explicit evidence.

## F. FDR-01 acceptance invariants

- INV-01: Graph check: all paths `P0 → P-DONE` contain `P7` and `P8`; `P8` inbound predecessor only `P7`; PF/PP have no direct P8.
- INV-02: An exact owner-approved screenplay revision, PASS/justified N/A on applicable hard gates, current dependencies and non-hard issue acknowledgment are all prerequisites to P7→P8 and rechecked at P8.
- INV-03: In REVIEW/EDIT, all actual changes flow `R3 → R4 → R4W → R5 → R6 → R7`; any `R-REPORT` path from R2 is report-only, and R-REPORT never claims canonical approval.
- INV-04: Every R5 new revision has immutable original, targeted diff, authorized scope and R6 recheck result; missing affected context yields bounded report/blocked handoff.
- INV-05: Quick path bypasses SW-G2 while retaining existing Director Project and production gates; no cross-path hidden approval.
- INV-06: Scene/beat identifiers are distinct from storyboard shot identifiers; 1..N mapping and justifications for grouping/splitting are traceable.

## G. Workbench boundary

This annex gives **behavioral requirements** and traceability, not Skill names, technical bindings, storage or scripts. The installed six-Skill design is a **compatibility reference**, not a mandate on the Workbench. No app/source ZIP modified; design package must be owner-approved before a Workbench handoff is permitted.
