"""Codex Stop Hookから監査ログを更新する連携テスト。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]
FIXTURE = Path(__file__).parent / "fixtures" / "transcript.jsonl"


class AuditTranscriptHookTest(unittest.TestCase):
    """Hookが実行時の入力を受け取り、監査ログを作ることを確認する。"""

    def test_stop_hook_exports_a_visible_conversation(self) -> None:
        """Stop Hookの標準入力から、ブランチ別の監査ログを生成する。"""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hook_directory = root / ".codex" / "hooks"
            hook_directory.parent.mkdir()

            # HookはGitルートから変換モジュールを読み込む。実際の作業ツリーを
            # 変更せずに同じ起動経路を検証するため、必要なコードだけを複製する。
            shutil.copytree(REPOSITORY_ROOT / ".codex" / "hooks", hook_directory)
            shutil.copytree(REPOSITORY_ROOT / "tools", root / "tools")

            # Hookが想定するGitリポジトリとブランチを隔離環境に用意する。
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(
                ["git", "-C", str(root), "checkout", "-q", "-b", "audit-test"],
                check=True,
            )

            # CodexがStop Hookへ渡す形式の入力を作り、Hookを起動する。
            payload = json.dumps(
                {
                    "cwd": str(root),
                    "transcript_path": str(FIXTURE),
                    "session_id": "hook-test",
                }
            )
            result = subprocess.run(
                [sys.executable, str(hook_directory / "audit_transcript.py")],
                check=True,
                input=payload,
                capture_output=True,
                text=True,
            )

            # Hookの応答と、作成された監査ログの内容を確認する。
            self.assertEqual(json.loads(result.stdout), {"continue": True})
            records = [
                json.loads(line)
                for line in (root / "docs" / "audit" / "audit-test.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(
                [(record["speaker"], record["message"]) for record in records],
                [
                    ("human", "Please inspect the project."),
                    ("codex", "I’ll inspect the project first."),
                    ("codex", "The inspection is complete."),
                ],
            )


            # 形式不一致の過去記録があっても、Hookは今回分を保存して警告する。
            staging = root / ".codex" / "audit-staging"
            (staging / "audit-test--broken.jsonl").write_text("invalid\n", encoding="utf-8")
            response_source = root / "response.jsonl"
            response_source.write_text(json.dumps({
                "timestamp": "2026-11-02T01:00:00Z", "type": "response_item",
                "payload": {"type": "message", "role": "user", "content": [
                    {"type": "input_text", "text": "latest user message"}]}
            }) + "\n", encoding="utf-8")
            payload = json.dumps({"cwd": str(root), "transcript_path": str(response_source), "session_id": "latest"})
            result = subprocess.run(
                [sys.executable, str(hook_directory / "audit_transcript.py")],
                check=True, input=payload, capture_output=True, text=True,
            )
            response = json.loads(result.stdout)
            self.assertTrue(response["continue"])
            self.assertIn("broken", response["systemMessage"])
            self.assertIn("latest user message", (root / "docs/audit/audit-test.jsonl").read_text())


if __name__ == "__main__":
    unittest.main()
