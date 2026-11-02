# GitHub APIの参照先

## 利用前の確認

- **接続先**: 依頼のURLまたは `git remote get-url origin` からリポジトリを特定する。番号だけで他のリポジトリを検索しない。
- **ツール**: GitHubプラグインを優先する。以下の識別名で利用可能なツールを探し、現在の引数定義を確認する。
- **操作範囲**: この資料は読み取り用。PR本文の更新やレビュー投稿は、Skill本文の「承認・反映」に従う。

## 読み取りに使うツール

| 確認する情報 | ツール | 引数 |
| --- | --- | --- |
| Issueの要求・完了条件 | `mcp__codex_apps__github_fetch_issue` | `repository_full_name`, `issue_number` |
| PRのタイトル・本文・差分・head SHA | `mcp__codex_apps__github_fetch_pr` | `repo_full_name`, `pr_number` |
| PRの議論・レビュー | `mcp__codex_apps__github_fetch_pr_comments` | `repo_full_name`, `pr_number` |
| PR全体のパッチ | `mcp__codex_apps__github_fetch_pr_patch` | `repo_full_name`, `pr_number` |
| コミットに対応するActionsの実行結果 | `mcp__codex_apps__github_fetch_commit_workflow_runs` | `repo_full_name`, `commit_sha` |

## 呼び出し例

PR #32なら `fetch_pr` に次の引数を渡す。

```json
{"repo_full_name": "tm-87-2026/atoyomin", "pr_number": 32}
```

## 取得結果の確認

- **関連Issue**: 本文などから番号を確認して `fetch_issue` で取得する。
- **差分**: `fetch_pr` の応答が大きい場合は本文とメタデータを先に確認し、パッチは別途取得する。必要な実装・テストの差分を省略されたまま判断しない。

- **CI**: 対象のhead SHAと照合する。`fetch_commit_workflow_runs` はPR起点の実行のみ・最初のページのみを返す。結果が空でも「検証未実施」と断定しない。
- **ローカル・実環境の検証**: それぞれの実行・確認記録を参照する。過去のPR本文の「成功」を現在の差分の結果として扱わない。

## ツールが使えない場合

| 状況 | 確認方法 |
| --- | --- |
| 認証済みのGitHub CLIが使える | `gh pr view`、`gh pr diff`、`gh issue view`、`gh pr checks` で補う。オプションはインストール済みCLIの `--help` で確認する |
| APIもCLIも使えない | ローカルの差分・共有されたIssueの内容・テスト記録で確認できる範囲を示し、不足する根拠だけ利用者に確認する |

GitのSSH認証とGitHub APIの認証は別に扱う。Git接続の成功だけでAPIも使えると判断しない。取得できない情報を推測で補わない。
