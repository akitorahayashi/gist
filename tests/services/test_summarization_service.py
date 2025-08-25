from unittest.mock import MagicMock, patch

import pytest
import requests
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from apps.gist.services.summarization_service import (
    SummarizationService,
    SummarizationServiceError,
)


@patch("apps.gist.services.summarization_service.requests.post")
class TestSummarizationService:
    API_URL = "http://llm-api:8000"
    ENDPOINT = f"{API_URL}/api/v1/generate"

    @override_settings(PVT_LLM_API_URL=API_URL)
    def test_summarize_success(self, mock_post):
        # Given: APIのモックを設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "タイトル: テスト\n要点:\n- テストです"
        }
        mock_post.return_value = mock_response

        service = SummarizationService()
        text = "これはテスト用のテキストです。"

        # When: 要約を実行
        result = service.summarize(text)

        # Then: 要約結果が返り、APIが正しく呼ばれる
        assert result == "タイトル: テスト\n要点:\n- テストです"
        mock_post.assert_called_once()
        # 呼び出し引数を検証
        args, kwargs = mock_post.call_args
        assert args[0] == self.ENDPOINT
        assert kwargs["headers"] == {"Content-Type": "application/json"}
        assert "prompt" in kwargs["json"]
        assert kwargs["json"]["stream"] is False

    @override_settings(PVT_LLM_API_URL=API_URL)
    def test_summarize_empty_text(self, mock_post):
        # Given: 空のテキスト
        service = SummarizationService()
        text = ""

        # When: 要約を実行
        result = service.summarize(text)

        # Then: 空文字列が返り、APIは呼ばれない
        assert result == ""
        mock_post.assert_not_called()

    @override_settings(PVT_LLM_API_URL=API_URL, SUMMARY_MAX_CHARS=10)
    def test_summarize_truncates_text(self, mock_post):
        # Given: APIのモックと文字数制限
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "truncated summary"}
        mock_post.return_value = mock_response

        service = SummarizationService()
        text = "This is a very long text that should be truncated."

        # When: 要約を実行
        service.summarize(text)

        # Then: APIに渡されるプロンプト内のテキストが切り詰められている
        payload = mock_post.call_args.kwargs["json"]
        prompt = payload["prompt"]
        truncated = prompt.split("テキスト:\n", 1)[1].split("\n\n要約は", 1)[0]
        assert truncated == "This is a "

    @override_settings(PVT_LLM_API_URL=API_URL)
    def test_api_http_error(self, mock_post):
        # Given: APIがエラーを返すように設定
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_post.return_value = mock_response

        service = SummarizationService()
        # Then: SummarizationServiceErrorが発生する
        with pytest.raises(
            SummarizationServiceError, match="APIへの接続に失敗しました"
        ):
            # When: 要約を実行
            service.summarize("test text")

    @override_settings(PVT_LLM_API_URL=API_URL)
    def test_api_network_error(self, mock_post):
        # Given: APIがネットワークエラーを発生させるように設定
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        service = SummarizationService()
        # Then: SummarizationServiceErrorが発生する
        with pytest.raises(
            SummarizationServiceError, match="APIへの接続に失敗しました"
        ):
            # When: 要約を実行
            service.summarize("test text")

    @override_settings(PVT_LLM_API_URL=API_URL)
    def test_api_invalid_json_response(self, mock_post):
        # Given: APIが不正なJSONを返すように設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Decoding failed")
        mock_post.return_value = mock_response

        service = SummarizationService()
        # Then: SummarizationServiceErrorが発生する
        with pytest.raises(
            SummarizationServiceError, match="APIレスポンスのJSONデコードに失敗しました"
        ):
            # When: 要約を実行
            service.summarize("test text")

    @override_settings(PVT_LLM_API_URL=API_URL)
    def test_api_missing_response_key(self, mock_post):
        # Given: APIのレスポンスに必要なキーがない
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"detail": "Something went wrong"}
        mock_post.return_value = mock_response

        service = SummarizationService()
        # Then: SummarizationServiceErrorが発生する
        with pytest.raises(
            SummarizationServiceError,
            match="APIレスポンスに'response'キーが含まれていません。",
        ):
            # When: 要約を実行
            service.summarize("test text")

    @override_settings(PVT_LLM_API_URL=None)
    def test_init_missing_settings(self, mock_post):
        # When: 設定が不足している状態で初期化
        # Then: ImproperlyConfigured が発生する
        with pytest.raises(
            ImproperlyConfigured, match="PVT_LLM_API_URL is not configured."
        ):
            SummarizationService()

    @override_settings(PVT_LLM_API_URL=API_URL)
    def test_summarize_missing_max_chars_setting(self, mock_post, monkeypatch):
        # Given: SUMMARY_MAX_CHARS が settings にない
        monkeypatch.delattr("django.conf.settings.SUMMARY_MAX_CHARS", raising=False)

        service = SummarizationService()
        text = "Some text"

        # When: max_chars を指定せずに要約を実行
        # Then: AttributeError が発生する
        with pytest.raises(
            AttributeError, match="settings.SUMMARY_MAX_CHARS is not defined."
        ):
            service.summarize(text)
