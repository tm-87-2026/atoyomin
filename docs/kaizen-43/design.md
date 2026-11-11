# worktree内での開始・再開の設計

## 基本情報

- 対象Issue: #43
- 状態: 合意済み
- 合意日・合意対象: 2026-11-11、設計・TODO全体。ユーザーの「ok」により明示合意。
- 正とする要求書: [requirements.md](requirements.md)（2026-11-11、要求全体に合意済み）

## 設計の概要

人間が最低限読む範囲は基本情報とこの節とする。後続サブエージェントは[詳細設計](#詳細設計)も読む。

### 全体構成

開始の言い回しだけで環境準備へ進むことを防ぐため、task-startの適用前に現在位置・ブランチ・対象Issueを照合する。対象Issueのworktreeを既に開いていればdevelopment-workflowへ進み、成果物と合意状態から工程を判断する。元リポジトリから環境を準備する場合は既存のtask-start手順を使う。具体的な境界は[適用条件と開始手順](#適用条件と開始手順)に示す。

### 主要な設計判断と採用理由

- Skill選択時に誤適用を防ぐため、両Skillのdescriptionと本文を揃える。本文だけを直すより変更箇所は増えるが、開始を表す語だけでtask-startを選ぶ説明を残さない。
- 分岐は環境準備より前に置き、同じIssueの既存worktreeでは準備・担当者追加・ウィンドウ起動へ進まない。環境準備側の既存コマンドや再利用規則は維持し、REQ-002への影響を抑える。
- 新しい工程や自動判定プログラムは追加せず、既存の適用範囲を明確にする。新たな重要設計判断や既存ADRの変更に当たらないためADRは追加しない。

### 適用条件と運用上の制約

対象は同じIssueのタスク用worktreeからの開始・再開と、元リポジトリからの環境準備である。パス名だけでタスクを判断せず、Gitの現在位置・worktree一覧・作業ブランチと依頼のIssueを照合する。別Issueへの切り替えは対象外であり、不一致・不足を同じIssueと推定せず確認する。工程・合意・公開境界は[正本](../development/development-workflow.md)を維持する。

### 成立を確認した根拠と限界

現行task-startのdescriptionと「開始の呼びかけでは」の本文が環境準備へ一律に進む一方、development-workflowとAGENTS.mdはworktreeを開いた後を開発の対象としていることを文書調査で確認した。[既存検証記録](../testing/task-skills.md)には環境準備の個別操作の実施根拠がある。

本設計の[代表シナリオ](#検証方針)は変更前に定めた判定基準であり、実施結果ではない。実装後は文書に対する進行判断を照合する。GitHub更新、実際のウィンドウ起動、一連のSkill自動実行をこの照合だけで保証しない。

### 人間の判断に関わる未決事項

なし。

## 詳細設計

### 適用条件と開始手順

REQ-001の誤適用を準備操作の前に防ぎ、REQ-002の既存手順へ必要な場合だけ進めるため、次の順序を両Skillで整合させる。

1. 現在のリポジトリ・ブランチ・worktreeと依頼対象Issueを確認する。`git rev-parse --show-toplevel`、`git branch --show-current`、`git worktree list --porcelain`、`git status --short --branch`などの読み取りで判断し、利用者の変更を保持する。
2. 対象Issueのタスク用worktree内ならtask-startの環境準備を適用せず、development-workflowの「状態を確かめる」へ進む。成果物がなければ目的・範囲・完了の目安のすり合わせから、成果物があれば有効な合意と未決事項を読んで正本の工程・再開条件から進める。
3. 元リポジトリからタスク用の環境準備を依頼された場合はtask-startの既存手順へ進む。Issue確認、担当者追加、新規作成または既存環境の再利用、認証リンク、別ウィンドウ起動、結果報告を維持する。
4. Issueとブランチの対応や現在位置が不明・不一致なら、準備操作へ進まず状況を示して確認する。別Issueへの切り替え手順は追加しない。

task-startではdescription・対象の説明・「#番号に着手する」節の導入を修正し、環境確認をAPIや変更操作より前に置く。「現在位置が既存worktreeでも」という既存の説明は、同じIssueの既存worktreeからの開始を環境準備へ戻す意味にならないよう適用範囲を限定する。準備用のコマンド例も、環境準備を行う場合の例であることを明示する。

development-workflowではdescriptionと「状態を確かめる」に、同じIssueのworktreeでの「#番号に着手する」「#番号をやります」なども開始・再開として扱うことを明記する。正本の「目的と適用範囲」には両Skillの境界を短く補足し、詳細手順はSkillへ置く。

### 成果物・変更範囲

変更箇所と責務を次の表に示す。要求や工程の再定義を他の共通文書へ広げない。

| 対象 | 変更内容・対応要求 |
| --- | --- |
| `.agents/skills/task-start/SKILL.md` | 適用条件、準備前の判定、準備手順の適用範囲を修正。既存の新規作成・再利用操作は維持（REQ-001・REQ-002） |
| `.agents/skills/development-workflow/SKILL.md` | 同じIssueの既存worktreeでの開始・再開を適用対象に明記し、成果物と合意に基づく開始へ接続（REQ-001） |
| `docs/development/development-workflow.md` | 目的と適用範囲でtask-startとの境界を補足。工程・成果物・合意・公開条件は維持（REQ-001・REQ-002） |
| `docs/testing/task-skills.md` | 下記の基準と変更後の照合結果をIssue #43の節として追記。過去の実施結果を保持（REQ-001・REQ-002） |
| `docs/kaizen-43/todo.md`・`verification.md` | TODOの実施根拠と、後続の完了確認結果を記録（REQ-001・REQ-002） |

### 検証方針

文書・Skillのみの変更として、コードの単体テストを追加せず、次の入力に対して変更後のSkill・正本が導く判断を読み取り照合する。各行の入力、根拠節、判断結果を検証文書へ残す。現在の文書にはS1・S2でtask-startへ一律に進む記述があることを変更前の不成立として記録し、実装後の結果と区別する。

代表シナリオと判定基準を次の表に示す。

| ID・要求 | 入力 | 成功条件・不成立の基準 |
| --- | --- | --- |
| S1・REQ-001 | 対象Issueのworktree、成果物なし。「#43に着手する」「#43をやります」の各表現 | 現在の環境で目的・範囲・完了の目安のすり合わせへ進む。ブランチ・worktree準備、担当者追加、認証リンク作成、別ウィンドウ起動へ進めば不成立 |
| S2・REQ-001 | 同じworktree、要求の合意記録あり・設計未合意。「#43を再開する」 | 成果物の合意状態に従って設計または確認待ちから再開する。準備の再実行、要求のやり直し、未合意設計での実装開始は不成立 |
| S3・REQ-002 | 元リポジトリから環境準備を依頼、対象ブランチ・worktreeなし | task-startの新規作成手順と準備完了報告へ進む。環境があると仮定して開発へ進めば不成立 |
| S4・REQ-002 | 元リポジトリから環境準備を依頼、対象ブランチまたはworktreeあり | ローカルブランチのみ、リモートブランチのみ、worktreeありの各条件で既存手順を選び、既存worktreeが標準と別の場所でも再利用する。重複作成、リセット、再利用手順の欠落は不成立 |

関連Skill・正本・検証文書を横断検索し、開始表現だけで無条件に環境準備へ進む記述が残らないことも確認する。変更したMarkdownのローカルリンク、Skillのfrontmatter、`git diff --check`を確認し、GitHub書き込みや実ウィンドウ起動は照合のために実施しない。文書照合による判断の確認であることを結果に明記する。

### 未決事項

なし。

## 関連資料・判断記録

- [要求書](requirements.md)、[TODO](todo.md)
- [task-start Skill](../../.agents/skills/task-start/SKILL.md)、[development-workflow Skill](../../.agents/skills/development-workflow/SKILL.md)
- [開発ワークフロー](../development/development-workflow.md)、[既存のタスクSkill検証](../testing/task-skills.md)
- [ADR 0011](../adr/0011-separate-development-context-by-phase.md)、[ADR 0012](../adr/0012-coordinate-phase-agents-through-artifacts.md)
