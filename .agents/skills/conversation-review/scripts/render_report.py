#!/usr/bin/env python3
"""構造化した会話振り返りを自己完結HTMLへ安全に描画する。"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse


TARGET_COMMENT = re.compile(r"<!--\s*conversation-review-targets\s+(\{.*?\})\s*-->", re.DOTALL)
TARGET_BLOCK = re.compile(r"```json conversation-review-targets\s*\n(\{.*?\})\s*\n```", re.DOTALL)
SHA256 = re.compile(r"[0-9a-f]{64}")
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
SAFE_ID = re.compile(r"[A-Za-z0-9_.:-]+")
ACTION_KINDS = {"instruction", "prior_judgment", "intervention", "habit"}


class ReportError(ValueError):
    """入力または既存レポートが契約に違反している。"""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReportError(f"{field} must be a non-empty string")
    if "\x00" in value:
        raise ReportError(f"{field} contains a NUL byte")
    return value


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReportError(f"{field} must be a non-negative integer")
    return value


def _url(value: Any, field: str) -> str:
    value = _text(value, field)
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise ReportError(f"{field} must be an http(s) URL without credentials")
    return value


def validate_targets(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"version", "targets"} or value["version"] != 1:
        raise ReportError("targets must contain only version=1 and targets")
    if not isinstance(value["targets"], list) or not value["targets"]:
        raise ReportError("targets.targets must be a non-empty list")
    seen: set[tuple[str, str]] = set()
    allowed = {"repository", "path", "sha256", "method", "pr", "branch", "reason"}
    for index, target in enumerate(value["targets"]):
        field = f"targets.targets[{index}]"
        if not isinstance(target, dict) or not set(target) <= allowed:
            raise ReportError(f"{field} contains unknown fields")
        repository = _text(target.get("repository"), f"{field}.repository")
        path = _text(target.get("path"), f"{field}.path")
        digest = _text(target.get("sha256"), f"{field}.sha256")
        method = target.get("method")
        if not REPOSITORY.fullmatch(repository):
            raise ReportError(f"{field}.repository must be owner/repo")
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts or not path.startswith("docs/audit/") or pure.suffix != ".jsonl":
            raise ReportError(f"{field}.path must be a tracked docs/audit/*.jsonl path")
        if not SHA256.fullmatch(digest):
            raise ReportError(f"{field}.sha256 must be lowercase SHA-256")
        if method not in {"matched", "manual"}:
            raise ReportError(f"{field}.method must be matched or manual")
        if method == "manual":
            _text(target.get("reason"), f"{field}.reason")
        if "pr" in target and (_integer(target["pr"], f"{field}.pr") == 0):
            raise ReportError(f"{field}.pr must be positive")
        if "branch" in target:
            _text(target["branch"], f"{field}.branch")
        if "reason" in target:
            _text(target["reason"], f"{field}.reason")
        if (repository, path) in seen:
            raise ReportError(f"duplicate target: {repository} {path}")
        seen.add((repository, path))
        for item in target.values():
            if isinstance(item, str) and ("--" in item or "-->" in item):
                raise ReportError(f"{field} contains a value unsafe for an HTML comment")
    return value


def read_targets(path: Path) -> dict[str, Any]:
    """HTMLコメントまたは既存Markdownブロックから完成対象を読む。"""

    source = path.read_text(encoding="utf-8")
    html_matches = TARGET_COMMENT.findall(source)
    markdown_matches = TARGET_BLOCK.findall(source)
    matches = html_matches + markdown_matches
    if len(matches) != 1:
        raise ReportError(f"{path}: expected exactly one targets record, found {len(matches)}")
    try:
        value = json.loads(matches[0])
    except json.JSONDecodeError as error:
        raise ReportError(f"{path}: invalid targets JSON: {error}") from error
    return validate_targets(value)


def analyzed_keys(paths: list[Path]) -> set[tuple[str, str]]:
    return {
        (target["repository"], target["path"])
        for path in paths
        for target in read_targets(path)["targets"]
    }


def validate_report(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ReportError("report input must be an object")
    required = {"title", "generated_at", "period", "summary", "targets", "metrics", "evidence", "findings", "actions", "limitations"}
    if not required <= set(data):
        raise ReportError(f"missing report fields: {sorted(required - set(data))}")
    for field in ("title", "generated_at", "period", "summary"):
        _text(data[field], field)
    validate_targets(data["targets"])
    if not isinstance(data["metrics"], list) or not data["metrics"]:
        raise ReportError("metrics must be a non-empty list")
    metric_ids: set[str] = set()
    for index, metric in enumerate(data["metrics"]):
        field = f"metrics[{index}]"
        if not isinstance(metric, dict):
            raise ReportError(f"{field} must be an object")
        identifier = _text(metric.get("id"), f"{field}.id")
        _text(metric.get("label"), f"{field}.label")
        if not SAFE_ID.fullmatch(identifier) or identifier in metric_ids:
            raise ReportError(f"{field}.id must be unique and safe")
        metric_ids.add(identifier)
        for name in ("sessions", "human_turns", "codex_turns", "rallies", "confirmation_adopted", "long_sessions", "longest_messages", "longest_characters", "correction_adopted", "repetition_adopted"):
            _integer(metric.get(name), f"{field}.{name}")
        if metric["confirmation_adopted"] > metric["codex_turns"] or metric["long_sessions"] > metric["sessions"]:
            raise ReportError(f"{field} has a numerator larger than its denominator")
        if metric["correction_adopted"] > metric["human_turns"] or metric["repetition_adopted"] > metric["human_turns"]:
            raise ReportError(f"{field} has a human-turn numerator larger than its denominator")
        if metric["rallies"] > metric["human_turns"] or metric["rallies"] > metric["codex_turns"]:
            raise ReportError(f"{field}.rallies cannot exceed either turn count")
        if metric["sessions"] == 0 and (metric["longest_messages"] != 0 or metric["longest_characters"] != 0):
            raise ReportError(f"{field} cannot have a longest session when sessions is zero")
        if metric["sessions"] > 0 and metric["longest_messages"] == 0:
            raise ReportError(f"{field}.longest_messages must be positive when sessions exist")
    if not isinstance(data["evidence"], list):
        raise ReportError("evidence must be a list")
    evidence_ids: set[str] = set()
    for index, evidence in enumerate(data["evidence"]):
        field = f"evidence[{index}]"
        identifier = _text(evidence.get("id") if isinstance(evidence, dict) else None, f"{field}.id")
        if not SAFE_ID.fullmatch(identifier) or identifier in evidence_ids:
            raise ReportError(f"{field}.id must be unique and safe")
        evidence_ids.add(identifier)
        if evidence.get("speaker") != "human":
            raise ReportError(f"{field}.speaker must be human")
        for name in ("log", "session_id", "quote"):
            _text(evidence.get(name), f"{field}.{name}")
        if _integer(evidence.get("line"), f"{field}.line") == 0:
            raise ReportError(f"{field}.line must be positive")
    if not isinstance(data["findings"], list):
        raise ReportError("findings must be a list")
    finding_ids: set[str] = set()
    for index, finding in enumerate(data["findings"]):
        field = f"findings[{index}]"
        identifier = _text(finding.get("id") if isinstance(finding, dict) else None, f"{field}.id")
        if not SAFE_ID.fullmatch(identifier) or identifier in finding_ids:
            raise ReportError(f"{field}.id must be unique and safe")
        finding_ids.add(identifier)
        if finding.get("kind") not in {"continue", "improve"}:
            raise ReportError(f"{field}.kind is invalid")
        for gate in ("reusable", "actionable", "evidence_complete"):
            if finding.get(gate) is not True:
                raise ReportError(f"{field}.{gate} must be true")
        if finding["kind"] == "improve" and finding.get("practice_applicable") is not True:
            raise ReportError(f"{field}.practice_applicable must be true")
        for name in ("title", "observation", "interpretation", "proposal", "scope"):
            _text(finding.get(name), f"{field}.{name}")
        claims = finding.get("claims")
        if not isinstance(claims, list) or not claims:
            raise ReportError(f"{field}.claims must be a non-empty list")
        claim_ids: set[str] = set()
        for claim_index, claim in enumerate(claims):
            claim_field = f"{field}.claims[{claim_index}]"
            claim_id = _text(claim.get("id") if isinstance(claim, dict) else None, f"{claim_field}.id")
            _text(claim.get("text"), f"{claim_field}.text")
            references = claim.get("evidence_ids")
            if not SAFE_ID.fullmatch(claim_id) or claim_id in claim_ids or not isinstance(references, list) or not references:
                raise ReportError(f"{claim_field} requires a unique id and evidence_ids")
            claim_ids.add(claim_id)
            unknown = set(references) - evidence_ids
            if unknown:
                raise ReportError(f"{claim_field} references unknown evidence: {sorted(unknown)}")
        if finding["kind"] == "improve":
            practice = finding.get("practice")
            if not isinstance(practice, dict):
                raise ReportError(f"{field}.practice is required")
            for name in ("id", "official_statement", "log_inference", "applicability", "unknown_conditions"):
                _text(practice.get(name), f"{field}.practice.{name}")
            _url(practice.get("url"), f"{field}.practice.url")
    if not isinstance(data["actions"], list):
        raise ReportError("actions must be a list")
    for index, action in enumerate(data["actions"]):
        field = f"actions[{index}]"
        if not isinstance(action, dict) or action.get("kind") not in ACTION_KINDS:
            raise ReportError(f"{field}.kind is invalid")
        _text(action.get("text"), f"{field}.text")
        finding_id = _text(action.get("finding_id"), f"{field}.finding_id")
        if finding_id not in finding_ids:
            raise ReportError(f"{field} references a non-final finding")
    if not isinstance(data["limitations"], list):
        raise ReportError("limitations must be a list")
    for index, limitation in enumerate(data["limitations"]):
        _text(limitation, f"limitations[{index}]")
    return data


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True).replace("\n", "&#10;")


def _ratio(numerator: int, denominator: int) -> str:
    return "取得不能" if denominator == 0 else f"{numerator / denominator * 100:.1f}%"


def _bars(title: str, description: str, metrics: list[dict[str, Any]], field: str, unit: str, chart_id: str) -> str:
    maximum = max((metric[field] for metric in metrics), default=0) or 1
    rows = []
    for index, metric in enumerate(metrics):
        y = 58 + index * 38
        width = metric[field] / maximum * 300
        rows.append(f'<text x="0" y="{y + 14}">{_e(metric["label"])}</text><rect x="150" y="{y}" width="{width:.2f}" height="20" rx="3"/><text x="{155 + width:.2f}" y="{y + 15}">{metric[field]} {_e(unit)}</text>')
    height = 80 + len(metrics) * 38
    ticks = "".join(f'<g><line x1="{150 + i * 75}" y1="46" x2="{150 + i * 75}" y2="{height - 18}"/><text x="{150 + i * 75}" y="38">{maximum * i / 4:.1f}</text></g>' for i in range(5))
    table_rows = "".join(f'<tr><th scope="row">{_e(m["label"])}</th><td>{m[field]}</td></tr>' for m in metrics)
    return f'''<figure><h3 id="{chart_id}-title">{_e(title)}</h3><svg viewBox="0 0 560 {height}" role="img" aria-labelledby="{chart_id}-title {chart_id}-desc"><desc id="{chart_id}-desc">{_e(description)}</desc><g class="grid">{ticks}<line class="axis" x1="150" y1="46" x2="150" y2="{height - 18}"/><line class="axis" x1="150" y1="{height - 18}" x2="450" y2="{height - 18}"/></g><g class="legend" aria-label="凡例"><rect x="150" y="2" width="14" height="14"/><text x="170" y="14">{_e(title)}</text></g><g class="bars">{''.join(rows)}</g><text x="450" y="14" text-anchor="end">単位: {_e(unit)}</text></svg><figcaption>{_e(description)}</figcaption><table class="sr-only"><caption>{_e(title)}の正確値</caption><thead><tr><th>対象</th><th>{_e(unit)}</th></tr></thead><tbody>{table_rows}</tbody></table></figure>'''


def _rates(metrics: list[dict[str, Any]]) -> str:
    available = [metric for metric in metrics if metric["codex_turns"] > 0]
    maximum = max((metric["confirmation_adopted"] / metric["codex_turns"] * 100 for metric in available), default=0) or 100
    height = 80 + len(metrics) * 38
    ticks = "".join(f'<g><line x1="{150 + i * 75}" y1="46" x2="{150 + i * 75}" y2="{height - 18}"/><text x="{150 + i * 75}" y="38">{maximum * i / 4:.1f}</text></g>' for i in range(5))
    rows = []
    for index, metric in enumerate(metrics):
        y = 58 + index * 38
        label = _e(metric["label"])
        if metric["codex_turns"] == 0:
            rows.append(f'<text x="0" y="{y + 14}">{label}</text><text class="unavailable" x="150" y="{y + 14}">取得不能（Codexターン 0）</text>')
            continue
        rate = metric["confirmation_adopted"] / metric["codex_turns"] * 100
        width = rate / maximum * 300
        rows.append(f'<text x="0" y="{y + 14}">{label}</text><rect x="150" y="{y}" width="{width:.2f}" height="20" rx="3"/><text x="{155 + width:.2f}" y="{y + 15}">{rate:.1f}%</text>')
    exact = "".join(f'<li>{_e(m["label"])}: {m["confirmation_adopted"]}/{m["codex_turns"]}（{_ratio(m["confirmation_adopted"], m["codex_turns"]) }）</li>' for m in metrics)
    table_rows = "".join(f'<tr><th scope="row">{_e(m["label"])}</th><td>{m["confirmation_adopted"]}</td><td>{m["codex_turns"]}</td><td>{_ratio(m["confirmation_adopted"], m["codex_turns"])}</td></tr>' for m in metrics)
    return f'''<figure><h3 id="confirmation-title">確認質問の採用率</h3><svg viewBox="0 0 560 {height}" role="img" aria-labelledby="confirmation-title confirmation-desc"><desc id="confirmation-desc">Codexターンを分母にした採用数の割合です。分母が0の対象は取得不能として棒を描画しません。</desc><g class="grid">{ticks}<line class="axis" x1="150" y1="46" x2="150" y2="{height - 18}"/><line class="axis" x1="150" y1="{height - 18}" x2="450" y2="{height - 18}"/></g><g class="legend" aria-label="凡例"><rect x="150" y="2" width="14" height="14"/><text x="170" y="14">確認質問の採用率</text></g><g class="bars">{''.join(rows)}</g><text x="450" y="14" text-anchor="end">単位: %</text></svg><figcaption>Codexターンを分母にした採用数の割合です。分母0は取得不能として区別します。</figcaption><ul class="exact">{exact}</ul><table class="sr-only"><caption>確認質問の採用率の正確値</caption><thead><tr><th>対象</th><th>採用数</th><th>Codexターン</th><th>採用率</th></tr></thead><tbody>{table_rows}</tbody></table></figure>'''


def render_report(data: dict[str, Any]) -> str:
    data = validate_report(data)
    metrics = data["metrics"]
    targets_json = json.dumps(data["targets"], ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    cards = (
        ("対象", len(metrics), "ログ"),
        ("セッション", sum(m["sessions"] for m in metrics), "件"),
        ("ラリー", sum(m["rallies"] for m in metrics), "回"),
        ("確定所見", len(data["findings"]), "件"),
    )
    card_html = "".join(f'<article class="metric"><span>{_e(label)}</span><strong>{value}</strong><small>{_e(unit)}</small></article>' for label, value, unit in cards)
    zero = all(m["correction_adopted"] == 0 and m["repetition_adopted"] == 0 for m in metrics)
    zero_html = '<section class="zero" aria-label="訂正・介入と反復のゼロ状態"><h3>訂正・介入と反復</h3><p>文脈上採用した訂正・介入と反復は、全対象で0件でした。</p></section>' if zero else _bars("訂正・介入", "文脈上採用した人間の介入件数です。", metrics, "correction_adopted", "件", "correction")
    evidence = {item["id"]: item for item in data["evidence"]}
    finding_html: dict[str, list[str]] = {"continue": [], "improve": []}
    for finding in data["findings"]:
        used = {item for claim in finding["claims"] for item in claim["evidence_ids"]}
        evidence_html = "".join(f'<li><code>{_e(evidence[item]["log"])}</code> / session_id={_e(evidence[item]["session_id"])} / line {evidence[item]["line"]} — 人間: <q>{_e(evidence[item]["quote"])}</q></li>' for item in sorted(used))
        claims_html = "".join(f'<li>{_e(claim["text"])} <small>根拠: {", ".join(_e(item) for item in claim["evidence_ids"])}</small></li>' for claim in finding["claims"])
        practice = ""
        if finding["kind"] == "improve":
            p = finding["practice"]
            practice = f'<h4>外部根拠</h4><dl><dt>観点</dt><dd>{_e(p["id"])}</dd><dt>公式資料</dt><dd><a href="{_e(p["url"])}">{_e(p["official_statement"])}</a></dd><dt>ログ評価への推論</dt><dd>{_e(p["log_inference"])}</dd><dt>適用条件</dt><dd>{_e(p["applicability"])}</dd><dt>不明条件</dt><dd>{_e(p["unknown_conditions"])}</dd></dl>'
        finding_html[finding["kind"]].append(f'''<article class="finding" id="{_e(finding['id'])}"><h3>{_e(finding['title'])}</h3><h4>観察事実</h4><p>{_e(finding['observation'])}</p><h4>解釈</h4><p>{_e(finding['interpretation'])}</p><h4>提案</h4><p>{_e(finding['proposal'])}</p><details><summary>根拠と監査情報</summary><p>範囲: {_e(finding['scope'])}</p><h4>主張と根拠の対応</h4><ul>{claims_html}</ul><h4>原文位置と最小引用</h4><ul>{evidence_html}</ul>{practice}</details></article>''')
    def findings_section(kind: str, title: str) -> str:
        content = "".join(finding_html[kind]) or '<p class="empty">確定所見は0件です。</p>'
        return f'<section><h2>{title}</h2>{content}</section>'
    action_labels = {"instruction": "指示", "prior_judgment": "事前判断", "intervention": "逸脱時介入", "habit": "継続習慣"}
    actions = "".join(f'<li><strong>{action_labels[a["kind"]]}</strong>: {_e(a["text"])} <a href="#{_e(a["finding_id"])}">{_e(a["finding_id"])}</a></li>' for a in data["actions"]) or '<li>確定所見に基づく次回行動はありません。</li>'
    detail_rows = "".join(f'<tr><th scope="row">{_e(m["label"])}</th><td>{m["sessions"]}</td><td>{m["human_turns"]}</td><td>{m["codex_turns"]}</td><td>{m["rallies"]} / {m["sessions"]} = {m["rallies"] / m["sessions"] if m["sessions"] else 0:.2f}</td><td>{m["confirmation_adopted"]}/{m["codex_turns"]} ({_ratio(m["confirmation_adopted"], m["codex_turns"])})</td><td>{m["long_sessions"]}/{m["sessions"]}</td><td>{m["longest_messages"]}発言・{m["longest_characters"]}文字</td></tr>' for m in metrics)
    limitations = "".join(f'<li>{_e(item)}</li>' for item in data["limitations"]) or "<li>なし</li>"
    css = """*{box-sizing:border-box}body{margin:0;background:#f5f7fb;color:#172033;font-family:system-ui,sans-serif;line-height:1.65}main{max-width:1120px;margin:auto;padding:2rem}header{background:#172554;color:white;padding:2rem;border-radius:1rem}.cards,.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem;margin:1.5rem 0}.metric,.finding,figure,.zero,details{background:white;border:1px solid #dbe3ef;border-radius:.75rem;padding:1rem}.metric strong{font-size:2rem;margin:.2rem}.metric span,.metric small{display:block;color:#526079}.finding{margin:1rem 0}.finding h4{margin-bottom:.2rem}svg{width:100%;min-height:220px}.bars rect,.legend rect{fill:#2563eb}.bars text,.grid text,.legend text{fill:#172033;font-size:12px}.grid line{stroke:#dbe3ef}.grid .axis{stroke:#526079;stroke-width:1.5}.exact{font-size:.9rem}details{margin-top:1rem}summary{cursor:pointer;font-weight:700}table{border-collapse:collapse;width:100%}th,td{border:1px solid #cbd5e1;padding:.5rem;text-align:left}.table-wrap{overflow:auto}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}.zero{border-left:5px solid #16a34a}a{color:#1d4ed8}@media(max-width:600px){main{padding:.75rem}header{padding:1.25rem}svg{min-width:520px}.charts figure{overflow:auto}}@media print{body{background:white}main{max-width:none;padding:0}header{color:#000;background:white;border:1px solid #999}details{break-inside:avoid}details:not([open])>*:not(summary){display:block}.cards,.charts{display:block}.metric,figure,.finding{break-inside:avoid;margin:.5rem 0}a{color:#000;text-decoration:none}}"""
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{_e(data['title'])}</title><style>{css}</style></head><body>
<!-- conversation-review-targets {targets_json} -->
<main><header><h1>{_e(data['title'])}</h1><p>{_e(data['summary'])}</p><p>実行日時: <time>{_e(data['generated_at'])}</time> / 対象期間: {_e(data['period'])}</p></header>
<section aria-labelledby="overview"><h2 id="overview">概要</h2><div class="cards">{card_html}</div></section>
<section aria-labelledby="visualizations"><h2 id="visualizations">利用傾向の可視化</h2><div class="charts">{_bars('規模（セッション）','対象ごとのセッション数です。',metrics,'sessions','セッション','scale')}{_bars('ラリー','対象ごとの完了した往復数です。',metrics,'rallies','回','rallies')}{_rates(metrics)}{_bars('長大化（該当セッション）','全セッションのうち長大化に該当した件数です。',metrics,'long_sessions','セッション','long')}</div>{zero_html}</section>
{findings_section('continue','継続すべき点')}{findings_section('improve','改善すべき点')}
<section><h2>次回に試す行動</h2><ul>{actions}</ul></section>
<details><summary>対象別の詳細値</summary><div class="table-wrap"><table><caption>グラフと同じ入力から生成した正確値</caption><thead><tr><th>対象</th><th>セッション</th><th>人間ターン</th><th>Codexターン</th><th>ラリー/セッション</th><th>確認質問採用率</th><th>長大化</th><th>最長</th></tr></thead><tbody>{detail_rows}</tbody></table></div></details>
<details><summary>不明・未分析・失敗・限界</summary><ul>{limitations}</ul></details>
</main></body></html>'''


def save_report(data: dict[str, Any], destination: Path) -> None:
    """同一ディレクトリで生成・fsyncし、既存ファイルを上書きせず公開する。"""

    if destination.suffix.lower() != ".html":
        raise ReportError("report destination must use the .html extension")
    document = render_report(data)
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(document)
            stream.flush()
            os.fsync(stream.fileno())
        if destination.exists():
            raise FileExistsError(destination)
        os.link(temporary, destination)
        temporary.unlink()
        directory_descriptor = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    render = subparsers.add_parser("render")
    render.add_argument("input", type=Path)
    render.add_argument("output", type=Path)
    targets = subparsers.add_parser("targets")
    targets.add_argument("reports", nargs="+", type=Path)
    arguments = parser.parse_args()
    try:
        if arguments.command == "render":
            data = json.loads(arguments.input.read_text(encoding="utf-8"))
            save_report(data, arguments.output)
        else:
            keys = sorted(analyzed_keys(arguments.reports))
            print(json.dumps({"analyzed_keys": keys}, ensure_ascii=False, separators=(",", ":")))
    except (OSError, json.JSONDecodeError, ReportError) as error:
        parser.exit(2, f"error: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
