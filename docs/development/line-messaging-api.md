# LINEの受信・確認返信を準備する

記事保存の実装に先立ち、LINE公式アカウントとの接続を確認する手順です。`line-webhook`は署名検証後、1対1トークのテキストに「メッセージを受信しました。接続確認用の返信です。記事は保存していません。」と返信します。アプリへのログインは不要です。

2026-11-18、非本番Supabaseへのデプロイ、Webhook切替、LINE Verify成功、1対1トークの固定確認返信到達をユーザーが確認しました。公開URLへの署名なし・架空署名のPOSTはいずれも401でした。正常署名の公開受信はLINE Verify成功を根拠とし、下記の独自補助スクリプトへ実シークレットを入力する試験は未実施です。再配信オフと、LINE秘密情報をSupabase Secretsだけに登録したこともユーザーが確認済みです。旧設定の控えなどの検証の限界と、確認担当ごとの根拠は[TODO](../env-58/todo.md#公開環境の確認結果2026-11-18)を参照してください。以下は再現用の手順です。

## 設定前に確認する

ユーザーが次の事項を確認し、秘密を含まない判定だけを担当者へ伝えます。未確認、権限不足、既存用途との競合があれば外部設定を止めて相談します。別環境の新規作成や本番利用へ自動的に切り替えません。

1. LINE Official Account Managerで対象アカウントのMessaging API有効状態を確認します。既存チャネルがあれば再利用できること、LINE Developers Consoleで公式アカウント・プロバイダーとの対応とAdmin権限を確認します。未有効の場合は有効化前にプロバイダーの所属を確かめます。
2. 既存Webhook URL、Use webhook、応答メッセージ・あいさつ設定と利用目的を確認します。既存連携を上書きせず、変更の影響と復旧方法を相談します。通常利用者への影響が避けられないアカウントは使いません。自動応答と確認返信が混在しない設定へ変更可能かも確認します。
3. Webhook再配信は今回無効にします。既に有効なら、無効化の可否を先に相談します。従前設定の値はユーザーが手元に保持し、記録へ転記しません。
4. Supabase Dashboardで対象Project URLの`project-ref`（プロジェクトを識別する文字列）を確認し、非本番専用で本番データ・本番用秘密情報を使わないことを確認します。共有環境では`line-webhook`関数名とLINE用変数名の競合を確認します。
5. ユーザーがSecrets編集・関数デプロイの権限を持つことを確認します。リモートSecretsの作成・削除にはOwner/Administrator権限が必要です。設定・デプロイ・接続確認の担当を確定します。

## 他のメンバーが既存LINE連携へ参加する

同じ公式アカウントをチームで管理する場合、参加者ごとの新規LINE公式アカウントは不要です。各自のLINE Developersアカウントへ、既存Messaging APIチャネルの権限を付けます。

1. 参加者は自分用のアカウントでLINE Developers Consoleにログインし、未登録なら開発者登録を済ませます。
2. 既存チャネルのAdminが、対象チャネルの「Roles」→「Invite by email」で参加者のメールアドレスを入力し、Webhookや秘密情報を設定する担当には「Admin」を選んで招待します。
3. 参加者は招待メールを開き、権限を付けたい自分の開発者アカウントでログインして招待を受諾します。受諾時にログインしているアカウントへ権限が付くため、別アカウントでログインしていないか確認します。
4. 対象チャネルとMessaging API設定を開けることを確認します。既存Webhookは共有設定なので、各自のローカルURLなどへ無断で変更しません。

プロバイダー（チャネルをまとめる管理単位）の権限とチャネル権限は独立しています。プロバイダーAdminだけでは既存チャネルへのアクセスは付かず、チャネルへの直接招待にはプロバイダー権限は必須ではありません。[LINE Developersの権限管理](https://developers.line.biz/en/docs/line-developers-console/managing-roles/)

応答設定などLINE Official Account Managerでの操作も担当する場合は、その管理画面の権限を別途付けます。既存管理者が「設定」→「権限管理」→「メンバーの追加」で管理者権限を選び、認証用URLを発行して本人へ共有します。参加者は自分のアカウントで受諾します。URLは1人用で発行から24時間で失効するため、使い回しません。[Official Account Managerの権限設定](https://www.lycbiz.com/jp/manual/OfficialAccountManager/account-settings_permission/)

各自が独立した検証環境を持つ場合は、検証用公式アカウント・別チャネルと別の接続先を用意する運用を別途決めます。共有チャネルのWebhookを個人用環境へ切り替えると、共有先へ通知されなくなります。

## ローカルで検証する

Denoは開発コンテナに含まれません。[インストール手順](https://docs.deno.com/runtime/getting_started/installation/)を参照してDeno 2.5.6を別途用意し、`deno --version`で確認します。関数と補助スクリプトはDenoでチェックし、ブラウザ向けESLintの範囲から分離しています。外部パッケージやLINE SDKは使いません。

```sh
pnpm install --frozen-lockfile
deno task --config supabase/functions/line-webhook/deno.json test
deno task --config supabase/functions/line-webhook/deno.json check
deno task --config supabase/functions/line-webhook/deno.json lint
deno task --config supabase/functions/line-webhook/deno.json fmt
pnpm exec tsc -b
pnpm lint
pnpm build
```

テストは架空シークレット・トークンと通信モックだけを使います。実値は不要です。

今回はローカルDocker環境の整備が難航したため、2026-11-18の合意により、ローカルSupabase起動・HTTP経路は未実施として記録します。上記チェック後、設定前条件を満たして開発用Supabaseへデプロイし、公開URLの署名試験・Verify・実LINE受信返信を直接確認します。Docker互換性の成功は主張しません。

以下はDockerを利用できる別環境でローカルSupabaseを確認する場合の手順です。今回のデプロイの前提ではありません。開発コンテナにはDockerデーモンを設定していません。

```sh
pnpm supabase start
cp supabase/functions/.env.example supabase/functions/.env.local
```

ローカル用ファイルには`LINE_CHANNEL_SECRET=fictional-secret`と`LINE_CHANNEL_ACCESS_TOKEN=fictional-token`を設定します。Gitで除外されることを確認し、実値へ置き換えません。

```sh
git check-ignore supabase/functions/.env.local
pnpm supabase functions serve line-webhook --env-file supabase/functions/.env.local
```

別のターミナルから署名試験を実施します。非表示入力には架空値`fictional-secret`を入力し、順番に200、401、401を期待します。JWT無効化は`supabase/config.toml`の当該関数だけに設定しているため、全関数向けの`--no-verify-jwt`は付けません。

```sh
bash tools/line/check-webhook.sh http://127.0.0.1:54321/functions/v1/line-webhook
```

この空events試験はLINEへ返信しません。実LINEへの送信テストには架空トークンを使いません。終了後は`pnpm supabase stop`でローカルスタックを止めます。

## 秘密情報を登録して公開する

設定前確認を満たし、ローカルチェックの結果と未実施事項を確認した後に行います。実値の取得・登録はユーザー自身が担当し、会話・コマンド引数・Git・Cloudflare Pages・`VITE_`環境変数へ渡しません。

登録するサーバー専用の変数と取得元を次に示します。登録先はいずれも対象Supabase DashboardのEdge Function Secretsです。

| 変数 | LINE Developers Consoleの取得元 |
| --- | --- |
| `LINE_CHANNEL_SECRET` | 対象チャネルのBasic settings |
| `LINE_CHANNEL_ACCESS_TOKEN` | 同チャネルのMessaging API設定 |

既存の利用可能なトークンを優先します。新規発行が必要な非本番チャネルでは長期トークンを使えますが、有効期限がなく手動での失効・更新が必要です。既存トークンやシークレットを再発行すると連携に影響するため、確認なく再発行しません。

1. ユーザーがDashboardで2変数を登録し、値を表示・共有せず登録済みであることだけ確認します。Pagesとブラウザ用設定にLINE秘密情報がないことも本人が確認します。
2. 担当者がSupabase CLIへログインします。次の`<project-ref>`をDashboardで確認した非本番対象へ置き換え、対象と関数設定を再照合して当該関数だけをデプロイします。`--use-api`はDocker不要のサーバー側バンドルを使います。固定CLI 3.0.0の`functions deploy --help`で対象指定が`--remote=<ref>`であることを確認しています。既存DBのマイグレーション適用はこの手順に含めません。

   ```sh
   pnpm supabase login
   pnpm supabase functions deploy line-webhook --remote=<project-ref> --use-api
   ```

3. LINE Developers Consoleの対象チャネルでWebhook URLを`https://<project-ref>.supabase.co/functions/v1/line-webhook`へ設定します。SupabaseのキーやJWTは渡しません。
4. Verifyを実行し成功を確認します。空の`events`配列に対して200を返すことを期待します。失敗したら有効化へ進まず、下の障害対応を行います。
5. Use webhookを有効にし、再配信が無効であること、自動応答との混在を避ける設定を再確認します。

## 公開URLと実トークを確認する

公開署名試験はユーザー端末の対話ターミナルで実行します。Denoとbashが必要です。`set -x`や入力記録を有効にせず、次のコマンドへURLだけを渡します。チャネルシークレットを非表示プロンプトへ入力し、アクセストークンやSupabase認証情報は入力しません。

```sh
bash tools/line/check-webhook.sh https://<project-ref>.supabase.co/functions/v1/line-webhook
```

スクリプトは空eventsに対する正常署名、誤署名、署名なしの順にPOSTし、HTTPステータスだけを表示します。期待値は200、401、401です。通信・入力エラーは固定の`probe_failed`で終了し、応答本文や秘密を出力しません。期待値不一致では終了コードが1になります。

実トークではアプリへログインしていない担当者が公式アカウントを友だち追加し、1対1トークで個人情報を含まない接続確認用テキストを送信します。上記固定文が届き、記事保存を示さないことを確認します。画像・スタンプ・グループ・複数人トークは返信対象外です。自動応答との混在がないことも確認します。

結果には日時、非本番環境の識別名、シナリオ、期待値に対する判定、確認担当だけを記録します。トーク本文、LINEユーザーID、署名、replyToken、秘密値、スクリーンショット、生のプラットフォームログは残しません。

## 失敗したときに戻す

1. 想定外の返信や既存連携への影響があればUse webhookを無効にして通知を止めます。以前の連携があった場合は、ユーザーが保持した従前のWebhook URLとUse webhook・応答設定・再配信設定へ戻します。
2. 401は署名とチャネルの対応、500は対象Secretsの登録有無、502はReply API・トークン・タイムアウトを確認します。アプリのログは`reply_failed`という分類とHTTPステータスに限定しています。レスポンス本文や例外全文を追加出力しません。Supabase側の401と関数の401は設定と固定応答を本人の端末で確認し、公開記録には結果だけ残します。
3. 返信の待機上限は5秒で、自動再試行はしません。タイムアウト時はLINEが既に受信している可能性があるため、replyTokenを再利用せず原因確認後に新しいテキストで試します。重複排除や到達の一度限り保証はありません。
4. 関数変更を戻す場合は既知の正常版の当該関数だけを同じ非本番project-refへ再デプロイします。今回新設した関数・Secretsの削除が必要なら、他の用途がないことを確認した担当者がDashboardで行います。既存共有SecretsやDBは削除しません。
5. 秘密漏えいが疑われる場合はWebhookを止め、影響先を確認した担当者が該当シークレット・トークンを失効/再発行し、Supabaseの登録を更新してから再検証します。

## 個人用Supabaseから組織側へ切り替えるとき

2026-11-18時点のLINE接続先は、個人開発用の非本番Supabase `fbfmgiebxezryudfxnva`です。組織側への切替は未実施で、対象プロジェクトと切替方式も未決です。以下は将来の作業手順であり、移行済みの記録ではありません。

### 別の組織プロジェクトへ関数を配置する場合

このLINE機能はDBを使わないため、関数・Secrets・LINE側Webhookの切替を扱います。アプリ全体のDB・Auth・Storage移行やCloudflare Pagesの接続先変更は別途検討・検証が必要で、この手順には含めません。

1. 組織側の担当者と移行先・用途・実施担当を決めます。[設定前の確認](#設定前に確認する)を移行先でも行い、Dashboardから20文字のproject-refを転記して照合します。既存関数・LINE用Secretsとの競合、Secrets編集・関数デプロイ権限を確認します。本番へ移す場合の運用条件は改めて確認します。
2. ユーザー本人が、引き続き使う同じLINEチャネルの`LINE_CHANNEL_SECRET`と`LINE_CHANNEL_ACCESS_TOKEN`を移行先DashboardのSecretsへ直接登録します。旧プロジェクトから値を会話やファイルへ書き出さず、不要な再発行もしません。
3. [公開手順](#秘密情報を登録して公開する)と同じ関数設定を使い、次の`<new-project-ref>`を確認した移行先へ置き換えて関数だけをデプロイします。DBマイグレーションは実行しません。

   ```sh
   pnpm supabase functions deploy line-webhook --remote=<new-project-ref> --use-api
   ```

4. 新URLへ署名なし・不正署名を送り401になることを確認します。正常署名の試験を行う場合は[公開署名試験](#公開urlと実トークを確認する)を使い、秘密値を表示・記録しません。
5. 旧Webhook URL・Use webhook・応答・再配信設定を本人の手元に控え、切替時刻と影響をチームで確認します。LINE Developers Consoleで新URLを設定してVerifyの成功を確認し、Use webhookを有効にします。再配信は無効とし、既存の応答設定も確認します。Verifyが失敗した場合は旧URLへ戻します。
6. 実際の1対1トークで固定確認返信だけが届くことを確認し、日時・新旧環境の識別名・担当・署名拒否/Verify/実返信の判定を記録します。本文・個人ID・秘密値は記録しません。問題があれば旧URLと従前設定へ戻し、旧接続での返信を確認します。
7. 切替が安定してから、旧関数・旧Secretsに他用途がないか確認し、削除の要否を別途判断します。切替直後に旧Secretsを削除して復旧手段を失わないようにします。

### 現在のプロジェクト自体を組織へ移管する場合

別プロジェクトへの再配置とは別に、Supabaseにはプロジェクト自体を別の組織へ移す機能があります。General settingsから開始しますが、移管元・移管先の権限、既存連携、プランと課金への影響などを[公式のProject Transfers](https://supabase.com/docs/guides/platform/project-transfer)で確認し、方式を決めてから実施します。今回はこの方法も未選定・未実施であり、移管条件や費用を確定していません。

## 後続へ引き継ぐ範囲

- [#20](https://github.com/tm-87-2026/atoyomin/issues/20): アプリユーザーとLINEアカウントの紐付け、認証・認可、期限指定トークンの発行・更新運用。LINE署名は通知元の確認であり、アプリユーザー本人を保証しません。
- [#8](https://github.com/tm-87-2026/atoyomin/issues/8): ブラウザ・SNSからLINEへの共有操作。
- [#9](https://github.com/tm-87-2026/atoyomin/issues/9): URL抽出、記事情報取得、DB保存、保存完了返信。現在は本文を保存せず、DBクライアントも導入していません。
- 定期通知は未対応です。保存や通知を追加する際は同期応答の制約を見直し、再試行・重複排除・応答時間を設計します。署名検証済みの入口と返信通信は再利用候補です。

## 根拠となる公式資料

以下は実装時の2026-11-18に参照した資料です。設定画面・権限・CLIの実際の挙動は操作時にも確認します。

- [LINE署名検証](https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/)
- [LINEの開始手順](https://developers.line.biz/en/docs/messaging-api/getting-started/)・[Reply API](https://developers.line.biz/en/reference/messaging-api/#send-reply-message)
- [Supabase外部Webhook認証](https://supabase.com/docs/guides/functions/auth#external-webhooks)・[Secrets](https://supabase.com/docs/guides/functions/secrets)
- [Supabase CLI](https://supabase.com/docs/reference/cli/supabase-functions-deploy)・[関数テスト](https://supabase.com/docs/guides/functions/unit-test)
- [Denoインストール](https://docs.deno.com/runtime/getting_started/installation/)・[Deno 2.5.6](https://github.com/denoland/deno/releases/tag/v2.5.6)
