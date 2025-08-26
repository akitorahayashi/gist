import os
import subprocess
import time

import httpx
import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="session")
def e2e_services():
    """
    Manages the lifecycle of the services for E2E tests.
    - Loads test environment variables.
    - Starts services using docker-compose.
    - Waits for the API to become healthy.
    - Yields to the test session.
    - Cleans up and shuts down services.
    """
    # .env.testから環境変数を読み込む
    load_dotenv(".env.test", override=True)
    host_port = os.getenv("HOST_PORT")
    project_name = "gist-test"
    compose_command = [
        "sudo",
        "docker",
        "compose",
        "--env-file",
        ".env.test",
        "--project-name",
        project_name,
    ]

    # docker-compose up
    print("\n--- Starting E2E services ---")
    # `docker-compose.yml` を明示的に指定
    up_command = compose_command + ["-f", "docker-compose.yml", "up", "-d", "--build"]
    subprocess.run(up_command, check=True)

    # ヘルスチェック
    health_check_url = f"http://localhost:{host_port}/health"
    start_time = time.time()
    timeout = 120  # タイムアウトを120秒に延長
    is_healthy = False

    print(f"Waiting for service to be healthy at {health_check_url}...")
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(health_check_url, timeout=5)
            if response.status_code == 200:
                print("Service is healthy!")
                is_healthy = True
                break
        except httpx.RequestError as e:
            print(f"Health check failed: {e}. Retrying in 5 seconds...")
        time.sleep(5)

    if not is_healthy:
        # サービスが起動しなかった場合、ログを出力してコンテナを落とす
        logs_command = compose_command + ["logs"]
        logs_result = subprocess.run(logs_command, capture_output=True, text=True)
        print("--- Service logs ---")
        print(logs_result.stdout)
        print(logs_result.stderr)

        down_command = compose_command + ["down", "-v", "--remove-orphans"]
        subprocess.run(down_command, check=True)
        pytest.fail(f"Service did not become healthy within {timeout} seconds.")

    # テスト実行
    yield

    # docker-compose down
    print("\n--- Tearing down E2E services ---")
    down_command = compose_command + ["down", "-v", "--remove-orphans"]
    subprocess.run(down_command, check=True)
