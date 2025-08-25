# --- 環境設定 ---
# .envファイルは、実際の環境ファイル（例：.env.dev, .env.prod）を指すシンボリックリンクです。
# この設定により、タスクごとに環境を簡単に切り替えることができます。
# DOCKER_COMPOSE変数は、開発タスクにdocker-compose.ymlとdocker-compose.override.ymlの両方が
# 使用されるようにします。

# デフォルト環境は'dev'
ENV ?= dev
# 基本のdocker-composeコマンド (環境変数で上書き可能)
DOCKER_COMPOSE ?= docker compose
# makeコマンド用のシェル
SHELL := /bin/bash

# `make`が引数なしで実行された場合のデフォルトターゲット
.DEFAULT_GOAL := help

# --- ターゲットをPhonyとして宣言 ---
.PHONY: all setup up down logs shell test format format-check lint lint-check clean help

# --- プロジェクトセットアップ --------------------------------------------------
setup:
	@echo "--- セットアップ開始: (.env.dev) 環境 ---"
	@echo "Python依存関係をインストール中..."
	@poetry install
	@echo "--- セットアップ完了 ---"


# --- Dockerコマンド ------------------------------------------------
up:
	@echo "--- Dockerコンテナを起動中... ---"
	@ln -sf .env.$(ENV) .env
	$(DOCKER_COMPOSE) up --build -d
	@echo "--- Dockerコンテナがバックグラウンドで実行中です ---"

down:
	@echo "--- Dockerコンテナを停止・削除中... ---"
	@ln -sf .env.$(ENV) .env
	$(DOCKER_COMPOSE) down
	@echo "--- Dockerコンテナが停止しました ---"

logs:
	@echo "--- Dockerコンテナのログを表示中... (Ctrl+Cで終了) ---"
	@ln -sf .env.$(ENV) .env
	$(DOCKER_COMPOSE) logs -f

shell:
	@echo "--- webコンテナのシェルに接続中... ---"
	@if [ -z "$$($(DOCKER_COMPOSE) ps -q web)" ] || [ "$$($(DOCKER_COMPOSE) ps -q web | xargs docker inspect -f '{{.State.Status}}')" != "running" ]; then \
		echo "Error: web container is not running. Please run 'make up' first."; \
		exit 1; \
	fi
	@ln -sf .env.$(ENV) .env
	$(DOCKER_COMPOSE) exec web /bin/bash
	@echo "--- シェルセッションを終了しました ---"


# --- コード品質とテスト -----------------------------------------
test:
	@echo "--- テストを実行中 (ENV=$(ENV))... ---"
	@ln -sf .env.$(ENV) .env
	poetry run pytest
	@echo "--- テスト完了 ---"

format:
	@echo "--- コードをフォーマット中... (black, ruff) ---"
	poetry run black .
	poetry run ruff check . --fix
	@echo "--- フォーマット完了 ---"

format-check:
	@echo "--- コードフォーマットをチェック中... (black) ---"
	poetry run black --check .
	@echo "--- Blackフォーマットチェック完了 ---"

lint:
	@echo "--- リントを実行中... (ruff) ---"
	poetry run ruff check .
	@echo "--- リント完了 ---"

lint-check:
	@echo "--- リントをチェック中... (ruff) ---"
	poetry run ruff check .
	@echo "--- Ruffリントチェック完了 ---"


# --- 一般的なコマンド ----------------------------------------------
all: setup up

clean:
	@echo "--- クリーンアップ中... ---"
	@rm -f .env
	@echo "--- .env シンボリックリンクを削除しました ---"


# --- ヘルプ -----------------------------------------------------------
help:
	@echo "利用可能なMakefileコマンド:"
	@echo ""
	@echo "  一般的なコマンド"
	@echo "    all            - 'setup'と'up'を実行し、開発環境を完全に起動します。"
	@echo "    clean          - 生成されたファイル（.envシンボリックリンク）を削除します。"
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
	@echo "    test           - poetry環境でpytestを実行します。 'ENV'変数で環境を指定できます (例: make test ENV=dev)。"
	@echo "    format         - BlackとRuffを使用してコードスタイルを自動で修正します。"
	@echo "    format-check   - Blackでコードスタイルが正しいかチェックします。"
	@echo "    lint           - Ruffでリントを実行します。"
	@echo "    lint-check     - Ruffでリントエラーがないかチェックします。"
	@echo ""
	@echo "  使い方:"
	@echo "    make up        - 開発環境でコンテナを起動します。"
	@echo "    make up ENV=prod - 本番環境でコンテナを起動します。"
	@echo ""
