"""Domain models for strategic planning.

This module contains SQLAlchemy models for strategic planning entities,
including domain events for event sourcing and association tables for
many-to-many relationships.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base

if TYPE_CHECKING:
    from src.models import Initiative, Workspace
    from src.strategic_planning.aggregates.product_vision import ProductVision
    from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar


class OutcomePillarLink(Base):
    """Association table linking product outcomes to strategic pillars.

    This table implements the many-to-many relationship between
    product outcomes and strategic pillars. One outcome can support
    multiple pillars, and one pillar can have multiple outcomes.

    Attributes:
        outcome_id: Foreign key to product_outcomes table
        pillar_id: Foreign key to strategic_pillars table
        created_at: Timestamp when the link was created
    """

    __tablename__ = "outcome_pillar_links"
    __table_args__ = ({"schema": "dev"},)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("private.get_user_id_from_jwt()"),
    )

    outcome_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.product_outcomes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    pillar_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.strategic_pillars.id", ondelete="CASCADE"),
        primary_key=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )


class ThemeOutcomeLink(Base):
    """Association table linking roadmap themes to product outcomes.

    This table implements the many-to-many relationship between
    roadmap themes and product outcomes. One theme can address
    multiple outcomes, and one outcome can be addressed by multiple themes.

    Attributes:
        theme_id: Foreign key to roadmap_themes table
        outcome_id: Foreign key to product_outcomes table
        created_at: Timestamp when the link was created
    """

    __tablename__ = "theme_outcome_links"
    __table_args__ = ({"schema": "dev"},)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("private.get_user_id_from_jwt()"),
    )

    theme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.roadmap_themes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    outcome_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.product_outcomes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )


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

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("private.get_user_id_from_jwt()"),
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
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    payload: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
