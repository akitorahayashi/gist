# Gist Summarizer

このプロジェクトは、指定されたウェブページの内容を要約し、問い合わせに応答するDjangoアプリケーションです。
近代的な開発プラクティスを導入しており、Docker、Makefile, GitHub ActionsによるCI/CDパイプラインが整備されています。

## ✅ 前提条件

開発を始める前に、以下のツールがインストールされていることを確認してください。

- **Docker**: 最新版を推奨
- **Docker Compose**: Dockerに同梱
- **Make**: `make` コマンドが利用可能であること
- **Python**: 3.12 (推奨, `.python-version` ファイル参照)
- **Poetry**: 1.8.3 (推奨)

## 🚀 はじめに (Getting Started)

開発を始めるには、まずリポジトリをクローンし、以下のコマンドで **ホストマシンに** Poetryの仮想環境をセットアップし、依存関係をインストールします。

```bash
make setup
```

## 🐳 コンテナのビルドと実行

アプリケーションはDockerコンテナ上で実行されます。以下のコマンドでコンテナをビルドし、バックグラウンドで起動します。

```bash
make up
```

コンテナが起動したら、`http://localhost:8000`でアプリケーションにアクセスできます。

> **📝 Linuxユーザー向けの注意**
> 開発環境では、コンテナからホストマシン上のサービス（例：モックサーバー）にアクセスするために `host.docker.internal` を使用します。この設定は `docker-compose.override.yml` 内の `extra_hosts` で自動的に行われます。もし `host.docker.internal` が解決できない古いDockerバージョンを使用している場合は、Dockerを最新版に更新してください。

コンテナを停止・削除するには、以下のコマンドを実行します。

```bash
make down
```

### 本番環境での実行

本番環境をシミュレートするには、`ENV=prod` を指定します。

```bash
make up ENV=prod
```

> **⚠️ 重要**
> `make up ENV=prod` を実行する前に、`.env.example` をコピーして `.env.prod` ファイルを作成する必要があります。`.env.prod` ファイルには本番環境用の設定を記述し、このファイルは `.gitignore` によりバージョン管理から除外されています。

## ✅ テストとコード品質

プロジェクトには、コードの品質を維持するためのテスト、リンター、フォーマッターが用意されています。

### テストの実行

ローカルでテストを実行するには、いくつかの方法があります。

1.  **Makeコマンドを使用する方法 (ホストのPoetry環境を利用):**
    ```bash
    make test ENV=dev
    ```

2.  **Dockerコンテナ内で直接実行する方法:**
    コンテナが起動している(`make up`実行後)ことを確認し、以下のコマンドを実行します。
    ```bash
    docker compose exec web poetry run pytest
    ```

### コードのフォーマット

`black`と`ruff`を使ってコードを自動整形します。
```bash
make format
```

### リンターとフォーマットのチェック

CIでも実行されるチェックです。コードに問題がないかを確認します。
```bash
make lint-check
make format-check
```

## 🛠 Makefileコマンド一覧

プロジェクトで利用可能なすべてのコマンドは、`make help`で確認できます。以下は主なコマンドの概要です。

```text
  一般的なコマンド
    all            - 'setup'と'up'を実行し、開発環境を完全に起動します。
    clean          - 生成されたファイル（.envシンボリックリンク）を削除します。

  プロジェクトセットアップ
    setup          - 開発環境をセットアップします（Poetry依存関係のインストール）。

  Docker管理
    up             - Dockerコンテナをビルドして起動します（デフォルト: dev環境）。
    down           - Dockerコンテナを停止して削除します。
    logs           - 実行中のDockerコンテナのログをリアルタイムで表示します。
    shell          - 実行中の'web'サービスコンテナのシェルに接続します。

  コード品質とテスト
    test           - poetry環境でpytestを実行します。 'ENV'変数で環境を指定できます (例: make test ENV=dev)。
    format         - BlackとRuffを使用してコードスタイルを自動で修正します。
    format-check   - Blackでコードスタイルが正しいかチェックします。
    lint           - Ruffでリントを実行します。
    lint-check     - Ruffでリントエラーがないかチェックします。
```
