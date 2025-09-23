"""
Tests for billing events domain models.

This module tests the event serialization, deserialization, and
domain model functionality for the event-sourced billing architecture.
"""

import uuid
from datetime import datetime

import pytest

from src.accounting.billing_events import (
    EVENT_TYPE_REGISTRY,
    BalanceRefundEvent,
    BalanceTopUpEvent,
    BalanceUsageEvent,
    BillingEvent,
    ChargebackDetectedEvent,
    CreditUsageEvent,
    MonthlyCreditsResetEvent,
    StateTransitionEvent,
    SubscriptionCancelEvent,
    SubscriptionSignupEvent,
    deserialize_event,
    serialize_event,
)
from src.accounting.models import UserAccountStatus


class TestBillingEventSerialization:
    """Test event serialization and deserialization."""

    def test_credit_usage_event_serialization(self):
        """Test CreditUsageEvent can be serialized and deserialized."""
        event = CreditUsageEvent(
            event_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            created_at=datetime.now(),
            amount_cents=100,
            external_id="test_request_123",
        )

        # Serialize
        event_type, event_data = serialize_event(event)
        assert event_type == "CREDIT_USAGE"
        assert event_data["amount_cents"] == 100
        assert event_data["external_id"] == "test_request_123"

        # Deserialize
        restored_event = deserialize_event(event_type, event_data)
        assert isinstance(restored_event, CreditUsageEvent)
        assert restored_event.event_id == event.event_id
        assert restored_event.user_id == event.user_id
        assert restored_event.amount_cents == event.amount_cents
        assert restored_event.external_id == event.external_id

    def test_state_transition_event_serialization(self):
        """Test StateTransitionEvent handles enum serialization correctly."""
        event = StateTransitionEvent(
            event_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            created_at=datetime.now(),
            from_state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            to_state=UserAccountStatus.METERED_BILLING,
            reason="USAGE_RECORDED",
        )

        # Serialize
        event_type, event_data = serialize_event(event)
        assert event_type == "STATE_TRANSITION"
        assert event_data["from_state"] == "ACTIVE_SUBSCRIPTION"
        assert event_data["to_state"] == "METERED_BILLING"

        # Deserialize
        restored_event = deserialize_event(event_type, event_data)
        assert isinstance(restored_event, StateTransitionEvent)
        assert restored_event.from_state == UserAccountStatus.ACTIVE_SUBSCRIPTION
        assert restored_event.to_state == UserAccountStatus.METERED_BILLING
        assert restored_event.reason == "USAGE_RECORDED"

    def test_all_event_types_in_registry(self):
        """Test that all event types are properly registered."""
        expected_types = {
            "CREDIT_USAGE",
            "BALANCE_USAGE",
            "STATE_TRANSITION",
            "BALANCE_TOPUP",
            "MONTHLY_CREDITS_RESET",
            "BALANCE_REFUND",
            "SUBSCRIPTION_SIGNUP",
            "SUBSCRIPTION_CANCEL",
            "CHARGEBACK_DETECTED",
        }

        assert set(EVENT_TYPE_REGISTRY.keys()) == expected_types

    def test_unknown_event_type_raises_error(self):
        """Test that unknown event types raise ValueError."""
        with pytest.raises(ValueError, match="Unknown event type: UNKNOWN_EVENT"):
            deserialize_event("UNKNOWN_EVENT", {})


class TestBillingEventImmutability:
    """Test that billing events are immutable (frozen dataclasses)."""

    def test_credit_usage_event_is_immutable(self):
        """Test that CreditUsageEvent cannot be modified after creation."""
        event = CreditUsageEvent(
            event_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            created_at=datetime.now(),
            amount_cents=100,
            external_id="test",
        )

        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            event.amount_cents = 200
