"""会話記録を監査ログへ変換する処理の単体テスト。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.codex_audit.transcript import TranscriptFormatError, update_branch_audit


FIXTURE = Path(__file__).parent / "fixtures" / "transcript.jsonl"


class TranscriptTest(unittest.TestCase):
    """可視会話の抽出と異常入力の扱いを確認する。"""

    def test_exports_only_visible_conversation_messages(self) -> None:
        """内部メッセージを除き、監査ログに必要な項目だけを出力する。"""

        # fixtureには内部メッセージも含め、出力から除外されることを確認する。
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = update_branch_audit(
                repository_root=root,
                branch="env/26",
                session_id="session-1",
                transcript=FIXTURE,
            )

            records = [
                json.loads(line)
                for line in destination.read_text(encoding="utf-8").splitlines()
            ]

            self.assertEqual(destination, root / "docs/audit/env-26.jsonl")
            self.assertEqual(
                [(record["speaker"], record["phase"], record["message"]) for record in records],
                [
                    ("human", None, "Please inspect the project."),
                    ("codex", "commentary", "I’ll inspect the project first."),
                    ("codex", "final_answer", "The inspection is complete."),
                ],
            )

    def test_fails_when_conversation_events_are_missing(self) -> None:
        """可視会話がない記録を、正常な空ログとして扱わない。"""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            transcript = root / "transcript.jsonl"
            transcript.write_text(
                '{"timestamp":"2026-10-31T01:00:00Z","type":"session_meta","payload":{}}\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                TranscriptFormatError, "no supported conversation events"
            ):
                update_branch_audit(
                    repository_root=root,
                    branch="env/26",
                    session_id="session-1",
                    transcript=transcript,
                )


if __name__ == "__main__":
    unittest.main()
