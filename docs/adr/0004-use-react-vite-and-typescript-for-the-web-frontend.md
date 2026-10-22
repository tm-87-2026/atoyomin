# ADR 0004: WebフロントエンドにReact・Vite・TypeScriptを採用する

## Status

Accepted — 2026-10-21

## Context

あとよみんは、ユーザーが保存したURLを一覧・整理・閲覧するWebアプリケーションとして提供する。画面を開発し、Cloudflare Pagesで配信するためのフロントエンド技術を決める必要がある。

候補は次のとおりである。

- React + Vite + TypeScript
- SvelteKit + TypeScript
- Vue + Vite + TypeScript
- Astro + ReactまたはSvelte
- Next.js + TypeScript

このアプリは、主にログイン済みユーザーが操作する画面で構成する。サーバーでHTMLを生成する機能よりも、SPA（画面遷移時にページ全体を読み直さず操作できるWebアプリケーション）としてシンプルに開発できることを優先する。

## Decision

UIライブラリにはReact、実装言語にはTypeScript、開発・ビルドツールにはViteを採用する。Viteは、開発中にアプリを動かす開発サーバーと、配信用ファイルを作るビルドツールである。

Reactは情報量が多く、問題が起きた際に調査しやすい。TypeScriptはデータの形を型として定義できるため、アプリの規模が大きくなった際の不整合を検出しやすい。ViteはReactによるSPAをシンプルに構成できる。

## Consequences

- UIを部品として分割して実装・再利用できる。
- 型を用いて、画面とSupabaseから受け取るデータの不整合を早期に検出できる。
- Node.jsを使ったフロントエンド開発環境が必要になる。
