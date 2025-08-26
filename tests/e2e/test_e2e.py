import os

import httpx
import pytest
from dotenv import load_dotenv

# .env.testを読み込んで、テスト実行前に環境変数を設定
load_dotenv(".env.test", override=True)


@pytest.mark.e2e
def test_index_page_loads(e2e_services):
    """
    Tests that the index page loads correctly.
    """
    host_port = os.getenv("HOST_PORT")
    assert host_port, "HOST_PORT environment variable must be set"

    index_url = f"http://localhost:{host_port}/"

    print(f"Sending request to {index_url}")

    try:
        with httpx.Client(timeout=60) as client:
            response = client.get(index_url)

        # ステータスコードの検証
        assert response.status_code == 200

        # レスポンスボディの検証
        assert "Enter URL to Scrape" in response.text

        print("Received successful response for index page.")

    except httpx.RequestError as e:
        pytest.fail(f"Request to index page failed: {e}")
