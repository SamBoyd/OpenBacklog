import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import stripe
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.accounting.stripe_views import stripe_webhook_handler
from src.main import app

client = TestClient(app)


class TestStripeWebhookHandler:
    """Test cases for the stripe_webhook_handler endpoint."""

    @pytest.mark.asyncio
    @patch("src.accounting.stripe_views.stripe.Webhook.construct_event")
    @patch("src.accounting.stripe_views.StripeService")
    async def test_webhook_checkout_session_completed_success(
        self, mock_stripe_service_class, mock_construct_event, session: Session
    ):
        """Test successful processing of checkout.session.completed webhook."""
        # Mock webhook event construction
        mock_event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test123",
                    "metadata": {
                        "user_id": str(uuid.uuid4()),
                        "topup_amount_cents": "1000",
                        "type": "account_topup",
                    },
                    "payment_status": "paid",
                }
            },
        }
        mock_construct_event.return_value = mock_event

        # Mock StripeService
        mock_stripe_service = MagicMock()
        mock_stripe_service_class.return_value = mock_stripe_service

        # Mock request
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=b'{"test": "data"}')
        mock_request.headers = {"stripe-signature": "test_signature"}

        # Call the function
        response = await stripe_webhook_handler(mock_request, session)

        # Verify the response
        assert response.status_code == 200
        assert response.body is not None

        # Verify StripeService was called
        mock_stripe_service_class.assert_called_once_with(session)
        mock_stripe_service.handle_checkout_session_completed.assert_called_once_with(
            mock_event
        )

    @pytest.mark.asyncio
    @patch("src.accounting.stripe_views.stripe.Webhook.construct_event")
    @patch("src.accounting.stripe_views.StripeService")
    async def test_webhook_checkout_session_expired(
        self, mock_stripe_service_class, mock_construct_event, session: Session
    ):
        """Test successful processing of checkout.session.expired webhook."""
        # Mock webhook event construction
        mock_event = {
            "type": "checkout.session.expired",
            "data": {
                "object": {"id": "cs_test123", "metadata": {"type": "account_topup"}}
            },
        }
        mock_construct_event.return_value = mock_event

        # Mock StripeService
        mock_stripe_service = MagicMock()
        mock_stripe_service_class.return_value = mock_stripe_service

        # Mock request
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=b'{"test": "data"}')
        mock_request.headers = {"stripe-signature": "test_signature"}

        # Call the function
        response = await stripe_webhook_handler(mock_request, session)

        # Verify the response
        assert response.status_code == 200
        assert response.body is not None

        # Verify StripeService was called
        mock_stripe_service_class.assert_called_once_with(session)
        mock_stripe_service.handle_checkout_session_expired.assert_called_once_with(
            mock_event
        )

    @pytest.mark.asyncio
    @patch("src.accounting.stripe_views.stripe.Webhook.construct_event")
    @patch("src.accounting.stripe_views.StripeService")
    async def test_webhook_checkout_session_async_payment_failed(
        self, mock_stripe_service_class, mock_construct_event, session: Session
    ):
        """Test successful processing of checkout.session.async_payment_failed webhook."""
        # Mock webhook event construction
        mock_event = {
            "type": "checkout.session.async_payment_failed",
            "data": {
                "object": {"id": "cs_test123", "metadata": {"type": "account_topup"}}
            },
        }
        mock_construct_event.return_value = mock_event

        # Mock StripeService
        mock_stripe_service = MagicMock()
        mock_stripe_service_class.return_value = mock_stripe_service

        # Mock request
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=b'{"test": "data"}')
        mock_request.headers = {"stripe-signature": "test_signature"}

        # Call the function
        response = await stripe_webhook_handler(mock_request, session)

        # Verify the response
        assert response.status_code == 200
        assert response.body is not None

        # Verify StripeService was called
        mock_stripe_service_class.assert_called_once_with(session)
        mock_stripe_service.handle_checkout_session_async_payment_failed.assert_called_once_with(
            mock_event
        )

    @pytest.mark.asyncio
    @patch("src.accounting.stripe_views.stripe.Webhook.construct_event")
    @patch("src.accounting.stripe_views.StripeService")
    async def test_webhook_checkout_session_async_payment_succeeded(
        self, mock_stripe_service_class, mock_construct_event, session: Session
    ):
        """Test successful processing of checkout.session.async_payment_succeeded webhook."""
        # Mock webhook event construction
        mock_event = {
            "type": "checkout.session.async_payment_succeeded",
            "data": {
                "object": {
                    "id": "cs_test123",
                    "metadata": {
                        "user_id": str(uuid.uuid4()),
                        "topup_amount_cents": "1000",
                        "type": "account_topup",
                    },
                }
            },
        }
        mock_construct_event.return_value = mock_event

        # Mock StripeService
        mock_stripe_service = MagicMock()
        mock_stripe_service_class.return_value = mock_stripe_service

        # Mock request
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=b'{"test": "data"}')
        mock_request.headers = {"stripe-signature": "test_signature"}

        # Call the function
        response = await stripe_webhook_handler(mock_request, session)

        # Verify the response
        assert response.status_code == 200
        assert response.body is not None

        # Verify StripeService was called
        mock_stripe_service_class.assert_called_once_with(session)
        mock_stripe_service.handle_checkout_session_async_payment_succeeded.assert_called_once_with(
            mock_event
        )

    @pytest.mark.asyncio
    @patch("src.accounting.stripe_views.stripe.Webhook.construct_event")
    async def test_webhook_unhandled_event_type(
        self, mock_construct_event, session: Session
    ):
        """Test webhook with unhandled event type."""
        # Mock webhook event construction
        mock_event = {"type": "payment_intent.succeeded", "data": {"object": {}}}
        mock_construct_event.return_value = mock_event

        # Mock request
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=b'{"test": "data"}')
        mock_request.headers = {"stripe-signature": "test_signature"}

        # Call the function
        response = await stripe_webhook_handler(mock_request, session)

        # Verify the response
        assert response.status_code == 200
        assert response.body is not None

    @pytest.mark.asyncio
    async def test_webhook_no_signature(self, session: Session):
        """Test webhook with no signature header."""
        # Mock request without signature
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=b'{"test": "data"}')
        mock_request.headers = {}

        # Call the function and expect an exception
        with pytest.raises(HTTPException) as e:
            await stripe_webhook_handler(mock_request, session)
        assert e.value.status_code == 400
        assert e.value.detail == "No signature provided"

    @pytest.mark.asyncio
    @patch("src.accounting.stripe_views.stripe.Webhook.construct_event")
    async def test_webhook_invalid_payload(
        self, mock_construct_event, session: Session
    ):
        """Test webhook with invalid payload."""
        # Mock webhook event construction to raise ValueError
        mock_construct_event.side_effect = ValueError("Invalid payload")

        # Mock request
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=b"invalid_json")
        mock_request.headers = {"stripe-signature": "test_signature"}

        # Call the function and expect an exception
        with pytest.raises(HTTPException) as e:
            await stripe_webhook_handler(mock_request, session)
        assert e.value.status_code == 400
        assert e.value.detail == "Invalid payload"

    @pytest.mark.asyncio
    @patch("src.accounting.stripe_views.stripe.Webhook.construct_event")
    async def test_webhook_invalid_signature(
        self, mock_construct_event, session: Session
    ):
        """Test webhook with invalid signature."""
        # Mock webhook event construction to raise SignatureVerificationError
        mock_construct_event.side_effect = stripe.SignatureVerificationError(
            "Invalid signature", "sig"
        )

        # Mock request
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=b'{"test": "data"}')
        mock_request.headers = {"stripe-signature": "invalid_signature"}

        # Call the function and expect an exception
        with pytest.raises(Exception, match="Invalid signature"):
            await stripe_webhook_handler(mock_request, session)
