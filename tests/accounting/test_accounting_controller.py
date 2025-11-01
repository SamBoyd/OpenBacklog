import datetime
from types import SimpleNamespace
from typing import Any, Dict, List
from unittest.mock import ANY, Mock, patch

import pytest
from sqlalchemy.orm import Session

import src.accounting.accounting_controller as accounting_controller
from src.accounting.accounting_controller import SubscriptionCancellationResult
from src.accounting.accounting_views import (
    RefundResult,  # Pydantic model used for API responses
)
from src.accounting.billing_service import BillingServiceException
from src.accounting.models import UserAccountDetails, UserAccountStatus
from src.accounting.stripe_service import CancellationRefundResult, RefundBreakdownItem
from src.accounting.stripe_service import RefundResult as StripeRefundResult
from src.models import User

# ---------------------------------------------------------------------------
# Helper fixtures and classes
# ---------------------------------------------------------------------------


@pytest.fixture()
def patch_refund_result(monkeypatch: pytest.MonkeyPatch):
    """Ensure RefundResult symbol exists inside accounting_controller at runtime."""
    monkeypatch.setattr(
        accounting_controller, "RefundResult", RefundResult, raising=False
    )


class _FakeBillingService:
    """Very small stub that mimics BillingService interface used in controller."""

    def __init__(self, db: Session):
        self.db = db

    def process_balance_refund(
        self, user: User, external_id: str
    ):  # noqa: D401, ANN001
        # Return an object with the attributes referenced by the controller (balance_cents, status)
        return SimpleNamespace(
            balance_cents=0, status=UserAccountStatus.NO_SUBSCRIPTION
        )


class _FakeBillingServiceWithException:
    """Billing service stub that raises BillingServiceException."""

    def __init__(self, db: Session):
        self.db = db

    def process_balance_refund(
        self, user: User, external_id: str
    ) -> UserAccountDetails:  # noqa: D401, ANN001
        raise BillingServiceException("Insufficient funds for refund")


class _BaseFakeStripeService:
    """Base stub that provides StripeService interface used in controller."""

    def __init__(self, db: Session):  # noqa: D401, ANN001
        self.db = db

    def calculate_refund_breakdown(
        self, invoices: List[str], refund_amount_cents: int
    ) -> List[RefundBreakdownItem]:  # noqa: D401, ANN001
        return [
            RefundBreakdownItem(
                invoice_id="inv_1",
                refund_amount_cents=refund_amount_cents,
                invoice_amount_cents=1000,
            )
        ]

    def process_refunds(
        self, refund_breakdown: List[RefundBreakdownItem]
    ) -> List[StripeRefundResult]:  # noqa: D401, ANN001
        return [
            StripeRefundResult(
                invoice_id="inv_1",
                credit_note_id="cn_1",
                amount_cents=refund_breakdown[0].refund_amount_cents,
                status="succeeded",
                success=True,
            )
        ]


class _FakeStripeServiceWithInvoices(_BaseFakeStripeService):
    def get_paid_invoices(
        self, stripe_customer_id: str
    ) -> List[str]:  # noqa: D401, ANN001
        return ["invoice_stub"]


class _FakeStripeServiceNoInvoices(_BaseFakeStripeService):
    def get_paid_invoices(
        self, stripe_customer_id: str
    ) -> List[str]:  # noqa: D401, ANN001
        return []


class _FakeStripeServiceError(_BaseFakeStripeService):
    def get_paid_invoices(
        self, stripe_customer_id: str
    ) -> List[str]:  # noqa: D401, ANN001
        raise Exception("stripe error")


# ---------------------------------------------------------------------------
# Fake services for cancel_subscription_with_refund tests
# ---------------------------------------------------------------------------


class _FakeBillingServiceForCancellation:
    """Billing service stub for subscription cancellation tests."""

    def __init__(self, db: Session):
        self.db = db

    def cancel_subscription(self, user: User, external_id: str):
        # Return an object with updated status
        return SimpleNamespace(
            balance_cents=0, status=UserAccountStatus.NO_SUBSCRIPTION
        )

    def reactivate_subscription(self, user: User, external_id: str):
        # Return an object with reactivated status
        return SimpleNamespace(
            balance_cents=0, status=UserAccountStatus.ACTIVE_SUBSCRIPTION
        )


class _FakeBillingServiceCancellationException:
    """Billing service stub that raises exception during cancellation."""

    def __init__(self, db: Session):
        self.db = db

    def cancel_subscription(self, user: User, external_id: str):
        raise BillingServiceException("Cannot cancel subscription")


class _FakeStripeServiceForCancellation:
    """Stripe service stub for successful cancellation and refund."""

    def __init__(self, db: Session):
        self.db = db

    def cancel_and_refund_subscription(
        self, stripe_customer_id: str, refund_last_n_days: int = 30
    ) -> CancellationRefundResult:
        return CancellationRefundResult(
            success=True,
            subscription_cancelled=True,
            subscription_id="sub_test123",
            refunds_processed=[
                StripeRefundResult(
                    invoice_id="inv_123",
                    credit_note_id="cn_123",
                    amount_cents=2500,
                    status="succeeded",
                    success=True,
                )
            ],
            total_refunded_cents=2500,
            error=None,
        )


class _FakeStripeServiceCancellationFailed:
    """Stripe service stub that fails to cancel subscription."""

    def __init__(self, db: Session):
        self.db = db

    def cancel_and_refund_subscription(
        self, stripe_customer_id: str, refund_last_n_days: int = 30
    ) -> CancellationRefundResult:
        return CancellationRefundResult(
            success=False,
            subscription_cancelled=False,
            subscription_id=None,
            refunds_processed=[],
            total_refunded_cents=0,
            error="Failed to cancel Stripe subscription",
        )


class _FakeStripeServiceCancellationException:
    """Stripe service stub that raises exception during cancellation."""

    def __init__(self, db: Session):
        self.db = db

    def cancel_and_refund_subscription(
        self, stripe_customer_id: str, refund_last_n_days: int = 30
    ) -> CancellationRefundResult:
        raise Exception("Unexpected Stripe error")


# ---------------------------------------------------------------------------
# Helper functions for tests
# ---------------------------------------------------------------------------


def _make_account_details(
    session: Session, user: User, balance: int, stripe_customer: str | None = "cus_123"
) -> UserAccountDetails:
    """Utility to create and persist a UserAccountDetails row for test user."""
    details = user.account_details
    details.balance_cents = balance
    details.status = UserAccountStatus.NEW
    details.stripe_customer_id = stripe_customer  # type: ignore[assignment]
    session.add(details)
    session.commit()
    session.refresh(details)
    return details


# ---------------------------------------------------------------------------
# Tests for process_refund
# ---------------------------------------------------------------------------


def _make_user_account_details_for_refund(session: Session, user: User):
    return _make_account_details(session, user, balance=2000, stripe_customer="cus_123")


@pytest.mark.usefixtures("patch_refund_result")
@patch("src.accounting.accounting_controller.get_usage_tracker")
def test_process_refund_success(
    mock_get_usage_tracker: Mock,
    monkeypatch: pytest.MonkeyPatch,
    session: Session,
    user: User,
):
    # Arrange
    user_account_details = _make_user_account_details_for_refund(session, user)

    # Patch services
    monkeypatch.setattr(accounting_controller, "BillingService", _FakeBillingService)
    monkeypatch.setattr(
        accounting_controller, "StripeService", _FakeStripeServiceWithInvoices
    )

    # Act
    result = accounting_controller.process_refund(
        user,
        2000,
        db=session,
    )

    # Assert
    assert isinstance(result, RefundResult)
    assert result.success is True
    assert result.details and "Refunded 2000 cents" in result.details

    mock_get_usage_tracker.return_value.process_user_usage.assert_called_once_with(
        user_account_details
    )


@pytest.mark.usefixtures("patch_refund_result")
@patch("src.accounting.accounting_controller.get_usage_tracker", Mock())
def test_process_refund_no_invoices(
    monkeypatch: pytest.MonkeyPatch, session: Session, user: User
):
    # Arrange
    _make_user_account_details_for_refund(session, user)

    monkeypatch.setattr(accounting_controller, "BillingService", _FakeBillingService)
    monkeypatch.setattr(
        accounting_controller, "StripeService", _FakeStripeServiceNoInvoices
    )

    # Act
    result = accounting_controller.process_refund(
        user,
        2000,
        db=session,
    )

    # Assert
    assert not result.success
    assert result.details == "No paid invoices available for refund."


@pytest.mark.usefixtures("patch_refund_result")
@patch("src.accounting.accounting_controller.get_usage_tracker", Mock())
def test_process_refund_stripe_error(
    monkeypatch: pytest.MonkeyPatch, session: Session, user: User
):
    # Arrange
    _make_user_account_details_for_refund(session, user)

    monkeypatch.setattr(accounting_controller, "BillingService", _FakeBillingService)
    monkeypatch.setattr(accounting_controller, "StripeService", _FakeStripeServiceError)

    # Act
    result = accounting_controller.process_refund(
        user,
        2000,
        db=session,
    )

    # Assert
    assert not result.success
    assert result.details == "Failed to retrieve invoices."


@pytest.mark.usefixtures("patch_refund_result")
@patch("src.accounting.accounting_controller.get_usage_tracker", Mock())
def test_process_refund_billing_service_exception(
    monkeypatch: pytest.MonkeyPatch, session: Session, user: User
):
    """Test that BillingServiceException is properly handled and returns RefundResult."""
    # Arrange
    _make_user_account_details_for_refund(session, user)

    monkeypatch.setattr(
        accounting_controller, "BillingService", _FakeBillingServiceWithException
    )
    monkeypatch.setattr(
        accounting_controller, "StripeService", _FakeStripeServiceWithInvoices
    )

    # Act
    result = accounting_controller.process_refund(
        user,
        2000,
        db=session,
    )

    # Assert
    assert isinstance(result, RefundResult)
    assert not result.success
    assert result.details == "Insufficient funds for refund"


# ---------------------------------------------------------------------------
# Tests for cancel_subscription_with_refund
# ---------------------------------------------------------------------------


def _make_user_with_stripe_customer(session: Session, user: User) -> UserAccountDetails:
    """Helper to create user account details with Stripe customer ID."""
    details = user.account_details
    details.stripe_customer_id = "cus_test123"
    details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
    session.add(details)
    session.commit()
    session.refresh(details)
    return details


def test_cancel_subscription_with_refund_success(
    monkeypatch: pytest.MonkeyPatch, session: Session, user: User
):
    """Test successful subscription cancellation with refund."""
    # Arrange
    _make_user_with_stripe_customer(session, user)

    monkeypatch.setattr(
        accounting_controller, "BillingService", _FakeBillingServiceForCancellation
    )
    monkeypatch.setattr(
        accounting_controller, "StripeService", _FakeStripeServiceForCancellation
    )

    # Act
    result = accounting_controller.cancel_subscription_with_refund(user, session)

    # Assert
    assert isinstance(result, SubscriptionCancellationResult)
    assert result.success is True
    assert result.billing_cancelled is True
    assert result.stripe_cancelled is True
    assert result.refunds_processed == 1
    assert result.total_refunded_cents == 2500
    assert result.error is None
    assert "Canceled subscription and refunded 2500 cents" in result.details


def test_cancel_subscription_with_refund_no_stripe_customer(
    monkeypatch: pytest.MonkeyPatch, session: Session, user: User
):
    """Test cancellation fails when user has no Stripe customer ID."""
    # Arrange - user account details without stripe_customer_id
    details = user.account_details
    details.stripe_customer_id = None
    details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
    session.add(details)
    session.commit()

    # Act
    result = accounting_controller.cancel_subscription_with_refund(user, session)

    # Assert
    assert isinstance(result, SubscriptionCancellationResult)
    assert result.success is False
    assert result.billing_cancelled is False
    assert result.stripe_cancelled is False
    assert result.refunds_processed == 0
    assert result.total_refunded_cents == 0
    assert result.error == "User has no Stripe customer ID"


def test_cancel_subscription_with_refund_billing_service_error(
    monkeypatch: pytest.MonkeyPatch, session: Session, user: User
):
    """Test billing service error during cancellation."""
    # Arrange
    _make_user_with_stripe_customer(session, user)

    monkeypatch.setattr(
        accounting_controller,
        "BillingService",
        _FakeBillingServiceCancellationException,
    )
    monkeypatch.setattr(
        accounting_controller, "StripeService", _FakeStripeServiceForCancellation
    )

    # Act
    result = accounting_controller.cancel_subscription_with_refund(user, session)

    # Assert
    assert isinstance(result, SubscriptionCancellationResult)
    assert result.success is False
    assert result.billing_cancelled is False
    assert result.stripe_cancelled is False
    assert result.refunds_processed == 0
    assert result.total_refunded_cents == 0
    assert result.error == "Billing service error: Cannot cancel subscription"


def test_cancel_subscription_with_refund_stripe_failure_with_rollback(
    monkeypatch: pytest.MonkeyPatch, session: Session, user: User
):
    """Test Stripe failure triggers billing rollback and reactivation."""
    # Arrange
    _make_user_with_stripe_customer(session, user)

    # Mock the billing service to track calls
    mock_billing_service = Mock()
    mock_billing_service.return_value.cancel_subscription.return_value = (
        SimpleNamespace(balance_cents=0, status=UserAccountStatus.NO_SUBSCRIPTION)
    )
    mock_billing_service.return_value.reactivate_subscription.return_value = (
        SimpleNamespace(balance_cents=0, status=UserAccountStatus.ACTIVE_SUBSCRIPTION)
    )

    monkeypatch.setattr(accounting_controller, "BillingService", mock_billing_service)
    monkeypatch.setattr(
        accounting_controller, "StripeService", _FakeStripeServiceCancellationFailed
    )

    # Act
    result = accounting_controller.cancel_subscription_with_refund(user, session)

    # Assert
    assert isinstance(result, SubscriptionCancellationResult)
    assert result.success is False
    assert result.billing_cancelled is False  # Rolled back
    assert result.stripe_cancelled is False
    assert result.refunds_processed == 0
    assert result.total_refunded_cents == 0
    assert (
        "Stripe operation failed: Failed to cancel Stripe subscription" in result.error
    )

    # Verify reactivation was called
    mock_billing_service.return_value.reactivate_subscription.assert_called_once()


def test_cancel_subscription_with_refund_stripe_exception_with_rollback(
    monkeypatch: pytest.MonkeyPatch, session: Session, user: User
):
    """Test unexpected Stripe exception triggers billing rollback."""
    # Arrange
    _make_user_with_stripe_customer(session, user)

    # Mock the billing service to track calls
    mock_billing_service = Mock()
    mock_billing_service.return_value.cancel_subscription.return_value = (
        SimpleNamespace(balance_cents=0, status=UserAccountStatus.NO_SUBSCRIPTION)
    )
    mock_billing_service.return_value.reactivate_subscription.return_value = (
        SimpleNamespace(balance_cents=0, status=UserAccountStatus.ACTIVE_SUBSCRIPTION)
    )

    monkeypatch.setattr(accounting_controller, "BillingService", mock_billing_service)
    monkeypatch.setattr(
        accounting_controller, "StripeService", _FakeStripeServiceCancellationException
    )

    # Act
    result = accounting_controller.cancel_subscription_with_refund(user, session)

    # Assert
    assert isinstance(result, SubscriptionCancellationResult)
    assert result.success is False
    assert result.billing_cancelled is False  # Rolled back
    assert result.stripe_cancelled is False
    assert result.refunds_processed == 0
    assert result.total_refunded_cents == 0
    assert "Unexpected Stripe error: Unexpected Stripe error" in result.error

    # Verify reactivation was attempted
    mock_billing_service.return_value.reactivate_subscription.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for handle_subscription_created_with_setup
# ---------------------------------------------------------------------------


def _create_stripe_event_data(
    customer_id: str, subscription_id: str = "sub_test123"
) -> Dict[str, Any]:
    """Helper function to create Stripe webhook event data."""
    return {
        "data": {
            "object": {
                "id": subscription_id,
                "customer": customer_id,
                "status": "active",
            }
        },
        "type": "customer.subscription.created",
    }


class _FakeStripeServiceForSubscriptionCreated:
    """Fake StripeService for subscription created tests."""

    def __init__(self, db: Session):
        self.db = db

    def handle_subscription_created(self, event: Dict[str, Any]):
        """Mock implementation that sets stripe_customer_id on user account."""
        # Extract customer ID from event
        customer_id = event["data"]["object"]["customer"]

        # Find user by email (we'll mock the Stripe customer retrieval)
        # For tests, we assume the customer email matches the test user
        from src.models import User

        user = self.db.query(User).first()  # Get the test user

        if user and user.account_details:
            user.account_details.stripe_customer_id = customer_id
            self.db.add(user.account_details)
            self.db.commit()


class TestHandleSubscriptionCreatedWithSetup:
    """Test cases for handle_subscription_created_with_setup function."""

    @patch("src.accounting.accounting_controller.OpenMeterService")
    @patch("src.accounting.accounting_controller.BillingService")
    @patch("src.accounting.accounting_controller.complete_onboarding")
    @patch(
        "src.accounting.accounting_controller.controller.create_litellm_user_and_key"
    )
    @patch("src.accounting.accounting_controller.StripeService")
    @patch("stripe.Customer.retrieve")
    def test_handle_subscription_created_with_setup_success(
        self,
        mock_stripe_customer_retrieve: Mock,
        mock_stripe_service_cls: Mock,
        mock_create_litellm_user_and_key: Mock,
        mock_complete_onboarding: Mock,
        mock_billing_service_cls: Mock,
        mock_openmeter_service_cls: Mock,
        session: Session,
        user: User,
    ):
        """Test successful subscription webhook processing with setup."""
        # Setup user without stripe customer ID initially
        user.account_details.stripe_customer_id = None
        user.account_details.onboarding_completed = False
        session.add(user.account_details)
        session.commit()

        # Mock Stripe customer retrieval
        mock_customer = Mock()
        mock_customer.email = user.email
        mock_stripe_customer_retrieve.return_value = mock_customer

        # Mock StripeService
        mock_stripe_service = _FakeStripeServiceForSubscriptionCreated(session)
        mock_stripe_service_cls.return_value = mock_stripe_service

        # Mock billing service
        mock_billing_service = Mock()
        mock_billing_service_cls.return_value = mock_billing_service

        # Mock complete onboarding
        updated_account_details = UserAccountDetails()
        updated_account_details.balance_cents = 0.0
        updated_account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        updated_account_details.onboarding_completed = True
        mock_complete_onboarding.return_value = updated_account_details

        # Mock OpenMeter service
        mock_openmeter_service = Mock()
        mock_openmeter_service_cls.return_value = mock_openmeter_service

        # Create test event
        event = _create_stripe_event_data("cus_test123")

        # Call the function
        now = datetime.datetime.now()
        accounting_controller.handle_subscription_created_with_setup(event, session)

        # Verify all services were called
        mock_create_litellm_user_and_key.assert_called_once()
        mock_billing_service.signup_subscription.assert_called_once_with(
            ANY, "cus_test123"
        )
        mock_complete_onboarding.assert_called_once_with(ANY, session)
        mock_openmeter_service.create_customer.assert_called_once_with(
            ANY, "cus_test123"
        )

        # Verify user account details were updated
        session.refresh(user.account_details)
        assert user.account_details.stripe_customer_id == "cus_test123"
        assert user.account_details.monthly_credits_total == 700
        assert user.account_details.monthly_credits_used == 0
        assert user.account_details.next_billing_cycle_starts is not None
        assert (
            user.account_details.next_billing_cycle_starts
            > now + datetime.timedelta(days=30)
        )

    @patch("stripe.Customer.retrieve")
    def test_handle_subscription_created_with_setup_no_customer_id(
        self, mock_stripe_customer_retrieve: Mock, session: Session, user: User
    ):
        """Test webhook processing failure when event has no customer ID."""
        # Create event without customer ID
        event = {
            "data": {
                "object": {
                    "id": "sub_test123",
                    "status": "active",
                    # No customer field
                }
            },
            "type": "customer.subscription.created",
        }

        # Should raise ValueError
        with pytest.raises(ValueError, match="No customer ID found"):
            accounting_controller.handle_subscription_created_with_setup(event, session)

        # Verify no Stripe customer lookup was attempted
        mock_stripe_customer_retrieve.assert_not_called()

    @patch("src.accounting.accounting_controller.StripeService")
    @patch("stripe.Customer.retrieve")
    def test_handle_subscription_created_with_setup_no_customer_email(
        self,
        mock_stripe_customer_retrieve: Mock,
        mock_stripe_service_cls: Mock,
        session: Session,
        user: User,
    ):
        """Test webhook processing failure when customer has no email."""
        # Mock Stripe customer without email
        mock_customer = Mock()
        mock_customer.email = None
        mock_stripe_customer_retrieve.return_value = mock_customer

        # Mock StripeService
        mock_stripe_service = _FakeStripeServiceForSubscriptionCreated(session)
        mock_stripe_service_cls.return_value = mock_stripe_service

        # Create test event
        event = _create_stripe_event_data("cus_test123")

        # Should raise ValueError
        with pytest.raises(ValueError, match="No email found for Stripe customer"):
            accounting_controller.handle_subscription_created_with_setup(event, session)

    @patch("src.accounting.accounting_controller.StripeService")
    @patch("stripe.Customer.retrieve")
    def test_handle_subscription_created_with_setup_user_not_found(
        self,
        mock_stripe_customer_retrieve: Mock,
        mock_stripe_service_cls: Mock,
        session: Session,
        user: User,
    ):
        """Test webhook processing failure when user with customer email not found."""
        # Mock Stripe customer with email that doesn't match any user
        mock_customer = Mock()
        mock_customer.email = "nonexistent@example.com"
        mock_stripe_customer_retrieve.return_value = mock_customer

        # Mock StripeService
        mock_stripe_service = _FakeStripeServiceForSubscriptionCreated(session)
        mock_stripe_service_cls.return_value = mock_stripe_service

        # Create test event
        event = _create_stripe_event_data("cus_test123")

        # Should raise ValueError
        with pytest.raises(ValueError, match="No user found with email"):
            accounting_controller.handle_subscription_created_with_setup(event, session)

    @patch("src.accounting.accounting_controller.OpenMeterService")
    @patch("src.accounting.accounting_controller.complete_onboarding")
    @patch("src.accounting.accounting_controller.BillingService")
    @patch(
        "src.accounting.accounting_controller.controller.create_litellm_user_and_key"
    )
    @patch("src.accounting.accounting_controller.StripeService")
    @patch("stripe.Customer.retrieve")
    def test_handle_subscription_created_with_setup_idempotent(
        self,
        mock_stripe_customer_retrieve: Mock,
        mock_stripe_service_cls: Mock,
        mock_create_litellm_user_and_key: Mock,
        mock_billing_service_cls: Mock,
        mock_complete_onboarding: Mock,
        mock_openmeter_service_cls: Mock,
        session: Session,
        user: User,
    ):
        """Test webhook processing can be called multiple times safely (idempotent behavior)."""
        # Setup user without stripe customer ID initially
        user.account_details.stripe_customer_id = None
        user.account_details.onboarding_completed = False
        session.add(user.account_details)
        session.commit()
        session.refresh(user.account_details)

        # Mock Stripe customer retrieval
        mock_customer = Mock()
        mock_customer.email = user.email
        mock_stripe_customer_retrieve.return_value = mock_customer

        # Mock StripeService
        mock_stripe_service = _FakeStripeServiceForSubscriptionCreated(session)
        mock_stripe_service_cls.return_value = mock_stripe_service

        # Mock billing service
        mock_billing_service = Mock()
        mock_billing_service_cls.return_value = mock_billing_service

        # Mock complete onboarding
        updated_account_details = UserAccountDetails()
        updated_account_details.balance_cents = 0.0
        updated_account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        updated_account_details.onboarding_completed = True
        mock_complete_onboarding.return_value = updated_account_details

        # Mock OpenMeter service
        mock_openmeter_service = Mock()
        mock_openmeter_service_cls.return_value = mock_openmeter_service

        # Create test event
        event = _create_stripe_event_data("cus_test123")

        # Call the function twice (simulating webhook retries)
        accounting_controller.handle_subscription_created_with_setup(event, session)
        accounting_controller.handle_subscription_created_with_setup(event, session)

        # Verify services were called for each invocation
        assert mock_create_litellm_user_and_key.call_count == 2
        assert mock_billing_service.signup_subscription.call_count == 2
        assert mock_complete_onboarding.call_count == 2
        assert mock_openmeter_service.create_customer.call_count == 2

        # Verify final state is correct
        session.refresh(user.account_details)
        assert user.account_details.stripe_customer_id == "cus_test123"


# ---------------------------------------------------------------------------
# Tests for complete_onboarding
# ---------------------------------------------------------------------------


class _FakeBillingServiceForOnboarding:
    """Billing service stub for onboarding tests that tracks skip_subscription calls."""

    def __init__(self, db: Session):
        self.db = db

    def skip_subscription(self, user: User, external_id: str):
        """Update user account details to simulate state transition."""
        user.account_details.status = UserAccountStatus.NO_SUBSCRIPTION
        return user.account_details


class TestCompleteOnboarding:
    """Test cases for complete_onboarding function."""

    def test_complete_onboarding_new_state_transitions_to_no_subscription(
        self, monkeypatch: pytest.MonkeyPatch, session: Session, user: User
    ):
        """Test that user in NEW state transitions to NO_SUBSCRIPTION and marks onboarding complete."""
        # Arrange
        account_details = user.account_details
        account_details.status = UserAccountStatus.NEW
        account_details.onboarding_completed = False
        session.add(account_details)
        session.commit()

        mock_billing_service = Mock(spec=_FakeBillingServiceForOnboarding)

        # Make skip_subscription update the status when called
        def skip_subscription_side_effect(user: User, external_id: str):
            user.account_details.status = UserAccountStatus.NO_SUBSCRIPTION
            return user.account_details

        mock_billing_service.skip_subscription.side_effect = (
            skip_subscription_side_effect
        )
        monkeypatch.setattr(
            accounting_controller, "BillingService", lambda db: mock_billing_service  # type: ignore
        )

        # Act
        result = accounting_controller.complete_onboarding(user, session)

        # Assert
        assert isinstance(result, UserAccountDetails)
        assert result.onboarding_completed is True
        mock_billing_service.skip_subscription.assert_called_once_with(
            user, f"onboarding_{user.id}"
        )

        # Verify database state
        session.refresh(account_details)
        assert account_details.onboarding_completed is True
        assert account_details.status == UserAccountStatus.NO_SUBSCRIPTION

    def test_complete_onboarding_no_subscription_state_idempotent(
        self, monkeypatch: pytest.MonkeyPatch, session: Session, user: User
    ):
        """Test that user already in NO_SUBSCRIPTION state doesn't call skip_subscription (idempotent)."""
        # Arrange
        account_details = user.account_details
        account_details.status = UserAccountStatus.NO_SUBSCRIPTION
        account_details.onboarding_completed = False
        session.add(account_details)
        session.commit()

        mock_billing_service = Mock(spec=_FakeBillingServiceForOnboarding)
        mock_billing_service.skip_subscription.return_value = account_details
        monkeypatch.setattr(
            accounting_controller, "BillingService", lambda db: mock_billing_service  # type: ignore
        )

        # Act
        result = accounting_controller.complete_onboarding(user, session)

        # Assert
        assert isinstance(result, UserAccountDetails)
        assert result.onboarding_completed is True
        mock_billing_service.skip_subscription.assert_not_called()

        # Verify database state
        session.refresh(account_details)
        assert account_details.onboarding_completed is True
        assert account_details.status == UserAccountStatus.NO_SUBSCRIPTION

    def test_complete_onboarding_active_subscription_state_idempotent(
        self, monkeypatch: pytest.MonkeyPatch, session: Session, user: User
    ):
        """Test that user in ACTIVE_SUBSCRIPTION state doesn't call skip_subscription (idempotent)."""
        # Arrange
        account_details = user.account_details
        account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        account_details.onboarding_completed = False
        session.add(account_details)
        session.commit()

        mock_billing_service = Mock(spec=_FakeBillingServiceForOnboarding)
        mock_billing_service.skip_subscription.return_value = account_details
        monkeypatch.setattr(
            accounting_controller, "BillingService", lambda db: mock_billing_service  # type: ignore
        )

        # Act
        result = accounting_controller.complete_onboarding(user, session)

        # Assert
        assert isinstance(result, UserAccountDetails)
        assert result.onboarding_completed is True
        mock_billing_service.skip_subscription.assert_not_called()

        # Verify database state
        session.refresh(account_details)
        assert account_details.onboarding_completed is True
        assert account_details.status == UserAccountStatus.ACTIVE_SUBSCRIPTION

    def test_complete_onboarding_already_completed_idempotent(
        self, monkeypatch: pytest.MonkeyPatch, session: Session, user: User
    ):
        """Test that calling complete_onboarding multiple times is idempotent."""
        # Arrange
        account_details = user.account_details
        account_details.status = UserAccountStatus.NEW
        account_details.onboarding_completed = False
        session.add(account_details)
        session.commit()

        mock_billing_service = Mock(spec=_FakeBillingServiceForOnboarding)
        mock_billing_service.skip_subscription.return_value = account_details
        monkeypatch.setattr(
            accounting_controller, "BillingService", lambda db: mock_billing_service  # type: ignore
        )

        # Act - call twice
        result1 = accounting_controller.complete_onboarding(user, session)
        # After first call, status should be NO_SUBSCRIPTION
        account_details.status = UserAccountStatus.NO_SUBSCRIPTION
        session.commit()
        result2 = accounting_controller.complete_onboarding(user, session)

        # Assert
        assert result1.onboarding_completed is True
        assert result2.onboarding_completed is True
        # skip_subscription should only be called once (on first call)
        mock_billing_service.skip_subscription.assert_called_once_with(
            user, f"onboarding_{user.id}"
        )

        # Verify database state
        session.refresh(account_details)
        assert account_details.onboarding_completed is True
