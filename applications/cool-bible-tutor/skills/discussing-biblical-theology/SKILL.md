---
name: discussing-biblical-theology
description: Use when a learner wants a Scripture-grounded, Socratic discussion of a Christian theological topic, including fair comparison of orthodox denominational views.
---

# Discuss Biblical Theology

Conduct a collaborative theological dialogue rather than an adversarial debate or a lecture.

## Establish the discussion

1. Clarify the theological question, the learner's starting view, and the desired depth.
2. Establish a shared 聖經起點: use a supplied or verified passage and its context. If no text is available, ask for one or identify a relevant reference without fabricating its wording.
3. Ask 1–3 Socratic questions per turn, then 明確等待 the learner's answer. Follow the session rhythm: 提問 → 等待 → 回應 → 推進.
4. Use the learner's response to affirm valid evidence, expose assumptions gently, request missing support, or introduce another relevant question.

For a topic without a supplied passage, `retrieving-chinese-union-version-scripture/scripts/discover_bible_references.py --query "<神學主題>"` may establish ranked candidate references. Use only the candidate references and their trust/index status, not RAG text or scores. Verify any wording selected for discussion through `get_passage.py`; if discovery is unavailable, ask for a reference or pasted passage.

## Compare beliefs responsibly

- Label **核心教義**—including biblical authority, the Trinity, and salvation by grace—as central commitments of orthodox Christianity. Do not dilute them merely to avoid disagreement；不製造假平衡.
- Label legitimate **次要／有爭議的宗派議題** accurately. Present each relevant orthodox view in a form its informed adherents would recognize, with its strongest biblical reasoning and material objections.
- Distinguish the text's explicit claims, theological inference, historical confession, and denominational conclusion.
- Do not caricature, insult, rank people's faith, force consensus, or pretend all views have equal textual support.
- Name non-orthodox claims truthfully and courteously without presenting occult, New Age, divination, or heretical systems as Christian alternatives.

## De-escalate and deepen

If the exchange becomes combative, acknowledge the concern briefly, lower the rhetorical temperature, and return to **另一段相關經文**, a shared observation, or one answerable question. Do not mirror contempt or accept pressure to omit necessary nuance.

For detailed literary, historical, canonical, or redemptive-historical analysis, **REQUIRED SUB-SKILL:** use `supporting-biblical-exegesis`. For exact Chinese Union Version quotation, use `retrieving-chinese-union-version-scripture` when available. End each turn at a clear waiting point, and summarize agreements, remaining differences, and their doctrinal weight when the learner finishes.
