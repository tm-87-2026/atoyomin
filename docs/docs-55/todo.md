# Supabaseで利用する機能と用途を整理し文書化するTODO

## 基本情報

- 対象Issue: #55
- 状態: 合意済み
- 合意日・合意対象: 2026-11-10（Asia/Tokyo）、設計書およびTODO全体
- 正とする要求書: [要求書](requirements.md)（2026-11-10、合意済み）
- 設計書: [設計書](design.md)（合意済み）

## 開始条件

- [要求書](requirements.md)のREQ-001〜REQ-004が合意済みであり、未決事項がないこと。
- 現在の実装、Accepted ADR、設計規約、#20、#47、#49の境界を再確認できること。

## 作業一覧

### 完了確認前の作業

- [x] TODO-001（REQ-001、REQ-004） `docs/development/supabase-features.md`を作成し、5機能の用途、利用状態、根拠、再検討条件または担当タスクを記載する。
- [x] TODO-002（REQ-002、REQ-003） 実装済みのDatabase・RLS最小構成と既存方針・未決定事項の区別、既存資料・関連Issueへのリンク、タスク境界を資料へ反映する。
- [x] TODO-003（REQ-001〜REQ-004） 資料を代表シナリオで照合し、TODOの実施記録へ結果と根拠を残す。

### 完了確認

- [x] TODO-004（REQ-001〜REQ-004） 実際の資料、要求書、設計書、TODO実施記録を照合し、完了確認書で全要求の判定と根拠を記録する。

### 確認後の手続き

- [ ] TODO-005（REQ-001〜REQ-004） 完了確認の通過後、親エージェントが変更内容・検証結果・残る課題を報告し、コミット前のユーザー確認を得る。

## 完了条件・依存関係

各作業の完了判定と依存順序を次の表に示す。TODO-005は確認後の手続きであり、TODO-004の通過条件には含めない。

| TODO     | 完了条件                                                                                                                                        | 検証方法                                                                                                                                                                                                                                      | 依存先             |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| TODO-001 | 最終資料が`docs/development/supabase-features.md`にあり、Auth、Database・RLS、Edge Functions、Storage、Realtimeの用途と合意済みの利用状態を示す | 最終資料のパスと機能一覧を目視照合し、Database・RLS＝実装済み、Auth・Edge Functions＝既存の方針で利用を予定、Storage・Realtime＝現時点で利用しないこと、Storage・Realtimeの再検討条件、Edge Functionsの個別処理を検討する担当タスクを確認する | 開始条件           |
| TODO-002 | Database・RLSを実装済み、それ以外を設計書の分類どおりに区別し、既存方針と関連タスクへの参照・境界を記載する                                     | `src/lib/supabase.ts`、マイグレーション、ADR 0002、ADR 0003、設計規約、#20、#47、#49と最終資料を目視照合する                                                                                                                                  | TODO-001           |
| TODO-003 | REQ-001〜REQ-004の代表シナリオをすべて実施し、結果と根拠を実施記録に残す                                                                        | [設計書の検証方針](design.md#検証方針)の表に従い、資料・実装・既存文書を照合する                                                                                                                                                              | TODO-001、TODO-002 |
| TODO-004 | 全要求とTODO-001〜TODO-003の実施結果に不足がないことを判定し、`verification.md`に根拠と残る課題を記録する                                       | 開発ワークフローの完了確認工程として、要求書・設計書・TODO・最終資料・実施記録を相互に照合する                                                                                                                                                | TODO-003           |
| TODO-005 | 親エージェントがユーザーへ完了報告を行い、コミット前の確認を得る                                                                                | 報告とユーザー確認を記録する                                                                                                                                                                                                                  | TODO-004の通過後   |

## 実施記録

- TODO-001（REQ-001、REQ-004）: `docs/development/supabase-features.md`を作成した。5機能すべてに用途、利用状態、根拠、再検討条件または担当タスクを記載した。資料パスと一覧を目視照合し、Database・RLS＝実装済み、Auth・Edge Functions＝既存の方針で利用を予定、Storage・Realtime＝現時点で利用しないという合意済み分類、ならびにStorage・Realtimeの再検討条件とEdge Functionsの担当タスクの境界を確認した。
- TODO-002（REQ-002、REQ-003）: [Supabaseクライアント](../../src/lib/supabase.ts)と[接続確認用マイグレーション](../../supabase/migrations/20261107000000_create_app_status.sql)を資料と照合した。公開用キーでData APIへ接続し、`public.app_status`でRLSを有効化して`anon`と`authenticated`への`SELECT`だけを許可する最小構成が一致した。さらに、[ADR 0002](../adr/0002-use-supabase-for-backend-services.md)、[ADR 0003](../adr/0003-use-cloudflare-pages-for-frontend-hosting.md)、[設計規約](../conventions/design.md)、Issue #20・#47・#49への参照と境界を目視照合し、認証詳細、環境設定・実動作、責務分割を追加していないことを確認した。
- TODO-003（REQ-001〜REQ-004）: [設計書の検証方針](design.md#検証方針)の代表シナリオを実施した。REQ-001・REQ-004は資料の配置と5機能の一覧・分類、REQ-002はクライアントとマイグレーションとの整合、REQ-003はADR・規約・関連Issueの参照および対象外の境界、REQ-004はStorage・Realtimeの再検討条件とEdge Functionsの個別導入判断の記載を照合し、すべて判定基準を満たした。
- TODO-004（REQ-001〜REQ-004）: [完了確認書](verification.md)を作成し、要求書・設計書・TODO実施記録・最終資料・既存の根拠を独立に照合した。全要求とTODO-001〜TODO-003に不足がないため通過と判定した。

## 残る課題

TODO-005（親エージェントの報告・コミット前確認）。

## 関連資料

- [要求書](requirements.md)
- [設計書](design.md)
- [開発ワークフロー](../development/development-workflow.md)
- [設計規約](../conventions/design.md)
- [SupabaseとCloudflare Pagesのセットアップ](../development/supabase-cloudflare-pages.md)
