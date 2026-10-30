# あとよみん（atoyomin）

あとで読みたいURLを保存し、一覧・整理・閲覧するWebアプリケーションです。
ユーザー認証、保存URLの管理、読了状態の管理を想定し、将来的にはLINE連携も検討しています。

## 現在の状況

技術選定と開発環境の整備を進めています。アプリケーション本体はまだ実装していません。
`package.json`や依存関係のlockfile、Supabaseの設定、デプロイ設定は未作成です。

## 採用技術

| 用途 | 技術 |
| --- | --- |
| フロントエンド | React・Vite・TypeScript |
| バックエンド | Supabase（PostgreSQL・認証・必要に応じてEdge Functionsなど） |
| フロントエンドの配信 | Cloudflare Pages |
| パッケージ管理 | pnpm |
| 標準開発環境 | Dev Containers |

採用理由と運用方針は[設計上の意思決定](#設計上の意思決定)に記録しています。

## 開発環境

開発ツールはDev Container内で利用します。Node.jsやpnpmをホストOSへ直接インストールする必要はありません。

### 必要なもの

- Git
- Docker互換ランタイム（Docker Desktopなど）
- Visual Studio CodeとDev Containers拡張機能
- Windowsの場合はWSL2

### 起動手順

1. リポジトリをクローンします。WindowsではWSL2内に配置します。
2. Docker互換ランタイムを起動します。
3. リポジトリをVS Codeで開きます。
4. コマンドパレットから`Dev Containers: Reopen in Container`を実行します。
5. コンテナ内のターミナルで、開発ツールを確認します。

   ```sh
   node --version
   pnpm --version
   ```

[Dockerfile](.devcontainer/Dockerfile)ではNode.js 22とpnpm 10.12.4を指定しています。
[Dev Container設定](.devcontainer/devcontainer.json)では、Vite開発サーバー用のポート5173を転送し、ESLint・Prettier・CodexのVS Code拡張機能を導入します。

アプリケーションの雛形が未作成のため、現時点では依存関係のインストール、開発サーバーの起動、ビルド、テストのコマンドはありません。実装時にこのREADMEへ追記します。

## リポジトリ構成

```text
.devcontainer/  開発コンテナの定義
.agents/skills/ 開発作業で利用するスキル
docs/adr/      設計・技術選定の意思決定記録
AGENTS.md      リポジトリ共通の作業規約
README.md      プロジェクトの概要と開発環境の案内
```

## 設計上の意思決定

- [ADR 0001: Dev Containersを標準開発環境にする](docs/adr/0001-dev-containers-as-standard-development-environment.md)
- [ADR 0002: バックエンドサービスにSupabaseを採用する](docs/adr/0002-use-supabase-for-backend-services.md)
- [ADR 0003: フロントエンドの配信にCloudflare Pagesを採用する](docs/adr/0003-use-cloudflare-pages-for-frontend-hosting.md)
- [ADR 0004: WebフロントエンドにReact・Vite・TypeScriptを採用する](docs/adr/0004-use-react-vite-and-typescript-for-the-web-frontend.md)
- [ADR 0005: JavaScriptの依存関係をpnpmで管理する](docs/adr/0005-manage-javascript-dependencies-with-pnpm.md)

## 開発時の規約

変更前に[AGENTS.md](AGENTS.md)を確認してください。ブランチ運用、コミット、ドキュメントの管理方針を定めています。
