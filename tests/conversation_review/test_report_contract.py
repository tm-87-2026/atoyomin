"""会話ログ振り返りSkillのポイント中心レポート契約を確認する。"""

from __future__ import annotations

import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]
SKILL = REPOSITORY_ROOT / ".agents/skills/conversation-review/SKILL.md"
TEMPLATE = (
    REPOSITORY_ROOT
    / ".agents/skills/conversation-review/references/report-template.md"
)


class ReportContractTest(unittest.TestCase):
    """評価対象、主構造、根拠と外部観点の必須項目を固定する。"""

    @classmethod
    def setUpClass(cls) -> None:
        """Skillとテンプレートを読み込む。"""

        cls.skill = SKILL.read_text(encoding="utf-8")
        cls.template = TEMPLATE.read_text(encoding="utf-8")

    def test_skill_limits_evaluation_and_preserves_long_log_controls(self) -> None:
        """人間だけを評価し、長いログの既存安全策を維持する。"""

        required = (
            "評価対象は人間の指示、判断、提案した進め方だけ",
            "Codexの応答は、人間が何へ反応したかを理解する前後文脈",
            "この二段階を省略しない",
            "境界の重複部分",
            "コンテキスト圧縮",
            "部分結果を完成扱いしない",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.skill)

    def test_template_uses_point_first_structure_and_traceable_findings(self) -> None:
        """継続・改善を主軸に、横断所見から全根拠へ戻れる。"""

        headings = (
            "## 機械データと読むべき位置",
            "## 継続すべき点",
            "## 改善すべき点",
            "## 次回に試す行動",
            "## 不明・未分析・失敗・限界",
        )
        positions = [self.template.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("## ブランチ別", self.template)
        self.assertNotIn("## セッション別", self.template)
        for phrase in (
            "単一セッション／横断傾向",
            "対象ログとセッションを列挙",
            "session_id=[ID]",
            "必要最小限の引用",
            "観察事実",
            "解釈",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.template)

    def test_template_separates_signal_drilldown_and_practice_reasoning(self) -> None:
        """シグナルを入口にし、改善所見の根拠種別を分離する。"""

        for signal in ("ラリー", "修正・介入", "確認質問", "反復", "長大化"):
            with self.subTest(signal=signal):
                self.assertIn(f"| {signal} |", self.template)
        for phrase in (
            "値から良否を決めるためではなく",
            "読むべき位置",
            "PRACTICE-IDと公式資料URL",
            "公式資料の明記",
            "ログ評価への推論",
            "適用条件",
            "不明条件",
            "十分な根拠がない候補はこの節へ入れず",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.template)


if __name__ == "__main__":
    unittest.main()
