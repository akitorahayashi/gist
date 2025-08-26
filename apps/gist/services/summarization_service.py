from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class SummarizationServiceError(Exception):
    """要約サービスで発生したエラーのベース例外クラス"""

    pass


class SummarizationService:
    def __init__(self):
        if not settings.PVT_LLM_API_URL:
            raise ImproperlyConfigured("PVT_LLM_API_URL is not configured.")
        self.api_base_url = settings.PVT_LLM_API_URL

    def _health_check(self):
        """
        連携先のLLM APIのヘルスチェックを行う。
        正常でない場合は SummarizationServiceError を送出する。
        """
        health_check_url = urljoin(self.api_base_url.rstrip("/") + "/", "health")
        try:
            response = requests.get(health_check_url, timeout=5)
            if response.status_code != 200:
                raise SummarizationServiceError(
                    f"LLM API is unhealthy. Status: {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            raise SummarizationServiceError(f"Failed to connect to LLM API: {e}") from e

    def summarize(self, text: str, max_chars: int | None = None) -> str:
        if not text or not text.strip():
            return ""

        if max_chars is None:
            if not hasattr(settings, "SUMMARY_MAX_CHARS"):
                raise AttributeError("settings.SUMMARY_MAX_CHARS is not defined.")
            max_chars = settings.SUMMARY_MAX_CHARS

        self._health_check()

        truncated_text = text[:max_chars]
        prompt = f"""以下のテキストを日本語で要約してください。

テキスト:
{truncated_text}

要約は以下の形式で出力してください。
タイトル: 記事の内容を一行で表すタイトルを1つ生成してください。
要点: 記事の最も重要なポイントを3つを目安として、最大5つまでの箇条書きで簡潔にまとめてください。各箇条書きは100字以内にしてください。
"""

        api_url = urljoin(self.api_base_url.rstrip("/") + "/", "api/v1/generate")
        headers = {"Content-Type": "application/json"}
        payload = {"prompt": prompt, "stream": False}

        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()  # 2xx以外のステータスコードでHTTPErrorを送出

            response_json = response.json()
            if "response" not in response_json:
                raise SummarizationServiceError(
                    "APIレスポンスに'response'キーが含まれていません。"
                )

            return response_json["response"]

        except requests.exceptions.RequestException as e:
            # ネットワークエラーやタイムアウトなど
            raise SummarizationServiceError(f"APIへの接続に失敗しました: {e}") from e
        except ValueError:
            # JSONデコードエラー
            raise SummarizationServiceError(
                "APIレスポンスのJSONデコードに失敗しました。"
            )
