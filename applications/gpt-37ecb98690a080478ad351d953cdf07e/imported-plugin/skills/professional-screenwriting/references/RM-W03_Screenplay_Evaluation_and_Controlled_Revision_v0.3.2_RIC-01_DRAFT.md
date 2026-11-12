# RM-W03 — Screenplay Evaluation & Controlled Revision
## Professional Critic, diagnosis, owner control and verification | v0.3.2 RIC-01 DRAFT

**Status:** KR-01 revised knowledge DRAFT; owner authorized knowledge refinement, **not approval of this exact text for installed Plugin**. **P0 implemented in this draft:** G01 evidence calibration; G02 score anchors/gates; G03 priority; G04 result dispositions; G05 regression matrix; G06 independent quality evidence.  
**Required behaviors:** Screenplay Critic, prioritized diagnosis, targeted improvement, verification of regression, material change decisions and screenplay review gate.  
**Out-of-scope:** Autonomous owner approval, actual audience-retention measurement, replacing relevant Bible/inspirational authority, or bypassing Director Project/production gates.

## 1. Editorial philosophy

A Critic must be a **careful diagnostician**, not a compliance-scoring robot. It must distinguish a specific weakness from a legitimate stylistic choice; prefer visible evidence over vague advice; offer actual alternatives with tradeoffs; and recognize when no change is warranted. Story quality remains partly subjective. The owner retains final artistic authority.

**Core loop:** `Diagnose → Prioritize → Offer Alternatives → Owner Decides → Apply Scoped Change → Recheck → Report`.

## 2. Structured evaluation dimensions

Rate only when evidence exists. Suggested diagnostic **1–5** scale expresses supported **editorial effectiveness relative to the work's purpose**, not scientific measurement. For non-dialogue works, mark dialogue `NOT_APPLICABLE` rather than forcing a score.

| Dimension | What to test | Warning signs |
|---|---|---|
| Premise/clarity | Can intended viewer grasp central situation and stake? | Vague aim, orientation withheld without purpose |
| Character causality | Do choices follow motivation/knowledge/constraints? | Characters act only to serve twist |
| Scene necessity | Does scene change state or meaning? | Repetition, no turn or contribution |
| Conflict/stakes | Are obstacles genuine and proportionate? | Hollow argument, unexplained danger |
| Dialogue/subtext | Does spoken content suit voice/action and avoid expository lecture? | Same voice for all, info already known to speakers |
| Pacing/emotional development | Is change digestible within duration? | Important choice skipped, redundant middle |
| Setup/payoff and reversals | Does later information feel earned? | Arbitrary coincidence or retroactive lie |
| Resolution/meaning | Does ending follow character action and premise? | Unsupported miracle, lecture replaces choice |
| Filmability/continuity | Can intended events be shown and tracked? | Invisible-only action, conflicting props/time |
| Source integrity/intent | Bible/rights/values boundaries preserved? | Fiction attributed to Scripture, user intention overwritten |

**Hard-gate risks** (non-score-based): Scripture misattribution, unsupported exact quotation, explicitly forbidden content, unapproved canonical rewrite, missing mandatory source reference or broken scene identity. Do not average these away with high artistic scores.

## 2A. Calibrated scoring and separate hard gates — KR-01 G02

**Scores are optional editorial aids**, not scientific measurements or audience forecasts. For each *applicable* dimension that has sufficient screenplay evidence, a 1–5 descriptor may be recorded with location, explanation, and confidence: **1** = essential dramatic function absent or demonstrably contradictory; **2** = major weakness obstructs the intended understanding or action; **3** = adequate function with identifiable limitations/tradeoffs; **4** = substantially effective with limited noncritical refinement; **5** = particularly effective for the approved purpose with concrete textual evidence, **not** objectively optimal. `NOT_APPLICABLE` and `INSUFFICIENT_EVIDENCE` are valid instead of a number. No forced average or overall grade; score disagreements remain visible.

**Two separate result lanes:** `SOURCE_AND_AUTHORITY_COMPLIANCE` and `CRAFT_QUALITY`. A high craft score cannot override a source/rights/human-approval gate. Biblical fidelity needs verified passage/version and applicable RM-S02; inspirational values use RM-S04 *when relevant*, not on unrelated fiction. A hard gate is triggered **only by an applicable actually established mandatory constraint** (e.g., Scripture quoted without verified source, unauthorized canonical change, rights prohibition for requested redistribution, required scene/line identity lost), not by ordinary subjective disagreement. Do not equate every plot weakness with a legal/safety hard blocker.

### Canonical Gate Registry — RIC-01 (normative across RM-W03, P5/P7/P8, IM-SW-06/07/09)

Use these **six and only six canonical gate identifiers** for workflow gate state. The registry is shared by script critique, exact-revision approval, and the storyboard bridge. An editorial finding with **no mandatory gate** has `gate_type: NONE`, `gate_status: NOT_APPLICABLE`; `NONE` is not a seventh gate and must not count as PASS.

| Gate ID | Trigger / applicability | PASS requires | BLOCK or NOT_CHECKED consequence |
|---|---|---|---|
| `SOURCE_AND_AUTHORITY` | Verbatim/source-dependent claim, provenance assertion, or canonical screenplay-derived transfer | Required sources identified, accessible, correctly attributed; source version and authority evidence current for the intended claim | Unsupported material source or authority claim blocks that claim; missing required lineage blocks P7/P8 |
| `RIGHTS_FOR_INTENDED_USE` | Adaptation, quotation, asset upload, redistribution or other activity whose rights must be checked | Rights checked **for the particular action**, including private inspection vs transformation vs publication | Unknown/prohibited required permission blocks that action, not unrelated private critique |
| `SCRIPTURE_SOURCE` | Bible-mode source fidelity, exact biblical wording or Bible factual attribution | Supplied/authorized passage and translation verified; fictional staging separately labeled | Unsupported exact quote or fidelity claim blocks source-conformant bridge |
| `CANONICAL_CONTINUITY` | Changes or handoff affecting protected scenes, approved facts, chronology, character knowledge, assets, scene IDs | Relevant dependencies/current revisions checked, with no unresolved material contradiction | Failed/missing mandatory dependency check blocks bridge and any affected approved transfer |
| `APPROVAL_INTEGRITY` | Material rewrite with approval requirement; **always** exact-revision professional P7/P8 transfer | Owner has explicitly authorized the exact action/scope; for P7/P8 same current screenplay ID+revision and scope of storyboard transfer | Inferred, absent, wrong-scope, changed-revision or stale approval blocks that action |
| `REFERENCE_CONSULTATION` | Any claim/action depending on knowledge defined as required by the current branch-level Usage Map; **always** P7/P8 for applicable required knowledge | Each triggered required reference was actually accessed at an identifiable version and materially applied, with an inspectable Consultation Record | Filename mention, uninstrumented access, missing content or misapplication cannot count as PASS; block source-dependent conformance/handoff claims |

**Gate status contract:** `PASS` = directly supported for the *exact action and current source revision*; `BLOCK` = negative evidence / known contradiction or prohibition; `NOT_CHECKED` = not evaluated or evidence missing; `NOT_APPLICABLE` = trigger does not apply, with recorded reason. An applicable mandatory gate at P7/P8 is admissible **only if PASS**; a properly justified NOT_APPLICABLE gate is excluded from mandatory set and must never be presented as a passed check. Recalculate gate applicability and status when source/revision, action/scope, assets, references or permissions change. Artistic scores never override status.

**Deprecated shorthand migration:** `OWNER_AUTHORITY` → `APPROVAL_INTEGRITY` only when the decision truly concerns exact action/scope authority; `RIGHTS` → `RIGHTS_FOR_INTENDED_USE` after specifying the intended use. Unmapped legacy values are `NOT_CHECKED`, not implicit PASS. `SOURCE_AND_AUTHORITY` and `SCRIPTURE_SOURCE` are **not** interchangeable: a correctly identified adaptation source does not prove an exact biblical quotation. A purely artistic `NONE` has no gate authority.

**P5/P7 sequencing:** P5 may record source-specific failures and advisory issues; a critique report may finish with applicable gates NOT_CHECKED but cannot claim readiness. At P7, show current screenplay revision and all applicable requirements **before** the owner confirms. After the user explicitly approves that exact revision and storyboard-transfer scope, evaluate `APPROVAL_INTEGRITY` transactionally with other applicable gates; save approval proof and proceed to P8 only if all applicable gates are PASS. P8 rechecks. The prior artistic approval, a proposed edit acceptance, an RM-W03 issue `FIXED`, or an AI-generated approval cannot satisfy this requirement. The existing Director Project and external-action approvals remain separate.

**Reference evidence:** A per-use `ConsultationRecord` (defined in the Reference Usage Map) must identify the exact reference/version, trigger, actual access evidence and distinctive knowledge applied; no record or an inapplicable citation cannot satisfy `REFERENCE_CONSULTATION`. Do not claim runtime verification from static indexes or a local ZIP marker probe.

**Author disagreement is not automatically a defect.**

## 2B. Review order and repair priority — KR-01 G03

Do not simply sort by aesthetic severity or model confidence. Review in this order: (1) source truth, rights, explicit owner authority and other applicable gates; (2) character knowledge/motivation and causality failures that undermine the plot; (3) scene information distribution, reveal logic, pacing and voice consistency; (4) local clarity and language polish. For each candidate record `impact_if_ignored`, `confidence`, `repair_scope`, `expected_gain`, `effort/cost`, `dependencies`, `preservation_constraints`, and `owner_options`. If repairing A requires moving a setup in SC01, surface that dependency before proposing a local-only change in SC03. Defer low-confidence “weak engagement” judgments rather than making mandatory rewrites.

**Priority is a proposal, not an authorization.** A user may elect to retain an unconventional treatment if no hard boundary is violated; the Critic records the deviation and its rationale where supplied. When a high priority issue is unsolved, lower-priority polish may be done only when it cannot hide the blocker and is permitted by the owner.

## 3. Evidence and problem diagnosis

For each substantial issue use a **Critique Finding**:

```
issue_id: SW-ISSUE-004
screenplay_id: SCR-07
screenplay_revision: 1
location: SC03 / dialogue lines D12-D15 (or stable beat ID)
observation: The mentor explains an error the apprentice already knows.
why_it_matters: Exposition interrupts confrontation and weakens character agency.
root_cause_hypothesis: Scene lacks distinct immediate goals.
editorial_severity: MAJOR
gate_type: NONE
confidence: MEDIUM
proposed_interventions:
  A: Replace explanation with challenge and visible evidence.
  B: Move technical background to earlier functional scene.
tradeoff: A increases ambiguity unless the scratch is established.
user_decision: PENDING
references_consulted: [RM-W03, RM-W02]
```

Legacy `severity` examples must be interpreted as **editorial_severity + separate gate_type/gate_status** under KR-01 §2A/§3B; a continuity discrepancy is not automatically a universal hard blocker. Use **confidence:** `HIGH`, `MEDIUM`, `LOW`. An issue cannot be a certain fact when inferred solely from viewer reaction speculation.

Distinguish a **defect**, **risk**, and **deliberate craft choice**. If the premise deliberately uses sparse dialogue, do not mark “too little dialogue” as a flaw without context.

## 3A. Evidence-calibrated finding contract — KR-01 G01

Each `MAJOR` or `BLOCKER` finding must separately identify **(a) observable source fact**, **(b) editorial inference**, **(c) plausible alternative explanation**, and **(d) what would falsify or verify the inference**. Quote only a minimal excerpt of a user-owned script when appropriate, otherwise use a stable line/beat anchor. A predicted audience reaction is a **hypothesis**, not an observed result. For incomplete source material, explicitly list what was not inspected and restrict confidence accordingly.

Illustrative **behavior-level** record (Workbench owns physical schema):

```yaml
issue_id: SW-ISSUE-004
source_screenplay_id: SCR-07
source_revision: 1
scene_or_beat_anchor: SC03 / D12-D15
criterion: DIALOGUE_EXPOSITION
source_evidence: [SC01/B03, SC03/D12-D15]
observable_fact: "SC03 restates apprenticeship history both speakers established in SC01."
editorial_inference: "This may interrupt an urgent confrontation."
root_cause_hypothesis: "The scene lacks distinct immediate objectives."
alternative_hypothesis: "Formal repetition is deliberately used to convey distance."
verification_needed: "Check creator's tone intent and full-scene goals."
editorial_severity: MAJOR
gate_type: NONE
gate_status: NOT_APPLICABLE
gate_reason: "DIALOGUE_EXPOSITION is an editorial judgement, not a mandatory source/rights/approval gate."
confidence: MEDIUM
repair_priority: 2
scope: [SC03]
owner_decision: PENDING
references_actually_consulted: [RM-W03, RM-W02]
```

A `LOW` confidence issue can still be urgent if an actual mandatory source restriction is threatened, but urgency does not turn an unverified hypothesis into fact. **A diagnostic result can be `INCONCLUSIVE`** with a reason and the additional evidence needed; never force a defect merely to display critique expertise.

## 3B. Distinguish editorial severity, hard gate and certainty

Use `editorial_severity` for creative **impact** (`MAJOR/MODERATE/MINOR/OBSERVATION`; `BLOCKER` only when an actually applicable mandatory requirement blocks the intended next transition). Use `gate_type` and `gate_status` separately from `confidence`, so “this dialogue may bore some viewers” is not a blocker and “the exact Scripture quote differs from the verified source” is not a subjective preference. Never claim `HIGH` confidence solely because multiple AI passes repeat the same opinion.

## 4. Targeted revision proposal

For any offered revision:

1. Quote/refer to a minimal local span or scene ID from the user's own draft.
2. Declare *intended effect*: clarity, tension, agency, credible twist, emotion, or filmability.
3. Declare *preservation contract*: theme, source facts, speaker intent, scene IDs, required dialogue, length/genre boundaries and owner restrictions.
4. Present 1–3 materially different alternatives if a meaningful tradeoff exists.
5. Surface downstream effects: previous setup, next scene, tone, costume/prop states, source faithfulness, estimated runtime.
6. Do not apply material changes without selection/approval. Draft suggestions are not canonical revisions.
7. Re-critique affected scene and dependencies after application; note actual change and residual risk.

**Default minimal-delta principle:** prefer the smallest change that solves the diagnosed problem. If a larger structural rewrite is necessary, describe why and obtain specific scope permission first.


## 5. Before/After verification — evidence, disposition and stopping rules (KR-01 G04–G06)

**Do not report a revised screenplay as better by default.** Preserve the original and revised immutable revisions and changed spans; perform both local and dependency-aware checks. For each issue, return one and only one outcome:

| Issue disposition | Required interpretation |
|---|---|
| `FIXED` | Specific defect absent or resolved in the reviewed revision **and** targeted textual checks passed; no new material regression in relevant dependencies. This is a *local text-level* conclusion, not a global audience-quality claim. |
| `PARTIAL` | Some evidence of progress, but original issue or material uncertainty remains. |
| `UNCHANGED` | Targeted weakness demonstrably remains with no meaningful corrective change. |
| `REGRESSED` | New material contradiction/source violation or a worsened important property attributable to the change; block completion until repaired/reverted or author-approved revision resolves a non-hard artistic tradeoff. |
| `INCONCLUSIVE` | Missing source, incomplete affected context, untestable effect or insufficient evidence prevents classification. |

**Never use `FIXED` on a change that has produced a new material contradiction in an applicable mandatory continuity/source dependency.** `REGRESSED` may coexist with a narrow improvement claim (“SC03 dialogue less expository”) but the *overall revision* is `NOT_READY_FOR_HANDOFF`. With mandatory gate `BLOCK` or `NOT_CHECKED`, handoff state is `BLOCKED_PENDING_FIX_OR_EVIDENCE` even if the Critic likes the prose. Record whether each issue outcome reflects `TEXTUAL_CHECK`, `EDITORIAL_REVIEW`, `INDEPENDENT_HUMAN_REVIEW`, or `NOT_DEMONSTRATED`; do not pretend a model-only review is independent.

For every changed issue produce:

| Field | Required content |
|---|---|
| Source and anchors | `issue_id`, original screenplay ID/revision, old scene/beat/line evidence |
| Revision and scope | proposed/current revision, new anchors, actual changed span, affected dependent scenes |
| Causal expectation | intended improvement and why this particular change could help |
| Observed textual result | quote/anchor showing what changed; verify evidence against the new text |
| Regression checks | check types performed, pass/fail/not-checkable, and dependency coverage |
| Residual uncertainty | unresolved issue, alternate hypothesis, source/rating limits |
| Disposition and evidence class | one of five dispositions, supporting observations, and evidence level |
| Author decision vs artifact status | approval of option vs applied edit vs verified draft vs exact screenplay approval |

**FDR-01 operational rule:** An author accepting a **proposal** results in `ACCEPTED_NOT_APPLIED`, not an edit. Only an explicit instruction authorizing the exact source revision, edit and scope permits mutation to `APPLIED_UNVERIFIED`; immediately run before/after plus affected-scene checks before reporting `VERIFIED` or `REGRESSED`. If required evidence is unavailable, preserve `APPLIED_UNVERIFIED` and mark affected issue `INCONCLUSIVE`; do not invent verification. An `R-REPORT` endpoint is not screenplay approval, even when a local issue is `FIXED`.

**Distinct proposal lifecycle** (does not replace RM-P05 canonical project/artifact state): `PROPOSED` → `ACCEPTED_NOT_APPLIED` → `APPLIED_UNVERIFIED` → `VERIFIED` or `REGRESSED`, with alternate exits `REJECTED` and `DEFERRED`. A `VERIFIED` local change does **not** confer `APPROVED` status on the screenplay; the screenplay approval gate explicitly identifies its exact revision. Rejection preserves the prior source; an accepted-but-not-applied proposal must not be silently written into the screenplay.

### 5A. Change-type-specific regression matrix — KR-01 G05

| Change type | Required checks and affected context |
|---|---|
| Event/scene reorder or addition | Scene causal links, chronology, location, who-knew-what, beat dependencies, resulting ending meaning |
| Dialogue/voice change | Character voice and knowledge, exact protected dialogue, listening/reaction, preceding/following response, tone/owner intent |
| Reveal/twist change | Seed/setup, reveal timing, information fairness, retrospective consistency, emotional consequence, source truth |
| Time/place/prop change | Timeline, spatial continuity, props/costume/asset states, shot handoff dependencies, estimated duration |
| Bible/inspirational adaptation | Verified cited source (when available), source labels, forbidden fictional attribution, original message/value constraints |
| Post-approval script edit | Exact source revision, human authorization, changed-scene dependencies, selective `STALE`/`SUPERSEDED` propagation through RM-P05 |

For every matrix row selected, distinguish `CHECKED_PASS`, `CHECKED_FAIL`, `NOT_CHECKED`, `NOT_APPLICABLE`, and explain how far surrounding context was read. A targeted dialogue edit may require checking SC01 and SC04 if they establish the information used in SC03. Machine-checkable scene IDs and hashes can be checked reproducibly; motivations, tone, emotional effect, and craft choices require editorial interpretation. If a mandatory cross-scene dependency cannot be checked, do not label the overall screenplay handoff ready.

### 5B. Example — stronger tension, broken chronology (negative control)

**Source facts (original fiction):** SC01: “Customer pickup is Friday, three days away.” SC03 v1: Apprentice explains history too long; customer is absent. **Candidate SC03 v2:** “Our confirmed contractual pickup date is TODAY!” This may intensify urgency, but **no intervening agreement change is established**. The verifiable **agreed-date contradiction** is between SC01 and SC03. Mere unannounced early arrival would *not* by itself contradict Friday: the review must distinguish a contradiction from a surprise visit.

*Issue SW-ISSUE-004 (exposition):* possibly `PARTIAL` or `FIXED` after verifying original dialogue was removed. *New issue SW-ISSUE-005 (timeline):* `REGRESSED` / `CANONICAL_CONTINUITY=BLOCK` (if Friday pickup is an approved required fact), and whole revised script `NOT_READY_FOR_HANDOFF`. **Repair choices:** retain Friday and add a different credible pressure; or seek explicit owner approval to revise SC01 and affected dependencies. Do **not** automatically assert Friday became Tuesday. A writer who chooses a surreal chronology must explicitly make that formal logic intelligible rather than be overruled by a rigid realism rule.

### 5C. Independent quality evidence and non-claims — KR-01 G06

Separate **textual defect correction** from **film quality/reader engagement**. One reviewer can verify an exact line no longer repeats a fact; that does **not** prove a more moving film. For product-level claims that SW-01 enhances screenwriting over v1.0.2, prepare matched briefs, requested duration, relevant constraints and source version for baseline/candidate. Use **two independent human readers where feasible**, separately assessing scripts with blind labels and counterbalanced order; require written text/scene anchors supporting their judgments. Record disagreements and negative cases—do not average away a fidelity failure or claim statistical certainty from a tiny sample. If fewer than two independent readers can be recruited, mark the comparative quality claim `QUALITY_GAIN_NOT_DEMONSTRATED` and document the limitation; this does not bar reasonable local editorial work.

**Proposed release-study decision rule (pending owner approval):** no applicable hard-gate failures; reviewers provide independently reasoned examples supporting improvement on at least one predeclared target dimension **without a material regression** in other protected dimensions; disagreement or insufficient evidence yields `INCONCLUSIVE` / `QUALITY_GAIN_NOT_DEMONSTRATED`, not a fabricated PASS. No predetermined numerical “quality score improvement” is assumed. Screenplay text review does **not** establish produced-film quality or actual viewer retention; those require different evidence.

### 5D. Example — genuine source-preserving improvement, with limits

**Original (fiction):**

MENTOR: “As you know, you have worked here for three years, and the customer expects the watch on Friday.”
APPRENTICE: “Yes, I learned that from you, and I damaged the gear.”

**Candidate (same story and time):**

MENTOR: “The watch stopped again.”
APPRENTICE (turns the dial away): “It won't after I replace the gear.”
MENTOR: “That's not what I asked.”

**Textual verification:** repeated background fact removed; characters now make opposed moves; Friday delivery remains unchanged in the source facts. Likely classification of exposition issue `FIXED` if adjacent scenes support comprehension and all required checks pass; **audience excitement or superior art remains unmeasured**. Verify whether the apprentice's new claim (“replace the gear”) conflicts with a prior SC02 showing that replacement is impossible. If SC02 not inspected, classify overall dependency check `NOT_CHECKED` and defer conclusive handoff.

## 6. Critic and Revision roles must not collapse

- **Critic** reads approved or draft source and returns a diagnosis; does not change canonical text.
- **Revision** proposes and applies only owner-approved material changes or nonconsequential language fixes within authorized scope.
- **Verification** checks that critique findings were addressed and re-evaluates new failures. A revised version can be worse and must be reported as such.
- **Approval** is a distinct human step with an exact revision ID, not an inferred signal from “looks good” when context is ambiguous.

Track `status`: `DRAFT`, `REVIEWED`, `APPROVED`, `REVISED_AFTER_APPROVAL`, `SUPERSEDED`, `REJECTED_PROPOSAL`, `STALE` for appropriate artifacts; do not conflate script/critique/target export state categories.

## 7. Decision and change-ledger contract

A change event should include:

```
change_id; source_script_id; original_revision; proposed_revision
issue_id; affected_scene_ids; requested_scope; protected_intent
proposal_summary; user_decision; applied (true/false)
verification_result; evidence_level; issue_disposition; regression_checks; unresolved_risks; time/actor when known
upstream_canonical_ref; affected_downstream_artifacts
```

**Rejected suggestions:** Retain without changing the source or treating the issue as “fixed.” **Deferred suggestions:** Retain as open issues. **Accepted but not yet applied:** Distinct from completed revision. Never mark a new script revision `APPROVED` merely because a single change was accepted.

## 8. Approval gates and version provenance

**FDR-01 exact-revision guards:** Entering the professional screenplay-to-storyboard bridge requires a current screenplay ID/revision, owner approval proof binding that exact revision, all applicable mandatory gates PASS (justified NOT_APPLICABLE allowed), required dependency checks complete, and explicit acknowledgment of unresolved non-hard issues. No `BLOCK` or required `NOT_CHECKED` can be overridden by artistic quality or owner acknowledgment. Pause/resume and bridge-error retry MUST route through approval revalidation before entering the bridge; an earlier approval does not transfer to changed text.

**Pro-path Screenplay Gate** is required before converting that screenplay to a **canonical** storyboard input. Present:

- screenplay ID + exact revision/hash or stable equivalent;
- brief story and mode, major source distinctions;
- critical unresolved issues and accepted departures;
- meaningful downstream implications of approval;
- clear `Approve revision Rn / Revise / Use quick-storyboard path / Pause / Stop` choices where appropriate.

**Quick Storyboard:** Existing quick workflow does not require SW screenplay approval; preserve existing Director Project approval, production approvals and provenance rules. Do not state that skipping screenplay review is intrinsically low-quality or unsafe.

**Post-approval edit:** Material change to script creates new revision. Mark dependent script-bridge/storyboard/Production Specification artifacts `STALE` selectively by changed dependency; old approved script remains historical, not silently replaced. Changes to exact dialogue, character intent, scene order, timing or props require downstream evaluation. Use existing RM-P05, never invent direct re-approval of changed canonical content.

## 8A. Scene/beat-to-shot bridge semantics

Professional screenplay scenes and their dramatic beats are not identical to storyboard shots. A source `(screenplay_scene_id, beat_id, script_revision)` may map to **1..N** ordered storyboard shots. When one storyboard record covers beats from multiple screenplay scenes, preserve source identities, coverage rationale, order and any authorized compression/merge. Original Director 5–10 storyboard scenes are an existing creative convention, **not** a limit on the number of screenplay scenes or camera shots. Owner-approved material changes to scripted events cannot be silently introduced in mapping.

## 9. Professional reference and Scripture authority handling

Relevant RM-W01/02 supply craft concepts but cannot override:

1. Verified Scripture and Bible-source fidelity when a biblical adaptation is requested;
2. Owner-approved creative decisions and mandatory exclusions;
3. Existing RM-P01/RM-P05 canonical production/state discipline;
4. The applicable Bible or inspirational story rubric for their specialized aspects.

When a professional reference is required but not consulted, mark `REFERENCE_CONSULTATION_UNVERIFIED`; report which dimensions are unverified rather than inventing evidence. Avoid treating an existing installed document header marked draft as proof it is approved; reconcile owner records during handoff.

## 10. Error and uncertainty handling

| Input condition | Response |
|---|---|
| Script incomplete | Critique visible portion; list unavailable sections and confidence limits |
| User asks for rating without script | Offer rubric and request script; do not fabricate assessment |
| Conflicting instructions | Identify contradiction, protect original and ask owner decision |
| Story intentionally sparse | Evaluate tension with applicable style; don't demand dialogue |
| No clear weak point | State strengths and remaining uncertainty; no forced rewrite |
| Missing original revision | Treat lineage as unresolved; avoid replacing authoritative source |
| Source text cannot be verified | Do not quote as exact; block claims of source-level conformance |
| Human rejects revision | Preserve current revision and record reason when supplied |
| Reference unavailable | Flag unverified and restrict claims dependent on it |
| Critic recommends a harmful/deceptive plot device | Suggest safer credible alternatives within user-approved meaning |

## 11. Quality assurance checklist

**For critique**: Each material issue has location, observable source fact, distinct inference, alternative hypothesis, causal impact, editorial severity, gate status and confidence, alternative and cost/tradeoff; hard constraints assessed independently. **For revision**: Only selected scope changed; original retained; diff and new risks reported; all source and owner constraints rechecked. **For approval**: exact revision and human consent captured. **For storyboard handoff**: all required scenes/beats have dispositions; no unapproved transformations. **For product validation**: include negative tests and human editorial evidence, avoid self-congratulatory self-scores.

## 12. Example of balanced revision findings (original)

**Original ending idea:** Apprentice confesses and mentor immediately tells her that all is forgiven; no practical consequence.  
**Possible diagnosis:** Character confession is credible but payoff removes the work's established stakes; the mentor's sudden acceptance may feel unearned.  
**Option A — relationally grounded:** Mentor accepts confession but asks the apprentice to personally explain the repair to the customer. **Gain:** responsibility and agency; **Risk:** could require an extra 20 seconds.  
**Option B — restrained:** Mentor silently gives the apprentice the customer phone number; apprentice makes the call. **Gain:** visual economy and active moral choice; **Risk:** may need stronger setup to clarify intent.  
**Option C — retain original:** If the story's intended point is unconditional grace, quick reconciliation may be deliberate. Keep original and improve performance only. **Gain:** preserves value emphasis; **Risk:** weaker dramatic consequence for some audiences.

The Critic must present these as alternatives and wait for author selection rather than assuming B is the best script.

## KR-01 reviewer guardrails and handoff contract

- **Diagnosed ≠ Verified.** A root-cause hypothesis is not a demonstrated mechanism without source-context checks.
- **Textually improved ≠ artistically better.** Fixing specific lines may remove a flaw without improving the whole script.
- **Editorial taste ≠ audience retention.** Do not report viewing-rate, popularity, emotional impact or production quality without appropriate independent evidence.
- **Accepted proposal ≠ applied revision ≠ approved screenplay ≠ authorized production.** Preserve each distinct human decision.
- **Critic independence:** a second pass by the same model is **not** an independent reader; it must re-open both versions and the protected source constraints, seek counterexamples, and report review identity/limits. External independent readers are optional for personal changes but needed for defensible product-level quality claims.
- **Stop conditions:** block canonical screenplay-to-storyboard handoff on unapproved screenplay revision, confirmed applicable hard-gate `BLOCK`, required unresolved continuity contradiction, or unverified mandatory dependency. A review-only request may finish with issues open, clearly labeled. Quick Storyboard does not gain a new screenplay gate.
- **Knowledge usage:** Critic/Revision must actually consult RM-W03 where required; when structural causality or dialogue are evaluated, also consult RM-W01/RM-W02 respectively. Log consulted reference/revision and any missing input; file existence is not consultation.
