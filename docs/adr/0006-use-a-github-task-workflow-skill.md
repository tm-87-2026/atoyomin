# ADR 0006: GitHubタスクの手順をSkillにまとめる

## Status

Proposed

## Context

GitHub Issueを起点とする作業を一貫して進め、Issue番号だけを指定された場合も対象リポジトリと必要な関連情報を特定できる状態を目指す。

IssueやPRの取得・作成、ブランチやコミット操作はGitHub APIやローカル環境に依存する。一方、何を調べるか、重複Issueをどう扱うか、どの操作を依頼の範囲とみなすかは、繰り返し使える作業手順として管理できる。

## Decision

GitHubタスクの依頼解釈、Issue調査、重複確認、ブランチ運用、外部変更の実行条件をリポジトリ内の `github-task-workflow` Skillに記載する。GitHub APIの通信やGitHub上の変更は、利用可能なGitHub連携ツールに任せる。リポジトリ固有の安定した規約は `AGENTS.md` に置き、詳細な手順を重複して記載しない。

## Consequences

- Issue作業、新しいIssue、PR作成の流れと操作条件を同じ手順で参照できる。
- GitHub CLIやSSHが使えない環境でも、接続済みGitHub連携ツールを代替手段として使える。
- このSkillの手順とリポジトリ共通規約を変更するときは、役割が重複しないよう両者を確認する必要がある。
