# Dev ContainerからGitHub APIを使うための初回設定

Issue・PR・ProjectsをDev Containerから操作できるようにする手順です。各メンバーが自分のGitHubアカウントでPAT（個人用アクセストークン）を発行し、設定します。Windows＋WSLとmacOSで共通です。

一覧を取得できれば初回設定は完了です。その後はCodexに操作を依頼できます。自分でコマンドを実行する場合は[操作例](github-api-operations.md)を参照してください。

Gitの取得・pushには別途[SSH認証の設定](github-authentication.md)が必要です。

## 1. コンテナを準備する

VS CodeでこのリポジトリをDev Containerとして開きます。以下のコマンドはすべて、**Dev Container内のターミナルで、リポジトリ直下から**実行してください。

```sh
gh --version
```

`gh version ...`が表示されれば、次へ進みます。`gh`が見つからない場合は、VS Codeのコマンドパレットで **Dev Containers: Rebuild and Reopen in Container** を実行し、もう一度確認してください。

## 2. 自分のPATを発行する

ブラウザーでGitHubへログインし、右上のプロフィール画像から **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token** を開きます。

次の内容で設定します。

| 項目 | 設定する値 |
| --- | --- |
| Token name | 用途が分かる名前（例：`atoyomin-dev`） |
| Resource owner | `tm-87-2026` |
| Repository access | **Only select repositories**で`atoyomin`を選択 |

続いて、**Permissions**で権限を追加します。リポジトリと組織の両方に設定が必要です。

1. **Repositories**タブで**Add permissions**を開き、**Issues**と**Pull requests**を追加します。それぞれのアクセス権を**Read and write**にします。
2. **Organizations**タブに切り替え、**Add permissions**から**Projects**を追加し、アクセス権を**Read and write**にします。
3. 発行前に、リポジトリ側のIssues・Pull requestsと、組織側のProjectsの3つが、すべて**Read and write**になっていることを確認します。

`atoyomin`を選択しただけではProjectsの権限は付きません。**Organizations側のProjectsも追加してください。** Organizationsタブが表示されない場合は、Resource ownerが自分のアカウントではなく`tm-87-2026`になっているか確認します。

有効期限は組織のポリシーに従って設定します。コードのpush用にContents権限を追加する必要はありません。Projects権限は組織内の特定のProjectだけには限定されません。

設定後、**Generate token**で発行します。表示されたトークンは次の手順で使います。自分のPATを他のメンバーと共有したり、チャットへ貼り付けたりしないでください。

`tm-87-2026`を選択できない場合や、組織の承認待ちになった場合は、組織の管理者に確認してください。承認が必要な場合、接続確認は承認後に行います。

## 3. PATを保存する

Dev Container内のターミナルに、次のコマンド全体を貼り付けて実行します。既に`.env.github`がある場合は、新しいPATで上書きします。

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

`GitHub API用fine-grained PAT:`と表示されたら、発行したPATを貼り付けてEnterを押します。入力した文字は画面に表示されません。入力待ちが終わり、エラーが出なければ保存は完了です。

PATはリポジトリ直下の`.env.github`に平文で保存されます。このファイルはGitの追跡対象から除外していますが、強制追加やフォルダーごとの共有には含まれ得るため、共有しないでください。

## 4. 接続を確認する

同じターミナルで、次を1つずつ実行します。

```sh
bash tools/gh.sh issue list --repo tm-87-2026/atoyomin
bash tools/gh.sh pr list --repo tm-87-2026/atoyomin
bash tools/gh.sh project list --owner tm-87-2026
```

それぞれの一覧が表示されれば設定は完了です。対象がない場合は、項目がない旨の表示でも正常です。これらのコマンドは一覧の取得だけを行い、データを変更しません。作成・編集の確認は、確認用の対象を決めて別途行います。

### うまくいかない場合

| 症状 | 確認すること |
| --- | --- |
| `gh`が見つからない | 手順1のRebuildを実行し、Dev Container内で操作しているか確認する |
| `GitHub API用PATを読み取れません` | 手順3を実行したか、リポジトリ直下に`.env.github`があり、読み取り可能か確認する |
| `GH_TOKENには引用符なしのfine-grained PATを指定してください`などの形式エラー | 手順3をやり直す。保存形式は引用符なしの`GH_TOKEN=github_pat_...`のみとする |
| `401`や`Bad credentials` | PATの入力間違い・有効期限・失効を確認し、必要なら再発行して手順3をやり直す |
| `403`、`404`や権限不足 | Resource owner、対象リポジトリ、手順2の権限（Organizations側のProjectsを含む）、組織の承認状況を確認する |

認証には`bash tools/gh.sh`を使います。コンテナ内で`gh auth login`や`gh auth setup-git`を実行する必要はありません。エラーを相談するときは、PATや`.env.github`の中身を貼らず、実行したコマンドとエラーメッセージを伝えてください。

## PATの更新・利用終了

更新するときは新しいPATを発行し、手順3で保存し直して手順4で確認します。次のコマンド実行から反映されるため、VS Codeの再起動やRebuildは不要です。使わなくなった古いPATはGitHubのFine-grained tokens画面で失効させてください。

利用をやめる場合は、GitHubでPATを失効させ、`.env.github`を削除します。

認証方式と保存方法を選んだ理由は[ADR 0010](../adr/0010-use-limited-pat-for-github-api.md)に記載しています。
