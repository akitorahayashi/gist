from unittest.mock import MagicMock, patch

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from requests.exceptions import RequestException

from apps.gist.services.summarization_service import (
    SummarizationService,
    SummarizationServiceError,
)

# Define constants for reuse
TEST_MODEL = "test-model"


@override_settings(SUMMARIZATION_MODEL=TEST_MODEL)
class TestSummarizationService(TestCase):
    def test_summarize_success(self):
        """
        Test successful summarization.
        """
        # Given
        text = "This is a test text."
        expected_summary = "This is the summary."
        mock_client = MagicMock()
        mock_client.generate.return_value = expected_summary

        # When
        service = SummarizationService()
        service.client = mock_client
        result = service.summarize(text)

        # Then
        self.assertEqual(result, expected_summary)
        mock_client.generate.assert_called_once()
        # Verify that the prompt contains the original text
        called_prompt = mock_client.generate.call_args.kwargs["prompt"]
        self.assertIn(text, called_prompt)
        # Verify the correct model is used
        called_model = mock_client.generate.call_args.kwargs["model"]
        self.assertEqual(called_model, TEST_MODEL)

    def test_summarize_api_failure(self):
        """
        Test that SummarizationServiceError is raised when the API client fails.
        """
        # Given
        text = "This text will cause an API failure."
        mock_client = MagicMock()
        mock_client.generate.side_effect = RequestException("API Error")

        # When & Then
        service = SummarizationService()
        service.client = mock_client
        with self.assertRaises(SummarizationServiceError) as context:
            service.summarize(text)

        # Verify the error message
        self.assertIn("要約の生成に失敗しました", str(context.exception))
        mock_client.generate.assert_called_once()

    def test_summarize_empty_response(self):
        """
        Test the service's behavior with an empty response from the API.
        """
        # Given
        text = "This text gets an empty summary."
        expected_summary = ""
        mock_client = MagicMock()
        mock_client.generate.return_value = ""

        # When
        service = SummarizationService()
        service.client = mock_client
        result = service.summarize(text)

        # Then
        self.assertEqual(result, expected_summary)
        mock_client.generate.assert_called_once()

    @override_settings(LLM_API_ENDPOINT=None)
    def test_init_raises_error_if_url_not_configured(self):
        """
        Test that initialization raises SummarizationServiceError if the URL is missing.
        """
        # When & Then
        with self.assertRaises(SummarizationServiceError) as context:
            SummarizationService()

        # Verify the underlying error is chained
        self.assertIsInstance(context.exception.__cause__, ImproperlyConfigured)
        self.assertIn("Service not configured", str(context.exception))

    def test_summarize_empty_input_text(self):
        """
        Test that the service returns an empty string for empty or whitespace input
        without calling the API.
        """
        # Given
        mock_client = MagicMock()

        # When
        service = SummarizationService()
        service.client = mock_client
        result_empty = service.summarize("")
        result_whitespace = service.summarize("   \n\t   ")

        # Then
        self.assertEqual(result_empty, "")
        self.assertEqual(result_whitespace, "")
        mock_client.generate.assert_not_called()
