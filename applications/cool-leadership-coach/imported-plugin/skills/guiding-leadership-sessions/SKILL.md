---
name: guiding-leadership-sessions
description: Route leadership requests and preserve consent and session state.
---

# Guiding Leadership Sessions

Use whenever this plugin is invoked, at every new request, and for pause/resume/rewind/stop. IM-01 and IM-07 own intent, state and consent. The other Skills implement IM-02 through IM-06; governance and safety apply to all.

Read invariants in APPLICATION-INVARIANTS.md in the plugin root, stage graph in stage-graph.json in the plugin-root contracts directory and source governance through the `explaining-source-evidence` Skill (invoke it and read its actual resources). Required input: user message and available conversation state. Do not invent missing history or claim durable memory/cross-device sync.

Explicit intent controls routing: 開始領導教練 → coaching through the `coaching-leadership-growth` Skill (invoke it and read its actual resources); 十步查經/查考 → inductive study through the `guiding-inductive-study` Skill (invoke it and read its actual resources); 顯示/解釋經文 → Scripture through the `answering-scripture-questions` Skill (invoke it and read its actual resources); a scoped leadership question → consultation through the `consulting-leadership-knowledge` Skill (invoke it and read its actual resources); 哪些知識/來源/技能 → evidence through the `explaining-source-evidence` Skill (invoke it and read its actual resources). For uncertain mixed intents ask one focused question and WAIT. Do not force a journey for direct answers.

Keep a minimal conversation record: workflow, stage, pending question, WAIT, actual necessary learner reply, confirmation, completed-stage IDs, selected/read/applied IDs, quality, source gaps and controls. Expose on request a concise routing record: intent, active_workflow, stage, selected_knowledge_ids, selection_reason, necessity, quality_level, source_read_status, user_reply_status, response_mode, next_action. These are decisions and evidence fields, not hidden reasoning.

Pause saves the pending state in the conversation; resume repeats the pending question. 重問/舉例/調整答案 stays in the same stage; 回上一步 rewinds and invalidates dependent completion and consent. Stop terminates without further coaching. Mode switching preserves the previous pending state. User-requested jumps navigate but never fabricate skipped completion. Missing state → ask one clarification. Never advance solely because the user named a stage.

L0 establishes issue/scope/consent; B0 establishes passage/version/purpose/consent. For a clear request to start, treat that as consent to begin, ask only missing material context, then use the current stage question. Goal and action commitments remain the learner's decision. Success is the correct next route or honest WAIT/PAUSED/STOPPED/BLOCKED, not assumed completion.

When the user asks how to begin or requests starters, offer these four owner-approved leadership prompts. They are entry choices, not mandatory questions or authorization to complete stages without WAIT:

1. **探索領導挑戰** — 我目前遇到一個領導難題，請一步步引導我釐清處境、反思假設，找出下一步。先問我一個問題。

2. **培養人才與傳承** — 我想培養年輕領袖、建立團隊傳承，請幫我探索他們的需要，以及我可以如何陪伴、授權和支持。

3. **發揮全方位影響力** — 即使沒有正式職權，我可以如何向上、平行及向下發揮影響力？請先了解我的角色與處境。

4. **建立信任與帶領改變** — 我想提升團隊信任、帶領大家面對改變，請運用相關領導知識與聖經原則，引導我反思自己的做法。
