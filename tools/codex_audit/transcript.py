"""Codexの生会話記録から、ブランチ別の監査ログJSONLを作成する。

生会話記録には可視の会話以外のイベントも含まれる。このモジュールは必要な
メッセージだけを抽出し、セッションごとの記録を時系列でまとめて保存する。
"""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import tempfile
from collections import Counter
from datetime import datetime, timezone
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
    """会話記録の形式や追記の整合性を検証できない場合の例外。"""


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

    events = []
    responses = []
    with transcript.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            try:
                event = json.loads(line)
                if not isinstance(event, dict):
                    raise ValueError("event is not an object")
                payload = event.get("payload", {})
                if not isinstance(payload, dict):
                    raise ValueError("payload is not an object")
                if event.get("type") == "session_meta":
                    origin = payload.get("source", {})
                    if isinstance(origin, dict) and "subagent" in origin:
                        return
                kind = event.get("type")
                if kind == "event_msg" and payload.get("type") in SUPPORTED_EVENT_TYPES:
                    speaker = SUPPORTED_EVENT_TYPES[payload["type"]]
                    message = payload.get("message")
                    target = events
                elif (kind == "response_item" and payload.get("type") == "message"
                      and payload.get("role") in ("user", "assistant")):
                    if payload.get("role") == "assistant" and (
                        payload.get("channel") not in (None, "final", "commentary")
                        or payload.get("recipient", "all") != "all"
                    ):
                        continue
                    speaker = "human" if payload["role"] == "user" else "codex"
                    content = payload.get("content")
                    if not isinstance(content, list):
                        raise ValueError("message content is not an array")
                    parts = [part.get("text") for part in content
                             if isinstance(part, dict) and part.get("type") in ("input_text", "output_text")]
                    if not parts:
                        continue
                    if not all(isinstance(part, str) for part in parts):
                        raise ValueError("message text is invalid")
                    message = "\n".join(parts)
                    if speaker == "human" and message.lstrip().startswith((
                        "# AGENTS.md instructions", "<environment_context>",
                        "<permissions instructions>", "<external_codex_apps_open_page>")):
                        continue
                    target = responses
                else:
                    continue
                timestamp = event.get("timestamp")
                phase = payload.get("phase")
                if not isinstance(timestamp, str) or not timestamp:
                    raise ValueError("conversation timestamp is missing")
                if not isinstance(message, str):
                    raise ValueError("conversation message is missing")
                if phase is not None and not isinstance(phase, str):
                    raise ValueError("conversation phase is invalid")
                if speaker == "codex" and phase not in (None, "commentary", "final", "final_answer"):
                    continue
                target.append(AuditMessage(timestamp, session_id, speaker, message, phase))
            except (ValueError, TypeError) as error:
                raise TranscriptFormatError(f"{transcript.name}: line {line_number}: {error}") from error

    # 同じ発言が二形式で保存された場合だけ、対応する件数を差し引く。
    remaining = Counter((item.speaker, item.message) for item in events)
    messages = list(events)
    for item in responses:
        key = (item.speaker, item.message)
        if remaining[key]:
            remaining[key] -= 1
        else:
            messages.append(item)
    if not messages:
        raise TranscriptFormatError(f"{transcript.name}: no supported conversation events were found")
    yield from sorted(messages, key=lambda item: item.timestamp)


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
    """今回の会話を保存し、既存の監査ログへ未記録分を追加する。

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

    branch_name = safe_name(branch)
    session_name = safe_name(session_id)
    staging_directory = repository_root / ".codex" / "audit-staging"
    staging_directory.mkdir(parents=True, exist_ok=True)
    destination = repository_root / "docs" / "audit" / f"{branch_name}.jsonl"

    # 読み取りから置き換えまでを排他し、並行Hookによる追記の消失を防ぐ。
    with (staging_directory / f"{branch_name}.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _update_locked(destination, staging_directory, branch_name, session_name, transcript)


def _update_locked(destination: Path, staging: Path, branch: str, session: str, transcript: Path) -> Path:
    """既存の公開ログを保持し、未記録の会話だけを追加する。

    Args:
        destination: 公開ログの出力先。
        staging: 原本と更新状態の保存先。
        branch: ファイル名用のブランチ名。
        session: 今回のセッション名。
        transcript: 今回の原本。

    Returns:
        更新した公開ログのパス。

    Raises:
        TranscriptFormatError: 一部の原本を反映できなかった場合。
    """

    messages = []
    if destination.exists():
        messages = [AuditMessage(**json.loads(line)) for line in destination.read_text(encoding="utf-8").splitlines()]
    counts = Counter(item.session_id for item in messages)
    current = staging / f"{branch}--{session}.jsonl"
    errors = []
    candidates = [path for path in sorted(staging.glob(f"{branch}--*.jsonl"))
                  if path != current and not counts[path.stem.removeprefix(f"{branch}--")]]
    candidates.append(transcript)
    for path in candidates:
        name = session if path == transcript else path.stem.removeprefix(f"{branch}--")
        try:
            extracted = list(extract_messages(path, name))
            if path == transcript and current.exists():
                previous = list(extract_messages(current, name))
                if extracted[:len(previous)] != previous:
                    raise TranscriptFormatError("source prefix changed; manual reconciliation required")
            if len(extracted) < counts[name]:
                raise TranscriptFormatError("source contains fewer messages than the public log")
            messages.extend(extracted[counts[name]:])
            if path == transcript and path.resolve() != current.resolve():
                # 原本を公開せず、次回の追記前に変更を検知するため保持する。
                temporary = current.with_suffix(".tmp")
                shutil.copyfile(path, temporary)
                os.replace(temporary, current)
        except (OSError, ValueError) as error:
            errors.append({"session": name, "source": str(path), "reason": str(error)})

    messages.sort(key=lambda item: (item.timestamp, item.session_id))
    write_jsonl(destination, messages)
    status = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "message_count": len(messages),
        "session_counts": dict(Counter(item.session_id for item in messages)),
        "latest_message_at": max((item.timestamp for item in messages), default=None),
        "errors": errors,
    }
    status_path = staging / f"{branch}.status.json"
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        raise TranscriptFormatError(f"audit update incomplete; see {status_path}: " + "; ".join(
            f"{item['session']}: {item['reason']}" for item in errors))
    return destination
