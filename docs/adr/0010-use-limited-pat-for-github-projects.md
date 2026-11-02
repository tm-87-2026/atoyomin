# ADR 0010: GitHub Projectsには権限を限定した個人用トークンを利用する

## Status

Proposed — ADR 0007を補足する。

## Context

GitHub Projectsの操作をChatGPTの自作プラグインから開発コンテナ内のGitHub CLI（`gh`）へ移し、各メンバーが自分の認証で利用できるようにしたい。現在のプラグインは組織のGitHub Appで認証しており、再現に必要なAppのSecretを全員へ配布することはできない。

目的はAIによるコード変更を制限することではなく、認証情報が漏れた場合の悪用範囲を抑えることである。Git操作には[ADR 0007](0007-use-host-ssh-authentication-for-development.md)のSSH認証を継続する。一方、ProjectsのAPI操作にはトークンが必要になる。

保管先としてWSL上の平文ファイルとSupabase Vaultも検討した。ホストへのGitHub CLIの導入は許容し、平文ファイルを残さずに運用するため、Windowsの資格情報ストアを利用する。独自の連携コードはリポジトリ内で管理する。今回はProjectsの移行に限定し、GitとAPIの認証を統一するかは決めない。

組織のProjectsにfine-grained PATを利用する構成は、2026-11-02に[GitHubの公式ガイド](https://github.github.com/gh-aw/reference/auth-projects/)で確認した。Projectsと、関連する非公開リポジトリのIssue・PRへのアクセス権限は分けて検証する必要がある。

## Decision

Gitの取得・pushには、ホストで管理するパスフレーズ付きSSH鍵をDev Containersの標準agent転送で利用する。秘密鍵はコンテナへコピーしない。Gitの認証を`gh`へ移す`gh auth setup-git`は実行しない。

Projectsの操作には、各メンバーが発行するfine-grained PAT（対象と操作権限を細かく指定できる個人用アクセストークン）を利用する。対象の組織をResource ownerとし、Organization permissionsのProjectsをRead and writeに限定する。コードを書き換える権限は付与しない。関連する非公開リポジトリへの読み取り権限は、必要な操作を検証してから最小限だけ追加する。

PATは共有せず、有効期限を30〜90日とする。Windowsの`gh`で資格情報ストアへ保存し、保存元が`keyring`であることを確認する。平文保存へのフォールバックは利用しない。WSLからリポジトリ内の起動スクリプトでPATを取得し、コンテナ内の`gh`には環境変数`GH_TOKEN`で渡す。WSLとコンテナのファイルにはPATを保存しない。

## Consequences

- Windowsとコンテナに`gh`を導入する。各メンバーがPATを登録し、リポジトリ内のスクリプトでVS Codeを起動する必要がある。
- 平文ファイルによる保管は避けるが、実行時にトークンを渡したコンテナ内の処理はPATを読み取れる。
- PATの漏えい時にもコードを書き換える権限は与えないが、許可されたProjectsの改変リスクは残る。Projects権限は特定のProjectだけに限定されない。
- 各メンバーによるPATの期限管理・更新と、組織のポリシーに応じた承認が必要になる。
- SSH秘密鍵をコピーしなくても、コンテナは転送されたagentを利用してGit操作を実行できる。パスフレーズはpushごとの承認にはならない。
- Issue・PR自体の作成・編集権限はこのPATに含めず、必要になった場合に別途検討する。
