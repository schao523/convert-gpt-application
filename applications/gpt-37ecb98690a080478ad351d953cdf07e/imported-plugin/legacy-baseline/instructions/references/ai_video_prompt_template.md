# 🎮 AI Video Prompt Template v2.0  
*(for Runway / Pika / Kaiber — structured cinematic generation)*  

---

## 🌟 Story Overview（故事總覽）
| 項目 | 說明 |
|------|------|
| **Title（標題）** | [故事名稱] |
| **Theme（主題）** | [核心信息／彙意] |
| **Audience（受眾）** | [年齡層或群體] |
| **Story Type（故事類型）** | 聖經／啟發／原創 |
| **Visual Style（影片風格）** | [風格名稱，如：故事繪本風、2D 動漫風…] |
| **Duration（影片長度）** | 約 [X] 分鐘／[N] 幕 |
| **Language（語言）** | 中文 + English (for AI models) |

---

## 🎞️ Scene Prompts（逐幕影片提示）

### 🎮 Scene [n]: [場景名稱]
**【Camera Prompt（運鏡說明）】**  
🖐 [專業鏡頭術語，如「緩推至主角臉部，營造緊張感」]  

**【Start Frame（AI 畫面描述）】**  
🖼️ [場景主體、表情、姿態、背景與氛圍；50 字內]  
🎨 *AI Prompt (English)*: "[English cinematic visual description]"  

**【Dialogue（對白腳本）】**  
🎙️ [角色名稱]：「[對白內容]」  
*(English)* “[Character]: \"[Dialogue]\"”  

**【Emotion（情緒指令）】**  
💭 [如：恐懼、勇氣、驚奇、平安等情感關鍵字]  

**【Audio Cue（音效／音樂提示）】**  
🎵 [背景音樂、音效建議，如「管弦樂漸強」、「風聲與鼓聲」]  

---

*(Repeat for each scene: Scene 1–10)*  

---

## 🎨 Global Style & Mood（整體風格與氛圍）
| 項目 | 設定 |
|------|------|
| Lighting（光線） | [柔光／逆光／高亮對比／靈性光曾 等] |
| Color Tone（色調） | [暖色系／冷色系／高飽和 等] |
| Motion Rhythm（運鏡節奏） | [緩推／快切／穩定手持 等] |
| Music & Sound（配樂音效） | [鋼琴、弦樂、史詩風、敬拜氛圍 等] |
| Aspect Ratio（畫面比例） | [16:9 / 9:16 / 4:3] |

---

## 🧩 Rendering Notes（渲染與工具說明）
| 工具 | 支援模式 | 輸入建議 |
|------|------------|-----------|
| **Runway Gen-2** | Text-to-Video / Storyboard | 每幕分別輸入或整體匯入 |
| **Pika Labs** | Frame-to-Frame Animation | 使用 Start Frame 為影像起始畫面 |
| **Kaiber AI** | Music + Story Visualization | 套用全局光影與音樂提示 |
| **Output Recommendation（輸出建議）** | 每幕 5–10 秒，採 Crossfade 過渡；合併後長度 1–3 分鐘。 |

---

## 📦 Export Metadata（輸出規格）
| 類型 | 檔名範例 | 用途 |
|------|------------|------|
| AI Prompt File | `AI_VideoPrompt_[StoryTitle].md` | 可直接上傳至 Runway/Pika/Kaiber |
| Storyboard Script | `Storyboard_[StoryTitle].md` | 劇本參考與教育使用 |
| Dialogue Script | `Dialogue_[StoryTitle].md` | 聲音錄製或字幕生成 |
| Cinematic Plan | `CinematicPlan_[StoryTitle].md` | 鏡頭與構圖依據 |

---

## 💡 Usage Notes（使用說明）
1. 此模板用於整合「分鏡腳本 + 運鏡 + 風格設定 + 對白 + Prompt」，生成 AI 可理解的影片指令。  
2. 若故事為「聖經導向」→ 套用 **Bible Rubric**；若為「啟發／彙話」→ 套用 **Inspirational Rubric**。  
3. 英文部分會自動生成，確保與多數 AI 影片引擎兼容。  
4. 支援自動匯出功能 `/generate_video_prompt`。  

---

📘 **建議放置路徑：**  
`Resources/AI Video Prompt Template.md`

🗎 **引用模組：**  
- 🎥 運鏡與起畫支援模組（Cinematic Framing & Shot Support Module）  
- 🎨 Visual Style Auto-Rules  
- 🌈 Cinematic Lighting & Mood Reference  
- 🎷 StorySound & Emotion Cues  

