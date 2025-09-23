import time
from typing import Dict, List, cast
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import (
    assert_that,
    calling,
    contains_string,
    equal_to,
    instance_of,
    is_,
    raises,
)
from openai import APIConnectionError, APITimeoutError, AuthenticationError
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from src.ai.openai_service import (
    LLMAPIError,
    LLMConnectionError,
    LLMTimeoutError,
    call_llm_api,
)
from src.models import ChatMessage


@pytest.fixture
def mock_openai_client():
    """
    Fixture that provides a mock OpenAI client with a successful response.

    Returns:
        MagicMock: A mock object simulating the OpenAI client.
    """
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Test response from LLM"
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


# Define a standard test messages list
test_messages: List[ChatMessage] = [{"role": "user", "content": "Hello, LLM!"}]


@patch("src.ai.openai_service.OpenAI")
def test_call_llm_api_success(mock_openai, mock_openai_client):
    """
    Test that call_llm_api successfully returns the LLM response.

    Args:
        mock_openai: Mocked OpenAI class.
        mock_openai_client: Mock OpenAI client fixture.
    """
    # Arrange
    mock_openai.return_value = mock_openai_client

    # Act
    result = call_llm_api(
        messages=cast(List[ChatCompletionMessageParam], test_messages),
        api_key="chatgpt_api_key",
    )

    # Assert
    assert_that(result, equal_to("Test response from LLM"))
    mock_openai.assert_called_once_with(api_key="chatgpt_api_key")
    mock_openai_client.chat.completions.create.assert_called_once_with(
        model="gpt-3.5-turbo",
        messages=test_messages,
        temperature=0.7,
    )


@patch("src.ai.openai_service.OpenAI")
def test_call_llm_api_empty_response(mock_openai, mock_openai_client):
    """
    Test that call_llm_api raises LLMAPIError when receiving an empty response.

    Args:
        mock_openai: Mocked OpenAI class.
        mock_openai_client: Mock OpenAI client fixture.
    """
    # Arrange
    mock_openai.return_value = mock_openai_client
    mock_openai_client.chat.completions.create.return_value.choices[
        0
    ].message.content = ""

    # Act & Assert
    assert_that(
        calling(call_llm_api).with_args(
            messages=cast(List[ChatCompletionMessageParam], test_messages),
            api_key="test_api_key",
        ),
        raises(LLMAPIError),
    )


@patch("src.ai.openai_service.OpenAI")
def test_call_llm_api_timeout(mock_openai):
    """
    Test that call_llm_api raises LLMTimeoutError when the API call times out.

    Args:
        mock_openai: Mocked OpenAI class.
    """
    # Arrange
    mock_openai.side_effect = APITimeoutError(request=MagicMock())

    # Act & Assert
    assert_that(
        calling(call_llm_api).with_args(
            messages=cast(List[ChatCompletionMessageParam], test_messages),
            api_key="test_api_key",
        ),
        raises(LLMTimeoutError),
    )


@patch("src.ai.openai_service.OpenAI")
def test_call_llm_api_connection_error(mock_openai):
    """
    Test that call_llm_api raises LLMConnectionError when there's a connection error.

    Args:
        mock_openai: Mocked OpenAI class.
    """
    # Arrange
    mock_openai.side_effect = APIConnectionError(
        message="Connection failed", request=MagicMock()
    )

    # Act & Assert
    assert_that(
        calling(call_llm_api).with_args(
            messages=cast(List[ChatCompletionMessageParam], test_messages),
            api_key="test_api_key",
        ),
        raises(LLMConnectionError),
    )


@patch("src.ai.openai_service.OpenAI")
def test_call_llm_api_generic_error(mock_openai):
    """
    Test that call_llm_api raises LLMAPIError for generic exceptions.

    Args:
        mock_openai: Mocked OpenAI class.
    """
    # Arrange
    mock_openai.side_effect = Exception("Generic error")

    # Act & Assert
    assert_that(
        calling(call_llm_api).with_args(
            messages=cast(List[ChatCompletionMessageParam], test_messages),
            api_key="test_api_key",
        ),
        raises(LLMAPIError),
    )


class ExampleResponseModel(BaseModel):
    """Test Pydantic model for structured response testing."""

    name: str
    age: int


# Define test messages for structured response test
structured_test_messages: List[ChatMessage] = [
    {"role": "user", "content": "Extract the user information"}
]


@patch("src.ai.openai_service.instructor.from_openai")
def test_call_llm_api_with_response_model(mock_instructor_from_openai):
    """
    Test that call_llm_api correctly uses instructor with a response model.

    Args:
        mock_instructor_from_openai: Mocked instructor.from_openai function.
    """
    # Arrange
    mock_instructor_client = MagicMock()
    mock_instructor_from_openai.return_value = mock_instructor_client

    mock_response = ExampleResponseModel(name="John Doe", age=30)
    mock_instructor_client.chat.completions.create.return_value = mock_response

    # Act
    result = call_llm_api(
        messages=cast(List[ChatCompletionMessageParam], structured_test_messages),
        api_key="chatgpt_api_key",
        response_model=ExampleResponseModel,
    )

    # Assert
    assert_that(result, instance_of(ExampleResponseModel))
    assert_that(result.name, equal_to("John Doe"))
    assert_that(result.age, equal_to(30))

    mock_instructor_client.chat.completions.create.assert_called_once_with(
        model="gpt-3.5-turbo",
        messages=structured_test_messages,
        temperature=0.7,
        response_model=ExampleResponseModel,
        validation_context=None,
    )


@patch("src.ai.openai_service.instructor.from_openai")
def test_call_llm_api_with_response_model_error(mock_instructor_from_openai):
    """
    Test that call_llm_api correctly handles errors when using a response model.

    Args:
        mock_instructor_from_openai: Mocked instructor.from_openai function.
    """
    # Arrange
    mock_instructor_client = MagicMock()
    mock_instructor_from_openai.return_value = mock_instructor_client

    mock_instructor_client.chat.completions.create.side_effect = Exception(
        "Validation error"
    )

    # Act & Assert
    assert_that(
        calling(call_llm_api).with_args(
            messages=cast(List[ChatCompletionMessageParam], structured_test_messages),
            api_key="test_api_key",
            response_model=ExampleResponseModel,
        ),
        raises(LLMAPIError),
    )


class TestOpenAIKeyValidation:
    """Tests for OpenAI API key validation functionality."""

    @patch("src.ai.openai_service.OpenAI")
    def test_validate_openai_key_success(self, mock_openai_client):
        """Test successful validation of an OpenAI API key."""
        # Arrange
        from src.ai.openai_service import _validate_openai_key

        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance
        # Make the models.list() call succeed
        mock_client_instance.models.list.return_value = ["gpt-4", "gpt-3.5-turbo"]

        # Act
        result = _validate_openai_key("valid_key_123")

        # Assert
        assert_that(result, is_(True))
        mock_openai_client.assert_called_once_with(api_key="valid_key_123")
        mock_client_instance.models.list.assert_called_once()

    @patch("src.ai.openai_service.OpenAI")
    def test_validate_openai_key_invalid_key(self, mock_openai_client):
        """Test validation failure with invalid OpenAI API key."""
        # Arrange
        import httpx
        from openai import AuthenticationError

        from src.ai.openai_service import _validate_openai_key

        # Create a mock response for the APIStatusError/AuthenticationError
        mock_response = httpx.Response(
            401, request=httpx.Request("GET", "https://api.openai.com/v1/models")
        )
        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance

        # Create proper AuthenticationError with required parameters
        auth_error = AuthenticationError(
            message="Invalid API key",
            response=mock_response,
            body={
                "error": {"message": "Invalid API key", "type": "invalid_request_error"}
            },
        )
        # Make the models.list() call raise AuthenticationError
        mock_client_instance.models.list.side_effect = auth_error

        # Act
        result = _validate_openai_key("invalid_key")

        # Assert
        assert_that(result, is_(False))
        mock_openai_client.assert_called_once_with(api_key="invalid_key")
        mock_client_instance.models.list.assert_called_once()

    @patch("src.ai.openai_service.OpenAI")
    def test_validate_openai_key_external_error(self, mock_openai_client):
        """Test validation failure due to external issue (like network error)."""
        # Arrange
        from src.ai.openai_service import _validate_openai_key

        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance
        # Make the models.list() call raise a general exception
        mock_client_instance.models.list.side_effect = Exception("Network error")

        # Act
        result = _validate_openai_key("network_issue_key")

        # Assert
        assert_that(result, is_(False))
        mock_openai_client.assert_called_once_with(api_key="network_issue_key")
        mock_client_instance.models.list.assert_called_once()

    @patch("src.ai.openai_service.logger")
    @patch("src.ai.openai_service.OpenAI")
    def test_validate_openai_key_logs_properly(self, mock_openai_client, mock_logger):
        """Test that validation logs appropriately."""
        # Arrange
        from src.ai.openai_service import _validate_openai_key

        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance

        # Act
        _validate_openai_key("valid_key")

        # Assert
        mock_logger.info.assert_any_call("Validating provided OpenAI API key")
        mock_logger.info.assert_any_call("OpenAI API key validation successful")

    @patch("src.ai.openai_service.OpenAI")
    def test_validate_openai_key_empty_key(self, mock_openai_client):
        """Test validation with an empty key."""
        # Arrange
        from src.ai.openai_service import _validate_openai_key

        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance
        mock_client_instance.models.list.side_effect = AuthenticationError(
            message="Invalid API key",
            response=MagicMock(),
            body={
                "error": {"message": "Invalid API key", "type": "invalid_request_error"}
            },
        )
        # Act
        result = _validate_openai_key("some_key")

        # Assert
        assert_that(result, is_(False))
        mock_openai_client.assert_called_once_with(api_key="some_key")
        mock_client_instance.models.list.assert_called_once()

    @patch("src.ai.openai_service.OpenAI")
    def test_validate_openai_key_none_key(self, mock_openai_client):
        """Test validation with a None key."""
        # Arrange
        from src.ai.openai_service import _validate_openai_key

        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance
        mock_client_instance.models.list.side_effect = AuthenticationError(
            message="Invalid API key",
            response=MagicMock(),
            body={
                "error": {"message": "Invalid API key", "type": "invalid_request_error"}
            },
        )

        # Act
        result = _validate_openai_key(None)

        # Assert
        assert_that(result, is_(False))
        mock_openai_client.assert_not_called()
        mock_client_instance.models.list.assert_not_called()
