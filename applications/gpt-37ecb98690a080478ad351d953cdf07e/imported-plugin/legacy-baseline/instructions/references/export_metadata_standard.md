# 🧾 Export Metadata Standard  
*(輸出後設資料標準 — for Vibe StorySpirit Director)*  

---

## 🌟 Purpose（目的）
統一所有導出檔案的索引格式，確保使用者清楚瞭解專案組成並便於 AI 影片平臺載入。

---

## 📋 Table Structure（表格結構）
| 類型 | 檔名 | 用途 |
|------|------|------|
| Storyboard Script | `Storyboard_[Title].md` | 劇本基礎 |
| Dialogue Script | `Dialogue_[Title].md` | 錄音／字幕 |
| Cinematic Plan | `CinematicPlan_[Title].md` | 鏡頭構圖 |
| AI Prompt File | `AI_VideoPrompt_[Title].md` | 投喊影片代理 |
| Rubric Summary | `Rubric_[Title].md` | 品質評估 |
| Revised Script | `Revised_[Title].md` | 精修版本 |
| Project Readme | `README_[Title].md` | 總覽與版本 |

---

## ⚙️ Auto-Attach Rules（自動附加規則）
- Starter 1 完成後：每個輸出檔尾部自動附上本表。  
- `/export_package` 指令：重新生成索引並更新各檔尾。  
- `/generate_video_prompt`：為 AI Prompt 檔單獨附表。  

---

## 🧩 Integration（整合模組）
- AI Video Production Package Module  
- Cinematic Framing & Shot Support Module  
- Rubric Evaluation Module  

---

## 📘 References
- AI Video Production Package Guide.md  
- AI Video Prompt Template v2.0.md

