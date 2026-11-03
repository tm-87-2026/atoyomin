---
name: task-start
description: "GitHub Issue番号を指定した「#番号に着手する」「#番号のタスクを開始する」という呼びかけで、ブランチ・worktreeを準備し、別ウィンドウで開く。"
---

# タスク開始

## 対象と操作経路

- 依頼のURL、または `git remote get-url origin` から対象の `owner/name` を特定する。番号だけで他のリポジトリを検索しない。
- リポジトリの `AGENTS.md` と変更対象に適用される規約を確認する。
- API操作の前に[認証・接続手順](../../../docs/development/github-api.md)を読み、コマンドは[操作例](../../../docs/development/github-api-operations.md)を参照する。Issue・PR・Projectsはリポジトリ直下で `bash tools/gh.sh` を使う。Gitの取得・pushは既存のSSH接続を使う。
- PATの読み込みはラッパーに任せ、認証情報を表示・記録しない。CLIの引数やJSON項目は必要に応じて対象コマンドの `--help` で確認する。

## ブランチのprefix

Issueのラベルから次の対応表でprefixを選び、ブランチ名を `<prefix>/<Issue番号>` とする。

| Issueラベル | prefix |
| --- | --- |
| `environment` | `env` |
| `documentation` | `docs` |
| `kaizen` | `kaizen` |
| `refactor` | `refactor` |
| `feature` | `feat` |
| `fix` | `fix` |

## 「#番号に着手する」

開始の呼びかけでは、ブランチ・worktreeを準備し、別ウィンドウで開いて準備完了を報告する。開始時には本人をIssueの担当者に追加する。実装、コミット、push、PR作成、Projectの更新や担当者以外のIssue更新へ自動的に進まない。

- Issueと既存ブランチ・worktree、作業ツリーの状態を確認する。利用者の変更を移動・破棄しない。
- `bash tools/gh.sh api user --jq .login` で認証中のアカウントを確認し、開始する本人として識別できたら `issue edit <番号> --repo <owner/name> --add-assignee <login>` で担当者に追加する。既存担当者は外さない。別人の認証など本人との対応が不明なら確認する。追加後は `issue view <番号> --repo <owner/name> --json assignees` で反映を確認する。
- `git worktree list --porcelain` の先頭のworktreeを元リポジトリとして確認する。現在位置が既存worktreeでも、配置先とPATの参照元は元リポジトリを基準にする。
- ブランチ名は対応表の `<prefix>/<Issue番号>`、worktreeの配置先はリポジトリ直下の `.worktrees/<prefix>-<Issue番号>` とする。例: `env/23` と `.worktrees/env-23`。
- 新規ブランチは `git fetch origin` の成功を確認し、最新の `origin/main` から作成する。取得に失敗した場合、古い参照を最新として扱わない。
- 同じタスクのブランチ・worktreeが既にある場合は再利用する。既存ブランチを `origin/main` にリセットしない。別の配置先にある既存worktreeも重複作成せず、その場所を使う。
- ブランチだけ存在する場合は、そのブランチにworktreeを追加する。既存ディレクトリを上書きせず、衝突があれば状況を確認する。
- 別ウィンドウで開く前に、元リポジトリの `.env.github` へのシンボリックリンクを対象worktree直下に作る。PATはコピー・表示しない。既存ファイルや異なる参照先のリンクは上書きせず確認する。元ファイルがなければ接続手順を案内し、認証未設定として報告する。
- 対象worktreeを `code --new-window <worktreeの絶対パス>` で開く。起動に失敗した場合は作成済みの状態と失敗内容を報告し、ウィンドウが開いたと断定しない。

## コマンドと確認

最初に対象Issueと作業状態を確認する。

```sh
git remote get-url origin
bash tools/gh.sh issue view <番号> --repo <owner/name> --comments
bash tools/gh.sh issue view <番号> --repo <owner/name> --json number,state,labels
git status --short --branch
git worktree list --porcelain
git branch --list
git branch --remotes
```

ラベルが未設定・複数・対応表にない場合はprefixを確認する。閉じたIssueは再開の意図を確認する。

以下は新規タスクの例。変数には確認した値を設定する。

```sh
# git worktree list --porcelain の先頭のworktreeを元リポジトリとして確認する。
task_root=/workspaces/atoyomin
task_branch=kaizen/23
task_path="$task_root/.worktrees/kaizen-23"
git fetch origin
# fetch成功後に実行する。originに同名ブランチがある場合は下の再利用手順へ進む。
git check-ignore "$task_path"
mkdir -p "$task_root/.worktrees"
git worktree add -b "$task_branch" "$task_path" origin/main
# 元ファイルが存在し、リンク先に既存ファイルがないことを確認してから実行する。
ln -s "$task_root/.env.github" "$task_path/.env.github"
# 対象worktreeをカレントディレクトリにしてAPI接続を確認する。
(cd "$task_path" && bash tools/gh.sh api user --jq .login)
code --new-window "$task_path"
git -C "$task_path" branch --show-current
git worktree list --porcelain
```

`.worktrees/` が追跡対象にならないことを確認する。除外されていなければローカルのGit除外設定である共通Gitディレクトリの `info/exclude` に `/.worktrees/` を重複なく追加する。開始処理のために共有の `.gitignore` をコミットしない。

ローカルブランチがある場合は `git worktree add "$task_path" "$task_branch"`、リモートだけにある場合は `git worktree add --track -b "$task_branch" "$task_path" "origin/$task_branch"` で再利用する。既にチェックアウトされていれば、そのworktreeを開く。

コマンドは一段階ずつ成功を確認する。失敗したまま次へ進まない。作成・起動の結果を区別し、ブランチ名・worktreeのパス・ウィンドウ起動コマンドの結果を報告して終了する。新しいウィンドウへのCodex会話の引き継ぎや、上記リンク以外の認証・開発環境設定は自動的に行わない。開いた後の開発ワークフローは #40 で別途定義する。
