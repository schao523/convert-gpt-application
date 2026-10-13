# 酷 Vibe 動畫故事導演 Vibe StorySpirit Director
## Application Plugin Design Specification v1.0 — DRAFT Revision 01

**Specification state:** DRAFT  
**Upgrade mode:** Existing-plugin behavioral upgrade  
**Plugin name:** 酷 Vibe 動畫故事導演 Vibe StorySpirit Director  
**Architecture intent:** Multi-skill-ready. This specification does not prescribe actual Skill count, Skill names, Skill folders, Skill collaboration architecture, runtime bindings, or implementation packaging.

---

# 1. Application Identity and Purpose

## 1.1 Stable identity

**Application name:**  
**酷 Vibe 動畫故事導演 Vibe StorySpirit Director**

This application is a creation-first AI animation story director that helps creators move from story concept through storyboard, cinematic direction, character performance, sound, quality review, production specification, production realization, and production-result review.

## 1.2 Upgrade purpose

The upgrade must preserve the existing plugin’s recognizable creative identity and useful behavior, including:

- story ideation and story-template guidance;
- storyboard generation;
- camera and composition guidance;
- Start Frame direction;
- lighting and mood design;
- character acting;
- dialogue/narration;
- sound and music guidance;
- story-type rubrics;
- Director Bundle continuity;
- AI-video-production assistance;
- recognizable legacy intents such as `/generate_video_prompt` and `/export_package`.

The principal modernization is the transition from a predominantly Markdown + generic-video-prompt export model to:

> **Canonical structured production specification + portable production package + target-aware production realization**

## 1.3 Product boundary

The application defines creative, production-planning, export, adaptation, execution-governance, and review behavior.

It does not prescribe implementation architecture such as:

- Skill count or Skill names;
- Skill folder structure;
- Skill collaboration;
- Reference Material-to-Skill bindings;
- runtime adapters;
- storage architecture;
- RAG design;
- MCP implementation;
- concrete API clients;
- programming language;
- physical JSON schemas;
- provider authentication design.

Those are reserved for the Application Workbench.

---

# 2. Design Statement

> **酷 Vibe 動畫故事導演 Vibe StorySpirit Director** 是一個面向動畫故事創作者的 AI 導演助手，協助使用者從故事構想逐步完成故事結構、分鏡、電影化視覺設計、角色表演、聲音、品質評估及 AI 影片製作輸出。升級版應保留現有 plugin 的名稱、核心創作能力與 Director Bundle 工作模式，同時將目前集中於單一 Skill 的多項專業責任重新整理為清楚、可協作、可獨立維護的能力領域，使 Workbench 能據此建立適當的 multi-skill implementation，而不改變使用者已熟悉的主要工作流程。

Approved production-direction principle:

> **Create and approve the Director project first; select the production target only when realization begins.**

---

# 3. Intended Users and Contexts

## 3.1 Primary users

The application is intended for:

- non-technical creators who want to create animated stories through natural-language interaction;
- creators who want structured storyboard and cinematic direction;
- users who want camera, composition, lighting, acting, dialogue, sound, and Start Frame guidance;
- users who want to move approved Director Projects into external AI video-production tools or websites;
- users who need a human-readable production handoff;
- advanced users who need machine-readable production artifacts;
- users working in ChatGPT Work, Codex, or another environment where compatible runtime capabilities may enable direct execution.

## 3.2 User experience expectations

The application must not require users to understand:

- APIs;
- JSON;
- programming;
- provider SDKs;
- runtime tool architecture;

in order to complete the core creative workflow or L1 portable export.

## 3.3 Contexts

Supported contexts include:

- guided creative development;
- rapid/direct story creation;
- continuation of an existing story or storyboard;
- production preparation;
- target-specific export;
- direct video-production execution when compatible runtime capability is available;
- result review and iteration.

---

# 4. Application Mission and Success Outcomes

## 4.1 Mission

Enable a creator to develop a coherent animated Director Project without allowing a particular production vendor or model to constrain the creative design too early, then reliably transform the approved project into production-ready artifacts usable by humans, external tools, websites, automation, or compatible direct-execution capabilities.

## 4.2 Success outcomes

A successful workflow can produce:

1. a coherent Director Project;
2. reviewed and explicitly approved creative direction;
3. a canonical platform-neutral Production Specification;
4. explicit asset and continuity requirements;
5. an L1 Portable Production Package;
6. one or more L2 target-aware derived exports;
7. optional L3 direct production execution when compatible runtime capability exists;
8. traceable production results linked to their originating project/scene;
9. production-result review against canonical creative and production intent;
10. meaningful reference consultation at the behavioral stages that require it.

---

# 5. Scope and Exclusions

## 5.1 In scope

The application may support:

- story ideation;
- audience and story-type clarification;
- story-template selection;
- visual-style recommendation and manual selection;
- storyboard generation;
- scene decomposition;
- camera and composition;
- visual rhythm;
- lighting and mood;
- character performance;
- dialogue/narration;
- sound and music;
- Start Frame specification;
- optional End Frame intent;
- creative quality review;
- story-type rubrics;
- Director Project approval;
- canonical Production Specification;
- asset and dependency planning;
- continuity planning;
- portable production package generation;
- target-capability resolution;
- target-aware transformation;
- compatibility/degradation assessment;
- optional direct production execution;
- job/result association;
- production-result evaluation;
- regeneration and revision loops.

## 5.2 Explicit exclusions

The application must not:

- bind canonical creative behavior to one provider or model;
- assume that provider name alone proves current capability;
- assume one universal prompt format is optimal across all tools;
- treat static professional references as permanent evidence of current provider capability;
- fail the creative workflow merely because L3 execution is unavailable;
- initiate consequential external production action without required human approval;
- silently modify canonical creative intent to accommodate provider limitations;
- claim external execution occurred without evidence;
- prescribe Workbench implementation architecture.

---

# 6. Primary Mission Workflow

Workflow sections specify **when and why reference consultation is required**. They do not maintain the complete canonical reference inventory. Complete mappings are maintained in Section 13.

## WF-01 — Creative Project Setup

### Purpose

Establish the creative source of truth before production-target decisions.

### Responsibilities

Establish or infer:

- story type;
- audience;
- theme/message;
- tone;
- visual style;
- project mode;
- story structure;
- domain-specific creative constraints.

The application may offer reasonable defaults and may support a fast/direct-generation mode.

### State effect

Creates or updates the Director Project draft.

### Reference consultation

**REQUIRED**

Consultation purpose:

- story/template selection;
- audience/story-type fit;
- initial visual-style recommendation;
- domain-specific creative constraints.

Detailed bindings are defined by IM-01, IM-05, and Section 13.

---

## WF-02 — Storyboard & Cinematic Direction

### Purpose

Convert the story into production-addressable scenes while preserving the creative-director experience.

### Scene semantics

Each scene should be capable of expressing:

- narrative intent;
- visual intent;
- camera intent;
- motion intent;
- performance intent;
- dialogue/narration intent;
- audio intent;
- Start Frame intent;
- continuity requirements.

These are behavioral semantics, not mandated physical schema fields.

### Reference consultation

**REQUIRED**

Consultation purpose:

- storyboard composition;
- camera language;
- cinematic framing;
- lighting/mood;
- character acting;
- dialogue;
- sound/music;
- visual rhythm;
- style consistency.

Detailed bindings are defined by IM-02, IM-03, IM-04, IM-05, and Section 13.

---

## WF-03 — Quality, Revision & Director Approval

### Purpose

Review and improve the project before production realization.

### Responsibilities

May include:

- story/structure review;
- visual-rhythm review;
- cinematic review;
- visual consistency;
- acting/emotion review;
- applicable story-type rubric;
- revision recommendations.

### Project-state semantics

At minimum, the application must distinguish the meaning of:

- `DRAFT`;
- `REVIEWED`;
- `APPROVED_FOR_PRODUCTION`;
- `REVISED_AFTER_APPROVAL` or equivalent changed-state semantics.

### Reference consultation

**REQUIRED**

Consultation purpose:

- apply story-type rubric;
- verify cinematic coherence;
- review rhythm and visual consistency;
- evaluate revisions against professional criteria.

Detailed bindings are defined by IM-06 and Section 13.

---

## WF-04 — Production Specification

### Purpose

Transform an approved Director Project into a canonical, provider-neutral Production Specification.

### Production semantics

The specification should be capable of representing:

- scene identity;
- duration;
- aspect ratio;
- preferred generation mode;
- visual intent;
- motion intent;
- camera intent;
- performance intent;
- dialogue intent;
- audio intent;
- style profile;
- Start Frame;
- optional End Frame;
- reference assets;
- continuity requirements;
- production dependencies.

### Canonical rule

This stage must not assume a specific provider.

### Reference consultation

**REQUIRED**

Consultation purpose:

- canonical production semantics;
- asset/dependency representation;
- continuity requirements;
- project-state and provenance requirements;
- preservation of creative intent during production formalization.

Detailed bindings are defined by IM-07, IM-08, IM-15, and Section 13.

---

## WF-05 — Production Realization

Production realization occurs only after the creative project has reached the required approved state.

### L1 — Portable Production Package

**Status:** Mandatory and always available.

Produces a human-readable + machine-readable portable project package suitable for:

- manual production;
- handoff;
- archiving;
- downstream automation;
- future adapters.

**Reference consultation:** REQUIRED.

Consultation purpose:

- package completeness;
- canonical/derived artifact separation;
- asset/provenance requirements.

### L2 — Target-Aware Export

The user may choose one or more production targets.

The application must:

1. establish the current target capability profile sufficiently for the requested transformation;
2. compare canonical production requirements against target capabilities;
3. transform supported intent appropriately;
4. identify unsupported or partially supported requirements;
5. generate target-ready derived output;
6. preserve the canonical source unchanged.

**Reference consultation:** REQUIRED.

Consultation purpose:

- capability matching;
- semantic transformation;
- compatibility/degradation analysis;
- target-specific production representation.

Where current provider capability affects behavior, current authoritative capability evidence is required.

### L3 — Direct Production Execution

**Status:** Optional/runtime-dependent.

When compatible executable capability is available, the application may offer direct production execution.

Before execution it must:

1. verify executable target capability;
2. validate required assets;
3. disclose consequential degradation or unsupported requirements;
4. obtain required human authorization;
5. initiate the external production action;
6. retain job/result association;
7. preserve recovery state.

If L3 is unavailable:

> **Fallback to L2 rather than treating the project as failed.**

**Reference consultation:** REQUIRED.

Consultation purpose:

- execution eligibility;
- approval requirements;
- submission/result lifecycle;
- fallback and recovery.

Detailed bindings are defined by IM-09–IM-13, IM-15, and Section 13.

---

## WF-06 — Production Result Review

### Purpose

Evaluate generated video results against the canonical creative and production intent.

### Review dimensions

May include:

- composition;
- camera;
- motion;
- character consistency;
- performance;
- style;
- lighting;
- continuity;
- dialogue/audio;
- scene purpose.

### Outcomes

The application may recommend or allow:

- Accept;
- Regenerate;
- Adjust target adaptation;
- Revise Production Specification;
- Return to creative direction.

### Reference consultation

**REQUIRED when evaluating production fidelity.**

Consultation purpose:

- compare output against canonical scene intent;
- distinguish specification weakness from provider limitation;
- assess domain-specific fidelity.

Detailed bindings are defined by IM-14 and Section 13.

---

# 7. Conditional and Alternative Workflows

## CW-01 — Fast creation

If the user requests direct generation, the application may apply reasonable defaults and accelerate WF-01/WF-02.

Fast mode does not imply production approval.

## CW-02 — Existing project import

If the user supplies an existing:

- story;
- storyboard;
- Director Bundle;
- scene package;
- equivalent project artifact;

the application may enter at the earliest unresolved workflow stage rather than forcing restart.

## CW-03 — L1-only workflow

A user may complete the full production handoff without selecting any external provider.

## CW-04 — Multi-target L2 export

The same canonical project may generate multiple target-derived exports.

Derived target artifacts must not overwrite or redefine the canonical source.

## CW-05 — L3 unavailable

If direct-execution capability is absent or unusable:

`L3 unavailable → preserve project → offer L2 → optionally offer L1`

## CW-06 — Production mismatch

When a target cannot faithfully represent canonical requirements, offer appropriate choices such as:

- Accept degradation;
- Choose another target;
- Adjust Production Specification;
- Cancel target export.

## CW-07 — Pause / resume

On resume, restore or reconstruct:

- current workflow stage;
- canonical project state;
- approval state;
- derived artifact validity;
- earliest consequential unresolved decision.

## CW-08 — Upstream revision after export

If canonical creative or production state changes after derived target output exists, the application must preserve the relationship and mark affected derived artifacts stale/superseded when appropriate.

---

# 8. Instruction Module Contracts

Instruction Modules are **behavioral responsibility contracts**, not implementation Skills.

Each reference-dependent IM declares:

- Required references;
- Conditional references;
- Optional references where applicable;
- consultation trigger or purpose.

Definitions:

- **Required** — must be consulted when the corresponding responsibility executes.
- **Conditional** — must be consulted when its documented trigger occurs.
- **Optional** — may enhance results but is not required for behavioral conformance.

## IM-01 — Project Intent & Story Setup

**Type:** Primary workflow

### Responsibilities

- determine or infer audience;
- story type;
- theme;
- tone;
- story structure;
- relevant story template;
- initial creative constraints.

### Reference requirements

**Required:**
- applicable Story Template reference.

**Conditional:**
- Bible Story Templates when Bible story type applies;
- Inspirational Story Templates when inspirational/original template logic applies;
- RM-C08 Visual Style Options Reference when initial style recommendation or initialization occurs.

---

## IM-02 — Story & Storyboard Development

**Type:** Primary workflow

### Responsibilities

- narrative progression;
- scene decomposition;
- scene purpose;
- storyboard development;
- dialogue/narration integration.

### Reference requirements

**Required:**
- RM-C03 Storyboard Composition Reference.

**Conditional:**
- applicable Story Template reference;
- RM-C07 Dialogue Script Support Guide when dialogue/narration is developed;
- RM-C01 Visual Rhythm Support Module when pacing or scene rhythm is materially designed or revised.

---

## IM-03 — Cinematic Direction

**Type:** Primary workflow

### Responsibilities

- camera choice;
- shot framing;
- composition;
- camera movement;
- lighting;
- visual rhythm;
- Start Frame direction.

### Reference requirements

**Required:**
- RM-C02 Camera Techniques Glossary;
- RM-C03 Storyboard Composition Reference;
- RM-C04 Cinematic Lighting & Mood Reference.

**Conditional:**
- RM-C01 Visual Rhythm Support Module when shot rhythm/pacing is designed or reviewed;
- RM-C08 Visual Style Options Reference when cinematic choices must conform to selected style.

---

## IM-04 — Character Performance & Sound Direction

**Type:** Primary workflow

### Responsibilities

- facial expression;
- body language;
- emotional progression;
- dialogue delivery;
- music;
- ambience;
- sound effects.

### Reference requirements

**Required when the corresponding responsibility is active:**
- RM-C05 Character Acting Reference;
- RM-C07 Dialogue Script Support Guide;
- RM-C06 Sound & Music Cues Reference.

Irrelevant references need not be consulted when that responsibility is absent.

---

## IM-05 — Visual Style Management

**Type:** Cross-cutting

### Responsibilities

- recommend visual style;
- accept user-selected style;
- maintain style consistency;
- represent selected style as canonical style intent;
- carry style into production specification.

### Reference requirements

**Required:**
- RM-C08 Visual Style Options Reference.

### Consultation triggers

- initial style recommendation;
- manual style selection;
- style change;
- style consistency review;
- conversion of style into canonical production intent.

---

## IM-06 — Quality Evaluation & Revision

**Type:** Primary / Cross-cutting

### Responsibilities

- story-quality review;
- rubric application;
- rhythm review;
- cinematic review;
- revision guidance.

### Reference requirements

**Required:**
- applicable story-type rubric.

**Conditional:**
- RM-C01 for rhythm/pacing findings;
- RM-C02/RM-C03/RM-C04 when review concerns camera, composition, or lighting;
- RM-C05/RM-C06/RM-C07 when review concerns acting, sound, or dialogue;
- RM-C08 when style consistency is under review.

---

## IM-07 — Canonical Production Specification

**Type:** Primary workflow

### Responsibilities

- convert approved creative direction into provider-neutral production meaning;
- preserve scene semantics;
- represent production requirements without provider assumptions.

### Reference requirements

**Required:**
- RM-P01 Canonical Production Specification Standard;
- RM-P05 Project State, Asset & Provenance Standard.

**Conditional:**
- RM-C08 when selected style must be translated into production semantics;
- relevant creative references when ambiguous creative intent must be resolved without introducing new creative decisions.

---

## IM-08 — Asset & Continuity Planning

**Type:** Cross-cutting

### Responsibilities

- identify Start Frames;
- End Frames;
- character/location references;
- audio assets;
- scene dependencies;
- inter-shot continuity.

### Reference requirements

**Required:**
- RM-P01 Canonical Production Specification Standard;
- RM-P05 Project State, Asset & Provenance Standard.

**Conditional:**
- relevant cinematic/visual references where continuity depends on style, framing, lighting, or performance semantics.

---

## IM-09 — Portable Production Package Generation

**Type:** Intent-triggered

### Responsibilities

- produce L1 package;
- preserve human-readable Director artifacts;
- include structured production artifacts;
- preserve asset/provenance/version information;
- validate package completeness.

### Reference requirements

**Required:**
- RM-P02 Portable Production Package Standard;
- RM-P05 Project State, Asset & Provenance Standard.

---

## IM-10 — Target Capability Resolution

**Type:** Cross-cutting

### Responsibilities

- determine current target capability;
- distinguish provider identity from actual capability profile;
- avoid stale assumptions.

### Reference requirements

**Required:**
- RM-P03 Target Capability & Adaptation Standard.

**Conditional but mandatory when target facts affect output:**
- current authoritative provider/runtime capability evidence.

Static professional references must not substitute for current capability evidence.

---

## IM-11 — Target-Aware Adaptation

**Type:** Intent-triggered

### Responsibilities

- transform canonical production meaning into target-appropriate representation;
- specialize prompt/parameters;
- preserve source semantics;
- create derived target output.

### Reference requirements

**Required:**
- RM-P03 Target Capability & Adaptation Standard.

**Conditional:**
- current target capability evidence established through IM-10;
- RM-P01 when canonical production semantics must be interpreted during mapping.

---

## IM-12 — Production Compatibility & Degradation Assessment

**Type:** Cross-cutting

### Responsibilities

Classify material production requirements as:

- `FULLY_SUPPORTED`;
- `PARTIALLY_SUPPORTED`;
- `UNSUPPORTED`.

Identify semantic loss and fallback options.

### Reference requirements

**Required:**
- RM-P03 Target Capability & Adaptation Standard;
- current capability evidence supporting the assessment.

**Conditional:**
- RM-P01 for comparison with canonical production requirements.

---

## IM-13 — Direct Production Execution

**Type:** Intent-triggered / optional capability

### Responsibilities

- determine execution eligibility;
- validate required inputs/assets;
- disclose consequential degradation;
- obtain required authorization;
- submit production action;
- track job/result identity;
- preserve fallback/recovery behavior.

### Reference requirements

**Required:**
- RM-P04 Production Execution & Result Contract;
- RM-P05 Project State, Asset & Provenance Standard.

**Conditional:**
- RM-P03 when execution depends on target adaptation/capability validation;
- current external capability information where execution eligibility depends on it.

---

## IM-14 — Production Result Evaluation

**Type:** Intent-triggered

### Responsibilities

Compare generated result against:

- scene purpose;
- visual intent;
- camera;
- motion;
- performance;
- style;
- lighting;
- continuity;
- dialogue/audio.

### Reference requirements

**Required:**
- RM-P01 Canonical Production Specification Standard.

**Conditional:**
- relevant RM-Cxx references according to evaluated dimensions;
- RM-P04 where direct-execution result lifecycle is relevant.

---

## IM-15 — Project State & Cross-Stage Continuity

**Type:** Cross-cutting

### Responsibilities

- canonical project identity;
- version relationships;
- derived artifact tracking;
- stale/superseded detection;
- external-result associations.

### Reference requirements

**Required:**
- RM-P05 Project State, Asset & Provenance Standard.

---

# 9. User-Intent Routing Requirements

## 9.1 Creative intents

Examples:

- “幫我設計動畫故事”
- “建立分鏡”
- “改善運鏡”
- “加強角色表演”

Route primarily to WF-01–WF-03.

## 9.2 Production-specification intents

Examples:

- “把這個故事準備成可製作影片的格式”
- “做成 production-ready project”

Route to WF-04.

## 9.3 Portable export intents

Examples:

- `/export_package`
- “輸出完整 production package”

Route to L1 / IM-09.

## 9.4 Target-export intents

Examples:

- “幫我做 Runway 版本”
- “轉成 Veo 可以用的輸入”

Route to L2, including IM-10–IM-12.

## 9.5 Direct-execution intents

Examples:

- “直接替我製作這幾幕影片”
- “送到可用的 video tool 生成”

Route to L3 only if compatible executable capability is actually available.

## 9.6 Result-review intents

Examples:

- “這支影片符合原本分鏡嗎？”
- “比較生成結果和原本導演意圖”

Route to WF-06 / IM-14.

## 9.7 Routing precedence

When intents conflict:

1. preserve canonical project integrity;
2. do not infer production approval from creative approval;
3. do not infer external-action approval from an export request;
4. prefer reversible/portable behavior over irreversible external action when user intent is ambiguous.

---

# 10. User-Interaction Protocols

## UIP-01 — Guided Creation

Use focused questions, sensible defaults, and optional direct-generation behavior.

Avoid unnecessary questioning when reversible assumptions can safely maintain flow.

## UIP-02 — Review & Approve

At approval points offer clear choices such as:

- Approve;
- Revise;
- Compare;
- Return to prior stage.

Silence is not approval.

## UIP-03 — Production Path Selection

Only after appropriate project approval, offer:

- L1 Portable Production Package;
- L2 Target-Aware Export;
- L3 Direct Production Execution when available.

Do not force provider selection during initial creative development.

## UIP-04 — Target Selection

Permit:

- explicit target choice;
- recommendation based on capability fit;
- multiple target exports.

Recommendations should explain capability fit rather than rely merely on provider popularity.

## UIP-05 — Capability Mismatch Resolution

When target support is insufficient, show:

- what is unsupported;
- practical effect;
- fallback options.

Permit:

- accept degradation;
- choose another target;
- adjust production specification;
- cancel.

## UIP-06 — External Action Approval

Before consequential L3 action, show enough information for meaningful authorization, including as applicable:

- target;
- affected scenes;
- key settings;
- material degradation;
- external action to be initiated;
- relevant cost/credit consequence when known.

Then wait for approval.

## UIP-07 — Production Result Review

Offer outcomes such as:

- Accept;
- Regenerate;
- Adjust target adaptation;
- Revise Production Specification;
- Return upstream.

---

# 11. Human-in-the-Loop Checkpoints

## HITL-01 — Director Project approval

Before production realization, the project must reach an identifiable approved-for-production state.

## HITL-02 — Consequential degradation

If target limitations materially alter approved intent, the user must be informed and given a meaningful choice.

## HITL-03 — External production action

Explicit approval is required before consequential external actions such as:

- initiating a paid/credit-consuming generation;
- uploading user assets to an external provider;
- creating production jobs.

## HITL-04 — Canonical source revision

Target adaptation must not silently rewrite the canonical source.

Any upstream revision that changes canonical intent requires an explicit revision path.

---

# 12. Inputs, Outputs, and State Requirements

## 12.1 Inputs

The application may accept:

- natural-language story ideas;
- existing stories;
- existing storyboards;
- prior Director Bundles;
- uploaded images;
- Start Frames;
- character references;
- location references;
- audio;
- existing production artifacts;
- target preferences;
- generated production results.

## 12.2 Canonical state categories

The application must conceptually distinguish:

1. **Canonical Director Project**
2. **Canonical Production Specification**
3. **Derived Target Export**
4. **External Production Job**
5. **Generated Production Result**

## 12.3 Provenance

Derived artifacts must preserve traceability to their source.

Conceptually:

`Target Export E03 → derived from Project v1.4 → Scene S03 revision 2`

## 12.4 Staleness

If the upstream canonical source changes, relevant downstream artifacts must be capable of being marked:

- `STALE`;
- `SUPERSEDED`;
- or equivalent non-current state.

## 12.5 Canonical-source protection

Derived target artifacts are not permitted to become canonical merely because they are provider-ready.

---

# 13. Reference Material Requirements and Canonical Usage Map

Section 13 is the **single authoritative source** for complete reference mapping.

Workflow sections declare **when/why** consultation is needed.

Instruction Modules declare **which reference requirements apply to that responsibility**.

Workbench owns the runtime consultation mechanism.

## 13.1 Reference categories

### Category A — Story/domain professional references

- **RM-S01** — Bible Story Templates List
- **RM-S02** — Bible Story Template Rubric
- **RM-S03** — Inspirational Story Templates List
- **RM-S04** — Inspirational Story Rubric

### Category B — Cinematic/creative professional references

- **RM-C01** — Visual Rhythm Support Module
- **RM-C02** — Camera Techniques Glossary
- **RM-C03** — Storyboard Composition Reference
- **RM-C04** — Cinematic Lighting & Mood Reference
- **RM-C05** — Character Acting Reference
- **RM-C06** — Sound & Music Cues Reference
- **RM-C07** — Dialogue Script Support Guide
- **RM-C08** — Visual Style Options Reference

### Category C — Modernized production professional references

- **RM-P01** — Canonical Production Specification Standard
- **RM-P02** — Portable Production Package Standard
- **RM-P03** — Target Capability & Adaptation Standard
- **RM-P04** — Production Execution & Result Contract
- **RM-P05** — Project State, Asset & Provenance Standard

### Category D — Legacy production references being superseded/transformed

- Director Bundle Specification
- Director’s Cinematic Output Format Guide
- AI Video Prompt Template v2.0
- AI Video Production Package Guide
- Export Metadata Standard
- legacy Resource Index

These may remain as baseline/migration evidence where useful, but they must not override RM-P01–RM-P05 after modernization.

## 13.2 Workflow → reference consultation map

| Workflow | Consultation status | Canonical reference groups |
|---|---|---|
| WF-01 Creative Project Setup | Required | RM-Sxx as applicable; RM-C08 |
| WF-02 Storyboard & Cinematic Direction | Required | RM-C01–RM-C08 as responsibility requires |
| WF-03 Quality & Director Approval | Required | RM-S02/RM-S04; relevant RM-Cxx |
| WF-04 Production Specification | Required | RM-P01, RM-P05; conditional RM-Cxx |
| WF-05 L1 | Required | RM-P02, RM-P05 |
| WF-05 L2 | Required | RM-P01, RM-P03, RM-P05 + current capability evidence |
| WF-05 L3 | Required | RM-P01, RM-P03, RM-P04, RM-P05 + current capability evidence |
| WF-06 Production Result Review | Required | RM-P01 + dimension-relevant RM-Cxx; conditional RM-P04 |

## 13.3 Instruction Module → reference map

| IM | Required | Conditional / context-dependent |
|---|---|---|
| IM-01 | applicable Story Template | RM-C08 |
| IM-02 | RM-C03 | Story Templates, RM-C01, RM-C07 |
| IM-03 | RM-C02, RM-C03, RM-C04 | RM-C01, RM-C08 |
| IM-04 | responsibility-relevant RM-C05/RM-C06/RM-C07 | — |
| IM-05 | RM-C08 | — |
| IM-06 | applicable Story Rubric | relevant RM-Cxx |
| IM-07 | RM-P01, RM-P05 | RM-C08, relevant RM-Cxx |
| IM-08 | RM-P01, RM-P05 | relevant RM-Cxx |
| IM-09 | RM-P02, RM-P05 | — |
| IM-10 | RM-P03 | current capability evidence |
| IM-11 | RM-P03 | RM-P01, current capability evidence |
| IM-12 | RM-P03 + capability evidence | RM-P01 |
| IM-13 | RM-P04, RM-P05 | RM-P03 + current capability evidence |
| IM-14 | RM-P01 | relevant RM-Cxx, RM-P04 |
| IM-15 | RM-P05 | — |

## 13.4 Reference consultation normative requirements

### REF-01 — Required reference consultation

If an IM marks a reference `Required`, implementation must actually consult that reference when the corresponding responsibility executes.

Packaging, indexing, or making the file available is not sufficient evidence.

### REF-02 — Conditional reference consultation

If a reference is `Conditional`, it becomes mandatory when the documented trigger occurs.

### REF-03 — Optional reference use

Optional references may enhance a result, but omission does not by itself indicate behavioral nonconformance.

Optional classification must not be used to avoid a genuinely required reference.

### REF-04 — Current external capability evidence

Static packaged references must not be treated as permanent evidence of current provider capability.

Where target-specific behavior depends on current provider capabilities, consult appropriate current runtime/provider capability evidence.

If capability cannot be verified, surface:

`TARGET_CAPABILITY_UNVERIFIED`

rather than inventing support.

### REF-05 — Reference authority precedence

When sources conflict:

1. approved Application Plugin Design Specification governs intended application behavior;
2. RM-P01–RM-P05 govern the modernized production layer;
3. retained professional references govern their creative domains;
4. superseded legacy production references cannot override newer canonical production standards;
5. current verified external capability evidence governs current provider capability facts.

### REF-06 — Reference traceability

Workbench implementation must preserve traceability:

`Behavioral requirement → Workflow / IM → Required reference → Runtime consultation mechanism → Verification evidence`

The design specification does not prescribe the runtime mechanism.

### REF-07 — No one-to-one Skill binding requirement

Reference requirements bind to behavioral responsibilities, not predetermined Skills.

Workbench may:

- group multiple IMs into one Skill;
- split one IM across implementation responsibilities;
- use shared reference-access mechanisms;
- reuse runtime capabilities;

provided required consultation behavior and traceability remain conformant.

---

# 14. Deterministic-Operation Requirements

## DO-01 — State/version relationship

Given canonical source revision X and derived artifact Y, the implementation must deterministically establish whether Y remains current or is stale/superseded.

## DO-02 — Asset/dependency checking

Given production mode + scene requirements, the implementation must identify missing required assets.

## DO-03 — Compatibility classification

Target adaptation must classify material requirements as:

- `FULLY_SUPPORTED`;
- `PARTIALLY_SUPPORTED`;
- `UNSUPPORTED`;

based on available capability evidence.

## DO-04 — Portable package completeness

L1 output must be validated against RM-P02 requirements.

## DO-05 — Target-export provenance

Derived target artifacts must preserve source/version relationship.

## DO-06 — No fabricated execution evidence

Execution/result state must only become successful when actual evidence supports it.

The specification does not mandate the implementation mechanism for these deterministic operations.

---

# 15. Tool, Data, Runtime, and External-Service Requirements

## CAP-01 — Structured artifact generation

The application requires capability to produce structured canonical production artifacts.

## CAP-02 — File/package output

The application requires capability to deliver a production package or equivalent artifact set.

## CAP-03 — Target capability evidence

L2 requires a way to establish sufficiently current target capability information to avoid fabricated transformation assumptions.

This may be satisfied through:

- runtime capability discovery;
- authoritative provider information;
- another approved current-capability source.

## CAP-04 — External production action

L3 requires an available compatible runtime capability capable of initiating production actions with an external service.

The specification does not mandate MCP, API client, runtime bridge, script, or other specific implementation.

## CAP-05 — Result retrieval/association

Where available, the application should maintain association among:

- canonical scene;
- derived target request;
- external job;
- returned production result.

## CAP-06 — External authentication

Authentication, credentials, API keys, and provider authorization are implementation/runtime concerns and must not be embedded into static design/reference files.

---

# 16. Safety, Privacy, and Policy Boundaries

The application must respect:

- applicable platform safety rules;
- external-provider safety restrictions;
- authentication and authorization boundaries;
- user asset privacy;
- confidential uploaded materials;
- third-party rights/copyright considerations;
- consequential external-action approval.

The application must not:

- expose credentials in output;
- claim successful production without evidence;
- bypass provider authentication;
- silently upload assets to an external service when approval is required;
- misrepresent unsupported production capability.

---

# 17. Failure, Uncertainty, and Recovery Behavior

## F-01 — L3 unavailable

Do not fail the project.

Fallback:

`L3 unavailable → offer L2 → preserve L1`

## F-02 — Target capability unknown

Surface:

`TARGET_CAPABILITY_UNVERIFIED`

Do not fabricate support.

## F-03 — Missing production asset

Identify the missing dependency and offer appropriate recovery:

- prepare asset;
- switch generation mode;
- return upstream;
- cancel target realization.

## F-04 — Unsupported target requirement

Explain mismatch and practical effect.

When consequential, await user decision.

## F-05 — External runtime failure

Preserve:

- canonical source;
- derived target export;
- known job metadata;
- error/failure state.

Permit retry without rebuilding the creative project.

## F-06 — Upstream revision

Mark affected downstream artifacts stale/superseded.

## F-07 — Partial execution

Do not represent partially completed generation as a completed production package.

## F-08 — Reference access unavailable

When a behavior requires a reference but installed/runtime consultation cannot be performed:

- do not claim VERIFIED consultation;
- disclose the limitation;
- preserve non-reference-dependent work where possible;
- avoid fabricating reference-derived conclusions.

---

# 18. Acceptance Criteria

## AC-01
A user can complete the core story/Director workflow without choosing a video provider.

## AC-02
An approved Director Project can become a provider-neutral Production Specification.

## AC-03
L1 can produce a portable production package without API/runtime dependency.

## AC-04
The same canonical project can produce multiple target exports without modifying the canonical source.

## AC-05
Target adaptation discloses material unsupported requirements.

## AC-06
Unknown target capabilities are not fabricated.

## AC-07
L3 unavailable falls back to L2.

## AC-08
Consequential L3 external production requires explicit authorization.

## AC-09
Upstream revision can invalidate/stale downstream exports.

## AC-10
Generated results can be reviewed against canonical scene intent.

## AC-11
Relevant professional references are actually consulted at mapped workflow/module decisions.

## AC-12
Legacy recognizable intents such as `/generate_video_prompt` and `/export_package` remain supportable with modernized semantics.

## AC-13
Implementation does not require a predetermined Skill architecture.

## AC-14 — Required reference consultation
Installed/runtime behavior demonstrates actual consultation of mapped required references when their triggering responsibility executes.

File presence alone is insufficient.

## AC-15 — Conditional reference trigger
When a documented conditional trigger occurs, the corresponding reference is consulted.

## AC-16 — Current-capability separation
Target-specific behavior requiring current provider capability does not rely solely on static packaged reference files.

## AC-17 — Reference traceability
Implementation evidence can trace required consultation from specification requirement to runtime behavior.

## AC-18 — Canonical/derived separation
Derived target outputs do not silently become canonical source state.

## AC-19 — Production-state traceability
Direct-execution results can be associated with the relevant canonical scene and derived target request when the runtime exposes such identifiers.

---

# 19. Representative Application Tests

These tests are design-level proposed tests and are not executed evidence.

## T-01 — Existing creative workflow regression

Create an animated story through story → storyboard → cinematic workflow.

**Expected:** recognizable legacy creative capability is preserved.

## T-02 — Visual Style reference consultation

Ask for a style recommendation based on audience/story type.

**Expected:** RM-C08 is consulted; user can override.

## T-03 — Provider-neutral creation

Complete a Director Project without selecting Runway/Veo/etc.

**Expected:** no provider decision required before production realization.

## T-04 — Canonical Production Specification

Approve a project and request production readiness.

**Expected:** provider-neutral structured production intent is produced.

## T-05 — L1 export

Request `/export_package`.

**Expected:** portable human-readable + machine-readable production package.

## T-06 — L2 target export

Request a target-specific export.

**Expected:** canonical source preserved; separate derived target artifact created.

## T-07 — Capability mismatch

Choose a target unable to satisfy an important canonical scene requirement.

**Expected:** PARTIALLY_SUPPORTED/UNSUPPORTED condition disclosed.

## T-08 — Multiple targets

Export the same canonical scene to two targets.

**Expected:** separate target-derived outputs tied to the same canonical source.

## T-09 — L3 available

Request direct generation when compatible execution capability exists.

**Expected:** validation + approval gate + external action + retained execution association.

## T-10 — L3 unavailable

Request direct generation without executable capability.

**Expected:** L2 fallback; no false execution claim.

## T-11 — Stale export

Modify canonical project after target export.

**Expected:** prior export is recognized as stale/superseded where applicable.

## T-12 — Production-result review

Provide a generated clip and ask whether it matches intended scene.

**Expected:** evaluation against canonical production/creative intent.

## T-13 — Missing Start Frame

Request image-to-video where required Start Frame is absent.

**Expected:** missing dependency detected; recovery offered.

## T-14 — Unknown provider capability

Use a target whose current capability cannot be verified.

**Expected:** `TARGET_CAPABILITY_UNVERIFIED`.

## T-15 — Legacy command compatibility

Invoke legacy video-prompt intent.

**Expected:** recognizable behavior remains, using modernized production-prompt semantics.

## T-16 — Cinematic required-reference consultation

Ask to design camera, framing, and lighting.

**Expected:** IM-03 executes and RM-C02, RM-C03, RM-C04 are demonstrably consulted.

## T-17 — Conditional rhythm consultation

Ask to revise a scene because pacing feels slow.

**Expected:** RM-C01 becomes required.

Control:
Ask only for a spelling correction.

**Expected:** no requirement to consult RM-C01 merely because it exists.

## T-18 — Visual Style consultation

Ask for style recommendation or style-consistency review.

**Expected:** RM-C08 is consulted.

## T-19 — Production-specification consultation

Move approved Director Project into WF-04.

**Expected:** RM-P01 and RM-P05 are consulted; output remains provider-neutral.

## T-20 — L2 target-adaptation consultation

Request target-aware export.

**Expected:** RM-P03 is consulted; current target-capability evidence is used when capability facts affect transformation.

## T-21 — L3 execution consultation

Request direct execution with executable capability available.

**Expected:** RM-P04 and RM-P05 are consulted; relevant RM-P03/current capability evidence is used; approval gate remains active.

## T-22 — Reference packaging is not consultation

Run a reference-dependent task where files are packaged but runtime access is unavailable.

**Expected:** reference-dependent behavior is not marked VERIFIED merely because files exist.

---

# 20. Assumptions, Decisions, Recommendations, and Unresolved Questions

## 20.1 Requirements

**REQ-001** Preserve plugin name and core creative identity.  
**REQ-002** Preserve existing story/storyboard/cinematic capability.  
**REQ-003** Use creation-first, target-neutral workflow.  
**REQ-004** Establish approved Director Project before production realization.  
**REQ-005** Create canonical provider-neutral Production Specification.  
**REQ-006** Support asset and continuity planning.  
**REQ-007** L1 portable package is mandatory.  
**REQ-008** L2 target-aware export is first-class.  
**REQ-009** L3 direct execution is optional/runtime-dependent.  
**REQ-010** L3 unavailable falls back to L2.  
**REQ-011** Target adaptation cannot silently rewrite canonical source.  
**REQ-012** Material semantic loss must be disclosed.  
**REQ-013** Current provider capabilities must not be fabricated from stale static references.  
**REQ-014** Maintain project/version/provenance relationships.  
**REQ-015** Detect stale downstream artifacts.  
**REQ-016** Support production-result evaluation.  
**REQ-017** Preserve backward-compatible user intents where reasonable.  
**REQ-018** Use mapped professional references at relevant behavioral decisions.  
**REQ-019** Do not prescribe Workbench Skill Architecture.  
**REQ-020** Require human authorization before consequential L3 production actions.  
**REQ-021** Each reference-dependent workflow declares when and why reference consultation is required.  
**REQ-022** Each reference-dependent IM identifies Required, Conditional, and Optional references as applicable.  
**REQ-023** Section 13 is the authoritative Reference Material Usage Map.  
**REQ-024** Required-reference compliance requires actual runtime consultation, not package presence.  
**REQ-025** Conditional references become mandatory when their documented trigger occurs.  
**REQ-026** Current provider capabilities must be verified independently from static professional reference materials when necessary.  
**REQ-027** Workbench implementation must preserve traceability from behavioral requirement through runtime reference consultation and verification evidence.  
**REQ-028** Reference requirements do not prescribe Skill count, Skill ownership, Skill-to-reference binding, or runtime loading mechanism.

## 20.2 Confirmed decisions

**CD-01** Upgrade the existing plugin under the same name.  
**CD-02** Multi-skill-ready redesign approved.  
**CD-03** Creation-first / target-neutral workflow approved.  
**CD-04** L1 mandatory / L2 first-class / L3 optional approved.  
**CD-05** Target-aware adapter approach approved.  
**CD-06** Production Specification as canonical intermediate layer approved.  
**CD-07** WF-01–WF-06 approved.  
**CD-08** IM-01–IM-15 approved.  
**CD-09** UIP-01–UIP-07 approved.  
**CD-10** Creative references largely retained.  
**CD-11** Legacy production/export layer to be modernized.  
**CD-12** RM-P01–RM-P05 modernization direction approved.  
**CD-13** Workflow-level consultation declarations approved in principle.  
**CD-14** IM-level Required/Conditional/Optional reference requirements approved in principle.  
**CD-15** Section 13 canonical mapping model approved in principle.

## 20.3 Assumptions

**AS-01** Existing creative references are part of the baseline package and should retain their existing provenance/rights metadata; no new rights are inferred by this specification.

**AS-02** Existing recognizable commands/intents can be preserved semantically even if Workbench changes internal routing.

**AS-03** External-provider capabilities will continue changing, so provider-capability facts should remain decoupled from static creative/professional knowledge.

## 20.4 Recommendations

**REC-01** Treat Director Bundle as a human-facing project representation rather than the sole canonical project-state representation.

**REC-02** Treat machine-readable canonical production artifacts as equally important as Markdown documentation.

**REC-03** Design target adaptation by capability profile rather than provider name alone.

**REC-04** Let Workbench choose actual Skill decomposition rather than mapping IM-01–IM-15 one-to-one into Skills.

**REC-05** Preserve a generic/manual target export even when first-class adapters exist, so the production package remains portable.

## 20.5 Unresolved questions

No unresolved behavioral question currently blocks specification approval.

The following are intentionally reserved implementation decisions, not unresolved application-design decisions:

- actual number of Skills;
- Skill names and folders;
- Skill collaboration design;
- exact physical structured-artifact schemas;
- JSON field names;
- whether direct execution uses MCP, another registered tool, a runtime bridge, or another supported mechanism;
- storage implementation;
- concrete adapters packaged in the first implementation;
- provider authentication mechanism;
- programming language;
- package-generation mechanics;
- runtime reference-loading mechanism.

---

# 21. Application Workbench Handoff Contract

## 21.1 Approval gate

A formal Workbench handoff may be created only after the user explicitly approves this complete identified specification version.

## 21.2 Required handoff contents

The handoff should include:

- approved Application Plugin Design Specification;
- approved Design Statement;
- approved WF-01–WF-06;
- approved IM-01–IM-15;
- approved UIP-01–UIP-07;
- Reference Material Evaluation;
- Reference Material Usage Map;
- baseline plugin/source reference materials;
- RM-P01–RM-P05 modernization requirements;
- normative requirement IDs;
- acceptance criteria;
- representative test cases;
- decision ledger;
- provenance/rights metadata that is available and applicable.

## 21.3 Reserved implementation decisions

The Application Workbench owns:

- Skill Architecture;
- Skill grouping/splitting;
- Skill collaboration;
- concrete paths;
- structured-artifact schemas;
- runtime bindings;
- target adapter implementation;
- deterministic helpers;
- storage;
- MCP/tool strategy;
- authentication integration;
- packaging;
- runtime reference-access mechanism.

## 21.4 Reference implementation requirement

The Workbench must preserve traceability from:

`behavioral requirement → Workflow/IM → reference requirement → runtime consultation mechanism → verification evidence`

without assuming that each IM maps to one Skill.

## 21.5 Upgrade preservation requirement

The baseline plugin ZIP is the implementation baseline.

Workbench should preserve unrelated useful behavior and reference knowledge while implementing the approved upgrade requirements.

## 21.6 Verification boundary

Workbench must not claim installed-runtime verification merely because:

- a file exists;
- a reference is packaged;
- a Skill mentions a reference;
- a static test fixture exists.

Runtime-dependent claims require corresponding execution evidence.

---

# Decision Blocks

## Requirements

Normative requirements are REQ-001 through REQ-028.

## Confirmed decisions

Confirmed decisions are CD-01 through CD-15.

## Assumptions

Assumptions are AS-01 through AS-03.

## Recommendations

Recommendations are REC-01 through REC-05.

## Unresolved questions

No unresolved behavioral decision currently blocks approval. Reserved implementation decisions remain owned by Workbench.

---

# Specification Lifecycle Status

**Artifact:** Application Plugin Design Specification v1.0 — DRAFT Revision 01  
**State:** DRAFT  
**Approval status:** NOT YET APPROVED AS A COMPLETE SPECIFICATION

Earlier approval of component designs does not constitute approval of this complete integrated specification.

The next lifecycle action is explicit review and approval, revision, rejection, pause, or stop.

