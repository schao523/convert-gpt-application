# RM-W01 — Professional Screenwriting Fundamentals
## Reusable professional knowledge for Vibe StorySpirit Director | v0.3.1 FDR-01 DRAFT

**Status:** KR-01 revised knowledge DRAFT; KR-01 revision work authorized by owner, **exact content not yet approved** for production Plugin. **Change scope:** distinctiveness, audience information, timing evidence, source-label clarification.  
**Intended behavioral users:** Story architecture and structural diagnostic tasks in the professional screenwriting workflow; not a forced prerequisite to Quick Storyboard.  
**Provenance:** Newly authored operational knowledge for SW-01, not copied from any published screenplay or screenwriting textbook. Familiar screenwriting terminology is described in original language.  
**Authority boundary:** Practical creative methods, **not** claims of proven audience retention, Scripture exegesis, exact industry acceptance standards, or normative screenwriting law.

## 1. Purpose and operating rules

Support coherent, filmable, emotionally intelligible stories. Diagnose **purpose before formula**. Adapt structure to chosen length, genre, audience and source fidelity rather than enforcing a universal three-act, eight-sequence, Save-the-Cat, or five-beat prescription. Every story-design recommendation must identify *why* a change benefits the user's specific goal and what it risks.

**When to consult:** A new professional story architecture, a substantial premise/character/causal revision, or Critic analysis of structural issues. May be skipped on explicit Quick Storyboard if no professional critique is requested. If unavailable on a required path, flag `REFERENCE_CONSULTATION_UNVERIFIED`; do not falsely claim source-grounded compliance.

## 2. Minimum Story Brief

Require or identify provisional assumptions for:

| Parameter | Why it matters | Good fallback when user does not specify |
|---|---|---|
| Purpose / intended audience | Defines emotional, ethical and complexity boundaries | Ask only when material; otherwise mark provisional |
| Story mode | Bible, inspirational, original, narrative music, etc. | Infer tentatively, verify if biblical truth boundary depends on it |
| Core premise | What changes and why this story matters | Offer 1–2 options, not a fabricated commitment |
| Duration / format | Determines scene economy and dialogue budget | Mark as estimate, never guarantee runtime |
| Tone and constraints | Prevents unwanted satire, sensationalism or moral shifts | Preserve explicit user instructions |
| Source provenance | Separates licensed adaptation, biblical text, and original fiction | Label unknown or unverified |

## 3. Premise & dramatic question

A **premise** is a compressed causal proposition: *a particular person in a particular predicament attempts a consequential action under a meaningful obstacle.* A **logline** expresses the central desire/obstacle/consequence without listing every twist. A **dramatic question** is what the viewer is invited to hope, fear or discover; it need not be mystery or a cliffhanger.

**Diagnostic questions:**
1. Who is acting, rather than merely receiving the plot?
2. What change or decision must occur on screen?
3. What resists that change?
4. What happens if the character does nothing?
5. What is distinctive about the situation or perspective?
6. Does the premise suit this length and audience?

**Example** (original): “An apprentice watchmaker must choose between admitting a costly error and letting her retired mentor take the blame before a family heirloom is delivered.” Stakes are relational and professional, rather than artificially life-threatening.

## 4. Character agency and internal coherence

A **goal** is an observable outcome the character pursues. **Motivation** is why that outcome matters. **Need** is a possible deeper unmet value, fear or mistaken belief; not every short film needs an explicit therapy-like transformation. **Pressure** forces choice; **action** has consequences; **reaction** reveals character. Character arcs may be transformational, revelatory, resistant/tragic, or stable-but-impactful.

Character design checks:
- Separate **what the character wants** from **what the writer wants the audience to learn**.
- Give consequential characters credible knowledge and agency. Do not reduce secondary characters to moral props.
- Check consistency of knowledge, power, ability, relationship, age and setting.
- Characters can behave irrationally, but the script must provide a plausible emotional basis.
- Avoid forcing sentimentality, villainy, redemption or dramatic confession where the source material does not support it.

**Character Card:** `character_id`, visible goal, emotional stake, internal tension (if applicable), choice under pressure, what others know, forbidden contradictions, voice/behavior traits, source fidelity labels.

## 4A. Distinctive story identity, perspective and memorable specificity (KR-01)

A logically complete story can still feel interchangeable. Evaluate **distinctiveness in service of intent**, not novelty for its own sake. Ask: (a) Who experiences the events and what can they know? (b) What specific relationship, place, object, moral tension or contradiction distinguishes this story from a generic premise? (c) What image, action, or choice carries the theme without a speech? (d) Does the ending fulfill the *same* promise the opening made? (e) Would the proposed improvement flatten the creator's quiet, unconventional, or culturally specific voice?

Optional, **author-facing** `story_identity` notes: `narrative_point_of_view`, `distinctive_specifics`, `thematic_tension`, `recurring_motif_if_any`, `protected_voice`, `likely_misreading_or_ambiguity`. These are diagnostic concepts, **not** requirements for every short film or a new runtime schema. A Bible retelling may be distinct through truthful perspective and cinematic selection; inventing sensational facts is never justified to force originality.

**Comparison example (original):** Generic: “An adult learns to forgive a parent after an argument.” More specific without greater spectacle: “While labeling boxes from the closed family tailor shop, an adult discovers that the parent silently kept every school uniform they repaired.” The stronger specificity is a **hypothesis**, not a proven audience preference. Verify whether the keepsakes fit the established family history and author-approved tone.

## 4B. Relationships and information-state ledger (KR-01)

When a reveal, delayed confession, or relationship reversal matters, track knowledge and relationship state **before** and **after** the scene. Keep this ledger compact or omit it for a purely observational piece.

| Scene | Character | What they know before | What they learn / choose | Relationship change | Prohibited contradiction |
|---|---|---|---|---|---|
| SC01 | Apprentice | She damaged the gear; customer collection is in three days | Conceals damage | Mentor still trusts her | Cannot establish mutually agreed delivery as due today without an explained change to the Friday agreement |
| SC03 | Mentor | Watch still stops, cause unknown | Notices apprenticeship mark | Trust becomes uncertain | Cannot know the exact accident time without evidence |

**Decision rule:** A later scene must not rely on knowledge, permission, ability, or relationship status that was never established, unless the script explicitly supplies a credible intervening event. Refer material knowledge contradictions to RM-W03 diagnosis and regression verification.

## 5. Conflict and stakes

Conflict is the **friction between an intention and resistance**, not necessarily shouting or physical danger. Types include person vs person, person vs circumstances/institution, competing duties, self-conflict, limited time/resources, or competing values.

For every major scene, ask:
- What does someone want *now*?
- What stands in the way *now*?
- What action changes the situation?
- What gets harder, clearer or emotionally costlier after this scene?

Stakes can be physical, relational, ethical, spiritual, emotional, reputational or practical. Keep them proportionate. A small grounded loss is often more powerful than an unsupported catastrophic threat.

## 6. Cause and effect, not event stacking

A scene is narratively necessary when it changes the state of the story or the viewer's understanding. Prefer “**because this happened, the character chooses X, causing Y**” over a chain of disconnected “and then” events. Check cause/effect on three levels:

- **Plot:** The action follows facts established or newly revealed.
- **Character:** The choice follows plausible knowledge, motive, pressure and capacity.
- **Audience:** Information is supplied when needed, not withheld to manufacture a false twist.

An event may be deliberately surprising. Surprise becomes *earned* when setup or character logic makes retrospective sense. Do not require a reversal for contemplative or Bible-faithful stories.

## 7. Story structures as optional lenses

Use the least prescriptive shape that clarifies the intended experience:

- **Goal–obstacle–choice–consequence:** efficient for short dramas with a protagonist pursuing something concrete.
- **Discovery/revelation:** effective when audience meaning changes through disclosed fact, without a mechanical reversal.
- **Contrast/transformation:** useful for inspirational or visual storytelling (before/after, expectation/reality).
- **Journey/encounter:** good for experiential or Bible storytelling; events may unfold through observation rather than escalating confrontation.
- **Contemplative/poetic:** suitable for visual meditation; image, sound and motif carry significance; may not require verbal dialogue.

If a model conflicts with Scripture or author-approved story identity, **the model yields**, not the source.

## 8. Beat sheet and filmic scene design

A **beat** is a meaningful microchange in goal, power, emotion, information or possibility. A **scene** is a continuous dramatic unit of place/time/action (not necessarily one shot). Do not conflate scenes with shots or Start Frames.

Proposed beat record:

```
beat_id: B04
scene_id: SC03
prior_state: mentor suspects the error is a factory defect
character_goal: apprentice wants mentor to sign off immediately
pressure: a buyer arrives early
visible_action: apprentice hesitates, then opens the repaired case
turn: mentor sees the apprentice's personal mark on the replacement part
post_state: concealment is no longer safe
source_boundary: ORIGINAL_FICTION
```

**Scene test:** entry condition → active objective → obstacle → action/reaction → turn/result → next-scene consequence. A quiet reflection scene may still change understanding or establish essential mood; do not discard it solely for low action.

## 9. Timing and production economy

Estimate rather than promise. Read-aloud pace, movement, pauses, emotion and edits change actual duration. Every scene should record *estimated* seconds, dialogue load, performance complexity, location/character count, and continuity-critical props. For multi-scene scripts include a **scene-by-scene estimated-duration subtotal and total**, indicate `timing_confidence` (HIGH/MEDIUM/LOW) with its basis (read aloud, planned performance, or text-only guess), and revise estimates after a table-read when possible. Do not infer actual generation runtime from a page count. A screenplay may require fewer scenes than a storyboard requires shots. A single screenwriting scene can translate into multiple shots.

**Short format check:** If runtime is too long, first consider redundancy, repeated exposition and too many subplots—do not mechanically increase cutting speed or delete necessary emotional breath. Respect budget and filmability while preserving story meaning.

## 10. Biblical adaptation safeguards

Scripture is the governing source when user requests biblical narrative; script craft **does not authorize invention as fact**. Require the actual passage/source for exact quotations. Distinguish:

1. `SCRIPTURE_EXACT` — verified verbatim wording with passage/version/source.
2. `SCRIPTURE_PARAPHRASE` — faithful non-quoted rendering, labeled.
3. `INTERPRETATION` — explanatory theological reading, not stated as literal narration.
4. `DRAMATIC_ELABORATION` — imagined stage direction or dialogue, explicitly marked as non-scriptural **in screenplay/source metadata and approval notes**. Whether viewers must see a screen label depends on the approved release plan and applicable rules; the internal source label alone is not a universal on-screen caption instruction.

If the proposed dramatic structure requires an invented motive, conversation, or sequence contradicted by Scripture, reject/revise it. When a passage is not verified, abstain from exact quotation and mark `SOURCE_UNVERIFIED`. Preserve unresolved theological choices for user review.

## 11. Output pattern: Story Architect

Produce a compact, actionable `Story Architecture Report`:

1. Confirmed user intent and constraints vs provisional assumptions.
2. One-sentence premise/logline and optional alternate.
3. Character Cards (protagonist + essential others).
4. Central question, stakes and consequence of inaction.
5. Ordered beats: each with reason and scene consequence.
6. Ending/outcome and emotional meaning; no mandatory surprise.
7. Duration/location/role complexity assumptions.
8. Bible/source provenance, value constraints, unresolved gaps.
9. Suggested writing improvements with tradeoffs; record narrative point of view, distinctive story identity and protected creative choices when relevant.
10. Audience information/relationship-state map for a significant reveal, and estimated scene-by-scene running time with confidence when duration is a material limit.
11. Gate decision needed before major departures from owner intent.

## 12. Failure patterns and corrective diagnosis

| Failure | Diagnostic evidence | Better intervention |
|---|---|---|
| Passive protagonist | Things happen to character but they never decide | Add meaningful choice unless story deliberately observational |
| Arbitrary reversal | New decisive information with no setup or credible origin | Seed earlier cue or replace twist with honest recognition |
| Stakes inflation | Huge threat introduced without causal support | Restore proportionate personal stake |
| Theme as sermon | Characters state lesson but don't act on it | Show tested value through costly choice |
| Repetitive beats | Multiple scenes restore same situation | Merge redundant scenes or create meaningful change |
| Unfilmable exposition | Internal diagnosis with no behavior or cinematic expression | Translate to observed action, dialogue, sound, or purposeful narration |
| Bible distortion | Invented miracle/dialogue presented as quotation | Restore source and label staging as imaginative |

## 13. Consultations, conflicts and evidence

Use RM-W01 as *advisory professional knowledge* in professional planning; when drafting dialogue, continue with RM-W02 and existing dialogue formats; for critique, combine RM-W03 and applicable Bible/inspirational rubric. In conflicts over Bible truth, verified Scripture and relevant biblical-evaluation reference take precedence over screenwriting convenience. In conflicts over approved owner intent, stop for human decision. File existence is not evidence of actual consultation. Store/use meaningful evidence of which knowledge was consulted for the specific artifact.

## 14. Completion check

A structurally ready outline answers: protagonist/agency, stakes, causal path, scene function, ending intention, filmability, source/rights status, and unresolved consequential questions. Readiness is **not** equal to final artistic excellence or human approval.

## KR-01 knowledge use evidence

**Applicability:** RM-W01 is **required** when the professional Architect builds or materially changes story structure, and when Critic diagnoses causality/character agency. A pure Quick Storyboard bypass does not newly require it. Reports should identify what concept was applied (e.g., information-state ledger at SC01/SC03), the inspected reference ID/revision, and limits. File presence is not consultation. **A better-looking output is not proof of audience engagement.**
