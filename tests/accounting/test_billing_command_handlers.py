"""
Unit tests for BillingCommandHandler.

This module tests the command handler in isolation by mocking all dependencies
except the database session:
- Mock FSM and EventStore to ensure true unit testing
- Use real DB session from conftest.py
- Verify both return values AND that dependencies were called correctly
"""

import uuid
from datetime import datetime
from typing import List
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from src.accounting.billing_command_handlers import (
    BillingCommandError,
    BillingCommandHandler,
)
from src.accounting.billing_events import (
    BalanceRefundEvent,
    BalanceTopUpEvent,
    BillingEvent,
    ChargebackDetectedEvent,
    CreditUsageEvent,
    MonthlyCreditsResetEvent,
    StateTransitionEvent,
    SubscriptionCancelEvent,
    SubscriptionSignupEvent,
)
from src.accounting.billing_state_machine import (
    AccountStatusResponse,
    BillingFSMInvalidTransitionError,
    BillingStateMachine,
)
from src.accounting.event_store import EventStore, OptimisticConcurrencyError
from src.accounting.models import UserAccountDetails, UserAccountStatus


class TestBillingCommandHandler:
    """Unit tests for BillingCommandHandler with mocked dependencies."""

    @pytest.fixture
    def user_id(self):
        """Test user ID."""
        return uuid.uuid4()

    @pytest.fixture
    def mock_event_store(self):
        """Mock EventStore for testing."""
        return Mock(spec=EventStore)

    @pytest.fixture
    def mock_fsm(self, user_id: uuid.UUID):
        """Mock BillingStateMachine for testing."""
        fsm = Mock(spec=BillingStateMachine)
        fsm.user_id = user_id
        fsm.version = 5
        fsm.state = UserAccountStatus.ACTIVE_SUBSCRIPTION
        fsm.usage_balance = 1000
        fsm.monthly_credits_used = 200
        fsm.monthly_credits_cents = 500
        return fsm

    @pytest.fixture
    def command_handler(self, mock_event_store: Mock, session: Session):
        """Create BillingCommandHandler with mocked dependencies."""
        return BillingCommandHandler(mock_event_store, session)

    @pytest.fixture
    def sample_events(self, user_id: uuid.UUID):
        """Sample events for testing."""
        return [
            CreditUsageEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                amount_cents=100,
                external_id="test_1",
            ),
            StateTransitionEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                from_state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                to_state=UserAccountStatus.METERED_BILLING,
                reason="USAGE_RECORDED",
            ),
        ]

    # =============================================================================
    # handle_record_usage() Tests
    # =============================================================================

    def test_handle_record_usage_success(
        self,
        command_handler: BillingCommandHandler,
        mock_event_store: Mock,
        user_id: uuid.UUID,
        sample_events: List[BillingEvent],
    ):
        """Test successful usage recording with event generation."""
        # Mock FSM reconstruction and event generation
        with (
            patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct,
            patch.object(command_handler, "_update_account_details") as mock_update,
        ):

            mock_fsm = Mock()
            mock_fsm.version = 3
            mock_fsm.record_usage.return_value = sample_events
            mock_reconstruct.return_value = mock_fsm

            # Execute
            command_handler.handle_record_usage(user_id, 150.0, "external_123")

            # Verify call sequence
            mock_reconstruct.assert_called_once_with(user_id)
            mock_fsm.record_usage.assert_called_once_with(150.0, "external_123")
            mock_event_store.save_events.assert_called_once_with(
                user_id, sample_events, 3
            )
            mock_update.assert_called_once_with(user_id)

    def test_handle_record_usage_fsm_validation_error(
        self, command_handler: BillingCommandHandler, user_id: uuid.UUID
    ):
        """Test that FSM validation errors are re-raised as-is."""
        with patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct:
            mock_fsm = Mock()
            mock_fsm.record_usage.side_effect = BillingFSMInvalidTransitionError(
                "Invalid state"
            )
            mock_reconstruct.return_value = mock_fsm

            # Should re-raise FSM validation error
            with pytest.raises(BillingFSMInvalidTransitionError, match="Invalid state"):
                command_handler.handle_record_usage(user_id, 150.0, "external_123")

    def test_handle_record_usage_concurrency_error(
        self,
        command_handler: BillingCommandHandler,
        mock_event_store: Mock,
        user_id: uuid.UUID,
    ):
        """Test optimistic concurrency conflict handling."""
        with patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct:
            mock_fsm = Mock()
            mock_fsm.version = 3
            mock_fsm.record_usage.return_value = []
            mock_reconstruct.return_value = mock_fsm

            # Mock concurrency error
            mock_event_store.save_events.side_effect = OptimisticConcurrencyError(
                "Version conflict"
            )

            # Should wrap in BillingCommandError
            with pytest.raises(
                BillingCommandError, match="Concurrency conflict record usage"
            ):
                command_handler.handle_record_usage(user_id, 150.0, "external_123")

    def test_handle_record_usage_infrastructure_error(
        self, command_handler: BillingCommandHandler, user_id: uuid.UUID
    ):
        """Test infrastructure failure handling."""
        with patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct:
            mock_reconstruct.side_effect = Exception("Database connection failed")

            # Should wrap in BillingCommandError
            with pytest.raises(BillingCommandError, match="Failed to record usage"):
                command_handler.handle_record_usage(user_id, 150.0, "external_123")

    # =============================================================================
    # handle_topup_balance() Tests
    # =============================================================================

    def test_handle_topup_balance_success(
        self,
        command_handler: BillingCommandHandler,
        mock_event_store: Mock,
        user_id: uuid.UUID,
    ):
        """Test successful balance top-up."""
        topup_events = [
            BalanceTopUpEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                amount_cents=1000,
                external_id="stripe_123",
                invoice_url="https://invoice.url",
            )
        ]

        with (
            patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct,
            patch.object(command_handler, "_update_account_details") as mock_update,
        ):

            mock_fsm = Mock()
            mock_fsm.version = 2
            mock_fsm.topup_usage_balance.return_value = topup_events
            mock_reconstruct.return_value = mock_fsm

            # Execute
            command_handler.handle_topup_balance(
                user_id, 1000, "stripe_123", "https://invoice.url"
            )

            # Verify call sequence
            mock_reconstruct.assert_called_once_with(user_id)
            mock_fsm.topup_usage_balance.assert_called_once_with(
                1000, "stripe_123", "https://invoice.url"
            )
            mock_event_store.save_events.assert_called_once_with(
                user_id, topup_events, 2
            )
            mock_update.assert_called_once_with(user_id)

    def test_handle_topup_balance_fsm_validation_error(
        self, command_handler: BillingCommandHandler, user_id: uuid.UUID
    ):
        """Test FSM validation error for invalid top-up."""
        with patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct:
            mock_fsm = Mock()
            mock_fsm.topup_usage_balance.side_effect = BillingFSMInvalidTransitionError(
                "Cannot top up"
            )
            mock_reconstruct.return_value = mock_fsm

            with pytest.raises(BillingFSMInvalidTransitionError, match="Cannot top up"):
                command_handler.handle_topup_balance(user_id, 1000, "stripe_123")

    # =============================================================================
    # handle_signup_subscription() Tests
    # =============================================================================

    def test_handle_signup_subscription_success(
        self,
        command_handler: BillingCommandHandler,
        mock_event_store: Mock,
        user_id: uuid.UUID,
    ):
        """Test successful subscription signup."""
        signup_events = [
            SubscriptionSignupEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                external_id="stripe_sub_123",
            ),
            StateTransitionEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                from_state=UserAccountStatus.NEW,
                to_state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                reason="SIGNUP_SUBSCRIPTION",
            ),
        ]

        with (
            patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct,
            patch.object(command_handler, "_update_account_details") as mock_update,
        ):

            mock_fsm = Mock()
            mock_fsm.version = 2
            mock_fsm.signup_subscription.return_value = signup_events
            mock_reconstruct.return_value = mock_fsm

            # Execute
            command_handler.handle_signup_subscription(user_id, "stripe_sub_123")

            # Verify call sequence
            mock_reconstruct.assert_called_once_with(user_id)
            mock_fsm.signup_subscription.assert_called_once_with("stripe_sub_123")
            mock_event_store.save_events.assert_called_once_with(
                user_id, signup_events, 2
            )
            mock_update.assert_called_once_with(user_id)

    def test_handle_signup_subscription_already_subscribed(
        self, command_handler: BillingCommandHandler, user_id: uuid.UUID
    ):
        """Test signup when already subscribed."""
        with patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct:
            mock_fsm = Mock()
            mock_fsm.signup_subscription.side_effect = BillingFSMInvalidTransitionError(
                "Already subscribed"
            )
            mock_reconstruct.return_value = mock_fsm

            with pytest.raises(
                BillingFSMInvalidTransitionError, match="Already subscribed"
            ):
                command_handler.handle_signup_subscription(user_id, "stripe_sub_123")

    # =============================================================================
    # handle_skip_subscription() Tests
    # =============================================================================

    def test_handle_skip_subscription_success(
        self,
        command_handler: BillingCommandHandler,
        mock_event_store: Mock,
        user_id: uuid.UUID,
    ):
        """Test successful subscription skip during onboarding."""
        skip_events = [
            StateTransitionEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                from_state=UserAccountStatus.NEW,
                to_state=UserAccountStatus.NO_SUBSCRIPTION,
                reason="SKIP_SUBSCRIPTION",
            ),
        ]

        with (
            patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct,
            patch.object(command_handler, "_update_account_details") as mock_update,
        ):

            mock_fsm = Mock()
            mock_fsm.version = 1
            mock_fsm.skip_subscription.return_value = skip_events
            mock_reconstruct.return_value = mock_fsm

            # Execute
            command_handler.handle_skip_subscription(user_id, "onboarding_123")

            # Verify call sequence
            mock_reconstruct.assert_called_once_with(user_id)
            mock_fsm.skip_subscription.assert_called_once_with("onboarding_123")
            mock_event_store.save_events.assert_called_once_with(
                user_id, skip_events, 1
            )
            mock_update.assert_called_once_with(user_id)

    def test_handle_skip_subscription_default_external_id(
        self,
        command_handler: BillingCommandHandler,
        mock_event_store: Mock,
        user_id: uuid.UUID,
    ):
        """Test subscription skip with default external_id."""
        skip_events = [
            StateTransitionEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                from_state=UserAccountStatus.NEW,
                to_state=UserAccountStatus.NO_SUBSCRIPTION,
                reason="SKIP_SUBSCRIPTION",
            ),
        ]

        with (
            patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct,
            patch.object(command_handler, "_update_account_details") as mock_update,
        ):

            mock_fsm = Mock()
            mock_fsm.version = 1
            mock_fsm.skip_subscription.return_value = skip_events
            mock_reconstruct.return_value = mock_fsm

            # Execute with default external_id
            command_handler.handle_skip_subscription(user_id)

            # Verify call sequence - should use "onboarding" as default
            mock_reconstruct.assert_called_once_with(user_id)
            mock_fsm.skip_subscription.assert_called_once_with("onboarding")
            mock_event_store.save_events.assert_called_once_with(
                user_id, skip_events, 1
            )
            mock_update.assert_called_once_with(user_id)

    def test_handle_skip_subscription_invalid_state(
        self, command_handler: BillingCommandHandler, user_id: uuid.UUID
    ):
        """Test skip subscription from invalid state."""
        with patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct:
            mock_fsm = Mock()
            mock_fsm.skip_subscription.side_effect = BillingFSMInvalidTransitionError(
                "Cannot skip subscription from ACTIVE_SUBSCRIPTION state"
            )
            mock_reconstruct.return_value = mock_fsm

            with pytest.raises(
                BillingFSMInvalidTransitionError,
                match="Cannot skip subscription from ACTIVE_SUBSCRIPTION state",
            ):
                command_handler.handle_skip_subscription(user_id, "onboarding_123")

    # =============================================================================
    # handle_cancel_subscription() Tests
    # =============================================================================

    def test_handle_cancel_subscription_success(
        self,
        command_handler: BillingCommandHandler,
        mock_event_store: Mock,
        user_id: uuid.UUID,
    ):
        """Test successful subscription cancellation."""
        cancel_events = [
            SubscriptionCancelEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                external_id="cancel_123",
                reason="USER_REQUESTED",
            ),
            StateTransitionEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                from_state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                to_state=UserAccountStatus.NO_SUBSCRIPTION,
                reason="CANCEL_SUBSCRIPTION",
            ),
        ]

        with (
            patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct,
            patch.object(command_handler, "_update_account_details") as mock_update,
        ):

            mock_fsm = Mock()
            mock_fsm.version = 4
            mock_fsm.cancel_subscription.return_value = cancel_events
            mock_reconstruct.return_value = mock_fsm

            # Execute
            command_handler.handle_cancel_subscription(
                user_id, "cancel_123", "CUSTOMER_REQUEST"
            )

            # Verify call sequence
            mock_reconstruct.assert_called_once_with(user_id)
            mock_fsm.cancel_subscription.assert_called_once_with(
                "cancel_123", "CUSTOMER_REQUEST"
            )
            mock_event_store.save_events.assert_called_once_with(
                user_id, cancel_events, 4
            )
            mock_update.assert_called_once_with(user_id)

    # =============================================================================
    # handle_start_billing_cycle() Tests
    # =============================================================================

    def test_handle_start_billing_cycle_success(
        self,
        command_handler: BillingCommandHandler,
        mock_event_store: Mock,
        user_id: uuid.UUID,
    ):
        """Test successful billing cycle start."""
        cycle_events = [
            MonthlyCreditsResetEvent(
                event_id=uuid.uuid4(), user_id=user_id, created_at=datetime.now()
            ),
            StateTransitionEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                from_state=UserAccountStatus.SUSPENDED,
                to_state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                reason="START_BILLING_CYCLE",
            ),
        ]

        with (
            patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct,
            patch.object(command_handler, "_update_account_details") as mock_update,
        ):

            mock_fsm = Mock()
            mock_fsm.version = 6
            mock_fsm.start_new_billing_cycle.return_value = cycle_events
            mock_reconstruct.return_value = mock_fsm

            # Execute
            command_handler.handle_start_billing_cycle(user_id)

            # Verify call sequence
            mock_reconstruct.assert_called_once_with(user_id)
            mock_fsm.start_new_billing_cycle.assert_called_once()
            mock_event_store.save_events.assert_called_once_with(
                user_id, cycle_events, 6
            )
            mock_update.assert_called_once_with(user_id)

    # =============================================================================
    # handle_detect_chargeback() Tests
    # =============================================================================

    def test_handle_detect_chargeback_success(
        self,
        command_handler: BillingCommandHandler,
        mock_event_store: Mock,
        user_id: uuid.UUID,
        caplog: pytest.LogCaptureFixture,
    ):
        """Test successful chargeback detection with warning logging."""
        chargeback_events = [
            ChargebackDetectedEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                external_id="chargeback_123",
                amount_cents=2500,
            ),
            StateTransitionEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                from_state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                to_state=UserAccountStatus.CLOSED,
                reason="CHARGEBACK_DETECTED",
            ),
        ]

        with (
            patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct,
            patch.object(command_handler, "_update_account_details") as mock_update,
        ):

            mock_fsm = Mock()
            mock_fsm.version = 8
            mock_fsm.detect_chargeback.return_value = chargeback_events
            mock_reconstruct.return_value = mock_fsm

            # Execute
            command_handler.handle_detect_chargeback(user_id, "chargeback_123", 2500)

            # Verify call sequence
            mock_reconstruct.assert_called_once_with(user_id)
            mock_fsm.detect_chargeback.assert_called_once_with("chargeback_123", 2500)
            mock_event_store.save_events.assert_called_once_with(
                user_id, chargeback_events, 8
            )
            mock_update.assert_called_once_with(user_id)

            # Verify warning logging
            assert "Chargeback detected and account closed" in caplog.text
            assert str(user_id) in caplog.text
            assert "2500" in caplog.text

    # =============================================================================
    # handle_process_balance_refund() Tests
    # =============================================================================

    def test_handle_process_balance_refund_success(
        self,
        command_handler: BillingCommandHandler,
        mock_event_store: Mock,
        user_id: uuid.UUID,
    ):
        """Test successful balance refund processing."""
        refund_events = [
            BalanceRefundEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                amount_cents=500,
                external_id="refund_123",
                reason="CUSTOMER_REQUEST",
            ),
            StateTransitionEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                from_state=UserAccountStatus.METERED_BILLING,
                to_state=UserAccountStatus.SUSPENDED,
                reason="REFUND_BALANCE",
            ),
        ]

        with (
            patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct,
            patch.object(command_handler, "_update_account_details") as mock_update,
        ):

            mock_fsm = Mock()
            mock_fsm.version = 7
            mock_fsm.process_balance_refund.return_value = refund_events
            mock_reconstruct.return_value = mock_fsm

            # Execute
            command_handler.handle_process_balance_refund(
                user_id, 500.0, "refund_123", "CUSTOMER_REQUEST"
            )

            # Verify call sequence
            mock_reconstruct.assert_called_once_with(user_id)
            mock_fsm.process_balance_refund.assert_called_once_with(
                500.0, "refund_123", "CUSTOMER_REQUEST"
            )
            mock_event_store.save_events.assert_called_once_with(
                user_id, refund_events, 7
            )
            mock_update.assert_called_once_with(user_id)

    def test_handle_process_balance_refund_insufficient_balance(
        self, command_handler: BillingCommandHandler, user_id: uuid.UUID
    ):
        """Test refund with insufficient balance."""
        with patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct:
            mock_fsm = Mock()
            mock_fsm.process_balance_refund.side_effect = (
                BillingFSMInvalidTransitionError("Insufficient balance")
            )
            mock_reconstruct.return_value = mock_fsm

            with pytest.raises(
                BillingFSMInvalidTransitionError, match="Insufficient balance"
            ):
                command_handler.handle_process_balance_refund(
                    user_id, 1000.0, "refund_123"
                )

    # =============================================================================
    # _reconstruct_fsm() Tests
    # =============================================================================

    def test_reconstruct_fsm_success(
        self,
        command_handler: BillingCommandHandler,
        mock_event_store: Mock,
        user_id: uuid.UUID,
        sample_events: List[BillingEvent],
    ):
        """Test successful FSM reconstruction from events."""
        mock_event_store.get_events_for_user.return_value = sample_events

        with patch(
            "src.accounting.billing_command_handlers.BillingStateMachine"
        ) as MockFSM:
            mock_fsm = Mock()
            MockFSM.return_value = mock_fsm

            # Execute
            result = command_handler._reconstruct_fsm(user_id)  # type: ignore

            # Verify call sequence
            mock_event_store.get_events_for_user.assert_called_once_with(user_id)
            MockFSM.assert_called_once_with(user_id=user_id)
            mock_fsm.apply_events.assert_called_once_with(sample_events)
            assert result == mock_fsm

    def test_reconstruct_fsm_event_retrieval_error(
        self,
        command_handler: BillingCommandHandler,
        mock_event_store: Mock,
        user_id: uuid.UUID,
    ):
        """Test FSM reconstruction with event retrieval failure."""
        mock_event_store.get_events_for_user.side_effect = Exception("Database error")

        with pytest.raises(BillingCommandError, match="Failed to reconstruct FSM"):
            command_handler._reconstruct_fsm(user_id)  # type: ignore

    # =============================================================================
    # _update_account_details() Tests
    # =============================================================================

    def test_update_account_details_success(
        self,
        command_handler: BillingCommandHandler,
        user_id: uuid.UUID,
        session: Session,
    ):
        """Test successful denormalized account details update."""
        # Create account details in database
        account_details = UserAccountDetails(
            user_id=user_id,
            status=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            balance_cents=1000,
            monthly_credits_used=0,
            monthly_credits_total=500,
        )
        session.add(account_details)
        session.commit()

        # Mock FSM reconstruction
        with patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct:
            mock_fsm = Mock()
            mock_account_status = AccountStatusResponse(
                state=UserAccountStatus.METERED_BILLING,
                usage_balance_cents=800,
                usage_balance_dollars=8.0,
                monthly_credits_cents=300,
                monthly_credits_dollars=3.0,
                has_active_subscription=True,
                is_suspended=False,
                is_closed=False,
                has_usage_balance=True,
                subscription_only=False,
                using_metered_billing=True,
                no_subscription=False,
            )
            mock_fsm.get_account_status.return_value = mock_account_status
            mock_fsm.usage_balance = 800
            mock_fsm.monthly_credits_used = 200
            mock_fsm.monthly_credits_cents = 500
            mock_reconstruct.return_value = mock_fsm

            # Execute
            command_handler._update_account_details(user_id)  # type: ignore

            # Verify account details were updated
            session.refresh(account_details)
            assert account_details.status == UserAccountStatus.METERED_BILLING
            assert account_details.balance_cents == 800
            assert account_details.monthly_credits_used == 200
            assert account_details.monthly_credits_total == 500

    def test_update_account_details_missing_account(
        self,
        command_handler: BillingCommandHandler,
        user_id: uuid.UUID,
        caplog: pytest.LogCaptureFixture,
    ):
        """Test update with missing account details (warning logged)."""
        # Don't create account details in database

        with patch.object(command_handler, "_reconstruct_fsm"):
            # Execute
            command_handler._update_account_details(user_id)  # type: ignore

            # Should log warning
            assert "No account details found" in caplog.text
            assert str(user_id) in caplog.text

    def test_update_account_details_database_error(
        self,
        command_handler: BillingCommandHandler,
        user_id: uuid.UUID,
        session: Session,
        sample_events: List[BillingEvent],
        caplog: pytest.LogCaptureFixture,
    ):
        """Test update with database error (logged, not failed)."""
        # Create account details
        account_details = UserAccountDetails(
            user_id=user_id,
            status=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            monthly_credits_used=0,
            monthly_credits_total=500,
            balance_cents=0,
        )
        session.add(account_details)
        session.commit()

        # Mock FSM reconstruction to fail
        with patch.object(command_handler, "_reconstruct_fsm") as mock_reconstruct:
            mock_reconstruct.side_effect = Exception("Database connection lost")

            # Should not raise exception, just log error
            command_handler._update_account_details(user_id)  # type: ignore

            # Should log error
            assert "Failed to update account details" in caplog.text
            assert str(user_id) in caplog.text
