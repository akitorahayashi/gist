# ==============================================================================
# Makefile for Project Automation
#
# Provides a unified interface for common development tasks, abstracting away
# the underlying Docker Compose commands for a better Developer Experience (DX).
#
# Inspired by the self-documenting Makefile pattern.
# ==============================================================================

# Default target executed when 'make' is run without arguments
.DEFAULT_GOAL := help

# ==============================================================================
# Sudo Configuration
#
# Allows running Docker commands with sudo when needed (e.g., in CI environments).
# Usage: make up SUDO=true
# ==============================================================================
SUDO_PREFIX :=
ifeq ($(SUDO),true)
    SUDO_PREFIX := sudo
endif

DOCKER_CMD := $(SUDO_PREFIX) docker

# Define the project name based on the directory name for dynamic container naming
PROJECT_NAME := $(shell basename $(CURDIR))

# Define project names for different environments
DEV_PROJECT_NAME := $(PROJECT_NAME)-dev
PROD_PROJECT_NAME := $(PROJECT_NAME)-prod
TEST_PROJECT_NAME := $(PROJECT_NAME)-test

# ==============================================================================
# Help
# ==============================================================================

.PHONY: all
all: help ## Default target

.PHONY: help
help: ## Show this help message
	@echo "Usage: make [target] [VAR=value]"
	@echo "Options:"
	@echo "  \033[36m%-15s\033[0m %s" "SUDO=true" "Run docker commands with sudo (e.g., make up SUDO=true)"
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ==============================================================================
# Environment Setup
# ==============================================================================

.PHONY: setup
setup: ## Initialize project: install dependencies and create .env file
	@echo "Installing python dependencies with Poetry..."
	@poetry install --no-root
	@echo "Creating environment file..."
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..." ; \
		cp .env.example .env; \
	else \
		echo ".env already exists. Skipping creation."; \
	fi
	@echo "Setup complete."

# ==============================================================================
# Development Environment Commands
# ==============================================================================

.PHONY: up
up: ## Start all development containers in detached mode
	@echo "Starting up development services..."
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) up -d

.PHONY: down
down: ## Stop and remove all development containers
	@echo "Shutting down development services..."
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) down --remove-orphans

.PHONY: up-prod
up-prod: ## Start all production-like containers
	@echo "Starting up production-like services..."
	$(DOCKER_CMD) compose -f docker-compose.yml --project-name $(PROD_PROJECT_NAME) up -d --build --pull always --remove-orphans

.PHONY: down-prod
down-prod: ## Stop and remove all production-like containers
	@echo "Shutting down production-like services..."
	$(DOCKER_CMD) compose -f docker-compose.yml --project-name $(PROD_PROJECT_NAME) down --remove-orphans


.PHONY: rebuild
rebuild: ## Rebuild the web service without cache and restart it
	@echo "Rebuilding web service with --no-cache..."
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) build --no-cache web
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) up -d web

.PHONY: logs
logs: ## View the logs for the development web service
	@echo "Following logs for the dev web service..."
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) logs -f web

.PHONY: shell
shell: ## Open a shell inside the running development web container
	@echo "Opening shell in dev web container..."
	@$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) exec web /bin/bash || \
		(echo "Failed to open shell. Is the container running? Try 'make up'" && exit 1)

# ==============================================================================
# Django Management Commands
# ==============================================================================

.PHONY: makemigrations
makemigrations: ## Create new migration files
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) exec web poetry run python manage.py makemigrations

.PHONY: migrate
migrate: ## Run database migrations against the development database
	@echo "Running database migrations for dev environment..."
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) exec web poetry run python manage.py migrate

.PHONY: superuser
superuser: ## Create a Django superuser
	@echo "Creating superuser..."
	$(DOCKER_CMD) compose -f docker-compose.yml -f docker-compose.dev.override.yml --project-name $(DEV_PROJECT_NAME) exec web poetry run python manage.py createsuperuser

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
unit-test: ## Run the fast, database-independent unit tests locally
	@echo "Running unit tests..."
	@poetry run python -m pytest tests/unit -s

.PHONY: build-test
build-test: ## Build Docker image for testing without leaving artifacts
	@echo "Building Docker image for testing (clean build)..."
	@TEMP_IMAGE_TAG=$$(date +%s)-build-test; \
	$(DOCKER_CMD) build --target production --tag temp-build-test:$$TEMP_IMAGE_TAG . && \
	echo "Build successful. Cleaning up temporary image..." && \
	$(DOCKER_CMD) rmi temp-build-test:$$TEMP_IMAGE_TAG || true

.PHONY: e2e-test
e2e-test: ## Run end-to-end tests against a live application stack
	@echo "Running end-to-end tests..."
	@poetry run python -m pytest tests/e2e -s