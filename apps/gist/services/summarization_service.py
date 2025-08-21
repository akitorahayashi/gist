from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from langchain_ollama import ChatOllama


def _ensure_ollama_config():
    if not settings.OLLAMA_BASE_URL or not settings.OLLAMA_MODEL:
        raise ImproperlyConfigured("OLLAMA_BASE_URL / OLLAMA_MODEL is not configured.")


class SummarizationService:
    def __init__(self):
        _ensure_ollama_config()
        self.llm = ChatOllama(
            model=settings.OLLAMA_MODEL, base_url=settings.OLLAMA_BASE_URL
        )

    def summarize(self, text: str, max_chars: int | None = None) -> str:
        if not text:
            return ""
        if max_chars is None:
            if not hasattr(settings, "SUMMARY_MAX_CHARS"):
                raise AttributeError("settings.SUMMARY_MAX_CHARS is not defined.")
            max_chars = settings.SUMMARY_MAX_CHARS
        truncated_text = text[:max_chars]
        prompt = f"""以下のテキストを日本語で要約してください。

テキスト:
{truncated_text}

要約は以下の形式で出力してください。
タイトル: 記事の内容を一行で表すタイトルを1つ生成してください。
要点: 記事の最も重要なポイントを3つを目安として、最大5つまでの箇条書きで簡潔にまとめてください。各箇条書きは100字以内にしてください。
"""
        result = self.llm.invoke(prompt)
        if isinstance(result.content, str):
            return result.content
        elif isinstance(result.content, list):
            return "\n".join(str(item) for item in result.content)
        return str(result.content)
