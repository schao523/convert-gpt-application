# RM-P03 — Target Capability & Adaptation Standard
## Provider-Neutral Professional Reference for Capability Resolution, Compatibility Assessment, and Target-Aware Production Export

**Reference ID:** RM-P03  
**Version:** 1.0-DRAFT  
**Status:** Professional Knowledge Reference — awaiting owner approval  
**Primary behavioral users:** WF-05/L2, WF-05/L3; IM-10, IM-11, IM-12; supporting IM-13  
**Depends on:** RM-P01 Canonical Production Specification Standard; RM-P02 Portable Production Package Standard  
**Authority scope:** Normalized target-capability representation, current-capability evidence handling, canonical-to-target adaptation, compatibility/degradation assessment, and target-export provenance  
**Out of scope:** Permanent provider feature tables, volatile model lists, authentication details, direct execution lifecycle, provider SDK implementation

---

# 1. Purpose

RM-P03 defines how **酷 Vibe 動畫故事導演 Vibe StorySpirit Director** evaluates an external production target and converts a canonical Production Specification into a target-ready derived export without corrupting the canonical source of truth.

The standard answers five questions:

1. **What can the current target actually do?**
2. **What evidence supports that capability claim?**
3. **How does canonical production intent map into the target's supported inputs and controls?**
4. **What canonical requirements are lost, weakened, or transformed?**
5. **How should the resulting target export remain traceable to the canonical project?**

RM-P03 does not define one permanent list of what Runway, Veo, Pika, Luma, or any other provider supports.

Those facts are volatile.

RM-P03 defines the **professional method for discovering, representing, assessing, and adapting to current capability**.

---

# 2. Core Principle

Target adaptation is a transformation of canonical intent, not a redesign of the project.

The canonical relationship is:

> **Canonical Production Specification**  
> → **Target Capability Profile**  
> → **Compatibility Assessment**  
> → **Target Adaptation**  
> → **Derived Target Export**

A target adapter must never silently change approved creative meaning merely to make a request acceptable to a provider.

When the target cannot faithfully realize a canonical requirement, the adapter must expose the gap.

---

# 3. Provider Identity Is Not Capability

The name of a provider is not enough to determine production capability.

A provider may expose:

- multiple models;
- multiple generation modes;
- different duration limits;
- different media inputs;
- different aspect ratios;
- different audio support;
- different reference-image behavior;
- different regional/plan/API availability.

Therefore:

> `provider = runway`

does **not** prove:

> `supports_end_frame = true`

Capability must be established from current evidence.

---

# 4. Target Identity Model

A target should be identified at a level specific enough to support reliable adaptation.

A Target Identity may conceptually include:

- provider;
- product/service;
- model or model family when relevant;
- interface type;
- capability mode;
- region/availability context if material;
- account/runtime context if material;
- profile revision;
- capability-evidence timestamp.

Example conceptual target identity:

```yaml
target:
  provider: "ExampleVideo"
  service: "Developer API"
  model_family: "Model-X"
  capability_mode: "IMAGE_TO_VIDEO"
  profile_revision: "2026-10-06"
```

The exact physical representation is implementation-specific.

---

# 5. Target Capability Profile

A Target Capability Profile is a normalized description of what a particular current production target can accept and produce.

A profile should contain:

1. target identity;
2. capability-evidence provenance;
3. supported generation modes;
4. accepted input modalities;
5. output characteristics;
6. parameter/control support;
7. media/reference limits;
8. duration constraints;
9. format constraints;
10. audio behavior;
11. known limitations;
12. confidence/currentness state.

---

# 6. Capability Evidence

A capability claim should be supported by current evidence.

Acceptable evidence sources may include:

- live runtime capability discovery;
- authoritative provider documentation;
- authoritative provider API schema;
- provider SDK metadata;
- connected tool capability declaration;
- verified runtime observation;
- another approved authoritative source.

The exact source mechanism is not prescribed by RM-P03.

---

# 7. Capability Evidence States

Every material capability claim should have a confidence/currentness state.

Recommended values:

## 7.1 VERIFIED_CURRENT

Current authoritative evidence supports the capability.

## 7.2 VERIFIED_RUNTIME

The connected runtime/tool itself reports or demonstrates the capability.

## 7.3 DOCUMENTED

Authoritative documentation supports the capability, but runtime availability has not been directly verified.

## 7.4 STALE

Evidence exists but is old enough that current capability cannot safely be assumed.

## 7.5 CONFLICTING

Authoritative or runtime evidence conflicts.

## 7.6 UNKNOWN

Capability could not be established.

If a material capability is UNKNOWN or STALE, the adapter must not invent support.

Use:

`TARGET_CAPABILITY_UNVERIFIED`

when necessary.

---

# 8. Capability Categories

A normalized Target Capability Profile should evaluate relevant capability categories.

Not every target needs every category.

---

## 8.1 Generation modes

Possible normalized modes include:

- `TEXT_TO_VIDEO`
- `IMAGE_TO_VIDEO`
- `FIRST_LAST_FRAME_TO_VIDEO`
- `REFERENCE_GUIDED_VIDEO`
- `VIDEO_TO_VIDEO`
- `EXTEND_VIDEO`
- `CHARACTER_PERFORMANCE`
- `LIP_SYNC`
- `AVATAR_VIDEO`
- `COMPOSITE_OR_POST_PROCESS`

These names express semantic capability classes rather than provider syntax.

---

## 8.2 Image input capability

Evaluate whether the target supports:

- Start Frame;
- End Frame;
- multiple image references;
- character references;
- style references;
- location/object references;
- masks;
- control images where applicable.

Also evaluate:

- count limits;
- file formats;
- dimensions;
- size limits;
- role restrictions.

---

## 8.3 Video input capability

Evaluate support for:

- source video;
- video extension;
- video transformation;
- motion reference;
- character-performance driving video;
- temporal reference.

---

## 8.4 Text prompt capability

Evaluate whether the target supports:

- positive text prompt;
- negative prompt;
- structured prompt fields;
- separate camera/motion controls;
- prompt weighting;
- prompt length limits;
- system/provider-specific prompt syntax.

Do not assume that more text always produces better fidelity.

---

## 8.5 Camera control capability

Evaluate whether camera behavior can be controlled through:

- natural-language prompt;
- explicit control fields;
- preset motion;
- no direct control.

Possible camera concepts include:

- static;
- pan;
- tilt;
- dolly;
- truck;
- crane;
- orbit;
- zoom;
- handheld character;
- rack-focus-like behavior.

If camera behavior is prompt-only, that is weaker than an explicit guaranteed parameter and should be treated accordingly.

---

## 8.6 Motion control capability

Evaluate support for:

- subject action;
- environmental motion;
- temporal ordering;
- motion intensity;
- motion reference;
- keyframes;
- pose/motion guidance.

---

## 8.7 Character consistency capability

Evaluate support for:

- character reference image;
- multiple character references;
- persistent identity;
- reusable character profile;
- face/identity locking;
- consistency across generations.

If consistency is probabilistic rather than guaranteed, the capability profile should reflect that uncertainty.

---

## 8.8 Audio capability

Evaluate support for:

- native audio generation;
- dialogue generation;
- narration;
- music;
- ambience;
- sound effects;
- synchronized speech;
- lip sync;
- separate audio input.

Canonical audio intent must remain preserved even if the target does not support native audio.

---

## 8.9 Duration capability

Evaluate:

- minimum duration;
- maximum duration;
- fixed duration choices;
- incremental duration choices;
- extension capability;
- scene stitching behavior.

A target that supports only fixed 5-second clips does not fully support a canonical 8-second exact-duration requirement.

---

## 8.10 Aspect ratio capability

Evaluate:

- supported ratios;
- custom ratio support;
- landscape;
- portrait;
- square;
- resolution-linked ratio constraints.

---

## 8.11 Resolution and quality controls

Evaluate support for:

- resolution;
- quality tiers;
- frame rate where controllable;
- upscale;
- output format;
- watermark behavior if material.

---

## 8.12 Seed / reproducibility controls

Evaluate:

- fixed seed;
- reproducible generation;
- deterministic variation controls;
- no seed control.

Seed support is a capability, not a guarantee of exact reproducibility.

---

## 8.13 Edit / extension capability

Evaluate whether a generated clip can be:

- extended;
- re-edited;
- restyled;
- inpainted;
- reframed;
- interpolated;
- continued from final frame.

---

# 9. Capability Strength

A target capability should distinguish not only whether something exists, but **how strongly it is supported**.

Recommended support levels:

## 9.1 NATIVE_EXPLICIT

The target exposes a dedicated parameter/control for the requirement.

## 9.2 NATIVE_REFERENCE

The target supports the requirement through dedicated media/reference inputs.

## 9.3 PROMPT_GUIDED

The requirement can be expressed only through prompt language.

## 9.4 INDIRECT

The requirement may be approximated through a workaround.

## 9.5 UNSUPPORTED

The capability is not supported.

## 9.6 UNKNOWN

Current support cannot be established.

This distinction is important because:

> prompt-guided camera movement is not equivalent to an explicit camera-control parameter.

---

# 10. Capability Profile Example

Illustrative only:

```yaml
target:
  provider: "ExampleVideo"
  service: "Web/API"
  model_family: "Model-X"
  profile_revision: "2026-10-06"

evidence:
  source_type: "authoritative_documentation"
  state: VERIFIED_CURRENT
  checked_at: "2026-10-06T18:00:00+08:00"

generation_modes:
  TEXT_TO_VIDEO: NATIVE_EXPLICIT
  IMAGE_TO_VIDEO: NATIVE_REFERENCE
  FIRST_LAST_FRAME_TO_VIDEO: UNSUPPORTED

inputs:
  start_frame:
    support: NATIVE_REFERENCE
    max_count: 1
  character_reference:
    support: UNSUPPORTED

camera:
  support: PROMPT_GUIDED

audio:
  native_audio: UNSUPPORTED

duration:
  allowed_seconds: [5, 10]

aspect_ratio:
  supported:
    - "16:9"
    - "9:16"

seed:
  support: NATIVE_EXPLICIT
```

The example demonstrates normalized semantics, not a mandated schema.

---

# 11. Canonical Requirement Extraction

Before adaptation, the adapter must extract relevant canonical requirements from RM-P01 production data.

For each requirement, identify:

- requirement category;
- value;
- strength;
- scene;
- relevant asset;
- whether exact or flexible;
- whether target adaptation may alter representation.

Example:

```yaml
canonical_requirement:
  id: S03-DURATION
  category: duration
  value: 8
  acceptable_range: [6, 8]
  strength: IMPORTANT
```

---

# 12. Requirement-to-Capability Mapping

Each material canonical requirement should be mapped to one or more target capabilities.

Examples:

| Canonical requirement | Target capability |
|---|---|
| Start Frame | image input / image-to-video |
| End Frame | first-last-frame support |
| slow dolly-in | camera control / prompt-guided camera |
| exact dialogue | native speech / lip-sync / external audio workflow |
| same character identity | character reference / identity consistency |
| 8-second duration | duration capability |
| 16:9 | aspect ratio capability |
| ambient sound | native audio or external audio path |

The mapping must be explicit enough to support compatibility assessment.

---

# 13. Compatibility Classification

Every material canonical requirement should receive a compatibility result.

Canonical classifications:

## 13.1 FULLY_SUPPORTED

The target can represent the requirement without material semantic loss.

Examples:

- target supports the requested aspect ratio exactly;
- target accepts the required Start Frame;
- target supports exact duration within allowed constraints.

## 13.2 PARTIALLY_SUPPORTED

The target can approximate the requirement, but fidelity is reduced or uncertain.

Examples:

- camera move is only prompt-guided;
- exact duration must be rounded;
- character consistency is probabilistic;
- native audio is absent but external post-production can preserve audio intent.

## 13.3 UNSUPPORTED

The target cannot represent the requirement adequately.

Examples:

- required End Frame but target has no End Frame or equivalent workflow;
- required native lip-synced dialogue but target has no applicable capability and no accepted fallback.

## 13.4 TARGET_CAPABILITY_UNVERIFIED

Current target support cannot be established.

This is not equivalent to UNSUPPORTED.

It is an evidence limitation.

---

# 14. Compatibility Outcome at Scene Level

A scene-level compatibility result should summarize material requirements.

Recommended overall states:

- `FULLY_SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `UNSUPPORTED`
- `TARGET_CAPABILITY_UNVERIFIED`

The scene-level state should be determined by the most consequential unresolved requirement, not by simple numeric averaging.

For example:

- 9 preferred details supported;
- 1 REQUIRED character-identity constraint unsupported.

Overall result should be `UNSUPPORTED`, not 90% compatible.

---

# 15. Constraint Strength and Compatibility

Use RM-P01 constraint strength:

- REQUIRED;
- IMPORTANT;
- PREFERRED.

A compatibility engine should evaluate severity accordingly.

## 15.1 REQUIRED + UNSUPPORTED

Normally blocks faithful target export unless the user explicitly accepts degradation or revises the canonical specification.

## 15.2 IMPORTANT + PARTIALLY_SUPPORTED

May proceed with visible degradation warning.

## 15.3 PREFERRED + UNSUPPORTED

May proceed if omission does not materially alter meaning.

The adapter must not silently downgrade REQUIRED to PREFERRED.

---

# 16. Semantic Loss Record

Whenever a canonical requirement is not FULLY_SUPPORTED, create a semantic loss/degradation record.

It should conceptually include:

- canonical requirement ID;
- canonical value;
- target capability;
- compatibility result;
- practical effect;
- fallback;
- whether user approval is required;
- whether canonical source remains unchanged.

Example:

```yaml
degradation:
  requirement_id: S03-END-FRAME
  result: UNSUPPORTED
  effect: "Target cannot enforce the approved final composition."
  fallback:
    option: "Generate without End Frame and review result manually."
  approval_required: true
  canonical_source_changed: false
```

---

# 17. Adaptation Decision Order

A professional target-aware adapter should proceed in this order:

1. Read canonical production requirements.
2. Resolve current target capability.
3. Verify capability evidence currentness.
4. Map canonical requirements to target capabilities.
5. Classify compatibility.
6. Identify degradation.
7. Determine whether user approval is needed.
8. Transform supported canonical intent into target representation.
9. Produce derived target export.
10. Preserve provenance and compatibility report.

Do not generate the target prompt first and justify it afterward.

---

# 18. Prompt Specialization Principle

Prompt generation is a **derived adaptation operation**.

The adapter should specialize prompt content according to the target mode.

---

## 18.1 Text-to-video adaptation

A text-to-video prompt may need to carry more canonical visual information because no Start Frame may exist.

Possible components:

- subject;
- environment;
- composition;
- style;
- action;
- camera;
- lighting;
- temporal behavior.

---

## 18.2 Image-to-video adaptation

When a Start Frame already establishes:

- subject appearance;
- composition;
- environment;
- lighting;
- style;

the adaptation should avoid unnecessary redundant visual restatement where the target's prompting behavior benefits from motion-focused instruction.

The prompt may emphasize:

- subject action;
- environmental motion;
- camera movement;
- temporal transition;
- performance evolution.

The exact specialization depends on current target guidance.

RM-P03 defines the adaptation principle, not provider-specific prompt wording.

---

## 18.3 First/Last-frame adaptation

If the target supports both start and end visual anchors, the adapter may separate:

- start state;
- transition/motion;
- end state.

If the target does not support End Frame, the loss must remain visible.

---

# 19. Parameter Mapping

Canonical production semantics may map to target parameters.

Examples:

```text
canonical.aspect_ratio
→ target.ratio

canonical.duration
→ target.duration

canonical.start_frame
→ target.image_input

canonical.seed_preference
→ target.seed
```

The mapping should preserve provenance:

> target parameter value derived from canonical requirement X.

Target-only parameters may be introduced as derived metadata, but they must not become canonical creative meaning.

---

# 20. Parameter Normalization

Target syntax may differ from canonical semantics.

Example:

Canonical:

`aspect_ratio = 16:9`

Target A:

`"1280:720"`

Target B:

`"landscape"`

Target C:

`"16:9"`

The adapter may transform syntax while preserving canonical meaning.

---

# 21. Value Adjustment

Sometimes the target supports the semantic category but not the exact canonical value.

Example:

Canonical:

`duration = preferred 8 sec; acceptable 6–8 sec`

Target:

only 5 or 10 seconds.

The adapter must not silently choose 10.

It should:

1. classify compatibility;
2. explain difference;
3. suggest options;
4. obtain approval if material.

---

# 22. Fallback Types

Fallbacks should be explicit and categorized.

Possible fallback classes:

## 22.1 PARAMETER_FALLBACK

Adjust a parameter within approved flexibility.

Example:

8 sec preferred, 7 sec supported and acceptable.

## 22.2 WORKFLOW_FALLBACK

Move unsupported capability to another production stage.

Example:

target lacks native audio → preserve video generation target, add audio in post-production.

## 22.3 ASSET_FALLBACK

Use additional reference asset to compensate.

Example:

character consistency weak → add stronger character reference if target supports it.

## 22.4 TARGET_FALLBACK

Recommend another target with better capability fit.

## 22.5 MANUAL_FALLBACK

Provide human-operable instructions rather than automated target export.

## 22.6 NO_ACCEPTABLE_FALLBACK

The target cannot faithfully realize a REQUIRED requirement.

---

# 23. Target Selection Recommendation

When the user asks the application to recommend a target, recommendation should be based primarily on capability fit.

Relevant dimensions may include:

- required generation mode;
- Start/End Frame needs;
- reference image needs;
- character consistency;
- audio/dialogue;
- duration;
- aspect ratio;
- camera control;
- execution availability.

Do not recommend solely based on brand popularity.

A recommendation should be explainable:

> “Target A is a better fit because this scene requires X, Y, and Z.”

---

# 24. Multi-Target Export

One canonical project may produce multiple target exports.

Each export must remain independent.

Example:

```text
Canonical Scene S03
├── Runway Export R2
├── Veo Export V1
└── Generic Manual Export G4
```

The target exports may differ in:

- prompts;
- parameters;
- asset usage;
- duration;
- workflow;
- degradation.

But all must reference the same canonical source revision unless explicitly updated.

---

# 25. Generic Target Profile

RM-P03 recommends support for a generic/manual target profile.

A Generic Target Profile does not pretend to know provider capabilities.

Its purpose is to produce:

- target-neutral prompt material;
- Start Frame references;
- motion instructions;
- camera instructions;
- dialogue/audio notes;
- duration;
- aspect ratio;
- asset checklist;
- compatibility notes.

This preserves usability when:

- no adapter exists;
- provider capability cannot be verified;
- the user wants to use a website manually.

---

# 26. Target Export Contract

A target-derived export should conceptually include:

1. target identity;
2. capability-profile revision;
3. capability-evidence provenance;
4. source project/scene revision;
5. compatibility summary;
6. degradation records;
7. adapted prompt(s);
8. target parameters;
9. required target assets;
10. execution readiness;
11. export state.

---

# 27. Target Export State

Recommended semantic states:

- `DRAFT`
- `READY_FOR_MANUAL_USE`
- `READY_FOR_EXECUTION`
- `BLOCKED`
- `STALE`
- `SUPERSEDED`
- `TARGET_CAPABILITY_UNVERIFIED`

An export created from stale capability evidence should not be marked fully current.

---

# 28. Target Export Provenance

Every target export should answer:

- Which canonical project revision produced it?
- Which canonical scene revision produced it?
- Which target profile was used?
- Which capability evidence supported it?
- When was it generated?
- Which degradation decisions were accepted?

Illustrative:

```yaml
target_export:
  export_id: EXP-S03-TARGETA-R2
  source_project_revision: 1.4
  source_scene_revision: 2
  target_profile_revision: "2026-10-06"
  compatibility: PARTIALLY_SUPPORTED
  accepted_degradations:
    - S03-END-FRAME
```

---

# 29. Currentness and Refresh

Target capability profiles should be refreshable independently from canonical production specifications.

When capability evidence changes:

- canonical project remains unchanged;
- target profile may be updated;
- existing exports may be re-evaluated;
- old exports may become stale.

This separation is fundamental to long-term maintainability.

---

# 30. Stale Capability Evidence

A capability profile should be treated as stale when:

- provider documentation changed materially;
- model/version changed;
- connected runtime capability changed;
- profile age exceeds an implementation-defined confidence threshold;
- observed runtime behavior conflicts with the profile.

RM-P03 does not mandate a fixed number of days for staleness.

The implementation should use context-appropriate currentness rules.

---

# 31. Conflicting Capability Evidence

When evidence conflicts:

1. prefer more authoritative/current evidence;
2. preserve the conflict record;
3. do not silently choose the more convenient capability claim;
4. mark material uncertainty;
5. use `TARGET_CAPABILITY_UNVERIFIED` when necessary.

---

# 32. Human Approval Conditions

Human approval is normally required before continuing when:

- a REQUIRED canonical requirement is not FULLY_SUPPORTED;
- an IMPORTANT requirement is materially degraded;
- duration or aspect ratio changes beyond approved flexibility;
- dialogue/audio fidelity materially changes;
- character identity risk is high;
- Start/End Frame constraints are removed;
- a fallback changes production workflow materially.

Minor loss of PREFERRED details may not require explicit approval if application policy allows.

---

# 33. Adaptation Without Canonical Mutation

The adapter may create:

- shortened prompt;
- expanded prompt;
- parameter transformation;
- multiple target jobs;
- post-production instructions;
- auxiliary reference usage.

But it must not write those target accommodations back into canonical data as though they were approved creative decisions.

If the user chooses to change canonical intent, that must occur through an explicit revision path.

---

# 34. Example Compatibility Assessment

Illustrative:

```yaml
scene_id: S03
target: ExampleVideo/Model-X

requirements:

  start_frame:
    canonical_strength: REQUIRED
    capability: NATIVE_REFERENCE
    result: FULLY_SUPPORTED

  end_frame:
    canonical_strength: IMPORTANT
    capability: UNSUPPORTED
    result: UNSUPPORTED
    effect: "Final composition cannot be constrained directly."

  camera_dolly:
    canonical_strength: IMPORTANT
    capability: PROMPT_GUIDED
    result: PARTIALLY_SUPPORTED
    effect: "Camera movement is probabilistic."

  audio_dialogue:
    canonical_strength: REQUIRED
    capability: UNSUPPORTED
    result: PARTIALLY_SUPPORTED
    fallback: "Generate silent video, preserve exact dialogue for post-production."

overall:
  result: PARTIALLY_SUPPORTED
  approval_required: true
```

---

# 35. Example Target Export

Illustrative:

```yaml
export_id: EXP-S03-X01

source:
  project_revision: 1.4
  scene_revision: 2

target:
  provider: ExampleVideo
  model_family: Model-X
  mode: IMAGE_TO_VIDEO

capability_profile:
  revision: 2026-10-06
  evidence_state: VERIFIED_CURRENT

compatibility:
  overall: PARTIALLY_SUPPORTED

adapted_inputs:
  start_frame: IMG-S03-START
  prompt: >
    The child slowly turns toward the road as a light breeze moves the leaves.
    Camera slowly dollies inward as recognition grows in the child's expression.
  duration: 10
  ratio: "16:9"

degradation:
  - requirement: S03-END-FRAME
    result: UNSUPPORTED
  - requirement: S03-DIALOGUE
    result: EXTERNAL_POST_PRODUCTION

state: READY_FOR_MANUAL_USE
```

This is a derived target artifact.

It does not redefine canonical Scene S03.

---

# 36. Anti-Patterns

## 36.1 Static provider truth table

Bad:

A permanent reference says:

> Provider X always supports 10-second video and native audio.

Why it fails:

- provider capabilities change;
- models differ;
- regions/accounts/interfaces differ.

Correct:

Use current capability evidence.

---

## 36.2 Brand-first adaptation

Bad:

User says “Runway,” and the application immediately creates a Runway-style prompt without capability assessment.

Correct:

Resolve target capability profile first.

---

## 36.3 Prompt-first adaptation

Bad:

Generate target prompt first, then infer compatibility afterward.

Correct:

Assess canonical requirements → capabilities → degradation → adaptation.

---

## 36.4 Silent parameter coercion

Bad:

Canonical 8 seconds becomes 10 seconds because target supports 10.

Correct:

Report adjustment and approval need.

---

## 36.5 Canonical rewrite

Bad:

Target lacks End Frame, so canonical End Frame is deleted.

Correct:

Keep End Frame canonically; mark target export degradation.

---

## 36.6 Capability hallucination

Bad:

Assume a target supports native audio because another model by the same provider does.

Correct:

Use target-specific current evidence.

---

## 36.7 False equivalence

Bad:

Treat `PROMPT_GUIDED` and `NATIVE_EXPLICIT` control as equal.

Correct:

Represent capability strength.

---

# 37. Relationship to RM-P01

RM-P01 defines:

> what the production scene canonically means.

RM-P03 defines:

> whether and how a current target can realize that meaning.

RM-P03 must never replace RM-P01 as the source of truth.

---

# 38. Relationship to RM-P02

RM-P02 defines the portable production package.

RM-P03 may add target-derived exports into the package.

The target export should remain separate from canonical package artifacts.

---

# 39. Relationship to RM-P04

RM-P03 stops at:

> target-ready derived export + compatibility state.

RM-P04 begins when the application moves toward:

> actual external execution.

RM-P04 governs:

- approval;
- submission;
- job state;
- result;
- failure/retry.

---

# 40. Relationship to RM-P05

RM-P05 governs:

- target export identity;
- provenance;
- stale/superseded state;
- source relationships;
- result lineage.

RM-P03 supplies the adaptation-specific metadata that RM-P05 tracks over time.

---

# 41. Consultation Guidance for the Application

Consult RM-P03 whenever the application:

- recommends a production target;
- evaluates whether a target is suitable;
- converts canonical production intent into target-specific inputs;
- generates a target-specific prompt;
- maps canonical parameters to provider syntax;
- evaluates semantic loss;
- classifies FULL/PARTIAL/UNSUPPORTED;
- uses current provider/runtime capability evidence;
- decides whether user approval is required for target degradation;
- prepares a target export for manual use or direct execution.

Do not use RM-P03 as a permanent table of provider facts.

Current provider facts must come from current authoritative evidence.

---

# 42. Professional Standard Summary

A professional target-aware adapter must be:

- **capability-driven**
- **evidence-grounded**
- **provider-neutral at the canonical layer**
- **explicit about uncertainty**
- **explicit about semantic loss**
- **constraint-aware**
- **traceable**
- **refreshable**
- **non-destructive**
- **human-governed when degradation matters**

The canonical question is not:

> “How do I write a prompt for this provider?”

It is:

> **“Given the approved canonical production requirements and the target's current verified capabilities, what can be realized faithfully, what must be transformed, what will be degraded, and what derived target input should be produced without changing the source of truth?”**
