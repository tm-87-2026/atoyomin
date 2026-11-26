"""合成会話から作った構造化所見と失敗時の完成判定を確認する。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]
FIXTURES = Path(__file__).parent / "fixtures"
SCRIPT = REPOSITORY_ROOT / ".agents/skills/conversation-review/scripts/extract_signals.py"
LOGS = (FIXTURES / "synthetic-one.jsonl", FIXTURES / "synthetic-two.jsonl")


class SyntheticReviewTest(unittest.TestCase):
    """機械候補と意味上の所見を原文までたどって検証する。"""

    @classmethod
    def setUpClass(cls) -> None:
        """合成ログ、構造化レビュー、機械シグナルを読み込む。"""

        cls.records = {
            path.name: [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            for path in LOGS
        }
        cls.review = json.loads(
            (FIXTURES / "synthetic-review.json").read_text(encoding="utf-8")
        )
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *(str(path) for path in LOGS)],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr)
        cls.signals = json.loads(result.stdout)

    def test_hand_counted_machine_signals_match_synthetic_logs(self) -> None:
        """全シグナルの値と候補位置を手計算値へ照合する。"""

        sessions = {item["session_id"]: item for item in self.signals["sessions"]}
        planning = sessions["planning"]
        implementation = sessions["implementation"]
        self.assertEqual((planning["message_count"], planning["rally_count"]), (11, 5))
        self.assertEqual((implementation["message_count"], implementation["rally_count"]), (6, 3))
        self.assertEqual(self.signals["totals"]["rally_count"], 8)
        self.assertEqual(self.signals["totals"]["message_count"], 17)
        self.assertEqual(
            self.signals["totals"]["character_count"],
            sum(len(record["message"]) for records in self.records.values() for record in records),
        )
        self.assertEqual(
            self._candidate_lines("correction_intervention_candidates"),
            {
                ("synthetic-one.jsonl", 5),
                ("synthetic-one.jsonl", 7),
                ("synthetic-two.jsonl", 1),
                ("synthetic-two.jsonl", 3),
            },
        )
        self.assertEqual(
            self._candidate_lines("confirmation_question_candidates"),
            {("synthetic-one.jsonl", 6), ("synthetic-two.jsonl", 4)},
        )
        repetitions = planning["exact_human_instruction_repetitions"]
        self.assertEqual(repetitions["repeated_normalized_value_count"], 1)
        self.assertEqual(repetitions["repeated_occurrence_count"], 2)
        self.assertEqual(
            [item["location"]["line_start"] for item in repetitions["groups"][0]["occurrences"]],
            [9, 11],
        )
        self.assertEqual(self.signals["long_session_candidates"]["threshold_session_keys"], [])
        self.assertIn(planning["session_key"], self.signals["long_session_candidates"]["top_session_keys"])

    def test_semantic_decisions_are_separate_from_intentional_false_positives(self) -> None:
        """表層語、疑問符、完全一致の偽陽性を機械候補から除外できる。"""

        classifications = self.review["semantic_classification"]
        for name, machine_signal in (
            ("correction_intervention", "correction_intervention_candidates"),
            ("confirmation_question", "confirmation_question_candidates"),
        ):
            expected = {tuple(item) for item in classifications[name]["machine_candidate_lines"]}
            self.assertEqual(expected, self._candidate_lines(machine_signal))
            decided = {
                tuple(item)
                for status in ("adopted", "rejected", "undetermined")
                for item in classifications[name][status]
            }
            self.assertEqual(decided, expected)
        repetition = classifications["exact_repetition"]
        self.assertEqual(repetition["adopted"], [])
        self.assertEqual(
            {tuple(item) for item in repetition["rejected"]},
            {("synthetic-one.jsonl", 9), ("synthetic-one.jsonl", 11)},
        )

    def test_findings_evaluate_human_actions_and_preserve_all_evidence(self) -> None:
        """継続・改善所見を人間の発言と全根拠位置へ照合する。"""

        findings = self.review["findings"]
        self.assertEqual({item["kind"] for item in findings}, {"continue", "improve"})
        self.assertTrue(all(item["subject"] == "human" for item in findings))
        self.assertTrue(all(item["scope"] == "cross_log" for item in findings))
        self.assertEqual(len(findings[0]["evidence"]), 3)
        self.assertEqual(len(findings[1]["evidence"]), 3)
        self.assertEqual(
            {evidence["log"] for evidence in findings[1]["evidence"]},
            {"synthetic-one.jsonl", "synthetic-two.jsonl"},
        )
        for finding in findings:
            self.assertNotIn("Codex", finding["title"])
            for evidence in finding["evidence"]:
                record = self.records[evidence["log"]][evidence["line"] - 1]
                self.assertEqual(record["session_id"], evidence["session_id"])
                self.assertEqual(record["speaker"], "human")
                self.assertEqual(record["message"], evidence["quote"])

    def test_improvement_separates_practice_statement_inference_and_limits(self) -> None:
        """改善所見が外部根拠の種類と適用・不明条件を混同しない。"""

        improvement = next(
            item for item in self.review["findings"] if item["kind"] == "improve"
        )
        practice = improvement["practice"]
        self.assertEqual(practice["id"], "PRACTICE-008")
        for field in (
            "official_statement",
            "log_inference",
            "applicability",
            "unknown_conditions",
        ):
            with self.subTest(field=field):
                self.assertTrue(practice[field])
        self.assertEqual(len(set(practice.values())), len(practice))

    def test_failures_block_completion_and_unobservable_compression_is_unknown(self) -> None:
        """処理失敗は完成を妨げ、圧縮観測不能は不明として分ける。"""

        completion = self.review["completion"]
        self.assertEqual(completion["status"], "incomplete")
        self.assertFalse(completion["invalid_jsonl_is_complete"])
        self.assertFalse(completion["partial_child_failure_is_complete"])
        self.assertGreaterEqual(len(completion["reasons"]), 2)

        compression = self.review["context_compression"]
        self.assertEqual(compression["status"], "unknown")
        self.assertTrue(compression["reason"])
        self.assertFalse(compression["blocks_completion_by_itself"])

        with tempfile.TemporaryDirectory() as directory:
            broken = Path(directory) / "broken.jsonl"
            broken.write_text('{"session_id":"broken"}\n', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(broken)],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("line 1", result.stderr)

    def _candidate_lines(self, signal_name: str) -> set[tuple[str, int]]:
        """指定した機械候補のログ名と開始行を返す。

        Args:
            signal_name: セッション結果内の候補シグナル名。

        Returns:
            ログ名と候補開始行の組。
        """

        return {
            (Path(candidate["location"]["log_path"]).name, candidate["location"]["line_start"])
            for session in self.signals["sessions"]
            for candidate in session[signal_name]["candidates"]
        }


if __name__ == "__main__":
    unittest.main()
