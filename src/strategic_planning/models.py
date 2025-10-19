"""Domain models for strategic planning.

This module contains SQLAlchemy models for strategic planning entities,
including domain events for event sourcing.
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import DateTime, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class DomainEvent(Base):
    """Domain event model for audit trail and event sourcing.

    This table stores all domain events for strategic planning operations,
    providing a complete audit trail and foundation for future read models.

    Attributes:
        id: Unique identifier for the event
        event_type: Type of event (e.g., 'VisionDraftCreated', 'StrategicPillarDefined')
        aggregate_id: ID of the aggregate that emitted this event
        occurred_at: Timestamp when the event occurred
        payload: JSON payload containing event data
    """

    __tablename__ = "domain_events"
    __table_args__ = (
        Index("ix_domain_events_aggregate_id", "aggregate_id"),
        Index("ix_domain_events_event_type", "event_type"),
        Index(
            "ix_domain_events_occurred_at",
            "occurred_at",
            postgresql_using="btree",
            postgresql_ops={"occurred_at": "DESC"},
        ),
        {"schema": "dev"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    aggregate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    payload: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
