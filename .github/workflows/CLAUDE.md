# CLAUDE.md - CI/CD Workflows Constitution

This document defines the architecture, principles, and rules for all GitHub Actions workflows in this project. All workflow files (`.yml`) in this directory must adhere to these guidelines.

## 1. Module Roles and Responsibilities

The `.github/workflows/` directory is responsible for all Continuous Integration (CI) and Continuous Deployment (CD) automation. Its mission is to provide a reliable, fast, and maintainable pipeline that:
1.  Validates code quality and formatting.
2.  Executes the full test suite to prevent regressions.
3.  Automates the building and publishing of the production Docker image.

## 2. Technology Stack and Environment

-   **Automation Platform:** All workflows must be implemented using **GitHub Actions**.
-   **Configuration Language:** All workflows must be written in **YAML**.
-   **Core Actions:** Utilize official and community-vetted actions. Key actions include:
    -   `actions/checkout@v4`
    -   `actions/setup-python@v5`
    -   `docker/setup-buildx-action@v3`
    -   `docker/login-action@v3`
    -   `docker/build-push-action@v5`
-   **Execution Abstraction:** Workflows must delegate complex commands to the root `Makefile`. The YAML files should define *what* to do, while the `Makefile` defines *how* to do it.

## 3. Architectural Principles and File Structure

This project uses a modular, reusable workflow architecture to ensure maintainability and clarity.

-   **Modularity:** Use `workflow_call` to create reusable, single-purpose workflows.
-   **Orchestration:** A primary workflow (`ci-pipeline.yml`) orchestrates the execution of reusable workflows for standard CI checks.
-   **Separation of Concerns:** Keep CI (testing, linting) and CD (publishing artifacts) in separate, independently triggered workflows.

-   **File Responsibilities:**
    -   `ci-pipeline.yml`: The main CI orchestrator. It triggers on pushes and pull requests to `main` and calls other workflows. Its purpose is to validate code changes.
    -   `format-and-lint.yml`: A reusable workflow responsible for checking code formatting and linting via `make lint`.
    -   `run-tests.yml`: A reusable workflow responsible for running the entire test suite. It uses a matrix strategy to run unit, build, and e2e tests in parallel.
    -   `build-and-push.yml`: The CD workflow. It triggers only on pushes to `main` and is responsible for building and publishing the production Docker image to GHCR.

## 4. Coding Standards and Style Guide

-   **Use `Makefile` Targets:** Always execute tasks like linting, testing, or building via `make` targets inside `run:` steps. Do not write complex multi-line scripts directly in the YAML files.
-   **Pin Action Versions:** Always pin GitHub Actions to a major version (e.g., `actions/checkout@v4`) to ensure stability.
-   **Job Naming:** Give jobs and steps clear, descriptive `name` attributes.
-   **Reusable Workflows:** When adding a new, distinct stage to the CI/CD process, create it as a new reusable workflow and call it from the appropriate orchestrator.

## 5. Critical Business Logic and Invariants

-   **CI Gate:** The `ci-pipeline.yml` workflow must be configured as a required status check for the `main` branch. All its jobs must pass before a pull request can be merged.
-   **Deployment Trigger:** The `build-and-push.yml` workflow must **only** be triggered on a `push` to the `main` branch. It must never be triggered by pull requests.
-   **Production Artifacts:** The `build-and-push.yml` workflow must build the `production` target of the multi-stage `Dockerfile` to ensure a lean and secure final image.
-   **Dependency Consistency:** All workflows that run Python code must use `poetry install --no-root` to install dependencies as defined in `poetry.lock`.

## 6. Testing Strategy and Procedures

-   **CI Implementation:** The `run-tests.yml` workflow is the CI implementation of the project's testing strategy.
-   **Parallel Execution:** The testing workflow uses a `matrix` strategy to run `unit-test`, `build-test`, and `e2e-test` jobs in parallel to provide faster feedback.
-   **Test Rules Reference:** These workflows execute the tests, but the rules for *how* to write those tests are defined in `@tests/CLAUDE.md`.

## 7. CI Process

### CI Pipeline (`ci-pipeline.yml`)

-   **Trigger:** On `push` or `pull_request` to the `main` branch.
-   **Purpose:** To validate the quality and correctness of proposed changes.
-   **Jobs:**
    1.  `format-and-lint`: Calls `format-and-lint.yml`.
    2.  `run-tests`: Calls `run-tests.yml`.

### Deployment Pipeline (`build-and-push.yml`)

-   **Trigger:** On `push` to the `main` branch.
-   **Purpose:** To continuously build and deploy the latest version of the application as a Docker image.
-   **Steps:**
    1.  Log in to GitHub Container Registry (GHCR).
    2.  Build the `production` stage of the `Dockerfile`.
    3.  Push the tagged image (`:latest`) to GHCR.

## 8. Don'ts

-   **Never** embed secrets directly in workflow files. Use GitHub repository secrets.
-   **Never** add complex logic (e.g., conditional execution, long scripts) directly into `run:` steps. Abstract this logic into the `Makefile`.
-   **Never** configure the `build-and-push.yml` workflow to run on pull requests to avoid building and pushing unnecessary images.
-   **Never** create monolithic workflow files. Always separate distinct responsibilities into reusable workflows.