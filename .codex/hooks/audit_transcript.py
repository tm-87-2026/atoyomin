#!/usr/bin/env python3
"""CodexのStop Hook入力を受け取り、現在のブランチの監査ログを更新する。

Hookから渡される会話記録とセッション情報を検証し、リポジトリ内の
会話ログ変換処理へ渡す。監査ログの更新に失敗しても、Codexの終了処理は継続する。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def git_output(cwd: Path, *args: str) -> str:
    """指定した作業ディレクトリでGitを実行し、標準出力を返す。

    Args:
        cwd: Gitを実行する作業ディレクトリ。
        *args: Gitコマンドへ渡す引数。

    Returns:
        前後の空白を除いた標準出力。

    Raises:
        subprocess.CalledProcessError: Gitコマンドが失敗した場合。
    """

    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def respond(message: str | None = None) -> None:
    """Codexが解釈できるHookの応答を標準出力へ返す。

    Args:
        message: 監査ログを更新できなかった場合にCodexへ伝える内容。
    """

    # 監査ログの失敗によってCodexの終了処理まで失敗させない。
    response: dict[str, object] = {"continue": True}
    if message:
        response["systemMessage"] = message
    print(json.dumps(response, ensure_ascii=False))


def main() -> int:
    """Hook入力を検証し、監査ログを更新してCodexへ応答する。

    Returns:
        常に正常終了を表す終了コード。
    """

    try:
        # Codexがstdinで渡す、今回の会話に関する情報を読み込む。
        payload = json.load(sys.stdin)
        cwd = Path(payload["cwd"])
        transcript_value = payload.get("transcript_path")
        session_id = payload.get("session_id")

        if not transcript_value:
            raise ValueError("transcript_path was unavailable")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id was unavailable")

        transcript = Path(transcript_value)
        if not transcript.is_file():
            raise ValueError("the transcript file was unavailable")

        # Hookが実行された場所を基準に、出力先となるリポジトリと現在の
        # ブランチを特定する。
        root = Path(git_output(cwd, "rev-parse", "--show-toplevel"))
        branch = git_output(cwd, "branch", "--show-current")
        if not branch:
            raise ValueError("Git is in detached HEAD state")

        # Hookはスクリプト自身のディレクトリから起動されるため、
        # リポジトリ内の変換モジュールを明示的にimport可能にする。
        sys.path.insert(0, str(root))
        from tools.codex_audit.transcript import update_branch_audit

        # 会話記録をブランチ別の監査ログへ変換して保存する。
        update_branch_audit(
            repository_root=root,
            branch=branch,
            session_id=session_id,
            transcript=transcript,
        )
        respond()
    except Exception as error:
        # 失敗内容はCodexに伝えるが、終了処理自体は継続させる。
        respond(f"Audit log was not updated: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
