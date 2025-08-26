from urllib.parse import urljoin
from unittest.mock import MagicMock

import pytest
import requests
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from apps.gist.services.summarization_service import (
    SummarizationService,
    SummarizationServiceError,
)

# Constants
API_URL = "http://llm-api:8000"
GENERATE_API_PATH = "api/v1/generate"
HEALTH_API_PATH = "health"
DEFAULT_TIMEOUT = 60
HEALTH_TIMEOUT = 5


@pytest.fixture
def mock_get(mocker):
    """Fixture for the mocked requests.get."""
    return mocker.patch(
        "apps.gist.services.summarization_service.requests.get", spec=True
    )


@pytest.fixture
def mock_post(mocker):
    """Fixture for the mocked requests.post."""
    return mocker.patch(
        "apps.gist.services.summarization_service.requests.post", spec=True
    )


@pytest.fixture
def summarization_service():
    """Fixture to provide an instance of SummarizationService."""
    with override_settings(PVT_LLM_API_URL=API_URL):
        return SummarizationService()


@pytest.fixture
def mock_health_check_success(mock_get, summarization_service):
    """Fixture to mock a successful health check."""
    mock_response = requests.Response()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    return mock_get


# --- Test Cases ---


@pytest.mark.parametrize(
    "base_url",
    [API_URL, f"{API_URL}/"],
)
def test_summarize_success(
    summarization_service, mock_health_check_success, mock_post, base_url
):
    # Given
    with override_settings(PVT_LLM_API_URL=base_url):
        expected_summary = "タイトル: テスト\n要点:\n- テストです"
        mock_api_response = requests.Response()
        mock_api_response.status_code = 200
        mock_api_response.json = lambda: {"response": expected_summary}
        mock_post.return_value = mock_api_response

        text = "これはテスト用のテキストです。"

        # When
        result = summarization_service.summarize(text)

        # Then
        assert result == expected_summary

        # Verify calls
        health_url = urljoin(base_url, HEALTH_API_PATH)
        mock_health_check_success.assert_called_once_with(
            health_url, timeout=HEALTH_TIMEOUT
        )

        api_url = urljoin(base_url, GENERATE_API_PATH)
        mock_post.assert_called_once()
        call_args, call_kwargs = mock_post.call_args
        assert call_args[0] == api_url
        assert call_kwargs["timeout"] == DEFAULT_TIMEOUT
        assert "prompt" in call_kwargs["json"]


@pytest.mark.parametrize("text_input", ["", "   \n\t   "])
def test_summarize_empty_or_whitespace_input(
    summarization_service, mock_get, mock_post, text_input
):
    # When
    result = summarization_service.summarize(text_input)

    # Then
    assert result == ""
    mock_get.assert_not_called()
    mock_post.assert_not_called()


@pytest.mark.parametrize(
    "side_effect, error_message_match",
    [
        (
            type("MockResponse", (object,), {"status_code": 503}),
            "LLM API is unhealthy",
        ),
        (requests.exceptions.Timeout("Connection timed out"), "Failed to connect"),
    ],
)
def test_health_check_fails(
    summarization_service, mock_get, mock_post, side_effect, error_message_match
):
    # Given
    if isinstance(side_effect, type) and hasattr(side_effect, "status_code"):
        mock_get.return_value = side_effect
    else:
        mock_get.side_effect = side_effect

    # Then
    with pytest.raises(SummarizationServiceError, match=error_message_match):
        # When
        summarization_service.summarize("test text")

    mock_post.assert_not_called()


@override_settings(SUMMARY_MAX_CHARS=10)
def test_summarize_truncates_text(
    summarization_service, mock_health_check_success, mock_post
):
    # Given
    max_chars = 10
    text = "This is a very long text that should be truncated."
    mock_post.return_value = requests.Response()
    mock_post.return_value.status_code = 200
    mock_post.return_value.json = lambda: {"response": "summary"}

    # When
    summarization_service.summarize(text, max_chars=max_chars)

    # Then
    payload = mock_post.call_args.kwargs["json"]
    prompt = payload["prompt"]
    truncated = prompt.split("テキスト:\n", 1)[1].split("\n\n要約は", 1)[0]
    assert truncated == text[:max_chars]


def test_summarize_with_max_chars_arg(
    summarization_service, mock_health_check_success, mock_post
):
    # Given
    text = "This text should be truncated by the argument."
    max_chars_arg = 5
    mock_post.return_value = requests.Response()
    mock_post.return_value.status_code = 200
    mock_post.return_value.json = lambda: {"response": "summary"}

    # When
    summarization_service.summarize(text, max_chars=max_chars_arg)

    # Then
    payload = mock_post.call_args.kwargs["json"]
    prompt = payload["prompt"]
    truncated = prompt.split("テキスト:\n", 1)[1].split("\n\n要約は", 1)[0]
    assert truncated == text[:max_chars_arg]


@pytest.mark.parametrize(
    "setup_mock, error_message_match",
    [
        (
            lambda mock: setattr(
                mock.return_value,
                "raise_for_status",
                MagicMock(side_effect=requests.exceptions.HTTPError("404 Not Found")),
            ),
            "APIへの接続に失敗しました",
        ),
        (
            lambda mock: setattr(
                mock, "side_effect", requests.exceptions.Timeout("Timeout")
            ),
            "APIへの接続に失敗しました",
        ),
        (
            lambda mock: setattr(
                mock.return_value,
                "json",
                MagicMock(side_effect=ValueError("JSON decode error")),
            ),
            "APIレスポンスのJSONデコードに失敗しました",
        ),
        (
            lambda mock: setattr(
                mock.return_value, "json", lambda: {"detail": "wrong key"}
            ),
            "APIレスポンスに'response'キーが含まれていません。",
        ),
    ],
)
def test_summarize_api_fails(
    summarization_service,
    mock_health_check_success,
    mock_post,
    setup_mock,
    error_message_match,
):
    # Given
    setup_mock(mock_post)

    # Then
    with pytest.raises(SummarizationServiceError, match=error_message_match):
        # When
        summarization_service.summarize("test text")


def test_init_missing_settings():
    # When & Then
    with override_settings(PVT_LLM_API_URL=None):
        with pytest.raises(
            ImproperlyConfigured, match="PVT_LLM_API_URL is not configured."
        ):
            SummarizationService()


def test_summarize_missing_max_chars_setting(
    summarization_service, mock_get, monkeypatch
):
    # Given
    monkeypatch.delattr("django.conf.settings.SUMMARY_MAX_CHARS", raising=False)

    # Then
    with pytest.raises(
        AttributeError, match="settings.SUMMARY_MAX_CHARS is not defined."
    ):
        # When
        summarization_service.summarize("some text")

    mock_get.assert_not_called()
