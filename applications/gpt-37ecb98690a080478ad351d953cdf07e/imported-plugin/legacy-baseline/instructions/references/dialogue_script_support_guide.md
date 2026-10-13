# 🎹 Dialogue Script Support Guide  
*(對白腳本支援指南 — for Vibe StorySpirit Director)*  

---

## 🌟 Purpose（目的）
定義對白生成格式、表演提示與輸出規格，確保對白與鏡頭、情緒及節奏一致。

---

## 📖 Dialogue Structure（對白結構）
每幕皆含：
- 【角色】 名稱  
- 【對白】 內容  
- 【表情／動作提示】 (可選)  
- 【情緒】 如：勇氣、恐懼、平安、敬畏  

**範例：**
```
🎮 Scene 3 — David Steps Forward  
大衛（堅定）：「耶和華會幫助我！」  
*David (firmly): “The Lord will help me!”*
```

---

## 🧱 Integration（整合點）
| 模組 | 功能 |
|------|------|
| Storyboard Generator | 生成逐幕對白段落 |
| Cinematic Framing Module | 對白與鏡頭節奏同步 |
| Sound & Emotion Cues | 自動附加聲音建議與情感標籤 |

---

## 📦 Output Files（輸出檔案）
| 檔案 | 說明 |
|------|------|
| **嵌入版** | 內含於 Storyboard_[Title].md 中 |
| **獨立版** | `Dialogue_[Title].md` 供錄音或字幕生成 |

---

## 🎧 Optional Fields（可選欄位）
- 音效／配樂提示 (🎵 Audio Cue)  
- 雙語字幕 (中／英 對照)  
- 情緒層級 (強、中、弱)  

---

## 📘 References
- Character Acting Reference.md  
- StorySound & Emotion Cues.md  
- Visual Rhythm Support Module.md

