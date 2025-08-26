# ==============================================================================
# Makefile for Gist Summarizer
#
# This Makefile provides a set of commands to manage the development and
# production-like environments for the Gist Summarizer application.
# ==============================================================================

# --- Variables ---
# Project name, derived from the current directory name
PROJECT_NAME := $(shell basename $(CURDIR))

# Docker Compose command wrappers
# Use --env-file to explicitly specify environment configuration, avoiding issues with `sudo` and symlinks.
DEV_COMPOSE := sudo docker compose --env-file .env.dev --project-name $(PROJECT_NAME)-dev
PROD_COMPOSE := sudo docker compose -f docker-compose.yml --env-file .env.prod --project-name $(PROJECT_NAME)-prod
TEST_COMPOSE := sudo docker compose -f docker-compose.yml --env-file .env.test --project-name $(PROJECT_NAME)-test

# Default target to run when make is called without arguments
.DEFAULT_GOAL := help

# --- Environment Setup ---
.PHONY: setup
setup: ## Install dependencies and create .env files from .env.example
	@echo "Installing python dependencies with Poetry..."
	@poetry install
	@for env in dev prod test; do \
		if [ ! -f .env.$$env ]; then \
			echo "Creating .env.$$env from .env.example..."; \
			cp .env.example .env.$$env; \
		fi; \
	done
	@echo "Setup complete. Dependencies are installed and .env files are ready."

# --- Development Environment Commands ---
.PHONY: up
up: ## Build images and start development containers
	@echo "Starting up DEVELOPMENT containers..."
	@$(DEV_COMPOSE) up --build -d

.PHONY: down
down: ## Stop and remove development containers
	@echo "Stopping DEVELOPMENT containers..."
	@$(DEV_COMPOSE) down --remove-orphans

.PHONY: rebuild
rebuild: ## Rebuild dev services, pulling base images, without cache, and restart
	@echo "Rebuilding all DEVELOPMENT services with --no-cache and --pull..."
	@$(DEV_COMPOSE) up -d --build --no-cache --pull always

.PHONY: logs
logs: ## Show and follow development container logs
	@echo "Showing DEVELOPMENT logs..."
	@$(DEV_COMPOSE) logs -f

.PHONY: shell
shell: ## Start a shell inside the development 'web' container
	@$(DEV_COMPOSE) ps --status=running --services | grep -q '^web$$' || { echo "Error: web container is not running. Please run 'make up' first." >&2; exit 1; }
	@echo "Connecting to DEVELOPMENT 'web' container shell..."
	@$(DEV_COMPOSE) exec web /bin/bash

# --- Production-like Environment Commands ---
.PHONY: up-prod
up-prod: ## Build images and start production-like containers
	@echo "Starting up PRODUCTION-like containers..."
	@$(PROD_COMPOSE) up -d --build

.PHONY: down-prod
down-prod: ## Stop and remove production-like containers
	@echo "Shutting down PRODUCTION-like containers..."
	@$(PROD_COMPOSE) down --remove-orphans

# --- Database and Application Commands ---
.PHONY: migrate
migrate: ## [DEV] Run database migrations
	@echo "Running DEVELOPMENT database migrations..."
	@$(DEV_COMPOSE) exec web poetry run python manage.py migrate

.PHONY: makemigrations
makemigrations: ## [DEV] Create new migration files
	@$(DEV_COMPOSE) exec web poetry run python manage.py makemigrations

.PHONY: superuser
superuser: ## [DEV] Create a Django superuser
	@echo "Creating DEVELOPMENT superuser..."
	@$(DEV_COMPOSE) exec web poetry run python manage.py createsuperuser

.PHONY: migrate-prod
migrate-prod: ## [PROD] Run database migrations in the production-like environment
	@echo "Running PRODUCTION-like database migrations..."
	@$(PROD_COMPOSE) exec web python manage.py migrate

.PHONY: superuser-prod
superuser-prod: ## [PROD] Create a Django superuser in the production-like environment
	@echo "Creating PRODUCTION-like superuser..."
	@$(PROD_COMPOSE) exec web python manage.py createsuperuser

# --- Code Quality and Testing ---
.PHONY: test
test: ## Run the test suite using the .env.test environment
	@echo "Running test suite with .env.test..."
	@poetry run pytest

.PHONY: format
format: ## Format the code using Black and Ruff
	@echo "Formatting code with Black and Ruff..."
	poetry run black .
	poetry run ruff check . --fix

.PHONY: format-check
format-check: ## Check if the code is formatted with Black
	@echo "Checking code format with Black..."
	poetry run black --check .

.PHONY: lint
lint: ## Lint the code with Ruff
	@echo "Linting code with Ruff..."
	poetry run ruff check .

.PHONY: lint-check
lint-check: ## Check the code for issues with Ruff
	@echo "Checking code with Ruff..."
	poetry run ruff check .

.PHONY: e2e-test
e2e-test: ## [E2E] Build, run tests against live containers, and cleanup
	@echo "Running E2E test..."
	@trap "echo '--- E2E test cleanup ---'; echo '--- Container logs: ---'; $(TEST_COMPOSE) logs; echo '--- Shutting down containers: ---'; $(TEST_COMPOSE) down -v --remove-orphans" EXIT
	@$(TEST_COMPOSE) up -d --build
	@echo "Waiting for services to be ready..."
	@if ! . ./.env.test && timeout 60s bash -c '\
		until curl -s -o /dev/null -w "%{http_code}" http://$$HOST_BIND_IP:$$HOST_PORT/ | grep -q 200; \
		do \
			echo "Service not ready, retrying in 5 seconds..."; \
			sleep 5; \
		done' > /dev/null 2>&1; then \
		echo "E2E test failed: Service did not become ready in 60 seconds." >&2; \
		exit 1; \
	fi
	@echo "Services are ready. E2E test successful."

# --- Cleanup ---
.PHONY: clean
clean: ## Remove all generated files and stop all containers
	@echo "Cleaning up project..."
	@$(DEV_COMPOSE) down -v --remove-orphans
	@$(PROD_COMPOSE) down -v --remove-orphans
	@echo "Cleanup complete."

# --- Help ---
.PHONY: help
help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS=":.*?## "; OFS="\t"} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
