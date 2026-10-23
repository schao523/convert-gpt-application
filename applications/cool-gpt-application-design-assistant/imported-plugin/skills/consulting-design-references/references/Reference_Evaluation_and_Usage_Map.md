# 參考資料評估及使用對照

狀態：draft。下方原資料盤點與引用名稱是原版來源的歷史記錄；現行跨平台用途以文末 Revision 02 更新與規格第 13 節為準。已讀全部十二份 MD、DOCX 主指令文字，並目視檢查 PNG。完整雜湊、出處與個別權利欄位見 Source_Inventory.json。評估維度依序為相關性／結構性／可重用性／增強效果。

| ID | 實際檔名 | 正文概念 | 支援模組 | 觸發 | 四維評估 | 限制 |
| --- | --- | --- | --- | --- | --- | --- |
| RM01 | Human-in-the-Loop_Guide.md | 關鍵協作節點；避免過度自動化 | IM01,IM02,IM12 | 所有需確認的設計決策 | 高／高／高／高 | Generate 應在確認後使用；可審閱草稿不能冒稱最終 |
| RM02 | use_case_brainstorm_guide.md | 五種發想方法；一次選一至兩種 | IM01 | 場景模糊或卡住 | 高／高／高／高 | 啟發使用者，避免代替使用者定義需求 |
| RM03 | interaction_patterns_guide.md | 六種互動模式；任務選型與組合 | IM06,IM08 | 設計或審查互動 | 高／高／高／高 | 與全程不直接回答的規則有張力；按任務分流 |
| RM04 | modular_design_guide.md | 任務分解；三層；行為知識分離 | IM03 | 生成或重構目標 GPT 架構 | 高／高／高／高 | 300–500 字為啟發式，不能視平台硬限制；不決定本插件 Skill 架構 |
| RM05 | prompt_refactoring_patterns.md | 七種修訂模式；小修優先 | IM03,IM07,IM10 | 指令重構、配置修訂、回饋修補 | 高／高／高／高 | 精簡不得移除門檻、原功能或安全規則 |
| RM06 | resource_types_guide.md | 六種資源類型；不是固定清單 | IM04 | 資源識別 | 高／高／高／高 | 範例中的醫療／法律不構成該領域權威 |
| RM07 | resource_evaluation_guide.md | 四維評估；YES／PARTIAL／NO | IM04 | 資料取捨與轉換前 | 高／高／高／高 | 沒有權利與敏感性維度，須由 R25 補足 |
| RM08 | knowledge_module_template.md | Purpose／Key Concepts／Structured Content／Usage Notes | IM04 | 有權限且內容可用的知識轉換 | 高／高／高／高 | 清晰優先不能刪除重要限定與來源脈絡 |
| RM09 | resource_binding_patterns.md | 四類對應；最小依賴與覆蓋檢查 | IM05 | 目標 GPT 模組與資源對應 | 高／高／高／高 | 只描述行為需求；不指定本插件載入技術 |
| RM10 | builder_guide.md | 配置步驟；按類別調整指令；改後測試 | IM02,IM07,IM08,IM10,IM11 | Builder 配置、操作、語氣及修訂 | 高／高／高／高 | 介面與功能名稱未查核當前版本，不能作現況保證 |
| RM11 | testing_guide.md | Test Cards；五項核心與三項延伸評估；回饋閉環 | IM07,IM08,IM09,IM10 | 產生測試、評估回覆及重測 | 高／高／高／高 | 聖經例子只示範測試形態，不應硬套所有目標 GPT |
| RM12 | Resource Index.md | 參考清單及範例檔名 | IM13 | 只用於解析資源是否存在 | 中／高／中／低 | 索引不是正文；兩份 PDF 不存在 |
| BASE01 | 酷 GPT 應用設計助理 Pro v2.docx | 角色、三階段、九個支援模組與門檻 | IM01–IM14 | 本次設計基準 | 高／中／高／高 | 多版 short description；大小寫與空白引用不一致 |
| ASSET01 | ChatGPT Image.png | 視覺候選資產 | 無行為依賴 | 僅圖示評估 | 不適用 | 已目視檢查；含類似 OpenAI 標誌的圖案；未確認再利用與品牌使用權 |

## 使用規則

每次提供實質方法建議，先按 IM 對照讀取必要正文；同一版本已完整讀取且仍在可用脈絡中可重用，不必為湊證據重讀。證據紀錄包含實際操作、成功／失敗、ID、雜湊或可辨識版本、來源章節、使用概念及輸出對應。只有索引時標記 index-only，不宣稱已閱讀正文。回顧來源時只報告當時可核實的讀取。

下表是行為用途，不是檔案路徑、Skill 綁定或 RAG 選型。required 是產出相應專業建議的必要條件；optional 是不阻礙核心流程的示例或視覺資產。權利分項在 inventory 中保留，所有再散布及原文衍生品均待權利確認。

| material_id | knowledge_supplied | supported_behavior | stage_or_triggering_intent | necessity | consultation_condition | authority_and_provenance | use_mode | limitations_and_conflicts | rights_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RM01 | 關鍵協作節點；避免過度自動化 | IM01,IM02,IM12 | 所有需確認的設計決策 | required | 即將提出該類建議／產出時；不可用則停止受影響子任務 | 使用者供件；外部作者權威未核實 | advisory | Generate 應在確認後使用；可審閱草稿不能冒稱最終 | inspection confirmed；其餘 unresolved |
| RM02 | 五種發想方法；一次選一至兩種 | IM01 | 場景模糊或卡住 | required | 即將提出該類建議／產出時；不可用則停止受影響子任務 | 使用者供件；外部作者權威未核實 | advisory | 啟發使用者，避免代替使用者定義需求 | inspection confirmed；其餘 unresolved |
| RM03 | 六種互動模式；任務選型與組合 | IM06,IM08 | 設計或審查互動 | required | 即將提出該類建議／產出時；不可用則停止受影響子任務 | 使用者供件；外部作者權威未核實 | advisory | 與全程不直接回答的規則有張力；按任務分流 | inspection confirmed；其餘 unresolved |
| RM04 | 任務分解；三層；行為知識分離 | IM03 | 生成或重構目標 GPT 架構 | required | 即將提出該類建議／產出時；不可用則停止受影響子任務 | 使用者供件；外部作者權威未核實 | advisory | 300–500 字為啟發式，不能視平台硬限制；不決定本插件 Skill 架構 | inspection confirmed；其餘 unresolved |
| RM05 | 七種修訂模式；小修優先 | IM03,IM07,IM10 | 指令重構、配置修訂、回饋修補 | required | 即將提出該類建議／產出時；不可用則停止受影響子任務 | 使用者供件；外部作者權威未核實 | advisory | 精簡不得移除門檻、原功能或安全規則 | inspection confirmed；其餘 unresolved |
| RM06 | 六種資源類型；不是固定清單 | IM04 | 資源識別 | required | 即將提出該類建議／產出時；不可用則停止受影響子任務 | 使用者供件；外部作者權威未核實 | advisory | 範例中的醫療／法律不構成該領域權威 | inspection confirmed；其餘 unresolved |
| RM07 | 四維評估；YES／PARTIAL／NO | IM04 | 資料取捨與轉換前 | required | 即將提出該類建議／產出時；不可用則停止受影響子任務 | 使用者供件；外部作者權威未核實 | advisory | 沒有權利與敏感性維度，須由 R25 補足 | inspection confirmed；其餘 unresolved |
| RM08 | Purpose／Key Concepts／Structured Content／Usage Notes | IM04 | 有權限且內容可用的知識轉換 | required | 即將提出該類建議／產出時；不可用則停止受影響子任務 | 使用者供件；外部作者權威未核實 | advisory | 清晰優先不能刪除重要限定與來源脈絡 | inspection confirmed；其餘 unresolved |
| RM09 | 四類對應；最小依賴與覆蓋檢查 | IM05 | 目標 GPT 模組與資源對應 | required | 即將提出該類建議／產出時；不可用則停止受影響子任務 | 使用者供件；外部作者權威未核實 | advisory | 只描述行為需求；不指定本插件載入技術 | inspection confirmed；其餘 unresolved |
| RM10 | 配置步驟；按類別調整指令；改後測試 | IM02,IM07,IM08,IM10,IM11 | Builder 配置、操作、語氣及修訂 | required | 即將提出該類建議／產出時；不可用則停止受影響子任務 | 使用者供件；外部作者權威未核實 | advisory | 介面與功能名稱未查核當前版本，不能作現況保證 | inspection confirmed；其餘 unresolved |
| RM11 | Test Cards；五項核心與三項延伸評估；回饋閉環 | IM07,IM08,IM09,IM10 | 產生測試、評估回覆及重測 | required | 即將提出該類建議／產出時；不可用則停止受影響子任務 | 使用者供件；外部作者權威未核實 | advisory | 聖經例子只示範測試形態，不應硬套所有目標 GPT | inspection confirmed；其餘 unresolved |
| RM12 | 參考清單及範例檔名 | IM13 | 只用於解析資源是否存在 | optional | 即將提出該類建議／產出時；不可用則停止受影響子任務 | 使用者供件；外部作者權威未核實 | metadata／visual | 索引不是正文；兩份 PDF 不存在 | inspection confirmed；其餘 unresolved |
| BASE01 | 角色、三階段、九個支援模組與門檻 | IM01–IM14 | 本次設計基準 | required | 即將提出該類建議／產出時；不可用則停止受影響子任務 | 使用者供件；外部作者權威未核實 | advisory | 多版 short description；大小寫與空白引用不一致 | inspection confirmed；其餘 unresolved |
| ASSET01 | 視覺候選資產 | 無行為依賴 | 僅圖示評估 | optional | 即將提出該類建議／產出時；不可用則停止受影響子任務 | 使用者供件；外部作者權威未核實 | metadata／visual | 已目視檢查；含類似 OpenAI 標誌的圖案；未確認再利用與品牌使用權 | inspection confirmed；其餘 unresolved |

## 缺件與別名

- 酷聖經教師.pdf 與 Vibe Designer GPT.pdf 只在索引及主指令列出，ZIP 未包含；未讀取，不推論內容。建議列為可選示例，缺少時不阻擋核心流程。
- Human-in-the-Loop Guide.md、human-in-the-Loop_Guide.md → 唯一現存檔 Human-in-the-Loop_Guide.md。
- Builder Guide.md → builder_guide.md；Testing Guide.md → testing_guide.md；Interaction Patterns Guide.md → interaction_patterns_guide.md。
- 別名只是本次來源對照，未指定最終封裝路徑。若出現多個候選版本，停止自動解析，請使用者選擇。

## 衝突處理

1. 助理有固定研發三階段，但目標 GPT 的實務流程須由任務推導；兩者不互相取代。
2. 全域「不得直接產出最終結果」約束最終化；簡單定義可直接回答，實際設計決策仍須確認。既有配置及測試門檻不因此放寬。
3. 模組化三層是本插件協助設計目標 GPT 的方法論；本插件自身的 Skill 架構留給 Workbench。
4. 模組調度摘要未單列 Interaction Logic，但主指令有完整專節；保留它為獨立行為責任。
5. 「不透露內部設定」保護平台與插件內部規則；不能拿來拒絕使用者查看自己提供的指令或本插件為其產生的設計成果。

## 權利決策

O02 由 Shen-Chang Chao 確認原指令、十一份方法指南及衍生知識內容的使用／封裝／再散布權限。未確認前本審閱包只帶來源盤點、行為摘要和新寫草案，不複製原始文件與圖示。不得稱為已獲授權正式插件。O03 圖示另行確認或提供替代圖，行為實作不必依賴圖示。沒有權限時，可提出獨立撰寫替代參考的變更方案，須保留核心功能並請使用者確認；不默認以摘要規避授權。


## Revision 02 規範用途更新

本次使用者 C04 明確要求跨平台自訂指令成果，取代本文件任何仍描述原 GPT／Builder 專用目標的歷史摘要。原檔名與 BASE01／RM01–RM12／ASSET01 保留供來源追溯，不能將原始文檔改名後冒稱跨平台權威。RM10 只用於通用方法：分工、最小修訂與改後測試，其 Builder 畫面及 GPT 專用配置不再構成現行操作依據。

新增 RM13 Platform_Target_Adaptation_Requirements.md，提供平台核心與變體分離、capability profile、平台別輸出與驗證、未知能力與降級處理。IM02、IM03、IM07–IM11、IM15 在提供平台適配、設定或平台效果評估前 required 讀取；缺 RM13 或必要當前能力證據時停止該平台版定稿，可先提供標記中立草稿。IM13 的來源報告只使用真實證據；不能要求目標平台捏造讀取日誌。

RM13 為本次專案新寫草案，非原 ZIP 成員，不改動 Source_Inventory.json 的十四項原始雜湊。其詳細用途、來源、權利與限制見 Supplemental_Reference_Inventory.json。當前平台官方資料只支持其有限能力摘要，不保證生成內容完全等效執行。
