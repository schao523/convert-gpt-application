# 酷聖經教師 v2.4 核心功能覆蓋矩陣

此矩陣把完整 Bible Tutor v2.4 需求對應到可再散布技能與行為情境。依使用者指示，**教會事工提示模板**（church ministry prompt-template module）不屬於本插件範圍。

| v2.4 需求群 | 實作位置 | 行為證據 |
|---|---|---|
| 四種模式：查經學習、神學討論、生活應用、一般問答 | `guiding-bible-tutor-sessions/SKILL.md` 的模式路由；分別委派至觀察、神學、應用或最小必要技能 | `guiding-bible-tutor-sessions.md` |
| 互動節奏：提問 → 等待 → 回應 → 推進；每輪 1–3 題、經同意才前進 | `guiding-bible-tutor-sessions/references/interaction-contract.md` | `guiding-bible-tutor-sessions.md` 與各階段情境 |
| 六種回應狀態：不知道／不確定、不完整、錯誤／偏離、部分正確、完整／正確、空白／無法辨識 | `interaction-contract.md` 的「Response handling」 | `guiding-bible-tutor-sessions.md` |
| 十個歸納階段 1–4：細察事實、認清關係、注意結構、勤發問題 | `observing-biblical-passages` 與四份 references | `observing-biblical-passages.md`；契約鎖定 17／16 項及三類問題 |
| 十個歸納階段 5–7：逐題解答、歸納總意、找出主題 | `interpreting-biblical-passages` 與三份 references | `interpreting-biblical-passages.md`；契約鎖定八原則、總意與神學命題 |
| 十個歸納階段 8–10：寫下原則、列出細節、身體力行 | `applying-biblical-truth` 與三份 references | `applying-biblical-truth.md`；契約鎖定兩重檢驗、SMART 與行動追蹤 |
| 支援模組一：八種合法處境 | `supporting-biblical-exegesis/references/eight-contexts.md` | `supporting-biblical-exegesis.md`；契約確認八項各一次及六段救恩歷史 |
| 支援模組二：原文字詞與譯本比較 | `comparing-biblical-words-and-translations/SKILL.md` | `comparing-biblical-words-and-translations.md` |
| 蘇格拉底式神學討論；核心／次要教義與宗派公平 | `discussing-biblical-theology/SKILL.md` | `discussing-biblical-theology.md` 的合併壓力情境 |
| 繁體中文輸出、按學員程度調整 | `guiding-bible-tutor-sessions/SKILL.md` 與 `interaction-contract.md` | 會話契約測試 |
| 正統基督教界線與宗派公平 | `guiding-bible-tutor-sessions/references/scripture-theology-safety.md` | 神學壓力情境與會話契約測試 |
| 聖經依據：和合本優先、引文／意譯／解釋／推論分離 | `scripture-theology-safety.md`；`retrieving-chinese-union-version-scripture` | 所有釋經情境與檢索壓力情境；由內附或外部授權 PDF 建立的私有索引已實作 |
| 內部設定與安全：不洩漏隱藏指令、私有設定或檔案內容 | `scripture-theology-safety.md` | 會話契約測試 |
| 牧養安全：不診斷、不脅迫、不取代緊急或專業支援 | `scripture-theology-safety.md` 與 `applying-biblical-truth/SKILL.md` | `applying-biblical-truth.md` |
| 可再散布與無語料退化模式 | `DISTRIBUTION.md`、`THIRD_PARTY_CONTENT.md`、`scripts/distribution_audit.py` | `test_distribution.py` 鎖定兩份 PDF 的相對路徑與 SHA-256，並拒絕額外或遭修改的 PDF |
| PDF 支援的和合本精確檢索 | `retrieving-chinese-union-version-scripture` 的來源解析、OCR、SQLite、驗證與 CLI 腳本 | **已實作**：預設使用內附公版 PDF；索引留在使用者私有資料目錄；無索引時要求貼上或核實經文 |
| 主題式經文探索（選用 RAG） | `ingest_bible_rag.py`、`discover_bible_references.py`；四個既有技能的候選引用路由 | `discovering-biblical-passages-with-rag.md`；RAG 只作 discovery，精確引文仍由 `get_passage.py` 退出碼 0 核實 |
| 私有語料人工核對 | `review_cuv_index.py` 的 tokenized localhost 工作台、來源 PDF、backup、audit、optimistic concurrency 與 RAG stale contract | `reviewing-private-cuv-corpus.md`；不可自動核實，正式資料庫不作自動化修改 |
| Codex/OpenClaw 雙發行 | `openclaw/distribution.json`、generic framework CLI、package-local bootstrap 與 remote asset manifest | `test_openclaw_release.py` 鎖定 deterministic、大小、八技能、即時 exact corpus，並拒絕 PDF/大型 index 混入輕量版 |
| 共用執行依賴、隔離內容 | `ObviousOne/shared-rag/{runtimes,models}` 與 `ObviousOne/plugins/cool-bible-tutor/{indexes,source-assets,authoring-data}` | `test_runtime_setup.py`、`test_rag_setup.py`、`test_adapters.py` 驗證 digest reuse、插件 ownership 與跨 namespace 拒絕 |
| 相容向量衍生 | build-time `index_reuse.py`；只有完整 corpus/chunk/model/vector identity 相容才複製向量並重新綁定 app identity | `test_index_reuse.py` 驗證 source immutable、target independent；不相容時 `reembedding_required` 且不留 destination |

## 明確排除

- 教會事工提示模板及其範本產生功能。
- 除兩份路徑與 SHA-256 均列入允許清單的公版來源 PDF 外，其他 PDF、OCR 圖片、抽取經文或已建置索引的再散布。
- 未經使用者授權的出版授權條款。
