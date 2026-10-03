# Decisions and Exclusions v1.0

## 20. Assumptions, decisions, recommendations, and unresolved questions

**Confirmed decisions：** 設計陳述 v1、行為藍圖 v1.1 已由使用者核准；非行為修訂由 Builder 經確認處理，行為修訂返回設計助手；更新基準為使用者提供 ZIP；W1/W2 皆必要；測試未執行可明示後封裝，明確必要失敗不可；未說明的更新內容待決；通用工具適用時優先重用。

**Assumptions：** 規格可供辨識版本與核准狀態；若格式不同，需在輸入解析時確認。現有插件 ZIP 可供比較；若內容不完整或無法辨識來源，須在更新時診斷。這些假設不構成使用者已確認的產品要求。

**Recommendations：** 採白話的要求覆蓋摘要與兩段式審查；使用者已確認兩個審查點，但呈現形式仍可由實作決定。

**Unresolved questions：** 具體規格格式、必要資源權利、目前 OpenAI ZIP 相容規則及 Work/Codex 執行能力，須由實作團隊根據實際輸入、repo 與目標環境驗證；不得在本規格中臆定。若具體輸入缺少合法使用權或無法忠實建置，該次工作阻斷，責任人為提供材料的使用者／實作團隊，須補充權利或可替代資源。這些問題不妨礙本設計規格供審查，但可能阻斷具體成品交付。

## 21. Application Workbench handoff contract

本文件已由使用者明確批准。交接時連同設計陳述、行為藍圖、邏輯模組、互動協定、參考材料使用圖及決策紀錄交給 Conversion Workbench 專案。專案先檢視 repo，再提出精簡的實作設計，辨識重用、調整、隨附及新增能力；增量實作且維持既有 Workbench 行為；於乾淨環境執行代表性新建與更新端到端驗證。實作團隊決定 Skills 數量與名稱、分工、工具綁定、載入與儲存方式；不得把本設計中的行為模組誤當固定 Skill 架構。
