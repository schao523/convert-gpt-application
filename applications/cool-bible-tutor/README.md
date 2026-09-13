# 酷聖經教師 Cool Bible Tutor

酷聖經教師是「明明可知 Obvious One」的繁體中文歸納式查經插件。插件內附兩份經發布者聲明為公版、並以雜湊鎖定的和合本 PDF，以及由它們凍結、完整核實且唯讀的 `assets/scripture/cuv.sqlite3`。安裝後可立即精確檢索經文；人工核對紀錄、替代語料與私人 RAG 資料仍留在插件外部。

OpenClaw 發行版是 native-free 的 Codex-format compatible bundle，不是原生 OpenClaw code plugin。技能透過內嵌 Python 啟動器執行支援功能；`rag_subsystem` 是啟動器背後的 Python 相依套件，不是另行註冊的 agent tool。完整分層契約見 [Runtime Compatibility Contract](docs/runtime-compatibility-contract.md)。

## 快速設定

所有本機操作都由插件根目錄的 `scripts/cool_bible_tutor.py` 統一啟動。精確檢索不需先安裝 Poppler、Tesseract、建立資料庫或連線網路：

```powershell
python scripts/cool_bible_tutor.py status --json
python scripts/cool_bible_tutor.py passage "約 3:16" --format json
python scripts/cool_bible_tutor.py verify --json
```

沒有 `--data-dir` 或 `COOL_BIBLE_TUTOR_DATA_DIR` 時，`status`、`verify`、`passage` 和探索流程使用內附唯讀語料。明確指定的外部語料優先，但不會改寫或取代內附資產。

## 選用的語料建置與人工核對

只有要從 PDF 重建、比較或修訂外部語料時，才需安裝 Python 3.10 以上、Poppler（`pdfinfo`、`pdftotext`、`pdftoppm`）、Tesseract，以及繁體中文語言資料 `chi_tra`：

```powershell
python scripts/cool_bible_tutor.py doctor
python scripts/cool_bible_tutor.py init
python scripts/cool_bible_tutor.py review
```

建置與核對資料目錄依序取自 `--data-dir`、`COOL_BIBLE_TUTOR_DATA_DIR`、宿主提供的 `PLUGIN_DATA/cuv`，最後才使用作業系統的個人應用程式資料目錄。啟動器拒絕把生成資料寫進已安裝插件。

若要明確指定私人資料目錄：

```powershell
$cuvDataDir = Join-Path $env:LOCALAPPDATA "ObviousOne\cool-bible-tutor"
python scripts/cool_bible_tutor.py init --data-dir $cuvDataDir
python scripts/cool_bible_tutor.py verify --data-dir $cuvDataDir --json
```

`init` 會在外部資料目錄從內附 PDF 建立或續建作者語料，不會修改內附的 runtime database。成功建置不代表每一列都已人工核實；`verify` 會報告結構、來源與核實狀態。

## 人工核對與經文測試

啟動只監聽 `127.0.0.1` 的瀏覽器核對工具：

```powershell
python scripts/cool_bible_tutor.py review --data-dir $cuvDataDir
```

只有人親自對照畫面中的雜湊相符 PDF 才能核實經文。OCR 信心、RAG 結果、既有文字和模型記憶都沒有核實權限。核對後重新執行 `verify`，並測試指定範圍：

```powershell
python scripts/cool_bible_tutor.py passage "約 3:16" --format json
```

只有 `passage` 退出碼 `0` 授權把結果當作已核實的精確和合本引文；退出碼 `3` 表示仍含待核 OCR 文字。

## 選用 RAGenius 探索

RAG 只負責由主題探索候選經文，不是精確引文的必要條件。Codex 完整版內附公版 PDF 與精簡向量索引；OpenClaw 輕量版不內附這些大型資產。兩種版本都內附已核實的 `cuv.sqlite3`、頂層啟動器、固定版本的 `rag_subsystem` wheel 與 package-local bootstrap，所以精確引用安裝後立即可用。

```powershell
python scripts/cool_bible_tutor.py passage "約 3:16" --format json
```

主題探索另有一次、明確同意後才開始的下載。使用 CPython 3.10–3.13 執行：

```powershell
python scripts/cool_bible_tutor.py setup-rag
# 非互動環境：
python scripts/cool_bible_tutor.py setup-rag --accept-downloads --json
```

`setup-rag` 會先顯示約 1.30 GB 模型下載與最多約 6 GB 安裝空間需求，再把 hash-locked、CPU-only 的 Python 相依套件和固定 revision 的 MIT 模型安裝到個人應用程式資料目錄。OpenClaw 版也會依 `assets/openclaw/remote-assets.json` 下載並核對本插件自己的索引與 PDF。未同意時不下載；所有摘要與成員雜湊、離線模型嵌入及語意 smoke test 通過後才原子啟用。

可相容插件只共用內容定址的執行依賴：`ObviousOne/shared-rag/runtimes/<digest>` 與 `ObviousOne/shared-rag/models/<digest>`。聖經資產不共用：本插件各自保存在 `ObviousOne/plugins/cool-bible-tutor/indexes` 與 `ObviousOne/plugins/cool-bible-tutor/source-assets`。移除插件不會自動刪除共用快取，因為其他插件可能仍在使用同一 digest。

設定完成後：

```powershell
python scripts/cool_bible_tutor.py status --json
python scripts/cool_bible_tutor.py rag-discover "饒恕與恩典" --top-k 5
```

RAG 探索輸出只提供候選引用與信任／來源狀態。選中的引用仍須經 `passage`，且只有退出碼 `0` 才是已核實精確引文。`COOL_BIBLE_TUTOR_RAG_PYTHON` 和 `COOL_BIBLE_TUTOR_RAG_ROOT` 仍保留為進階外部 runtime 覆寫；一般使用者不需手動設定環境變數或自行安裝 RAGenius。

外部／作者模式可另行檢查 runtime 並把外部語料匯入私人索引：

```powershell
python scripts/cool_bible_tutor.py rag-check --json
python scripts/cool_bible_tutor.py rag-ingest --data-dir $cuvDataDir
```

## 指令摘要

| 指令 | 用途 |
|---|---|
| `doctor` | 檢查 PDF、Poppler、Tesseract、`chi_tra` 與目前資料狀態 |
| `init` | 建立或續建 `cuv.sqlite3` |
| `status` | 顯示資料列、待核列與 RAG 索引狀態 |
| `verify` | 執行完整語料驗證 |
| `review` | 啟動本機瀏覽器人工核對工具 |
| `passage` | 測試精確引用與信任 gate |
| `rag-check` | 檢查選用的 `rag_subsystem` runtime |
| `setup-rag` | 經明確同意後安裝並驗證主題探索 runtime 與模型 |
| `rag-ingest` | 把私人結構化語料匯入 RAG |
| `rag-discover` | 測試主題式候選引用探索 |

進階來源覆寫、復原與核對規則見 [設定和合本檢索資料](skills/retrieving-chinese-union-version-scripture/references/setup-scripture-data.md)。插件作者可參考 [頂層啟動器模式](docs/top-level-launcher-pattern.md) 在未來插件重用相同 UX 架構。
