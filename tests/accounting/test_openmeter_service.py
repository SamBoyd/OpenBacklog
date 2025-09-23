"""
Tests for OpenMeter service.

This module tests the OpenMeter service functionality including the simplified
checkout experience for creating customers and generating Stripe checkout URLs.
"""

import time
from unittest.mock import Mock, patch

import pytest
import requests
import responses
from hamcrest import assert_that, close_to

from src.accounting.openmeter_service import (
    CheckoutOptions,
    CreateCheckoutSessionRequest,
    CreateCheckoutSessionResult,
    CustomerData,
    OpenMeterService,
    TokenBucketRateLimiter,
    UsageAttribution,
)
from src.models import User


class TestOpenMeterService:
    """Test cases for OpenMeterService."""

    @pytest.fixture
    def openmeter_service(self):
        """Create a test instance of OpenMeterService."""
        return OpenMeterService(
            base_url="https://openmeter.cloud", api_token="test-token"
        )

    @pytest.fixture
    def mock_success_response(self):
        """Mock successful response from OpenMeter API."""
        return {
            "customerId": "01JKHFVVZ71HGXD25E28PG8F5Z",
            "stripeCustomerId": "cus_xxx",
            "sessionId": "cs_test_xxx",
            "setupIntentId": "seti_xxx",
            "url": "https://checkout.stripe.com/c/pay/cs_test_xxx",
            "mode": "setup",
            "cancelURL": "https://example.com/cancel",
            "successURL": "https://example.com/success",
            "returnURL": "https://example.com/return",
        }

    def test_service_initialization(self, openmeter_service):
        """Test OpenMeterService initialization."""
        assert openmeter_service.base_url == "https://openmeter.cloud"
        assert openmeter_service.api_token == "test-token"
        assert openmeter_service.session.headers["Authorization"] == "Bearer test-token"
        assert openmeter_service.session.headers["Content-Type"] == "application/json"
        assert openmeter_service.session.headers["Accept"] == "*/*"

    def test_service_initialization_with_trailing_slash(self):
        """Test OpenMeterService initialization with trailing slash in base_url."""
        service = OpenMeterService(
            base_url="https://openmeter.cloud/", api_token="test-token"
        )
        assert service.base_url == "https://openmeter.cloud"

    @responses.activate
    def test_create_checkout_session_success(
        self, openmeter_service, mock_success_response
    ):
        """Test successful checkout session creation."""
        # Mock the API response
        responses.add(
            responses.POST,
            "https://openmeter.cloud/api/v1/stripe/checkout/sessions",
            json=mock_success_response,
            status=201,
        )

        # Call the service
        result = openmeter_service.create_checkout_session(
            customer_name="ACME, Inc.",
            success_url="https://example.com/success",
            customer_key="my-database-id",
            subject_keys=["my-usage-event-subject"],
            currency="USD",
        )

        # Verify the result
        assert isinstance(result, CreateCheckoutSessionResult)
        assert result.customer_id == "01JKHFVVZ71HGXD25E28PG8F5Z"
        assert result.stripe_customer_id == "cus_xxx"
        assert result.session_id == "cs_test_xxx"
        assert result.setup_intent_id == "seti_xxx"
        assert result.url == "https://checkout.stripe.com/c/pay/cs_test_xxx"
        assert result.mode == "setup"
        assert result.success_url == "https://example.com/success"

        # Verify the request was made correctly
        assert len(responses.calls) == 1
        call = responses.calls[0]
        assert (
            call.request.url
            == "https://openmeter.cloud/api/v1/stripe/checkout/sessions"
        )
        assert call.request.method == "POST"
        assert call.request.headers["Authorization"] == "Bearer test-token"
        assert call.request.headers["Content-Type"] == "application/json"

        # Verify request payload
        import json

        assert call.request.body is not None
        request_data = json.loads(call.request.body)
        assert request_data["customer"]["name"] == "ACME, Inc."
        assert request_data["customer"]["key"] == "my-database-id"
        assert request_data["customer"]["usageAttribution"]["subjectKeys"] == [
            "my-usage-event-subject"
        ]
        assert request_data["options"]["successUrl"] == "https://example.com/success"
        assert request_data["options"]["currency"] == "USD"

    @responses.activate
    def test_create_checkout_session_minimal_params(
        self, openmeter_service, mock_success_response
    ):
        """Test checkout session creation with minimal parameters."""
        # Mock the API response
        responses.add(
            responses.POST,
            "https://openmeter.cloud/api/v1/stripe/checkout/sessions",
            json=mock_success_response,
            status=201,
        )

        # Call the service with minimal parameters
        result = openmeter_service.create_checkout_session(
            customer_name="Test Customer", success_url="https://example.com/success"
        )

        # Verify the result
        assert isinstance(result, CreateCheckoutSessionResult)
        assert result.customer_id == "01JKHFVVZ71HGXD25E28PG8F5Z"

        # Verify request payload has defaults
        call = responses.calls[0]
        import json

        assert call.request.body is not None
        request_data = json.loads(call.request.body)
        assert request_data["customer"]["name"] == "Test Customer"
        assert request_data["customer"]["key"] is None
        assert request_data["customer"]["usageAttribution"] is None
        assert request_data["options"]["currency"] == "USD"

    @responses.activate
    def test_create_checkout_session_with_subject_keys(
        self, openmeter_service, mock_success_response
    ):
        """Test checkout session creation with subject keys for usage attribution."""
        # Mock the API response
        responses.add(
            responses.POST,
            "https://openmeter.cloud/api/v1/stripe/checkout/sessions",
            json=mock_success_response,
            status=201,
        )

        # Call the service with subject keys
        result = openmeter_service.create_checkout_session(
            customer_name="Test Customer",
            success_url="https://example.com/success",
            subject_keys=["subject1", "subject2"],
        )

        # Verify request payload includes usage attribution
        call = responses.calls[0]
        import json

        assert call.request.body is not None
        request_data = json.loads(call.request.body)
        assert request_data["customer"]["usageAttribution"]["subjectKeys"] == [
            "subject1",
            "subject2",
        ]

    @responses.activate
    def test_create_checkout_session_http_error(self, openmeter_service):
        """Test checkout session creation with HTTP error."""
        # Mock HTTP error response
        responses.add(
            responses.POST,
            "https://openmeter.cloud/api/v1/stripe/checkout/sessions",
            json={"error": "Bad Request"},
            status=400,
        )

        # Call the service and expect an exception
        with pytest.raises(requests.RequestException):
            openmeter_service.create_checkout_session(
                customer_name="Test Customer", success_url="https://example.com/success"
            )

    @responses.activate
    def test_create_checkout_session_invalid_response(self, openmeter_service):
        """Test checkout session creation with invalid response format."""
        # Mock invalid response
        responses.add(
            responses.POST,
            "https://openmeter.cloud/api/v1/stripe/checkout/sessions",
            json={"invalid": "response"},
            status=201,
        )

        # Call the service and expect a ValueError
        with pytest.raises(ValueError, match="Invalid response from OpenMeter API"):
            openmeter_service.create_checkout_session(
                customer_name="Test Customer", success_url="https://example.com/success"
            )

    @responses.activate
    def test_create_checkout_session_network_error(self, openmeter_service):
        """Test checkout session creation with network error."""
        # Mock network error
        responses.add(
            responses.POST,
            "https://openmeter.cloud/api/v1/stripe/checkout/sessions",
            body=requests.ConnectionError("Network error"),
        )

        # Call the service and expect an exception
        with pytest.raises(requests.RequestException):
            openmeter_service.create_checkout_session(
                customer_name="Test Customer", success_url="https://example.com/success"
            )

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = Mock(spec=User)
        user.id = "test-user-123"
        user.name = "Test User"
        user.email = "test@example.com"
        return user

    @responses.activate
    def test_create_customer_success(self, openmeter_service, mock_user):
        """Test successful customer creation."""
        stripe_customer_id = "cus_test123"

        # Mock subject creation response
        responses.add(
            responses.GET,
            "https://openmeter.cloud/api/v1/customers/test-user-123",
            status=404,
        )
        responses.add(
            responses.POST,
            "https://openmeter.cloud/api/v1/subjects",
            json=[{"id": "subject_123"}],
            status=200,
        )

        # Call the method
        result = openmeter_service.create_customer(mock_user, stripe_customer_id)

        # Verify the result
        assert result == "test-user-123"

        # Verify both API calls were made
        assert len(responses.calls) == 2

        # Verify subject creation call
        subject_call = responses.calls[0]
        assert (
            subject_call.request.url
            == "https://openmeter.cloud/api/v1/customers/test-user-123"
        )
        assert subject_call.request.method == "GET"

        subject_call = responses.calls[1]
        assert subject_call.request.url == "https://openmeter.cloud/api/v1/subjects"
        assert subject_call.request.method == "POST"

        import json

        subject_data = json.loads(subject_call.request.body)
        assert len(subject_data) == 1
        assert subject_data[0]["key"] == "test-user-123"
        assert subject_data[0]["displayName"] == "Test User"
        assert subject_data[0]["metadata"]["externalId"] == "test-user-123"
        assert subject_data[0]["stripeCustomerId"] == "cus_test123"

    @responses.activate
    def test_create_customer_subject_creation_fails(self, openmeter_service, mock_user):
        """Test customer creation when subject creation fails."""
        stripe_customer_id = "cus_test123"

        # Mock subject creation failure
        responses.add(
            responses.GET,
            "https://openmeter.cloud/api/v1/customers/test-user-123",
            status=404,
        )
        responses.add(
            responses.POST,
            "https://openmeter.cloud/api/v1/subjects",
            json={"error": "Subject creation failed"},
            status=400,
        )

        # Call the method and expect an exception
        with pytest.raises(requests.RequestException):
            openmeter_service.create_customer(mock_user, stripe_customer_id)

        # Verify only subject creation was attempted
        assert len(responses.calls) == 2
        assert (
            responses.calls[0].request.url
            == "https://openmeter.cloud/api/v1/customers/test-user-123"
        )
        assert responses.calls[0].request.method == "GET"

        assert (
            responses.calls[1].request.url == "https://openmeter.cloud/api/v1/subjects"
        )
        assert responses.calls[1].request.method == "POST"

    @responses.activate
    def test_create_customer_network_error(self, openmeter_service, mock_user):
        """Test customer creation with network error."""
        stripe_customer_id = "cus_test123"

        # Mock network error on subject creation
        responses.add(
            responses.GET,
            "https://openmeter.cloud/api/v1/customers/test-user-123",
            status=404,
        )
        responses.add(
            responses.POST,
            "https://openmeter.cloud/api/v1/subjects",
            body=requests.ConnectionError("Network error"),
        )

        # Call the method and expect an exception
        with pytest.raises(requests.RequestException):
            openmeter_service.create_customer(mock_user, stripe_customer_id)

    @responses.activate
    def test_create_customer_with_special_characters(self, openmeter_service):
        """Test customer creation with special characters in user data."""
        # Create a user with special characters
        user = Mock(spec=User)
        user.id = "test-user-éñ-123"
        user.name = "Test Üser & Co."
        user.email = "test+special@example.com"

        stripe_customer_id = "cus_test123"

        # Mock successful responses
        responses.add(
            responses.GET,
            "https://openmeter.cloud/api/v1/customers/test-user-%C3%A9%C3%B1-123",
            status=404,
        )
        responses.add(
            responses.POST,
            "https://openmeter.cloud/api/v1/subjects",
            json=[{"id": "subject_123"}],
            status=200,
        )

        # Call the method
        result = openmeter_service.create_customer(user, stripe_customer_id)

        # Verify the result
        assert result == "test-user-éñ-123"

        # Verify the data was properly encoded/sent
        import json

        subject_data = json.loads(responses.calls[1].request.body)
        assert subject_data[0]["key"] == "test-user-éñ-123"
        assert subject_data[0]["displayName"] == "Test Üser & Co."

    @responses.activate
    def test_create_customer_handles_subject_creation_non_200_status(
        self, openmeter_service, mock_user
    ):
        """Test that non-200 status codes for subject creation are handled properly."""
        stripe_customer_id = "cus_test123"

        # Mock subject creation with 201 status (created)
        responses.add(
            responses.GET,
            "https://openmeter.cloud/api/v1/customers/test-user-123",
            status=404,
        )
        responses.add(
            responses.POST,
            "https://openmeter.cloud/api/v1/subjects",
            json={"error": "Unauthorized"},
            status=401,
        )

        # Call the method and expect an exception
        with pytest.raises(requests.RequestException):
            openmeter_service.create_customer(mock_user, stripe_customer_id)


class TestPydanticModels:
    """Test cases for Pydantic models."""

    def test_usage_attribution_model(self):
        """Test UsageAttribution model."""
        usage_attribution = UsageAttribution(subjectKeys=["key1", "key2"])
        assert usage_attribution.subject_keys == ["key1", "key2"]

    def test_customer_data_model(self):
        """Test CustomerData model."""
        customer_data = CustomerData(
            name="Test Customer",
            key="test-key",
            usageAttribution=UsageAttribution(subjectKeys=["key1"]),
        )
        assert customer_data.name == "Test Customer"
        assert customer_data.key == "test-key"
        assert customer_data.usage_attribution is not None
        assert customer_data.usage_attribution.subject_keys == ["key1"]

    def test_customer_data_model_minimal(self):
        """Test CustomerData model with minimal data."""
        customer_data = CustomerData(name="Test Customer")
        assert customer_data.name == "Test Customer"
        assert customer_data.key is None
        assert customer_data.usage_attribution is None

    def test_checkout_options_model(self):
        """Test CheckoutOptions model."""
        options = CheckoutOptions(
            successUrl="https://example.com/success", currency="EUR"
        )
        assert options.success_url == "https://example.com/success"
        assert options.currency == "EUR"

    def test_checkout_options_model_default_currency(self):
        """Test CheckoutOptions model with default currency."""
        options = CheckoutOptions(successUrl="https://example.com/success")
        assert options.currency == "USD"

    def test_create_checkout_session_request_model(self):
        """Test CreateCheckoutSessionRequest model."""
        customer_data = CustomerData(name="Test Customer")
        options = CheckoutOptions(successUrl="https://example.com/success")

        request = CreateCheckoutSessionRequest(customer=customer_data, options=options)

        assert request.customer.name == "Test Customer"
        assert request.options.success_url == "https://example.com/success"

    def test_create_checkout_session_result_model(self):
        """Test CreateCheckoutSessionResult model."""
        result_data = {
            "customerId": "01JKHFVVZ71HGXD25E28PG8F5Z",
            "mode": "setup",
            "sessionId": "cs_test_xxx",
            "setupIntentId": "seti_xxx",
            "stripeCustomerId": "cus_xxx",
            "successURL": "https://example.com/success",
            "url": "https://checkout.stripe.com/c/pay/cs_test_xxx",
        }

        result = CreateCheckoutSessionResult(**result_data)
        assert result.customer_id == "01JKHFVVZ71HGXD25E28PG8F5Z"
        assert result.stripe_customer_id == "cus_xxx"
        assert result.session_id == "cs_test_xxx"
        assert result.setup_intent_id == "seti_xxx"
        assert result.url == "https://checkout.stripe.com/c/pay/cs_test_xxx"
        assert result.mode == "setup"
        assert result.success_url == "https://example.com/success"

    def test_create_checkout_session_result_model_with_optional_fields(self):
        """Test CreateCheckoutSessionResult model with optional fields."""
        result_data = {
            "customerId": "01JKHFVVZ71HGXD25E28PG8F5Z",
            "mode": "setup",
            "sessionId": "cs_test_xxx",
            "setupIntentId": "seti_xxx",
            "stripeCustomerId": "cus_xxx",
            "successURL": "https://example.com/success",
            "url": "https://checkout.stripe.com/c/pay/cs_test_xxx",
            "cancelURL": "https://example.com/cancel",
            "returnURL": "https://example.com/return",
        }

        result = CreateCheckoutSessionResult(**result_data)
        assert result.cancel_url == "https://example.com/cancel"
        assert result.return_url == "https://example.com/return"


class TestTokenBucketRateLimiter:
    """Test the TokenBucketRateLimiter class."""

    def test_init_default_burst_capacity(self):
        """Test that burst capacity defaults to rate when not specified."""
        limiter = TokenBucketRateLimiter(rate=10.0)
        assert limiter.rate == 10.0
        assert limiter.burst_capacity == 10
        assert limiter.tokens == 10.0

    def test_init_custom_burst_capacity(self):
        """Test initialization with custom burst capacity."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst_capacity=5)
        assert limiter.rate == 10.0
        assert limiter.burst_capacity == 5
        assert limiter.tokens == 5.0

    def test_wait_if_needed_with_available_tokens(self):
        """Test that no waiting occurs when tokens are available."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst_capacity=5)

        start_time = time.time()
        limiter.wait_if_needed()
        end_time = time.time()

        # Should not wait
        assert end_time - start_time < 0.01
        assert limiter.tokens == 4.0  # One token consumed

    def test_wait_if_needed_blocks_when_no_tokens(self):
        """Test that waiting occurs when no tokens are available."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst_capacity=1)

        # Consume the initial token
        limiter.wait_if_needed()
        assert limiter.tokens == 0.0

        # Next call should block
        start_time = time.time()
        limiter.wait_if_needed()
        end_time = time.time()

        # Should have waited approximately 0.1 seconds (1/10 rate)
        wait_time = end_time - start_time
        assert wait_time >= 0.09  # Allow some tolerance
        assert wait_time <= 0.15  # But not too much
        assert limiter.tokens == 0.0

    def test_token_refill_over_time(self):
        """Test that tokens are refilled over time."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst_capacity=5)

        # Consume all tokens
        for _ in range(5):
            limiter.wait_if_needed()
        assert_that(limiter.tokens, close_to(0.0, 0.01))

        # Wait for tokens to refill
        time.sleep(0.6)  # Should refill 6 tokens, but capacity is 5

        # Check that tokens have been refilled (up to capacity)
        limiter.wait_if_needed()  # This should not block
        assert limiter.tokens == 4.0  # 5 - 1 consumed

    def test_burst_capacity_limit(self):
        """Test that tokens don't exceed burst capacity."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst_capacity=3)

        # Wait longer than needed to fill beyond capacity
        time.sleep(1.0)  # Would refill 10 tokens if no limit

        # Verify tokens are capped at burst capacity
        limiter.wait_if_needed()
        assert limiter.tokens == 2.0  # 3 - 1 consumed


class TestOpenMeterServiceRateLimiting:
    """Test rate limiting functionality in OpenMeterService."""

    def test_init_with_default_rate_limits(self):
        """Test initialization with default rate limiting parameters."""
        service = OpenMeterService(
            base_url="https://api.example.com", api_token="test-token"
        )

        assert service.checkout_rate_limiter.rate == 48.0
        assert service.checkout_rate_limiter.burst_capacity == 10

    def test_init_with_custom_rate_limits(self):
        """Test initialization with custom rate limiting parameters."""
        service = OpenMeterService(
            base_url="https://api.example.com",
            api_token="test-token",
            checkout_rate_limit=25.0,
            checkout_burst_capacity=5,
        )

        assert service.checkout_rate_limiter.rate == 25.0
        assert service.checkout_rate_limiter.burst_capacity == 5

    @responses.activate
    def test_create_checkout_query_usage_applies_rate_limiting(self):
        """Test that rate limiting is applied to query usage."""
        # Mock successful response
        mock_response = {
            "data": [{"timestamp": "2024-01-01T00:00:00Z", "value": 100.0}]
        }
        responses.add(
            responses.GET,
            "https://api.example.com/api/v1/meters/cost_total/query",
            json=mock_response,
            status=200,
        )

        service = OpenMeterService(
            base_url="https://api.example.com",
            api_token="test-token",
            checkout_rate_limit=10.0,
            checkout_burst_capacity=1,
        )

        # First call should succeed quickly
        start_time = time.time()
        result1 = service.query_usage(subject="user_123", meter_slug="cost_total")
        end_time = time.time()

        assert end_time - start_time < 0.01  # Should be fast
        assert result1.data == [{"timestamp": "2024-01-01T00:00:00Z", "value": 100.0}]

        # Second call should be rate limited
        start_time = time.time()
        result2 = service.query_usage(subject="user_123", meter_slug="cost_total")
        end_time = time.time()

        # Should have waited approximately 0.1 seconds (1/10 rate)
        wait_time = end_time - start_time
        assert wait_time >= 0.09  # Allow some tolerance
        assert wait_time <= 0.15  # But not too much
        assert result2.data == [{"timestamp": "2024-01-01T00:00:00Z", "value": 100.0}]

        # Verify both requests were made
        assert len(responses.calls) == 2

    @responses.activate
    def test_query_usage_rate_limit_doesnt_affect_other_methods(self):
        """Test that rate limiting only applies to query usage."""
        service = OpenMeterService(
            base_url="https://api.example.com",
            api_token="test-token",
            checkout_rate_limit=1.0,  # Very low rate limit
            checkout_burst_capacity=1,
        )

        # Other methods should not be affected by rate limiting
        mock_response = {
            "id": "token_123",
            "subject": "user_123",
            "expiresAt": "2024-12-31T23:59:59Z",
            "token": "test_token",
            "allowedMeterSlugs": ["cost_total"],
        }
        responses.add(
            responses.POST,
            "https://openmeter.cloud/api/v1/portal/tokens",
            json=mock_response,
            status=200,
        )

        # This should execute quickly without rate limiting
        start_time = time.time()
        service.get_portal_token("user_123")
        end_time = time.time()

        assert end_time - start_time < 0.01  # Should be fast

        # This should execute quickly without rate limiting
        start_time = time.time()
        service.get_portal_token("user_123")
        end_time = time.time()

        assert end_time - start_time < 0.01  # Should be fast

    @responses.activate
    def test_query_usage_error_handling_with_rate_limiting(self):
        """Test that errors are handled correctly even with rate limiting."""
        responses.add(
            responses.GET,
            "https://api.example.com/api/v1/meters/cost_total/query",
            json={"error": "API Error"},
            status=500,
        )

        service = OpenMeterService(
            base_url="https://api.example.com", api_token="test-token"
        )

        # Should still apply rate limiting even when request fails
        with pytest.raises(requests.RequestException):
            service.query_usage(subject="user_123", meter_slug="cost_total")

        # Verify rate limiter was called (token consumed)
        assert service.checkout_rate_limiter.tokens == 9.0  # 10 - 1 consumed
