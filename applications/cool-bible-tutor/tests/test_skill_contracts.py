import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).parents[1]


def read(relative: str) -> str:
    return (PLUGIN_ROOT / relative).read_text(encoding="utf-8")


class SkillContractTests(unittest.TestCase):
    def test_session_orchestrator_preserves_v24_interaction_contract(self):
        skill = read("skills/guiding-bible-tutor-sessions/SKILL.md")
        interaction = read(
            "skills/guiding-bible-tutor-sessions/references/interaction-contract.md"
        )
        safety = read(
            "skills/guiding-bible-tutor-sessions/references/scripture-theology-safety.md"
        )
        metadata = read(
            "skills/guiding-bible-tutor-sessions/agents/openai.yaml"
        )

        self.assertIn("description: Use when", skill)
        self.assertIn("提問 → 等待 → 回應 → 推進", interaction)
        self.assertIn("1–3", interaction)
        for state in ("不知道或不確定", "不完整", "錯誤或偏離", "部分正確", "完整或正確", "空白"):
            self.assertIn(state, interaction)
        for sibling in (
            "observing-biblical-passages",
            "interpreting-biblical-passages",
            "applying-biblical-truth",
            "discussing-biblical-theology",
            "supporting-biblical-exegesis",
            "comparing-biblical-words-and-translations",
            "retrieving-chinese-union-version-scripture",
        ):
            self.assertIn(sibling, skill)
        self.assertIn("繁體中文", skill)
        self.assertIn("正統基督教", safety)
        self.assertIn("內部設定", safety)
        self.assertIn("$guiding-bible-tutor-sessions", metadata)

    def test_observation_skill_covers_steps_one_through_four(self):
        skill = read("skills/observing-biblical-passages/SKILL.md")
        observation = read("skills/observing-biblical-passages/references/observation.md")
        relationships = read("skills/observing-biblical-passages/references/relationships.md")
        structure = read("skills/observing-biblical-passages/references/structure.md")
        questions = read("skills/observing-biblical-passages/references/questions.md")
        metadata = read("skills/observing-biblical-passages/agents/openai.yaml")

        self.assertIn("description: Use when", skill)
        self.assertIn("只載入目前階段", skill)
        self.assertIn("17 項", observation)
        self.assertIn("16 項", relationships)
        self.assertIn("明顯結構", structure)
        self.assertIn("隱藏結構", structure)
        for question_type in ("定義性", "邏輯性", "引申性"):
            self.assertIn(question_type, questions)
        self.assertIn("interpreting-biblical-passages", skill)
        self.assertIn("$observing-biblical-passages", metadata)

    def test_interpretation_skill_covers_steps_five_through_seven(self):
        skill = read("skills/interpreting-biblical-passages/SKILL.md")
        answering = read("skills/interpreting-biblical-passages/references/answering.md")
        synthesis = read("skills/interpreting-biblical-passages/references/synthesis.md")
        theme = read("skills/interpreting-biblical-passages/references/theme.md")
        metadata = read("skills/interpreting-biblical-passages/agents/openai.yaml")

        self.assertIn("description: Use when", skill)
        self.assertIn("只載入目前階段", skill)
        for principle in (
            "實義解釋", "上下文理", "歷史文化背景", "語法結構",
            "詞語研究", "以經解經", "比較經文", "化解象徵",
        ):
            self.assertIn(principle, answering)
        self.assertIn("最多示範一題", answering)
        self.assertIn("一至兩句", synthesis)
        self.assertIn("自己的話", synthesis)
        self.assertIn("完整的神學性命題", theme)
        self.assertIn("整卷書", theme)
        self.assertIn("supporting-biblical-exegesis", skill)
        self.assertIn("comparing-biblical-words-and-translations", skill)
        self.assertIn("applying-biblical-truth", skill)
        self.assertIn("$interpreting-biblical-passages", metadata)

    def test_application_skill_covers_steps_eight_through_ten(self):
        skill = read("skills/applying-biblical-truth/SKILL.md")
        principles = read("skills/applying-biblical-truth/references/principles.md")
        specifics = read("skills/applying-biblical-truth/references/specifics.md")
        action = read("skills/applying-biblical-truth/references/action.md")
        metadata = read("skills/applying-biblical-truth/agents/openai.yaml")

        self.assertIn("description: Use when", skill)
        self.assertIn("只載入目前階段", skill)
        self.assertIn("文化中立性", principles)
        self.assertIn("全書神學一致", principles)
        self.assertIn("正面", principles)
        for dimension in ("Specific", "Measurable", "Achievable", "Relevant", "Time-bound"):
            self.assertIn(dimension, specifics)
        for scope in ("對神", "對人", "對己", "知識", "態度", "行動"):
            self.assertIn(scope, specifics)
        for follow_through in ("立即", "提醒", "禱告", "回顧", "自願"):
            self.assertIn(follow_through, action)
        self.assertIn("專業協助", skill)
        self.assertIn("$applying-biblical-truth", metadata)

    def test_theology_discussion_is_socratic_and_fair(self):
        skill = read("skills/discussing-biblical-theology/SKILL.md")
        metadata = read("skills/discussing-biblical-theology/agents/openai.yaml")

        self.assertIn("description: Use when", skill)
        self.assertIn("聖經起點", skill)
        self.assertIn("1–3", skill)
        self.assertIn("等待", skill)
        self.assertIn("核心教義", skill)
        self.assertIn("次要", skill)
        self.assertIn("宗派", skill)
        self.assertIn("不製造假平衡", skill)
        self.assertIn("另一段相關經文", skill)
        self.assertIn("supporting-biblical-exegesis", skill)
        self.assertIn("$discussing-biblical-theology", metadata)

    def test_exegesis_support_preserves_eight_contexts(self):
        skill = read("skills/supporting-biblical-exegesis/SKILL.md")
        contexts = read("skills/supporting-biblical-exegesis/references/eight-contexts.md")
        metadata = read("skills/supporting-biblical-exegesis/agents/openai.yaml")

        self.assertIn("description: Use when", skill)
        self.assertIn("一至兩種", skill)
        for context in (
            "文本出現次序形成的上下文", "經文交織／互涉", "史地文化背景",
            "文學與文法", "相同神學主題", "相同文體", "人物生平",
            "聖經敘事與神救恩歷史",
        ):
            self.assertEqual(contexts.count(f"## {context}"), 1)
        for stage in (
            "創造與墮落", "應許", "律法與國度", "被擄與盼望",
            "彌賽亞成就", "教會與再來",
        ):
            self.assertIn(stage, contexts)
        self.assertIn("不可虛構", skill)
        self.assertIn("$supporting-biblical-exegesis", metadata)

    def test_word_and_translation_comparison_has_evidence_boundaries(self):
        skill = read("skills/comparing-biblical-words-and-translations/SKILL.md")
        metadata = read("skills/comparing-biblical-words-and-translations/agents/openai.yaml")

        self.assertIn("description: Use when", skill)
        self.assertIn("具體經節", skill)
        for layer in ("詞元", "語境義", "文法", "翻譯選擇"):
            self.assertIn(layer, skill)
        self.assertIn("字源", skill)
        self.assertIn("不可", skill)
        self.assertIn("未核實", skill)
        self.assertIn("單一中文對應詞", skill)
        self.assertIn("回到整段經文", skill)
        self.assertIn("retrieving-chinese-union-version-scripture", skill)
        self.assertIn("$comparing-biblical-words-and-translations", metadata)

    def test_v24_core_coverage_matrix_is_complete(self):
        matrix = read("tests/coverage-matrix.md")
        for requirement in (
            "四種模式", "查經學習", "神學討論", "生活應用", "一般問答",
            "提問 → 等待 → 回應 → 推進", "六種回應狀態", "十個歸納階段",
            "八種合法處境", "字詞與譯本", "繁體中文", "正統基督教",
            "聖經依據", "內部設定", "已實作", "教會事工提示模板",
        ):
            self.assertIn(requirement, matrix)

    def test_scripture_retrieval_skill_requires_verified_provenance(self):
        skill = read("skills/retrieving-chinese-union-version-scripture/SKILL.md")
        trust = read(
            "skills/retrieving-chinese-union-version-scripture/references/corpus-and-verification.md"
        )
        setup = read(
            "skills/retrieving-chinese-union-version-scripture/references/setup-scripture-data.md"
        )
        metadata = read(
            "skills/retrieving-chinese-union-version-scripture/agents/openai.yaml"
        )

        self.assertIn("description: Use when", skill)
        self.assertIn("get_passage.py", skill)
        for code in ("退出碼 0", "退出碼 2", "退出碼 3"):
            self.assertIn(code, skill)
        self.assertIn("不可當作精確引文", skill)
        self.assertIn("來源檔案", trust)
        self.assertIn("來源頁碼", trust)
        self.assertIn("OCR 信心", trust)
        self.assertIn("COOL_BIBLE_TUTOR_DATA_DIR", setup)
        self.assertIn("不會自動下載", setup)
        self.assertIn("$retrieving-chinese-union-version-scripture", metadata)

    def test_rag_discovery_is_optional_reference_only_support(self):
        guiding = read("skills/guiding-bible-tutor-sessions/SKILL.md")
        theology = read("skills/discussing-biblical-theology/SKILL.md")
        exegesis = read("skills/supporting-biblical-exegesis/SKILL.md")
        retrieving = read("skills/retrieving-chinese-union-version-scripture/SKILL.md")

        for skill in (guiding, theology, exegesis):
            self.assertIn("discover_bible_references.py", skill)
        self.assertIn("退出碼 4", guiding)
        self.assertIn("候選引用", guiding)
        self.assertIn("discover_bible_references.py", retrieving)
        self.assertIn("不可把 RAG chunk 當作精確引文", retrieving)
        self.assertIn("get_passage.py", retrieving)
        self.assertIn("只有退出碼 0", retrieving)

    def test_scripture_skill_routes_human_review_without_automatic_verification(self):
        skill = read("skills/retrieving-chinese-union-version-scripture/SKILL.md")
        setup = read(
            "skills/retrieving-chinese-union-version-scripture/references/setup-scripture-data.md"
        )
        trust = read(
            "skills/retrieving-chinese-union-version-scripture/references/corpus-and-verification.md"
        )
        self.assertIn("review_cuv_index.py", skill)
        self.assertIn("不可自動核實", skill)
        self.assertIn("get_passage.py", skill)
        self.assertIn("--source-pdf", setup)
        self.assertIn("cuv-review-history.sqlite3", setup)
        self.assertIn("rag_index_state=stale", trust)


if __name__ == "__main__":
    unittest.main()
