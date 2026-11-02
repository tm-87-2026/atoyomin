"""二形式の会話抽出と差分更新の回帰を検証する。"""

import json
import tempfile
import unittest
from pathlib import Path

from tools.codex_audit.transcript import extract_messages, update_branch_audit, TranscriptFormatError


class IncrementalTest(unittest.TestCase):
    """原本の形式と既存公開ログの保持を確認する。"""

    def event(self, text, kind="event_msg", role="user"):
        """指定形式の可視会話を作る。

        Args:
            text: 発言内容。
            kind: 保存形式。
            role: 発言者。

        Returns:
            JSONLに保存するイベント。
        """

        payload = {"type": "user_message" if role == "user" else "agent_message", "message": text}
        if kind == "response_item":
            payload = {"type": "message", "role": role, "content": [{"type": "input_text", "text": text}]}
        return {"timestamp": "2026-11-02T01:00:00Z", "type": kind, "payload": payload}

    def save(self, path, events):
        """試験用の原本を保存する。

        Args:
            path: 保存先。
            events: 保存するイベント。
        """

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(event) + "\n" for event in events))

    def test_formats_and_repeated_messages(self):
        """二形式の重複だけを除き、同文の繰り返しは保持する。"""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.jsonl"
            for kinds in [("event_msg",), ("response_item",), ("event_msg", "response_item")]:
                self.save(path, [self.event("hello", kind) for kind in kinds for _ in range(2)])
                self.assertEqual(len(list(extract_messages(path, "test"))), 2)

    def test_incremental_preserves_masks_and_retries(self):
        """複数セッションの再実行と追記でマスクを保持する。"""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.jsonl"
            self.save(source, [self.event("secret")])
            destination = update_branch_audit(repository_root=root, branch="test", session_id="one", transcript=source)
            destination.write_text(destination.read_text().replace("secret", "[MASKED]"))
            self.save(source, [self.event("second", "response_item")])
            update_branch_audit(repository_root=root, branch="test", session_id="two", transcript=source)
            self.save(source, [self.event("secret"), self.event("new")])
            for _ in range(2):
                update_branch_audit(repository_root=root, branch="test", session_id="one", transcript=source)
            records = [json.loads(line) for line in destination.read_text().splitlines()]
            self.assertEqual([item["message"] for item in records], ["[MASKED]", "new", "second"])

    def test_bad_history_does_not_block_current_session(self):
        """不正な過去原本を報告しながら今回の会話を保存する。"""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staging = root / ".codex/audit-staging"
            staging.mkdir(parents=True)
            (staging / "test--bad.jsonl").write_text("broken\n")
            self.save(staging / "test--old.jsonl", [self.event("old", "response_item")])
            source = root / "source.jsonl"
            self.save(source, [self.event("current")])
            for _ in range(2):
                with self.assertRaisesRegex(TranscriptFormatError, "bad"):
                    update_branch_audit(repository_root=root, branch="test", session_id="current", transcript=source)
            records = (root / "docs/audit/test.jsonl").read_text().splitlines()
            self.assertEqual(len(records), 2)
            status = json.loads((staging / "test.status.json").read_text())
            self.assertEqual(status["errors"][0]["session"], "bad")
            self.assertEqual(status["message_count"], 2)

    def test_internal_content_is_excluded(self):
        """環境情報、開発者指示、推論、内部セッションを除外する。"""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.jsonl"
            analysis = self.event("private", "response_item", "assistant")
            analysis["payload"]["channel"] = "analysis"
            self.save(path, [self.event("visible", "response_item"),
                             self.event("# AGENTS.md instructions for /tmp", "response_item"),
                             self.event("internal", "response_item", "developer"), analysis])
            self.assertEqual([item.message for item in extract_messages(path, "test")], ["visible"])
            self.save(path, [{"type": "session_meta", "payload": {"source": {"subagent": "approval_review"}}}, self.event("internal")])
            self.assertEqual(list(extract_messages(path, "test")), [])

    def test_rewritten_source_is_reported(self):
        """原本の書き換えを検知して既存ログを保持する。"""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.jsonl"
            self.save(source, [self.event("original")])
            destination = update_branch_audit(repository_root=root, branch="test", session_id="one", transcript=source)
            self.save(source, [self.event("rewritten")])
            with self.assertRaisesRegex(TranscriptFormatError, "prefix changed"):
                update_branch_audit(repository_root=root, branch="test", session_id="one", transcript=source)
            self.assertIn("original", destination.read_text())
