import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from requests.exceptions import RequestException

from apps.gist.clients.llm_api_client import LlmApiClient

logger = logging.getLogger(__name__)


class SummarizationServiceError(Exception):
    """A custom exception for errors during the summarization process."""

    pass


class SummarizationService:
    """
    A service for summarizing web page content.
    """

    def __init__(self):
        try:
            self.llm_client = LlmApiClient()
            self.model = settings.SUMMARIZATION_MODEL
        except ImproperlyConfigured as e:
            # Re-raise as a service-specific exception to decouple from the client
            raise SummarizationServiceError(f"Service not configured: {e}") from e

    def summarize(self, text: str, max_chars: int | None = None) -> str:
        """
        Summarizes the given text using the LLM API.

        Args:
            text: The text content to summarize.
            max_chars: The maximum number of characters of the text to use.
                       Defaults to settings.SUMMARY_MAX_CHARS.

        Returns:
            The summarized text.

        Raises:
            SummarizationServiceError: If the summarization fails.
        """
        if not text or not text.strip():
            return ""

        if max_chars is None:
            max_chars = settings.SUMMARY_MAX_CHARS

        truncated_text = text[:max_chars]
        prompt = self._build_prompt(truncated_text)

        try:
            summary = self.llm_client.generate(prompt=prompt, model=self.model)
            return summary.strip()
        except RequestException as e:
            logger.error(f"Summarization failed due to an API error: {e}")
            raise SummarizationServiceError(
                "要約の生成に失敗しました。外部APIとの通信中にエラーが発生しました。"
            ) from e

    def _build_prompt(self, text: str) -> str:
        """Constructs the prompt for the summarization task."""
        return f"""以下のテキストを日本語で要約してください。

テキスト:
{text}

要約は以下の形式で出力してください。
タイトル: 記事の内容を一行で表すタイトルを1つ生成してください。
要点: 記事の最も重要なポイントを3つを目安として、最大5つまでの箇条書きで簡潔にまとめてください。各箇条書きは100字以内にしてください。
"""
