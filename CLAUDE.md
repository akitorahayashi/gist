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

This project follows a standard Django structure with a clear separation of concerns.

- **Configuration:** All project-level configurations (settings, root URLconf) reside in the `config/` directory.
- **Applications:** All Django applications must be placed within the `apps/` directory. The primary application is `apps/gist`.
- **Service Layer:** Decouple business logic from the view layer.
  - Implement complex business logic within service classes in the `apps/gist/services/` directory.
  - `ScrapingService`: Responsible for fetching and parsing web page content.
  - `SummarizationService`: Responsible for interacting with the LLM and generating summaries.
- **Client Layer:** Encapsulate communication with external APIs.
  - Implement clients for external services in the `apps/gist/clients/` directory.
  - `LlmApiClient`: The dedicated client for all communication with the LLM API.
- **File Structure:**

    ```text
    .
    ├── apps/
    │   └── gist/
    │       ├── clients/      # External API clients
    │       │   └── llm_api_client.py
    │       ├── services/     # Business logic
    │       │   ├── scraping_service.py
    │       │   └── summarization_service.py
    │       ├── templates/    # HTML templates
    │       ├── views.py      # View logic
    │       └── urls.py       # App-specific URLs
    ├── config/             # Django project configuration
    ├── tests/
    │   ├── unit/           # Unit tests
    │   └── e2e/            # End-to-end tests
    ├── Dockerfile          # Multi-stage Docker build
    ├── docker-compose.yml  # Production Docker Compose setup
    ├── Makefile            # Development task runner
    └── pyproject.toml      # Dependencies and tool configuration
    ```

- **Static Context:** For detailed testing guidelines, refer to `@tests/CLAUDE.md`.

## 4. Coding Standards and Style Guide

- **Formatting:** Strictly use **Black** for all Python code formatting. Run `make format` before committing.
- **Linting:** Strictly use **Ruff** for linting. All code must pass `make lint` checks without errors.
- **Configuration:** All formatter and linter rules are defined in `pyproject.toml`. Do not alter these rules without team consensus.
- **Imports:** Use Ruff's import sorting (`I` rule in `pyproject.toml`). Group imports according to standard conventions (standard library, third-party, local application).

## 5. Critical Business Logic and Invariants

- **URL Validation:** Before scraping, always validate incoming URLs using `ScrapingService.validate_url`. This function must enforce two invariants:
1.  The URL scheme must be either `http` or `https`.
2.  The URL must not resolve to a private, reserved, loopback, or otherwise non-public IP address to prevent Server-Side Request Forgery (SSRF) attacks.
- **Summarization Prompt:** All summarization requests to the LLM must use the prompt structure defined in `SummarizationService._build_prompt`. The prompt must explicitly ask for a title and a bulleted list of key points in Japanese.
- **Error Handling:** In `apps/gist/views.py`, handle exceptions gracefully.
- For user input errors (`ValueError`), display the error message directly to the user.
- For service-specific errors (`SummarizationServiceError`), log the full exception and display a generic "service unavailable" message.
- For all other unexpected exceptions, log the full exception and display a generic "an error occurred" message.
- **Placeholder for Additional Business Logic:**
- `[Human input required]: Please add any other critical business rules or invariants here. For example, are there specific domains that should be blacklisted from scraping?`

## 6. Testing Strategy and Procedures

- **Framework:** Use **Pytest** as the sole testing framework.
- **Test Types:** The project maintains three distinct types of tests, which can be executed via the `Makefile`.
1.  **Unit Tests (`make unit-test`):**
    - Place all unit tests in the `tests/unit/` directory.
    - Unit tests must be fast, isolated, and must not depend on external services like databases or APIs. Use `pytest-mock` to mock dependencies.
2.  **Build Test (`make build-test`):**
    - This test verifies that the production Docker image can be built successfully. It does not run any application code.
3.  **End-to-End Tests (`make e2e-test`):**
    - Place all E2E tests in the `tests/e2e/` directory.
    - These tests validate the entire application stack by running it via `docker-compose.test.override.yml`.
- **Test Execution:** Always run the full test suite with `make test` before merging code.
- **Detailed Guidelines:** For more specific rules on writing tests, mocking strategies, and test data management, refer to `@tests/CLAUDE.md`.

## 7. CI Process

- **Provider:** All CI processes are run using **GitHub Actions**.
- **Workflows:** The CI pipeline is defined in `.github/workflows/ci-pipeline.yml` and consists of two main jobs:
1.  `format-and-lint`: Ensures all code adheres to the defined coding standards.
2.  `run-tests`: Executes the complete test suite (unit, build, and e2e tests).
- **Trigger:** The CI pipeline automatically runs on every push and pull request to the `main` branch.
- **Deployment:** A separate workflow (`.github/workflows/build-and-push.yml`) builds and pushes the production Docker image to GitHub Container Registry (GHCR) on every push to the `main` branch.

## 8. Don'ts

- **Never** place business logic directly in `views.py`. Always use the service layer.
- **Never** hardcode configuration values like API keys, model names, or URLs. Use environment variables and `config/settings.py`.
- **Never** commit `.env` files or other secrets to the repository.
- **Never** disable the SSRF protection in `ScrapingService`.
- **Never** bypass the `Makefile` for running tests or linters in the CI environment. Maintain it as the single source of truth for development tasks.
- **Never** add dependencies directly with `pip` or `poetry add`. All dependency changes must be reflected in `pyproject.toml`.