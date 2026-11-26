# 人間とコーディングエージェントの協働を評価する観点

## 目的と使い方

この資料は、会話ログに記録された人間の指示、判断、提案した進め方を振り返るための評価観点である。Codexの応答は評価せず、人間の発言が何に反応し、何を変えたかを理解する前後文脈としてだけ参照する。

各観点の「資料の明記」は原典の推奨と理由、「ログ評価への推論」はその推奨を会話ログへ適用する解釈である。観点は所見を探す手掛かりであり、項目の有無や回数だけで良否を採点しない。適用範囲外、資料間に緊張がある、またはログ外の情報が必要な場合は「不明」とする。

出典は2026-11-26に確認したスナップショットである。原典の現行性が所見を左右する場合だけ公式ページを再確認する。

## 共通の証拠区分

- **公式実践ガイド**: 提供組織が示す運用上の推奨。推奨の根拠にはなるが、対照実験による因果の証明ではない。
- **公式技術記事・事例**: 提供組織の実装例や観察に基づく説明。条件を越えて一般化しない。
- **観察研究**: 実利用や公開データの相関・傾向。因果や規範的な推奨を示すとは限らない。

## PRACTICE-001 指示の構造

### 出典

- 資料名: Codex best practices / 提供組織: OpenAI / URL: https://developers.openai.com/codex/learn/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Prompting Codex / 提供組織: OpenAI / URL: https://developers.openai.com/codex/prompting / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド

### 資料の明記と理由

Codexへの指示には目的、関係するファイルやエラーなどの文脈、規約や安全要件などの制約、完了条件を含めることが推奨されている。別の型では目的、文脈、出力、境界を示し、結果から書き始め、手順はプロセス自体が重要な場合だけ書く。これにより仮定が減り、範囲を守ったレビュー可能な成果になりやすい。

### ログ評価への推論

人間の初回指示に目的、文脈、制約、完了条件が示されているか、後続ターンで同じ要素を補っていないか、Codexの確認質問が欠けた要素に対応していないかを調べる。

### 適用範囲

Codex向けの指示形式である。他のエージェントへの適用は推論とする。大規模または重要な作業ほど明確さの価値が高いが、短い指示を一律に問題としない。

### ログだけでは判断不能な事項と不明条件

背景がAGENTS.md、Issue、口頭、別ツールにあるかはログだけでは分からない。簡潔な指示で十分だったか、手順を指定すべき作業だったかを確認できない場合は不明とする。

### 資料間の緊張

目的・境界を明確にする推奨と、不要な手順を指定せず結果を中心に書く推奨が併存する。情報量が多いほど良いとは判定しない。

## PRACTICE-002 具体性とスコープ

### 出典

- 資料名: Claude Code best practices / 提供組織: Anthropic / URL: https://code.claude.com/docs/en/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Getting the best results from Copilot coding agent / 提供組織: GitHub / URL: https://docs.github.com/en/copilot/tutorials/cloud-agent/get-the-best-results / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Codex best practices / 提供組織: OpenAI / URL: https://developers.openai.com/codex/learn/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: An Empirical Study of GitHub Issues for Copilot Coding Agent / 提供組織: 研究著者 / URL: https://arxiv.org/html/2512.21426v1 / 確認日: 2026-11-26 / 証拠種別: 観察研究

### 資料の明記と理由

対象ファイルやシナリオ、症状と場所、直った状態、再現手順、受け入れ基準、既存実装の参照を具体的にすることが推奨されている。正確な指示は修正の往復を減らす。一方、探索目的では曖昧な指示にも価値がある。GitHub Issueの研究は、限定的、簡潔、自己完結的で手順に分かれたIssueを推奨するが、観察に基づく示唆である。

### ログ評価への推論

人間の指示に対象パス、症状、再現手順、参照実装、受け入れ基準があるか、抽象語や同一論点の修正往復があるかを調べる。

### 適用範囲

製品固有の操作を除き、具体性の原則をコーディングエージェント一般へ適用することは推論である。探索タスクには同じ具体性を要求しない。

### ログだけでは判断不能な事項と不明条件

曖昧さが意図的か、具体的な前提が正しかったか、最終成果が使えたかはログだけでは分からない。作業の探索性や外部の受け入れ結果が確認できない場合は不明とする。

### 資料間の緊張

具体性を高める推奨と、探索では余地を残す推奨がある。具体性の高さだけで良否を決めない。

## PRACTICE-003 検証可能な完了条件

### 出典

- 資料名: Claude Code best practices / 提供組織: Anthropic / URL: https://code.claude.com/docs/en/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Prompting Codex / 提供組織: OpenAI / URL: https://developers.openai.com/codex/prompting / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Codex best practices / 提供組織: OpenAI / URL: https://developers.openai.com/codex/learn/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Effective harnesses for long-running agents / 提供組織: Anthropic / URL: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents / 確認日: 2026-11-26 / 証拠種別: 公式技術記事・事例

### 資料の明記と理由

テスト、ビルド、lint、再現手順、スクリーンショット比較など、エージェントが実行できる検証を渡し、成功の主張ではなく出力などの証拠を示させることが推奨されている。検証がなければ誤りが人間の発見待ちになり、十分なテストなしに機能を完了扱いにする失敗が起きる。

### ログ評価への推論

人間が検証方法や成功条件を指示したか、証拠の提示を求めたか、完了後に検証有無を聞き直したかを調べる。実際の検証結果は人間の指示の背景としてだけ参照する。

### 適用範囲

検証可能なソフトウェア作業に広く適用する。`/verify` やStop hookなどはClaude Code固有であり、他製品の必須手段とはしない。

### ログだけでは判断不能な事項と不明条件

人間の手元確認、CI、AGENTS.md記載のコマンド、テスト自体の質はログに現れない場合がある。外部検証の有無や十分性を確認できなければ不明とする。

### 資料間の緊張

特段の対立はないが、検証方法を発言内に毎回書く必要性は、既存の指示ファイルやCIの有無で変わる。

## PRACTICE-004 計画、分割、曖昧さの解消

### 出典

- 資料名: Codex best practices / 提供組織: OpenAI / URL: https://developers.openai.com/codex/learn/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Claude Code best practices / 提供組織: Anthropic / URL: https://code.claude.com/docs/en/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド

### 資料の明記と理由

複雑、曖昧、説明しにくいタスクは実装前に調査・計画し、大きな作業を小さく焦点の絞られたステップへ分けることが推奨されている。誤った問題を解く危険を減らし、テストとレビューを容易にする。一文で説明できる小さな差分では計画の負担を避けてもよい。

### ログ評価への推論

大きな変更の前に人間が調査や計画を求めたか、作業をレビュー可能な単位へ分けたか、計画へフィードバックしたか、小さな作業に過剰な工程を課していないかを調べる。

### 適用範囲

複雑または曖昧な作業に適用する。Plan modeや`/plan`などの方法は製品固有であり、計画の存在と同一視しない。

### ログだけでは判断不能な事項と不明条件

人間の頭の中や別ツールの計画、適切な分割粒度、作業の実質的な複雑さはログだけでは分からない。複雑さと計画の所在を確認できなければ不明とする。

### 資料間の緊張

複雑な作業での計画推奨と、小さな作業での省略推奨がある。計画の有無だけで評価しない。

## PRACTICE-005 コンテキスト管理

### 出典

- 資料名: Claude Code best practices / 提供組織: Anthropic / URL: https://code.claude.com/docs/en/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Codex best practices / 提供組織: OpenAI / URL: https://developers.openai.com/codex/learn/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Mastering Codex remote for engineering / 提供組織: OpenAI / URL: https://developers.openai.com/blog/mastering-codex-remote-for-engineering / 確認日: 2026-11-26 / 証拠種別: 公式技術記事・事例
- 資料名: Effective context engineering for AI agents / 提供組織: Anthropic / URL: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents / 確認日: 2026-11-26 / 証拠種別: 公式技術記事・事例

### 資料の明記と理由

無関係な作業は会話を分け、一つのまとまった成果ごとに一つのチャットを使い、横道の質問を別文脈へ分け、必要最小限で情報価値の高いコンテキストを渡すことが推奨されている。関係ない情報が増えると以前の指示を忘れ、誤りが増えるためである。一方、同じ問題へ深く取り組む間は履歴に価値がある。

### ログ評価への推論

人間が一つのスレッドへ無関係な話題を混在させていないか、長大化後に指示を再説明していないか、横道を分離したかを調べる。

### 適用範囲

有限のコンテキストを持つエージェントに共通する原則としての適用は推論である。`/clear`、side chat、forkは製品固有である。

### ログだけでは判断不能な事項と不明条件

ログの単位が実際のスレッドまたはセッションと一致するか、圧縮で何が失われたか、履歴継続に価値があったかは分からない。境界や圧縮状態を確認できない場合は不明とする。

### 資料間の緊張

短く分離する推奨と、同じ問題では履歴を保つ利点がある。長さだけで非効率としない。

## PRACTICE-006 軌道修正とステアリング

### 出典

- 資料名: Claude Code best practices / 提供組織: Anthropic / URL: https://code.claude.com/docs/en/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Prompting Codex / 提供組織: OpenAI / URL: https://developers.openai.com/codex/prompting / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Getting the best results from Copilot coding agent / 提供組織: GitHub / URL: https://docs.github.com/en/copilot/tutorials/cloud-agent/get-the-best-results / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Measuring AI agent autonomy in practice / 提供組織: Anthropic / URL: https://www.anthropic.com/research/measuring-agent-autonomy / 確認日: 2026-11-26 / 証拠種別: 観察研究

### 資料の明記と理由

逸脱に気づいたら早く止めて修正し、実行中の方向転換と作業後に回す追加依頼を使い分けることが推奨されている。CopilotのPRコメントは個別送信ではなくレビューへまとめる。早期修正は不要な往復を減らす。Anthropicの観察では、経験者は自動承認と割り込みの双方を多く使う傾向がある。

### ログ評価への推論

人間の割り込みが逸脱の序盤か終盤か、同一事項を連続して直しているか、追加情報と方針訂正のどちらか、即時修正と後続依頼を使い分けたかを調べる。

### 適用範囲

早期の軌道修正は一般化しやすいが、steer/queueはCodex、レビュー一括送信はCopilot固有である。利用統計はClaude Codeの観察である。

### ログだけでは判断不能な事項と不明条件

割り込みの意図、作業進捗、割り込まなかった場合の損失は分からない。割り込み回数だけでは監督の質を判断できないため、理由と作用を追えなければ不明とする。

### 資料間の緊張

逸脱への即時介入と、細かなレビュー指摘をまとめて送る推奨は、介入の目的と媒体で使い分ける必要がある。

## PRACTICE-007 レビューと独立検証

### 出典

- 資料名: Codex best practices / 提供組織: OpenAI / URL: https://developers.openai.com/codex/learn/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Claude Code best practices / 提供組織: Anthropic / URL: https://code.claude.com/docs/en/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Harness design for long-running application development / 提供組織: Anthropic / URL: https://www.anthropic.com/engineering/harness-design-long-running-apps / 確認日: 2026-11-26 / 証拠種別: 公式技術記事・事例

### 資料の明記と理由

テストとlint、diffレビュー、専用レビュー機能、チームのレビュー基準、実装者と異なる新しいコンテキストのレビュアーが推奨されている。新しいレビュアーは実装時の推論に依存せず成果を評価できる。一方、指摘を無条件にすべて直すと過剰設計になるため、正しさと要件に関わる指摘へ絞る。

### ログ評価への推論

人間が具体的な行や挙動、レビュー観点を示したか、独立レビューを求めたか、指摘を要件に照らして取捨選択したかを調べる。

### 適用範囲

変更のレビュー全般に適用する。製品固有のレビューコマンドを必須としない。独立コンテキストの価値は、変更のリスクと規模に応じて判断する。

### ログだけでは判断不能な事項と不明条件

IDEやGitHub上のレビュー、画面上での精査はログに現れない場合がある。「OK」だけからレビュー不足と断定せず、外部レビューの有無が分からなければ不明とする。

### 資料間の緊張

独立レビューで指摘を探す推奨と、全指摘への対応が過剰設計を生む警告がある。指摘数や採用率だけで評価しない。

## PRACTICE-008 再利用可能な指示

### 出典

- 資料名: Codex best practices / 提供組織: OpenAI / URL: https://developers.openai.com/codex/learn/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Claude Code best practices / 提供組織: Anthropic / URL: https://code.claude.com/docs/en/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Getting the best results from Copilot coding agent / 提供組織: GitHub / URL: https://docs.github.com/en/copilot/tutorials/cloud-agent/get-the-best-results / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド

### 資料の明記と理由

繰り返す規約、コマンド、制約、完了定義はAGENTS.mdなどへ移し、繰り返す一つのワークフローはSkillにすることが推奨されている。同じ指示を減らし一貫性を保つ一方、曖昧な規則を大量に置かず、削除してもミスが増えない行は除く。長すぎる指示は重要な規則を埋もれさせる。

### ログ評価への推論

人間が複数のセッションで同じ制約を繰り返していないか、同種の指摘が再発していないか、長い定型文を貼っていないかを調べ、再利用可能な指示の候補として扱う。

### 適用範囲

複数セッションで再発する安定した規約やワークフローに適用する。ファイル名、配置、読込方式は製品ごとに異なる。

### ログだけでは判断不能な事項と不明条件

単一ログでは反復を判断できず、AGENTS.mdやSkillの現物も必要である。既存指示があるのに守られなかった場合は人間の指示品質と分離できないため不明とする。

### 資料間の緊張

再利用による一貫性と、指示ファイルの肥大化を避ける要請がある。反復を見つけただけで規則追加を推奨しない。

## PRACTICE-009 権限、承認、並列作業の安全

### 出典

- 資料名: Codex best practices / 提供組織: OpenAI / URL: https://developers.openai.com/codex/learn/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Claude Code best practices / 提供組織: Anthropic / URL: https://code.claude.com/docs/en/best-practices / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド

### 資料の明記と理由

初めは制限された権限とサンドボックスを使い、信頼できるリポジトリや定型作業に限って緩め、同じファイルを変更する作業を同時実行しないことが推奨されている。承認が過多だと確認せずクリックする習慣が生じ、安全策が形骸化するため、許可リストやサンドボックスで負担を減らす。

### ログ評価への推論

人間が削除、本番、認証情報などの操作に応じて権限を調整したか、承認の内容を確認した形跡があるか、同じファイルを触る並列作業を避けたかを調べる。

### 適用範囲

エージェントが外部状態やファイルを変更する作業に適用する。権限、承認、worktreeの具体的な仕組みは製品・環境固有である。

### ログだけでは判断不能な事項と不明条件

承認UIでの操作、実際の設定、別スレッドの編集対象はログに出ない場合がある。応答速度だけで確認の有無を推定せず、設定と対象を確認できなければ不明とする。

### 資料間の緊張

安全のための承認と、承認疲れを避ける自動化の間に緊張がある。承認回数の多寡だけで良否を決めない。

## PRACTICE-010 長時間・複数セッションの引き継ぎ

### 出典

- 資料名: Codex Exec Plans / 提供組織: OpenAI / URL: https://developers.openai.com/cookbook/articles/codex_exec_plans / 確認日: 2026-11-26 / 証拠種別: 公式技術記事・事例
- 資料名: Codex long-horizon tasks / 提供組織: OpenAI / URL: https://developers.openai.com/cookbook/examples/codex/long_horizon_tasks/ / 確認日: 2026-11-26 / 証拠種別: 公式技術記事・事例
- 資料名: Effective harnesses for long-running agents / 提供組織: Anthropic / URL: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents / 確認日: 2026-11-26 / 証拠種別: 公式技術記事・事例

### 資料の明記と理由

長期作業では、検証を伴うマイルストーン、失敗時に先へ進まない規則、判断、進捗をファイルとgit履歴へ残し、一機能ずつクリーンな状態で終える事例が示されている。新しいセッションは前の記憶を持たず、状態を外部化しないと途中で止まるためである。

### ログ評価への推論

人間がセッションごとに状況を口頭で再説明していないか、計画・進捗・残課題を成果物へ残すよう指示したか、検証可能な区切りを設けたかを調べる。

### 適用範囲

長時間または複数セッションの作業に適用する。PLANS.mdとAnthropicの進捗ファイルは異なる事例であり、特定形式を一般要件にしない。

### ログだけでは判断不能な事項と不明条件

小規模作業には過剰となり得る。git履歴や成果物を読まなければ引き継ぎ状態を判断できず、会話ログだけの場合は不明とする。

### 資料間の緊張

状態の詳細な外部化は引き継ぎを助けるが、小規模作業では管理負担になる。作業規模を確認せず採用を評価しない。

## PRACTICE-011 委任の適否と自律度

### 出典

- 資料名: Getting the best results from Copilot coding agent / 提供組織: GitHub / URL: https://docs.github.com/en/copilot/tutorials/cloud-agent/get-the-best-results / 確認日: 2026-11-26 / 証拠種別: 公式実践ガイド
- 資料名: Measuring AI agent autonomy in practice / 提供組織: Anthropic / URL: https://www.anthropic.com/research/measuring-agent-autonomy / 確認日: 2026-11-26 / 証拠種別: 観察研究

### 資料の明記と理由

広範、複雑、機密性や重要度が高い、または曖昧な作業はエージェントへ任せず人間が行う選択肢があり、最初は簡単なタスクから試すことが推奨されている。Anthropicの観察では、経験者ほどfull auto-approveを使う割合が高く、モデルが扱える自律度が実際に与えられた自律度を上回ると分析されているが、運用上の規範や因果を示すものではない。

### ログ評価への推論

人間がタスクの難度、曖昧さ、重要度に応じて委任範囲、承認方針、介入頻度を変えたか、曖昧な課題を計画なしで委任していないかを調べる。

### 適用範囲

Copilotクラウドエージェント向けの推奨とClaude Code利用の観察である。Codexへ適用する場合は推論と明記する。

### ログだけでは判断不能な事項と不明条件

タスクの実際の難度・機密性、委任結果の成否、利用者の経験、承認設定はログ外にあり得る。これらを確認できなければ自律度の適否は不明とする。

### 資料間の緊張

高リスク・曖昧な作業では委任を控える推奨と、経験に伴い自律度が上がる観察がある。後者を自動承認の推奨として扱わない。

## 横断して適用する限界

- 公式実践ガイドは運用上の推奨であり、対照実験による因果の証明とは扱わない。
- 観察研究の相関を「この行動を取れば成功する」という規範へ変換しない。
- 成果の合否、IDEやGitHub上のレビュー、手元確認、指示ファイル、承認UI、口頭や別ツールの合意はログ外にあり得る。
- 人間の指示とCodexの能力・誤りを分離できない場合は、人間側の改善点として確定しない。
- 「具体的に指示する」と「結果を示して手順を任せる」、「早く介入する」と「レビューをまとめる」、「厳しい承認」と「承認疲れを避ける」には条件付きの緊張がある。課題、リスク、媒体を確認できない場合は不明とする。
