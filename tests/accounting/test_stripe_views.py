import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
import stripe
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.accounting.billing_state_machine import AccountStatusResponse
from src.accounting.models import (
    PendingTopup,
    PendingTopupStatus,
    User,
    UserAccountDetails,
    UserAccountStatus,
)
from src.accounting.stripe_views import (
    TopupRequest,
    billing_cancel,
    billing_success,
    create_customer_portal_session,
    get_payment_methods,
    stripe_checkout_session,
    topup_account,
)
from src.config import settings
from src.main import app

client = TestClient(app)


@pytest.fixture
def test_account_details(session: Session, user: User):
    """Create real account details with Stripe customer ID."""
    account_details = user.account_details
    account_details.stripe_customer_id = "cus_test123"
    account_details.balance_cents = 0
    account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
    session.add(account_details)
    session.commit()
    session.refresh(account_details)
    return account_details


@pytest.fixture
def test_account_details_no_stripe(session: Session, user: User):
    """Create real account details without Stripe customer ID."""
    account_details = user.account_details

    account_details.stripe_customer_id = None
    account_details.balance_cents = 0
    account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
    session.add(account_details)
    session.commit()
    session.refresh(account_details)

    return account_details


class TestTopupAccount:
    """Test cases for the topup_account endpoint."""

    @patch("src.accounting.stripe_views.stripe.checkout.Session.create")
    @patch("src.accounting.stripe_views.stripe.Invoice.create")
    @patch("src.accounting.stripe_views.stripe.InvoiceItem.create")
    def test_topup_account_success(
        self,
        mock_invoice_item_create,
        mock_invoice_create,
        mock_stripe_create,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test successful topup account creation with pending topup."""
        # Mock Stripe invoice creation
        mock_invoice = MagicMock()
        mock_invoice.id = "in_test123"
        mock_invoice_create.return_value = mock_invoice

        # Mock Stripe invoice item creation
        mock_invoice_item = MagicMock()
        mock_invoice_item_create.return_value = mock_invoice_item

        # Mock Stripe checkout session creation
        mock_checkout_session = MagicMock()
        mock_checkout_session.id = "cs_test123"
        mock_checkout_session.url = "https://checkout.stripe.com/c/pay/cs_test123"
        mock_stripe_create.return_value = mock_checkout_session

        # Create request
        request = TopupRequest(amount_cents=1000)

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = topup_account(request, user, session)

        # Verify the response
        assert response.status_code == 200
        assert response.body is not None

        # Verify a pending topup was created
        pending_topup = (
            session.query(PendingTopup)
            .filter(PendingTopup.session_id == "cs_test123")
            .first()
        )
        assert pending_topup is not None
        assert pending_topup.user_id == user.id
        assert pending_topup.amount_cents == 1000
        assert pending_topup.status.value == "PENDING"

        # Verify Stripe checkout session was created
        mock_stripe_create.assert_called_once()
        call_args = mock_stripe_create.call_args[1]
        assert call_args["customer"] == "cus_test123"
        assert call_args["mode"] == "payment"
        assert call_args["line_items"][0]["price_data"]["unit_amount"] == 1000
        assert call_args["metadata"]["user_id"] == str(user.id)
        assert call_args["metadata"]["topup_amount_cents"] == "1000"
        assert call_args["metadata"]["type"] == "account_topup"
        assert call_args["invoice_creation"]["enabled"] == True
        assert call_args["invoice_creation"]["invoice_data"]["metadata"][
            "user_id"
        ] == str(user.id)
        assert (
            call_args["invoice_creation"]["invoice_data"]["metadata"][
                "topup_amount_cents"
            ]
            == "1000"
        )
        assert (
            call_args["invoice_creation"]["invoice_data"]["metadata"]["type"]
            == "account_topup"
        )

    def test_topup_account_no_stripe_customer(
        self,
        user: User,
        test_account_details_no_stripe: UserAccountDetails,
        session: Session,
    ):
        """Test topup account when user has no Stripe customer ID."""
        request = TopupRequest(amount_cents=1000)

        # Call the function and expect an exception
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                with pytest.raises(Exception, match="User account not onboarded"):
                    topup_account(request, user, session)

    @patch("src.accounting.stripe_views.stripe.checkout.Session.create")
    def test_topup_account_stripe_error(
        self,
        mock_stripe_create,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test topup account when Stripe returns an error."""
        # Mock Stripe to raise an error
        mock_stripe_create.side_effect = Exception("Stripe API error")

        request = TopupRequest(amount_cents=1000)

        # Call the function and expect an exception
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                with pytest.raises(
                    Exception, match="Failed to create checkout session"
                ):
                    topup_account(request, user, session)


class TestBillingSuccess:
    """Test cases for the billing_success endpoint."""

    @patch("stripe.checkout.Session.retrieve")
    def test_billing_success_paid_payment(
        self,
        mock_stripe_retrieve,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test successful payment processing with paid status."""
        # Create a pending topup first
        pending_topup = PendingTopup()
        pending_topup.user_id = user.id
        pending_topup.session_id = "cs_test123"
        pending_topup.amount_cents = 1000
        pending_topup.status = PendingTopupStatus.PENDING
        session.add(pending_topup)
        session.commit()

        # Mock Stripe session retrieval
        mock_checkout_session = MagicMock()
        mock_checkout_session.metadata = {
            "user_id": str(user.id),
            "topup_amount_cents": "1000",
            "type": "account_topup",
        }
        mock_checkout_session.payment_status = "paid"
        mock_stripe_retrieve.return_value = mock_checkout_session

        # Mock request with session_id
        mock_request = MagicMock()
        mock_request.query_params = {"session_id": "cs_test123"}

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = billing_success(mock_request, user, session)

        # Verify the response is a redirect with pending message
        assert response.status_code == 307
        assert (
            "workspace/billing?pending=payment_processing"
            in response.headers["location"]
        )

        # Verify the balance was NOT updated (payment processing happens via webhook)
        session.refresh(test_account_details)
        assert test_account_details.balance_cents == 0

    @patch("stripe.checkout.Session.retrieve")
    def test_billing_success_pending_payment(
        self,
        mock_stripe_retrieve,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test successful payment processing with pending status."""
        # Create a pending topup first
        pending_topup = PendingTopup()
        pending_topup.user_id = user.id
        pending_topup.session_id = "cs_test123"
        pending_topup.amount_cents = 1000
        pending_topup.status = PendingTopupStatus.PENDING
        session.add(pending_topup)
        session.commit()

        # Mock Stripe session retrieval
        mock_checkout_session = MagicMock()
        mock_checkout_session.metadata = {
            "user_id": str(user.id),
            "topup_amount_cents": "1000",
            "type": "account_topup",
        }
        mock_checkout_session.payment_status = "pending"
        mock_stripe_retrieve.return_value = mock_checkout_session

        # Mock request with session_id
        mock_request = MagicMock()
        mock_request.query_params = {"session_id": "cs_test123"}

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = billing_success(mock_request, user, session)

        # Verify the response is a redirect with pending message
        assert response.status_code == 307
        assert (
            "workspace/billing?pending=payment_pending" in response.headers["location"]
        )

        # Verify the balance was NOT updated (payment processing happens via webhook)
        session.refresh(test_account_details)
        assert test_account_details.balance_cents == 0

    @patch("stripe.checkout.Session.retrieve")
    def test_billing_success_no_pending_topup(
        self,
        mock_stripe_retrieve,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test billing success when no pending topup exists."""
        # Mock Stripe session retrieval
        mock_checkout_session = MagicMock()
        mock_checkout_session.metadata = {
            "user_id": str(user.id),
            "topup_amount_cents": "1000",
            "type": "account_topup",
        }
        mock_checkout_session.payment_status = "paid"
        mock_stripe_retrieve.return_value = mock_checkout_session

        # Mock request with session_id
        mock_request = MagicMock()
        mock_request.query_params = {"session_id": "cs_test123"}

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = billing_success(mock_request, user, session)

        # Verify the response is a redirect with error
        assert response.status_code == 307
        assert (
            "workspace/billing?error=no_pending_topup" in response.headers["location"]
        )

    def test_billing_success_no_session_id(self, user: User, session: Session):
        """Test billing success with no session_id parameter."""
        # Mock request without session_id
        mock_request = MagicMock()
        mock_request.query_params = {}

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = billing_success(mock_request, user, session)

        # Verify the response is a redirect with error
        assert response.status_code == 307
        assert "workspace/billing?error=no_session" in response.headers["location"]

    @patch("stripe.checkout.Session.retrieve")
    def test_billing_success_unauthorized_session(
        self, mock_stripe_retrieve, user: User, session: Session
    ):
        """Test billing success with session that doesn't belong to user."""
        # Mock Stripe session retrieval with different user_id
        mock_checkout_session = MagicMock()
        mock_checkout_session.metadata = {
            "user_id": "different-user-id",
            "topup_amount_cents": "1000",
            "type": "account_topup",
        }
        mock_stripe_retrieve.return_value = mock_checkout_session

        # Mock request with session_id
        mock_request = MagicMock()
        mock_request.query_params = {"session_id": "cs_test123"}

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = billing_success(mock_request, user, session)

        # Verify the response is a redirect with error
        assert response.status_code == 307
        assert "workspace/billing?error=unauthorized" in response.headers["location"]


class TestBillingCancel:
    """Test cases for the billing_cancel endpoint."""

    def test_billing_cancel_success(self, user: User, session: Session):
        """Test billing cancel endpoint."""
        # Mock request
        mock_request = MagicMock()
        mock_request.query_params = {"session_id": "cs_test123"}

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = billing_cancel(mock_request, user, session)

        # Verify the response is a redirect
        assert response.status_code == 307
        assert "workspace/billing?cancelled=true" in response.headers["location"]

    def test_billing_cancel_with_session_id_success(
        self, user: User, test_account_details: UserAccountDetails, session: Session
    ):
        """Test billing cancel with session_id that successfully cancels pending topup."""
        # Create a pending topup first
        pending_topup = PendingTopup()
        pending_topup.user_id = user.id
        pending_topup.session_id = "cs_test123"
        pending_topup.amount_cents = 1000
        pending_topup.status = PendingTopupStatus.PENDING
        session.add(pending_topup)
        session.commit()

        # Mock request with session_id
        mock_request = MagicMock()
        mock_request.query_params = {"session_id": "cs_test123"}

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = billing_cancel(mock_request, user, session)

        # Verify the response is a redirect
        assert response.status_code == 307
        assert "workspace/billing?cancelled=true" in response.headers["location"]

        # Verify the pending topup status was updated to CANCELLED
        session.refresh(pending_topup)
        assert pending_topup.status == PendingTopupStatus.CANCELLED

    def test_billing_cancel_with_session_id_no_pending_topup(
        self, user: User, test_account_details: UserAccountDetails, session: Session
    ):
        """Test billing cancel with session_id but no pending topup found."""
        # Mock request with session_id
        mock_request = MagicMock()
        mock_request.query_params = {"session_id": "cs_nonexistent"}

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = billing_cancel(mock_request, user, session)

        # Verify the response is a redirect
        assert response.status_code == 307
        assert "workspace/billing?cancelled=true" in response.headers["location"]

        # Verify no pending topup was created or modified
        pending_topups = (
            session.query(PendingTopup)
            .filter(PendingTopup.session_id == "cs_nonexistent")
            .all()
        )
        assert len(pending_topups) == 0

    def test_billing_cancel_with_session_id_wrong_user(
        self, user: User, test_account_details: UserAccountDetails, session: Session
    ):
        """Test billing cancel with session_id that belongs to a different user."""
        # Create a pending topup for a different user
        different_user_id = uuid.uuid4()
        pending_topup = PendingTopup()
        pending_topup.user_id = different_user_id
        pending_topup.session_id = "cs_test123"
        pending_topup.amount_cents = 1000
        pending_topup.status = PendingTopupStatus.PENDING
        session.add(pending_topup)
        session.commit()

        # Mock request with session_id
        mock_request = MagicMock()
        mock_request.query_params = {"session_id": "cs_test123"}

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = billing_cancel(mock_request, user, session)

        # Verify the response is a redirect
        assert response.status_code == 307
        assert "workspace/billing?cancelled=true" in response.headers["location"]

        # Verify the pending topup status was NOT changed (wrong user)
        session.refresh(pending_topup)
        assert pending_topup.status == PendingTopupStatus.PENDING

    def test_billing_cancel_with_session_id_already_cancelled(
        self, user: User, test_account_details: UserAccountDetails, session: Session
    ):
        """Test billing cancel with session_id for already cancelled pending topup."""
        # Create a pending topup that's already cancelled
        pending_topup = PendingTopup()
        pending_topup.user_id = user.id
        pending_topup.session_id = "cs_test123"
        pending_topup.amount_cents = 1000
        pending_topup.status = PendingTopupStatus.CANCELLED
        session.add(pending_topup)
        session.commit()

        # Mock request with session_id
        mock_request = MagicMock()
        mock_request.query_params = {"session_id": "cs_test123"}

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = billing_cancel(mock_request, user, session)

        # Verify the response is a redirect
        assert response.status_code == 307
        assert "workspace/billing?cancelled=true" in response.headers["location"]

        # Verify the pending topup status remains CANCELLED
        session.refresh(pending_topup)
        assert pending_topup.status == PendingTopupStatus.CANCELLED

    def test_billing_cancel_with_session_id_completed_topup(
        self, user: User, test_account_details: UserAccountDetails, session: Session
    ):
        """Test billing cancel with session_id for completed pending topup."""
        # Create a pending topup that's already completed
        pending_topup = PendingTopup()
        pending_topup.user_id = user.id
        pending_topup.session_id = "cs_test123"
        pending_topup.amount_cents = 1000
        pending_topup.status = PendingTopupStatus.COMPLETED
        session.add(pending_topup)
        session.commit()

        # Mock request with session_id
        mock_request = MagicMock()
        mock_request.query_params = {"session_id": "cs_test123"}

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = billing_cancel(mock_request, user, session)

        # Verify the response is a redirect
        assert response.status_code == 307
        assert "workspace/billing?cancelled=true" in response.headers["location"]

        # Verify the pending topup status was changed to CANCELLED (even if it was completed)
        session.refresh(pending_topup)
        assert pending_topup.status == PendingTopupStatus.CANCELLED


class TestGetPaymentMethods:
    """Test cases for the get_payment_methods endpoint."""

    @patch("src.accounting.stripe_views.stripe.PaymentMethod.list")
    @patch("src.accounting.stripe_views.stripe.Customer.retrieve")
    def test_get_payment_methods_success(
        self,
        mock_customer_retrieve,
        mock_payment_method_list,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test successful retrieval of payment methods."""
        # Mock Stripe customer with default payment method
        mock_customer = MagicMock()
        mock_customer.invoice_settings.default_payment_method = "pm_default123"
        mock_customer_retrieve.return_value = mock_customer

        # Mock Stripe payment methods list
        mock_payment_methods = MagicMock()
        mock_payment_methods.data = [
            MagicMock(
                id="pm_default123",
                type="card",
                card=MagicMock(brand="visa", last4="4242", exp_month=12, exp_year=2025),
            ),
            MagicMock(
                id="pm_secondary456",
                type="card",
                card=MagicMock(
                    brand="mastercard", last4="8888", exp_month=6, exp_year=2026
                ),
            ),
        ]
        mock_payment_method_list.return_value = mock_payment_methods

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = get_payment_methods(user, session)

        # Verify the response
        assert response.payment_methods is not None
        assert len(response.payment_methods) == 2
        assert response.default_payment_method_id == "pm_default123"

        # Verify first payment method (default)
        pm1 = response.payment_methods[0]
        assert pm1.id == "pm_default123"
        assert pm1.type == "card"
        assert pm1.card_brand == "visa"
        assert pm1.card_last4 == "4242"
        assert pm1.card_exp_month == 12
        assert pm1.card_exp_year == 2025
        assert pm1.is_default is True

        # Verify second payment method (non-default)
        pm2 = response.payment_methods[1]
        assert pm2.id == "pm_secondary456"
        assert pm2.type == "card"
        assert pm2.card_brand == "mastercard"
        assert pm2.card_last4 == "8888"
        assert pm2.card_exp_month == 6
        assert pm2.card_exp_year == 2026
        assert pm2.is_default is False

        # Verify Stripe API calls
        mock_customer_retrieve.assert_called_once_with("cus_test123")
        mock_payment_method_list.assert_called_once_with(
            customer="cus_test123", type="card"
        )

    @patch("src.accounting.stripe_views.stripe.PaymentMethod.list")
    @patch("src.accounting.stripe_views.stripe.Customer.retrieve")
    def test_get_payment_methods_empty_list(
        self,
        mock_customer_retrieve,
        mock_payment_method_list,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test retrieval when user has no payment methods."""
        # Mock Stripe customer with no default payment method
        mock_customer = MagicMock()
        mock_customer.invoice_settings.default_payment_method = None
        mock_customer_retrieve.return_value = mock_customer

        # Mock empty payment methods list
        mock_payment_methods = MagicMock()
        mock_payment_methods.data = []
        mock_payment_method_list.return_value = mock_payment_methods

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = get_payment_methods(user, session)

        # Verify the response
        assert response.payment_methods == []
        assert response.default_payment_method_id is None

    @patch("src.accounting.stripe_views.stripe.PaymentMethod.list")
    @patch("src.accounting.stripe_views.stripe.Customer.retrieve")
    def test_get_payment_methods_no_default_payment_method(
        self,
        mock_customer_retrieve,
        mock_payment_method_list,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test retrieval when customer has payment methods but no default set."""
        # Mock Stripe customer with no default payment method
        mock_customer = MagicMock()
        mock_customer.invoice_settings.default_payment_method = None
        mock_customer_retrieve.return_value = mock_customer

        # Mock payment methods list
        mock_payment_methods = MagicMock()
        mock_payment_methods.data = [
            MagicMock(
                id="pm_test123",
                type="card",
                card=MagicMock(brand="visa", last4="4242", exp_month=12, exp_year=2025),
            )
        ]
        mock_payment_method_list.return_value = mock_payment_methods

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = get_payment_methods(user, session)

        # Verify the response
        assert len(response.payment_methods) == 1
        assert response.payment_methods[0].is_default is False
        assert response.default_payment_method_id is None

    @patch("src.accounting.stripe_views.stripe.PaymentMethod.list")
    @patch("src.accounting.stripe_views.stripe.Customer.retrieve")
    def test_get_payment_methods_no_invoice_settings(
        self,
        mock_customer_retrieve,
        mock_payment_method_list,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test retrieval when customer has no invoice settings."""
        # Mock Stripe customer with no invoice settings
        mock_customer = MagicMock()
        mock_customer.invoice_settings = None
        mock_customer_retrieve.return_value = mock_customer

        # Mock payment methods list
        mock_payment_methods = MagicMock()
        mock_payment_methods.data = [
            MagicMock(
                id="pm_test123",
                type="card",
                card=MagicMock(brand="visa", last4="4242", exp_month=12, exp_year=2025),
            )
        ]
        mock_payment_method_list.return_value = mock_payment_methods

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = get_payment_methods(user, session)

        # Verify the response
        assert len(response.payment_methods) == 1
        assert response.payment_methods[0].is_default is False
        assert response.default_payment_method_id is None

    def test_get_payment_methods_no_stripe_customer(
        self,
        user: User,
        test_account_details_no_stripe: UserAccountDetails,
        session: Session,
    ):
        """Test payment methods retrieval when user has no Stripe customer ID."""
        # Call the function and expect an HTTPException
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                with pytest.raises(HTTPException) as exc_info:
                    get_payment_methods(user, session)

        assert exc_info.value.status_code == 400
        assert "User account not onboarded with Stripe" in str(exc_info.value.detail)

    @patch("src.accounting.stripe_views.stripe.Customer.retrieve")
    def test_get_payment_methods_stripe_customer_error(
        self,
        mock_customer_retrieve,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test payment methods retrieval when Stripe customer retrieval fails."""
        # Mock Stripe customer retrieval to raise an error
        mock_customer_retrieve.side_effect = stripe.StripeError("Customer not found")

        # Call the function and expect an HTTPException
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                with pytest.raises(HTTPException) as exc_info:
                    get_payment_methods(user, session)

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve payment methods" in str(exc_info.value.detail)

    @patch("src.accounting.stripe_views.stripe.PaymentMethod.list")
    @patch("src.accounting.stripe_views.stripe.Customer.retrieve")
    def test_get_payment_methods_stripe_payment_methods_error(
        self,
        mock_customer_retrieve,
        mock_payment_method_list,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test payment methods retrieval when Stripe payment methods list fails."""
        # Mock successful customer retrieval
        mock_customer = MagicMock()
        mock_customer.invoice_settings.default_payment_method = None
        mock_customer_retrieve.return_value = mock_customer

        # Mock payment methods list to raise an error
        mock_payment_method_list.side_effect = stripe.StripeError(
            "Payment methods list failed"
        )

        # Call the function and expect an HTTPException
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                with pytest.raises(HTTPException) as exc_info:
                    get_payment_methods(user, session)

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve payment methods" in str(exc_info.value.detail)

    @patch("src.accounting.stripe_views.stripe.Customer.retrieve")
    def test_get_payment_methods_unexpected_error(
        self,
        mock_customer_retrieve,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test payment methods retrieval when an unexpected error occurs."""
        # Mock customer retrieval to raise a non-Stripe error
        mock_customer_retrieve.side_effect = Exception("Unexpected error")

        # Call the function and expect an HTTPException
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                with pytest.raises(HTTPException) as exc_info:
                    get_payment_methods(user, session)

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve payment methods" in str(exc_info.value.detail)

    @patch("src.accounting.stripe_views.stripe.PaymentMethod.list")
    @patch("src.accounting.stripe_views.stripe.Customer.retrieve")
    def test_get_payment_methods_card_without_details(
        self,
        mock_customer_retrieve,
        mock_payment_method_list,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test retrieval when payment method has no card details."""
        # Mock Stripe customer
        mock_customer = MagicMock()
        mock_customer.invoice_settings.default_payment_method = None
        mock_customer_retrieve.return_value = mock_customer

        # Mock payment method without card details
        mock_payment_methods = MagicMock()
        mock_payment_methods.data = [MagicMock(id="pm_test123", type="card", card=None)]
        mock_payment_method_list.return_value = mock_payment_methods

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = get_payment_methods(user, session)

        # Verify the response
        assert len(response.payment_methods) == 1
        pm = response.payment_methods[0]
        assert pm.id == "pm_test123"
        assert pm.type == "card"
        assert pm.card_brand is None
        assert pm.card_last4 is None
        assert pm.card_exp_month is None
        assert pm.card_exp_year is None
        assert pm.is_default is False


class TestSessionStatus:
    """Test cases for the session_status endpoint."""

    @patch("stripe.checkout.Session.retrieve")
    def test_session_status_success_with_stripe_customer(
        self,
        mock_stripe_retrieve,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test successful session status retrieval when user has Stripe customer ID."""
        # Mock Stripe session retrieval
        mock_checkout_session = MagicMock()
        mock_checkout_session.status = "complete"
        mock_stripe_retrieve.return_value = mock_checkout_session

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                from src.accounting.stripe_views import session_status

                response = session_status("cs_test123", user, session)

        # Verify the response
        assert response.status_code == 200
        response_data = json.loads(response.body)
        assert response_data["status"] == "complete"

        # Verify Stripe API call
        mock_stripe_retrieve.assert_called_once_with(
            "cs_test123", expand=["payment_intent"]
        )

    @patch("stripe.checkout.Session.retrieve")
    def test_session_status_waiting_for_webhook(
        self,
        mock_stripe_retrieve,
        user: User,
        test_account_details_no_stripe: UserAccountDetails,
        session: Session,
    ):
        """Test session status when waiting for webhook to set stripe_customer_id."""
        # Mock Stripe session retrieval
        mock_checkout_session = MagicMock()
        mock_checkout_session.status = "complete"
        mock_stripe_retrieve.return_value = mock_checkout_session

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                from src.accounting.stripe_views import session_status

                response = session_status("cs_test123", user, session)

        # Verify the response shows "open" status (waiting for webhook)
        assert response.status_code == 200
        response_data = json.loads(response.body)
        assert response_data["status"] == "open"

        # Verify Stripe API call was still made
        mock_stripe_retrieve.assert_called_once_with(
            "cs_test123", expand=["payment_intent"]
        )

    @patch("stripe.checkout.Session.retrieve")
    def test_session_status_no_account_details(
        self,
        mock_stripe_retrieve,
        user: User,
        session: Session,
    ):
        """Test session status when user account details are not found."""
        # Remove the user's account details
        if user.account_details:
            session.delete(user.account_details)
            session.commit()

        # Call the function and expect an HTTPException
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                from src.accounting.stripe_views import session_status

                with pytest.raises(HTTPException) as exc_info:
                    session_status("cs_test123", user, session)

        assert exc_info.value.status_code == 400
        assert "User account details not found" in str(exc_info.value.detail)

    @patch("stripe.checkout.Session.retrieve")
    def test_session_status_stripe_error(
        self,
        mock_stripe_retrieve,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test session status when Stripe API returns an error."""
        # Mock Stripe to raise an error
        mock_stripe_retrieve.side_effect = stripe.StripeError("Session not found")

        # Call the function and expect the error to propagate
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                from src.accounting.stripe_views import session_status

                with pytest.raises(stripe.StripeError):
                    session_status("cs_test123", user, session)

        # Verify Stripe API call was made
        mock_stripe_retrieve.assert_called_once_with(
            "cs_test123", expand=["payment_intent"]
        )

    @patch("stripe.checkout.Session.retrieve")
    def test_session_status_different_session_statuses(
        self,
        mock_stripe_retrieve,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test session status endpoint returns various Stripe session statuses."""
        test_statuses = ["open", "complete", "expired"]

        for status in test_statuses:
            # Mock Stripe session retrieval with different status
            mock_checkout_session = MagicMock()
            mock_checkout_session.status = status
            mock_stripe_retrieve.return_value = mock_checkout_session

            # Call the function
            with patch(
                "src.accounting.stripe_views.dependency_to_override", return_value=user
            ):
                with patch("src.accounting.stripe_views.get_db", return_value=session):
                    from src.accounting.stripe_views import session_status

                    response = session_status("cs_test123", user, session)

            # Verify the response
            assert response.status_code == 200
            response_data = json.loads(response.body)
            assert response_data["status"] == status


class TestCreateCustomerPortalSession:
    """Test cases for the create_customer_portal_session endpoint."""

    @patch("src.accounting.stripe_views.stripe.billing_portal.Session.create")
    def test_create_customer_portal_session_success(
        self,
        mock_portal_session_create,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test successful creation of customer portal session."""
        # Mock Stripe customer portal session creation
        mock_portal_session = MagicMock()
        mock_portal_session.url = "https://billing.stripe.com/p/session_test123"
        mock_portal_session_create.return_value = mock_portal_session

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = create_customer_portal_session(user, session)

        # Verify the response
        assert response.url == "https://billing.stripe.com/p/session_test123"

        # Verify Stripe API call
        mock_portal_session_create.assert_called_once_with(
            customer="cus_test123", return_url="http://localhost:8000/workspace/billing"
        )

    def test_create_customer_portal_session_no_stripe_customer(
        self,
        user: User,
        test_account_details_no_stripe: UserAccountDetails,
        session: Session,
    ):
        """Test customer portal session creation when user has no Stripe customer ID."""
        # Call the function and expect an HTTPException
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                with pytest.raises(HTTPException) as exc_info:
                    create_customer_portal_session(user, session)

        assert exc_info.value.status_code == 400
        assert "User account not onboarded with Stripe" in str(exc_info.value.detail)

    @patch("src.accounting.stripe_views.stripe.billing_portal.Session.create")
    def test_create_customer_portal_session_stripe_error(
        self,
        mock_portal_session_create,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test customer portal session creation when Stripe returns an error."""
        # Mock Stripe to raise an error
        mock_portal_session_create.side_effect = stripe.StripeError(
            "Portal session creation failed"
        )

        # Call the function and expect an HTTPException
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                with pytest.raises(HTTPException) as exc_info:
                    create_customer_portal_session(user, session)

        assert exc_info.value.status_code == 500
        assert "Failed to create customer portal session" in str(exc_info.value.detail)


class TestStripeCheckoutSession:
    """Test cases for the stripe_checkout_session endpoint (duplicate subscription prevention)."""

    @patch("src.accounting.stripe_views.stripe.checkout.Session.create")
    @patch("src.accounting.stripe_views.stripe.Customer.search")
    @patch("src.accounting.stripe_views.BillingService")
    def test_stripe_checkout_session_with_active_subscription(
        self,
        mock_billing_service_class,
        mock_customer_search,
        mock_stripe_create,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test that users with active subscriptions are redirected to workspace."""
        # Mock BillingService to return active subscription status
        mock_billing_service = MagicMock()
        mock_billing_service.get_account_status_detailed.return_value = (
            AccountStatusResponse(
                state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                usage_balance_cents=0.0,
                usage_balance_dollars=0.0,
                monthly_credits_cents=500,
                monthly_credits_dollars=5.0,
                has_active_subscription=True,
                is_closed=False,
                has_usage_balance=False,
                subscription_only=True,
                using_metered_billing=False,
                no_subscription=False,
                is_suspended=False,
            )
        )
        mock_billing_service_class.return_value = mock_billing_service

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = stripe_checkout_session(user, session)

        # Verify redirect response
        assert response.status_code == 200
        response_data = json.loads(response.body)
        assert response_data["redirect"] is True
        assert response_data["redirect_url"] == "/workspace"
        assert response_data["reason"] == "active_subscription"

        # Verify BillingService was called
        mock_billing_service_class.assert_called_once_with(session)
        mock_billing_service.get_account_status_detailed.assert_called_once_with(user)

        # Verify Stripe methods were NOT called
        mock_customer_search.assert_not_called()
        mock_stripe_create.assert_not_called()

    @patch("src.accounting.stripe_views.stripe.checkout.Session.create")
    @patch("src.accounting.stripe_views.stripe.Customer.search")
    @patch("src.accounting.stripe_views.BillingService")
    def test_stripe_checkout_session_with_closed_account(
        self,
        mock_billing_service_class,
        mock_customer_search,
        mock_stripe_create,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test that users with closed accounts are redirected to workspace."""
        # Mock BillingService to return closed account status
        mock_billing_service = MagicMock()
        mock_billing_service.get_account_status_detailed.return_value = (
            AccountStatusResponse(
                state=UserAccountStatus.CLOSED,
                usage_balance_cents=0.0,
                usage_balance_dollars=0.0,
                monthly_credits_cents=500,
                monthly_credits_dollars=5.0,
                has_active_subscription=True,
                is_closed=True,
                has_usage_balance=False,
                subscription_only=True,
                using_metered_billing=False,
                no_subscription=False,
                is_suspended=False,
            )
        )
        mock_billing_service_class.return_value = mock_billing_service

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = stripe_checkout_session(user, session)

        # Verify redirect response
        assert response.status_code == 200
        response_data = json.loads(response.body)
        assert response_data["redirect"] is True
        assert response_data["redirect_url"] == "/workspace"
        assert response_data["reason"] == "account_closed"

        # Verify BillingService was called
        mock_billing_service_class.assert_called_once_with(session)
        mock_billing_service.get_account_status_detailed.assert_called_once_with(user)

        # Verify Stripe methods were NOT called
        mock_customer_search.assert_not_called()
        mock_stripe_create.assert_not_called()

    @patch("src.accounting.stripe_views.stripe.checkout.Session.create")
    @patch("src.accounting.stripe_views.stripe.Customer.search")
    @patch("src.accounting.stripe_views.BillingService")
    def test_stripe_checkout_session_allows_new_subscription(
        self,
        mock_billing_service_class,
        mock_customer_search,
        mock_stripe_create,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test that users without active subscriptions or closed accounts can proceed with checkout."""
        # Mock BillingService to return eligible status
        mock_billing_service = MagicMock()
        mock_billing_service.get_account_status_detailed.return_value = (
            AccountStatusResponse(
                state=UserAccountStatus.NO_SUBSCRIPTION,
                usage_balance_cents=0.0,
                usage_balance_dollars=0.0,
                monthly_credits_cents=0,
                monthly_credits_dollars=0.0,
                has_active_subscription=False,
                is_closed=False,
                has_usage_balance=False,
                subscription_only=False,
                using_metered_billing=False,
                no_subscription=True,
                is_suspended=False,
            )
        )
        mock_billing_service_class.return_value = mock_billing_service

        # Mock Stripe customer search (no existing customer)
        mock_customer_search_result = MagicMock()
        mock_customer_search_result.data = []
        mock_customer_search.return_value = mock_customer_search_result

        # Mock Stripe checkout session creation
        mock_checkout_session = MagicMock()
        mock_checkout_session.__getitem__ = lambda self, key: (
            "cs_test_client_secret_123" if key == "client_secret" else None
        )
        mock_stripe_create.return_value = mock_checkout_session

        # Call the function
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                response = stripe_checkout_session(user, session)

        # Verify successful checkout session creation
        assert response.status_code == 200
        response_data = json.loads(response.body)
        assert "checkoutSessionClientSecret" in response_data
        assert (
            response_data["checkoutSessionClientSecret"] == "cs_test_client_secret_123"
        )

        # Verify BillingService was called
        mock_billing_service_class.assert_called_once_with(session)
        mock_billing_service.get_account_status_detailed.assert_called_once_with(user)

        # Verify Stripe methods were called
        mock_customer_search.assert_called_once()
        mock_stripe_create.assert_called_once_with(
            line_items=[
                {
                    "price": settings.stripe_price_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            ui_mode="custom",
            return_url=f"{settings.app_url}/workspace/billing/subscription/complete?session_id={{CHECKOUT_SESSION_ID}}",
            customer_email=user.email,
            metadata={
                "type": "subscription_signup",
            },
        )

    @patch("src.accounting.stripe_views.stripe.billing_portal.Session.create")
    def test_create_customer_portal_session_unexpected_error(
        self,
        mock_portal_session_create,
        user: User,
        test_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test customer portal session creation when an unexpected error occurs."""
        # Mock portal session creation to raise a non-Stripe error
        mock_portal_session_create.side_effect = Exception("Unexpected error")

        # Call the function and expect an HTTPException
        with patch(
            "src.accounting.stripe_views.dependency_to_override", return_value=user
        ):
            with patch("src.accounting.stripe_views.get_db", return_value=session):
                with pytest.raises(HTTPException) as exc_info:
                    create_customer_portal_session(user, session)

        assert exc_info.value.status_code == 500
        assert "Failed to create customer portal session" in str(exc_info.value.detail)
