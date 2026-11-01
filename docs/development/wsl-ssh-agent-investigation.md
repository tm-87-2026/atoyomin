# WSLからDev ContainerへのSSH agent転送の検証記録

2026-11-02、Issue #28で確認した挙動と判断を記録する。採用した方針は[ADR 0008](../adr/0008-prepare-wsl-ssh-agent-before-opening-dev-container.md)、利用手順は[GitHub認証](github-authentication.md)を参照する。

## 目指す状態

ホストのagentが起動し、鍵を利用できることに加え、Dev Containersがその接続先を取得してコンテナへ転送できる状態を目指す。秘密鍵はコンテナへコピーしない。ホストとコンテナの`SSH_AUTH_SOCK`は、それぞれから見える通信窓口のパスであり、同じ値である必要はない。

## 実機で確認したこと

環境はWindows上のWSL Ubuntu、VS Code 1.144.0、Dev Containers 0.469.0、Dev Containers CLI 0.89.0。

1. WSLで手動起動したagentに鍵を登録すると、そのターミナルの`ssh-add -l`は成功した。WSL接続したVS Codeのターミナルでも成功した。
2. コンテナでは`SSH_AUTH_SOCK`が未設定で、`ssh-add -l`は失敗した。`/tmp`直下から深さ2までのSSH関連ソケットの検索にも結果がなかった。この検索だけで全ソケットの不存在を証明したわけではない。
3. 起動ログには次の記録があった。

   ```text
   ssh-agent: SSH_AUTH_SOCK not set on wsl host.
   ssh-agent: SSH_AUTH_SOCK not set on local host.
   ```

4. ホストで次を実行すると、接続先は空になり、agentに接続できなかった。

   ```sh
   env -u SSH_AUTH_SOCK bash -lic 'printf "SSH_AUTH_SOCK=%s\n" "$SSH_AUTH_SOCK"; ssh-add -l'
   ```

5. 現在のagentの接続先をホストの`~/.profile`に一時設定すると、同じ確認コマンドが成功した。これは診断用の固定値であり、agent再起動後も使える恒久設定ではない。
6. 利用者がVS Codeを開き直してコンテナへ接続し、コンテナ内の環境変数と鍵一覧、続けてGitHub認証・読み取り確認の成功を報告した。

標準転送が利用可能であることは確認できた。設定変更とVS Codeの開き直しを合わせて行ったため、それぞれの寄与は分離していない。pushとWSL再起動後の再現性は、この検証では確認していない。

## 初回設定を準備するタイミング

失敗時の実機ログでは、WSLホストの`userEnvProbe`（シェルからの環境取得）が462 msで始まり、579 msでPATHが記録された。CLIの`up`起動は2115 msだった。

CLI 0.89.0の[設定解決処理](https://github.com/devcontainers/cli/blob/v0.89.0/src/spec-node/configContainer.ts#L58)では、CLI起動後に`initializeCommand`を実行する。[コマンド実行処理](https://github.com/devcontainers/cli/blob/v0.89.0/src/spec-node/utils.ts#L502)はホストの子プロセスでコマンドを実行し、その環境変数を呼び出し元へ取り込む処理ではない。

したがって、次の順序になる。

```text
ホストのログイン環境を取得
  → CLIを起動
    → initializeCommandを実行
      → コンテナを起動
```

`initializeCommand`で初めて`~/.profile`を書き換えても、先に取得した環境にはさかのぼって反映されない。書いた内容は、次に設定が読み込まれるときに利用できる。

この順序の確認は、既存の実機ログと同一バージョンの公開実装の照合による。`initializeCommand`で設定を変更し、同じ起動で標準転送されるかを試す実験は行っていない。拡張による再取得の有無も確定しておらず、「initializeCommandでは絶対に実現できない」とは結論していない。初回からの確実性を優先し、環境取得前にセットアップを済ませる判断とした。

## 公式説明との対応

以下は2026-11-02に確認した。

- [Dev ContainersのSSH認証](https://code.visualstudio.com/remote/advancedcontainers/sharing-git-credentials#_using-ssh-keys)：ローカルagentの自動転送と、シェルのログイン設定でagentを準備する方法を案内している。
- [WSLの拡張ホストの環境設定](https://code.visualstudio.com/docs/remote/troubleshooting#_configure-the-environment-for-the-remote-extension-host)：ログイン用シェルから環境を取得すると説明している。
- [WSL Serverの環境設定](https://code.visualstudio.com/docs/remote/wsl#_advanced-environment-setup-script)：`~/.vscode-server/server-env-setup`はVS Code Server起動前の設定用である。拡張ホストの環境取得とは区別する。
- [過去の類似報告 #3902](https://github.com/microsoft/vscode-remote-release/issues/3902)：WSLのシェル起動設定によりagentを検出できない事例がある。ただし開発者は2022年に環境取得方法を変更したと説明しており、当時の不具合が現在も残る根拠とはしない。

## 残作業

- 初回セットアップと、ログイン時のagent起動・再利用処理を実装する。現時点では未実装。
- ホストに追加した診断用の固定パス設定を恒久設定に置き換える。
- 対話が必要な鍵登録の操作を用意し、手順を文書化する。
- WSL再起動・コンテナ再接続後の再現性と、作業ブランチへのpushを確認する。
