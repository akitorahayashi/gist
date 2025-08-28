import logging

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class LlmApiClient:
    """
    A client for interacting with the private LLM API.
    """

    def __init__(self):
        self.api_url = settings.LLM_API_ENDPOINT
        if not self.api_url:
            raise ImproperlyConfigured(
                "LLM_API_ENDPOINT is not configured in settings."
            )
        self.generate_endpoint = f"{self.api_url}/api/v1/generate"

    def generate(self, prompt: str, model: str) -> str:
        """
        Generates text using the LLM API.

        Args:
            prompt: The prompt to send to the model.
            model: The name of the model to use for generation.

        Returns:
            The generated text from the API.

        Raises:
            requests.exceptions.RequestException: If a network error occurs.
        """
        payload = {
            "prompt": prompt,
            "model": model,
            "stream": False,
        }
        try:
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                timeout=(10, 120),  # (connect, read)
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API request failed: {e}")
            raise e
