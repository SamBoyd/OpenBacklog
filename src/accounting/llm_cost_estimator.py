"""
LLM Cost Estimation Service

This service estimates the cost of LLM requests before they are made to help
with account balance enforcement. It uses litellm's model_cost dictionary for
up-to-date pricing information.
"""

import logging
import math
from typing import Dict, List, Optional

import litellm
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Safety margins and constants
DEFAULT_RESPONSE_TOKEN_ESTIMATE = 500  # Conservative estimate for response tokens
SAFETY_MARGIN_MULTIPLIER = 1.2  # 20% safety margin
COST_PRECISION = 7  # 7 decimal places for cost precision (from usage_tracker.py)


class SearchContextCost(BaseModel):
    """Model for search context cost information."""

    search_context_size_low: float = Field(default=0.0)
    search_context_size_medium: float = Field(default=0.0)
    search_context_size_high: float = Field(default=0.0)


class ModelPricing(BaseModel):
    """Pydantic model for litellm model pricing information."""

    # Token limits
    max_tokens: Optional[int] = Field(default=None, description="Legacy parameter")
    max_input_tokens: Optional[int] = Field(
        default=None, description="Max input tokens"
    )
    max_output_tokens: Optional[int] = Field(
        default=None, description="Max output tokens"
    )

    # Core pricing
    input_cost_per_token: float = Field(default=0.0, description="Cost per input token")
    output_cost_per_token: float = Field(
        default=0.0, description="Cost per output token"
    )
    output_cost_per_reasoning_token: Optional[float] = Field(
        default=None, description="Cost per reasoning token"
    )

    # Provider and capabilities
    litellm_provider: Optional[str] = Field(
        default=None, description="LiteLLM provider name"
    )
    mode: Optional[str] = Field(
        default=None, description="Model mode (chat, embedding, etc.)"
    )

    # Feature support flags
    supports_function_calling: Optional[bool] = Field(default=None)
    supports_parallel_function_calling: Optional[bool] = Field(default=None)
    supports_vision: Optional[bool] = Field(default=None)
    supports_audio_input: Optional[bool] = Field(default=None)
    supports_audio_output: Optional[bool] = Field(default=None)
    supports_prompt_caching: Optional[bool] = Field(default=None)
    supports_response_schema: Optional[bool] = Field(default=None)
    supports_system_messages: Optional[bool] = Field(default=None)
    supports_reasoning: Optional[bool] = Field(default=None)
    supports_web_search: Optional[bool] = Field(default=None)

    # Additional cost structures
    search_context_cost_per_query: Optional[SearchContextCost] = Field(default=None)
    file_search_cost_per_1k_calls: Optional[float] = Field(default=None)
    file_search_cost_per_gb_per_day: Optional[float] = Field(default=None)
    vector_store_cost_per_gb_per_day: Optional[float] = Field(default=None)
    computer_use_input_cost_per_1k_tokens: Optional[float] = Field(default=None)
    computer_use_output_cost_per_1k_tokens: Optional[float] = Field(default=None)
    code_interpreter_cost_per_session: Optional[float] = Field(default=None)

    # Regional and lifecycle
    supported_regions: Optional[List[str]] = Field(default=None)
    deprecation_date: Optional[str] = Field(
        default=None, description="YYYY-MM-DD format"
    )


class LLMCostEstimatorError(Exception):
    """Exception raised for LLM cost estimation errors."""

    pass


class LLMCostEstimator:
    """Service for estimating LLM request costs before execution."""

    def __init__(self, model_name: str = "gpt-4.1-nano"):
        """
        Initialize the cost estimator.

        Args:
            model_name: The name of the LLM model to use for pricing

        Raises:
            LLMCostEstimatorError: If pricing information is not available for the model
        """
        self.model_name = model_name
        self.pricing = self._get_model_pricing(model_name)

        if not self.pricing:
            raise LLMCostEstimatorError(
                f"No pricing information found for model '{model_name}'. "
                f"Available models: {list(litellm.model_cost.keys())[:10]}..."
            )

    def _get_model_pricing(self, model_name: str) -> Optional[ModelPricing]:
        """
        Get pricing information for a model from litellm.

        Args:
            model_name: The name of the model

        Returns:
            ModelPricing instance or None if not found
        """
        try:
            model_cost = litellm.model_cost
            if model_name in model_cost:
                pricing_data = model_cost[model_name]

                # Create ModelPricing instance from the raw data
                pricing = ModelPricing(**pricing_data)

                # Validate that we have the essential pricing information
                if (
                    pricing.input_cost_per_token == 0.0
                    and pricing.output_cost_per_token == 0.0
                ):
                    logger.error(
                        f"Model {model_name} has zero costs for both input and output tokens"
                    )
                    return None

                return pricing
        except Exception as e:
            logger.error(f"Error getting pricing for model {model_name}: {e}")

        return None

    def estimate_token_count(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.

        This is a simplified estimation. For more accurate results,
        consider using tiktoken or similar libraries.

        Args:
            text: The text to estimate tokens for

        Returns:
            Estimated number of tokens
        """
        if not text:
            return 0

        # Rough estimation: 1 token ≈ 4 characters for English text
        # This is conservative and may overestimate, which is preferable
        # for cost estimation purposes
        return math.ceil(len(text) / 3.5)

    def estimate_messages_token_count(
        self, messages: List[ChatCompletionMessageParam]
    ) -> int:
        """
        Estimate the total token count for a list of messages.

        Args:
            messages: List of chat completion messages

        Returns:
            Estimated total input token count
        """
        total_tokens = 0

        for message in messages:
            # Add tokens for role
            total_tokens += 3  # Rough estimate for role tokens

            # Add tokens for content
            content = message.get("content", "")
            if isinstance(content, str):
                total_tokens += self.estimate_token_count(content)
            elif isinstance(content, list):
                # Handle multimodal content (text + images)
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        total_tokens += self.estimate_token_count(item.get("text", ""))
                    # Note: Image tokens would need special handling

        # Add overhead for message formatting
        total_tokens += len(messages) * 3  # Rough estimate for message formatting

        return total_tokens

    def estimate_request_cost(
        self,
        messages: List[ChatCompletionMessageParam],
        response_tokens: Optional[int] = None,
    ) -> float:
        """
        Estimate the cost of an LLM request in dollars.

        Args:
            messages: List of chat completion messages
            response_tokens: Estimated response tokens (uses default if not provided)

        Returns:
            Estimated cost in dollars
        """
        if not messages:
            return 0.0

        # Estimate input tokens
        input_tokens = self.estimate_messages_token_count(messages)

        # Use provided response tokens or default estimate
        if response_tokens is None:
            response_tokens = DEFAULT_RESPONSE_TOKEN_ESTIMATE

        # Calculate costs using litellm pricing
        input_cost = input_tokens * self.pricing.input_cost_per_token
        output_cost = response_tokens * self.pricing.output_cost_per_token

        total_cost = input_cost + output_cost

        # Apply safety margin
        total_cost_with_margin = total_cost * SAFETY_MARGIN_MULTIPLIER

        logger.debug(
            f"Cost estimation for {self.model_name}: "
            f"input_tokens={input_tokens}, response_tokens={response_tokens}, "
            f"input_cost=${input_cost:.6f}, output_cost=${output_cost:.6f}, "
            f"total_cost=${total_cost:.6f}, with_margin=${total_cost_with_margin:.6f}"
        )

        return total_cost_with_margin

    def estimate_request_cost_cents(
        self,
        messages: List[ChatCompletionMessageParam],
        response_tokens: Optional[int] = None,
    ) -> float:
        """
        Estimate the cost of an LLM request in cents.

        Args:
            messages: List of chat completion messages
            response_tokens: Estimated response tokens (uses default if not provided)

        Returns:
            Estimated cost in cents, rounded up to the specified precision
        """
        cost_dollars = self.estimate_request_cost(messages, response_tokens)
        cost_cents = cost_dollars * 100

        # Round up to the specified precision (same as usage_tracker.py)
        exp = 10**COST_PRECISION
        cost_cents_rounded = math.ceil(cost_cents * exp) / exp

        return cost_cents_rounded

    def get_model_info(self) -> Dict[str, any]:
        """
        Get information about the current model and pricing.

        Returns:
            Dictionary containing model information
        """
        return {
            "model_name": self.model_name,
            "pricing": self.pricing.model_dump() if self.pricing else None,
            "safety_margin": SAFETY_MARGIN_MULTIPLIER,
            "default_response_tokens": DEFAULT_RESPONSE_TOKEN_ESTIMATE,
        }


def create_cost_estimator(model_name: str = "gpt-4.1-nano") -> LLMCostEstimator:
    """
    Factory function to create a cost estimator instance.

    Args:
        model_name: The name of the LLM model to use for pricing

    Returns:
        LLMCostEstimator instance

    Raises:
        LLMCostEstimatorError: If pricing information is not available for the model
    """
    return LLMCostEstimator(model_name)


def validate_model_pricing(model_name: str = "gpt-4.1-nano") -> None:
    """
    Validate that pricing information is available for the specified model.
    This should be called during app startup to fail early if pricing is missing.

    Args:
        model_name: The name of the model to validate pricing for

    Raises:
        LLMCostEstimatorError: If pricing information is not available for the model
    """
    try:
        create_cost_estimator(model_name)
        logger.info(
            f"LLM cost estimator validated successfully for model '{model_name}'"
        )
    except LLMCostEstimatorError as e:
        logger.error(f"LLM cost estimator validation failed: {e}")
        raise
