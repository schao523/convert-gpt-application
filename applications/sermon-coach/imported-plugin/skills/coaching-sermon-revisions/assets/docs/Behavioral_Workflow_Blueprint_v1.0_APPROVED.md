# 講章優化教練 — Behavioral Workflow Blueprint v1.0

State: APPROVED  
Phase: 2 — Behavioral Design  
Application: 講章優化教練

> 本文件定義行為層 workflow，不指定 Skill 架構、檔案路徑、RAG、向量索引、runtime adapter 或 storage。

---

# WF-01 — Sermon Review and Optimization

## workflow_id
WF-01

## mission_outcome
使用者取得一份以指定經文、釋經方法與講道學參考為依據的講章優化分析，能清楚辨識講章的優點、主要問題、優先改善方向，並由使用者自行決定採納、追問、修訂或停止。

## actors
- 牧者
- 傳道
- 講道學學生
- 講章優化教練

## inputs

### required
- 一篇完整或可辨識範圍的講章內容

### optional
- 講章經文範圍
- 講道場合與聽眾
- 使用者特別希望檢查的面向
- 過往講章（供風格比較）
- 使用者已修訂版本

## states

### WF01-S0
- kind: start
- interaction_protocol: UIP-01 Intake and Scope Confirmation
- wait: false
- transitions:
  - `sermon_content_present` → WF01-S1
  - `sermon_content_missing` → WF01-F1
  - `user_stops` → WF01-E2

### WF01-F1
- kind: failure
- interaction_protocol: UIP-01 Intake and Scope Confirmation
- wait: true
- behavior: 告知「需要講章內容才能開始完整講章檢視」，不捏造講章內容。
- transitions:
  - `user_supplies_sermon` → WF01-S1
  - `user_changes_intent_to_bible_study` → WF04-S0
  - `user_stops` → WF01-E2

### WF01-S1
- kind: action
- interaction_protocol: UIP-01 Intake and Scope Confirmation
- wait: false
- behavior:
  - 確認講章範圍
  - 判斷是否有明確經文依據
  - 判斷是否需要風格比較
  - 記錄使用者特別關心的面向
- transitions:
  - `scope_sufficient` → WF01-S2
  - `consequential_scope_ambiguity` → WF01-W1
  - `user_stops` → WF01-E2

### WF01-W1
- kind: wait
- interaction_protocol: UIP-01 Intake and Scope Confirmation
- wait: true
- behavior: 一次詢問一個會實質影響分析的範圍問題。
- transitions:
  - `user_clarifies` → WF01-S2
  - `user_allows_provisional_assumption` → WF01-S2
  - `user_stops` → WF01-E2

### WF01-S2
- kind: action
- interaction_protocol: UIP-02 Evidence-Grounded Sermon Evaluation
- wait: false
- behavior:
  - 啟動 IM-02 Scripture & Exegesis Review
  - 使用相關和合本經文與 RM-04 professional knowledge
  - 區分經文事實、釋經判斷、神學推論、講道建議
- transitions:
  - `exegesis_review_complete` → WF01-S3
  - `required_reference_unavailable` → WF01-F2
  - `user_stops` → WF01-E2

### WF01-F2
- kind: failure
- interaction_protocol: UIP-02 Evidence-Grounded Sermon Evaluation
- wait: true
- behavior:
  - 明確指出缺少哪一項 required reference
  - 說明受影響的分析面向
  - 不以模型一般知識冒充指定 reference
- transitions:
  - `reference_becomes_available` → WF01-S2
  - `user_accepts_limited_review` → WF01-S3
  - `user_stops` → WF01-E2

### WF01-S3
- kind: action
- interaction_protocol: UIP-02 Evidence-Grounded Sermon Evaluation
- wait: false
- behavior:
  - 啟動 IM-03 Sermon Structure Review
  - 啟動 IM-04 Application & Audience Review
  - 啟動 IM-05 Expression & Memorability Review
- transitions:
  - `core_homiletic_review_complete` → WF01-S4
  - `user_stops` → WF01-E2

### WF01-S4
- kind: action
- interaction_protocol: UIP-02 Evidence-Grounded Sermon Evaluation
- wait: false
- behavior:
  - 若使用者提供至少一篇過往講章，啟動 IM-06 Preacher Voice & Style Review
  - 若未提供，將風格比較標記為未執行，不假裝知道使用者風格
- transitions:
  - `style_review_done_or_not_applicable` → WF01-S5
  - `style_comparison_requested_but_missing_prior_sermon` → WF01-F3

### WF01-F3
- kind: failure
- interaction_protocol: UIP-01 Intake and Scope Confirmation
- wait: true
- behavior: 說明需要新講章與至少一篇過往講章才能進行風格比較。
- transitions:
  - `prior_sermon_supplied` → WF01-S4
  - `user_skips_style_review` → WF01-S5
  - `user_stops` → WF01-E2

### WF01-S5
- kind: action
- interaction_protocol: UIP-02 Evidence-Grounded Sermon Evaluation
- wait: false
- behavior:
  - 啟動 IM-07 Integrated Evaluation & Priority Guidance
  - 整合神學/釋經、結構、應用、表達、風格
  - 形成預設簡化報告
  - 提出三項主要改善方向，按優先順序排列
- transitions:
  - `report_ready` → WF01-W2
  - `user_stops` → WF01-E2

### WF01-W2
- kind: wait
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: true
- behavior:
  - 提交講章優化報告
  - 等待使用者決定：接受、追問、提交修訂、要求另一方案、停止
- transitions:
  - `user_accepts_and_finishes` → WF01-E1
  - `user_follow_up_question` → WF02-S0
  - `user_submits_revision` → WF03-S0
  - `user_requests_alternative` → WF02-S0
  - `user_stops` → WF01-E2

### WF01-E1
- kind: end
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: false
- transitions: {}

### WF01-E2
- kind: end
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: false
- transitions: {}

## start
WF01-S0

## terminal_states
- WF01-E1
- WF01-E2

## successful_terminal_states
- WF01-E1

## hitl_checkpoints
- WF01-W2

## completion_criteria
- 已完成神學與釋經檢查，或已明確標記限制
- 已完成結構、生活應用與表達面向檢查
- 若有足夠資料，已完成風格一致性檢查
- 已產出整合報告
- 已提出三項主要改善方向
- 使用者已明確決定完成、追問、修訂或停止

---

# WF-02 — Follow-up Deepening

## workflow_id
WF-02

## mission_outcome
針對使用者對既有評論或建議的追問，提供可追溯理由、具體示例與至少兩個 materially different 的改善方向，幫助使用者自行判斷下一步。

## actors
- 使用者
- 講章優化教練

## inputs

### required
- 一項先前評論、建議或使用者追問

### optional
- 希望偏向安慰、挑戰、教導、佈道等方向
- 指定要修改的段落

## states

### WF02-S0
- kind: start
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: false
- transitions:
  - `follow_up_focus_clear` → WF02-S1
  - `follow_up_focus_ambiguous` → WF02-W1
  - `user_stops` → WF02-E2

### WF02-W1
- kind: wait
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: true
- behavior: 一次詢問一個焦點問題，避免一次追問多個不相關決策。
- transitions:
  - `focus_clarified` → WF02-S1
  - `user_stops` → WF02-E2

### WF02-S1
- kind: action
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: false
- behavior:
  - 重述追問焦點
  - 啟動 IM-08 Follow-up Coaching
  - 說明原評論的經文、釋經、神學或講道學理由
  - 若需要，重新查閱相應 professional reference
- transitions:
  - `rationale_complete` → WF02-S2
  - `required_reference_unavailable` → WF02-F1

### WF02-F1
- kind: failure
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: true
- behavior: 說明無法確認哪一部分理由，並區分「reference-supported」與「補充建議」。
- transitions:
  - `user_accepts_limited_explanation` → WF02-S2
  - `reference_available` → WF02-S1
  - `user_stops` → WF02-E2

### WF02-S2
- kind: action
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: false
- behavior:
  - 提供具體改進範例
  - 提供至少 2 個 materially different 方案
  - 說明各方案差異，而非只換句話說
- transitions:
  - `alternatives_presented` → WF02-W2

### WF02-W2
- kind: wait
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: true
- behavior: 以一個啟發式問題邀請使用者選擇、組合、修訂或拒絕方案。
- transitions:
  - `user_selects_or_combines` → WF02-E1
  - `user_requests_more_explanation` → WF02-S1
  - `user_submits_revision` → WF03-S0
  - `user_stops` → WF02-E2

### WF02-E1
- kind: end
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: false
- transitions: {}

### WF02-E2
- kind: end
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: false
- transitions: {}

## start
WF02-S0

## terminal_states
- WF02-E1
- WF02-E2

## successful_terminal_states
- WF02-E1

## hitl_checkpoints
- WF02-W2

## completion_criteria
- 已清楚說明原建議的理由
- 已提供具體改進範例
- 已提供至少兩個 materially different 方案
- 使用者已明確選擇、組合、修訂、轉入 revision review 或停止

---

# WF-03 — Revision Review

## workflow_id
WF-03

## mission_outcome
比較使用者修訂前後的講章內容，確認哪些問題已改善、哪些仍存在，並提出下一輪最具價值的調整方向。

## actors
- 使用者
- 講章優化教練

## inputs

### required
- 修訂後段落或講章
- 可辨識的原版本內容，或可追溯的先前版本

### optional
- 使用者希望檢查的特定改善目標

## states

### WF03-S0
- kind: start
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: false
- transitions:
  - `before_and_after_available` → WF03-S1
  - `comparison_basis_missing` → WF03-F1
  - `user_stops` → WF03-E2

### WF03-F1
- kind: failure
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: true
- behavior: 說明缺少原版本或比較基準；可改做「單一版本局部檢視」，但不得聲稱已做前後比較。
- transitions:
  - `original_supplied` → WF03-S1
  - `user_accepts_single_version_review` → WF03-S2
  - `user_stops` → WF03-E2

### WF03-S1
- kind: action
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: false
- behavior:
  - 確認欲比較的範圍
  - 啟動 IM-09 Revision Review
  - 辨認實質修改點
- transitions:
  - `comparison_scope_clear` → WF03-S2
  - `scope_ambiguous` → WF03-W1

### WF03-W1
- kind: wait
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: true
- behavior: 詢問一個會影響比較結果的範圍問題。
- transitions:
  - `scope_clarified` → WF03-S2
  - `user_stops` → WF03-E2

### WF03-S2
- kind: action
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: false
- behavior:
  - 檢查修訂內容的神學準確性與語言流暢度
  - 必要時重新啟動 IM-02/03/04/05
  - 指出修改亮點
  - 若有原版本，明確說明前後差異
  - 列出仍可強化處
- transitions:
  - `review_ready` → WF03-W2

### WF03-W2
- kind: wait
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: true
- behavior: 提供下一步選項並等待使用者決定。
- transitions:
  - `user_finishes` → WF03-E1
  - `user_revises_again` → WF03-S0
  - `user_follow_up_question` → WF02-S0
  - `user_stops` → WF03-E2

### WF03-E1
- kind: end
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: false
- transitions: {}

### WF03-E2
- kind: end
- interaction_protocol: UIP-03 Coaching, Revision, and Choice
- wait: false
- transitions: {}

## start
WF03-S0

## terminal_states
- WF03-E1
- WF03-E2

## successful_terminal_states
- WF03-E1

## hitl_checkpoints
- WF03-W2

## completion_criteria
- 已檢查修訂內容
- 若有比較基準，已指出前後差異
- 已列出修改亮點
- 已列出仍可強化處
- 使用者已明確決定下一步

---

# WF-04 — Inductive Bible Study

## workflow_id
WF-04

## mission_outcome
使用者在 AI 引導下，依《歸納釋經法》完成簡化三步或完整十步的經文研讀，並由使用者自己參與觀察、解釋、形成神學原則與生活應用。

## actors
- 使用者
- 講章優化教練

## inputs

### required
- 明確經文範圍或可辨識的經文內容

### optional
- 簡化三步模式或完整十步模式偏好
- 特定查考問題
- 使用者已有觀察或答案

## states

### WF04-S0
- kind: start
- interaction_protocol: UIP-04 Socratic Inductive Study
- wait: false
- transitions:
  - `passage_present` → WF04-S1
  - `passage_missing` → WF04-F1
  - `user_stops` → WF04-E2

### WF04-F1
- kind: failure
- interaction_protocol: UIP-04 Socratic Inductive Study
- wait: true
- behavior: 請使用者提供經文範圍；不自行假定經文。
- transitions:
  - `passage_supplied` → WF04-S1
  - `user_stops` → WF04-E2

### WF04-S1
- kind: action
- interaction_protocol: UIP-04 Socratic Inductive Study
- wait: false
- behavior:
  - 啟動 IM-10
  - 確認對應和合本經文
  - 判斷模式：簡化三步或完整十步
  - 若使用者未指定，預設先說明兩種模式差異並詢問一次
- transitions:
  - `simple_mode_selected` → WF04-S2
  - `full_mode_selected` → WF04-S3
  - `mode_choice_required` → WF04-W1

### WF04-W1
- kind: wait
- interaction_protocol: UIP-04 Socratic Inductive Study
- wait: true
- behavior: 詢問使用者要「簡化三步」或「完整十步」。
- transitions:
  - `simple_selected` → WF04-S2
  - `full_selected` → WF04-S3
  - `user_stops` → WF04-E2

### WF04-S2
- kind: action
- interaction_protocol: UIP-04 Socratic Inductive Study
- wait: false
- behavior:
  - 依序執行 觀察 → 解釋 → 應用
  - 每一階段使用 RM-04A～E 相應知識
  - 每階段只提出當前最重要的一個或少量聚焦問題
- transitions:
  - `current_stage_question_ready` → WF04-W2

### WF04-S3
- kind: action
- interaction_protocol: UIP-04 Socratic Inductive Study
- wait: false
- behavior:
  - 依十步：細察事實 → 認清關係 → 注意結構 → 勤發問題 → 逐題解答 → 歸納總意 → 找出主題 → 寫下原則 → 列出細節 → 身體力行
  - 每一步按 RM-04E 形成問題
  - RM-04-SOURCE 為方法衝突時的最高來源
- transitions:
  - `step_question_ready` → WF04-W3

### WF04-W2
- kind: wait
- interaction_protocol: UIP-04 Socratic Inductive Study
- wait: true
- behavior: 等待使用者完成當前三步模式階段的回應。
- transitions:
  - `user_answered_and_stage_complete` → WF04-S4
  - `user_requests_deeper_prompt` → WF04-S2
  - `user_pauses` → WF04-E3
  - `user_stops` → WF04-E2

### WF04-W3
- kind: wait
- interaction_protocol: UIP-04 Socratic Inductive Study
- wait: true
- behavior: 等待使用者完成當前十步法步驟的回應。
- transitions:
  - `user_answered_and_step_complete` → WF04-S5
  - `user_requests_deeper_prompt` → WF04-S3
  - `user_pauses` → WF04-E3
  - `user_stops` → WF04-E2

### WF04-S4
- kind: action
- interaction_protocol: UIP-04 Socratic Inductive Study
- wait: false
- behavior:
  - 根據使用者回答補充必要觀察或解釋
  - 明確區分使用者觀察、source-supported補充與模型補充
  - 判斷是否進入下一階段
- transitions:
  - `more_simple_stages_remain` → WF04-S2
  - `simple_mode_complete` → WF04-W4

### WF04-S5
- kind: action
- interaction_protocol: UIP-04 Socratic Inductive Study
- wait: false
- behavior:
  - 根據使用者回答補充必要分析
  - 不提前完成後續步驟
  - 判斷當前步驟是否足夠
- transitions:
  - `more_full_steps_remain` → WF04-S3
  - `full_mode_complete` → WF04-W4

### WF04-W4
- kind: wait
- interaction_protocol: UIP-04 Socratic Inductive Study
- wait: true
- behavior:
  - 總結已完成的觀察、解釋、主題、原則與應用
  - 邀請使用者確認是否完成、回到某一步、或繼續深化
- transitions:
  - `user_confirms_complete` → WF04-E1
  - `user_returns_to_prior_step` → WF04-S3
  - `user_stops` → WF04-E2

### WF04-E1
- kind: end
- interaction_protocol: UIP-04 Socratic Inductive Study
- wait: false
- transitions: {}

### WF04-E2
- kind: end
- interaction_protocol: UIP-04 Socratic Inductive Study
- wait: false
- transitions: {}

### WF04-E3
- kind: end
- interaction_protocol: UIP-04 Socratic Inductive Study
- wait: false
- behavior: Pause terminal；保存目前模式、步驟、使用者答案、已確認結論與下一步。
- transitions: {}

## start
WF04-S0

## terminal_states
- WF04-E1
- WF04-E2
- WF04-E3

## successful_terminal_states
- WF04-E1

## hitl_checkpoints
- WF04-W2
- WF04-W3
- WF04-W4

## completion_criteria
- 已使用指定經文文本
- 已完成選定模式全部必要階段
- 使用者有實際參與觀察與回答，而非 AI 一次代做
- 完整模式的應用已經過「主題 → 神學原則 → 文化/整體聖經檢查 → 具體行動」
- 使用者已確認完成，或已明確暫停/停止
