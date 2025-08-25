# Gist Summarizer

このプロジェクトは、指定されたウェブページの内容を要約し、問い合わせに応答するDjangoアプリケーションです。
近代的な開発プラクティスを導入しており、Docker、Makefile, GitHub ActionsによるCI/CDパイプラインが整備されています。

## 🚀 はじめに

開発を始めるには、まずリポジトリをクローンし、以下のコマンドで開発環境をセットアップします。
このコマンドは、必要なPythonの依存関係をインストールします。

```bash
make setup
```

## 🐳 コンテナのビルドと実行

アプリケーションはDockerコンテナ上で実行されます。以下のコマンドでコンテナをビルドし、バックグラウンドで起動します。

```bash
make up
```

コンテナが起動したら、`http://localhost:8000`でアプリケーションにアクセスできます。

コンテナを停止・削除するには、以下のコマンドを実行します。

```bash
make down
```

## ✅ テストとコード品質

プロジェクトには、コードの品質を維持するためのテスト、リンター、フォーマッターが用意されています。

- **テストの実行**:
  ```bash
  make test
  ```
  *注意: このコマンドはCI環境での使用を想定しています。ローカルでテストを実行する場合は、`make shell`でコンテナに入り、`poetry run pytest`を実行してください。*

- **コードのフォーマット**:
  `black`と`ruff`を使ってコードを自動整形します。
  ```bash
sh
  make format
  ```

- **リンターとフォーマットのチェック**:
  CIでも実行されるチェックです。コードに問題がないかを確認します。
  ```bash
  make lint-check
  make format-check
  ```

## 🛠 Makefileコマンド一覧

プロジェクトで利用可能なすべてのコマンドは、`make help`で確認できます。

```text
利用可能なMakefileコマンド:

  プロジェクトセットアップ
    setup          - 開発環境をセットアップします（Poetry依存関係のインストール）。

  Docker管理
    up             - Dockerコンテナをビルドして起動します（デフォルト: dev環境）。
    down           - Dockerコンテナを停止して削除します。
    logs           - 実行中のDockerコンテナのログをリアルタイムで表示します。
    shell          - 実行中の'web'サービスコンテナのシェルに接続します。

  コード品質とテスト
    test           - poetry環境でpytestを実行します（CI用）。ローカルでは 'make shell' の後 'poetry run pytest' を推奨します。
    format         - BlackとRuffを使用してコードスタイルを自動で修正します。
    format-check   - Blackでコードスタイルが正しいかチェックします。
    lint           - Ruffでリントを実行します（最初にformatを適用）。
    lint-check     - Ruffでリントエラーがないかチェックします。

  使い方:
    make up        - 開発環境でコンテナを起動します。
    make up ENV=prod - 本番環境でコンテナを起動します。
```
