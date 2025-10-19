"""Event publishing service for strategic planning domain events.

This service provides a centralized mechanism for persisting domain events
to the database and emitting structured logs for searchability.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from src.strategic_planning.models import DomainEvent

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes domain events to database and structured logs.

    This service persists events to the domain_events table and emits
    structured logs with searchable fields (event_type, aggregate_id, workspace_id).

    Attributes:
        db: SQLAlchemy database session for persistence operations
    """

    def __init__(self, db_session: Session):
        """Initialize the event publisher with a database session.

        Args:
            db_session: SQLAlchemy database session for operations
        """
        self.db = db_session

    def publish(self, event: DomainEvent, workspace_id: Optional[str] = None) -> None:
        """Publish a domain event to database and structured logs.

        Persists the event to the domain_events table and emits a structured
        log entry with searchable fields for monitoring and debugging.

        Args:
            event: DomainEvent instance to publish
            workspace_id: Optional workspace ID for log searchability

        Example:
            >>> event = DomainEvent(
            ...     user_id=uuid.uuid4(),
            ...     event_type="VisionDraftCreated",
            ...     aggregate_id=vision_id,
            ...     payload={"vision_text": "Build the best product"}
            ... )
            >>> publisher.publish(event, workspace_id=workspace.id)
        """
        self.db.add(event)
        self.db.flush()

        logger.info(
            f"Domain event published: {event.event_type}",
            extra={
                "event_type": event.event_type,
                "aggregate_id": str(event.aggregate_id),
                "workspace_id": workspace_id,
                "occurred_at": event.occurred_at.isoformat(),
                "event_data": event.payload,
            },
        )
