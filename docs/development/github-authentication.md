# Dev Container からの GitHub 認証

Git操作にはホストのSSH鍵とDev Containersの標準agent転送を利用する。判断と理由は[ADR 0007](../adr/0007-use-host-ssh-authentication-for-development.md)を参照する。

## ホストの準備

ホスト側でSSH鍵を用意し、公開鍵を自分のGitHubアカウントに登録する。既存の鍵が利用できる場合は作り直す必要はない。秘密鍵はホストに置き、コンテナやリポジトリへコピーしない。

- [GitHub：SSH接続の設定](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [VS Code：ホストOSごとのagent設定](https://code.visualstudio.com/remote/advancedcontainers/sharing-git-credentials#_using-ssh-keys)

### Windows＋WSL

ホスト側の初回セットアップを、コンテナ接続前に行う（[ADR 0008](../adr/0008-prepare-wsl-ssh-agent-before-opening-dev-container.md)）。標準転送の検証経緯と起動順序は[検証記録](wsl-ssh-agent-investigation.md)を参照する。

WSLホストにBash、OpenSSHの`ssh-agent`・`ssh-add`・`ssh-keygen`、`flock`が必要である。Ubuntuでは通常利用できる。以下はコンテナ内ではなく、ホスト側のWSLターミナルでリポジトリへ移動して実行する。

```sh
bash .devcontainer/setup-host-ssh.sh
bash .devcontainer/add-github-ssh-key.sh
```

初回セットアップは、Bashが優先して読む`~/.bash_profile`、`~/.bash_login`、`~/.profile`のいずれかに共通処理の呼び出しを登録する。通常は`~/.profile`が対象になる。元の設定は表示されたバックアップ先へ保存し、他の設定は保持する。再実行しても呼び出しは重複しない。#28の検証で追加した`env-28 temporary agent test`のブロックは自動で置き換える。

鍵登録コマンドは、標準では`~/.ssh/id_ed25519`と対応する`.pub`ファイルを使う。登録済みなら何もせず、未登録の場合だけ`ssh-add`を実行する。パスフレーズは、この操作中に本人が入力する。別の鍵を使う場合は、その秘密鍵のパスを指定する。

```sh
bash .devcontainer/add-github-ssh-key.sh ~/.ssh/github_work
```

agentはWSLホストの`~/.ssh/atoyomin-agent/agent.sock`を使い、既存の別用途のagentとは分離する。新しいBashログイン環境が準備される際に、共通処理がagentを起動・再利用し、接続先を環境変数に設定する。鍵の作成やGitHubへの公開鍵登録は自動では行わない。

初回設定後は、未保存ファイルを保存してVS Codeの全ウィンドウを閉じ、ホスト側のWSLターミナルから開き直す。

```sh
code --new-window --remote wsl+Ubuntu .
```

`Ubuntu`は使用するディストリビューション名に合わせる。その後、Dev Containersでコンテナを開き、次節の接続確認を行う。コンテナの設定変更がない場合、Rebuildは不要である。

通常のコンテナ再接続やRebuildでは、agentが保持している鍵を再利用する。WSL再起動などでagentが終了すると鍵の登録は失われるため、同じ鍵登録コマンドをWSLターミナルで実行してからコンテナへ接続する。初回セットアップを繰り返す必要はない。ログイン設定からは対話的な鍵登録を行わない。

共通処理はセットアップ時のリポジトリの絶対パスを参照する。リポジトリを移動した場合は新しい場所から初回セットアップを再実行する。削除した場合、ログイン設定の`BEGIN atoyomin SSH agent`から`END atoyomin SSH agent`までのブロックを削除すれば呼び出しを解除できる。

転送できない場合は、ホスト側で次を確認する。

```sh
env -u SSH_AUTH_SOCK bash -lic 'printf "SSH_AUTH_SOCK=%s\n" "$SSH_AUTH_SOCK"; ssh-add -l'
```

鍵が表示されるのに転送されない場合は、Dev Containersのログの`ssh-agent:`の行を確認する。VS Codeが古い環境を保持している場合は、開き直しが必要になる。

### macOS

ホストのターミナルで `ssh-add -l` を確認し、必要なら `ssh-add ~/.ssh/id_ed25519` で鍵を追加する。`ssh -T git@github.com` で認証できることを確認してから、VS Codeでリポジトリを開く。

## コンテナからの確認

VS Codeでコンテナを開く。Dockerfileなどの設定変更を反映する場合は **Dev Containers: Rebuild and Reopen in Container** を実行する。SSH agentの転送はDev Containersに任せ、独自のソケットマウントや `SSH_AUTH_SOCK` の固定設定は追加しない。

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
