# 私有語料與核實規則

## 資料邊界

精確檢索預設使用插件內 `assets/scripture/cuv.sqlite3`：它是由兩份經擁有者聲明為公版、且通過 SHA-256 核對的舊約／新約 PDF 所凍結的唯讀語料。它包含 31,008 列已核實經文；71 個原始來源本身的節號不連續事件由獨立 manifest 逐項列出，且只有來源、作者語料、runtime database、結構、列數和完整事件集合全部相符時才算 `approved_source_gap`。

使用者可明確指定經授權的外部作者語料作比較、重建和修訂，但核對工具不得修改內附資料庫。抽取頁面、OCR 輸出、建置中資料庫、人工核對紀錄、備份、私人路徑和 RAG 工作資料均不隨插件散布。

## 每節來源資料

每一筆紀錄必須包含：

- 正典書卷 ID、章與節；
- 從 PDF 嵌入文字或 OCR 取得的文字；
- **來源檔案**名稱；
- **來源頁碼**；
- **OCR 信心／抽取信心**（0–100；直接嵌入文字使用 100，但仍不會自動取得人工核實旗標）；
- 是否經人工／受控流程核實的旗標。

資料庫另存來源 PDF 的 SHA-256、schema 版本、信心門檻和語料模式。`verify_cuv_index.py` 檢查 66 卷覆蓋、順序、空值、頁碼、信心範圍、核實旗標、來源雜湊和 approved-gap 身分。合成 fixture 永不具有 production-ready 資格；未列入或身分不符的 gap 仍是 warning，且 `production_ready=false`。

## 信任判斷

- `verified`: 請求內每節皆有核實旗標且 OCR 信心不低於資料庫門檻。
- `unverified`: 任一節未核實或低於門檻；只能當作待核 OCR 輔助文字。
- 來源檔案變更、雜湊不符、結構錯誤或缺卷時，不可把語料宣稱為可正式引用。

RAG 候選另有 `rag_index_status`：`current` 表示候選所列來源雜湊仍符合私有索引，`stale` 表示需要重新匯入，`unknown` 表示無法比較。這個狀態只判斷探索索引的新鮮度；即使是 `current`，仍不能取代 `get_passage.py` 的逐節完整性、核實旗標與信心門檻檢查。RAG chunk 文字不會交給導師作逐字引用。

核實代表索引紀錄通過既定檢查，不代表該 PDF 版本、排版或文字沒有任何可能錯誤。爭議時回到來源頁面。

## 人工核對與探索索引狀態

`review_cuv_index.py` 是本機人工核對輔助工具，不是自動驗證器。它只允許人對照已通過雜湊檢查的來源 PDF 後，明確修改或核實資料；RAG、OCR 信心和模型輸出都沒有核實權限。`get_passage.py` 退出碼 0 仍是精確引文的唯一程式 gate。

每次成功修改會在私有 metadata 設定 `rag_index_state=stale` 及 `rag_index_stale_at=<UTC>`。此全域狀態優先於來源雜湊比較，所以 discovery 不得回報 `current`。指定書卷或章的部分匯入不會清除標記。

成功、無 `--book`／`--chapter` 篩選的完整 JSON `ingest_bible_rag.py` 匯入會從實際向量檔記錄語料結構指紋、向量片段數與 identity digest；結束前還會重讀語料，確認匯入期間沒有核對修改，才清除 stale。唯一快速例外是工作台的 JSON metadata-only 同步：它必須取得與完整匯入共用的向量檔鎖，確認 stale、三項基準、逐段經文及來源資料全部未變，建立備份，再只更新 `verified_all`／`unverified_count`；寫入後也必須確認經文與 embedding 指紋不變。任一條件不符即保留 stale，要求完整匯入。
