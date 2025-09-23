from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, close_to
from openai.types.chat import ChatCompletionMessageParam

from src.accounting.llm_cost_estimator import (
    LLMCostEstimator,
    LLMCostEstimatorError,
    ModelPricing,
    SearchContextCost,
    create_cost_estimator,
    validate_model_pricing,
)

# Mock Pricing
# ModelPricing(max_tokens=32768, max_input_tokens=1047576, max_output_tokens=32768, input_cost_per_token=1e-07, output_c..._output_cost_per_1k_tokens=None, code_interpreter_cost_per_session=None, supported_regions=None, deprecation_date=None).input_cost_per_token


class TestLLMCostEstimator:
    """Test suite for LLMCostEstimator class."""

    def test_constructor(self, mock_litellm_model_cost):
        """Test constructor with valid model."""
        estimator = LLMCostEstimator("gpt-4.1-nano")

        assert estimator.model_name == "gpt-4.1-nano"
        assert estimator.pricing is not None
        assert estimator.pricing.input_cost_per_token == 1e-07
        assert estimator.pricing.output_cost_per_token == 4e-07

    def test_constructor_invalid_model(self, mock_litellm_model_cost):
        """Test constructor with invalid model raises error."""
        with pytest.raises(LLMCostEstimatorError) as exc_info:
            LLMCostEstimator("invalid-model")

        assert "No pricing information found" in str(exc_info.value)

    def test_constructor_zero_costs(self, mock_litellm_model_cost):
        """Test constructor with model that has zero costs."""
        # Temporarily modify the mock to have zero costs
        with patch.dict(
            mock_litellm_model_cost,
            {
                "zero-cost-model": {
                    "input_cost_per_token": 0.0,
                    "output_cost_per_token": 0.0,
                }
            },
        ):
            with pytest.raises(LLMCostEstimatorError) as exc_info:
                LLMCostEstimator("zero-cost-model")

            assert "No pricing information found" in str(exc_info.value)

    def test_get_model_pricing(self, mock_litellm_model_cost):
        """Test _get_model_pricing method with mocked litellm.model_cost."""
        estimator = LLMCostEstimator("gpt-4.1-nano")

        assert estimator.pricing.input_cost_per_token == 1e-07
        assert estimator.pricing.output_cost_per_token == 4e-07
        assert estimator.pricing.max_tokens == 32768
        assert estimator.pricing.litellm_provider == "openai"

    def test_get_model_pricing_not_found(self, mock_litellm_model_cost):
        """Test _get_model_pricing when model is not found."""
        estimator = LLMCostEstimator.__new__(LLMCostEstimator)
        estimator.model_name = "not-found"

        result = estimator._get_model_pricing("not-found")
        assert result is None

    def test_estimate_token_count_normal(self):
        """Test estimate_token_count with normal text."""
        estimator = LLMCostEstimator.__new__(LLMCostEstimator)

        # Test with normal text
        text = "Hello world, this is a test message."
        tokens = estimator.estimate_token_count(text)

        # Should be roughly len(text) / 3.5, rounded up
        expected_tokens = 11
        assert tokens == expected_tokens

    def test_estimate_token_count_edge_cases(self):
        """Test estimate_token_count with edge cases."""
        estimator = LLMCostEstimator.__new__(LLMCostEstimator)

        # Test empty string
        assert estimator.estimate_token_count("") == 0

        # Test very short text
        assert estimator.estimate_token_count("Hi") == 1

        # Test very long text
        long_text = "x" * 1000
        tokens = estimator.estimate_token_count(long_text)
        expected_tokens = 286  # 1000 / 3.5, rounded up
        assert tokens == expected_tokens

    @patch.object(LLMCostEstimator, "estimate_token_count")
    def test_estimate_messages_token_count(self, mock_estimate_tokens):
        """Test estimate_messages_token_count with mocked estimate_token_count."""
        estimator = LLMCostEstimator.__new__(LLMCostEstimator)
        mock_estimate_tokens.return_value = 10

        messages: List[ChatCompletionMessageParam] = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]

        total_tokens = estimator.estimate_messages_token_count(messages)

        # Should call estimate_token_count for each message content
        assert mock_estimate_tokens.call_count == 3

        # Total should include role tokens (3 per message) + content tokens + formatting overhead
        # 3 messages * (3 role tokens + 10 content tokens) + 3 messages * 3 formatting = 48
        expected_tokens = 3 * (3 + 10) + 3 * 3
        assert total_tokens == expected_tokens

    @patch.object(LLMCostEstimator, "estimate_token_count")
    def test_estimate_messages_token_count_multimodal(self, mock_estimate_tokens):
        """Test estimate_messages_token_count with multimodal content."""
        estimator = LLMCostEstimator.__new__(LLMCostEstimator)
        mock_estimate_tokens.return_value = 5

        messages: List[ChatCompletionMessageParam] = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/jpeg;base64,..."},
                    },
                ],
            }
        ]

        total_tokens = estimator.estimate_messages_token_count(messages)

        # Should only call estimate_token_count for text content
        mock_estimate_tokens.assert_called_once_with("Describe this image")

        # Total should include role tokens + text content tokens + formatting overhead
        expected_tokens = 3 + 5 + 3  # role + content + formatting
        assert total_tokens == expected_tokens

    def test_estimate_request_cost_no_messages(self, mock_litellm_model_cost):
        """Test estimate_request_cost with no messages."""
        estimator = LLMCostEstimator("gpt-4.1-nano")

        cost = estimator.estimate_request_cost([])
        assert cost == 0.0

    def test_estimate_request_cost_no_pricing(self, mock_litellm_model_cost):
        """Test estimate_request_cost when pricing is None."""
        estimator = LLMCostEstimator.__new__(LLMCostEstimator)
        estimator.model_name = "test-model"
        estimator.pricing = None

        with pytest.raises(AttributeError):
            estimator.estimate_request_cost([{"role": "user", "content": "test"}])

    @patch.object(LLMCostEstimator, "estimate_messages_token_count")
    def test_estimate_request_cost_with_safety_margin(
        self, mock_estimate_tokens, mock_litellm_model_cost
    ):
        """Test estimate_request_cost applies safety margin correctly."""
        estimator = LLMCostEstimator("gpt-4.1-nano")
        mock_estimate_tokens.return_value = 100  # 100 input tokens

        messages: List[ChatCompletionMessageParam] = [
            {"role": "user", "content": "test"}
        ]
        cost = estimator.estimate_request_cost(messages, response_tokens=50)

        expected_cost = 3.6e-05
        assert_that(cost, close_to(expected_cost, 1e-06))

    @patch.object(LLMCostEstimator, "estimate_messages_token_count")
    def test_estimate_request_cost_default_response_tokens(
        self, mock_estimate_tokens, mock_litellm_model_cost
    ):
        """Test estimate_request_cost uses default response tokens when not provided."""
        estimator = LLMCostEstimator("gpt-4.1-nano")
        mock_estimate_tokens.return_value = 100

        messages: List[ChatCompletionMessageParam] = [
            {"role": "user", "content": "test"}
        ]
        cost = estimator.estimate_request_cost(messages)

        # Should use default response tokens (500)
        expected_cost = 0.00025
        assert_that(cost, close_to(expected_cost, 0.00001))

    @patch.object(LLMCostEstimator, "estimate_request_cost")
    def test_estimate_request_cost_cents(
        self, mock_estimate_cost, mock_litellm_model_cost
    ):
        """Test estimate_request_cost_cents converts dollars to cents correctly."""
        estimator = LLMCostEstimator("gpt-4.1-nano")
        mock_estimate_cost.return_value = 0.123456789  # Some dollar amount

        messages: List[ChatCompletionMessageParam] = [
            {"role": "user", "content": "test"}
        ]
        cost_cents = estimator.estimate_request_cost_cents(messages)

        # Should convert to cents and round up to 7 decimal places
        expected_cents = 12.3456789  # 0.123456789 * 100
        assert cost_cents == expected_cents

    def test_get_model_info(self, mock_litellm_model_cost):
        """Test get_model_info returns correct information."""
        estimator = LLMCostEstimator("gpt-4.1-nano")
        info = estimator.get_model_info()

        assert info["model_name"] == "gpt-4.1-nano"
        assert info["safety_margin"] == 1.2
        assert info["default_response_tokens"] == 500
        assert info["pricing"] is not None
        assert info["pricing"]["input_cost_per_token"] == 1e-07

    def test_get_model_info_no_pricing(self, mock_litellm_model_cost):
        """Test get_model_info when pricing is None."""
        estimator = LLMCostEstimator.__new__(LLMCostEstimator)
        estimator.model_name = "test-model"
        estimator.pricing = None

        info = estimator.get_model_info()

        assert info["model_name"] == "test-model"
        assert info["pricing"] is None
        assert info["safety_margin"] == 1.2
        assert info["default_response_tokens"] == 500


class TestFactoryFunctions:
    """Test suite for factory functions."""

    def test_create_cost_estimator(self, mock_litellm_model_cost):
        """Test create_cost_estimator factory function."""
        estimator = create_cost_estimator("gpt-4.1-nano")

        assert isinstance(estimator, LLMCostEstimator)
        assert estimator.model_name == "gpt-4.1-nano"

    def test_validate_model_pricing_success(self, mock_litellm_model_cost):
        """Test validate_model_pricing with valid model."""
        # Should not raise an exception
        validate_model_pricing("gpt-4.1-nano")

    def test_validate_model_pricing_failure(self, mock_litellm_model_cost):
        """Test validate_model_pricing with invalid model."""
        with pytest.raises(LLMCostEstimatorError):
            validate_model_pricing("invalid-model")


class TestModelPricing:
    """Test suite for ModelPricing Pydantic model."""

    def test_model_pricing_creation(self):
        """Test ModelPricing model creation with valid data."""
        pricing_data = {
            "input_cost_per_token": 0.001,
            "output_cost_per_token": 0.002,
            "max_tokens": 4096,
            "litellm_provider": "openai",
            "supports_function_calling": True,
        }

        pricing = ModelPricing(**pricing_data)

        assert pricing.input_cost_per_token == 0.001
        assert pricing.output_cost_per_token == 0.002
        assert pricing.max_tokens == 4096
        assert pricing.litellm_provider == "openai"
        assert pricing.supports_function_calling is True

    def test_model_pricing_defaults(self):
        """Test ModelPricing model with default values."""
        pricing = ModelPricing()

        assert pricing.input_cost_per_token == 0.0
        assert pricing.output_cost_per_token == 0.0
        assert pricing.max_tokens is None
        assert pricing.litellm_provider is None

    def test_model_pricing_with_search_context(self):
        """Test ModelPricing model with search context cost."""
        search_context = SearchContextCost(
            search_context_size_low=0.01,
            search_context_size_medium=0.02,
            search_context_size_high=0.03,
        )

        pricing_data = {
            "input_cost_per_token": 0.001,
            "output_cost_per_token": 0.002,
            "search_context_cost_per_query": search_context,
        }

        pricing = ModelPricing(**pricing_data)

        assert pricing.search_context_cost_per_query is not None
        assert pricing.search_context_cost_per_query.search_context_size_low == 0.01
        assert pricing.search_context_cost_per_query.search_context_size_medium == 0.02
        assert pricing.search_context_cost_per_query.search_context_size_high == 0.03
