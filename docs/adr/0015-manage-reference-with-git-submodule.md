# ADR 0015: Bulletproof ReactをGit submoduleで管理する

## Status

Accepted — 2026-11-17

## Context

設計方針を正確に確認できるよう、Bulletproof Reactの原文とサンプル設定を人間とAIがローカルで参照したい。外部リンクだけに頼らず、チームで同じ版を確認できる形が必要である。

## Decision

Bulletproof Reactを `references/bulletproof-react/` にGit submoduleとして配置し、参照するコミットを親リポジトリで固定する。取得・更新手順と原文への導線は[参照資料の案内](../../references/README.md)に記載する。

## Consequences

- 取得後は原文をローカルで参照でき、参照バージョンをチームで揃えられる。
- 新規クローンやworktreeではsubmoduleの初期化・取得が必要になる。
- 参照バージョンの更新時は、親リポジトリで参照コミットと関連文書を更新する。
