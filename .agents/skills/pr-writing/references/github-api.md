# GitHub APIの参照先

このリポジトリのAPI操作は[GitHub APIの操作手順](../../../../docs/development/github-api.md)に従い、`bash tools/gh.sh`経由でGitHub CLIを利用する。PATを表示せず、ファイルの読み込みはスクリプトに任せる。

## 利用前の確認

- **接続先**: 依頼のURLまたは`git remote get-url origin`からリポジトリを特定する。番号だけで他のリポジトリを検索しない。
- **操作範囲**: この資料は読み取り用。PR本文の更新やレビュー投稿は、Skill本文の「承認・反映」に従う。
- **オプション**: インストール済みCLIの各コマンドの`--help`で確認する。

## 読み取りに使うコマンド

以下は`bash tools/gh.sh`に続けて指定し、`--repo`には対象の`owner/name`を渡す。

| 確認する情報 | コマンド |
| --- | --- |
| Issueの要求・完了条件 | `issue view <番号> --repo <owner/name>` |
| PRのタイトル・本文・head SHA | `pr view <番号> --repo <owner/name> --json title,body,headRefOid` |
| PRの会話・レビュー | `pr view <番号> --repo <owner/name> --comments` |
| PR全体の差分 | `pr diff <番号> --repo <owner/name>` |
| PRのチェック結果 | `pr checks <番号> --repo <owner/name>` |

レビューのインラインコメントなど標準コマンドで足りない情報は、`api`でREST APIまたはGraphQL APIを呼び出して補う。必要なコメントを省略したまま判断しない。

## 取得結果の確認

- **関連Issue**: PR本文などから番号を確認して取得する。
- **差分**: 本文とメタデータだけで変更内容を判断せず、実際の差分を確認する。
- **CI**: 対象のhead SHAと照合する。結果が空でも「検証未実施」と断定しない。Actionsなどの権限不足で取得できない場合は、その旨を示す。
- **ローカル・実環境の検証**: 実行記録を参照し、過去のPR本文の成功を今回実行した結果として扱わない。

CLIやPATが利用できない場合は、ローカルの差分・共有されたIssue・テスト記録で確認できる範囲と、取得できない情報を示す。GitのSSH接続の成功だけでAPIも利用できると判断しない。
