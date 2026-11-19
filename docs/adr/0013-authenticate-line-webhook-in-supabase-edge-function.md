# ADR 0013: LINE WebhookをSupabase Edge Functionで署名認証する

## Status

Accepted（2026-11-18）。設計・TODOと併せてユーザーが明示承認。

## Context

LINEからの正当な通知だけを受け付け、アプリへのログインを要求せず接続確認の返信を返したい。[Issue #58の要求](../env-58/requirements.md)はLINEの署名検証、秘密情報のサーバー管理、既存構成との整合を求めている。[ADR 0002](0002-use-supabase-for-backend-services.md)・[ADR 0003](0003-use-cloudflare-pages-for-frontend-hosting.md)ではサーバー処理をSupabaseへ置き、Cloudflare上のサーバー処理を初期構成に含めない。

LINEはSupabaseのJWT（ログイン状態などを示す認証トークン）を送らないため、通常のユーザー認証をこの入口に適用すると正当な通知も拒否される。2026-11-18に[Supabaseの外部Webhook認証](https://supabase.com/docs/guides/functions/auth#external-webhooks)と[LINEの署名検証](https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/)を確認した。前者は関数単位のJWT検証無効化と処理内での提供元署名検証、後者は未加工本文とチャネルシークレットによる署名検証を説明している。

## Decision

LINE受信の入口をSupabaseの `line-webhook` Edge Function（サーバーで動く小さな処理）に置く。この関数だけ `verify_jwt = false` とし、LINEの `x-line-signature` を未加工本文に対して検証してからイベント処理・返信を許可する。署名なし・不正署名は拒否し、Supabaseの公開キーやログインを認証の代用にしない。

## Consequences

既存のサーバー配置方針に沿って、アカウント紐付け前にLINEとの受信・返信を確認できる。一方、URLは匿名の呼出しにも到達可能になるため、関数が署名検証と秘密情報管理を担う。JWT検証の無効化を他の関数へ広げず、署名拒否時に返信が発生しないことを自動・公開環境の両方で確認する。

LINEの署名は通知元の正当性を確認するものであり、アプリの利用者との紐付けやDB操作権限は保証しない。後続の保存機能では別途認証・認可が必要になる。具体的な処理と検証は[設計書](../env-58/design.md)に置く。
