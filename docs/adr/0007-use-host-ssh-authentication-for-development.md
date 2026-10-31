# ADR 0007: 開発環境のGit操作にホストのSSH認証を利用する

## Status

Accepted — 2026-10-31。ADR 0006を置き換える。

## Context

開発コンテナからGitHubを利用でき、チームの認証準備と日常の管理負担を抑えたい。認証情報の平文での永続保存も避けたい。

[ADR 0006](0006-use-fine-grained-pat-for-development-github-authentication.md)では、対象リポジトリを限定できるfine-grained PAT（操作権限を指定できる個人用アクセストークン）を採用した。しかし、保管と更新の運用まで考えると、ホスト側の設定や別の保管手段が必要になる。権限をリポジトリ単位で限定することは必須条件とせず、既存の認証を利用して管理対象を増やさないことを優先する。

VS CodeのDev Containersには、ホストのSSH agent（秘密鍵を使った認証要求に応答する常駐プログラム）をコンテナへ自動転送する機能がある。2026-10-31に[公式ガイド](https://code.visualstudio.com/remote/advancedcontainers/sharing-git-credentials)で確認した。

## Decision

開発コンテナからのGit操作には、ホストで管理するSSH鍵とDev Containersの標準agent転送を利用する。秘密鍵はコンテナへコピーせず、ホストで管理する。

## Consequences

- コンテナ専用のPATの発行・保管・更新が不要になる。
- 各開発者のホストでSSH鍵とagentを準備する必要がある。
- 個人アカウントのSSH鍵は、利用先をあとよみんのリポジトリだけには限定できない。
- PR作成などGitHub APIを使う操作の認証は、この判断の対象外とする。
