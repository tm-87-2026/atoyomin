# ADR 0003: フロントエンドの配信にCloudflare Pagesを採用する

## Status

Accepted — 2026-10-21

## Context

Reactで作成したWebアプリを配信するサービスを決める必要がある。候補はGitHub Pages、Vercel、Netlify、Cloudflare Pagesである。

開発は各自のローカル環境で行い、本番環境とは別に開発用の画面を確認できるようにしたい。Cloudflare PagesのPreview Deployment（ブランチやプルリクエストの画面を、本番公開前に専用URLで確認できる仕組み）を使うと、ローカル・開発用・本番用という段階を持てる。これは採用の必須条件ではないが、3人での開発において有用である。Cloudflare Pagesでは、GitHubのプルリクエストごとにプレビューURLを作成でき、無料枠でも月500回のビルドと無制限の有効プレビューを利用できる。

Netlifyの無料プランは月300クレジットが上限であり、上限に達すると追加利用できない。当時は必要なクレジット量を見積もれておらず、300クレジットでは不足する可能性があると感じた。Cloudflare Pagesは無料枠で月500回までビルドでき、上限が開発中の操作と直接対応していて把握しやすい。そのため、Cloudflare Pagesを選んだ。Supabaseをバックエンドに採用するため、Cloudflare上のサーバー処理は初期段階では必要としない。

現在の機能と上限は、[Cloudflare Pages](https://developers.cloudflare.com/pages/)、[Cloudflare Pagesの制限](https://developers.cloudflare.com/pages/platform/limits/)、[Preview Deployment](https://developers.cloudflare.com/pages/configuration/preview-deployments/)、[GitHub Pagesの利用制限](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)、[Netlifyの料金体系](https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/)で確認した。

## Decision

フロントエンドの配信にはCloudflare Pagesを採用する。GitHubリポジトリと連携し、mainブランチを本番環境、プルリクエストをプレビュー環境として自動デプロイする。

Cloudflare WorkersおよびPages Functionsは初期構成に含めない。サーバー処理はSupabaseで実装する。

## Consequences

- ローカル・開発用・本番用の段階を使い分けて画面を確認できる。
- Cloudflare Pagesの無料枠では月500ビルドが上限となる。
- Preview Deploymentは画面を確認するための環境であり、Supabaseのデータベースまで完全に分離するものではない。
- サーバー処理が必要になった場合、まずSupabaseの機能で実現できるか検討する。
- Cloudflareは新規アプリケーションにWorkersを主軸として案内しているため、Pagesの提供方針や必要なサーバー処理が変わった場合はこの決定を見直す。
