# CLAUDE.md - Gist Summarizer Project Constitution

## 1. Project Overview and Mission

This project is a Django-based web application. Its primary mission is to scrape the main content of a public web page from a given URL and generate a concise summary using an external Large Language Model (LLM) API. The application must provide a simple user interface for URL input and display the generated summary and scraped content.

## 2. Technology Stack and Environment

- **Language:** Python 3.12.
- **Backend Framework:** Django 5.2.
- **Package Management:** Use Poetry for dependency management. All dependencies are defined in `pyproject.toml`.
- **Web Server Gateway Interface (WSGI):** Gunicorn is the production WSGI server.
- **Containerization:** The application must be fully containerized using Docker and Docker Compose.
  - **Base Image:** Use `python:3.12-slim` for production builds.
  - **Web Proxy:** Use Nginx as a reverse proxy in front of the Gunicorn server.
- **Development Environment:**
  - Use the `Makefile` for all common development tasks (e.g., `make up`, `make down`, `make test`).
  - Configure environment variables by creating a `.env` file from `.env.example`.

## 3. Architectural Principles and File Structure

This project follows a standard Django structure with a clear separation of concerns, centered around a **View-Service-Client** architecture within the `apps/gist` application.

- **Configuration:** Project-level settings and URL configurations are located in the `config/` directory.
- **Applications:** The primary application logic resides in `apps/gist/`. For a detailed breakdown of this application's internal architecture, component responsibilities, and logic, see **`@apps/gist/CLAUDE.md`**.
- **High-Level Structure:**
    ```text
    .
    ├── apps/gist/      # Core Django application logic
    ├── config/         # Django project configuration
    ├── tests/          # All automated tests
    ├── .github/workflows/ # CI/CD pipelines
    ├── Dockerfile      # Multi-stage Docker build
    ├── Makefile        # Development task runner
    └── pyproject.toml  # Dependencies and tool configuration
    ```


## 4. Coding Standards and Style Guide

- **Formatting:** Strictly use **Black** for all Python code formatting. Run `make format` before committing.
- **Linting:** Strictly use **Ruff** for linting. All code must pass `make lint` checks without errors.
- **Configuration:** All formatter and linter rules are defined in `pyproject.toml`. Do not alter these rules.
- **Imports:** Use Ruff's import sorting (`I` rule in `pyproject.toml`).

## 5. Critical Business Logic and Invariants

- **URL Validation:** Before scraping, always validate incoming URLs to ensure the scheme is `http` or `https` and that the URL does not resolve to a private IP address, preventing SSRF attacks.
- **Summarization Prompt:** All summarization requests to the LLM must use the specific prompt structure defined in `SummarizationService._build_prompt` to ensure consistent output.
- **Error Handling:** The main view (`scrape_page`) must handle `ValueError` from user input, `SummarizationServiceError` from the summarization service, and generic `Exception` types gracefully, logging details and providing clear user feedback.
- **Placeholder for Additional Business Logic:**
- `[Human input required]: Please add any other critical business rules or invariants here. For example, are there specific domains that should be blacklisted from scraping?`

## 6. Testing Strategy and Procedures

- **Framework:** Use **Pytest** as the sole testing framework for the project.
- **Test Types:** The project maintains a multi-layered testing strategy, executed via `Makefile` commands:
  1.  **Unit Tests (`make unit-test`):** Fast, isolated tests for individual components.
  2.  **Build Test (`make build-test`):** Verifies the production Docker image builds successfully.
  3.  **End-to-End Tests (`make e2e-test`):** Validates the entire application stack.
- **Detailed Guidelines:** This document provides a high-level overview. For detailed rules on writing tests, mocking strategies, file structure, and test execution, always refer to **`@tests/CLAUDE.md`**.

## 7. CI/CD Process

- **Provider:** All CI/CD processes are run using **GitHub Actions**.
- **Pipeline Overview:** The pipeline automatically validates code quality, runs all tests, and deploys the application by building and pushing a Docker image to GHCR.
- **Detailed Guidelines:** This section is a summary. For a comprehensive explanation of the CI/CD workflows, job responsibilities, triggers, and architectural principles, always refer to **`@.github/workflows/CLAUDE.md`**.

## 8. Don'ts

- **Never** place business logic directly in `views.py`. Always use the service layer as defined in `@apps/gist/CLAUDE.md`.
- **Never** hardcode configuration values. Use environment variables loaded via `config/settings.py`.
- **Never** commit `.env` files or other secrets to the repository.
- **Never** disable the SSRF protection in `ScrapingService`.
- **Never** bypass the `Makefile` for running tests or linters, especially in the CI environment.
- **Never** add dependencies without updating `pyproject.toml`.