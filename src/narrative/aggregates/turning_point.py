"""TurningPoint aggregate for workspace turning point management.

This module contains the TurningPoint aggregate that encapsulates
business logic for creating turning points from domain events.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.db import Base
from src.strategic_planning.models import DomainEvent

if TYPE_CHECKING:
    from src.models import Initiative, Task, Workspace
    from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme


class Significance(str, Enum):
    """Significance level enumeration."""

    MINOR = "MINOR"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    CLIMACTIC = "CLIMACTIC"


class TurningPoint(Base):
    """TurningPoint aggregate for workspace turning point lifecycle.

    This aggregate encapsulates the business logic for creating turning points
    from domain events. Turning points provide narrative framing for significant
    domain events and do not emit domain events themselves (they are created
    after domain events occur).

    Attributes:
        id: Unique identifier for the turning point
        identifier: Human-readable identifier (e.g., "TP-2003")
        user_id: Foreign key to user (for RLS)
        workspace_id: Foreign key to workspace
        domain_event_id: Foreign key to domain event (one-to-one, unique)
        narrative_description: Human-readable "what happened" summary
        significance: Significance level (enum)
        story_arc_id: Optional foreign key to roadmap theme (story arc)
        initiative_id: Optional foreign key to initiative
        task_id: Optional foreign key to task
        created_at: Timestamp when turning point was created
        workspace: Relationship to Workspace entity
        domain_event: Relationship to DomainEvent entity
        story_arc: Relationship to RoadmapTheme entity
        initiative: Relationship to Initiative entity
        task: Relationship to Task entity
    """

    __tablename__ = "turning_points"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "identifier",
            name="uq_turning_points_workspace_id_identifier",
        ),
        UniqueConstraint(
            "domain_event_id",
            name="uq_turning_points_domain_event_id",
        ),
        {"schema": "dev"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    identifier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("private.users.id", ondelete="CASCADE"),
        nullable=False,
        server_default=text("private.get_user_id_from_jwt()"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.workspace.id", ondelete="CASCADE"),
        nullable=False,
    )

    domain_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.domain_events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    narrative_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    significance: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    story_arc_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.roadmap_themes.id", ondelete="SET NULL"),
        nullable=True,
    )

    initiative_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.initiative.id", ondelete="SET NULL"),
        nullable=True,
    )

    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.task.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="turning_points",
    )

    domain_event: Mapped["DomainEvent"] = relationship(
        "DomainEvent",
    )

    story_arc: Mapped["RoadmapTheme | None"] = relationship(
        "RoadmapTheme",
    )

    initiative: Mapped["Initiative | None"] = relationship(
        "Initiative",
    )

    task: Mapped["Task | None"] = relationship(
        "Task",
    )

    @staticmethod
    def create_from_event(
        domain_event: "DomainEvent",
        narrative_description: str,
        significance: Significance,
        story_arc_id: uuid.UUID | None,
        initiative_id: uuid.UUID | None,
        task_id: uuid.UUID | None,
        session: Session,
    ) -> "TurningPoint":
        """Create a turning point from a domain event.

        This factory method extracts workspace_id from the domain event payload,
        creates a fully-initialized turning point linking to the domain event,
        and persists it. Note: This does NOT emit a domain event (turning points
        are created after domain events occur).

        Args:
            domain_event: The domain event to link to
            narrative_description: Human-readable "what happened" summary
            significance: Significance level (enum)
            story_arc_id: Optional UUID of story arc
            initiative_id: Optional UUID of initiative
            task_id: Optional UUID of task
            session: Database session for persistence

        Returns:
            The created and persisted TurningPoint with ID assigned

        Example:
            >>> turning_point = TurningPoint.create_from_event(
            ...     domain_event=event,
            ...     narrative_description="Sarah completed the MCP command task!",
            ...     significance=Significance.MODERATE,
            ...     story_arc_id=arc.id,
            ...     initiative_id=initiative.id,
            ...     task_id=task.id,
            ...     session=session
            ... )
        """
        workspace_id_str = domain_event.payload.get("workspace_id")
        if not workspace_id_str:
            raise ValueError("Domain event payload must contain workspace_id")

        workspace_id = uuid.UUID(workspace_id_str)

        turning_point = TurningPoint(
            workspace_id=workspace_id,
            user_id=domain_event.user_id,
            domain_event_id=domain_event.id,
            narrative_description=narrative_description,
            significance=significance.value,
            story_arc_id=story_arc_id,
            initiative_id=initiative_id,
            task_id=task_id,
        )

        session.add(turning_point)
        session.flush()

        return turning_point
