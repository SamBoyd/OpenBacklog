"""
Tests for the Event-Sourced Billing State Machine.

This module tests the event-sourced FSM that generates domain events instead of
directly mutating state. Tests verify both event generation and event application.
All monetary amounts are in cents to avoid floating point precision issues.
"""

import uuid
from datetime import datetime
from typing import List

import pytest
from hamcrest import (
    assert_that,
    calling,
    equal_to,
    has_key,
    instance_of,
    is_,
    not_none,
    raises,
)

from src.accounting.billing_events import (
    BalanceUsageEvent,
    BillingEvent,
    CreditUsageEvent,
    StateTransitionEvent,
    SubscriptionSignupEvent,
)
from src.accounting.billing_state_machine import (
    BillingFSMInvalidTransitionError,
    BillingStateMachine,
    BillingStateMachineManager,
    UsageBreakdown,
)
from src.accounting.models import UserAccountStatus


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def fsm_new(user_id: uuid.UUID) -> BillingStateMachine:
    """Create FSM in NEW state (default)."""
    return BillingStateMachine(user_id=user_id)


@pytest.fixture
def fsm_active_subscription(user_id: uuid.UUID) -> BillingStateMachine:
    """Create FSM in ACTIVE_SUBSCRIPTION state."""
    fsm = BillingStateMachine(user_id=user_id)
    events = fsm.signup_subscription()
    fsm.apply_events(events)
    assert_that(fsm.state, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION))
    return fsm


@pytest.fixture
def fsm_no_subscription(user_id: uuid.UUID) -> BillingStateMachine:
    """Create FSM in NO_SUBSCRIPTION state."""
    fsm = BillingStateMachine(user_id=user_id)
    # First signup, then cancel
    signup_events = fsm.signup_subscription()
    fsm.apply_events(signup_events)
    cancel_events = fsm.cancel_subscription()
    fsm.apply_events(cancel_events)
    assert_that(fsm.state, equal_to(UserAccountStatus.NO_SUBSCRIPTION))
    return fsm


@pytest.fixture
def fsm_metered_billing(user_id: uuid.UUID) -> BillingStateMachine:
    """Create FSM in METERED_BILLING state with positive balance of 900cents and 0 monthly credits."""
    fsm = BillingStateMachine(user_id=user_id)
    # Signup, then add balance, then use credits to transition to metered
    signup_events = fsm.signup_subscription()
    fsm.apply_events(signup_events)
    topup_events = fsm.topup_usage_balance(1000, "test_topup")
    fsm.apply_events(topup_events)
    # Use more than available credits to transition to metered
    usage_events = fsm.record_usage(800, "test_usage")
    fsm.apply_events(usage_events)

    assert_that(fsm.state, equal_to(UserAccountStatus.METERED_BILLING))
    return fsm


@pytest.fixture
def fsm_suspended(user_id: uuid.UUID) -> BillingStateMachine:
    """Create FSM in SUSPENDED state."""
    fsm = BillingStateMachine(user_id=user_id)
    # Signup, then use all credits and more to get suspended
    signup_events = fsm.signup_subscription()
    fsm.apply_events(signup_events)
    # Use more than available credits to get suspended
    usage_events = fsm.record_usage(700, "test_usage")
    fsm.apply_events(usage_events)

    assert_that(fsm.state, equal_to(UserAccountStatus.SUSPENDED))
    return fsm


@pytest.fixture
def fsm_closed(user_id: uuid.UUID) -> BillingStateMachine:
    """Create FSM in CLOSED state."""
    fsm = BillingStateMachine(user_id=user_id)
    chargeback_events = fsm.detect_chargeback()
    fsm.apply_events(chargeback_events)

    assert_that(fsm.state, equal_to(UserAccountStatus.CLOSED))
    return fsm


class TestBillingStateMachineInitialization:
    """Tests for BillingStateMachine initialization and setup."""

    def test_initialization_defaults(self, fsm_new: BillingStateMachine):
        """Test default initialization values."""
        assert_that(fsm_new.user_id, not_none())
        assert_that(fsm_new.usage_balance, equal_to(0))
        assert_that(fsm_new.state, equal_to(UserAccountStatus.NEW))
        assert_that(fsm_new.monthly_credits_cents, equal_to(0))
        assert_that(fsm_new.monthly_credits_used, equal_to(0))
        assert_that(fsm_new.version, equal_to(0))

    def test_initialization_custom_values(self, user_id: uuid.UUID):
        """Test initialization with custom values."""
        fsm = BillingStateMachine(user_id=user_id, version=5)

        assert_that(fsm.user_id, equal_to(user_id))
        assert_that(fsm.usage_balance, equal_to(0))
        assert_that(fsm.state, equal_to(UserAccountStatus.NEW))
        assert_that(fsm.monthly_credits_cents, equal_to(0))
        assert_that(fsm.monthly_credits_used, equal_to(0))
        assert_that(fsm.version, equal_to(5))

    def test_event_system_setup(self, fsm_new: BillingStateMachine):
        """Verify event system methods exist."""
        # Verify event generation methods exist
        assert_that(hasattr(fsm_new, "apply_event"), is_(True))
        assert_that(hasattr(fsm_new, "apply_events"), is_(True))
        assert_that(hasattr(fsm_new, "record_usage"), is_(True))
        assert_that(hasattr(fsm_new, "signup_subscription"), is_(True))
        assert_that(hasattr(fsm_new, "detect_chargeback"), is_(True))


class TestEventApplication:
    """Tests for event application system."""

    def test_apply_single_event(self, fsm_new: BillingStateMachine):
        """Test applying a single event updates FSM state."""
        # Apply a credit usage event
        event = CreditUsageEvent(
            event_id=uuid.uuid4(),
            user_id=fsm_new.user_id,
            created_at=datetime.now(),
            amount_cents=100,
            external_id="test_123",
        )

        fsm_new.apply_event(event)

        assert_that(fsm_new.monthly_credits_used, equal_to(100))
        assert_that(fsm_new.version, equal_to(1))

    def test_apply_multiple_events(self, fsm_new: BillingStateMachine):
        """Test applying multiple events in sequence."""
        events = [
            CreditUsageEvent(
                event_id=uuid.uuid4(),
                user_id=fsm_new.user_id,
                created_at=datetime.now(),
                amount_cents=100,
                external_id="test_1",
            ),
            BalanceUsageEvent(
                event_id=uuid.uuid4(),
                user_id=fsm_new.user_id,
                created_at=datetime.now(),
                amount_cents=50,
                external_id="test_2",
            ),
        ]

        fsm_new.apply_events(events)

        assert_that(fsm_new.monthly_credits_used, equal_to(100))
        assert_that(fsm_new.usage_balance, equal_to(-50))
        assert_that(fsm_new.version, equal_to(2))


class TestSubscriptionLifecycle:
    """Tests for subscription lifecycle event generation."""

    def test_signup_subscription_from_new(self, fsm_new: BillingStateMachine):
        """Test subscription signup generates correct events."""
        # Generate signup events
        events = fsm_new.signup_subscription()

        # Verify correct events are generated
        assert_that(len(events), equal_to(2))
        assert_that(events[0], instance_of(SubscriptionSignupEvent))
        assert_that(events[1], instance_of(StateTransitionEvent))

        # Verify state transition event details
        transition_event: StateTransitionEvent = events[1]
        assert_that(transition_event.from_state, equal_to(UserAccountStatus.NEW))
        assert_that(
            transition_event.to_state, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION)
        )
        assert_that(transition_event.reason, equal_to("SIGNUP_SUBSCRIPTION"))

        # Apply events and verify final state
        fsm_new.apply_events(events)
        assert_that(fsm_new.state, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION))

    def test_signup_subscription_from_no_subscription(
        self, fsm_no_subscription: BillingStateMachine
    ):
        """Test subscription signup from NO_SUBSCRIPTION generates correct events."""
        # Generate signup events
        events: List[BillingEvent] = fsm_no_subscription.signup_subscription()

        # Verify events and state transition
        assert_that(len(events), equal_to(2))
        assert_that(events[0], instance_of(SubscriptionSignupEvent))
        assert_that(events[1], instance_of(StateTransitionEvent))

        assert_that(events[1].from_state, equal_to(UserAccountStatus.NO_SUBSCRIPTION))
        assert_that(events[1].to_state, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION))

        # Apply events and verify final state
        fsm_no_subscription.apply_events(events)
        assert_that(
            fsm_no_subscription.state, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION)
        )

    def test_signup_subscription_invalid_states(
        self,
        fsm_active_subscription: BillingStateMachine,
        fsm_metered_billing: BillingStateMachine,
        fsm_suspended: BillingStateMachine,
        fsm_closed: BillingStateMachine,
    ):
        """Test subscription signup fails from invalid states."""
        # Test with FSM fixtures in invalid states
        assert_that(
            calling(fsm_active_subscription.signup_subscription),
            raises(BillingFSMInvalidTransitionError),
        )
        assert_that(
            calling(fsm_metered_billing.signup_subscription),
            raises(BillingFSMInvalidTransitionError),
        )
        assert_that(
            calling(fsm_suspended.signup_subscription),
            raises(BillingFSMInvalidTransitionError),
        )
        assert_that(
            calling(fsm_closed.signup_subscription),
            raises(BillingFSMInvalidTransitionError),
        )

    def test_cancel_subscription_from_active(
        self, fsm_active_subscription: BillingStateMachine
    ):
        """Test subscription cancellation from ACTIVE_SUBSCRIPTION state."""
        events = fsm_active_subscription.cancel_subscription()
        fsm_active_subscription.apply_events(events)

        assert_that(
            fsm_active_subscription.state, equal_to(UserAccountStatus.NO_SUBSCRIPTION)
        )

    def test_cancel_subscription_from_suspended(
        self, fsm_suspended: BillingStateMachine
    ):
        """Test subscription cancellation from SUSPENDED state."""
        events = fsm_suspended.cancel_subscription()
        fsm_suspended.apply_events(events)

        assert_that(fsm_suspended.state, equal_to(UserAccountStatus.NO_SUBSCRIPTION))

    def test_cancel_subscription_invalid_states(
        self,
        fsm_new: BillingStateMachine,
        fsm_no_subscription: BillingStateMachine,
        fsm_metered_billing: BillingStateMachine,
        fsm_closed: BillingStateMachine,
    ):
        """Test subscription cancellation fails from invalid states."""
        assert_that(
            calling(fsm_new.cancel_subscription),
            raises(BillingFSMInvalidTransitionError),
        )
        assert_that(
            calling(fsm_no_subscription.cancel_subscription),
            raises(BillingFSMInvalidTransitionError),
        )
        assert_that(
            calling(fsm_metered_billing.cancel_subscription),
            raises(BillingFSMInvalidTransitionError),
        )
        assert_that(
            calling(fsm_closed.cancel_subscription),
            raises(BillingFSMInvalidTransitionError),
        )


class TestUsageRecording:
    """Tests for usage recording with hybrid billing model."""

    def test_record_usage_active_subscription_within_credits(
        self, fsm_active_subscription: BillingStateMachine
    ):
        """Test usage fully covered by monthly credits."""
        # Add some balance first
        topup_events = fsm_active_subscription.topup_usage_balance(100, "test_topup")
        fsm_active_subscription.apply_events(topup_events)

        events = fsm_active_subscription.record_usage(300, "test_usage")

        # State should remain ACTIVE_SUBSCRIPTION
        fsm_active_subscription.apply_events(events)
        assert_that(
            fsm_active_subscription.state,
            equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION),
        )
        assert_that(fsm_active_subscription.monthly_credits_used, equal_to(300))
        assert_that(fsm_active_subscription.usage_balance, equal_to(100))  # Unchanged

    def test_record_usage_active_subscription_exceeds_monthly_credits(
        self, fsm_active_subscription: BillingStateMachine
    ):
        """Test usage partially covered by monthly credits, remainder from balance."""
        # Add balance and use some credits first
        topup_events = fsm_active_subscription.topup_usage_balance(700, "test_topup")
        fsm_active_subscription.apply_events(topup_events)

        usage_events = fsm_active_subscription.record_usage(500, "test_usage")
        fsm_active_subscription.apply_events(usage_events)
        assert_that(
            fsm_active_subscription.state,
            equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION),
        )
        assert_that(fsm_active_subscription.monthly_credits_used, equal_to(500))
        assert_that(fsm_active_subscription.usage_balance, equal_to(700))

        events = fsm_active_subscription.record_usage(400, "test_usage")
        fsm_active_subscription.apply_events(events)

        # Should transition to METERED_BILLING (has positive balance)
        assert_that(
            fsm_active_subscription.state, equal_to(UserAccountStatus.METERED_BILLING)
        )
        assert_that(
            fsm_active_subscription.monthly_credits_used, equal_to(700)
        )  # Used all credits
        assert_that(
            fsm_active_subscription.usage_balance, equal_to(500)
        )  # 700 - 200 overflow

    def test_record_usage_active_subscription_no_remaining_credits(
        self, fsm_active_subscription: BillingStateMachine
    ):
        """Test usage when all credits are already used."""
        # Use all credits first
        usage_events = fsm_active_subscription.record_usage(700, "test_usage")
        fsm_active_subscription.apply_events(usage_events)
        # Add some balance
        topup_events = fsm_active_subscription.topup_usage_balance(300, "test_topup")
        fsm_active_subscription.apply_events(topup_events)

        events = fsm_active_subscription.record_usage(200, "test_usage")
        fsm_active_subscription.apply_events(events)

        # Should transition to METERED_BILLING
        assert_that(
            fsm_active_subscription.state, equal_to(UserAccountStatus.METERED_BILLING)
        )
        assert_that(
            fsm_active_subscription.monthly_credits_used, equal_to(700)
        )  # Unchanged
        assert_that(fsm_active_subscription.usage_balance, equal_to(100))  # 300 - 200

    def test_record_usage_active_subscription_insufficient_balance(
        self, fsm_active_subscription: BillingStateMachine
    ):
        """Test usage transitions to SUSPENDED when balance insufficient."""
        # Use some credits first
        usage_events = fsm_active_subscription.record_usage(500, "test_usage")
        fsm_active_subscription.apply_events(usage_events)
        # Add small balance
        topup_events = fsm_active_subscription.topup_usage_balance(100, "test_topup")
        fsm_active_subscription.apply_events(topup_events)

        events = fsm_active_subscription.record_usage(400, "test_usage")
        fsm_active_subscription.apply_events(events)

        # Should transition to SUSPENDED (negative balance)
        assert_that(
            fsm_active_subscription.state, equal_to(UserAccountStatus.SUSPENDED)
        )
        assert_that(fsm_active_subscription.monthly_credits_used, equal_to(700))
        assert_that(
            fsm_active_subscription.usage_balance, equal_to(-100)
        )  # 100 - 200 overflow

    def test_record_usage_from_suspended_state(
        self, fsm_suspended: BillingStateMachine
    ):
        """
        Test usage from SUSPENDED state transitions to METERED_BILLING.
        Could have since the usage tracking works on a schedule.
        """

        events = fsm_suspended.record_usage(100, "test_usage")
        fsm_suspended.apply_events(events)

        assert_that(fsm_suspended.state, equal_to(UserAccountStatus.SUSPENDED))
        assert_that(fsm_suspended.usage_balance, equal_to(-100))  # 1000 - 100

    def test_record_usage_metered_billing_sufficient_balance(
        self, fsm_metered_billing: BillingStateMachine
    ):
        """Test usage from METERED_BILLING stays in METERED_BILLING when balance remains positive."""
        events = fsm_metered_billing.record_usage(200, "test_usage")
        fsm_metered_billing.apply_events(events)

        # Should stay in METERED_BILLING since balance > 0
        assert_that(
            fsm_metered_billing.state, equal_to(UserAccountStatus.METERED_BILLING)
        )
        assert_that(fsm_metered_billing.usage_balance, equal_to(700))  # 900 - 200

    def test_record_usage_metered_billing_insufficient_balance(
        self, fsm_metered_billing: BillingStateMachine
    ):
        """Test usage from METERED_BILLING transitions to SUSPENDED."""
        events = fsm_metered_billing.record_usage(900, "test_usage")
        fsm_metered_billing.apply_events(events)

        # Should transition to SUSPENDED
        assert_that(fsm_metered_billing.state, equal_to(UserAccountStatus.SUSPENDED))
        assert_that(fsm_metered_billing.usage_balance, equal_to(0))  # 900 - 900

    def test_record_usage_invalid_amount(self, fsm_new: BillingStateMachine):
        """Test record_usage raises ValueError for invalid amounts."""
        assert_that(
            calling(fsm_new.record_usage).with_args(0, "test"),
            raises(ValueError, "Usage amount must be positive"),
        )
        assert_that(
            calling(fsm_new.record_usage).with_args(-100, "test"),
            raises(ValueError, "Usage amount must be positive"),
        )

    def test_record_usage_returns_breakdown(
        self, fsm_active_subscription: BillingStateMachine
    ):
        """Test that record_usage returns proper UsageBreakdown structure."""
        events = fsm_active_subscription.record_usage(300, "test_usage")
        fsm_active_subscription.apply_events(events)

        # Check that we have the expected state
        assert_that(fsm_active_subscription.monthly_credits_used, equal_to(300))


class TestBalanceTopup:
    """Tests for balance top-up functionality."""

    def test_topup_usage_balance_updates_balance(
        self, fsm_active_subscription: BillingStateMachine
    ):
        """Test top-up correctly updates the balance."""
        events = fsm_active_subscription.topup_usage_balance(250, "test_topup")
        fsm_active_subscription.apply_events(events)

        assert_that(fsm_active_subscription.usage_balance, equal_to(250))
        assert_that(
            fsm_active_subscription.state,
            equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION),
        )

    def test_cant_topup_from_state(
        self,
        fsm_new: BillingStateMachine,
        fsm_no_subscription: BillingStateMachine,
        fsm_closed: BillingStateMachine,
    ):
        with pytest.raises(BillingFSMInvalidTransitionError):
            fsm_new.topup_usage_balance(200, "test_topup")

        with pytest.raises(BillingFSMInvalidTransitionError):
            fsm_no_subscription.topup_usage_balance(200, "test_topup")

        with pytest.raises(BillingFSMInvalidTransitionError):
            fsm_closed.topup_usage_balance(200, "test_topup")

    def test_topup_usage_balance_from_suspended(
        self, fsm_suspended: BillingStateMachine
    ):
        """Test top-up from SUSPENDED transitions to METERED_BILLING."""
        events = fsm_suspended.topup_usage_balance(700, "test_topup")
        fsm_suspended.apply_events(events)

        assert_that(fsm_suspended.state, equal_to(UserAccountStatus.METERED_BILLING))
        assert_that(fsm_suspended.usage_balance, equal_to(700))  # 0 + 700

    def test_topup_usage_balance_other_states(
        self,
        fsm_active_subscription: BillingStateMachine,
        fsm_metered_billing: BillingStateMachine,
    ):
        """Test top-up from other states doesn't change state."""
        states = [
            (fsm_active_subscription, UserAccountStatus.ACTIVE_SUBSCRIPTION),
            (fsm_metered_billing, UserAccountStatus.METERED_BILLING),
        ]

        for fsm, expected_state in states:
            initial_balance = fsm.usage_balance
            events = fsm.topup_usage_balance(200, "test_topup")
            fsm.apply_events(events)

            assert_that(fsm.state, equal_to(expected_state))
            assert_that(fsm.usage_balance, equal_to(initial_balance + 200))

    def test_topup_usage_balance_invalid_amount(
        self, fsm_active_subscription: BillingStateMachine
    ):
        """Test top-up raises ValueError for invalid amounts."""
        assert_that(
            calling(fsm_active_subscription.topup_usage_balance).with_args(0, "test"),
            raises(ValueError, "Top-up amount must be positive"),
        )
        assert_that(
            calling(fsm_active_subscription.topup_usage_balance).with_args(
                -100, "test"
            ),
            raises(ValueError, "Top-up amount must be positive"),
        )


class TestBillingCycleManagement:
    """Tests for billing cycle management."""

    def test_start_new_billing_cycle_from_metered_billing(
        self, fsm_metered_billing: BillingStateMachine
    ):
        """Test billing cycle start from METERED_BILLING."""
        # Use some credits first
        events = fsm_metered_billing.start_new_billing_cycle()
        fsm_metered_billing.apply_events(events)

        assert_that(
            fsm_metered_billing.state, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION)
        )
        assert_that(fsm_metered_billing.monthly_credits_used, equal_to(0))

    def test_start_new_billing_cycle_from_suspended(
        self, fsm_suspended: BillingStateMachine
    ):
        """Test billing cycle start from SUSPENDED."""
        events = fsm_suspended.start_new_billing_cycle()
        fsm_suspended.apply_events(events)

        assert_that(
            fsm_suspended.state, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION)
        )
        assert_that(fsm_suspended.monthly_credits_used, equal_to(0))

    def test_start_new_billing_cycle_resets_monthly_credits(
        self, fsm_metered_billing: BillingStateMachine
    ):
        """Test billing cycle start resets monthly_credits_used."""
        # Use some credits first
        usage_events = fsm_metered_billing.record_usage(450, "test_usage")
        fsm_metered_billing.apply_events(usage_events)

        events = fsm_metered_billing.start_new_billing_cycle()
        fsm_metered_billing.apply_events(events)

        assert_that(fsm_metered_billing.monthly_credits_used, equal_to(0))

    def test_start_new_billing_cycle_from_active_subscription(
        self, fsm_active_subscription: BillingStateMachine
    ):
        """Test billing cycle start from ACTIVE_SUBSCRIPTION."""
        # Use some credits first
        usage_events = fsm_active_subscription.record_usage(300, "test_usage")
        fsm_active_subscription.apply_events(usage_events)

        assert_that(fsm_active_subscription.monthly_credits_used, equal_to(300))

        events = fsm_active_subscription.start_new_billing_cycle()
        fsm_active_subscription.apply_events(events)

        assert_that(
            fsm_active_subscription.state,
            equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION),
        )
        assert_that(fsm_active_subscription.monthly_credits_used, equal_to(0))

    def test_start_new_billing_cycle_invalid_states(
        self,
        fsm_new: BillingStateMachine,
        fsm_no_subscription: BillingStateMachine,
        fsm_closed: BillingStateMachine,
    ):
        """Test billing cycle start fails from invalid states."""
        assert_that(
            calling(fsm_new.start_new_billing_cycle),
            raises(BillingFSMInvalidTransitionError),
        )
        assert_that(
            calling(fsm_no_subscription.start_new_billing_cycle),
            raises(BillingFSMInvalidTransitionError),
        )
        assert_that(
            calling(fsm_closed.start_new_billing_cycle),
            raises(BillingFSMInvalidTransitionError),
        )


class TestRefundProcessing:
    """Tests for refund processing."""

    def test_process_balance_refund_from_metered_billing_zero_balance(
        self, fsm_metered_billing: BillingStateMachine
    ):
        """Test refund from METERED_BILLING transitions to SUSPENDED when balance becomes zero."""
        events = fsm_metered_billing.process_balance_refund(900)
        fsm_metered_billing.apply_events(events)

        assert_that(fsm_metered_billing.state, equal_to(UserAccountStatus.SUSPENDED))
        assert_that(fsm_metered_billing.usage_balance, equal_to(0))  # 100 - 100

    def test_process_balance_refund_exceeds_balance(
        self, fsm_metered_billing: BillingStateMachine
    ):
        """Test refund that exceeds balance raises error."""
        # Should fail because we can't refund more than available balance
        assert_that(
            calling(fsm_metered_billing.process_balance_refund).with_args(950),
            raises(
                BillingFSMInvalidTransitionError,
                "Cannot refund 950 cents when balance is only 900 cents",
            ),
        )

    def test_process_balance_refund_from_metered_billing_positive_balance(
        self, fsm_metered_billing: BillingStateMachine
    ):
        """Test refund from METERED_BILLING stays in same state when balance remains positive."""
        events = fsm_metered_billing.process_balance_refund(50)
        fsm_metered_billing.apply_events(events)

        # Should stay in METERED_BILLING since balance > 0 after refund
        assert_that(
            fsm_metered_billing.state, equal_to(UserAccountStatus.METERED_BILLING)
        )
        assert_that(fsm_metered_billing.usage_balance, equal_to(850))  # 900 - 50

    def test_process_balance_refund_from_active_subscription(
        self,
        fsm_active_subscription: BillingStateMachine,
    ):
        """Test refund from other states doesn't change state."""
        initial_balance = fsm_active_subscription.usage_balance

        # Add some balance first
        events = fsm_active_subscription.topup_usage_balance(100, "test_topup")
        fsm_active_subscription.apply_events(events)

        events = fsm_active_subscription.process_balance_refund(100)
        fsm_active_subscription.apply_events(events)

        assert_that(
            fsm_active_subscription.state,
            equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION),
        )
        assert_that(fsm_active_subscription.usage_balance, equal_to(initial_balance))

    def test_process_balance_refund_invalid_amount(self, fsm_new: BillingStateMachine):
        """Test refund raises error for invalid amounts."""
        assert_that(
            calling(fsm_new.process_balance_refund).with_args(0),
            raises(BillingFSMInvalidTransitionError, "Refund amount must be positive"),
        )
        assert_that(
            calling(fsm_new.process_balance_refund).with_args(-100),
            raises(BillingFSMInvalidTransitionError, "Refund amount must be positive"),
        )

    def test_process_balance_refund_from_invalid_states(
        self,
        fsm_new: BillingStateMachine,
        fsm_no_subscription: BillingStateMachine,
        fsm_closed: BillingStateMachine,
        fsm_suspended: BillingStateMachine,
    ):
        """Test refund from invalid states raises error."""
        states = [
            fsm_new,
            fsm_no_subscription,
            fsm_closed,
            fsm_suspended,
        ]

        for fsm in states:
            assert_that(
                calling(fsm.process_balance_refund).with_args(100),
                raises(BillingFSMInvalidTransitionError),
            )


class TestChargebackDetection:
    """Tests for chargeback detection."""

    def test_detect_chargeback_from_all_states(
        self,
        fsm_new: BillingStateMachine,
        fsm_active_subscription: BillingStateMachine,
        fsm_metered_billing: BillingStateMachine,
        fsm_suspended: BillingStateMachine,
        fsm_no_subscription: BillingStateMachine,
    ):
        """Test chargeback detection works from all states."""
        all_fsms = [
            fsm_new,
            fsm_active_subscription,
            fsm_metered_billing,
            fsm_suspended,
            fsm_no_subscription,
        ]

        for fsm in all_fsms:
            events = fsm.detect_chargeback()
            fsm.apply_events(events)

            assert_that(fsm.state, equal_to(UserAccountStatus.CLOSED))

    def test_detect_chargeback_final_state(self, fsm_closed: BillingStateMachine):
        """Test that CLOSED state is terminal."""
        events = fsm_closed.detect_chargeback()
        fsm_closed.apply_events(events)

        assert_that(fsm_closed.state, equal_to(UserAccountStatus.CLOSED))
        assert_that(fsm_closed.usage_balance, equal_to(0))
        assert_that(fsm_closed.monthly_credits_used, equal_to(0))


# class TestReplayMethods:
#     """Tests for FSM reconstruction replay methods."""

#     def test_replay_subscription_signup_transition(self, fsm_new: BillingStateMachine):
#         """Test replay subscription signup."""
#         fsm_new.replay_subscription_signup_transition()

#         assert_that(fsm_new.state, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION))

#     def test_replay_subscription_cancel_transition(
#         self, fsm_active_subscription: BillingStateMachine
#     ):
#         """Test replay subscription cancellation."""
#         fsm_active_subscription.replay_subscription_cancel_transition()

#         assert_that(
#             fsm_active_subscription.state, equal_to(UserAccountStatus.NO_SUBSCRIPTION)
#         )

#     def test_replay_usage_transition(
#         self, fsm_active_subscription: BillingStateMachine
#     ):
#         """Test replay usage transition."""
#         fsm_active_subscription.replay_usage_transition()

#         assert_that(
#             fsm_active_subscription.state, equal_to(UserAccountStatus.METERED_BILLING)
#         )

#     def test_replay_topup_transition_from_suspended(self, fsm_suspended):
#         """Test replay top-up only works from SUSPENDED."""
#         fsm_suspended.replay_topup_transition()

#         assert_that(fsm_suspended.state, equal_to(UserAccountStatus.METERED_BILLING))

#     def test_replay_topup_transition_other_states(
#         self, fsm_new, fsm_no_subscription, fsm_closed
#     ):
#         """Test replay top-up is no-op from other states."""
#         states_that_should_fail = [
#             fsm_new,
#             fsm_no_subscription,
#             fsm_closed,
#             fsm_active_subscription,
#             fsm_metered_billing,
#         ]

#         for fsm in states_that_should_fail:
#             with pytest.raises(BillingFSMInvalidTransitionError):
#                 fsm.replay_topup_transition()

#     def test_replay_billing_cycle_start_valid_states(
#         self, fsm_metered_billing: BillingStateMachine
#     ):
#         """Test replay billing cycle start from valid states."""
#         # Use some credits first
#         usage_events = fsm_metered_billing.record_usage(400, "test_usage")
#         fsm_metered_billing.apply_events(usage_events)

#         fsm_metered_billing.replay_billing_cycle_start_transition()

#         assert_that(
#             fsm_metered_billing.state, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION)
#         )

#     def test_replay_billing_cycle_start_invalid_states(
#         self, fsm_new, fsm_active_subscription, fsm_no_subscription, fsm_closed
#     ):
#         """Test replay billing cycle start is no-op from invalid states."""
#         invalid_states = [
#             fsm_new,
#             fsm_active_subscription,
#             fsm_no_subscription,
#             fsm_closed,
#         ]

#         for fsm in invalid_states:
#             initial_state = fsm.state

#             with pytest.raises(BillingFSMInvalidTransitionError):
#                 fsm.replay_billing_cycle_start_transition()

#             assert_that(fsm.state, equal_to(initial_state))

#     def test_replay_refund_transition_from_metered_billing(
#         self, fsm_metered_billing: BillingStateMachine
#     ):
#         """Test replay refund only works from METERED_BILLING."""
#         fsm_metered_billing.replay_refund_transition()

#         assert_that(fsm_metered_billing.state, equal_to(UserAccountStatus.SUSPENDED))

#     def test_replay_refund_transition_other_states(
#         self,
#         fsm_new,
#         fsm_active_subscription,
#         fsm_suspended,
#         fsm_no_subscription,
#         fsm_closed,
#     ):
#         """Test replay refund is no-op from other states."""
#         states = [
#             fsm_new,
#             fsm_active_subscription,
#             fsm_suspended,
#             fsm_no_subscription,
#             fsm_closed,
#         ]

#         for fsm in states:
#             initial_state = fsm.state

#             fsm.replay_refund_transition()

#             assert_that(fsm.state, equal_to(initial_state))

#     def test_replay_chargeback_transition(
#         self, fsm_active_subscription: BillingStateMachine
#     ):
#         """Test replay chargeback detection."""
#         fsm_active_subscription.replay_chargeback_transition()

#         assert_that(fsm_active_subscription.state, equal_to(UserAccountStatus.CLOSED))


class TestAccountStatus:
    """Tests for account status reporting."""

    def test_get_account_status_remaining_credits_calculation(
        self, fsm_active_subscription: BillingStateMachine
    ):
        """Test that monthly_credits_cents shows remaining, not total."""
        # Use some credits first
        usage_events = fsm_active_subscription.record_usage(200, "test_usage")
        fsm_active_subscription.apply_events(usage_events)

        status = fsm_active_subscription.get_account_status()

        assert_that(status.monthly_credits_cents, equal_to(200))
        assert_that(status.monthly_credits_dollars, equal_to(2.0))

    def test_get_account_status_computed_properties(
        self,
        fsm_active_subscription: BillingStateMachine,
        fsm_suspended: BillingStateMachine,
        fsm_no_subscription: BillingStateMachine,
    ):
        """Test computed boolean properties for different states."""
        # Test ACTIVE_SUBSCRIPTION
        status_active = fsm_active_subscription.get_account_status()

        assert_that(status_active.has_active_subscription, is_(True))
        assert_that(status_active.is_suspended, is_(False))
        assert_that(status_active.is_closed, is_(False))
        assert_that(status_active.has_usage_balance, is_(False))
        assert_that(status_active.subscription_only, is_(True))
        assert_that(status_active.using_metered_billing, is_(False))
        assert_that(status_active.no_subscription, is_(False))

        # Test SUSPENDED
        status_suspended = fsm_suspended.get_account_status()

        assert_that(status_suspended.has_active_subscription, is_(True))
        assert_that(status_suspended.is_suspended, is_(True))
        assert_that(status_suspended.is_closed, is_(False))

        # Test NO_SUBSCRIPTION
        status_no_sub = fsm_no_subscription.get_account_status()

        assert_that(status_no_sub.has_active_subscription, is_(False))
        assert_that(status_no_sub.no_subscription, is_(True))

    def test_get_account_status_balance_conversions(
        self, fsm_active_subscription: BillingStateMachine
    ):
        """Test cents to dollars conversion."""
        # Add balance
        topup_events = fsm_active_subscription.topup_usage_balance(12345, "test_topup")
        fsm_active_subscription.apply_events(topup_events)

        status = fsm_active_subscription.get_account_status()

        assert_that(status.usage_balance_cents, equal_to(12345))
        assert_that(status.usage_balance_dollars, equal_to(123.45))

    def test_get_account_status_different_states(
        self, fsm_metered_billing, fsm_closed: BillingStateMachine
    ):
        """Test computed properties vary correctly by state."""
        # Test METERED_BILLING with balance
        status_metered = fsm_metered_billing.get_account_status()

        assert_that(status_metered.has_active_subscription, is_(True))
        assert_that(status_metered.using_metered_billing, is_(True))
        assert_that(status_metered.has_usage_balance, is_(True))
        assert_that(status_metered.subscription_only, is_(False))

        # Test CLOSED
        status_closed = fsm_closed.get_account_status()

        assert_that(status_closed.is_closed, is_(True))
        assert_that(status_closed.has_active_subscription, is_(False))


class TestUsageBreakdown:
    """Tests for UsageBreakdown dataclass."""

    def test_usage_breakdown_dataclass_structure(self):
        """Test UsageBreakdown has correct structure."""
        breakdown = UsageBreakdown(total_amount=700, credits_used=300, balance_used=200)

        assert_that(breakdown.total_amount, equal_to(700))
        assert_that(breakdown.credits_used, equal_to(300))
        assert_that(breakdown.balance_used, equal_to(200))

    def test_usage_breakdown_values_sum_to_total(self):
        """Test credits_used + balance_used = total_amount."""
        breakdown = UsageBreakdown(total_amount=750, credits_used=450, balance_used=300)

        total = breakdown.credits_used + breakdown.balance_used
        assert_that(total, equal_to(breakdown.total_amount))


class TestBillingStateMachineManager:
    """Tests for BillingStateMachineManager."""

    def test_manager_create_account_default_credits(self, user_id: uuid.UUID):
        """Test manager creates account with default monthly credits."""
        manager = BillingStateMachineManager()

        account = manager.create_account("test-account", user_id)

        assert_that(account.monthly_credits_cents, equal_to(0))
        assert_that(account.state, equal_to(UserAccountStatus.NEW))
        assert_that(account.usage_balance, equal_to(0))

    def test_manager_create_account_duplicate_id(self, user_id: uuid.UUID):
        """Test manager raises ValueError for duplicate account ID."""
        manager = BillingStateMachineManager()
        manager.create_account("test-account", user_id)

        assert_that(
            calling(manager.create_account).with_args("test-account", user_id),
            raises(ValueError, "Account test-account already exists"),
        )

    def test_manager_get_account_exists(self, user_id: uuid.UUID):
        """Test manager returns existing account."""
        manager = BillingStateMachineManager()
        created_account = manager.create_account("test-account", user_id)

        retrieved_account = manager.get_account("test-account")

        assert_that(retrieved_account, equal_to(created_account))

    def test_manager_get_account_not_exists(self):
        """Test manager returns None for non-existent account."""
        manager = BillingStateMachineManager()

        account = manager.get_account("non-existent")

        assert_that(account, is_(None))

    def test_manager_close_account_chargeback(self, user_id: uuid.UUID):
        """Test manager closes account via chargeback detection."""
        manager = BillingStateMachineManager()
        account = manager.create_account("test-account", user_id)
        # Signup first
        signup_events = account.signup_subscription()
        account.apply_events(signup_events)

        manager.close_account("test-account", reason="chargeback")

        assert_that(account.state, equal_to(UserAccountStatus.CLOSED))

    def test_manager_close_account_manual(self, user_id: uuid.UUID):
        """Test manager closes account manually."""
        manager = BillingStateMachineManager()
        account = manager.create_account("test-account", user_id)
        # Signup first
        signup_events = account.signup_subscription()
        account.apply_events(signup_events)

        manager.close_account("test-account", reason="manual_closure")

        assert_that(account.state, equal_to(UserAccountStatus.CLOSED))

    def test_manager_get_all_accounts_status(self, user_id: uuid.UUID):
        """Test manager returns status for all accounts."""
        manager = BillingStateMachineManager()
        manager.create_account("account1", user_id)
        manager.create_account("account2", user_id)

        all_status = manager.get_all_accounts_status()

        assert_that(all_status, has_key("account1"))
        assert_that(all_status, has_key("account2"))
        assert_that(all_status["account1"].state, equal_to(UserAccountStatus.NEW))
        assert_that(all_status["account2"].state, equal_to(UserAccountStatus.NEW))
