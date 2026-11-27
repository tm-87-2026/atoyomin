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

        for signal in (
            "ラリー",
            "訂正・介入",
            "確認質問",
            "人間の指示の反復",
            "セッションの長大化",
        ):
            with self.subTest(signal=signal):
                self.assertIn(f"| {signal} |", self.template)
        for phrase in (
            "値から良否を決めるものではない",
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

    def test_template_explains_signals_and_uses_log_dashboard(self) -> None:
        """初見向け説明とログ別の比較表を機械データの主表示にする。"""

        for signal in ("ラリー", "訂正・介入", "確認質問", "人間の指示の反復", "セッションの長大化"):
            with self.subTest(signal=signal):
                self.assertIn(f"| {signal} |", self.template)
        for phrase in (
            "| シグナル | 何を数えるか | 値から何を探せるか |",
            "| ブランチ・ログ | 規模（セッション／人間ターン／Codexターン） |",
            "機械候補／文脈上の採用／採用率（採用÷人間ターン）",
            "機械候補／文脈上の採用／採用率（採用÷Codexターン）",
            "読む入口・探せること",
            "全体合計（補助）",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.template)
        dashboard = self.template.split("### ログ別ダッシュボード", 1)[1].split(
            "### ラリー数の比較", 1
        )[0]
        self.assertNotIn("読む理由と限界", dashboard)

    def test_template_requires_portable_rally_chart(self) -> None:
        """ラリー比較を通常Markdownで確実に表示できる等幅グラフにする。"""

        chart = self.template.split("### ラリー数の比較", 1)[1].split(
            "## 継続すべき点", 1
        )[0]
        self.assertIn("```text", chart)
        self.assertIn("[棒。末尾に表と同じ正確なラリー数]", chart)
        self.assertNotIn("```mermaid", chart)

    def test_findings_and_next_actions_keep_human_behavior_as_subject(self) -> None:
        """所見を再利用可能な人間の行動にし、次回行動の主体を限定する。"""

        for phrase in (
            "複数タスクで再利用できる人間のCodex活用行動",
            "個別タスクの出来事は観察事実と根拠例",
            "提案: [複数タスクで再利用できる、人間がCodexを使う行動]",
            "人間がCodexへ与える指示",
            "人間が事前に行う判断",
            "人間が逸脱時に行う介入",
            "人間が続ける習慣",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.template)
        actions = self.template.split("## 次回に試す行動", 1)[1].split(
            "## 不明・未分析・失敗・限界", 1
        )[0]
        for forbidden in ("Codexが分析する", "Codexが実装する", "テストを実行する", "PRを作成する"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, actions)

    def test_skill_keeps_branch_list_out_of_report_title(self) -> None:
        """対象ブランチの列挙をタイトルではなく概要・監査詳細へ置く。"""

        self.assertIn("対象ブランチを列挙しない", self.skill)
        self.assertIn("対象は概要と監査詳細へ置く", self.skill)


if __name__ == "__main__":
    unittest.main()
