import os
import subprocess
import time
from pathlib import Path
from typing import Generator

import httpx
import pytest


def load_env_file(env_path: Path) -> None:
    """Load environment variables from .env file."""
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key, value)


@pytest.fixture(scope="session", autouse=True)
def e2e_setup() -> Generator[None, None, None]:
    """
    Manages the lifecycle of the application for end-to-end testing.
    """
    # Load .env file if it exists
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_env_file(env_path)
    
    # Use environment variables or defaults
    host_bind_ip = os.getenv("HOST_BIND_IP", "127.0.0.1")
    test_port = os.getenv("TEST_PORT", "8002")
    health_url = f"http://{host_bind_ip}:{test_port}/"

    # Determine if sudo should be used based on environment variable
    # This allows `SUDO=true make e2e-test` to work as expected.
    use_sudo = os.getenv("SUDO") == "true"
    docker_command = ["sudo", "docker"] if use_sudo else ["docker"]

    # Start services using docker-compose
    print("\n🚀 Starting E2E services...")
    compose_up_command = docker_command + [
        "compose",
        "-f",
        "docker-compose.yml",
        "-f",
        "docker-compose.test.override.yml",
        "--project-name",
        "gist-test",
        "up",
        "-d",
        "--build",
    ]
    subprocess.run(compose_up_command, check=True)

    # Teardown command to be used both on success and failure
    compose_down_command = docker_command + [
        "compose",
        "--project-name",
        "gist-test",
        "down",
        "--remove-orphans",
    ]

    # Health Check
    start_time = time.time()
    timeout = 120
    is_healthy = False
    print(f"Polling health check at {health_url}...")
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(health_url, timeout=5, verify=False)
            if response.status_code == 200:
                print("✅ Application is healthy!")
                is_healthy = True
                break
        except httpx.RequestError:
            print("⏳ Application not yet healthy, retrying...")
            time.sleep(5)

    if not is_healthy:
        log_command = docker_command + [
            "compose",
            "--project-name",
            "gist-test",
            "logs",
            "web",
        ]
        subprocess.run(log_command)
        # Ensure teardown on failure to avoid lingering containers
        print("\n🛑 Stopping E2E services due to health check failure...")
        subprocess.run(compose_down_command, check=True)
        pytest.fail(f"Application did not become healthy within {timeout} seconds.")

    yield

    # Stop services
    print("\n🛑 Stopping E2E services...")
    subprocess.run(compose_down_command, check=True)
