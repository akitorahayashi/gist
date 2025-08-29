# Gist Summarizer

A Django-based web application that scrapes the content of a given URL and uses a Large Language Model (LLM) to generate a summary.

This project is designed with a modern and professional development experience in mind, incorporating containerization with Docker, a streamlined command interface with Make, and automated CI/CD pipelines using GitHub Actions.

## ✨ Features

- **Web Content Scraping**: Extracts the main text content from any provided article URL.
- **AI-Powered Summarization**: Integrates with an LLM to produce concise summaries of the scraped text.
- **Simple Web Interface**: A clean UI to input a URL and view the generated summary.
- **Containerized Environment**: Uses Docker and Docker Compose for consistent and reproducible development and production environments.
- **Developer Experience (DX)**: A `Makefile` provides a simple, unified interface for all common development tasks like running servers, tests, and linters.
- **Continuous Integration & Deployment**: Automated workflows for testing, linting, and deploying the application to the GitHub Container Registry.

## 🛠️ Tech Stack

- **Backend**: Django
- **Web Server**: Gunicorn, Nginx
- **Dependency Management**: Poetry
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Code Quality**: Black (Formatter), Ruff (Linter)
- **Testing**: Pytest

##  Prerequisites

Before you begin, ensure you have the following tools installed on your system:

- **Docker**: The latest version is recommended.
- **Docker Compose**: Included with modern Docker installations.
- **Make**: The `make` command must be available in your shell.

## 🚀 Getting Started

Follow these steps to set up and run the development environment.

### 1. Clone the Repository

```bash
git clone https://github.com/akitorahayashi/gist.git
cd gist
```

### 2. Initial Project Setup

Run the following command to install Python dependencies using Poetry and create your local environment file (`.env`) from the template.

```bash
make setup
```

This command inspects the `.env.example` file and creates a `.env` file for you to customize. You must fill in the `LLM_API_ENDPOINT` for the application to work.

### 3. Launch the Application

Once the setup is complete, start the application services (web, nginx) in detached mode:

```bash
make up
```

The application will now be running and accessible at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## ⚙️ Environment Variables

The application's behavior is configured via environment variables, which are defined in the `.env` file. This file is ignored by Git.

| Variable              | Description                                                                                               | Default Value      | Example                               |
| --------------------- | --------------------------------------------------------------------------------------------------------- | ------------------ | ------------------------------------- |
| `LLM_API_ENDPOINT`    | **Required.** The full URL of the LLM API service.                                                        | (None)             | `http://host.docker.internal:8080`    |
| `SUMMARIZATION_MODEL` | The identifier for the summarization model to use.                                                        | `qwen3:0.6b`       | `gemma:2b`                            |
| `SUMMARY_MAX_CHARS`   | The maximum number of characters for the generated summary.                                               | `600`              | `1000`                                |
| `HOST_BIND_IP`        | The host IP address for the Nginx proxy to bind to. `127.0.0.1` for local access, `0.0.0.0` for network access. | `127.0.0.1`        | `0.0.0.0`                             |
| `HOST_PORT`           | The host port to access the application.                                                                  | `8000`             | `8080`                                |

## 🌐 Application Usage

This application provides a simple web interface and does not have a public API.

1.  Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000) in your web browser.
2.  Enter the URL of a web page you want to summarize in the input field.
3.  Click the "Summarize" button.
4.  The application will scrape the content and display the generated summary on the same page.

## 👨‍💻 Development Workflow

The `Makefile` provides several commands to streamline the development process.

### Formatting and Linting

To ensure code quality and consistency, always format and lint your code before committing.

-   **Format Code**: Automatically formats the code using Black and Ruff.
    ```bash
    make format
    ```
-   **Check for Issues**: Runs the linter (Ruff) and format checker (Black) without modifying files. This is the same check that runs in CI.
    ```bash
    make lint
    ```

### Running Tests

The project includes a comprehensive test suite.

-   **Run All Tests**: Executes the full suite, including unit and end-to-end tests.
    ```bash
    make test
    ```
-   **Run Unit Tests**: Run fast, isolated tests that do not require a running database or other services.
    ```bash
    make unit-test
    ```
-   **Run End-to-End Tests**: Run tests against a live, containerized instance of the application.
    ```bash
    make e2e-test
    ```

## 🚀 Deployment

The project is configured for Continuous Deployment to the **GitHub Container Registry (ghcr.io)**.

When code is pushed to the `main` branch, a GitHub Actions workflow (`.github/workflows/build-and-push.yml`) is triggered. The workflow performs the following steps:
1.  Logs in to `ghcr.io`.
2.  Builds a production-ready Docker image based on the `runner` stage in the `Dockerfile`.
3.  Pushes the image to `ghcr.io/akitorahayashi/gist:latest`.

This image can then be pulled and deployed to any container hosting platform.

## 📜 Makefile Commands

The `Makefile` is self-documenting. Run `make help` to see a full list of available commands. The most common ones are listed below.

| Command             | Description                                                         |
| ------------------- | ------------------------------------------------------------------- |
| `make help`         | Displays the help message with all available targets.               |
| `make setup`        | Installs dependencies and creates the `.env` file.                  |
| `make up`           | Starts all development containers in detached mode.                 |
| `make down`         | Stops and removes all development containers.                       |
| `make up-prod`      | Starts all production-like containers.                              |
| `make down-prod`    | Stops and removes all production-like containers.                   |
| `make rebuild`      | Rebuilds the `web` service without cache and restarts it.           |
| `make logs`         | Tails the logs from the running `web` service.                      |
| `make shell`        | Opens a bash shell inside the running `web` container.              |
| `make makemigrations`| Creates new Django database migration files.                        |
| `make migrate`      | Applies database migrations to the development database.            |
| `make superuser`    | Creates a Django superuser.                                         |
| `make format`       | Formats all code using Black and Ruff.                              |
| `make lint`         | Checks code for formatting and linting issues.                      |
| `make test`         | Runs the complete test suite (unit, build, and e2e).                |
| `make unit-test`    | Runs only the unit tests locally.                                   |
| `make build-test`   | Builds a temporary Docker image to ensure it builds successfully.   |
| `make e2e-test`     | Runs the end-to-end tests.                                          |
