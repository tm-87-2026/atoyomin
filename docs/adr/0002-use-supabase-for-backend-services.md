# ADR 0002: バックエンドサービスにSupabaseを採用する

## Status

Accepted — 2026-10-21

## Context

このプロジェクトでは、限られた開発時間をクラウド基盤の設計・運用よりも、あとよみんの機能開発に使いたい。AWSのようなクラウドサービスは多くの機能を提供する一方、認証、データベース、ファイル保存、サーバー処理を組み合わせる設計と運用を自分たちで決める必要がある。今回はクラウド基盤そのものの学習を主目的にしないため、それらをまとめて提供するBaaS（Backend as a Service）を使う。

あとよみんには、ユーザーの認証、保存URLの管理、将来のLINE連携などのサーバー処理が必要になる。候補にはFirebase、Supabase、Cloudflare D1、Neonがある。Cloudflare D1はSQLite互換のデータベース、NeonはPostgreSQLデータベースを主に提供するサービスであり、認証などは別サービスとの組み合わせが必要になる。一方、SupabaseとFirebaseは認証を含む複数のバックエンド機能を提供する。

保存URL、ユーザー、読了状態などは互いに関係するデータである。これらをテーブルとテーブル間の関係として扱い、必要に応じて集計しやすいRDB（リレーショナルデータベース）を選びたい。Firebaseで主に使うCloud FirestoreはNoSQLのドキュメントデータベースである。

初期段階では無料枠で試せることも重視する。2026-10-21時点で、Supabaseの無料枠にはPostgreSQL、認証、月50万回のEdge Functions実行が含まれる。Firebaseの無料SparkプランにもFirestoreの無料枠はあるが、Cloud Functionsを使うには課金アカウントを紐付けたBlazeプランが必要になる。

各サービスの現在の提供範囲と料金は、[Supabase](https://supabase.com/docs)、[Supabase料金](https://supabase.com/pricing)、[Firebase Cloud Firestore](https://firebase.google.com/docs/firestore/data-model)、[Firebase料金プラン](https://firebase.google.com/docs/projects/billing/firebase-pricing-plans)、[Cloudflare D1](https://developers.cloudflare.com/d1/best-practices/query-d1/)の公式ドキュメントで確認した。

## Decision

バックエンドサービスにはSupabaseを採用する。

SupabaseはPostgreSQLを提供し、認証、ファイル保存、リアルタイム通信、Edge Functions（小さなサーバー処理）も同じサービスで利用できる。RDBを利用でき、必要なバックエンド機能をまとめて導入できることに加え、初期開発で必要なサーバー処理を無料枠から試せることを選定理由とする。

## Consequences

- 初期開発では、認証・データベース・将来のサーバー処理を別々のサービスとして設計・運用しなくてよい。
- データベースはPostgreSQLのテーブルと関係を前提に設計する。
- Supabaseの機能、料金、提供条件に依存する。料金は利用量と料金体系の変更に応じて継続して確認する。
- ブラウザから直接データを扱う場合は、RLS（行ごとのデータアクセス権限）を設計・設定する必要がある。

