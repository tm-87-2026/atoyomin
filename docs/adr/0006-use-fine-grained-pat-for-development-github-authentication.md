# ADR 0006: 開発環境のGitHub認証にfine-grained PATを採用する

## Status

Accepted — 2026-10-31

## Context

開発コンテナからGitHubのリポジトリを取得・更新でき、そのために与える権限をあとよみんの開発に必要な範囲に限定したい。

#28ではGitHub CLI（GitHubをコマンドで操作するツール）のブラウザ認証を試したが、あとよみん以外のリポジトリや所属組織にも及ぶ権限が要求された。SSH鍵を利用する方式も試したが、ホスト側の認証エージェントをコンテナへ引き継ぐ設定に手間がかかった。

fine-grained PAT（対象リポジトリと操作権限を指定できる個人用アクセストークン）では、権限をリポジトリ単位で限定できる。機能と制約は2026-10-31に[GitHub公式ドキュメント](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)で確認した。

## Decision

開発コンテナからGitHubへアクセスする認証方式として、fine-grained PATを採用する。対象はあとよみんのリポジトリに限定し、開発に必要な操作権限だけを付与する。

## Consequences

- 認証情報が利用できる対象と操作を限定できる。
- 開発者ごとにトークンの発行・管理が必要になり、有効期限を設けた場合は更新が必要になる。
- 組織のポリシーによっては、トークンの利用に管理者の承認が必要になる。
