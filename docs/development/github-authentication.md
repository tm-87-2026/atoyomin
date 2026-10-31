# Dev Container からの GitHub 認証

認証方式の判断と理由は[ADR 0006](../adr/0006-use-fine-grained-pat-for-development-github-authentication.md)を参照する。ここでは、開発者ごとの初回設定と更新手順を説明する。

## PATの発行

GitHubの Settings → Developer settings → Personal access tokens → Fine-grained tokens でトークンを作成する。

- Resource owner：`tm-87-2026`
- Repository access：Only select repositories で `atoyomin` のみを選択
- Repository permissions：Contents を Read and write
- Expiration：利用期間に応じた有効期限を設定

PRも操作する場合はPull requestsのRead and write、GitHub Actionsのワークフローファイルを更新する場合はWorkflowsの書き込み権限を追加する。組織の設定により承認が必要な場合は、承認後に接続を確認する。

設定項目と制約は[GitHubのPAT管理ガイド](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)を参照する。

## コンテナへの保存

1. VS Codeで **Dev Containers: Rebuild and Reopen in Container** を実行する。
2. コンテナ内ターミナルで次を実行し、入力欄にPATを貼り付ける。入力内容は画面に表示されない。

   ```sh
   bash .devcontainer/setup-github-auth.sh
   ```

3. 接続を確認する。

   ```sh
   git remote get-url origin
   git ls-remote origin HEAD
   ```

URLがHTTPS形式で表示され、HEADの参照を取得できれば読み取り接続は成功である。書き込みは、完成した変更を作業ブランチへpushする際に確認する。

PATは専用Docker volume `atoyomin-git-credentials` 内に、Gitのcredential store（認証情報の保存機能）で保存する。保存先ディレクトリは所有者のみアクセス可能、ファイルは所有者のみ読み書き可能とする。**保存内容は暗号化されないため、Dockerの管理権限を持つ利用者からは読み取れる。** [Git公式の保存仕様](https://git-scm.com/docs/git-credential-store)

PATをコマンドの引数、リポジトリ内のファイル、チャットに記載しない。この設定では、Gitは `tm-87-2026/atoyomin.git` へのHTTPS接続時に保存したPATを使用する。SSH形式のremoteもHTTPSへ変換し、remote URL自体は変更しない。

## Rebuildと更新

Rebuild後もvolume内のPATを再利用する。Gitの認証設定はコンテナ作成時に再設定される。Rebuild後に `git ls-remote origin HEAD` を実行し、再入力なしで利用できることを確認する。

期限切れや権限変更時は、新しいPATを発行してセットアップスクリプトを再実行する。接続確認後、不要になった古いPATをGitHubで削除する。利用を終了する場合はGitHubでPATを失効させ、保存ファイルも削除する。

```sh
rm -f ~/.config/atoyomin/credentials
```

GitHub CLIのブラウザ認証はこの手順では使わない。以前の方式で認証を完了していた場合は、必要に応じてGitHubのSettings → ApplicationsからGitHub CLIの認可を取り消す。他の環境でも同じ認可を利用している場合は、その影響を確認してから取り消す。
