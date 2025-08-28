from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from requests.exceptions import RequestException

from apps.gist.services.summarization_service import (
    SummarizationService,
    SummarizationServiceError,
)

# Define constants for reuse
TEST_URL = "http://fake-api-url.com"
TEST_MODEL = "test-model"


@override_settings(PVT_LLM_API_URL=TEST_URL, SUMMARIZATION_MODEL=TEST_MODEL)
class TestSummarizationService(TestCase):
    def test_summarize_success(self):
        """
        Test successful summarization.
        """
        # Given
        text = "This is a test text."
        expected_summary = "This is the summary."

        with patch(
            "apps.gist.services.summarization_service.LlmApiClient"
        ) as MockApiClient:
            # Configure the mock instance
            mock_instance = MockApiClient.return_value
            mock_instance.generate.return_value = expected_summary

            # When
            service = SummarizationService()
            result = service.summarize(text)

            # Then
            self.assertEqual(result, expected_summary)
            mock_instance.generate.assert_called_once()
            # Verify that the prompt contains the original text
            called_prompt = mock_instance.generate.call_args.kwargs["prompt"]
            self.assertIn(text, called_prompt)
            # Verify the correct model is used
            called_model = mock_instance.generate.call_args.kwargs["model"]
            self.assertEqual(called_model, TEST_MODEL)

    def test_summarize_api_failure(self):
        """
        Test that SummarizationServiceError is raised when the API client fails.
        """
        # Given
        text = "This text will cause an API failure."

        with patch(
            "apps.gist.services.summarization_service.LlmApiClient"
        ) as MockApiClient:
            # Configure the mock to raise an exception
            mock_instance = MockApiClient.return_value
            mock_instance.generate.side_effect = RequestException("API Error")

            # When & Then
            service = SummarizationService()
            with self.assertRaises(SummarizationServiceError) as context:
                service.summarize(text)

            # Verify the error message
            self.assertIn("要約の生成に失敗しました", str(context.exception))
            mock_instance.generate.assert_called_once()

    def test_summarize_empty_response(self):
        """
        Test the service's behavior with an empty response from the API.
        """
        # Given
        text = "This text gets an empty summary."
        expected_summary = ""

        with patch(
            "apps.gist.services.summarization_service.LlmApiClient"
        ) as MockApiClient:
            # Configure the mock to return an empty string
            mock_instance = MockApiClient.return_value
            mock_instance.generate.return_value = ""

            # When
            service = SummarizationService()
            result = service.summarize(text)

            # Then
            self.assertEqual(result, expected_summary)
            mock_instance.generate.assert_called_once()

    @override_settings(PVT_LLM_API_URL=None)
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
        with patch(
            "apps.gist.services.summarization_service.LlmApiClient"
        ) as MockApiClient:
            mock_instance = MockApiClient.return_value

            # When
            service = SummarizationService()
            result_empty = service.summarize("")
            result_whitespace = service.summarize("   \n\t   ")

            # Then
            self.assertEqual(result_empty, "")
            self.assertEqual(result_whitespace, "")
            mock_instance.generate.assert_not_called()
