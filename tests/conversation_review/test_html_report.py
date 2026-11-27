"""自己完結HTMLレポート生成器の契約を合成入力で検証する。"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / ".agents/skills/conversation-review/scripts/render_report.py"
SPEC = importlib.util.spec_from_file_location("render_report", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def report() -> dict:
    """表示・安全性・品質ゲートを通る最小の合成レポートを返す。"""

    return {
        "title": "合成 <振り返り>",
        "generated_at": "2026-11-27T12:00:00Z",
        "period": "2026-11-01〜2026-11-27",
        "summary": "人間の判断 & 指示の傾向です。",
        "targets": {"version": 1, "targets": [{
            "repository": "owner/repo", "path": "docs/audit/example.jsonl",
            "sha256": "a" * 64, "method": "matched", "pr": 12, "branch": "feat/example",
        }]},
        "metrics": [{
            "id": "one", "label": "ログ <A>", "sessions": 2, "human_turns": 10,
            "codex_turns": 8, "rallies": 7, "confirmation_adopted": 2,
            "long_sessions": 1, "longest_messages": 120, "longest_characters": 41000,
            "correction_adopted": 0, "repetition_adopted": 0,
        }],
        "evidence": [{
            "id": "E1", "speaker": "human", "log": "docs/audit/example.jsonl",
            "session_id": "s<1>", "line": 4, "quote": "範囲を <script>alert(1)</script> に限定する",
        }],
        "findings": [{
            "id": "F1", "kind": "continue", "title": "範囲を先に示す",
            "observation": "人間が変更範囲を明示した。", "interpretation": "境界を共有できる。",
            "proposal": "依頼時に対象を示す。", "scope": "単一セッション",
            "reusable": True, "actionable": True, "evidence_complete": True,
            "claims": [{"id": "C1", "text": "変更範囲を明示した", "evidence_ids": ["E1"]}],
        }],
        "actions": [{"kind": "instruction", "text": "対象範囲を最初に伝える。", "finding_id": "F1"}],
        "limitations": ["成果はログだけでは不明。"],
    }


class HtmlReportTest(unittest.TestCase):
    def test_chart_header_rows_do_not_share_the_tick_label_band(self) -> None:
        document = MODULE.render_report(report())

        self.assertIn('<rect x="150" y="2" width="14" height="14"/>', document)
        self.assertIn('<text x="450" y="14" text-anchor="end">単位: セッション</text>', document)
        self.assertIn('<text x="150" y="38">0.0</text>', document)
        self.assertNotIn('<rect x="300" y="2" width="14" height="14"/>', document)

    def test_preserves_source_newlines_in_escaped_text_without_splitting_html(self) -> None:
        data = report()
        data["evidence"][0]["quote"] = "前半\n後半"

        document = MODULE.render_report(data)

        self.assertIn("<q>前半&#10;後半</q>", document)

    def test_renders_real_self_contained_html_from_structured_input(self) -> None:
        document = MODULE.render_report(report())
        self.assertTrue(document.startswith("<!doctype html>"))
        self.assertEqual(document.count("<!-- conversation-review-targets "), 1)
        self.assertNotIn("<script", document.lower())
        self.assertNotIn("src=", document.lower())
        self.assertNotIn("@import", document.lower())
        self.assertNotIn("https://", document)
        self.assertIn("合成 &lt;振り返り&gt;", document)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", document)
        self.assertIn("role=\"img\"", document)
        self.assertIn("aria-labelledby=", document)
        self.assertIn("<figure>", document)
        self.assertIn("<figcaption>", document)
        self.assertIn("単位: セッション", document)
        self.assertIn(">2/8 (25.0%)<", document)
        self.assertIn("訂正・介入と反復は、全対象で0件", document)
        self.assertIn("<details><summary>根拠と監査情報</summary>", document)
        self.assertNotIn("<details open", document)

    def test_allows_zero_findings_and_actions(self) -> None:
        value = report()
        value["evidence"] = []
        value["findings"] = []
        value["actions"] = []
        document = MODULE.render_report(value)
        self.assertEqual(document.count("確定所見は0件です。"), 2)
        self.assertIn("確定所見に基づく次回行動はありません", document)

    def test_confirmation_rate_with_zero_denominator_is_unavailable(self) -> None:
        value = report()
        metric = value["metrics"][0]
        metric.update({"codex_turns": 0, "rallies": 0, "confirmation_adopted": 0})
        document = MODULE.render_report(value)
        chart = document.split('<h3 id="confirmation-title">', 1)[1].split("</figure>", 1)[0]
        self.assertIn("取得不能（Codexターン 0）", chart)
        self.assertIn("0/0（取得不能）", chart)
        self.assertIn("<td>取得不能</td>", chart)
        self.assertNotIn("0.0%", chart)
        self.assertNotIn('<rect x="150" y="36"', chart)

    def test_rejects_findings_that_fail_gates_or_claim_coverage(self) -> None:
        for mutation in ("gate", "orphan_evidence", "non_human", "improvement"):
            value = report()
            finding = value["findings"][0]
            if mutation == "gate":
                finding["reusable"] = False
            elif mutation == "orphan_evidence":
                finding["claims"][0]["evidence_ids"] = ["missing"]
            elif mutation == "non_human":
                value["evidence"][0]["speaker"] = "codex"
            else:
                finding["kind"] = "improve"
            with self.subTest(mutation=mutation), self.assertRaises(MODULE.ReportError):
                MODULE.render_report(value)

    def test_rejects_orphan_action_and_unsafe_url(self) -> None:
        value = report()
        value["actions"][0]["finding_id"] = "missing"
        with self.assertRaises(MODULE.ReportError):
            MODULE.render_report(value)
        value = report()
        value["findings"][0].update({
            "kind": "improve", "practice_applicable": True,
            "practice": {"id": "P1", "url": "javascript:alert(1)", "official_statement": "記述",
                         "log_inference": "推論", "applicability": "条件", "unknown_conditions": "不明"},
        })
        with self.assertRaises(MODULE.ReportError):
            MODULE.render_report(value)

    def test_rejects_invalid_metric_boundaries_and_zero_evidence_line(self) -> None:
        mutations = {
            "correction_over_human": lambda value: value["metrics"][0].update(correction_adopted=11),
            "repetition_over_human": lambda value: value["metrics"][0].update(repetition_adopted=11),
            "rallies_over_human": lambda value: value["metrics"][0].update(rallies=11),
            "rallies_over_codex": lambda value: value["metrics"][0].update(rallies=9),
            "longest_without_session": lambda value: value["metrics"][0].update(sessions=0, long_sessions=0),
            "zero_longest_messages": lambda value: value["metrics"][0].update(longest_messages=0),
            "zero_evidence_line": lambda value: value["evidence"][0].update(line=0),
        }
        for name, mutate in mutations.items():
            value = report()
            mutate(value)
            with self.subTest(name=name), self.assertRaises(MODULE.ReportError):
                MODULE.render_report(value)
    def test_reads_html_and_legacy_markdown_targets_and_validates_them(self) -> None:
        targets = report()["targets"]
        encoded = json.dumps(targets, separators=(",", ":"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            html_path = root / "new.html"
            md_path = root / "old.md"
            html_path.write_text(f"<!-- conversation-review-targets {encoded} -->", encoding="utf-8")
            md_path.write_text(f"```json conversation-review-targets\n{encoded}\n```", encoding="utf-8")
            self.assertEqual(MODULE.read_targets(html_path), targets)
            self.assertEqual(MODULE.analyzed_keys([html_path, md_path]), {("owner/repo", "docs/audit/example.jsonl")})
            html_path.write_text(html_path.read_text() + f"\n<!-- conversation-review-targets {encoded} -->", encoding="utf-8")
            with self.assertRaises(MODULE.ReportError):
                MODULE.read_targets(html_path)
        for change in ("version", "duplicate", "path", "sha", "method", "comment"):
            value = report()["targets"]
            target = value["targets"][0]
            if change == "version": value["version"] = 2
            elif change == "duplicate": value["targets"].append(dict(target))
            elif change == "path": target["path"] = "../audit.jsonl"
            elif change == "sha": target["sha256"] = "ABC"
            elif change == "method": target["method"] = "guess"
            else: target["branch"] = "bad--comment"
            with self.subTest(change=change), self.assertRaises(MODULE.ReportError):
                MODULE.validate_targets(value)

    def test_save_is_non_overwriting_and_cleans_temporary_file_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "report.html"
            MODULE.save_report(report(), destination)
            original = destination.read_bytes()
            with self.assertRaises(FileExistsError):
                MODULE.save_report(report(), destination)
            self.assertEqual(destination.read_bytes(), original)
            self.assertEqual(list(Path(directory).glob(".report.html.*")), [])


if __name__ == "__main__":
    unittest.main()
