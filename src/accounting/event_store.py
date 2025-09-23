"""
Event Store for Billing Events.

This module provides the EventStore class for persisting and retrieving
billing events in an append-only, event-sourced architecture.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Type

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .billing_events import BillingEvent, deserialize_event, serialize_event
from .models import BillingEventRecord

logger = logging.getLogger(__name__)


class EventStoreError(Exception):
    """Base exception for event store operations."""

    pass


class OptimisticConcurrencyError(EventStoreError):
    """Raised when optimistic concurrency check fails."""

    pass


class EventStore:
    """
    Event Store for billing events with optimistic concurrency control.

    This store provides append-only persistence of billing events with
    strong consistency guarantees and replay capabilities.
    """

    def __init__(self, db: Session):
        """
        Initialize event store with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def save_events(
        self, user_id: uuid.UUID, events: List[BillingEvent], expected_version: int
    ) -> None:
        """
        Save events atomically with optimistic concurrency control.

        This method ensures that events are saved in order and that
        concurrent modifications are detected and rejected.

        Args:
            user_id: User ID these events belong to
            events: List of events to save (in order)
            expected_version: Expected current version for optimistic locking

        Raises:
            OptimisticConcurrencyError: If expected_version doesn't match current version
            EventStoreError: If save operation fails
        """
        if not events:
            return

        try:
            # Check current version for optimistic concurrency control
            current_version = self.get_user_version(user_id)
            if current_version != expected_version:
                raise OptimisticConcurrencyError(
                    f"Expected version {expected_version} but current version is {current_version}"
                )

            # Create event records
            event_records = []
            for i, event in enumerate(events):
                # Ensure event belongs to the correct user
                if event.user_id != user_id:
                    raise EventStoreError(
                        f"Event {event.event_id} has user_id {event.user_id} but expected {user_id}"
                    )

                event_type, event_data = serialize_event(event)

                record = BillingEventRecord(
                    id=event.event_id,
                    user_id=user_id,
                    event_type=event_type,
                    event_data=event_data,
                    version=expected_version + i + 1,
                    created_at=event.created_at,
                )
                event_records.append(record)

            # Save all records in a batch
            self.db.add_all(event_records)
            self.db.commit()

            logger.info(
                f"Saved {len(events)} events for user {user_id}, "
                f"new version: {expected_version + len(events)}"
            )

        except IntegrityError as e:
            self.db.rollback()
            # Check if this is a version conflict
            if "unique constraint" in str(e).lower() and "version" in str(e).lower():
                raise OptimisticConcurrencyError(
                    f"Version conflict saving events for user {user_id}"
                ) from e
            else:
                raise EventStoreError(f"Database error saving events: {e}") from e

        except Exception as e:
            self.db.rollback()
            raise EventStoreError(f"Unexpected error saving events: {e}") from e

    def get_events_for_user(
        self,
        user_id: uuid.UUID,
        from_version: int = 0,
        to_version: Optional[int] = None,
    ) -> List[BillingEvent]:
        """
        Get all events for a user from a specific version range.

        Args:
            user_id: User ID to get events for
            from_version: Starting version (inclusive), defaults to 0
            to_version: Ending version (inclusive), defaults to latest

        Returns:
            List of events ordered by version
        """
        try:
            query = (
                self.db.query(BillingEventRecord)
                .filter(BillingEventRecord.user_id == user_id)
                .filter(BillingEventRecord.version > from_version)
            )

            if to_version is not None:
                query = query.filter(BillingEventRecord.version <= to_version)

            records = query.order_by(BillingEventRecord.version.asc()).all()

            events = []
            for record in records:
                try:
                    event = deserialize_event(record.event_type, record.event_data)
                    events.append(event)
                except Exception as e:
                    logger.error(
                        f"Failed to deserialize event {record.id} for user {user_id}: {e}"
                    )
                    # Skip corrupted events but continue processing
                    continue

            logger.debug(f"Retrieved {len(events)} events for user {user_id}")
            return events

        except Exception as e:
            raise EventStoreError(
                f"Error retrieving events for user {user_id}: {e}"
            ) from e

    def get_user_version(self, user_id: uuid.UUID) -> int:
        """
        Get the current event version for a user.

        The version represents the number of events that have been
        saved for this user. Version 0 means no events.

        Args:
            user_id: User ID to check version for

        Returns:
            Current version (0 if no events exist)
        """
        try:
            max_version = (
                self.db.query(BillingEventRecord.version)
                .filter(BillingEventRecord.user_id == user_id)
                .order_by(BillingEventRecord.version.desc())
                .first()
            )

            return max_version[0] if max_version else 0

        except Exception as e:
            raise EventStoreError(
                f"Error getting version for user {user_id}: {e}"
            ) from e

    def get_events_since(
        self, user_id: uuid.UUID, since: datetime
    ) -> List[BillingEvent]:
        """
        Get all events for a user since a specific timestamp.

        Args:
            user_id: User ID to get events for
            since: Timestamp to get events after

        Returns:
            List of events ordered by created_at
        """
        try:
            records = (
                self.db.query(BillingEventRecord)
                .filter(BillingEventRecord.user_id == user_id)
                .filter(BillingEventRecord.created_at > since)
                .order_by(BillingEventRecord.created_at.asc())
                .all()
            )

            events = []
            for record in records:
                try:
                    event = deserialize_event(record.event_type, record.event_data)
                    events.append(event)
                except Exception as e:
                    logger.error(
                        f"Failed to deserialize event {record.id} for user {user_id}: {e}"
                    )
                    continue

            return events

        except Exception as e:
            raise EventStoreError(
                f"Error retrieving events since {since} for user {user_id}: {e}"
            ) from e

    def get_event_count_for_user(self, user_id: uuid.UUID) -> int:
        """
        Get the total number of events for a user.

        Args:
            user_id: User ID to count events for

        Returns:
            Total number of events
        """
        try:
            count = (
                self.db.query(BillingEventRecord)
                .filter(BillingEventRecord.user_id == user_id)
                .count()
            )

            return count

        except Exception as e:
            raise EventStoreError(
                f"Error counting events for user {user_id}: {e}"
            ) from e

    def has_events_for_user(self, user_id: uuid.UUID) -> bool:
        """
        Check if any events exist for a user.

        Args:
            user_id: User ID to check

        Returns:
            True if events exist, False otherwise
        """
        try:
            exists = (
                self.db.query(BillingEventRecord.id)
                .filter(BillingEventRecord.user_id == user_id)
                .first()
                is not None
            )

            return exists

        except Exception as e:
            raise EventStoreError(
                f"Error checking events for user {user_id}: {e}"
            ) from e
