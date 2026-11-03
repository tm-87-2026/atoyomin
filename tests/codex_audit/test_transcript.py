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

    def test_preserves_split_start_and_mask_on_repeated_updates(self) -> None:
        """分割前の発言を再追加せず、マスクを保持して後続発言を追記する。"""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staging = root / ".codex/audit-staging"
            staging.mkdir(parents=True)
            status = staging / "docs-23.status.json"
            status.write_text(json.dumps({"source_offsets": {"session-1": 1}}))
            source = root / "source.jsonl"
            source.write_bytes(FIXTURE.read_bytes())
            destination = update_branch_audit(
                repository_root=root, branch="docs/23", session_id="session-1", transcript=source
            )
            records = [json.loads(line) for line in destination.read_text().splitlines()]
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]["speaker"], "codex")
            records[0]["message"] = "[REDACTED]"
            destination.write_text("".join(json.dumps(row) + "\n" for row in records))
            before = destination.read_bytes()
            update_branch_audit(
                repository_root=root, branch="docs/23", session_id="session-1", transcript=source
            )
            self.assertEqual(destination.read_bytes(), before)
            with source.open("a") as target:
                target.write(json.dumps({"timestamp": "2026-11-03T00:00:00Z", "type": "event_msg",
                                         "payload": {"type": "user_message", "message": "Next"}}) + "\n")
            update_branch_audit(
                repository_root=root, branch="docs/23", session_id="session-1", transcript=source
            )
            records = [json.loads(line) for line in destination.read_text().splitlines()]
            self.assertEqual(len(records), 3)
            self.assertEqual(records[0]["message"], "[REDACTED]")
            self.assertEqual(records[-1]["message"], "Next")

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
