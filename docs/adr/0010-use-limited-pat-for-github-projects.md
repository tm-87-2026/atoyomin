# ADR 0010: GitHub Projectsには権限を限定した個人用トークンを利用する

## Status

Proposed — ADR 0007を補足する。

## Context

GitHub Projectsの操作をChatGPTの自作プラグインから開発コンテナ内のGitHub CLI（`gh`）へ移したい。現在は組織のGitHub Appで認証しており、再現に必要なAppのSecretを全員へ配布することはできない。各メンバーが自分の認証で利用し、漏えい時の悪用範囲を抑える必要がある。

チームにはWindows＋WSLとmacOSの利用者がいる。両環境で初回導入を小さく始め、VS Codeの通常の起動・再接続を維持し、独自コードはリポジトリ内で管理したい。今回の対象はProjectsのみで、GitとAPIの認証統一は別途検討する。

組織のProjectsにfine-grained PATを利用する構成は、2026-11-02に[GitHubの公式ガイド](https://github.github.com/gh-aw/reference/auth-projects/)で確認した。関連する非公開リポジトリのIssue・PRへのアクセス権限は、Projectsの権限とは分けて検証する必要がある。

## Decision

各メンバーが発行するfine-grained PAT（対象と操作権限を細かく指定できる個人用アクセストークン）を利用する。対象の組織をResource ownerとし、Organization permissionsのProjectsをRead and writeに限定する。コードを書き換える権限は付与せず、関連する非公開リポジトリへの読み取り権限は、検証して必要なものだけ追加する。PATは共有しない。

PATはWSLまたはmacOSのホストのリポジトリ外に平文保存し、ファイル権限を`600`にする。専用の保存先ディレクトリをコンテナへ読み取り専用でマウントする。リポジトリ内のProjects用スクリプトが実行時に読み、起動する`gh`プロセスだけに環境変数`GH_TOKEN`で渡す。

平文保存のリスクを受け入れ、OS固有の連携と日常の起動手順の変更を避けることを優先する。代替案は次の理由で見送る。

- **OSの資格情報ストア**：平文ファイルを避けられるが、Windows＋WSLとmacOSそれぞれで、ホストの保管庫からコンテナへ取得する連携と検証が必要になる。
- **Supabase Vault**：暗号化保管できるが、取得時の認証とメンバーごとのアクセス制御を整備・保守する必要がある。初回導入では負担が大きく、OSの保管庫とともに将来の改善候補とする。
- **専用スクリプトからのVS Code起動**：環境変数を供給できるが、Projects利用時の起動方法を制約し、起動済みプロセスへPAT更新が自動反映されない。

Gitの取得・pushは[ADR 0007](0007-use-host-ssh-authentication-for-development.md)のSSH認証を維持する。秘密鍵はコンテナへコピーせず、`gh auth setup-git`は実行しない。Issue・PR自体の作成・編集権限は今回のPATに含めない。

## Consequences

- ホストへの`gh`導入や専用のVS Code起動手順は不要になる。Projects操作はリポジトリ内のスクリプト経由で行う。
- ホストにPATの平文ファイルが残り、ホストの同じユーザー権限の処理とコンテナ内の処理は読み取れる。読み取り専用マウントは書き換えを防ぐが、持ち出しは防がない。
- PATにコードを書き換える権限は含まれないが、漏えい時には許可されたProjectsを改変され得る。Projects権限は特定のProjectだけには限定されない。
- 各メンバーによるPATの管理・更新と、組織のポリシーに応じた承認が必要になる。ホストでファイルを差し替えた後は、次のコマンド実行で読み直せる。
