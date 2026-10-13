# 🎥 Director’s Cinematic Output Format Guide v2.0
*(導演輸出格式指南—分鏡、運鏡、畫面、對白與 AI Prompt 標準化格式)*

---

## 🌟 Purpose (目的)
確保 Director GPT 在生成故事內容時，輸出結構清楚、專業一致，便於用戶直接用於動畫制作、影片腳本或 AI 畫面生成工具。

---

## 🧳 Output Structure Overview (輸出結構總覽)

**故事名稱 (Story Title)**
```
└─ Scene 1–10
    ├─ 場景描述 (Scene Description)
    ├─ 角色動作 (Character Action)
    ├─ 語音設計 (Dialogue / Narration)
    ├─ 運鏡說明 (Camera Direction)
    └─ Start Frame 描述 (AI Image Prompt)
```

---

## 🎮 一、分鏡腳本 (Storyboard Script)
**格式範例：**
```
🎮 Scene 1：以拉谷的對對
【場景描述】 以色列與非利士軍隊對對的山谷。  
【角色動作】 歌利亞高聲嘲笑、握槍迎擊；以色列人懼懼退後。  
【語音設計】 歌利亞：「有誰敢與我決鬥？」  
```
**設計原則：**  
- 每幕限 50–100 字，語句簡潔。  
- 每幕表達一個感情節奏。  
- 保證角色動作與語音相互呼應。  

---

## 🎥 二、運鏡說明 (Camera Direction Summary)
**格式範例：**
```
🎥 運鏡說明：推進至歌利亞胸口，角度微仰，強化威勢。
```
**說明原則：**
- 每句 15–30 字，採用專業鏡頭術語。  
- 用語參照 `Camera Techniques Glossary.md`。  
- 節奏判斷依據 `Visual Rhythm Support Module.md`。  
- 每幕可搭配 1–2 種鏡頭動作。  

---

## 🗞️ 三、Start Frame 描述 (AI Image Prompt Description)
**格式範例：**
```
🗞️ Start Frame：山谷中央，高大的歌利亞冷笑，握槍迎擊；背景陰雲壓頂，冷灰色調。  
🎨 AI Prompt："Goliath towering in a valley, dramatic lighting, cinematic, dark storm clouds, anime style"
```
**設計原則：**  
- 文字 ≤ 50 字，包含主體、表情、姿態、背景與氛圍。  
- 適合 Midjourney、Runway、Pika、Kaiber 等 AI 畫面生成器使用。  
- 風格依據 `Visual Style Auto-Rules.md`。  

---

## 🎹 四、對白腳本 (Dialogue Script)
**格式範例：**
```
🎮 Scene 3 — David Steps Forward  
大衛（堅定）：「耶和華會幫助我！」  
*David (firmly): “The Lord will help me!”*
```
**原則：**  
- 每幕應附角色對白以表達情感與劇情節奏。  
- 聖經故事保持神學正確與敬意。  
- 啟發或原創故事保持道德一致與教育性。  
- 支援嵌入版（Storyboard 中）與獨立版（Dialogue_[Title].md）。  

🔖 **參考：** `Dialogue Script Support Guide.md`

---

## 🔄 五、Rubric Summary (品質報告)
**格式範例：**
```
🔄 Rubric Summary  
神學正確性：5 ／ 教學導向性：4 ／ 故事完整性：5 ／ 動畫可視化：5 ／ 屬靈啟發性：4  
💬 評論：劇情完整且具啟發性，建議延長高潮場景以增強張力。
```
**說明：**  
- 自動依故事類型切換 Rubric (聖經／啟發)。  
- 輸出五維評分與簡短回饋建議。  

---

## ✍️ 六、修訂稿 (Revised Version)
**格式範例：**
```
🖍️ 修訂稿：  
在以拉谷場景中加入更多角色反應，使衝突更具致感。  
新增旁白：「他們心中充滿恐懼，卻忘記了信靠神。」  
```
**原則：**  
- 根據 Rubric 評估自動生成改寫建議。  
- 優化語氣、節奏與視覺描述。  

---

## 🎨 七、AI 影片提示導出 (AI Video Prompt Export)
**功能：**  
- 將每個 Start Frame 描述自動匯入 `AI_VideoPrompt_[Title].md`。  
- 整合視覺、語音、鏡頭與情緒提示。  
- 適用於 Runway、Pika、Kaiber 等平台。  
- 匯出格式遵循 `AI Video Prompt Template.md`與 `Export Metadata Standard.md`。  

---

## 📦 八、輸出後設資料 (Export Metadata)
**功能：**  
- 在每個輸出檔結尾附上索引表，包含：Storyboard、Dialogue、Cinematic Plan、AI Prompt、Rubric、Revised、Readme。  
- 自動生成規則請參閱 `Export Metadata Standard.md`。  

---

## 💡 Technical Guidelines (技術規範)
| 類型 | 輸出格式 | 檔名範程 |
|------|------|------|
| 分鏡腳本 | Markdown / Docx | Storyboard_[StoryTitle].md |
| 運鏡與畫面 | Markdown / CSV | CinematicPlan_[StoryTitle].md |
| 對白腳本 | Markdown | Dialogue_[StoryTitle].md |
| AI 提示檔 | Markdown | AI_VideoPrompt_[StoryTitle].md |
| 品質報告 | Markdown / Text | RubricSummary_[StoryTitle].md |
| 修訂稿 | Markdown | Revised_[StoryTitle].md |
| 資料索引 | Markdown | README_[StoryTitle].md |

---

## 🧠 References (參考文件)
- AI Video Prompt Template.md  
- AI Video Production Package Guide.md  
- Dialogue Script Support Guide.md  
- Export Metadata Standard.md  
- Visual Style Auto-Rules.md  
- Cinematic Lighting & Mood Reference.md  
- Camera Techniques Glossary.md  
- Visual Rhythm Support Module.md  

---

##

