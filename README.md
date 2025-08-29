# Gist Summarizer

## Overview

This project is a Django-based web application designed to scrape the content of a given web page and generate a concise summary using a Large Language Model (LLM) API.

It is built with modern development practices in mind, featuring:
- **Containerization**: The entire application is containerized using Docker, ensuring a consistent and reproducible environment for both development and production.
- **Developer Experience (DX)**: A comprehensive `Makefile` is provided to streamline common tasks such as setup, testing, and running the application.
- **CI/CD**: The repository is configured with GitHub Actions to automatically build and push a production-ready Docker image to the GitHub Container Registry (GHCR) upon pushes to the `main` branch.

## Tech Stack

The project utilizes the following key technologies and libraries:

- **Backend**: Django
- **Containerization**: Docker, Docker Compose
- **Web Server / Proxy**: Nginx, Gunicorn
- **Package Management**: Poetry
- **Web Scraping**: `requests`, `BeautifulSoup4`
- **Testing**: Pytest, pytest-django, pytest-mock
- **Code Quality**: Black (Formatter), Ruff (Linter)

## Setup and Execution

Follow these steps to get the development environment up and running.

### Prerequisites

Ensure you have the following tools installed on your host machine:
- **Make**: A `make` compatible command-line utility.
- **Docker**: The latest version of Docker Engine.
- **Docker Compose**: Included with modern Docker installations.
- **Poetry**: For local dependency management and script execution.

### Step-by-Step Guide

1.  **Clone the Repository**:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Initial Project Setup**:
    Run the following command to install local Python dependencies using Poetry and create a `.env` file from the example template.
    ```sh
    make setup
    ```
    This command populates your local environment but does not affect the Docker containers.

3.  **Start the Application**:
    Build and start the Docker containers in detached mode using:
    ```sh
    make up
    ```
    This command uses `docker-compose.yml` and `docker-compose.dev.override.yml` to spin up the `web` (Django) and `nginx` services.

4.  **Access the Application**:
    Once the containers are running, you can access the web UI at **http://127.0.0.1:8000** (or the address specified by `HOST_BIND_IP` and `HOST_PORT` in your `.env` file).

5.  **Stopping the Application**:
    To stop and remove the development containers, run:
    ```sh
    make down
    ```

## Environment Variables

The application is configured via environment variables. Create a `.env` file by copying `.env.example` (`make setup` does this for you) and customize the values as needed.

| Variable              | Description                                                                                              | Default / Example                             |
| --------------------- | -------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `LLM_API_ENDPOINT`    | The full URL for the LLM API endpoint. `host.docker.internal` allows the container to reach the host.      | `http://host.docker.internal:8080`            |
| `SUMMARIZATION_MODEL` | The name of the specific LLM model to use for summarization.                                             | `qwen3:0.6b`                                  |
| `SUMMARY_MAX_CHARS`   | The maximum number of characters for the generated summary.                                              | `600`                                         |
| `GUNICORN_BIND`       | The IP and port for Gunicorn to bind to *inside* the `web` container.                                    | `0.0.0.0:8000`                                |
| `HOST_BIND_IP`        | The IP address on the host machine for Nginx to bind to.                                                 | `127.0.0.1`                                   |
| `HOST_PORT`           | The port on the host machine to expose the application through Nginx.                                    | `8000`                                        |
| `DEV_PORT`            | The port used by `docker-compose.dev.override.yml` for development.                                      | `8001`                                        |
| `TEST_PORT`           | The port used by `docker-compose.test.override.yml` for e2e testing.                                     | `8002`                                        |


## Application Usage

The application provides a simple web interface.
1.  Navigate to the main page.
2.  Enter the URL of a web page you wish to summarize in the input field.
3.  Click the "Submit" button.
4.  The application will scrape the content, generate a summary, and display both the original scraped text and the final summary on the page.

## Development Workflow

This project includes several tools to maintain code quality and verify functionality.

### Formatting and Linting

- **To automatically format your code**: Run `make format`. This executes Black and Ruff in fix-mode.
- **To check for linting and format issues**: Run `make lint`. This is the same check that runs in the CI pipeline.

### Running Tests

The project has a full test suite that includes unit, build, and end-to-end tests.
- **To run all tests**:
  ```sh
  make test
  ```
- **To run only unit tests** (fast, no Docker required):
  ```sh
  make unit-test
  ```
- **To run only end-to-end tests** (requires Docker):
  ```sh
  make e2e-test
  ```

## Deployment

Deployment is automated via a GitHub Actions workflow defined in `.github/workflows/build-and-push.yml`.

- **Trigger**: The workflow runs automatically on every `push` to the `main` branch.
- **Process**:
    1. The action checks out the repository code.
    2. It logs into the GitHub Container Registry (GHCR).
    3. It builds the `production` stage of the `Dockerfile`.
    4. It pushes the final image to GHCR, tagging it as `ghcr.io/<GITHUB_USERNAME>/<REPOSITORY_NAME>:latest`.

This process ensures that the latest version of the application is always available as a container image for deployment.

## Makefile Commands

The `Makefile` provides a convenient interface for most development tasks. Run `make help` to see all available commands. The table below lists the most common ones.

| Command             | Description                                                                 |
| ------------------- | --------------------------------------------------------------------------- |
| `make help`         | Displays a help message with all available targets.                         |
| `make setup`        | Installs local dependencies with Poetry and creates a `.env` file.          |
| `make up`           | Starts the development containers in detached mode.                         |
| `make down`         | Stops and removes the development containers.                               |
| `make up-prod`      | Starts containers in a production-like mode (no dev overrides).             |
| `make down-prod`    | Stops and removes the production-like containers.                           |
| `make rebuild`      | Rebuilds the `web` service without using cache and restarts it.             |
| `make logs`         | Tails the logs of the running `web` service.                                |
| `make shell`        | Opens a bash shell inside the `web` container.                              |
| `make makemigrations`| Creates new Django database migration files.                                |
| `make migrate`      | Applies database migrations in the development environment.                 |
| `make superuser`    | Creates a Django superuser for the development environment.                 |
| `make format`       | Formats all code using Black and Ruff.                                      |
| `make lint`         | Checks code for formatting and linting errors.                              |
| `make test`         | Runs the complete test suite (unit, build, and e2e).                        |
| `make unit-test`    | Runs only the unit tests.                                                   |
| `make e2e-test`     | Runs only the end-to-end tests.                                             |
