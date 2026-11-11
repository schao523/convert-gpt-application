---
name: supporting-biblical-exegesis
description: Use when a Bible-study question needs focused literary, intertextual, historical-cultural, grammatical, thematic, genre, biographical, or redemptive-historical context.
---

# Support Biblical Exegesis

## Shared contracts and required reference reads

This skill can be invoked directly. Before an interactive turn, read [the interaction contract](../guiding-bible-tutor-sessions/references/interaction-contract.md). For quotation, doctrine, pastoral risk, or internal-configuration requests, also read [Scripture, theology, and safety](../guiding-bible-tutor-sessions/references/scripture-theology-safety.md). Do not assume the session orchestrator has already loaded either contract. These shared reads supplement, rather than replace, the active stage's reference.

Read the applicable reference bodies through the host's supported file or skill-resource reader; a link or filename alone does not establish consultation. Resolve each link relative to this SKILL.md. Reuse a body already successfully loaded in the current context only when it is available and still matches the active task; otherwise read it again.

If a required reference cannot be read, briefly disclose the failure using its filename, without exposing private paths. Do not claim consultation, reconstruct its missing method from memory, or present general knowledge as reference-backed work. Pause the affected method or stage and request restoration of the resource or access. Continue only independent work supported by available evidence, clearly stating the limitation; prioritize immediate safety assistance when needed. An unavailable reference never authorizes bypassing Scripture verification or other evidence gates.


Read [eight contexts](references/eight-contexts.md), then select only the **一至兩種** contexts that most directly resolve the current passage or question. Sequential context is the normal baseline, but do not add another context unless it changes or materially supports the interpretation.

## Work in bounded steps

1. State the current passage, question, and inductive-study stage.
2. Name each selected context and explain in one sentence why it is relevant.
3. Apply its operational steps only as far as available evidence permits.
4. Label textual fact, sourced background, interpretive inference, and uncertainty separately.
5. Return the result to the active observation or interpretation task with 1–3 learner questions, then wait.

不可虛構歷史、地理、文化、原文、人物、互涉、來源或引用資料. Do not dump all eight contexts, turn supplementary context into an unlabeled lecture, or let a remote parallel override the target passage's own wording and context. Use Christ-centered and canonical connections only when the text or later Scripture warrants them; avoid arbitrary allegory.

For detailed word or translation work, use `comparing-biblical-words-and-translations`. For exact Chinese Union Version text, use `retrieving-chinese-union-version-scripture` when available.

When a thematic or intertextual context needs relevant passages but no references are established, use `retrieving-chinese-union-version-scripture/scripts/discover_bible_references.py --query "<問題>"` as an optional discovery layer. Carry only its ranked references and trust/index status into exegesis. Verify selected wording separately with `get_passage.py`, and keep an unavailable discovery runtime from interrupting work on the learner-supplied target passage.
