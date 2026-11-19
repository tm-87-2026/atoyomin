# アプリケーションのアーキテクチャ

## 目的と位置付け

あとよみんの実装・レビューで参照する初期設計方針をまとめる。Supabaseとの接続を確認する最小アプリケーションは実装済みである。本書は今後の機能開発に適用する方針を定める。

開発は3人で業務時間外に行い、2027年3月19日までにプロダクトバックログのStoryをすべて実装することを目指す。Supabaseは全員未経験であり、React・TypeScriptの経験にも差がある。コードの役割と変更の影響をチームで理解し、一定の品質で開発できることを重視する。

初めから特定のアーキテクチャに固定せず、[設計規約](conventions/design.md)と本書に沿って実装を始め、実際のコードをもとに構成を見直す。判断の背景は[ADR 0011](adr/0011-evolve-architecture-through-implementation.md)に記録する。

## 全体構成と責務

採用技術は[ADR 0002](adr/0002-use-supabase-for-backend-services.md)、[ADR 0003](adr/0003-use-cloudflare-pages-for-frontend-hosting.md)、[ADR 0004](adr/0004-use-react-vite-and-typescript-for-the-web-frontend.md)に従う。

| 構成要素 | 役割 |
| --- | --- |
| React・Vite・TypeScript | ブラウザーで動くSPAとして、画面表示とユーザー操作を扱う |
| Cloudflare Pages | フロントエンドのビルド成果物を配信する |
| Supabase Auth | ユーザー認証を担う |
| SupabaseのPostgreSQL・データAPI | データの保存・取得とアクセス制御を担う |
| Supabase上のサーバー処理 | LINEやLLMなど外部サービスとの連携を扱う。具体的な実装構成は未決定 |

Cloudflare Workers・Pages Functionsは初期構成に含めない。サーバー処理はSupabaseで実装する。

フロントエンドとバックエンドはAPIを通じて連携する。ブラウザーからデータAPIを直接利用する場合は、DB側のRLS（行ごとのアクセス制御）で利用者のデータを保護する。画面で表示を制限するだけではアクセス制御にならない。

LINEからの保存、記事の一覧・検索・詳細、要約、通知、アクティビティ分析を設計の対象とする。各処理のAPI、データ構造、LINE利用者とアプリ利用者の対応付けは、それぞれの機能設計で具体化する。

## 領域別の設計方針

- [フロントエンド](architecture/frontend.md)：画面の組み立て方、state・props、コードの配置と依存関係。
- [バックエンド](architecture/backend.md)：Supabaseを前提とする初期方針と、実装を通じて具体化する事項。

## 見直しと文書の役割

最初の動く機能ができた段階で、処理を追えるか、変更箇所を判断できるか、レビューで責務を説明できるかをチームで確認する。理解・変更しにくい箇所があれば、具体的なコードをもとにリファクタリングと配置ルールを検討し、本書を更新する。重要な判断はADRに残す。

共通の設計原則は[設計規約](conventions/design.md)、命名・型・書式などは[コーディング規約](conventions/coding.md)、本アプリ固有の構成・適用方針は本書とFE・BEの文書、選択の背景と理由はADRで管理する。
