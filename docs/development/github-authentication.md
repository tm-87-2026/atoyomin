# Dev Container からの GitHub 認証

Git操作にはホストのSSH鍵とDev Containersの標準agent転送を利用する。判断と理由は[ADR 0007](../adr/0007-use-host-ssh-authentication-for-development.md)を参照する。

## ホストの準備

ホスト側でSSH鍵を用意し、公開鍵を自分のGitHubアカウントに登録する。既存の鍵が利用できる場合は作り直す必要はない。秘密鍵はホストに置き、コンテナやリポジトリへコピーしない。

- [GitHub：SSH接続の設定](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [VS Code：ホストOSごとのagent設定](https://code.visualstudio.com/remote/advancedcontainers/sharing-git-credentials#_using-ssh-keys)

### Windows＋WSL

ホスト側のログイン設定は、コンテナ接続前の初回セットアップで準備する方針とした（[ADR 0008](../adr/0008-prepare-wsl-ssh-agent-before-opening-dev-container.md)）。自動化用スクリプトは未実装であり、以下は手動の準備手順である。標準転送の検証経緯と起動順序は[検証記録](wsl-ssh-agent-investigation.md)を参照する。

VS CodeでリポジトリをWSLから開く場合は、WSL側でagentが鍵を利用できるようにする。まずWSLターミナルで確認する。

```sh
ssh-add -l
```

agentに接続できない場合は、そのターミナルで起動する。

```sh
eval "$(ssh-agent -s)"
```

鍵が読み込まれていなければ追加する。ファイル名は自分の鍵に合わせる。

```sh
ssh-add ~/.ssh/id_ed25519
ssh -T git@github.com
```

認証成功メッセージを確認してから、同じWSLターミナルでリポジトリへ移動し `code .` を実行する。すでにVS CodeやWSL側のVS Code Serverが起動していると、新しいagentの環境を引き継がない場合がある。転送できない場合は、Dev Containersのログでagentの検出状況を確認する。VS Codeの既存プロセスが古い環境を利用している場合は、未保存ファイルを保存してVS CodeとWSL側のVS Code Serverを終了し、agentを利用できるWSLターミナルから開き直す。

WSL再起動後もagentを利用するためのログイン時設定は、上記VS Code公式ガイドを参照する。パスフレーズ付きの鍵は、agentへの追加時に入力を求められることがある。

### macOS

ホストのターミナルで `ssh-add -l` を確認し、必要なら `ssh-add ~/.ssh/id_ed25519` で鍵を追加する。`ssh -T git@github.com` で認証できることを確認してから、VS Codeでリポジトリを開く。

## コンテナからの確認

VS Codeで **Dev Containers: Rebuild and Reopen in Container** を実行する。SSH agentの転送はDev Containersに任せ、独自のソケットマウントや `SSH_AUTH_SOCK` の固定設定は追加しない。

コンテナ内で次を実行する。

```sh
ssh-add -l
ssh -T git@github.com
git remote set-url origin git@github.com:tm-87-2026/atoyomin.git
git remote get-url origin
git ls-remote origin HEAD
```

初回接続でホスト鍵の確認を求められた場合は、[GitHubが公開する指紋](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints)と照合する。`ssh -T` は認証成功メッセージを表示しても終了コード1を返す。

鍵が表示され、GitHubの認証成功メッセージとHEADの参照を取得できれば読み取りの確認は完了である。書き込みは、完成した変更を作業ブランチへpushする際に確認する。Rebuild後も同じ確認を行う。

agentに接続できない場合は、ホスト側の `ssh-add -l` と、Dev Containersのログでagent転送を確認する。コンテナ内で新たにagentを起動しても、ホストの鍵は利用できない。

## 旧PAT設定からの移行

以前のセットアップスクリプトを実行した環境では、コンテナ内の古いGit設定を削除する。以下は旧スクリプトが追加した設定だけを対象とする。設定がなければエラーで終了するが、追加の対応は不要である。

```sh
git config --global --fixed-value --unset-all url.https://github.com/.insteadOf 'git@github.com:'
git config --global --remove-section credential.https://github.com/tm-87-2026/atoyomin.git
```

その後、上記の手順でremoteをSSH形式へ変更する。既存コンテナの設定はRebuildしても残らない場合があるため、Rebuild後にも `git remote get-url origin` がSSH形式になっていることを確認する。

PATを発行していた場合は、GitHubで不要なPATを削除する。旧volume `atoyomin-git-credentials` と `atoyomin-gh-config` は自動削除しない。不要であることを確認したうえで、コンテナをRebuildしてマウントを外してから、ホストで削除する。

```sh
docker volume rm atoyomin-git-credentials atoyomin-gh-config
```

PR作成などGitHub APIを利用するツールの認証は、このGit接続とは別に扱う。
