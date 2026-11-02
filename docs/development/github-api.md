# Dev ContainerからのGitHub API操作

SSHで扱えないIssue・PR・Projectsの操作は、コンテナ内のGitHub CLI（`gh`）と各メンバーのfine-grained PAT（対象と操作権限を指定できる個人用アクセストークン）で操作する。PATはリポジトリ直下の`.env.github`に`GH_TOKEN=値`の形式で平文保存し、`.gitignore`でGitの追跡対象から除外する。判断案は[ADR 0010](../adr/0010-use-limited-pat-for-github-api.md)を参照する。

Windows＋WSLではWSL側、macOSではMac側をホストとする。ホストへの`gh`導入やログイン設定の変更は不要で、通常の`code .`やVS Codeからの再接続を利用できる。Gitの取得・pushは今回変更せず、既存の[SSH認証](github-authentication.md)を利用する。Gitの認証もPATに統一するかは、この手順では判断しない。

## PATの発行と保存

組織の管理者はfine-grained PATの利用可否・承認要否を確認する。各メンバーはGitHubのSettings → Developer settings → Personal access tokens → Fine-grained tokensからPATを発行する。

- Resource owner: `tm-87-2026`。
- Organization permissions: ProjectsのRead and write。
- Repository access: Only select repositoriesで`atoyomin`だけを選択する。
- Repository permissions: IssuesとPull requestsのRead and write。Contentsなどのpush用権限は追加しない。
- PATは各メンバーが自分のものを発行し、共有しない。

Projects権限は特定のProjectだけに限定されない。組織の承認が必要な場合は承認後に接続確認する。

リポジトリ直下へ移動して、次を実行する。Windows＋WSLとmacOSのどちらでも利用できるよう、入力処理にはBashを明示する。

```sh
bash -c '
set +x
set -eu
umask 077
read -r -s -p "GitHub API用fine-grained PAT: " github_token </dev/tty
printf "\n"
touch .env.github
chmod 600 .env.github
printf "GH_TOKEN=%s\n" "$github_token" > .env.github
'
```

PATは非表示の入力欄へ貼り付ける。保存形式は引用符なしの`GH_TOKEN=github_pat_...`とする。空行と`#`で始まるコメント行を除き、この設定だけを記載する。スクリプトは`source`や`eval`を使わず値だけを読む。PATをコマンド引数や履歴に書かない。

これは暗号化された保管ではない。ホストとコンテナ内でファイルへアクセスできる処理はPATを読み取り・書き換えできる。`.gitignore`は誤コミットを減らすためのもので、`git add -f`やフォルダごとのコピーにはPATが含まれ得る。

## コンテナからの利用

コンテナへの`gh`導入を反映する初回は **Dev Containers: Rebuild and Reopen in Container** を実行する。envファイルは通常のワークスペース共有で参照するため、追加のマウントやホスト初期化処理は不要である。PATが未設定でもコンテナは起動でき、GitHub API用コマンドを実行した際に設定不足を通知する。

コンテナで次を実行する。

```sh
gh --version
bash tools/gh.sh project list --owner tm-87-2026
git remote get-url origin
```

CodexはIssue・PR・ProjectsのAPI操作に`bash tools/gh.sh`を使う。ファイルの読み込みはスクリプトに任せ、PATの表示や手動での環境変数設定は行わない。素の`gh`にはこのファイルのPATは自動供給されない。スクリプトは毎回ファイルを読み直し、起動する`gh`の環境変数だけにPATを渡す。VS Codeの起動方法や起動時の`GH_TOKEN`には依存しない。

初回設定時に各メンバーがPATを発行・保存し、以後の操作は依頼に応じてCodexが行う。Codexはユーザーが依頼した範囲で書き込みを実行し、PATや必要な権限が不足する場合は報告する。

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

Projectsは対象の組織とProjectを指定する。実際の書き込み確認は、確認用のIssue・PR・Project項目を使うなど、ユーザーと合意した対象で行う。

```sh
bash tools/gh.sh project view <Project番号> --owner tm-87-2026 --format json
bash tools/gh.sh project field-list <Project番号> --owner tm-87-2026 --format json
bash tools/gh.sh project item-list <Project番号> --owner tm-87-2026 --format json
bash tools/gh.sh project item-add <Project番号> --owner tm-87-2026 --url <IssueのURL>
bash tools/gh.sh project item-edit --id <項目ID> --project-id <ProjectのID> --field-id <StatusフィールドID> --single-select-option-id <選択肢ID>
```

IDやオプションは一覧のJSON出力と各コマンドの`--help`で確認する。標準コマンドで足りない情報は`bash tools/gh.sh api ...`のREST APIまたは`bash tools/gh.sh api graphql ...`で補える。APIを変えてもPATの権限は増えない。権限不足時には対象・組織の承認・必要な権限を確認し、一律に権限を広げない。

スクリプトは`issue`・`pr`・`project`・`api`を受け付けるが、PATの悪用を防ぐ境界はGitHub側の権限設定である。コンテナ内で`gh auth login`や`gh auth setup-git`は実行しない。トークンの表示やデバッグログへの記録も避ける。

必要な操作を確認するまでは既存プラグインを削除しない。GitHub Appは他の利用者・用途を確認してから別途整理する。

## 更新と解除

PATを更新する場合は新しいものを発行し、同じ保存手順でホストのファイルを差し替える。次のコマンド実行で新しいファイルを読む。VS Codeの終了やRebuildは不要である。古いPATはGitHub上で失効する。実行中の処理には既に取得した古いPATが残る。

利用をやめる場合はPATをGitHub上で失効し、`.env.github`を削除する。

Windows＋WSLとmacOSでのRebuild・envファイルの読み取り権限、および実際のIssue・PR・Projectsの取得・作成・編集は、各ホストでの検証が必要である。

以前の手順で`.env.github-projects`を作った場合は、`.env.github`へ名前を変更する。旧名も誤コミット防止のためignore対象として残している。
