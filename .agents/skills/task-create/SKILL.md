---
name: task-create
description: "GitHub Issueのタスクを起票する。「タスクを切る」「Issueを作る」という依頼で、重複確認・本文作成・ラベル選択・Project登録を行う。"
---

# タスク起票

## 対象と操作経路

- 依頼のURL、または `git remote get-url origin` から対象の `owner/name` を特定する。番号だけで他のリポジトリを検索しない。
- リポジトリの `AGENTS.md` と変更対象に適用される規約を確認する。
- API操作の前に[認証・接続手順](../../../docs/development/github-api.md)を読み、コマンドは[操作例](../../../docs/development/github-api-operations.md)を参照する。Issue・PR・Projectsはリポジトリ直下で `bash tools/gh.sh` を使う。Gitの取得・pushは既存のSSH接続を使う。
- PATの読み込みはラッパーに任せ、認証情報を表示・記録しない。CLIの引数やJSON項目は必要に応じて対象コマンドの `--help` で確認する。

## 新しいタスクを切る

1. 同じ目的のIssueを開閉両方の状態で検索し、候補の本文を確認する。起票者が同じという理由だけで同一タスクにしない。
2. 同じ目的のIssueが見つかった場合は、状態と内容を確認して候補を示し、既存を使うか新しく起票するか利用者に確認する。確認前に既存Issueの本文を更新しない。
3. 起票時点で分かっている内容をタイトルと本文に記載する。目的・範囲・完了条件が未整理でも起票する。それらの具体化を起票の条件にせず、不明点を推測で補ったり、形式を埋めるためだけに質問したりしない。必要な関連リンクを添え、長い本文は一時ファイルに書いて `--body-file` で渡す。目的・範囲・完了条件の具体化は、着手後の[開発ワークフロー](../../../docs/development/development-workflow.md)で扱う。
4. 既存ラベルの説明を確認し、タスクの主目的に合う**1個**を付ける。合うものがなければ新設を即断せず相談する。既存Issueのラベルを直すときは変更対象と現在値を確認する。
5. 起票時は担当者を設定しない。担当者の設定はタスク開始時に行う。利用者から起票時の担当者を明示的に指定された場合は、その指示に従う。
6. 対象Projectを確認して登録する。既存登録を重複させず、未着手のStatusはProjectの選択肢に合わせる。

## 作業方法と環境のラベル

- `kaizen`: 開発フロー、Skill、レビュー手順など、どう作業するかの改善。
- `environment`: Dev Container、認証、CI、デプロイなど、作業・実行の基盤の整備。

成果物の形式ではなくタスクの主目的で選ぶ。例として #23のSkill整備と #40の開発ワークフロー定義は `kaizen`、GitHub接続の整備は `environment` に当たる。両方にまたがり主目的が曖昧な場合は、利用者に確認してから1個を選ぶ。

## その他のラベル

- `feature`: 利用者向けの機能追加・拡張。
- `documentation`: 説明資料の追加・更新が主目的。
- `refactor`: 動作を変えずにコード構造を改善する。

## 不具合系のラベル

不具合の調査・修正は `fix` に統一する。`bug` ラベルは使わない。

## コマンドと確認

以下はリポジトリ直下で実行する例。対象リポジトリ・検索語・ラベル・Project番号は確認した値に置き換える。

```sh
bash tools/gh.sh issue list --repo <owner/name> --state all --search '<検索語>' --limit 100
bash tools/gh.sh api --paginate repos/<owner/name>/labels
bash tools/gh.sh issue create --repo <owner/name> --title '<タイトル>' --label <ラベル1個> --body-file <本文ファイル>
bash tools/gh.sh project list --owner <owner> --format json
bash tools/gh.sh project item-add <Project番号> --owner <owner> --url <作成したIssueのURL>
bash tools/gh.sh issue view <番号> --repo <owner/name> --json number,title,body,labels,assignees,projectItems
```

検索の取得上限・ページ数を確認し、候補は本文まで読む。既存Issueの更新は `issue edit` を使う。Projectは依頼や既存の運用から特定し、候補が曖昧な場合だけ確認する。登録後のStatusが未設定なら、操作例に従って実際のフィールド・選択肢IDを取得し、未着手の状態にする。

起票の依頼は、この範囲のIssue作成・Project登録を含む。相談だけでは公開しない。作成後はIssueとProjectの値を再取得し、リンクと結果を報告する。成否不明なら再取得してから再実行し、重複起票を避ける。接続・権限不足は認証手順に照らして確認し、未反映の操作を報告する。
