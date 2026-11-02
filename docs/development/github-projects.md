# Dev ContainerからのGitHub Projects操作

Projectsはコンテナ内のGitHub CLI（`gh`）と各メンバーのfine-grained PAT（対象と操作権限を指定できる個人用アクセストークン）で操作する。PATはホストのリポジトリ外に平文保存し、コンテナへ読み取り専用で共有する。判断案は[ADR 0010](../adr/0010-use-limited-pat-for-github-projects.md)を参照する。

Windows＋WSLではWSL側、macOSではMac側をホストとする。ホストへの`gh`導入やログイン設定の変更は不要で、通常の`code .`やVS Codeからの再接続を利用できる。Gitの取得・pushは既存の[SSH認証](github-authentication.md)を利用する。Issue・PR自体の作成・編集は今回の移行範囲に含めない。

## PATの発行と保存

組織の管理者はfine-grained PATの利用可否・承認要否・有効期限のポリシーを確認する。各メンバーはGitHubのSettings → Developer settings → Personal access tokens → Fine-grained tokensからPATを発行する。

- Resource owner: `tm-87-2026`。
- Organization permissions: ProjectsのRead and write。
- Repository access: 最初はPublic repositoriesにとどめ、Repository permissionsは追加しない。非公開リポジトリのIssue・PRを扱う際は対象を`atoyomin`に絞り、必要な読み取り権限だけを検証して追加する。Contentsの書き込み権限は付与しない。
- 有効期限: 組織のポリシーの範囲で30〜90日。PATは共有しない。

Projects権限は特定のProjectだけに限定されない。組織の承認が必要な場合は承認後に接続確認する。

ホストのターミナルで次を実行する。Windowsではコンテナ内ではなくWSLで実行する。macOSの標準シェルからも実行できるよう、入力処理にはBashを明示する。

```sh
bash -c '
set +x
set -eu
umask 077
pat_dir="$HOME/.config/atoyomin/projects"
mkdir -p "$pat_dir"
chmod 700 "$pat_dir"
read -r -s -p "Projects用fine-grained PAT: " projects_token </dev/tty
printf "\n"
pat_tmp=$(mktemp "$pat_dir/.token.XXXXXX")
trap '\''rm -f "$pat_tmp"'\'' EXIT
printf "%s\n" "$projects_token" > "$pat_tmp"
chmod 600 "$pat_tmp"
mv -f "$pat_tmp" "$pat_dir/token"
'
```

PATは非表示の入力欄へ貼り付ける。保存ファイルにはPATだけが1行で入り、シェルコードとして読み込まない。PATをコマンド引数や履歴、リポジトリの`.env`に書かない。

これは暗号化された保管ではない。ホストの同じユーザー権限の処理と、共有したコンテナ内の処理はPATを読み取れる。読み取り専用マウントは書き換えを防ぐが、読み取りや持ち出しは防がない。

## コンテナからの利用

設定を反映する初回は **Dev Containers: Rebuild and Reopen in Container** を実行する。`gh`をコンテナへ導入し、ホストの`~/.config/atoyomin/projects`を`/run/atoyomin-projects`へ読み取り専用でマウントする。

初期化処理はホストに保存先ディレクトリだけを作る。PATが未設定でもコンテナは起動でき、Projects用コマンドを実行した際に設定不足を通知する。既存ディレクトリの権限は変更しない。

コンテナで次を実行する。

```sh
gh --version
bash tools/gh-projects.sh project list --owner tm-87-2026
git remote get-url origin
```

Projects操作は`bash tools/gh-projects.sh project ...`を使う。素の`gh project ...`にはこのファイルのPATは供給されない。スクリプトは毎回ファイルを読み直し、起動する`gh`の環境変数だけにPATを渡す。VS Codeの起動方法や起動時の`GH_TOKEN`には依存しない。

一覧取得だけでは移行完了とせず、対象のProjectでフィールド・項目の取得、既存Issueの追加、Statusの更新を確認する。書き込み確認は専用の確認用項目で行う。

```sh
bash tools/gh-projects.sh project view <Project番号> --owner tm-87-2026 --format json
bash tools/gh-projects.sh project field-list <Project番号> --owner tm-87-2026 --format json
bash tools/gh-projects.sh project item-list <Project番号> --owner tm-87-2026 --format json
bash tools/gh-projects.sh project item-add <Project番号> --owner tm-87-2026 --url <IssueのURL>
bash tools/gh-projects.sh project item-edit --id <項目ID> --project-id <ProjectのID> --field-id <StatusフィールドID> --single-select-option-id <選択肢ID>
```

IDやオプションは一覧のJSON出力と各コマンドの`--help`で確認する。標準コマンドが足りない場合は`bash tools/gh-projects.sh api graphql ...`で補える。APIを変えてもPATの権限は増えない。非公開Issueの取得・追加が失敗する場合は、組織の承認と、対象リポジトリのIssuesまたはPull requestsの読み取り権限を確認し、権限を一律に広げない。

スクリプトは`project`と`api graphql`だけを受け付けるが、PATの悪用を防ぐ境界はGitHub側の権限設定である。コンテナ内で`gh auth login`や`gh auth setup-git`は実行しない。トークンの表示やデバッグログへの記録も避ける。

必要な操作を確認するまでは既存プラグインを削除しない。GitHub Appは他の利用者・用途を確認してから別途整理する。

## 更新と解除

期限前に新しいPATを発行し、同じ保存手順でホストのファイルを差し替える。ディレクトリをマウントしているため、次のコマンド実行で新しいファイルを読む。VS Codeの終了やRebuildは不要である。古いPATはGitHub上で失効する。実行中の処理には既に取得した古いPATが残る。

利用をやめる場合はPATをGitHub上で失効し、ホストの`~/.config/atoyomin/projects/token`を削除する。

Windowsの`gh`を既に設定した場合でも、この方式では使用しない。不要な認証設定は、他の用途を確認したうえでWindowsの`gh auth logout`で別途削除する。

Windows＋WSLとmacOSでのRebuild・読み取り専用マウント・ファイル権限、および実際のProjectsの取得・追加・更新は、各ホストでの検証が必要である。
