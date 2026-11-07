# SupabaseとCloudflare Pagesのセットアップ

Issue #47の最小アプリケーションを、ローカル環境、Supabase、Cloudflare Pagesで再現する手順です。

## 構成

ReactとViteでビルドした静的ファイルをCloudflare Pagesから配信します。ブラウザはSupabase Data APIへ直接接続し、`public.app_status`の接続確認用レコードだけを読み取ります。

`app_status`はRLSを有効にし、`anon`と`authenticated`へ`SELECT`だけを明示的に許可します。書込み権限は付与しません。認証、ユーザー固有のデータ、URL保存機能はこの最小構成に含めません。

## ローカルでアプリを起動する

1. 依存関係をlockfileどおりに導入します。

   ```sh
   pnpm install --frozen-lockfile
   ```

2. 環境変数のテンプレートをコピーします。

   ```sh
   cp .env.example .env.local
   ```

3. `.env.local`にSupabase Dashboardの値を設定します。

   ```dotenv
   VITE_SUPABASE_URL=https://<project-ref>.supabase.co
   VITE_SUPABASE_PUBLISHABLE_KEY=<publishable-key>
   ```

   Publishable keyはブラウザで使う公開前提の値です。Secret keyや`service_role` keyは設定・共有しません。

4. 開発サーバーを起動し、表示されたURLを開きます。

   ```sh
   pnpm dev
   ```

## データベースを準備する

Supabaseのスキーマ変更はDashboardで直接変更せず、`supabase/migrations/`のSQLとして管理します。

1. Supabaseへログインし、作成済みプロジェクトをリンクします。

   ```sh
   pnpm supabase login
   pnpm supabase link --project-ref <project-ref>
   ```

2. マイグレーションをリモートへ適用します。

   ```sh
   pnpm supabase db push --remote
   ```

3. アプリを起動し、「Supabaseとの接続を確認できました。」と表示されることを確認します。

ローカルのSupabaseスタックを使う場合はDocker互換ランタイムを起動してから`pnpm supabase start`を実行します。マイグレーションを最初から検証するには`pnpm supabase db reset`を使います。

## Cloudflare Pagesへデプロイする

アプリを含む`main`ブランチをGitHubへpushしてから、Cloudflare DashboardでPagesプロジェクトを作成します。

| 項目 | 値 |
| --- | --- |
| Git repository | `tm-87-2026/atoyomin` |
| Production branch | `main` |
| Framework preset | React (Vite) |
| Build command | `pnpm run build` |
| Build output directory | `dist` |

Cloudflare Workers & Pages GitHub Appのリポジトリアクセスは、`tm-87-2026/atoyomin`だけに限定します。

PagesプロジェクトのEnvironment variablesで、ProductionとPreviewの両方に次を設定します。

| 変数 | 値 |
| --- | --- |
| `VITE_SUPABASE_URL` | Supabase Project URL |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Supabase Publishable key |

これらはViteによりブラウザ用のビルドへ埋め込まれます。Secret keyや`service_role` keyをPagesの環境変数に設定してはいけません。

デプロイ後、PagesのURLを開き、接続確認メッセージが表示されることを確認します。

## 今後の運用

`main`へのマージでマイグレーションを自動適用する場合は、`supabase/`をGitHubへコミットした後にSupabaseのGitHub integrationを有効にします。現在は、マイグレーション適用を担当者が明示的に実行します。
