# CLAUDE.md - Gist Application Constitution

This document outlines the architectural principles, logic, and rules for the `gist` Django application. All code within the `apps/gist/` directory must comply with these standards.

## 1. Module Roles and Responsibilities

The `gist` application is the core of this project. It is responsible for:
1.  Providing the user interface for URL submission.
2.  Orchestrating the business logic for scraping web content and generating summaries.
3.  Handling user input and rendering results or errors.

## 2. Technology Stack and Environment

This application exclusively uses the technologies defined in the root `pyproject.toml`. Key libraries utilized are:
-   **Django:** For handling web requests, responses, and template rendering.
-   **Requests:** Used within the client layer for making HTTP calls to the external LLM API.
-   **BeautifulSoup4:** Used within the service layer for parsing and cleaning HTML content.

## 3. Architectural Principles and File Structure

Adhere strictly to a **View-Service-Client** layered architecture to ensure separation of concerns.

-   **Views (`views.py`):**
    -   **Responsibility:** Act as the entry point for user requests. Orchestrate calls to the service layer. Handle high-level exceptions and prepare the context dictionary for the template.
    -   **Rule:** Must not contain any business logic (e.g., HTML parsing, API request construction).
-   **Service Layer (`services/`):**
    -   **Responsibility:** Contain all core business logic. Services should be stateless and reusable.
    -   `ScrapingService`: Encapsulates all logic for fetching, validating, and parsing web page content.
    -   `SummarizationService`: Encapsulates the logic for preparing text and orchestrating the call to the LLM via the client layer.
    -   **Rule:** Must never directly interact with Django's `request` or `response` objects.
-   **Client Layer (`clients/`):**
    -   **Responsibility:** Encapsulate all details of communicating with external APIs.
    -   `LlmApiClient`: The single point of contact for the external LLM API. It handles request formatting, authentication (if any), and network error handling.
    -   **Rule:** Clients should be specific to a single external service.
-   **Templates (`templates/`):**
    -   **Responsibility:** Contains only presentation logic for the UI.

## 4. Coding Standards and Style Guide

-   **Formatting & Linting:** All code must conform to the project's **Black** and **Ruff** configurations.
-   **Layer Decoupling:** Never pass the Django `request` object to the service or client layers. Pass only primitive data types (e.g., strings, integers) that the services require.
-   **Custom Exceptions:** Use custom, specific exceptions to communicate failures from services to the view layer. `SummarizationServiceError` is the canonical example.

## 5. Critical Business Logic and Invariants

-   **Scraping Logic (`ScrapingService`):**
    -   **URL Validation:** Before any request, the URL must be validated by `validate_url`. This check must reject non-`http`/`https` schemes and any hostname that resolves to a private or loopback IP address to prevent SSRF.
    -   **Content Cleaning:** The scraping process must remove the following tags from the HTML before text extraction: `script`, `style`, `header`, `footer`, `nav`, and `aside`.
-   **Summarization Logic (`SummarizationService`):**
    -   **Input Truncation:** Before summarization, truncate the input text to the character limit defined by `SUMMARY_MAX_CHARS` in Django settings.
    -   **Prompt Structure:** All calls to the LLM must use the exact, multi-line prompt format defined in the `_build_prompt` method to ensure consistent output quality.
-   **API Client Logic (`LlmApiClient`):**
    -   **Configuration:** The client must be initialized using `LLM_API_ENDPOINT` from Django settings. It will raise an `ImproperlyConfigured` error if this setting is missing.
    -   **Request Timeout:** All outgoing API requests must use a connect timeout of 10 seconds and a read timeout of 120 seconds.

## 6. Testing Strategy and Procedures

-   **Unit Test Coverage:** All public methods within the `services/` and `clients/` directories must have corresponding unit tests.
-   **Test Location:** Unit tests for this application's components must be placed in `tests/unit/`. The internal structure must mirror this application's structure (e.g., `tests/unit/services/`).
-   **Detailed Guidelines:** For detailed instructions on how to write tests, use mocks, and run the test suite, refer to the project's primary testing document: `@tests/CLAUDE.md`.

## 7. CI Process

-   **Validation:** All code within this application is automatically validated by the project's CI pipeline, as defined in `.github/workflows/`.
-   **Process:** The pipeline runs formatting checks (`make lint`) and the full test suite (`make test`) on every pull request to `main`.

## 8. Don'ts

-   **Never** put business logic (e.g., parsing, prompt engineering) directly in `views.py`. Delegate to a service.
-   **Never** make direct `requests.get` or `requests.post` calls from the view or service layers. Always use a dedicated client from the `clients/` directory.
-   **Never** catch low-level exceptions like `requests.RequestException` in the view layer. This must be handled in the client or service layer, which should then raise a more abstract, domain-specific exception.
-   **Never** add new database models (`models.py`) without first creating a corresponding `admin.py` registration and a clear plan for data migration.