#!/usr/bin/env python3
"""監査ログから、文脈判断前の機械的シグナルを決定的に抽出する。

JSONLを行単位で検証し、ログパスとセッションIDの組ごとに集計する。
表層語や疑問符による候補は、後段の文脈判断で採否を決める前の候補として
出力し、このスクリプトでは会話や人間の行動の良否を判定しない。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


MESSAGE_LIMIT = 100
CHARACTER_LIMIT = 40_000
CORRECTION_TERMS = (
    "no,",
    "no ",
    "don't",
    "do not",
    "stop",
    "cancel",
    "revert",
    "undo",
    "instead",
    "wrong",
    "incorrect",
    "not what",
    "やめ",
    "止め",
    "中止",
    "取り消",
    "戻して",
    "戻す",
    "違い",
    "誤り",
    "ではなく",
    "しないで",
    "変更して",
    "修正して",
)


class SignalInputError(ValueError):
    """監査ログを安全に集計できない入力であることを表す。"""


@dataclass(frozen=True)
class Message:
    """入力位置を保持した監査ログの1発言。"""

    log_path: str
    line_number: int
    session_id: str
    speaker: str
    message: str


@dataclass(frozen=True)
class Turn:
    """同一セッションで連続する同じ話者の発言まとまり。"""

    speaker: str
    messages: tuple[Message, ...]

    @property
    def text(self) -> str:
        """まとまり内の本文を改行で連結する。

        Returns:
            発言順に連結した本文。
        """

        return "\n".join(message.message for message in self.messages)


def parse_arguments(arguments: Sequence[str]) -> argparse.Namespace:
    """コマンドライン引数を読み取る。

    Args:
        arguments: プログラム名を除いた引数。

    Returns:
        検証前のコマンドライン引数。
    """

    parser = argparse.ArgumentParser(
        description="監査ログJSONLから文脈判断前の機械的シグナルをJSON出力します。"
    )
    parser.add_argument("logs", nargs="+", type=Path, help="監査ログJSONLのパス")
    return parser.parse_args(arguments)


def read_log(path: Path) -> list[Message]:
    """監査ログを行単位で検証して読み込む。

    Args:
        path: 読み込むJSONLファイル。

    Returns:
        入力位置を保持した発言一覧。

    Raises:
        SignalInputError: ファイルを読めない、空である、JSONLまたは必須項目が
            不正である場合。
    """

    try:
        source = path.open(encoding="utf-8")
    except OSError as error:
        raise SignalInputError(f"{path}: cannot read input: {error}") from error

    messages = []
    try:
        with source:
            for line_number, line in enumerate(source, 1):
                if not line.strip():
                    raise SignalInputError(f"{path}: line {line_number}: blank line is not valid JSONL")
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise SignalInputError(
                        f"{path}: line {line_number}: invalid JSON: {error.msg}"
                    ) from error
                validate_record(path, line_number, record)
                messages.append(
                    Message(
                        log_path=str(path),
                        line_number=line_number,
                        session_id=record["session_id"],
                        speaker=record["speaker"],
                        message=record["message"],
                    )
                )
    except OSError as error:
        raise SignalInputError(f"{path}: cannot read input: {error}") from error
    if not messages:
        raise SignalInputError(f"{path}: input contains no records")
    return messages


def validate_record(path: Path, line_number: int, record: object) -> None:
    """監査ログの1レコードが集計可能な形式か検証する。

    Args:
        path: エラー表示に使う入力パス。
        line_number: エラー表示に使う行番号。
        record: JSONから復元した値。

    Raises:
        SignalInputError: レコードまたは必須項目が不正な場合。
    """

    location = f"{path}: line {line_number}"
    if not isinstance(record, dict):
        raise SignalInputError(f"{location}: record must be an object")
    for field in ("timestamp", "session_id", "speaker", "message"):
        if field not in record:
            raise SignalInputError(f"{location}: missing required field '{field}'")
    if not isinstance(record["timestamp"], str) or not record["timestamp"]:
        raise SignalInputError(f"{location}: timestamp must be a non-empty string")
    if not isinstance(record["session_id"], str) or not record["session_id"]:
        raise SignalInputError(f"{location}: session_id must be a non-empty string")
    if record["speaker"] not in ("human", "codex"):
        raise SignalInputError(f"{location}: speaker must be 'human' or 'codex'")
    if not isinstance(record["message"], str):
        raise SignalInputError(f"{location}: message must be a string")
    if "phase" in record and record["phase"] is not None and not isinstance(record["phase"], str):
        raise SignalInputError(f"{location}: phase must be a string or null")


def group_turns(messages: list[Message]) -> list[Turn]:
    """連続する同じ話者の発言を一まとまりにする。

    Args:
        messages: 同じログ・セッションの発言一覧。

    Returns:
        入力順の話者まとまり。
    """

    turns: list[Turn] = []
    pending: list[Message] = []
    for message in messages:
        if pending and pending[-1].speaker != message.speaker:
            turns.append(Turn(pending[0].speaker, tuple(pending)))
            pending = []
        pending.append(message)
    if pending:
        turns.append(Turn(pending[0].speaker, tuple(pending)))
    return turns


def location(turn: Turn) -> dict[str, object]:
    """話者まとまりを原文へ戻れる位置情報に変換する。

    Args:
        turn: 位置を示す話者まとまり。

    Returns:
        ログパス、セッションID、行番号を含む位置情報。
    """

    first = turn.messages[0]
    numbers = [message.line_number for message in turn.messages]
    return {
        "log_path": first.log_path,
        "session_id": first.session_id,
        "line_start": min(numbers),
        "line_end": max(numbers),
        "line_numbers": numbers,
    }


def normalize_instruction(value: str) -> str:
    """完全一致候補の比較用に人間の発言を正規化する。

    Unicode NFKC、大小文字の同一視、連続空白の単一空白化、前後空白の
    除去だけを行い、句読点や語順は保持する。

    Args:
        value: 人間発言まとまりの本文。

    Returns:
        比較用の正規化済み文字列。
    """

    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).casefold()).strip()


def surface_matches(value: str) -> list[str]:
    """訂正・介入を詳しく読むための表層語を返す。

    Args:
        value: 人間発言まとまりの本文。

    Returns:
        本文に含まれた表層語。意味上の採否は表さない。
    """

    normalized = unicodedata.normalize("NFKC", value).casefold()
    return [term for term in CORRECTION_TERMS if term in normalized]


def classification_placeholder() -> dict[str, object]:
    """後段の文脈判断が未実施であることを表す値を作る。

    Returns:
        採否をゼロと誤認しないための未判定情報。
    """

    return {
        "status": "not_performed",
        "adopted_count": None,
        "rejected_count": None,
        "undetermined_count": None,
    }


def analyze_session(log_path: str, session_id: str, messages: list[Message]) -> dict[str, object]:
    """1ログ・1セッションの決定的シグナルを集計する。

    Args:
        log_path: 入力ログの表示用パス。
        session_id: セッション識別子。
        messages: 対象セッションの発言一覧。

    Returns:
        値、候補位置、算出対象、算出方法、限界を含む集計結果。
    """

    turns = group_turns(messages)
    human_turns = [turn for turn in turns if turn.speaker == "human"]
    codex_turns = [turn for turn in turns if turn.speaker == "codex"]
    rallies = [
        {"human": location(turns[index]), "codex": location(turns[index + 1])}
        for index in range(len(turns) - 1)
        if turns[index].speaker == "human" and turns[index + 1].speaker == "codex"
    ]

    correction_candidates = []
    for turn in human_turns:
        matches = surface_matches(turn.text)
        if matches:
            correction_candidates.append({"location": location(turn), "surface_matches": matches})

    question_candidates = [
        {
            "location": location(turn),
            "surface_matches": [mark for mark in ("?", "？") if mark in turn.text],
        }
        for turn in codex_turns
        if "?" in turn.text or "？" in turn.text
    ]

    occurrences: dict[str, list[Turn]] = defaultdict(list)
    for turn in human_turns:
        normalized = normalize_instruction(turn.text)
        if normalized:
            occurrences[normalized].append(turn)
    repeated = [
        {
            "normalized_text": normalized,
            "occurrence_count": len(items),
            "occurrences": [{"location": location(item)} for item in items],
        }
        for normalized, items in occurrences.items()
        if len(items) > 1
    ]

    character_count = sum(len(message.message) for message in messages)
    session_key = f"{log_path}::{session_id}"
    return {
        "session_key": session_key,
        "log_path": log_path,
        "session_id": session_id,
        "message_count": len(messages),
        "character_count": character_count,
        "human_turn_count": len(human_turns),
        "codex_turn_count": len(codex_turns),
        "rally_count": len(rallies),
        "rallies": rallies,
        "correction_intervention_candidates": {
            "candidate_count": len(correction_candidates),
            "candidate_rate_status": "available" if human_turns else "unavailable_no_human_turns",
            "candidate_rate_per_human_turn": (
                len(correction_candidates) / len(human_turns) if human_turns else None
            ),
            "candidates": correction_candidates,
            "llm_classification": classification_placeholder(),
        },
        "confirmation_question_candidates": {
            "candidate_count": len(question_candidates),
            "candidate_rate_status": "available" if codex_turns else "unavailable_no_codex_turns",
            "candidate_rate_per_codex_turn": (
                len(question_candidates) / len(codex_turns) if codex_turns else None
            ),
            "candidates": question_candidates,
            "llm_classification": classification_placeholder(),
        },
        "exact_human_instruction_repetitions": {
            "repeated_normalized_value_count": len(repeated),
            "repeated_occurrence_count": sum(item["occurrence_count"] for item in repeated),
            "groups": repeated,
            "llm_classification": classification_placeholder(),
        },
        "long_session_threshold_match": {
            "message_count": len(messages) >= MESSAGE_LIMIT,
            "character_count": character_count >= CHARACTER_LIMIT,
        },
    }


def build_output(paths: Sequence[Path]) -> dict[str, object]:
    """すべての入力を検証し、セッション別・全体集計を作る。

    Args:
        paths: 読み込む監査ログJSONLの一覧。

    Returns:
        JSONへ直列化できるシグナル集計。

    Raises:
        SignalInputError: 入力パスが重複する、または入力ログが不正な場合。
    """

    display_paths = [str(path) for path in paths]
    if len(display_paths) != len(set(display_paths)):
        raise SignalInputError("input log paths must not be duplicated")

    sessions = []
    for path in paths:
        grouped: dict[str, list[Message]] = defaultdict(list)
        for message in read_log(path):
            grouped[message.session_id].append(message)
        for session_id, messages in grouped.items():
            sessions.append(analyze_session(str(path), session_id, messages))

    # 異なる長さの尺度を一つの重みへ潰さず、各尺度の最大セッションを候補にする。
    top_by_metric = {}
    for metric in ("message_count", "character_count", "rally_count"):
        maximum = max(session[metric] for session in sessions)
        top_by_metric[metric] = {
            "maximum": maximum,
            "session_keys": [
                session["session_key"] for session in sessions if session[metric] == maximum
            ],
        }
    top_key_set = {
        key
        for result in top_by_metric.values()
        for key in result["session_keys"]
    }
    top_keys = [session["session_key"] for session in sessions if session["session_key"] in top_key_set]
    threshold_keys = [
        session["session_key"]
        for session in sessions
        if session["long_session_threshold_match"]["message_count"]
        or session["long_session_threshold_match"]["character_count"]
    ]
    return {
        "version": 1,
        "input_logs": display_paths,
        "methods": {
            "analysis_unit": "log_path and session_id",
            "turn_grouping": "consecutive messages by the same speaker within an analysis unit",
            "rally": "a human turn immediately followed by a codex turn",
            "correction_intervention_candidate": "human turn containing a configured surface term",
            "confirmation_question_candidate": "codex turn containing '?' or '？'",
            "exact_repetition_normalization": "Unicode NFKC, casefold, collapse whitespace, strip",
            "semantic_classification": "not performed; candidates require later context review",
        },
        "limits": {
            "correction_intervention": "surface terms can include ordinary requests or added information",
            "confirmation_question": "punctuation can include rhetorical or self-directed questions",
            "exact_repetition": "identical wording can be approval, quotation, or instructions for another target",
            "session_length": "length does not establish inefficiency or quality",
        },
        "sessions": sessions,
        "totals": {
            "session_count": len(sessions),
            "message_count": sum(session["message_count"] for session in sessions),
            "character_count": sum(session["character_count"] for session in sessions),
            "rally_count": sum(session["rally_count"] for session in sessions),
            "correction_intervention_candidate_count": sum(
                session["correction_intervention_candidates"]["candidate_count"]
                for session in sessions
            ),
            "confirmation_question_candidate_count": sum(
                session["confirmation_question_candidates"]["candidate_count"]
                for session in sessions
            ),
        },
        "long_session_candidates": {
            "thresholds": {
                "message_count": MESSAGE_LIMIT,
                "character_count": CHARACTER_LIMIT,
            },
            "threshold_session_keys": threshold_keys,
            "top_by_metric": top_by_metric,
            "top_session_keys": top_keys,
        },
    }


def main(arguments: Sequence[str] | None = None) -> int:
    """CLIを実行して集計JSONまたは入力エラーを出力する。

    Args:
        arguments: プログラム名を除いた引数。省略時は実際の引数を使う。

    Returns:
        成功時0、入力不備時2。
    """

    options = parse_arguments(sys.argv[1:] if arguments is None else arguments)
    try:
        result = build_output(options.logs)
    except SignalInputError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
