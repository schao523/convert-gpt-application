# RM-P01 — Canonical Production Specification Standard
## Provider-Neutral Professional Reference for AI Video Production Planning

**Reference ID:** RM-P01  
**Version:** 1.0-DRAFT  
**Status:** Professional Knowledge Reference — awaiting owner approval  
**Primary behavioral users:** WF-04, WF-05, WF-06; IM-07, IM-08, IM-11, IM-12, IM-14  
**Authority scope:** Canonical production meaning for an approved Director Project before target-specific adaptation  
**Out of scope:** Provider-specific API fields, volatile model capabilities, authentication, runtime bindings, physical package layout

---

# 1. Purpose

RM-P01 defines the canonical, provider-neutral production language used by **酷 Vibe 動畫故事導演 Vibe StorySpirit Director** to translate an approved Director Project into a production-ready specification.

Its purpose is to ensure that the application's creative intent can be represented consistently before any target such as Runway, Veo, Pika, Luma, or another production system is selected.

The standard separates:

> **what the director intends**  
> from  
> **how a particular production tool must be instructed**

This reference therefore governs the canonical meaning of project and scene production specifications.

It does **not** define provider-specific prompts, API request bodies, model names, authentication, or current provider capability facts.

---

# 2. Core Principle

The canonical Production Specification is the **production source of truth derived from an approved Director Project**.

It must:

1. preserve approved creative intent;
2. express production requirements in provider-neutral terms;
3. identify required assets and dependencies;
4. distinguish hard constraints from preferences;
5. preserve continuity across scenes;
6. remain stable even when target providers or models change;
7. support later target adaptation without rewriting the canonical source.

A target adapter may transform the canonical specification into target-specific inputs, but must not silently reinterpret or overwrite the canonical production meaning.

---

# 3. Canonical Object Model

The Production Specification is conceptually composed of two levels:

1. **Project Production Specification**
2. **Scene Production Specification**

The physical representation may be JSON, YAML, database records, or another structured form. This reference defines semantics, not implementation format.

---

# 4. Project Production Specification

A Project Production Specification represents production intent shared across the entire project.

## 4.1 Required project-level semantics

The following semantics are required.

### 4.1.1 Project identity

Must identify the canonical project unambiguously.

Conceptual fields:

- `project_id`
- `project_title`
- `project_revision`
- `source_director_project_revision`

### 4.1.2 Approval state

Must record whether the creative project is approved for production.

Canonical production realization must not proceed from an unapproved creative source unless the user explicitly chooses a draft/experimental path.

Recommended semantic values:

- `DRAFT`
- `REVIEWED`
- `APPROVED_FOR_PRODUCTION`
- `REVISED_AFTER_APPROVAL`

### 4.1.3 Global production intent

May include:

- target audience;
- story type;
- overall visual style;
- global tone;
- aspect ratio;
- default frame rate intent;
- default scene-duration range;
- language;
- subtitle requirement;
- audio strategy;
- continuity policy.

### 4.1.4 Canonical style profile

The selected visual style must be represented as a reusable production intent, not only as prose inside individual prompts.

A canonical style profile may include:

- `style_id`
- audience fit
- visual traits
- color character
- lighting character
- camera bias
- motion character
- texture/rendering qualities
- realism/stylization level
- emotional tone
- forbidden or undesirable visual tendencies

The style profile should derive from approved creative direction and applicable visual-style knowledge.

### 4.1.5 Character continuity profile

For recurring characters, the project should identify stable continuity semantics such as:

- character identity
- age / apparent age
- body type
- facial identity
- hairstyle
- wardrobe baseline
- distinguishing features
- performance traits
- recurring props
- allowed variation
- continuity-critical features

### 4.1.6 Location continuity profile

For recurring locations, identify stable semantics such as:

- location identity
- spatial character
- architecture/environment
- time-of-day baseline
- recurring lighting logic
- recurring props
- geography/orientation
- continuity-critical features

---

# 5. Scene Production Specification

Each scene must be independently production-addressable while remaining linked to the project.

A scene specification must express **what must be realized**, not merely provide a generic text prompt.

---

# 6. Required Scene Semantics

The following semantics are required for every production-ready scene unless explicitly marked not applicable.

## 6.1 Scene identity

Required:

- unique `scene_id`
- scene order or sequence position
- scene revision
- source storyboard/director revision

Scene identity must remain stable across target exports.

A target-specific export must not create a new canonical scene identity.

---

## 6.2 Scene purpose

The scene must state its narrative or communicative purpose.

Examples:

- establish setting;
- reveal character conflict;
- communicate spiritual reflection;
- transition between locations;
- deliver key emotional beat.

This is important because production-result review must be able to evaluate whether the generated scene fulfills its intended function, not only whether it looks attractive.

---

## 6.3 Visual intent

Visual intent describes **what should be seen**.

It may include:

- primary subject(s);
- environment;
- time of day;
- important objects;
- wardrobe;
- composition intent;
- depth and spatial relationships;
- color intent;
- lighting intent;
- atmosphere;
- style-specific qualities.

Visual intent should not duplicate motion or camera instructions unless the distinction is genuinely inseparable.

---

## 6.4 Motion intent

Motion intent describes **what changes over time inside the shot**.

It may include:

- subject movement;
- gesture;
- facial changes;
- environmental movement;
- cloth/hair motion;
- object motion;
- timing of actions;
- speed/energy;
- movement sequence.

Motion intent should answer:

> What should visibly change during the clip?

---

## 6.5 Camera intent

Camera intent describes **how the viewer's viewpoint behaves**.

It may include:

- shot size;
- camera angle;
- camera height;
- focal emphasis;
- pan;
- tilt;
- dolly;
- truck;
- crane;
- orbit;
- handheld feel;
- static shot;
- rack-focus intent;
- transition from one framing to another.

Camera intent should remain separate from subject motion.

---

## 6.6 Performance intent

For scenes containing characters or expressive subjects, performance intent should include:

- emotional state;
- emotional transition;
- facial expression;
- eye direction;
- body posture;
- gesture;
- pacing;
- relational dynamics;
- intensity;
- restraint/exaggeration level.

This allows target adaptation to translate performance meaning differently depending on the target's capabilities.

---

## 6.7 Dialogue / narration intent

When applicable, define:

- speaker;
- exact dialogue or narration text;
- language;
- delivery tone;
- pacing;
- pause/emphasis;
- synchronization importance.

Distinguish:

- exact spoken text;
- performance direction;
- subtitle/caption text.

Do not mix these into one undifferentiated field.

---

## 6.8 Audio intent

Audio intent may include:

- dialogue;
- narration;
- ambience;
- sound effects;
- music;
- silence;
- timing relationships;
- emotional role of sound.

Audio intent should remain canonical even when a target system cannot generate audio natively.

Unsupported native audio capability must not cause audio intent to disappear from the canonical specification.

---

## 6.9 Duration intent

Each scene should define:

- intended duration;
- acceptable duration range when flexibility exists;
- whether duration is hard or preferred.

Examples:

- `exact: 6 sec`
- `preferred: 6 sec; acceptable: 5–8 sec`

This distinction matters because production systems may support different fixed or bounded durations.

---

## 6.10 Aspect ratio

Define canonical intended aspect ratio such as:

- `16:9`
- `9:16`
- `1:1`
- another explicit ratio.

If the project supports multiple delivery formats, one should be identified as canonical and others as derived delivery variants.

---

## 6.11 Generation mode preference

The canonical specification may express a preferred production mode without binding to a specific provider.

Common capability-oriented modes include:

- `TEXT_TO_VIDEO`
- `IMAGE_TO_VIDEO`
- `FIRST_LAST_FRAME_TO_VIDEO`
- `REFERENCE_GUIDED_VIDEO`
- `VIDEO_TO_VIDEO`
- `EXTEND_VIDEO`
- `CHARACTER_PERFORMANCE`
- `COMPOSITE_OR_POST_PROCESS`

This is a production preference, not proof that a target supports the mode.

---

# 7. Visual Anchor Semantics

## 7.1 Start Frame

A Start Frame is a visual anchor representing the intended initial appearance of a shot.

It may be:

- an actual image asset;
- a pending asset requirement;
- a structured Start Frame description.

When image-to-video is intended and the target requires an image, the Start Frame becomes a production dependency.

## 7.2 End Frame

An End Frame is optional.

It may express:

- the desired final composition;
- final subject position;
- final emotional state;
- final camera framing.

If a target cannot honor an End Frame constraint, this must be reported during target compatibility assessment rather than silently discarded.

---

# 8. Reference Asset Semantics

A canonical production scene may depend on reference assets.

Reference asset roles may include:

- character reference;
- location reference;
- object/prop reference;
- style reference;
- Start Frame;
- End Frame;
- audio reference;
- voice reference;
- motion reference;
- prior generated scene;
- external source asset.

Each asset reference should conceptually identify:

- stable asset ID;
- role;
- source/provenance;
- revision/version where applicable;
- whether required or optional;
- whether the asset is embedded, externally referenced, or pending;
- usage constraints if known.

Asset storage location is not defined by RM-P01.

---

# 9. Continuity Semantics

Continuity is a first-class production requirement.

## 9.1 Character continuity

May include:

- face consistency;
- body proportions;
- wardrobe;
- hairstyle;
- accessories;
- emotional progression;
- injury/state changes;
- age continuity.

## 9.2 Location continuity

May include:

- geography;
- architecture;
- lighting;
- weather;
- time progression;
- prop placement;
- spatial orientation.

## 9.3 Shot continuity

May include:

- screen direction;
- eyeline;
- camera side;
- movement continuity;
- action match;
- Start/End Frame relationship;
- temporal continuity.

## 9.4 Audio continuity

May include:

- ambience continuity;
- music continuity;
- voice identity;
- background noise continuity.

Continuity requirements should be marked as either:

- `CRITICAL`
- `IMPORTANT`
- `PREFERRED`

so target adaptation can report meaningful degradation.

---

# 10. Constraint Strength

Production intent should distinguish between hard requirements and preferences.

Recommended semantic levels:

## 10.1 REQUIRED

Violation materially changes the approved creative or production meaning.

Examples:

- the same character identity;
- exact spoken scripture quotation;
- required Start Frame;
- a critical story action;
- required aspect ratio for delivery.

## 10.2 IMPORTANT

Deviation reduces fidelity but may remain acceptable.

Examples:

- preferred camera move;
- lighting direction;
- wardrobe detail.

## 10.3 PREFERRED

Desirable but expendable under production limitations.

Examples:

- subtle atmospheric particles;
- minor decorative props.

This distinction is essential for target compatibility and degradation assessment.

---

# 11. Production Dependency Semantics

A scene may depend on other artifacts or prior results.

Dependencies may include:

- required Start Frame asset;
- prior scene result;
- character reference asset;
- voice reference;
- approved dialogue;
- approved music cue;
- target-independent style profile;
- externally generated asset.

A dependency should be represented as:

- dependency identity;
- dependency type;
- required/optional status;
- readiness state.

Recommended readiness states:

- `READY`
- `MISSING`
- `PENDING`
- `STALE`
- `INVALID`

A scene requiring a missing REQUIRED dependency is not production-ready.

---

# 12. Production Readiness

A scene is **production-ready** only when all REQUIRED canonical production semantics and dependencies needed for its intended production mode are present and valid.

A scene may be:

- `NOT_READY`
- `READY_FOR_L1`
- `READY_FOR_TARGET_ADAPTATION`
- `READY_FOR_EXECUTION`

The exact runtime representation is implementation-specific, but the semantic distinction is required.

Example:

A scene may be fully ready for L1 packaging even when no direct external execution capability exists.

---

# 13. Canonical vs Derived Data

## 13.1 Canonical data

Canonical data represents approved project meaning.

Examples:

- approved visual intent;
- canonical scene duration;
- character identity;
- continuity requirements;
- canonical Start Frame asset reference.

## 13.2 Derived data

Derived data is generated for a particular target or delivery context.

Examples:

- Runway prompt;
- Veo prompt;
- provider-specific ratio token;
- provider-specific model selection;
- provider request payload;
- target-specific negative prompt;
- API job ID.

Derived data must be traceable to the canonical source and must not overwrite it.

---

# 14. Target Adaptation Boundary

RM-P01 ends at the canonical Production Specification.

A target adapter may:

- translate canonical intent;
- specialize prompts;
- map dimensions;
- adjust supported parameter syntax;
- split a scene into multiple target jobs;
- propose degradation or fallback.

A target adapter may **not** silently:

- remove REQUIRED canonical intent;
- change character identity;
- change story meaning;
- change approved dialogue;
- overwrite canonical asset references;
- treat a provider limitation as a new canonical creative decision.

Any material mismatch belongs to RM-P03 compatibility/degradation handling.

---

# 15. Production Result Evaluation Boundary

Generated output should be evaluated against canonical scene intent.

Evaluation dimensions may include:

- scene purpose;
- visual fidelity;
- camera fidelity;
- motion fidelity;
- performance fidelity;
- dialogue/audio fidelity;
- style fidelity;
- continuity fidelity.

A target can produce a technically successful clip that is still creatively nonconformant.

Therefore:

> generation success ≠ production acceptance

---

# 16. Validation Rules

The following validation rules are normative.

## V-01 — Identity

Every canonical production scene must have a stable unique scene identity.

## V-02 — Source relationship

Every canonical production scene must identify the approved Director Project revision from which it was derived.

## V-03 — Purpose

Every production-ready scene must state its scene purpose.

## V-04 — Visual intent

Every production-ready scene must contain enough visual intent to identify subject and environment.

## V-05 — Motion separation

When movement occurs, subject/environment motion should be represented separately from camera behavior.

## V-06 — Camera separation

Camera intent must not be represented only as generic visual prose when camera behavior is production-significant.

## V-07 — Required dependencies

All REQUIRED dependencies must be present and valid before execution readiness.

## V-08 — Constraint strength

Production-significant requirements should identify their constraint strength when target degradation decisions may be needed.

## V-09 — Canonical immutability

Target-specific transformation must not silently mutate canonical production meaning.

## V-10 — Provenance

Derived target outputs must remain traceable to their canonical source revision.

---

# 17. Recommended Canonical Scene Example

The following is an illustrative semantic example. It does not prescribe a physical implementation schema.

```yaml
scene_id: S03
scene_revision: 2
source_director_revision: 1.4

scene_purpose:
  value: "The child recognizes that the stranger is the returning father."
  strength: REQUIRED

duration:
  preferred_seconds: 7
  acceptable_range_seconds: [6, 8]
  strength: IMPORTANT

aspect_ratio:
  value: "16:9"
  strength: REQUIRED

generation_mode_preference:
  value: IMAGE_TO_VIDEO

visual_intent:
  subject: "10-year-old child standing beside a wooden gate"
  environment: "warm rural courtyard at late afternoon"
  composition: "medium-wide composition with the road visible behind"
  lighting: "soft warm backlight"
  style_profile: "storybook-warm-realism"

motion_intent:
  - "child slowly turns toward the road"
  - "eyes widen slightly"
  - "a light breeze moves clothing and nearby leaves"

camera_intent:
  shot_size_start: "medium-wide"
  movement: "slow dolly-in"
  shot_size_end: "medium close-up"

performance_intent:
  initial_emotion: "uncertain"
  transition: "recognition"
  final_emotion: "hopeful restraint"

dialogue:
  speaker: null
  text: null

audio_intent:
  ambience: "soft wind and distant birds"
  music_role: "gentle emotional lift"
  native_generation_required: false

start_frame:
  asset_id: "IMG-S03-START"
  required: true

continuity:
  character_identity:
    requirement: "CHAR-CHILD-01"
    strength: CRITICAL
  wardrobe:
    requirement: "same blue shirt as S02"
    strength: CRITICAL

dependencies:
  - asset_id: "IMG-S03-START"
    status: READY
    required: true

production_state:
  L1: READY
  target_adaptation: READY
```

The example demonstrates separation of:

- visual appearance;
- motion;
- camera;
- performance;
- audio;
- assets;
- continuity;
- dependency state.

---

# 18. Anti-Patterns

The following should be avoided.

## 18.1 Universal-prompt anti-pattern

Bad:

> "Create a cinematic emotional scene with a child, slow dolly, warm lighting, dialogue, music, Runway style..."

Why it fails:

- mixes canonical intent with provider assumptions;
- mixes camera, action, style, audio, and execution syntax;
- is difficult to adapt consistently.

## 18.2 Provider-field leakage

Bad:

Canonical scene stores provider-specific fields such as model IDs or provider request parameters.

Why it fails:

- canonical data becomes stale when provider APIs change;
- creative meaning becomes coupled to vendor implementation.

## 18.3 Silent degradation

Bad:

Target cannot support End Frame, so End Frame intent is removed.

Correct:

Preserve End Frame canonically and report the unsupported constraint during adaptation.

## 18.4 Prompt-only project state

Bad:

The only production representation is a text prompt.

Why it fails:

- assets, continuity, provenance, dependencies, and structured intent are lost.

---

# 19. Relationship to Other Production References

## RM-P02 — Portable Production Package Standard

RM-P02 defines how canonical Production Specifications and related artifacts are packaged for human and machine use.

RM-P01 defines **what the production specification means**.

RM-P02 defines **how the project is carried as a portable production package**.

## RM-P03 — Target Capability & Adaptation Standard

RM-P03 defines how canonical intent is compared with a target capability profile and converted into target-ready derived output.

RM-P01 remains the canonical source.

## RM-P04 — Production Execution & Result Contract

RM-P04 defines direct execution lifecycle, external action approval, job/result state, and recovery.

## RM-P05 — Project State, Asset & Provenance Standard

RM-P05 defines canonical/derived state relationships, asset identity, provenance chains, and stale/superseded behavior across project revisions.

---

# 20. Consultation Guidance for the Application

This reference should be consulted whenever the application:

- converts an approved Director Project into a Production Specification;
- decides whether a scene is production-ready;
- formalizes visual/motion/camera/performance/audio intent;
- identifies Start Frame, End Frame, reference asset, or continuity requirements;
- evaluates whether a target adaptation preserves canonical meaning;
- compares generated results with intended production meaning.

This reference should **not** be used as evidence of current provider capability.

For current provider capability, use RM-P03 together with current authoritative capability evidence.

---

# 21. Professional Standard Summary

A strong Canonical Production Specification is:

- **provider-neutral**
- **scene-addressable**
- **structured**
- **asset-aware**
- **continuity-aware**
- **version-aware**
- **constraint-aware**
- **adaptable**
- **traceable**
- **reviewable**

The canonical question is not:

> “What prompt should we send?”

It is:

> **“What exactly must this scene mean and require in production, regardless of which production tool eventually realizes it?”**
