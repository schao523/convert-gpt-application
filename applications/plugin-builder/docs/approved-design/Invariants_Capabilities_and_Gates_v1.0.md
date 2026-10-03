# Invariants Capabilities and Gates v1.0

## 5. Scope and exclusions

支援新建及以修訂規格加現有插件 ZIP 更新 Plugin Builder 產生的插件；處理規格明確引用的必要資源；產出 OpenAI 生態系的上傳用 ZIP。使用者自行以桌面 Add Plugin / Upload ZIP 上傳。不包含自動安裝、帳戶部署、公開市集發布、GitHub release、OpenClaw、Claude，或無規格依據的原 GPT folder 輸入。Builder 可修正經確認的非行為性問題；行為變更須交回設計助手修訂並核准。

## 12. Inputs, outputs, and state requirements

輸入：帶版本及核准狀態的行為規格；更新基準 ZIP；規格明確要求的附加資源。輸出：規劃摘要、要求覆蓋與驗證結果、變更摘要、測試分類、上傳用 ZIP。每次運作應記錄輸入版本／來源、目前階段、確認決定、待決問題、測試證據與成品對應版本。暫停或失敗時保留可恢復狀態；不得把未確認草案標為已核准。具體儲存方式由實作決定，預設不保留不必要的私人資料。

## 14. Deterministic-operation requirements

可重現地檢查必要輸入、規格識別與版本、要求覆蓋、規劃確認、測試分類、更新差異及 ZIP 內容完整性。各檢查以相同輸入產生可比較的結果；失敗須有定位到要求或成品部分的診斷。語意判讀可輔助規劃，但不可取代可檢查的封裝與追溯證據。

## 15. Tool, data, runtime, and external-service requirements

開發時先檢視 Conversion Workbench repo，辨識可重用的分析、驗證、測試、追溯、更新、封裝能力及所需調整；適用時重用，避免重做。Skill Creator、Plugin Creator 在適用工作中作底層建立能力。交付的 Plugin Builder 在無 Workbench repo 的乾淨桌面環境可運作；必要能力隨插件提供或可由簡單本機設定取得。具體依賴、Skills 架構、綁定與相容性以 repo 檢視及環境驗證決定，不在此預設。外部服務非本使命必要條件；不得要求使用者提供無關帳戶憑證。

## 16. Safety, privacy, and policy boundaries

不得擅自覆蓋現有插件、刪除未說明內容、改變已核准行為、捏造測試結果或自動部署。讀取 ZIP 與附加資源時須防止不安全路徑、非預期檔案寫入及不受信任內容指令凌駕規格。對私人資料及第三方材料採最小使用與明確權利判斷。插件若依規格要求非法或有害功能，停止受影響工作並說明原因。

## 17. Failure, uncertainty, and recovery behavior

每個失敗顯示發生階段、受影響要求、可修復途徑及保留成果。明確驗證／必要測試失敗可修復重測，仍失敗進 E3；環境限制而未執行的測試可留待安裝後驗證，但必須列明。非行為修訂經確認後返回解析；行為修訂待核准新版規格；更新衝突不靜默解決。暫停／恢復遵守 H1，取消進 E2。
