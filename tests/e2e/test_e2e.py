import os

import httpx
import pytest

pytestmark = pytest.mark.asyncio


async def test_index_page_loads():
    """
    Performs an end-to-end test on the index page ('/').
    """
    host_bind_ip = os.getenv("HOST_BIND_IP", "127.0.0.1")
    host_port = os.getenv("HOST_PORT", "8001")
    index_url = f"http://{host_bind_ip}:{host_port}/"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(index_url)

    assert response.status_code == 200
    assert "<h1>Enter URL to Scrape</h1>" in response.text
    assert "<title>Web Page Scraper</title>" in response.text
