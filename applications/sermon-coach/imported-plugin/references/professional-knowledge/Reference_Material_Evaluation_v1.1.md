# Reference Material Evaluation v1.1

Application: 講章優化教練  
State: APPROVED — Phase 2  
Update scope: Incorporates RM-04 professional-knowledge extraction and the owner's confirmed packaging rights decision.

## Rights decision

Owner-confirmed: All six supplied source materials may legally be included in the Plugin package for the intended application use.

This owner confirmation establishes the design decision for packaging. The Workbench remains responsible for implementing the approved package without changing the behavioral authority of the sources.

## Evaluation inventory

### RM-01 — 講章優化教練 GPT Instructions

- **Evidence basis:** inspected content
- **Role:** Existing behavior baseline and migration input
- **Topics:** audience, role, sermon review workflow, follow-up, revision review, inductive Bible study, tone, boundaries
- **Behavioral impact:** defines the application’s inherited mission and interaction patterns
- **Format:** Markdown; directly inspectable
- **Authority:** owner-supplied GPT instructions; treated as baseline input, not as an independent theological authority
- **Limitations:** contains implementation-like wording from GPT-era behavior and some duplicated instructions; must be normalized at behavior level
- **Rights:** packaging confirmed by owner
- **Use mode:** design authority / behavioral baseline
- **Primary supported modules:** IM-01 through IM-10

### RM-02 — Integrative Preaching Resource Abstract

- **Evidence basis:** inspected content
- **Knowledge supplied:** vertical, horizontal, and cross-point integration; theological, structural, emotional, and applied integration
- **Relevance:** high
- **Behavioral impact:** improves sermon evaluation beyond surface editing
- **Format:** focused Markdown abstract; highly suitable for direct professional-knowledge use
- **Authority/provenance:** abstract identifies Kenton C. Anderson and the Integrative Preaching model; this evaluation does not independently verify publication metadata
- **Limitations:** derivative abstract, not the full book
- **Quotation policy:** source explicitly says not to quote book wording directly
- **Rights:** package use confirmed; exact quotation from original book remains outside this derivative’s intended use
- **Use mode:** advisory
- **Primary supported modules:** IM-02, IM-03, IM-04, IM-07

### RM-03 — The Unforgettable Sermon Resource Abstract

- **Evidence basis:** inspected content
- **Knowledge supplied:** purpose, theme, call to action, stories, rhetoric, passion, delivery, memorability, opening/closing
- **Relevance:** high
- **Behavioral impact:** strengthens expression, memorability, emotional resonance, and practical response
- **Format:** focused Markdown abstract
- **Authority/provenance:** abstract identifies Edward Reynolds; publication metadata not independently verified here
- **Limitations:** derivative abstract, not the full book
- **Quotation policy:** internal analytical use; not intended for public verbatim quotation from the book
- **Rights:** package use confirmed
- **Use mode:** advisory
- **Primary supported modules:** IM-03, IM-05, IM-07

### RM-04-SOURCE — 歸納釋經法 PDF

- **Evidence basis:** fully inspected across 19 pages
- **Knowledge supplied:** integrated inductive-exegetical method; observation, interpretation, application; ten-step workflow; nine interpretive principles; theological-principle application method
- **Relevance:** critical
- **Behavioral impact:** provides the methodological authority for Scripture review and interactive Bible study
- **Format:** PDF with diagram and structured prose; usable as canonical provenance source but less behavior-ready than focused derivatives
- **Limitations:** OCR/text extraction contains some character noise and typographic corruption; the method itself is still recoverable from the document
- **Rights:** package use and transformation confirmed by owner
- **Use mode:** source authority / advisory
- **Primary supported modules:** IM-02, IM-04, IM-10

### RM-04A — Inductive Exegesis Method Overview

- **Source:** derived only from RM-04-SOURCE
- **Purpose:** method overview and ten-step map
- **Behavioral value:** gives IM-02 and IM-10 a concise authoritative orientation before using focused step references
- **Use mode:** advisory
- **Required when:** selecting or explaining the inductive workflow

### RM-04B — Observation Steps 1–3

- **Source:** derived only from RM-04-SOURCE
- **Knowledge supplied:** 17 observation items, 16 relationship categories, explicit/hidden structure distinction, prose/narrative structure method
- **Behavioral value:** prevents “observation” from becoming generic summarization
- **Use mode:** advisory
- **Required when:** IM-10 runs Steps 1–3; IM-02 needs to evaluate whether sermon interpretation is grounded in textual observation

### RM-04C — Interpretation Steps 4–7

- **Source:** derived only from RM-04-SOURCE
- **Knowledge supplied:** questioning, answering, interpretive principles, synthesis, theme formation
- **Behavioral value:** constrains theological interpretation to an evidence-based path
- **Use mode:** advisory
- **Required when:** IM-02 performs exegetical review; IM-10 runs Steps 4–7

### RM-04D — Application Steps 8–10

- **Source:** derived only from RM-04-SOURCE
- **Knowledge supplied:** theological-principle bridge, cultural-distance tests, SMART application, embodiment
- **Behavioral value:** prevents direct jumps from ancient text to arbitrary modern application
- **Use mode:** advisory
- **Required when:** IM-04 evaluates sermon application; IM-10 runs Steps 8–10

### RM-04E — Inductive Study Questioning Guide

- **Source:** transformation of RM-04-SOURCE only
- **Knowledge supplied:** behavior-ready questions aligned to each of the ten steps
- **Behavioral value:** enables Socratic step-by-step coaching while preserving source methodology
- **Use mode:** advisory
- **Required when:** IM-10 runs interactive full inductive study
- **Limitation:** derivative coaching format; if any question conflicts with RM-04-SOURCE, RM-04-SOURCE governs

### RM-05 — Bible 舊約聖經和合本

- **Evidence basis:** inspected structure and text
- **Knowledge supplied:** Old Testament Chinese Union Version text with verse references
- **Relevance:** critical when Old Testament passages are involved
- **Behavioral impact:** exact verse checking, sermon citation review, Bible-study passage access
- **Format:** large PDF; verse-structured
- **Rights:** package use confirmed by owner
- **Use mode:** exact structured retrieval / exact quotation
- **Primary supported modules:** IM-02, IM-10
- **Limitations:** large source; runtime retrieval architecture is a Workbench decision

### RM-06 — Bible 新約聖經和合本

- **Evidence basis:** inspected structure and text
- **Knowledge supplied:** New Testament Chinese Union Version text with verse references
- **Relevance:** critical when New Testament passages are involved
- **Behavioral impact:** exact verse checking, sermon citation review, Bible-study passage access
- **Format:** large PDF; verse-structured
- **Rights:** package use confirmed by owner
- **Use mode:** exact structured retrieval / exact quotation
- **Primary supported modules:** IM-02, IM-10
- **Limitations:** large source; runtime retrieval architecture is a Workbench decision

## Conflict and precedence rules

1. RM-04A–E are derivatives; **RM-04-SOURCE governs** if wording or method conflicts.
2. RM-02 and RM-03 address homiletics rather than Scripture textual authority; neither overrides biblical text or RM-04 exegesis method.
3. RM-05/RM-06 govern exact CUV verse wording when exact Scripture text is requested or checked.
4. Model general knowledge may supplement only where approved references do not cover the issue; it must not silently replace required professional references.
5. A homiletical recommendation should be distinguished from an exegetical or scriptural claim.

## Duplication

- RM-04A overlaps intentionally with the ten-step overview in RM-04-SOURCE.
- RM-04B/C/D divide RM-04 by behavioral phase, reducing retrieval ambiguity.
- RM-04E repeats concepts from B/C/D only to convert them into interactive coaching prompts; it is not a separate methodological authority.
- RM-02 and RM-03 overlap on emotional connection and application but serve different emphases: integration vs. memorability/expression.

## Remaining gaps

No material gap blocks the currently approved mission. Possible future optional enhancements, not required for this version:
- denomination-specific doctrinal standards;
- original-language tools;
- audience-analysis frameworks beyond the supplied homiletics references.

These are not assumed into the current design.
