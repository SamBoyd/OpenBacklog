import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, cast

import instructor
from fastapi import HTTPException
from openai import APIConnectionError, APITimeoutError, AuthenticationError, OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from src.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMAPIError(Exception):
    """Exception raised for errors in the LLM API call."""

    pass


class LLMTimeoutError(LLMAPIError):
    """Exception raised for timeout errors in the LLM API call."""

    pass


class LLMConnectionError(LLMAPIError):
    """Exception raised for connection errors in the LLM API call."""

    pass


def call_llm_api(
    messages: List[ChatCompletionMessageParam],
    api_key: str,
    response_model: Optional[Type[T]] = None,
    validation_context: Optional[dict] = None,
) -> Any:
    """
    Call the OpenAI API with the given messages and validate the response using Instructor.

    Args:
        messages (List[ChatCompletionMessageParam]): The list of messages (system, user, assistant) to send to the LLM.
        api_key (str): The OpenAI API key to use for the request.
        response_model (Optional[Type[BaseModel]]): The Pydantic model to validate the response against.
            If None, returns the raw string response.
        validation_context (Optional[dict]): Context to pass to Pydantic validation (used by instructor).

    Returns:
        Any: If response_model is provided, returns an instance of that model.
             Otherwise, returns the raw string response.

    Raises:
        LLMTimeoutError: If the API call times out.
        LLMConnectionError: If there's a connection error.
        LLMAPIError: For other API-related errors.
    """
    if not api_key:
        raise ValueError("API key must be provided to call the LLM API")

    try:
        # Initialize the OpenAI client with the provided key
        client = OpenAI(api_key=api_key)

        if response_model:
            # Use instructor to patch the client and validate the response
            instructor_client = instructor.from_openai(client)

            # Make the API call with structured output validation and context
            response = instructor_client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=0.7,
                response_model=response_model,
                validation_context=validation_context,
            )

            return response
        else:
            # Make the standard API call without validation
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=0.7,
            )

            # Extract and return the generated text
            response_text = response.choices[0].message.content

            if not response_text:
                raise LLMAPIError("Empty response from LLM API")

            return response_text

    except APITimeoutError:
        logger.exception("LLM API call timed out")
        raise LLMTimeoutError("The request to the LLM API timed out")

    except APIConnectionError:
        logger.exception("Connection error when calling LLM API")
        raise LLMConnectionError("Failed to connect to the LLM API")

    except Exception as e:
        # Catch potential OpenAI specific errors if needed, otherwise generalize
        logger.exception(f"Error when calling LLM API: {e}")
        raise LLMAPIError(f"An unexpected error occurred when calling the LLM API: {e}")


def _validate_openai_key(key: Optional[str]) -> bool:
    """
    Validates an OpenAI API key by making a simple API call.

    Args:
        key (Optional[str]): The OpenAI API key to validate.

    Returns:
        bool: True if the key is valid, False otherwise.
    """
    if not key:  # Handle None or empty string early
        logger.warning("OpenAI API key validation failed: Key is missing or empty")
        return False

    try:
        logger.info("Validating provided OpenAI API key")
        client = OpenAI(api_key=key)
        # Use a simple, low-cost API call to verify the key is valid
        client.models.list()
        logger.info("OpenAI API key validation successful")
        return True
    except AuthenticationError:
        logger.warning("OpenAI API key validation failed: Invalid credentials")
        return False
    except Exception as e:
        logger.exception(
            f"An unexpected error occurred during OpenAI key validation: {e}"
        )
        return False
