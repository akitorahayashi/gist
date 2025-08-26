from unittest.mock import MagicMock

import pytest
import requests
from django.test import override_settings

from apps.gist.services.summarization_service import (
    SummarizationService,
)

# Constants
API_URL = "http://llm-api:8000"
HEALTH_API_PATH = "health"


@pytest.fixture
def mock_get(mocker):
    """Fixture for the mocked requests.get."""
    return mocker.patch(
        "apps.gist.services.summarization_service.requests.get", autospec=True
    )


@pytest.fixture
def mock_post(mocker):
    """Fixture for the mocked requests.post."""
    return mocker.patch(
        "apps.gist.services.summarization_service.requests.post", autospec=True
    )


@pytest.fixture
def summarization_service_factory():
    """Factory fixture that instantiates service under current settings context."""

    def _factory():
        return SummarizationService()

    return _factory


@pytest.fixture
def summarization_service(summarization_service_factory):
    """Fixture to provide a service instance with default settings."""
    with override_settings(PVT_LLM_API_URL=API_URL):
        yield summarization_service_factory()


@pytest.fixture
def mock_health_check_success(mock_get):
    """Fixture to mock a successful health check."""
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 200
    mock_response.ok = True
    mock_get.return_value = mock_response
    return mock_get
