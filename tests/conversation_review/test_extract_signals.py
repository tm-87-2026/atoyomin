"""会話監査ログの機械的シグナル抽出を確認する。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]
SCRIPT = (
    REPOSITORY_ROOT
    / ".agents/skills/conversation-review/scripts/extract_signals.py"
)


class ExtractSignalsTest(unittest.TestCase):
    """手計算できる会話と不正入力に対する出力を確認する。"""

    def run_script(self, *paths: Path) -> subprocess.CompletedProcess[str]:
        """指定した監査ログに対してシグナル抽出CLIを実行する。

        Args:
            *paths: 入力に渡すJSONLファイル。

        Returns:
            CLIの終了結果。
        """

        return subprocess.run(
            [sys.executable, str(SCRIPT), *(str(path) for path in paths)],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_extracts_hand_counted_signals_and_locations(self) -> None:
        """話者まとまり、表層候補、反復、長さを手計算値と照合する。"""

        records = [
            self.record("s1", "human", "Please run tests."),
            self.record("s1", "human", "Use the focused suite."),
            self.record("s1", "codex", "I will inspect it."),
            self.record("s1", "codex", "May I update it?"),
            self.record("s1", "human", "No, stop and revert that."),
            self.record("s1", "codex", "Stopped."),
            self.record(
                "s1", "human", "  PLEASE\n run   tests.  use the focused suite.  "
            ),
            self.record("s2", "human", "変更しないでください"),
            self.record("s2", "codex", "どちらを使いますか？"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            audit = Path(directory) / "sample.jsonl"
            audit.write_text(
                "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
                encoding="utf-8",
            )

            result = self.run_script(audit)

        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        sessions = {session["session_id"]: session for session in output["sessions"]}
        first = sessions["s1"]
        self.assertEqual(first["message_count"], 7)
        self.assertEqual(first["human_turn_count"], 3)
        self.assertEqual(first["codex_turn_count"], 2)
        self.assertEqual(first["rally_count"], 2)
        self.assertEqual(
            first["character_count"], sum(len(record["message"]) for record in records[:7])
        )
        self.assertEqual(first["correction_intervention_candidates"]["candidate_count"], 1)
        self.assertEqual(
            first["correction_intervention_candidates"]["candidates"][0]["location"]["line_numbers"],
            [5],
        )
        self.assertEqual(first["confirmation_question_candidates"]["candidate_count"], 1)
        self.assertEqual(
            first["confirmation_question_candidates"]["candidates"][0]["location"]["line_numbers"],
            [3, 4],
        )
        repetition = first["exact_human_instruction_repetitions"]
        self.assertEqual(repetition["repeated_normalized_value_count"], 1)
        self.assertEqual(repetition["repeated_occurrence_count"], 2)
        self.assertEqual(
            [item["location"]["line_numbers"] for item in repetition["groups"][0]["occurrences"]],
            [[1, 2], [7]],
        )
        self.assertEqual(sessions["s2"]["rally_count"], 1)
        self.assertEqual(
            sessions["s2"]["correction_intervention_candidates"]["candidate_count"], 1
        )
        self.assertEqual(
            sessions["s2"]["confirmation_question_candidates"]["candidate_count"], 1
        )
        self.assertEqual(output["totals"]["rally_count"], 3)
        self.assertEqual(output["long_session_candidates"]["thresholds"]["message_count"], 100)
        self.assertEqual(output["long_session_candidates"]["thresholds"]["character_count"], 40000)
        self.assertEqual(output["long_session_candidates"]["top_session_keys"], [first["session_key"]])

    def test_keeps_same_session_in_different_logs_separate(self) -> None:
        """同じsession_idでもログパスが異なれば別の分析単位にする。"""

        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for name in ("one.jsonl", "two.jsonl"):
                path = Path(directory) / name
                path.write_text(
                    json.dumps(self.record("shared", "human", name)) + "\n",
                    encoding="utf-8",
                )
                paths.append(path)

            result = self.run_script(*paths)

        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(len(output["sessions"]), 2)
        self.assertEqual({item["session_id"] for item in output["sessions"]}, {"shared"})
        self.assertEqual(len({item["log_path"] for item in output["sessions"]}), 2)
        self.assertTrue(
            all(
                item["confirmation_question_candidates"]["candidate_rate_status"]
                == "unavailable_no_codex_turns"
                and item["confirmation_question_candidates"]["candidate_rate_per_codex_turn"]
                is None
                for item in output["sessions"]
            )
        )

    def test_reports_input_path_line_and_field_for_invalid_jsonl(self) -> None:
        """不正行のファイル、行番号、原因を利用者へ返す。"""

        with tempfile.TemporaryDirectory() as directory:
            audit = Path(directory) / "broken.jsonl"
            audit.write_text(
                json.dumps(self.record("s1", "human", "ok"))
                + "\n"
                + json.dumps(self.record("s1", "system", "bad"))
                + "\n",
                encoding="utf-8",
            )

            result = self.run_script(audit)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn(f"{audit}: line 2", result.stderr)
        self.assertIn("speaker", result.stderr)

    @staticmethod
    def record(session_id: str, speaker: str, message: str) -> dict[str, object]:
        """テスト用の監査ログレコードを作る。

        Args:
            session_id: セッション識別子。
            speaker: 発言者。
            message: 発言本文。

        Returns:
            監査ログの1レコード。
        """

        return {
            "timestamp": "2026-11-26T00:00:00Z",
            "session_id": session_id,
            "speaker": speaker,
            "message": message,
            "phase": None,
        }


if __name__ == "__main__":
    unittest.main()
