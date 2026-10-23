# 資料與成果契約

本文件是行為資料需求，不指定程式語言、資料庫、路徑或 API。所有物件都有 artifact_id、project_id、version、state、provenance 與 created_context。state 依成果使用 draft／approved／needs-reconfirmation／superseded；每次確認攜帶 artifact_id、version、範圍及實際使用者確認證據。未確認值一律不能寫入 confirmed。

## 輸入狀態

- DesignBrief：audience、context、problem、role、goal、style、depth；每個欄位帶值、來源及四態。
- ExistingConfiguration：instructions 正文與版本、starters 清單、resource_settings（檔案、資料來源、工具／功能；可明確為無）；缺少與明確為無不同。
- InteractionInput：mode=new／review；new 可用場景／任務；review 必須有現行指令／互動流程。生成測試另須補齊互動藍圖。
- ResourceRecord：material_id、來源、作者／日期聲明及驗證狀態、正文可用性、版本／hash、四維評估、用途、必要性、使用條件、優先級、必要的切分建議、權利五分項、敏感性、衝突與缺口。切分是目標 AI 應用 設計建議，不硬定本插件架構。
- RuntimeEvidence：target_version、環境、使用者輸入序列、實際回覆、時間／來源（可用時）、與 testcase 的關聯及限制；模擬有 simulation=true，不得標 Runtime verified。

## 主要輸出

- DesignStatement：六個意圖欄位、版本、確認狀態，保留草稿假設。
- CustomInstructionDesignPackage：DesignStatement、Custom Instructions（角色／目標／範圍／觸發／流程／互動／來源規則／安全）、啟動範例、目標 AI 應用 邏輯模組、互動藍圖、Resources Manifest、模組資源使用對照、目標平台 指引、適用工具能力與限制、版本紀錄、確認範圍、未決事項。沒有資源時明確列 none，不虛構資料。
- InteractionBlueprint：任務、模式、候選差異、狀態、輸入守衛、輸出、等待、確認、推進、分支、失敗與恢復；不得用研發三階段替代目標 AI 應用 實務流程。
- TestCard：id、target_version、goal、context、preconditions、input、steps、expected_observable、requirement_ids、rubric_dimensions、evidence_state、actual_result、evidence_ref。沒有執行時 actual_result=NOT RUN。
- Rubric：準確性／相關性／清晰度／互動性／一致性；每項明確描述符合／部分符合／不符合的判準。按需追加深度／結構／資源使用；維度不足不能用平均分蓋過安全或門檻失敗。
- PromptPatch：patch_id、baseline_version、problem、evidence、location、before、after、reason、affected_requirements、preserved_features、impact、approval_state、rollback、retest_ids。若 before 不可取得則停止精確替換，不能編造基準文字。
- SourceUse：material_id、成功讀取操作識別或可核實紀錄、version_or_hash、section、concept、output_mapping、read_status、read_context；後補讀取另建事件，不覆寫歷史。
- ChangeLog：from_version、to_version、理由、差異、使用者確認、受影響成果與重測證據。

## 狀態生命週期

ProjectState：project_id、mission、phase、active_intent、artifact_versions、decisions（confirmed／assumption／recommendation／unresolved）、approvals、source_uses、missing_inputs、risks、resume_point、next_question、capability_limits。

修改目標會影響聲明、模組、互動、配置與測試；修改參考只使依賴它的設計和測試需重新確認；單純語句修飾依影響分析決定重測範圍。確認不可跨版本自動移轉。重複收到同一版本同一範圍確認不重複產生新版本。暫停只保留狀態，停止不刪除使用者成果。保留／刪除與跨會話能力須如實說明；無儲存能力則匯出可攜摘要，由使用者控制後續提供。


## Revision 02 平台欄位及成果補強

TargetCapabilityProfile 與 CustomInstructionDesignPackage 以 Platform_Target_Adaptation_Requirements.md 為完整欄位依據。每個平台版獨立保存 platform_id、surface、capability_evidence、version、state、指令放置位置與文字、資源設定、launch_examples、limitations、unsupported 及驗證狀態；portable_core 也獨立版本化。ExistingConfiguration 新增目標平台，啟動範例／原生啟動欄位可明確為 none／not-applicable，不能要求不存在的 Builder 欄位。此例外不放寬目前指令、互動藍圖、目標與情境的測試前置要求。

輸出的主要自訂指令不是各家 API 的 system message。若平台只接受較短欄位，依實際查核值調整，保留安全、必需門檻與確認；不能單純把超長指令放在知識文件便宣稱已獲同等控制權。新平台需重驗 capability 與相應測試；不擅改已確認的共同設計。沒有原生啟動問題欄位時，提供使用者可複製到新對話的啟動提示。
