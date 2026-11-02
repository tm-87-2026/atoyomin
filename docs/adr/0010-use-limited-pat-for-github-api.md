# ADR 0010: SSHで扱えないGitHub操作には権限を限定した個人用トークンを利用する

## Status

Proposed — ADR 0007の対象外だったGitHub API操作を扱う。

## Context

GitHubのIssue・PR・Projectsの操作をChatGPTの自作プラグインから開発コンテナ内のGitHub CLI（`gh`）へ移したい。現在は組織のGitHub Appで認証しており、再現に必要なAppのSecretを全員へ配布することはできない。各メンバーが自分の認証で利用し、漏えい時の悪用範囲を抑える必要がある。

チームにはWindows＋WSLとmacOSの利用者がいる。通常のVS Code起動・再接続を維持し、独自コードはリポジトリ内で管理したい。SSHで扱えないAPI操作を今回の対象とし、Gitの認証もPATに統一するかは判断しない。

fine-grained PATによる[Issue](https://docs.github.com/en/rest/issues/issues#create-an-issue)・[PR](https://docs.github.com/en/rest/pulls/pulls#create-a-pull-request)の作成と、[組織のProjects操作](https://github.github.com/gh-aw/reference/auth-projects/)の権限は、2026-11-02に公式情報で確認した。

## Decision

各メンバーが発行するfine-grained PAT（対象と操作権限を細かく指定できる個人用アクセストークン）を利用する。Resource ownerは対象の組織とし、リポジトリは`atoyomin`に限定する。Organization permissionsのProjects、Repository permissionsのIssues・Pull requestsにRead and writeを付与し、コードのpush用権限は追加しない。PATは共有しない。

PATはリポジトリ直下の`.env.github`に平文保存し、`.gitignore`で追跡対象から除外する。ファイル権限は`600`とする。リポジトリ内の実行スクリプトが実行時にファイルを読み、起動する`gh`だけにPATを渡す。

保存先はセキュリティ上の利点と導入・実装コストを比較し、初回は平文ファイルを採用する。

- **OSの保管庫**：平文より保存時の保護に優れるが、WindowsではWindows・WSL・Dev Containerの3層をまたぐPAT受け渡しが必要になる。macOSも含めて利用するための共通インターフェース設計と、両環境への実装・検証コストがある。
- **Supabase Vault**：暗号化保管できるが、現時点ではインフラがなく、Supabase環境のプロビジョニングから必要になる。加えてPAT取得の認証とメンバーごとのアクセス制御も整備する必要があり、初回導入には重い。

Gitの取得・pushには[ADR 0007](0007-use-host-ssh-authentication-for-development.md)のSSH設定を利用し、Git用の認証設定は変更しない。

## Consequences

- Windows＋WSL・macOSで同じenvファイルと実行スクリプトを使える。ホストへの`gh`導入や専用のVS Code起動手順は不要になる。
- ファイルへアクセスできるホスト・コンテナ内の処理はPATを読み取り・書き換えできる。`.gitignore`でも`git add -f`やフォルダごとのコピーによる漏えいは防げない。
- PATが漏えいすると、許可されたIssue・PR・Projectsを改変され得る。Projects権限は特定のProjectだけには限定されない。
- 各メンバーによるPATの管理・更新と、組織のポリシーに応じた承認が必要になる。更新したPATは次のコマンド実行から読み直す。
