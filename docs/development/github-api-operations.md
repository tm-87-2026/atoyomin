# Dev ContainerからのIssue・PR・Projects操作

[初回設定](github-api.md)を完了した環境で使うコマンド例。Dev Container内のターミナルで、リポジトリ直下から実行する。

`bash tools/gh.sh`が`.env.github`を読み、実行するGitHub CLI（`gh`）にPATを渡す。`gh`を直接実行しても、このファイルのPATは使われない。

Issue・PRは対象リポジトリを明示して操作する。

```sh
bash tools/gh.sh issue list --repo tm-87-2026/atoyomin
bash tools/gh.sh issue create --repo tm-87-2026/atoyomin --title <タイトル> --body-file <本文ファイル>
bash tools/gh.sh issue edit <番号> --repo tm-87-2026/atoyomin --body-file <本文ファイル>
bash tools/gh.sh pr list --repo tm-87-2026/atoyomin
bash tools/gh.sh pr create --repo tm-87-2026/atoyomin --head <push済みブランチ> --base main --title <タイトル> --body-file <本文ファイル>
bash tools/gh.sh pr edit <番号> --repo tm-87-2026/atoyomin --body-file <本文ファイル>
```

PRの元になるコードは先にSSHでpushする。PATにはコードを送信する権限を追加しない。

Projectsは対象の組織とProjectを指定する。作成・編集を試す場合は、確認用のIssueやProject項目を使う。

```sh
bash tools/gh.sh project view <Project番号> --owner tm-87-2026 --format json
bash tools/gh.sh project field-list <Project番号> --owner tm-87-2026 --format json
bash tools/gh.sh project item-list <Project番号> --owner tm-87-2026 --format json
bash tools/gh.sh project item-add <Project番号> --owner tm-87-2026 --url <IssueのURL>
bash tools/gh.sh project item-edit --id <項目ID> --project-id <ProjectのID> --field-id <StatusフィールドID> --single-select-option-id <選択肢ID>
```

IDやオプションは一覧のJSON出力と各コマンドの`--help`で確認する。標準コマンドで足りない情報は`bash tools/gh.sh api ...`のREST APIまたは`bash tools/gh.sh api graphql ...`で補える。APIを変えてもPATの権限は増えない。権限不足時には対象・組織の承認・必要な権限を確認し、一律に権限を広げない。

スクリプトは`issue`・`pr`・`project`・`api`を受け付けるが、PATの悪用を防ぐ境界はGitHub側の権限設定である。コンテナ内で`gh auth login`や`gh auth setup-git`は実行しない。トークンの表示やデバッグログへの記録も避ける。

