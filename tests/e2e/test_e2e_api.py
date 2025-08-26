import os

import httpx
import pytest
from dotenv import load_dotenv

# .env.testを読み込んで、テスト実行前に環境変数を設定
load_dotenv(".env.test", override=True)


@pytest.mark.e2e
def test_generate_api_success(e2e_services):
    """
    Tests the /api/v1/generate endpoint for a successful summarization.
    """
    host_port = os.getenv("HOST_PORT")
    assert host_port, "HOST_PORT environment variable must be set"

    api_url = f"http://localhost:{host_port}/api/v1/generate"

    # テスト対象のURL
    target_url = "https://www.metoffice.gov.uk/weather/forecast/gcpvj0v07"  # A known public and stable website

    print(f"Sending request to {api_url} with target_url: {target_url}")

    try:
        with httpx.Client(timeout=60) as client:
            response = client.post(
                api_url,
                json={"url": target_url},
            )

        # ステータスコードの検証
        assert response.status_code == 200

        # レスポンスボディの検証
        response_data = response.json()
        assert "response" in response_data
        assert isinstance(response_data["response"], str)
        assert len(response_data["response"]) > 0

        print(f"Received successful response: {response_data['response'][:100]}...")

    except httpx.RequestError as e:
        pytest.fail(f"API request failed: {e}")
