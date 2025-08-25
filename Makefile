# --- 環境設定 ---
# .envファイルは、実際の環境ファイル（例：.env.dev, .env.prod）を指すシンボリックリンクです。
# この設定により、タスクごとに環境を簡単に切り替えることができます。
# DOCKER_COMPOSE変数は、開発タスクにdocker-compose.ymlとdocker-compose.override.ymlの両方が
# 使用されるようにします。

# デフォルト環境は'dev'
ENV ?= dev
# 基本のdocker-composeコマンド
DOCKER_COMPOSE := docker-compose
# makeコマンド用のシェル
SHELL := /bin/bash

# `make`が引数なしで実行された場合のデフォルトターゲット
.DEFAULT_GOAL := help


# --- プロジェクトセットアップ --------------------------------------------------
.PHONY: setup
setup:
	@echo "--- セットアップ開始: (.env.dev) 環境 ---"
	@echo "Python依存関係をインストール中..."
	@poetry install
	@echo "--- セットアップ完了 ---"


# --- Dockerコマンド ------------------------------------------------
.PHONY: up
up:
	@echo "--- Dockerコンテナを起動中... ---"
	@ln -sf .env.$(ENV) .env
	$(DOCKER_COMPOSE) up --build -d
	@echo "--- Dockerコンテナがバックグラウンドで実行中です ---"

.PHONY: down
down:
	@echo "--- Dockerコンテナを停止・削除中... ---"
	@ln -sf .env.$(ENV) .env
	$(DOCKER_COMPOSE) down
	@echo "--- Dockerコンテナが停止しました ---"

.PHONY: logs
logs:
	@echo "--- Dockerコンテナのログを表示中... (Ctrl+Cで終了) ---"
	@ln -sf .env.$(ENV) .env
	$(DOCKER_COMPOSE) logs -f

.PHONY: shell
shell:
	@echo "--- webコンテナのシェルに接続中... ---"
	@ln -sf .env.$(ENV) .env
	$(DOCKER_COMPOSE) exec web /bin/bash
	@echo "--- シェルセッションを終了しました ---"


# --- コード品質とテスト -----------------------------------------
.PHONY: test
test:
	@echo "--- テストを実行中... ---"
	@ln -sf .env.dev .env
	poetry run pytest
	@echo "--- テスト完了 ---"

.PHONY: format
format:
	@echo "--- コードをフォーマット中... (black, ruff) ---"
	poetry run black .
	poetry run ruff check . --fix
	@echo "--- フォーマット完了 ---"

.PHONY: format-check
format-check:
	@echo "--- コードフォーマットをチェック中... (black) ---"
	poetry run black --check .
	@echo "--- Blackフォーマットチェック完了 ---"

.PHONY: lint
lint: format
	@echo "--- リントを実行中... (ruff) ---"
	poetry run ruff check .
	@echo "--- リント完了 ---"

.PHONY: lint-check
lint-check:
	@echo "--- リントをチェック中... (ruff) ---"
	poetry run ruff check .
	@echo "--- Ruffリントチェック完了 ---"


# --- ヘルプ -----------------------------------------------------------
.PHONY: help
help:
	@echo "利用可能なMakefileコマンド:"
	@echo ""
	@echo "  プロジェクトセットアップ"
	@echo "    setup          - 開発環境をセットアップします（Poetry依存関係のインストール）。"
	@echo ""
	@echo "  Docker管理"
	@echo "    up             - Dockerコンテナをビルドして起動します（デフォルト: dev環境）。"
	@echo "    down           - Dockerコンテナを停止して削除します。"
	@echo "    logs           - 実行中のDockerコンテナのログをリアルタイムで表示します。"
	@echo "    shell          - 実行中の'web'サービスコンテナのシェルに接続します。"
	@echo ""
	@echo "  コード品質とテスト"
	@echo "    test           - poetry環境でpytestを実行します（CI用）。ローカルでは 'make shell' の後 'poetry run pytest' を推奨します。"
	@echo "    format         - BlackとRuffを使用してコードスタイルを自動で修正します。"
	@echo "    format-check   - Blackでコードスタイルが正しいかチェックします。"
	@echo "    lint           - Ruffでリントを実行します（最初にformatを適用）。"
	@echo "    lint-check     - Ruffでリントエラーがないかチェックします。"
	@echo ""
	@echo "  使い方:"
	@echo "    make up        - 開発環境でコンテナを起動します。"
	@echo "    make up ENV=prod - 本番環境でコンテナを起動します。"
	@echo ""
