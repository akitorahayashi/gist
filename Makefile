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
# For development, it uses docker-compose.override.yml by default.
DEV_COMPOSE := sudo docker compose --project-name $(PROJECT_NAME)-dev
# For production, it explicitly uses only the base docker-compose.yml.
PROD_COMPOSE := sudo docker compose -f docker-compose.yml --project-name $(PROJECT_NAME)-prod

# Default target to run when make is called without arguments
.DEFAULT_GOAL := help

# --- Environment Setup ---
.PHONY: setup
setup: ## Install dependencies and create .env files from .env.example
	@echo "Installing python dependencies with Poetry..."
	@poetry install
	@if [ ! -f .env.dev ]; then \
		echo "Creating .env.dev from .env.example..."; \
		cp .env.example .env.dev; \
	fi
	@if [ ! -f .env.prod ]; then \
		echo "Creating .env.prod from .env.example..."; \
		cp .env.example .env.prod; \
	fi
	@echo "Setup complete. Dependencies are installed and .env files are ready."

# --- Development Environment Commands ---
.PHONY: up
up: ## Build images and start development containers
	@ln -sf .env.dev .env
	@echo "Starting up DEVELOPMENT containers..."
	@$(DEV_COMPOSE) up --build -d

.PHONY: down
down: ## Stop and remove development containers
	@ln -sf .env.dev .env
	@echo "Stopping DEVELOPMENT containers..."
	@$(DEV_COMPOSE) down --remove-orphans

.PHONY: rebuild
rebuild: ## Rebuild dev services, pulling base images, without cache, and restart
	@ln -sf .env.dev .env
	@echo "Rebuilding all DEVELOPMENT services with --no-cache and --pull..."
	@$(DEV_COMPOSE) up -d --build --no-cache --pull always

.PHONY: logs
logs: ## Show and follow development container logs
	@ln -sf .env.dev .env
	@echo "Showing DEVELOPMENT logs..."
	@$(DEV_COMPOSE) logs -f

.PHONY: shell
shell: ## Start a shell inside the development 'web' container
	@ln -sf .env.dev .env
	@$(DEV_COMPOSE) ps --status=running --services | grep -q '^web$$' || { echo "Error: web container is not running. Please run 'make up' first." >&2; exit 1; }
	@echo "Connecting to DEVELOPMENT 'web' container shell..."
	@$(DEV_COMPOSE) exec web /bin/bash

# --- Production-like Environment Commands ---
.PHONY: up-prod
up-prod: ## Build images and start production-like containers
	@ln -sf .env.prod .env
	@echo "Starting up PRODUCTION-like containers..."
	@$(PROD_COMPOSE) up -d --build

.PHONY: down-prod
down-prod: ## Stop and remove production-like containers
	@ln -sf .env.prod .env
	@echo "Shutting down PRODUCTION-like containers..."
	@$(PROD_COMPOSE) down --remove-orphans

# --- Database and Application Commands ---
.PHONY: migrate
migrate: ## [DEV] Run database migrations
	@ln -sf .env.dev .env
	@echo "Running DEVELOPMENT database migrations..."
	@$(DEV_COMPOSE) exec web poetry run python manage.py migrate

.PHONY: makemigrations
makemigrations: ## [DEV] Create new migration files
	@ln -sf .env.dev .env
	@$(DEV_COMPOSE) exec web poetry run python manage.py makemigrations

.PHONY: superuser
superuser: ## [DEV] Create a Django superuser
	@ln -sf .env.dev .env
	@echo "Creating DEVELOPMENT superuser..."
	@$(DEV_COMPOSE) exec web poetry run python manage.py createsuperuser

.PHONY: migrate-prod
migrate-prod: ## [PROD] Run database migrations in the production-like environment
	@ln -sf .env.prod .env
	@echo "Running PRODUCTION-like database migrations..."
	@$(PROD_COMPOSE) exec web python manage.py migrate

.PHONY: superuser-prod
superuser-prod: ## [PROD] Create a Django superuser in the production-like environment
	@ln -sf .env.prod .env
	@echo "Creating PRODUCTION-like superuser..."
	@$(PROD_COMPOSE) exec web python manage.py createsuperuser

# --- Code Quality and Testing ---
.PHONY: test
test: ## Run the test suite using the host's poetry environment
	@ln -sf .env.dev .env
	@echo "Running test suite on host..."
	poetry run pytest

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

# --- Cleanup ---
.PHONY: clean
clean: ## Remove all generated files and stop all containers
	@echo "Cleaning up project..."
	@$(DEV_COMPOSE) down -v --remove-orphans
	@$(PROD_COMPOSE) down -v --remove-orphans
	@rm -f .env
	@echo "Cleanup complete."

# --- Help ---
.PHONY: help
help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "; OFS="t"} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-25s\033[0m %sn", $$1, $$2}' $(MAKEFILE_LIST)
