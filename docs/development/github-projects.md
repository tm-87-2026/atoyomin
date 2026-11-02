# Dev ContainerからのGitHub Projects操作

Projectsはコンテナ内のGitHub CLI（`gh`）と各メンバーのfine-grained PAT（対象と操作権限を指定できる個人用アクセストークン）で操作する。PATはWindowsの資格情報ストアに保管し、WSLとコンテナのファイルには保存しない。判断案は[ADR 0010](../adr/0010-use-limited-pat-for-github-projects.md)を参照する。

Gitの取得・pushには既存の[SSH認証](github-authentication.md)を利用する。`gh auth setup-git`は実行しない。Issue・PR自体の作成・編集は今回の移行範囲に含めない。

## 初回の準備

Windowsに[GitHub CLI](https://cli.github.com/)をインストールする。WSL側への`gh`導入や、リポジトリ外への独自スクリプトの配置は不要である。

組織の管理者はfine-grained PATの利用可否・承認要否・有効期限のポリシーを確認する。各メンバーはGitHubのSettings → Developer settings → Personal access tokens → Fine-grained tokensからPATを発行する。

- Resource owner: `tm-87-2026`。
- Organization permissions: ProjectsのRead and write。
- Repository access: 最初はPublic repositoriesにとどめ、Repository permissionsは追加しない。非公開リポジトリのIssue・PRを扱う際は、対象を`atoyomin`に絞り、必要な読み取り権限だけを検証して追加する。Contentsの書き込み権限は付与しない。
- 有効期限: 組織のポリシーの範囲で30〜90日。PATは共有しない。

Projects権限は特定のProjectだけに限定されない。組織の承認が必要な場合は承認後に接続確認する。

WSLホストのターミナルでリポジトリへ移動し、次を実行する。PATは非表示の入力欄へ貼り付ける。コマンド引数、シェル履歴、`.env`には書かない。

```sh
powershell.exe -NoProfile -File "$(wslpath -w "$PWD/.devcontainer/windows-projects-token.ps1")" -Mode Register
```

登録にはWindowsの`gh auth login --with-token`を使う。既に同じGitHubアカウントでWindowsの`gh`を利用している場合は、その認証をProjects用PATで更新するため、従来の広い権限を前提とした操作には影響がある。

`gh`は資格情報ストアが利用できない場合に平文保存へフォールバックすることがある。このスクリプトは登録後に保存元が`keyring`かを確認し、それ以外では失敗する。失敗した場合はWindowsの`gh auth status`で保存先を確認し、平文保存されていれば`gh auth logout --hostname github.com --user <自分のGitHubユーザー名>`で削除し、GitHub上でもPATを失効する。平文フォールバックを起こさない環境で登録し直す。[GitHub CLIの保存仕様](https://cli.github.com/manual/gh_auth_login)

## コンテナの起動

未保存ファイルを保存して、VS Codeの全ウィンドウを閉じる。既存のVS Codeプロセスを再利用すると古い環境変数が使われる場合がある。WSLホストのリポジトリで次を実行する。

```sh
bash .devcontainer/open-with-projects-token.sh
```

スクリプトはWindowsの`gh`の有効なアカウントを確認し、資格情報ストアのfine-grained PATだけを取得してVS Codeの環境変数`GH_TOKEN`に渡す。Windows・WSL間の引き継ぎには、その起動プロセス内で`WSLENV`も設定する。ユーザーの永続的な環境変数やログイン設定は変更しない。`Read`モードのPowerShellスクリプトはトークンを呼び出し元へ返すため、ターミナルから直接実行しない。`bash -x`などのデバッグ出力も使用しない。

初回は **Dev Containers: Rebuild and Reopen in Container** を実行する。`github-cli` Featureで`gh`を導入し、`remoteEnv`でホストの`GH_TOKEN`を渡す。以後もProjectsを使う場合はこの起動スクリプトを利用する。Windowsのスタートメニューから開く場合や、通常の`code .`だけではPATの供給を保証しない。

PATはファイルに保存しないが、VS Codeとコンテナのプロセスの環境に保持される。コンテナ内の処理はPATを読み取れるため、必要な権限だけを付与する。`printenv`や`gh auth token`などでトークンを表示・記録しない。

## 接続と操作の確認

コンテナで次を実行する。

```sh
test -n "${GH_TOKEN:-}" && echo 'GH_TOKENは設定されています'
gh --version
gh project list --owner tm-87-2026
git remote get-url origin
```

Project一覧を取得でき、Git remoteが従来のSSH形式であることを確認する。一覧の取得だけでは移行完了とせず、対象のProjectでフィールド・項目の取得、既存Issueの追加、Statusの更新を確認する。書き込み確認は専用の確認用項目で行う。

```sh
gh project field-list <Project番号> --owner tm-87-2026 --format json
gh project view <Project番号> --owner tm-87-2026 --format json
gh project item-list <Project番号> --owner tm-87-2026 --format json
gh project item-add <Project番号> --owner tm-87-2026 --url <IssueのURL>
gh project item-edit --id <項目ID> --project-id <ProjectのID> --field-id <StatusフィールドID> --single-select-option-id <選択肢ID>
```

IDやオプションは一覧のJSON出力と各コマンドの`--help`で確認する。コマンドが足りない場合は`gh api graphql`で補うが、APIを変えてもPATの権限は増えない。非公開Issueの取得・追加が失敗する場合は、組織の承認と、対象リポジトリのIssuesまたはPull requestsの読み取り権限を確認する。権限を一律に広げない。

必要な操作を確認するまでは既存プラグインを削除しない。GitHub Appは他の利用者・用途を確認してから別途整理する。

## 更新と解除

期限前に新しいPATを発行し、同じRegister手順で更新する。その後VS Codeを全て終了し、起動スクリプトから開き直してコンテナへ再接続する。古いPATは失効する。`gh auth refresh`で権限を広げたり、コンテナ内で`gh auth login`を実行したりしない。

利用をやめる場合はGitHub上でPATを失効し、Windowsの`gh auth logout --hostname github.com --user <自分のGitHubユーザー名>`で保存情報を削除する。既に起動中のVS Codeとコンテナも終了する。

Windowsの資格情報ストア、WSLからの受け渡し、実際のProjects操作はホストでの検証が必要である。設定ファイルの検査や代替コマンドによるテストだけでは、これらの成功を保証しない。
