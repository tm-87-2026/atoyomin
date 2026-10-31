"""Codexの生会話記録から、ブランチ別の監査ログJSONLを作成する。

生会話記録には可視の会話以外のイベントも含まれる。このモジュールは必要な
メッセージだけを抽出し、セッションごとの記録を時系列でまとめて保存する。
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator


# Codexの内部イベントは監査ログに含めず、会話として表示されるユーザーと
# Codexのメッセージだけを扱う。
SUPPORTED_EVENT_TYPES = {
    "user_message": "human",
    "agent_message": "codex",
}


class TranscriptFormatError(ValueError):
    """Raised when the Codex transcript does not match the validated format."""


@dataclass(frozen=True)
class AuditMessage:
    """監査ログに書き出す、1件の可視会話メッセージ。"""
    timestamp: str
    session_id: str
    speaker: str
    message: str
    phase: str | None = None


def safe_name(value: str) -> str:
    """文字列を出力ファイル名として安全な形にする。

    Args:
        value: ブランチ名またはセッションID。

    Returns:
        英数字、ハイフン、アンダースコア、ピリオドだけで構成される文字列。
    """

    return "".join(
        character if character.isalnum() or character in "-_." else "-"
        for character in value
    )


def extract_messages(transcript: Path, session_id: str) -> Iterator[AuditMessage]:
    """生会話記録から可視メッセージだけを監査ログ形式へ変換する。

    Args:
        transcript: Codexが出力したJSONL形式の会話記録。
        session_id: 変換したメッセージに付与する会話の識別子。

    Yields:
        監査ログに書き出す可視会話メッセージ。

    Raises:
        TranscriptFormatError: 会話記録がJSONL形式でない、必要な項目がない、
            または可視会話が含まれない場合。
    """

    matched = 0
    with transcript.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            # JSONLの各行をイベントとして読み込む。
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise TranscriptFormatError(
                    f"invalid JSON on transcript line {line_number}"
                ) from error

            # transcriptにはメタデータなど会話以外の行も混在する。
            if event.get("type") != "event_msg":
                continue
            payload = event.get("payload")
            if not isinstance(payload, dict):
                raise TranscriptFormatError(
                    f"event_msg payload is not an object on line {line_number}"
                )

            # 可視会話を表すイベントかを判定する。
            event_type = payload.get("type")
            if event_type not in SUPPORTED_EVENT_TYPES:
                continue

            # 監査ログに必要な項目を検証して、出力用の形式に整える。
            timestamp = event.get("timestamp")
            message = payload.get("message")
            phase = payload.get("phase")
            if not isinstance(timestamp, str) or not timestamp:
                raise TranscriptFormatError(
                    f"conversation timestamp is missing on line {line_number}"
                )
            if not isinstance(message, str):
                raise TranscriptFormatError(
                    f"conversation message is missing on line {line_number}"
                )
            if phase is not None and not isinstance(phase, str):
                raise TranscriptFormatError(
                    f"conversation phase is invalid on line {line_number}"
                )

            matched += 1
            yield AuditMessage(
                timestamp=timestamp,
                session_id=session_id,
                speaker=SUPPORTED_EVENT_TYPES[event_type],
                message=message,
                phase=phase,
            )

    if matched == 0:
        raise TranscriptFormatError("no supported conversation events were found")


def write_jsonl(destination: Path, messages: list[AuditMessage]) -> None:
    """メッセージ一覧をJSONLとして、途中状態を見せずに保存する。

    Args:
        destination: 生成する監査ログのパス。
        messages: 出力する会話メッセージの一覧。
    """

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            for message in messages:
                temporary.write(json.dumps(asdict(message), ensure_ascii=False) + "\n")

        # 完成したファイルだけを置き換えるため、読み手が途中までの
        # 監査ログを参照することがない。
        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def update_branch_audit(
    *,
    repository_root: Path,
    branch: str,
    session_id: str,
    transcript: Path,
) -> Path:
    """今回の会話を保存し、同じブランチの監査ログ全体を再生成する。

    Args:
        repository_root: 監査ログを保存するリポジトリのルートディレクトリ。
        branch: 監査ログを更新するブランチ名。
        session_id: 今回の会話の識別子。
        transcript: Codexが出力したJSONL形式の会話記録。

    Returns:
        更新したブランチ別監査ログのパス。

    Raises:
        TranscriptFormatError: 保存済みの会話記録を監査ログへ変換できない場合。
    """

    # ブランチ名とセッションIDを出力先で使える名前に整える。
    branch_name = safe_name(branch)
    session_name = safe_name(session_id)
    staging_directory = repository_root / ".codex" / "audit-staging"
    staging_directory.mkdir(parents=True, exist_ok=True)
    staged_transcript = staging_directory / f"{branch_name}--{session_name}.jsonl"

    # セッションごとの元データを残し、同じブランチの過去セッション分も
    # まとめて監査ログを再生成できるようにする。
    shutil.copyfile(transcript, staged_transcript)

    # 同じブランチで保存済みの全セッションを読み直す。
    messages: list[AuditMessage] = []
    for staged_file in sorted(staging_directory.glob(f"{branch_name}--*.jsonl")):
        staged_session = staged_file.stem.removeprefix(f"{branch_name}--")
        messages.extend(extract_messages(staged_file, staged_session))

    # セッションの終了順に左右されない、再現可能な出力順にする。
    messages.sort(key=lambda message: (message.timestamp, message.session_id))

    # 時系列順にまとめ、ブランチごとの監査ログとして出力する。
    destination = repository_root / "docs" / "audit" / f"{branch_name}.jsonl"
    write_jsonl(destination, messages)
    return destination
