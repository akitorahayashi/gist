# CLAUDE.md - Testing Strategy and Guidelines

This document provides detailed rules and procedures for writing and running automated tests in this project. It expands upon the testing strategy outlined in the root `CLAUDE.md`.

## 1. Module Roles and Responsibilities

The `tests/` directory is the central location for all automated tests. Its primary responsibility is to ensure the correctness, reliability, and quality of the application code through a structured, multi-layered testing approach. This includes verifying individual components in isolation (unit tests) and validating the behavior of the fully integrated system (end-to-end tests).

## 2. Technology Stack and Environment

- **Test Runner:** All tests must be written for and executed with **Pytest**.
- **Core Libraries:**
  - `pytest`: The primary test framework.
  - `pytest-django`: For Django-specific testing utilities and database integration.
  - `pytest-mock`: Provides a fixture for easy mocking of objects.
  - `httpx`: The required client for making HTTP requests in end-to-end tests.
- **E2E Test Environment:** End-to-end tests are run against a live application stack managed by Docker Compose, using the definitions in `docker-compose.test.override.yml`.

## 3. Architectural Principles and File Structure

- **Strict Separation of Test Types:** Maintain a clear separation between unit and end-to-end tests.
  - `tests/unit/`: This directory is exclusively for unit tests.
  - `tests/e2e/`: This directory is exclusively for end-to-end tests.
- **Mirror Application Structure:** The directory structure within `tests/unit/` must mirror the application's structure in `apps/`. For example, tests for `apps/gist/services/scraping_service.py` must be located at `tests/unit/services/test_scraping_service.py`.
- **Test File Naming:** All test files must be named using the `test_*.py` pattern, as configured in `pyproject.toml`.

## 4. Coding Standards and Style Guide

- **Code Style:** All test code must adhere to the project's **Black** and **Ruff** configurations defined in the root `pyproject.toml`.
- **Test Naming:** Test functions must be named descriptively to reflect what they are testing (e.g., `test_scrape_raises_error_on_private_host`).
- **Assertions:** Use Pytest's plain `assert` statements for all assertions.
- **Fixtures:** Use Pytest fixtures for setup and teardown logic. Define reusable fixtures in a `conftest.py` file within the relevant test directory.

## 5. Critical Business Logic and Invariants

- **Isolation of Unit Tests:** Unit tests must be completely isolated. They must **never** make real network requests, access the filesystem, or interact with a real database. Always use mocks to simulate these interactions.
- **E2E Test Environment Management:** The E2E test environment lifecycle (startup, health check, shutdown) is managed globally by the `e2e_setup` fixture in `tests/e2e/conftest.py`. Individual E2E tests must **never** attempt to manage Docker containers themselves.
- **Stateless Tests:** All tests must be independent and stateless. The success or failure of one test must not affect another.

## 6. Testing Strategy and Procedures

### Unit Testing

- **Objective:** To test a single function, class, or module in isolation. Tests must be fast and reliable.
- **Execution Command:** Always run unit tests using the command `make unit-test`.
- **Mocking External Dependencies:**
  - For external modules or classes (like `requests`), use `@patch` from `unittest.mock`. Refer to `tests/unit/services/test_scraping_service.py` for examples.
  - For objects you control, use `MagicMock` or the `mocker` fixture from `pytest-mock`.
- **Mocking Django Settings:** Use the `@override_settings` decorator from `django.test` to modify Django settings for a specific test case. Refer to `tests/unit/services/test_summarization_service.py`.

### End-to-End (E2E) Testing

- **Objective:** To test the application as a whole, from the Nginx entrypoint to the Django backend, simulating real user interaction.
- **Execution Command:** Always run E2E tests using the command `make e2e-test`.
- **HTTP Client:** Use the `httpx` library to make asynchronous requests to the running application.
- **Test URLs:** Construct test URLs using the `HOST_BIND_IP` and `TEST_PORT` environment variables to target the Nginx container managed by the E2E test setup.

## 7. CI Process

- **Integration:** The test suites defined here are automatically executed by GitHub Actions on every push and pull request to the `main` branch.
- **Execution:** The CI workflow invokes the `make unit-test` and `make e2e-test` targets to run the tests in a clean environment.

## 8. Don'ts

- **Never** mix unit and E2E test concerns in the same file or directory.
- **Never** add E2E tests that depend on external, third-party services that are not part of this repository's Docker Compose stack.
- **Never** write tests without clear `assert` statements that validate the expected outcome.
- **Never** hardcode URLs, ports, or other configuration in tests. Use environment variables or fixtures to provide this information.
- **Never** introduce `time.sleep()` calls in tests to wait for events. For E2E tests, rely on the health check in `conftest.py`.