"""
Unit tests for BillingService.

This module tests the BillingService in isolation by mocking all dependencies
except the database session:
- Mock command handler, query service, and event store
- Use real DB session from conftest.py
- Verify both return values AND that dependencies were called correctly
- Test the service as an orchestration layer that delegates to specialized components
"""

import uuid
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from src.accounting.billing_command_handlers import (
    BillingCommandError,
    BillingCommandHandler,
)
from src.accounting.billing_query_service import BillingQueryService
from src.accounting.billing_service import BillingService
from src.accounting.billing_state_machine import (
    AccountStatusResponse,
    BalanceStatusWithPreview,
    UsageImpactSimulation,
)
from src.accounting.event_store import EventStore
from src.accounting.models import PendingTopup, PendingTopupStatus, UserAccountStatus
from src.models import User


# Global fixtures for BillingService testing
@pytest.fixture
def user_id():
    """Test user ID."""
    return uuid.uuid4()


@pytest.fixture
def mock_event_store():
    """Mock EventStore for testing."""
    return Mock(spec=EventStore)


@pytest.fixture
def mock_command_handler(mock_event_store: Mock, session: Session):
    """Mock BillingCommandHandler for testing."""
    return Mock(spec=BillingCommandHandler)


@pytest.fixture
def mock_query_service(session: Session):
    """Mock BillingQueryService for testing."""
    return Mock(spec=BillingQueryService)


@pytest.fixture
def mock_refresh(session: Session):
    """Mock db.refresh for testing."""
    with patch.object(session, "refresh") as mock_refresh:
        yield mock_refresh


@pytest.fixture
def billing_service(
    session: Session,
    mock_event_store: Mock,
    mock_command_handler: Mock,
    mock_query_service: Mock,
):
    """Create BillingService with mocked dependencies."""
    service = BillingService(db=session)
    service.event_store = mock_event_store
    service.command_handler = mock_command_handler
    service.query_service = mock_query_service
    return service


class TestSubscriptionLifecycle:
    """Test subscription lifecycle management methods."""

    def test_signup_subscription_success(
        self,
        billing_service: BillingService,
        user: User,
        session: Session,
        mock_refresh: Mock,
    ):
        """Test successful subscription signup."""
        # Execute
        result = billing_service.signup_subscription(user, "stripe_sub_123")

        # Verify command handler was called correctly
        billing_service.command_handler.handle_signup_subscription.assert_called_once_with(
            user.id, "stripe_sub_123"
        )

        # Verify account details were refreshed
        mock_refresh.assert_called_once_with(user.account_details)

        # Verify account details were returned
        assert result == user.account_details

    def test_signup_subscription_command_error(
        self, billing_service: BillingService, user: User
    ):
        """Test subscription signup with command handler error."""
        # Setup command handler to raise error
        billing_service.command_handler.handle_signup_subscription.side_effect = (
            BillingCommandError("Command failed")
        )

        # Execute and verify error is propagated
        with pytest.raises(BillingCommandError, match="Command failed"):
            billing_service.signup_subscription(user, "stripe_sub_123")

        # Verify command handler was called
        billing_service.command_handler.handle_signup_subscription.assert_called_once_with(
            user.id, "stripe_sub_123"
        )

    def test_cancel_subscription_success(
        self,
        billing_service: BillingService,
        user: User,
        session: Session,
        mock_refresh: Mock,
    ):
        """Test successful subscription cancellation."""
        # Execute
        result = billing_service.cancel_subscription(user, "cancel_123")

        # Verify command handler was called correctly
        billing_service.command_handler.handle_cancel_subscription.assert_called_once_with(
            user.id, "cancel_123"
        )

        # Verify account details were refreshed
        mock_refresh.assert_called_once_with(user.account_details)

        # Verify return value is the account details object
        assert result == user.account_details

    def test_cancel_subscription_command_error(
        self, billing_service: BillingService, user: User
    ):
        """Test subscription cancellation with command handler error."""
        # Setup command handler to raise error
        billing_service.command_handler.handle_cancel_subscription.side_effect = (
            BillingCommandError("Cancel failed")
        )

        # Execute and verify error is propagated
        with pytest.raises(BillingCommandError, match="Cancel failed"):
            billing_service.cancel_subscription(user, "cancel_123")

    def test_reactivate_subscription_success(
        self,
        billing_service: BillingService,
        user: User,
        session: Session,
        mock_refresh: Mock,
    ):
        """Test successful subscription reactivation (delegates to signup)."""
        # Execute
        result = billing_service.reactivate_subscription(user, "reactivate_123")

        # Verify delegates to signup command handler
        billing_service.command_handler.handle_signup_subscription.assert_called_once_with(
            user.id, "reactivate_123"
        )

        # Verify account details were refreshed
        mock_refresh.assert_called_once_with(user.account_details)

        # Verify return value is the account details object
        assert result == user.account_details

    def test_reactivate_subscription_command_error(
        self, billing_service: BillingService, user: User
    ):
        """Test subscription reactivation with command handler error."""
        # Setup command handler to raise error
        billing_service.command_handler.handle_signup_subscription.side_effect = (
            BillingCommandError("Reactivate failed")
        )

        # Execute and verify error is propagated
        with pytest.raises(BillingCommandError, match="Reactivate failed"):
            billing_service.reactivate_subscription(user, "reactivate_123")

    def test_skip_subscription_success(
        self,
        billing_service: BillingService,
        user: User,
        session: Session,
        mock_refresh: Mock,
    ):
        """Test successful subscription skip."""
        # Execute
        result = billing_service.skip_subscription(user, "onboarding_complete_123")

        # Verify command handler was called correctly
        billing_service.command_handler.handle_skip_subscription.assert_called_once_with(
            user.id, "onboarding_complete_123"
        )

        # Verify account details were refreshed
        mock_refresh.assert_called_once_with(user.account_details)

        # Verify return value is the account details object
        assert result == user.account_details

    def test_skip_subscription_command_error(
        self, billing_service: BillingService, user: User
    ):
        """Test subscription skip with command handler error."""
        # Setup command handler to raise error
        billing_service.command_handler.handle_skip_subscription.side_effect = (
            BillingCommandError("Skip failed")
        )

        # Execute and verify error is propagated
        with pytest.raises(BillingCommandError, match="Skip failed"):
            billing_service.skip_subscription(user, "onboarding_complete_123")

        # Verify command handler was called
        billing_service.command_handler.handle_skip_subscription.assert_called_once_with(
            user.id, "onboarding_complete_123"
        )


class TestBalanceManagement:
    """Test balance management methods."""

    def test_topup_balance_success(
        self,
        billing_service: BillingService,
        user: User,
        session: Session,
        mock_refresh: Mock,
    ):
        """Test successful balance top-up."""
        # Execute
        result = billing_service.topup_balance(
            user, 2000, "stripe_pi_123", "https://invoice.url"
        )

        # Verify command handler was called correctly
        billing_service.command_handler.handle_topup_balance.assert_called_once_with(
            user.id, 2000, "stripe_pi_123", "https://invoice.url"
        )

        # Verify account details were refreshed
        mock_refresh.assert_called_once_with(user.account_details)

        # Verify return value is the account details object
        assert result == user.account_details

    def test_topup_balance_without_invoice_url(
        self,
        billing_service: BillingService,
        user: User,
        session: Session,
        mock_refresh: Mock,
    ):
        """Test balance top-up without invoice URL."""
        # Execute
        result = billing_service.topup_balance(user, 1500, "stripe_pi_456")

        # Verify command handler was called with None for invoice URL
        billing_service.command_handler.handle_topup_balance.assert_called_once_with(
            user.id, 1500, "stripe_pi_456", None
        )

        # Verify account details were refreshed
        mock_refresh.assert_called_once_with(user.account_details)

        # Verify return value
        assert result == user.account_details

    def test_topup_balance_command_error(
        self, billing_service: BillingService, user: User
    ):
        """Test balance top-up with command handler error."""
        # Setup command handler to raise error
        billing_service.command_handler.handle_topup_balance.side_effect = (
            BillingCommandError("Topup failed")
        )

        # Execute and verify error is propagated
        with pytest.raises(BillingCommandError, match="Topup failed"):
            billing_service.topup_balance(user, 1000, "stripe_pi_123")

    def test_record_usage_success(
        self,
        billing_service: BillingService,
        user: User,
        session: Session,
        mock_refresh: Mock,
    ):
        """Test successful usage recording."""
        # Execute
        result = billing_service.record_usage(user, 150.5, "request_123")

        # Verify command handler was called correctly
        billing_service.command_handler.handle_record_usage.assert_called_once_with(
            user.id, 150.5, "request_123"
        )

        # Verify account details were refreshed
        mock_refresh.assert_called_once_with(user.account_details)

        # Verify return value is the account details object
        assert result == user.account_details

    def test_record_usage_command_error(
        self, billing_service: BillingService, user: User
    ):
        """Test usage recording with command handler error."""
        # Setup command handler to raise error
        billing_service.command_handler.handle_record_usage.side_effect = (
            BillingCommandError("Usage failed")
        )

        # Execute and verify error is propagated
        with pytest.raises(BillingCommandError, match="Usage failed"):
            billing_service.record_usage(user, 100.0, "request_123")

    def test_process_full_refund_with_balance(
        self, billing_service: BillingService, user: User
    ):
        """Test full refund with existing usage balance."""
        # Setup - user has balance to refund
        user.account_details.balance_cents = 1500

        with (
            patch.object(billing_service, "_refund_balance") as mock_refund_balance,
            patch.object(billing_service, "cancel_subscription") as mock_cancel,
        ):

            mock_refund_balance.return_value = user.account_details
            mock_cancel.return_value = user.account_details

            # Execute
            result = billing_service.process_full_refund(user, "refund_123")

            # Verify balance refund was called first
            mock_refund_balance.assert_called_once_with(user, 1500, "refund_123")

            # Verify subscription cancellation was called
            mock_cancel.assert_called_once_with(user, "refund_123")

            # Verify return value
            assert result == user.account_details

    def test_process_full_refund_without_balance(
        self, billing_service: BillingService, user: User, session: Session
    ):
        """Test full refund without usage balance and already cancelled subscription."""
        # Setup - user has no balance and subscription already cancelled
        user.account_details.balance_cents = 0
        user.account_details.status = UserAccountStatus.NO_SUBSCRIPTION

        with (
            patch.object(billing_service, "_refund_balance") as mock_refund_balance,
            patch.object(billing_service, "cancel_subscription") as mock_cancel,
        ):

            mock_cancel.return_value = user.account_details

            # Execute
            result = billing_service.process_full_refund(user, "refund_123")

            # Verify no balance refund was called (balance is 0)
            mock_refund_balance.assert_not_called()

            # Verify subscription cancellation was NOT called (already cancelled)
            mock_cancel.assert_not_called()

            # Verify return value
            assert result == user.account_details

    def test_process_balance_refund_success(
        self, billing_service: BillingService, user: User, session: Session
    ):
        """Test successful balance refund."""
        # Setup
        user.account_details.balance_cents = 1200

        with patch.object(billing_service, "_refund_balance") as mock_refund_balance:
            mock_refund_balance.return_value = user.account_details

            # Execute
            result = billing_service.process_balance_refund(user, "refund_123")

            # Verify internal refund method was called
            mock_refund_balance.assert_called_once_with(user, 1200, "refund_123")

            # Verify return value
            assert result == user.account_details

    def test_refund_balance_internal_success(
        self, billing_service: BillingService, user: User, session: Session
    ):
        """Test internal _refund_balance method."""
        # Mock db.refresh to verify it's called
        with patch.object(billing_service.db, "refresh") as mock_refresh:
            # Execute
            result = billing_service._refund_balance(user, 500.0, "refund_internal_123")

            # Verify command handler was called correctly
            billing_service.command_handler.handle_process_balance_refund.assert_called_once_with(
                user.id, 500.0, "refund_internal_123"
            )

            # Verify account details were refreshed
            mock_refresh.assert_called_once_with(user.account_details)

            # Verify return value is the account details object
            assert result == user.account_details

    def test_refund_balance_command_error(
        self, billing_service: BillingService, user: User
    ):
        """Test balance refund with command handler error."""
        # Setup command handler to raise error
        billing_service.command_handler.handle_process_balance_refund.side_effect = (
            BillingCommandError("Refund failed")
        )

        # Execute and verify error is propagated
        with pytest.raises(BillingCommandError, match="Refund failed"):
            billing_service._refund_balance(user, 500.0, "refund_123")


class TestBillingCycleAndChargeback:
    """Test billing cycle and chargeback handling methods."""

    def test_start_new_billing_cycle_success(
        self,
        billing_service: BillingService,
        user: User,
        session: Session,
        mock_refresh: Mock,
    ):
        """Test successful billing cycle start."""
        # Execute
        result = billing_service.start_new_billing_cycle(user)

        # Verify command handler was called correctly
        billing_service.command_handler.handle_start_billing_cycle.assert_called_once_with(
            user.id
        )

        # Verify account details were refreshed
        mock_refresh.assert_called_once_with(user.account_details)

        # Verify return value is the account details object
        assert result == user.account_details

    def test_start_new_billing_cycle_command_error(
        self, billing_service: BillingService, user: User
    ):
        """Test billing cycle start with command handler error."""
        # Setup command handler to raise error
        billing_service.command_handler.handle_start_billing_cycle.side_effect = (
            BillingCommandError("Cycle start failed")
        )

        # Execute and verify error is propagated
        with pytest.raises(BillingCommandError, match="Cycle start failed"):
            billing_service.start_new_billing_cycle(user)

    def test_detect_chargeback_success(
        self,
        billing_service: BillingService,
        user: User,
        session: Session,
        mock_refresh: Mock,
    ):
        """Test successful chargeback detection."""
        # Execute
        result = billing_service.detect_chargeback(user, "chargeback_123")

        # Verify command handler was called correctly
        billing_service.command_handler.handle_detect_chargeback.assert_called_once_with(
            user.id, "chargeback_123"
        )

        # Verify account details were refreshed
        mock_refresh.assert_called_once_with(user.account_details)

        # Verify return value is the account details object
        assert result == user.account_details

    def test_detect_chargeback_command_error(
        self, billing_service: BillingService, user: User
    ):
        """Test chargeback detection with command handler error."""
        # Setup command handler to raise error
        billing_service.command_handler.handle_detect_chargeback.side_effect = (
            BillingCommandError("Chargeback failed")
        )

        # Execute and verify error is propagated
        with pytest.raises(BillingCommandError, match="Chargeback failed"):
            billing_service.detect_chargeback(user, "chargeback_123")


class TestPendingTopupSystem:
    """Test pending top-up system methods."""

    def test_create_pending_topup_success(
        self, billing_service: BillingService, user: User, session: Session
    ):
        """Test successful pending top-up creation."""
        user_id = user.id
        session_id = "cs_test_123"
        amount_cents = 2000

        # Execute
        result = billing_service.create_pending_topup(user_id, session_id, amount_cents)

        # Verify database record was created
        assert result.user_id == user_id
        assert result.session_id == session_id
        assert result.amount_cents == amount_cents
        assert result.status == PendingTopupStatus.PENDING
        assert result.id is not None

        # Verify record exists in database
        db_record = (
            session.query(PendingTopup)
            .filter(PendingTopup.session_id == session_id)
            .first()
        )
        assert db_record is not None
        assert db_record.user_id == user_id

    def test_create_pending_topup_invalid_amount(
        self, billing_service: BillingService, user: User
    ):
        """Test pending top-up creation with invalid amount."""
        user_id = user.id
        session_id = "cs_test_invalid"
        amount_cents = -500  # Invalid negative amount

        # Execute and verify error
        with pytest.raises(ValueError, match="Top-up amount must be positive"):
            billing_service.create_pending_topup(user_id, session_id, amount_cents)

    def test_create_pending_topup_duplicate_session(
        self, billing_service: BillingService, user: User, session: Session
    ):
        """Test pending top-up creation with duplicate session ID."""
        user_id = user.id
        session_id = "cs_test_duplicate"
        amount_cents = 1500

        # Create first pending top-up
        first_result = billing_service.create_pending_topup(
            user_id, session_id, amount_cents
        )

        # Attempt to create duplicate
        second_result = billing_service.create_pending_topup(
            user_id, session_id, amount_cents
        )

        # Verify same record is returned
        assert first_result.id == second_result.id
        assert second_result.user_id == user_id
        assert second_result.session_id == session_id
        assert second_result.amount_cents == amount_cents

    def test_process_pending_topup_success(
        self, billing_service: BillingService, user: User, session: Session
    ):
        """Test successful pending top-up processing."""
        # Setup - create pending top-up
        user_id = user.id
        session_id = "cs_test_process"
        amount_cents = 1800
        download_url = "https://stripe.com/invoice/download"

        existing_monthly_credits_cents = user.account_details.monthly_credits_total
        existing_monthly_credits_used = user.account_details.monthly_credits_used

        pending_topup = billing_service.create_pending_topup(
            user_id, session_id, amount_cents
        )
        assert pending_topup.status == PendingTopupStatus.PENDING

        # Mock topup_balance to succeed
        with patch.object(billing_service, "topup_balance") as mock_topup:
            mock_topup.return_value = user.account_details

            # Execute
            result = billing_service.process_pending_topup(
                session_id, download_url, True
            )

            # Verify topup_balance was called
            mock_topup.assert_called_once_with(
                user=user,
                amount_cents=amount_cents,
                external_id=session_id,
                invoice_download_url=download_url,
            )

            # Verify pending top-up was marked as completed
            session.refresh(pending_topup)
            assert pending_topup.status == PendingTopupStatus.COMPLETED
            assert pending_topup.completed_at is not None

            # Verify return value
            assert result == user.account_details
            assert (
                result.monthly_credits_total == existing_monthly_credits_cents
            )  # monthly credits remaining is 200
            assert (
                result.monthly_credits_used == existing_monthly_credits_used
            )  # monthly credits used is 0
            assert result.balance_cents == 1800

    def test_process_pending_topup_failure(
        self, billing_service: BillingService, user: User, session: Session
    ):
        """Test pending top-up processing with failure."""
        # Setup - create pending top-up
        user_id = user.id
        session_id = "cs_test_fail"
        amount_cents = 1200

        existing_monthly_credits_cents = user.account_details.monthly_credits_total
        existing_monthly_credits_used = user.account_details.monthly_credits_used
        existing_balance_cents = user.account_details.balance_cents

        pending_topup = billing_service.create_pending_topup(
            user_id, session_id, amount_cents
        )

        # Execute with success=False
        result = billing_service.process_pending_topup(session_id, None, False)

        # Verify pending top-up was marked as failed
        session.refresh(pending_topup)
        assert pending_topup.status == PendingTopupStatus.FAILED

        # Verify return value is unchanged account details
        assert result == user.account_details
        assert result.monthly_credits_total == existing_monthly_credits_cents
        assert result.monthly_credits_used == existing_monthly_credits_used
        assert result.balance_cents == existing_balance_cents

    def test_process_pending_topup_not_found(self, billing_service: BillingService):
        """Test pending top-up processing with non-existent session."""
        session_id = "cs_test_nonexistent"

        # Execute and verify error
        with pytest.raises(ValueError, match="No pending top-up found for session"):
            billing_service.process_pending_topup(session_id, None, True)

    def test_process_pending_topup_already_processed(
        self, billing_service: BillingService, user: User, session: Session
    ):
        """Test pending top-up processing with already processed session."""
        # Setup - create and complete pending top-up
        user_id = user.id
        session_id = "cs_test_completed"
        amount_cents = 1000

        existing_monthly_credits_cents = user.account_details.monthly_credits_total
        existing_monthly_credits_used = user.account_details.monthly_credits_used
        existing_balance_cents = user.account_details.balance_cents

        pending_topup = billing_service.create_pending_topup(
            user_id, session_id, amount_cents
        )
        pending_topup.status = PendingTopupStatus.COMPLETED
        pending_topup.completed_at = datetime.now()
        session.add(pending_topup)
        session.commit()

        # Execute - should return account details without processing
        result = billing_service.process_pending_topup(session_id, None, True)

        # Verify return value
        assert result == user.account_details
        assert result.monthly_credits_total == existing_monthly_credits_cents
        assert result.monthly_credits_used == existing_monthly_credits_used
        assert result.balance_cents == existing_balance_cents

        # Verify status remains completed
        session.refresh(pending_topup)
        assert pending_topup.status == PendingTopupStatus.COMPLETED

    def test_process_pending_topup_exception_handling(
        self, billing_service: BillingService, user: User, session: Session
    ):
        """Test pending top-up processing with exception during topup."""
        # Setup - create pending top-up
        user_id = user.id
        session_id = "cs_test_exception"
        amount_cents = 1600

        existing_monthly_credits_cents = user.account_details.monthly_credits_total
        existing_monthly_credits_used = user.account_details.monthly_credits_used
        existing_balance_cents = user.account_details.balance_cents

        pending_topup = billing_service.create_pending_topup(
            user_id, session_id, amount_cents
        )

        # Mock topup_balance to raise exception
        with patch.object(billing_service, "topup_balance") as mock_topup:
            mock_topup.side_effect = Exception("Payment processing failed")

            # Execute and verify exception is raised
            with pytest.raises(Exception, match="Payment processing failed"):
                billing_service.process_pending_topup(session_id, None, True)

            # Verify pending top-up was marked as failed
            session.refresh(pending_topup)
            assert pending_topup.status == PendingTopupStatus.FAILED

            session.refresh(user.account_details)
            assert (
                user.account_details.monthly_credits_total
                == existing_monthly_credits_cents
            )
            assert (
                user.account_details.monthly_credits_used
                == existing_monthly_credits_used
            )
            assert user.account_details.balance_cents == existing_balance_cents


class TestQueryDelegation:
    """Test query method delegation to query service."""

    def test_get_account_status_detailed_delegation(
        self, billing_service: BillingService, user: User
    ):
        """Test account status detailed query delegation."""
        # Setup mock return value
        mock_response = AccountStatusResponse(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance_cents=1500,
            usage_balance_dollars=15.0,
            monthly_credits_cents=500,
            monthly_credits_dollars=5.0,
            has_active_subscription=True,
            is_suspended=False,
            is_closed=False,
            has_usage_balance=True,
            subscription_only=False,
            using_metered_billing=False,
            no_subscription=False,
        )
        billing_service.query_service.get_account_status_detailed.return_value = (
            mock_response
        )

        # Execute
        result = billing_service.get_account_status_detailed(user)

        # Verify delegation
        billing_service.query_service.get_account_status_detailed.assert_called_once_with(
            user
        )

        # Verify return value
        assert result == mock_response
        assert result.state == UserAccountStatus.ACTIVE_SUBSCRIPTION
        assert result.usage_balance_cents == 1500

    def test_can_afford_request_delegation(
        self, billing_service: BillingService, user: User
    ):
        """Test can afford request query delegation."""
        # Setup mock return value
        billing_service.query_service.can_afford_request.return_value = True

        # Execute
        result = billing_service.can_afford_request(user, 250.0)

        # Verify delegation
        billing_service.query_service.can_afford_request.assert_called_once_with(
            user, 250.0
        )

        # Verify return value
        assert result is True

    def test_can_afford_request_false_delegation(
        self, billing_service: BillingService, user: User
    ):
        """Test can afford request query delegation returning False."""
        # Setup mock return value
        billing_service.query_service.can_afford_request.return_value = False

        # Execute
        result = billing_service.can_afford_request(user, 5000.0)

        # Verify delegation
        billing_service.query_service.can_afford_request.assert_called_once_with(
            user, 5000.0
        )

        # Verify return value
        assert result is False

    def test_simulate_usage_impact_delegation(
        self, billing_service: BillingService, user: User
    ):
        """Test usage impact simulation query delegation."""
        # Setup mock return value
        mock_simulation = UsageImpactSimulation(
            current_usage_balance_cents=1200.0,
            current_status=UserAccountStatus.METERED_BILLING,
            current_monthly_credits_used=300.0,
            remaining_monthly_credits=200.0,
            estimated_cost_cents=150.0,
            projected_usage_balance_cents=1050.0,
            projected_monthly_credits_used=300.0,
            projected_status=UserAccountStatus.METERED_BILLING,
            would_be_suspended=False,
            would_be_metered=True,
            would_be_low_balance=False,
        )
        billing_service.query_service.simulate_usage_impact.return_value = (
            mock_simulation
        )

        # Execute
        result = billing_service.simulate_usage_impact(user, 150.0)

        # Verify delegation
        billing_service.query_service.simulate_usage_impact.assert_called_once_with(
            user, 150.0
        )

        # Verify return value
        assert result == mock_simulation
        assert result.estimated_cost_cents == 150.0
        assert result.would_be_suspended is False

    def test_get_balance_status_with_preview_delegation(
        self, billing_service: BillingService, user: User
    ):
        """Test balance status with preview query delegation."""
        # Setup mock return value
        mock_status = BalanceStatusWithPreview(
            current_status=AccountStatusResponse(
                state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                usage_balance_cents=800,
                usage_balance_dollars=8.0,
                monthly_credits_cents=500,
                monthly_credits_dollars=5.0,
                has_active_subscription=True,
                is_suspended=False,
                is_closed=False,
                has_usage_balance=True,
                subscription_only=False,
                using_metered_billing=False,
                no_subscription=False,
            ),
            usage_impact=UsageImpactSimulation(
                current_usage_balance_cents=800.0,
                current_status=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                current_monthly_credits_used=200.0,
                remaining_monthly_credits=300.0,
                estimated_cost_cents=100.0,
                projected_usage_balance_cents=800.0,
                projected_monthly_credits_used=300.0,
                projected_status=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                would_be_suspended=False,
                would_be_metered=False,
                would_be_low_balance=False,
            ),
            can_afford=True,
            top_up_needed_cents=0,
            top_up_needed_dollars=0.0,
            enforcement_decision=Mock(),  # Mock the enforcement decision
        )
        billing_service.query_service.get_balance_status_with_preview.return_value = (
            mock_status
        )

        # Execute
        result = billing_service.get_balance_status_with_preview(user, 100.0)

        # Verify delegation
        billing_service.query_service.get_balance_status_with_preview.assert_called_once_with(
            user, 100.0
        )

        # Verify return value
        assert result == mock_status
        assert result.can_afford is True
        assert result.top_up_needed_cents == 0
