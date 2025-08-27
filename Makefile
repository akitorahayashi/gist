.DEFAULT_GOAL := help

PROJECT_NAME := $(shell basename $(CURDIR))
TEST_PROJECT_NAME := $(PROJECT_NAME)-test

# ==============================================================================
# Variables
# ==============================================================================

# Sudo Configuration - Allows running Docker commands with sudo when needed
SUDO_PREFIX :=
ifeq ($(SUDO),true)
    SUDO_PREFIX := sudo
endif

DOCKER_CMD := $(SUDO_PREFIX) docker

# Define VENV_PATH to ensure we use the correct python/pytest executable.
VENV_PATH := $(shell poetry env info --path)

# ==============================================================================
# Docker Commands
# ==============================================================================

DEV_COMPOSE := PROJECT_NAME=$(PROJECT_NAME) ENV=dev COMPOSE_PROJECT_NAME=$(PROJECT_NAME)-dev $(DOCKER_CMD) compose --project-name $(PROJECT_NAME)-dev
PROD_COMPOSE := PROJECT_NAME=$(PROJECT_NAME) ENV=prod COMPOSE_PROJECT_NAME=$(PROJECT_NAME)-prod $(DOCKER_CMD) compose -f docker-compose.yml --override-file /dev/null --project-name $(PROJECT_NAME)-prod
TEST_COMPOSE := PROJECT_NAME=$(PROJECT_NAME) ENV=test COMPOSE_PROJECT_NAME=$(PROJECT_NAME)-test $(DOCKER_CMD) compose --project-name $(PROJECT_NAME)-test

# ==============================================================================
# Help
# ==============================================================================

.PHONY: all
all: help ## Default target

.PHONY: help
help: ## Show this help message
	@echo "Usage: make [target] [VAR=value]"
	@echo ""
	@echo "Options:"
	@echo "  \033[36m%-25s\033[0m %s" "SUDO=true" "Run docker commands with sudo (e.g., make up SUDO=true)"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "; OFS=" "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ==============================================================================
# Environment Setup
# ==============================================================================

.PHONY: setup
setup: ## Install dependencies and create .env files from .env.example
	@echo "Installing python dependencies with Poetry..."
	@poetry install
	@echo "Creating .env files..."
	@for env in dev prod test; do \
		if [ ! -f .env.$$env ] && [ -f .env.example ]; then \
			echo "Creating .env.$$env from .env.example..."; \
			cp .env.example .env.$$env; \
		fi; \
	done
	@echo "Setup complete. Dependencies are installed and .env files are ready."

# ==============================================================================
# Development Environment Commands
# ==============================================================================

.PHONY: up
up: ## Build images and start dev containers
	@ln -sf .env.dev .env
	@echo "Building images and starting DEV containers..."
	@$(DEV_COMPOSE) up --build -d

.PHONY: down
down: ## Stop dev containers
	@ln -sf .env.dev .env
	@echo "Stopping DEV containers..."
	@$(DEV_COMPOSE) down --remove-orphans

.PHONY: up-prod
up-prod: ## Build images and start prod-like containers
	@ln -sf .env.prod .env
	@echo "Starting up PROD-like containers..."
	@$(PROD_COMPOSE) up -d --build

.PHONY: down-prod
down-prod: ## Stop prod-like containers
	@ln -sf .env.prod .env
	@echo "Shutting down PROD-like containers..."
	@$(PROD_COMPOSE) down --remove-orphans

.PHONY: up-test
up-test: ## Build images and start test containers
	@ln -sf .env.test .env
	@echo "Starting up TEST containers..."
	@$(TEST_COMPOSE) up -d --build

.PHONY: down-test
down-test: ## Stop test containers
	@ln -sf .env.test .env
	@echo "Shutting down TEST containers..."
	@$(TEST_COMPOSE) down --remove-orphans

.PHONY: rebuild
rebuild: ## Rebuild services, pulling base images, without cache, and restart
	@ln -sf .env.dev .env
	@echo "Rebuilding all DEV services with --no-cache and --pull..."
	@$(DEV_COMPOSE) up -d --build --no-cache --pull always

.PHONY: clean
clean: ## Remove all generated files and stop all containers
	@echo "Cleaning up project..."
	@$(DEV_COMPOSE) down -v --remove-orphans 2>/dev/null || true
	@$(PROD_COMPOSE) down -v --remove-orphans 2>/dev/null || true
	@$(TEST_COMPOSE) down -v --remove-orphans 2>/dev/null || true
	@echo "Cleanup complete."

.PHONY: logs
logs: ## Show and follow dev container logs
	@ln -sf .env.dev .env
	@echo "Showing DEV logs..."
	@$(DEV_COMPOSE) logs -f

.PHONY: shell
shell: ## Start a shell inside the dev 'web' container
	@ln -sf .env.dev .env
	@$(DEV_COMPOSE) ps --status=running --services | grep -q '^web$$' || { echo "Error: web container is not running. Please run 'make up' first." >&2; exit 1; }
	@echo "Connecting to DEV 'web' container shell..."
	@$(DEV_COMPOSE) exec web /bin/bash

# ==============================================================================
# Django Management Commands
# ==============================================================================

.PHONY: makemigrations
makemigrations: ## [DEV] Create new migration files
	@ln -sf .env.dev .env
	@$(DEV_COMPOSE) exec web poetry run python manage.py makemigrations

.PHONY: migrate
migrate: ## [DEV] Run database migrations
	@ln -sf .env.dev .env
	@echo "Running DEV database migrations..."
	@$(DEV_COMPOSE) exec web poetry run python manage.py migrate

.PHONY: superuser
superuser: ## [DEV] Create a Django superuser
	@ln -sf .env.dev .env
	@echo "Creating DEV superuser..."
	@$(DEV_COMPOSE) exec web poetry run python manage.py createsuperuser

.PHONY: migrate-prod
migrate-prod: ## [PROD] Run database migrations in production-like environment
	@ln -sf .env.prod .env
	@echo "Running PROD-like database migrations..."
	@$(PROD_COMPOSE) exec web python manage.py migrate

.PHONY: superuser-prod
superuser-prod: ## [PROD] Create a Django superuser in production-like environment
	@ln -sf .env.prod .env
	@echo "Creating PROD-like superuser..."
	@$(PROD_COMPOSE) exec web python manage.py createsuperuser

# ==============================================================================
# Code Quality
# ==============================================================================

.PHONY: format
format: ## Format code with Black and fix Ruff issues
	@echo "Formatting code with Black and Ruff..."
	@poetry run black .
	@poetry run ruff check . --fix

.PHONY: lint
lint: ## Check code format and lint issues
	@echo "Checking code format with Black..."
	@poetry run black --check .
	@echo "Checking code with Ruff..."
	@poetry run ruff check .

# ==============================================================================
# Testing
# ==============================================================================

.PHONY: test
test: unit-test build-test e2e-test ## Run the full test suite

.PHONY: unit-test
unit-test: ## Run unit tests
	@echo "Running unit tests..."
	@$(VENV_PATH)/bin/pytest tests/unit

.PHONY: build-test
build-test: ## Build Docker image and run smoke tests in clean environment
	@echo "Building Docker image and running smoke tests..."
	@if [ ! -f .env.test ]; then \
		echo "Creating .env.test from .env.example..."; \
		cp .env.example .env.test; \
	fi
	@$(DOCKER_CMD) compose --progress plain -f docker-compose.yml --env-file .env.test --project-name $(PROJECT_NAME)-build-test build --no-cache web
	@echo "Cleaning up build-test environment..."
	@$(DOCKER_CMD) compose -f docker-compose.yml --env-file .env.test --project-name $(PROJECT_NAME)-build-test down --remove-orphans --volumes 2>/dev/null || true

.PHONY: e2e-test
e2e-test: ## Run end-to-end tests against a live application stack
	@echo "Running end-to-end tests..."
	@$(VENV_PATH)/bin/pytest tests/e2e