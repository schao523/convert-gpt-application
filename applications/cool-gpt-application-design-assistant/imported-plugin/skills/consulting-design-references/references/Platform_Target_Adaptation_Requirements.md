# 平台適配與自訂指令成果要求

Version: RM13 v1 DRAFT
Evidence checked: 2026-10-22 Asia/Shanghai
Material class: 本次專案新撰寫的行為需求與官方能力摘要，非平台原文複製。

## 適配原則

平台中立核心負責任務、角色、目標、流程、輸入門檻、互動規則、HITL、輸出、參考使用、安全與不確定性。Platform Variant 保持共同設計並按平台能力改寫設定，不複製 GPT Builder 欄位假設。Custom Instructions 是使用者可設定的行為引導；不能宣稱等同各家 API system message，也不能覆蓋平台規則。產品名稱中的 GPT 保留為使用者指定品牌，支援範圍已擴展。

先問目標平台；使用者尚未選擇時可先完成可攜草稿，平台版與平台設定步驟保持 pending-target。一般需求分析不必等所有平台的能力資訊齊全。一次只針對使用者選定的平台輸出適配；明確要求比較／多平台輸出時才生成多版。各版帶 platform_id 與版本，不讓平台細節污染共同設計。

## 目標矩陣

| 目標 | 已查閱官方能力 | 本插件應產生 | 差異處理 |
| --- | --- | --- | --- |
| OpenAI Project／ChatGPT Projects | 專案可容納指令與檔案；專案指令作用於該專案 | 專案用 Custom Instructions、參考資料清單、啟動提示與設定驗證說明 | 檢查工作區、功能權限、來源與記憶條件；不沿用 GPT Builder 的設定欄位 |
| Gemini Notebook | 官方說明列有 Custom 對話設定與來源選擇；同頁同時描述來源導向聊天與實驗性功能 | 適合該 notebook 使用方式的指令、來源配置、來源使用邊界、啟動提示 | 對研究型／來源導向與實驗功能分開核對帳號／介面；不將跨情境能力一概保證 |
| Claude Project | 官方說明列有 project instructions 與 project knowledge | 專案指令、知識資料清單、啟動提示、設定與驗證說明 | 不依賴名稱與描述作任務指令；跨對話記憶條件需另查核 |
| 其他支援 Custom Instructions 的 AI 工具 | 未指定產品前能力為 unknown | 平台中立核心；取得 capability profile 後才生成平台版 | 未知欄位、來源、工具與記憶不猜；不捏造平台名稱或設定位置 |

這是設計適配要求，不是四平台已實測相容的認證。

## 能力資料契約

TargetCapabilityProfile 至少包含 target_id、product_label、surface（web／desktop／mobile／unknown）、account_or_workspace_constraints、instruction_field、instruction_scope、instruction_limit（value／unit／verification_state）、reference_support、source_grounding、tool_support、memory_scope、sharing_visibility、source_evidence（URL 或使用者畫面資訊、讀取日期、相關位置）、confidence、unknowns。每項用 verified／user-reported／unknown／unsupported；不得用 undocumented 推論 unlimited。

當前精確欄位、長度與計量未知時不硬編上限；需要壓縮時先保留安全、必要前置與確認，再移出教學說明。若平台不能保證引用完整正文、提供檔案操作紀錄或逐次檢索證據，適配版必須把它列為能力限制；不可要求目標 AI 虛構「已讀」事件。參考資料上傳不等於每次全文載入。來源檔是知識資料，不保證能充當高優先控制指令。必要依賴不支援時，阻擋相應功能定稿並提出可供使用者選擇的降級／換平台方案。

## 自訂指令包契約

CustomInstructionDesignPackage = portable_core + selected_platform_variants + design_statement + modules_and_workflows + interaction_blueprint + resources_manifest + source_usage_map + launch_examples + setup_guide + capability_profile + unsupported_or_degraded_behaviors + tests + version_log + decisions_and_approvals。

portable_core 及各 platform_variant 各有 artifact_id、version、state、requirement_mapping。平台版有 placement、text、resource_setup、launch_examples、capability_evidence、known_limits、unsupported、verification_status。沒有原生 Starter 欄位時，launch_examples 是使用者可複製到新對話的提示。工具、檔案與分享設定另列為人工設定，不把 API 或外部工具描述成只靠一段指令便能啟用。

## 適配與驗證流程

選定平台→查核必要能力→建立 portable core→產生平台適配→對照共同需求與差異→確認平台版→由使用者設定→新對話執行驗收→保存實際回覆與限制。轉到另一平台時保留已確認核心，但新平台 capability、variant 與適用測試必須重新檢查。涉及跨對話連續性時另測新對話，不因單輪示範成功就宣稱已持久保存。未執行為 EXPECTED，不合併成全平台通過。

## 官方證據與適用界線

- OpenAI：[Projects in ChatGPT](https://help.openai.com/en/articles/10169521-projects-in-chatgpt)，已讀取 Add project instructions 與 Add files 相關段落。只支持上述有限能力摘要，不證明任何自訂指令的效果。
- Google：[Use chat in Gemini Notebook](https://support.google.com/gemininotebook/answer/16179559?hl=en)，已讀取 Manage chat settings 與 chat 能力／來源限制段落。同頁來源限制與新實驗功能描述有不同適用情境，未替使用者帳號作實測。
- Anthropic：[How can I create and manage projects?](https://support.claude.com/en/articles/9519177-how-can-i-create-and-manage-projects)，已讀取 Add project instructions 與 project knowledge 相關段落。該頁跨聊天 context 註記與後段記憶功能描述應按具體能力與使用者設定再核對，不能統一假設永久記憶。
- OpenAI：[Custom GPT retirement and migration FAQ](https://help.openai.com/en/articles/20001519-custom-gpt-retirement-and-migration-faq)，已讀取退休與遷移說明。退休資訊是此次改變的背景；本規格支援跨平台的權威來自使用者 C04，正確性不依賴寫死某個退休日期。

原始 RM10 builder_guide.md 只保留任務分工、最小修訂及改後測試的通用方法；其 GPT Builder 操作不再是主要輸出目標。平台設定以本 RM13 與生成時已核對的能力資料為準。發生衝突時，平台中立設計意圖由使用者確認；平台可行性以適用官方資料與當前可觀察介面處理；歷史指南不覆蓋兩者。
