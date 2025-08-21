from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from apps.gist.services.summarization_service import SummarizationService


class TestSummarizationService:
    @override_settings(OLLAMA_BASE_URL="http://ollama:11434", OLLAMA_MODEL="llama3")
    @patch("apps.gist.services.summarization_service.ChatOllama")
    def test_summarize_success(self, mock_chat_ollama):
        # Given: LLM の mock を設定
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value.content = (
            "タイトル: テスト\n要点:\n- テストです"
        )
        mock_chat_ollama.return_value = mock_llm_instance

        service = SummarizationService()
        # ChatOllama が設定値で初期化されることを明示検証
        mock_chat_ollama.assert_called_once_with(
            model="llama3", base_url="http://ollama:11434"
        )
        text = "これはテスト用のテキストです。"

        # When: 要約を実行
        result = service.summarize(text)

        # Then: 要約結果が返り、LLM が呼ばれる
        assert result == "タイトル: テスト\n要点:\n- テストです"
        mock_llm_instance.invoke.assert_called_once()

    @override_settings(OLLAMA_BASE_URL="http://ollama:11434", OLLAMA_MODEL="llama3")
    @patch("apps.gist.services.summarization_service.ChatOllama")
    def test_summarize_list_content(self, mock_chat_ollama):
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value.content = [
            "タイトル: A",
            "要点: 1",
            "要点: 2",
        ]
        mock_chat_ollama.return_value = mock_llm_instance

        service = SummarizationService()
        result = service.summarize("x" * 5, max_chars=5)
        assert result == "タイトル: A\n要点: 1\n要点: 2"

    @override_settings(OLLAMA_BASE_URL="http://ollama:11434", OLLAMA_MODEL="llama3")
    @patch("apps.gist.services.summarization_service.ChatOllama")
    def test_summarize_empty_text(self, mock_chat_ollama):
        # Given: 空のテキスト
        mock_llm_instance = MagicMock()
        mock_chat_ollama.return_value = mock_llm_instance
        service = SummarizationService()
        text = ""

        # When: 要約を実行
        result = service.summarize(text)

        # Then: 空文字列が返り、LLM は呼ばれない
        assert result == ""
        mock_llm_instance.invoke.assert_not_called()

    @override_settings(
        OLLAMA_BASE_URL="http://ollama:11434",
        OLLAMA_MODEL="llama3",
        SUMMARY_MAX_CHARS=10,
    )
    @patch("apps.gist.services.summarization_service.ChatOllama")
    def test_summarize_truncates_text(self, mock_chat_ollama):
        # Given: LLM の mock と文字数制限
        mock_llm_instance = MagicMock()
        mock_chat_ollama.return_value = mock_llm_instance
        service = SummarizationService()
        text = "This is a very long text that should be truncated."

        # When: 要約を実行
        service.summarize(text)

        # Then: LLM に渡されるテキストが切り詰められている
        called_prompt = mock_llm_instance.invoke.call_args[0][0]
        # プロンプトの「テキスト: ... 要約は...」区間のみを検査して誤検知を回避
        truncated = called_prompt.split("テキスト:\n", 1)[1].split("\n\n要約は", 1)[0]
        assert truncated == "This is a "

    @override_settings(OLLAMA_BASE_URL=None, OLLAMA_MODEL=None)
    def test_init_missing_settings(self):
        # When: 設定が不足している状態で初期化
        # Then: ImproperlyConfigured が発生する
        with pytest.raises(
            ImproperlyConfigured,
            match="OLLAMA_BASE_URL / OLLAMA_MODEL is not configured.",
        ):
            SummarizationService()

    @override_settings(OLLAMA_BASE_URL="http://ollama:11434", OLLAMA_MODEL="llama3")
    @patch("apps.gist.services.summarization_service.ChatOllama")
    def test_summarize_missing_max_chars_setting(self, mock_chat_ollama, monkeypatch):
        # Given: SUMMARY_MAX_CHARS が settings にない
        # settings から SUMMARY_MAX_CHARS を安全に取り除く
        monkeypatch.delattr("django.conf.settings.SUMMARY_MAX_CHARS", raising=False)

        mock_chat_ollama.return_value = MagicMock()
        service = SummarizationService()
        text = "Some text"

        # When: max_chars を指定せずに要約を実行
        # Then: AttributeError が発生する
        with pytest.raises(
            AttributeError, match="settings.SUMMARY_MAX_CHARS is not defined."
        ):
            service.summarize(text)
