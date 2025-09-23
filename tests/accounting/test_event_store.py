"""
Tests for the EventStore class.

This module tests event persistence, retrieval, and optimistic concurrency
control for the event-sourced billing architecture.
"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from src.accounting.billing_events import (
    BalanceUsageEvent,
    CreditUsageEvent,
    MonthlyCreditsResetEvent,
    StateTransitionEvent,
)
from src.accounting.event_store import (
    EventStore,
    EventStoreError,
    OptimisticConcurrencyError,
)
from src.accounting.models import UserAccountStatus


class TestEventStore:
    """Test EventStore functionality."""

    def test_save_and_retrieve_events(self, session: Session, user):
        """Test basic event saving and retrieval."""
        event_store = EventStore(session)
        user_id = user.id

        # Create test events
        events = [
            CreditUsageEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                amount_cents=100,
                external_id="test_1",
            ),
            BalanceUsageEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now() + timedelta(seconds=1),
                amount_cents=50,
                external_id="test_2",
            ),
        ]

        # Save events
        event_store.save_events(user_id, events, expected_version=0)

        # Retrieve events
        retrieved_events = event_store.get_events_for_user(user_id)

        assert len(retrieved_events) == 2
        assert isinstance(retrieved_events[0], CreditUsageEvent)
        assert isinstance(retrieved_events[1], BalanceUsageEvent)
        assert retrieved_events[0].amount_cents == 100
        assert retrieved_events[1].amount_cents == 50

    def test_optimistic_concurrency_control(self, session: Session, user):
        """Test that optimistic concurrency control prevents version conflicts."""
        event_store = EventStore(session)
        user_id = user.id

        # Save first event
        event1 = CreditUsageEvent(
            event_id=uuid.uuid4(),
            user_id=user_id,
            created_at=datetime.now(),
            amount_cents=100,
            external_id="test_1",
        )
        event_store.save_events(user_id, [event1], expected_version=0)

        # Verify version is now 1
        assert event_store.get_user_version(user_id) == 1

        # Try to save with wrong expected version
        event2 = CreditUsageEvent(
            event_id=uuid.uuid4(),
            user_id=user_id,
            created_at=datetime.now(),
            amount_cents=200,
            external_id="test_2",
        )

        # The OptimisticConcurrencyError should be caught and re-raised as EventStoreError
        with pytest.raises((OptimisticConcurrencyError, EventStoreError)):
            event_store.save_events(
                user_id, [event2], expected_version=0
            )  # Wrong version

        # Save with correct expected version should work
        event_store.save_events(user_id, [event2], expected_version=1)
        assert event_store.get_user_version(user_id) == 2

    def test_get_user_version_no_events(self, session: Session, user):
        """Test getting version for user with no events returns 0."""
        event_store = EventStore(session)
        user_id = user.id

        version = event_store.get_user_version(user_id)
        assert version == 0

    def test_get_events_with_version_range(self, session: Session, user):
        """Test retrieving events within a specific version range."""
        event_store = EventStore(session)
        user_id = user.id

        # Save multiple events
        events = [
            CreditUsageEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now() + timedelta(seconds=i),
                amount_cents=100 + i,
                external_id=f"test_{i}",
            )
            for i in range(5)
        ]

        event_store.save_events(user_id, events, expected_version=0)

        # Get events from version 2 to 4
        partial_events = event_store.get_events_for_user(
            user_id, from_version=2, to_version=4
        )

        assert len(partial_events) == 2  # Events at version 3 and 4
        assert partial_events[0].amount_cents == 102
        assert partial_events[1].amount_cents == 103

    def test_get_events_since_timestamp(self, session: Session, user):
        """Test retrieving events since a specific timestamp."""
        event_store = EventStore(session)
        user_id = user.id

        base_time = datetime.now()

        # Save events with different timestamps
        events = [
            CreditUsageEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=base_time + timedelta(seconds=i),
                amount_cents=100 + i,
                external_id=f"test_{i}",
            )
            for i in range(5)
        ]

        event_store.save_events(user_id, events, expected_version=0)

        # Get events since base_time + 2 seconds (should get events at seconds 3, 4)
        since_time = base_time + timedelta(seconds=2)
        recent_events = event_store.get_events_since(user_id, since_time)

        assert (
            len(recent_events) == 2
        )  # Events at seconds 3, 4 (since_time uses > not >=)
        assert all(event.created_at > since_time for event in recent_events)

    def test_has_events_for_user(self, session: Session, user, other_user):
        """Test checking if events exist for a user."""
        event_store = EventStore(session)
        user_id = user.id
        other_user_id = other_user.id

        # Initially no events
        assert not event_store.has_events_for_user(user_id)
        assert not event_store.has_events_for_user(other_user_id)

        # Save event for one user
        event = CreditUsageEvent(
            event_id=uuid.uuid4(),
            user_id=user_id,
            created_at=datetime.now(),
            amount_cents=100,
            external_id="test",
        )
        event_store.save_events(user_id, [event], expected_version=0)

        # Now only first user has events
        assert event_store.has_events_for_user(user_id)
        assert not event_store.has_events_for_user(other_user_id)

    def test_get_event_count_for_user(self, session: Session, user):
        """Test counting events for a user."""
        event_store = EventStore(session)
        user_id = user.id

        # Initially no events
        assert event_store.get_event_count_for_user(user_id) == 0

        # Save some events
        events = [
            CreditUsageEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now() + timedelta(seconds=i),
                amount_cents=100,
                external_id=f"test_{i}",
            )
            for i in range(3)
        ]

        event_store.save_events(user_id, events, expected_version=0)

        assert event_store.get_event_count_for_user(user_id) == 3

    def test_save_events_wrong_user_id(self, session: Session, user, other_user):
        """Test that events with wrong user_id are rejected."""
        event_store = EventStore(session)
        user_id = user.id
        other_user_id = other_user.id

        # Create event for different user
        event = CreditUsageEvent(
            event_id=uuid.uuid4(),
            user_id=other_user_id,  # Different user
            created_at=datetime.now(),
            amount_cents=100,
            external_id="test",
        )

        # Should raise error when trying to save with wrong user_id
        with pytest.raises(EventStoreError, match="has user_id"):
            event_store.save_events(user_id, [event], expected_version=0)

    def test_save_empty_event_list(self, session: Session, user):
        """Test that saving empty event list is a no-op."""
        event_store = EventStore(session)
        user_id = user.id

        # Save empty list
        event_store.save_events(user_id, [], expected_version=0)

        # Should still have no events
        assert event_store.get_user_version(user_id) == 0
        assert len(event_store.get_events_for_user(user_id)) == 0

    def test_version_increments_correctly(self, session: Session, user):
        """Test that versions increment correctly with multiple saves."""
        event_store = EventStore(session)
        user_id = user.id

        # Save first batch
        events1 = [
            CreditUsageEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                amount_cents=100,
                external_id="test_1",
            ),
            CreditUsageEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                amount_cents=200,
                external_id="test_2",
            ),
        ]
        event_store.save_events(user_id, events1, expected_version=0)
        assert event_store.get_user_version(user_id) == 2

        # Save second batch
        events2 = [
            BalanceUsageEvent(
                event_id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(),
                amount_cents=50,
                external_id="test_3",
            ),
        ]
        event_store.save_events(user_id, events2, expected_version=2)
        assert event_store.get_user_version(user_id) == 3

        # Verify all events are retrievable
        all_events = event_store.get_events_for_user(user_id)
        assert len(all_events) == 3

    def test_complex_event_serialization(self, session: Session, user):
        """Test that complex events with enums serialize correctly."""
        event_store = EventStore(session)
        user_id = user.id

        # Create state transition event with enums
        event = StateTransitionEvent(
            event_id=uuid.uuid4(),
            user_id=user_id,
            created_at=datetime.now(),
            from_state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            to_state=UserAccountStatus.METERED_BILLING,
            reason="USAGE_RECORDED",
        )

        event_store.save_events(user_id, [event], expected_version=0)

        # Retrieve and verify enum deserialization
        retrieved_events = event_store.get_events_for_user(user_id)
        retrieved_event = retrieved_events[0]

        assert isinstance(retrieved_event, StateTransitionEvent)
        assert retrieved_event.from_state == UserAccountStatus.ACTIVE_SUBSCRIPTION
        assert retrieved_event.to_state == UserAccountStatus.METERED_BILLING
        assert retrieved_event.reason == "USAGE_RECORDED"
