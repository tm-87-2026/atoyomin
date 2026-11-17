# 参照資料

## Bulletproof React

[bulletproof-react](bulletproof-react/README.md)をGit submoduleとして配置する。人間とAIが同じ原文・サンプル設定をローカルで確認するための資料である。採用する方針は[FEのアーキテクチャ](../docs/architecture/frontend.md)に記載する。

- 原文：[ガイド一覧](bulletproof-react/README.md#table-of-contents)
- 配置・依存関係：[Project Structure](bulletproof-react/docs/project-structure.md)
- Linter・書式・命名：[Project Standards](bulletproof-react/docs/project-standards.md)
- ESLintの実設定：[Vite版の設定](bulletproof-react/apps/react-vite/.eslintrc.cjs)
- 出典：<https://github.com/alan2207/bulletproof-react>
- ライセンス：[MIT](bulletproof-react/LICENSE)

### 取得

新しくクローンするときは `git clone --recurse-submodules <リポジトリURL>` を使う。既存のクローンやworktreeでは、リポジトリ直下から次を実行する。

```sh
git submodule update --init --recursive
```

初回取得にはネット接続が必要で、取得後はローカルで参照できる。ブランチ切り替え後も同じコマンドで、そのブランチが記録するコミットへ揃える。

### 更新

参照バージョンは親リポジトリが記録するコミットに固定する。更新時は対象コミットの変更内容と採用方針への影響を確認し、次の操作を行う。

```sh
git -C references/bulletproof-react fetch origin
git -C references/bulletproof-react checkout --detach <確認したコミットSHA>
git add references/bulletproof-react
```

参照コミットを明記した文書も合わせて更新し、親リポジトリでコミットする。原文の修正や依存パッケージのインストールは、参照のためには不要である。
