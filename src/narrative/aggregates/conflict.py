"""Conflict aggregate for workspace conflict management.

This module contains the Conflict aggregate that encapsulates
business logic for creating, updating, and resolving conflicts.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.db import Base
from src.narrative.exceptions import DomainException
from src.strategic_planning.models import DomainEvent

if TYPE_CHECKING:
    from src.initiative_management.aggregates.strategic_initiative import (
        StrategicInitiative,
    )
    from src.models import Initiative, Workspace
    from src.narrative.aggregates.hero import Hero
    from src.narrative.aggregates.villain import Villain
    from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
    from src.strategic_planning.services.event_publisher import EventPublisher


class ConflictStatus(str, Enum):
    """Conflict status enumeration."""

    OPEN = "OPEN"
    ESCALATING = "ESCALATING"
    RESOLVING = "RESOLVING"
    RESOLVED = "RESOLVED"


class Conflict(Base):
    """Conflict aggregate for workspace conflict lifecycle.

    This aggregate encapsulates the business logic for creating, updating,
    and resolving conflicts between heroes and villains. It enforces invariants
    like field length limits and valid status transitions.

    Attributes:
        id: Unique identifier for the conflict
        identifier: Human-readable identifier (e.g., "C-2003")
        user_id: Foreign key to user (for RLS)
        workspace_id: Foreign key to workspace
        hero_id: Foreign key to hero
        villain_id: Foreign key to villain
        description: Rich description of the conflict (1-2000 characters, required)
        status: Current status of the conflict (enum, default OPEN)
        story_arc_id: Optional foreign key to roadmap theme (story arc)
        resolved_at: Timestamp when conflict was resolved (nullable)
        resolved_by_initiative_id: Optional foreign key to initiative that resolved it
        created_at: Timestamp when conflict was created
        updated_at: Timestamp when conflict was last modified
        workspace: Relationship to Workspace entity
        hero: Relationship to Hero entity
        villain: Relationship to Villain entity
        story_arc: Relationship to RoadmapTheme entity
        resolved_by_initiative: Relationship to Initiative entity
    """

    __tablename__ = "conflicts"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "identifier",
            name="uq_conflicts_workspace_id_identifier",
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

    hero_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.heroes.id", ondelete="CASCADE"),
        nullable=False,
    )

    villain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.villains.id", ondelete="CASCADE"),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'OPEN'"),
    )

    story_arc_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.roadmap_themes.id", ondelete="SET NULL"),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolved_by_initiative_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.initiative.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="conflicts",
    )

    hero: Mapped["Hero"] = relationship(
        "Hero",
        back_populates="conflicts",
    )

    villain: Mapped["Villain"] = relationship(
        "Villain",
        back_populates="conflicts",
    )

    story_arc: Mapped["RoadmapTheme | None"] = relationship(
        "RoadmapTheme",
    )

    resolved_by_initiative: Mapped["Initiative | None"] = relationship(
        "Initiative",
    )

    strategic_initiatives: Mapped[List["StrategicInitiative"]] = relationship(
        "StrategicInitiative",
        secondary="dev.strategic_initiative_conflicts",
        back_populates="conflicts",
    )

    @staticmethod
    def _validate_description(description: str) -> None:
        """Validate conflict description meets character limit requirements.

        Args:
            description: The description to validate

        Raises:
            DomainException: If description is not between 1-2000 characters
        """
        if not description or len(description) < 1:
            raise DomainException("Conflict description must be at least 1 character")
        if len(description) > 2000:
            raise DomainException(
                f"Conflict description must be 2000 characters or less (got {len(description)})"
            )

    @staticmethod
    def create_conflict(
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        hero_id: uuid.UUID,
        villain_id: uuid.UUID,
        description: str,
        story_arc_id: uuid.UUID | None,
        session: Session,
        publisher: "EventPublisher",
    ) -> "Conflict":
        """Create a new conflict with business validation.

        This factory method validates inputs, validates hero and villain exist,
        creates a fully-initialized conflict with status=OPEN, persists it to get
        an ID, and emits the ConflictCreated domain event.

        Args:
            workspace_id: UUID of the workspace
            user_id: UUID of the user creating the conflict
            hero_id: UUID of the hero experiencing the conflict
            villain_id: UUID of the villain creating the conflict
            description: Conflict description (1-2000 characters, required)
            story_arc_id: Optional UUID of story arc addressing this conflict
            session: Database session for persistence
            publisher: EventPublisher instance for emitting domain events

        Returns:
            The created and persisted Conflict with ID assigned

        Raises:
            DomainException: If any field violates validation rules or hero/villain don't exist

        Example:
            >>> conflict = Conflict.create_conflict(
            ...     workspace_id=workspace.id,
            ...     user_id=user.id,
            ...     hero_id=hero.id,
            ...     villain_id=villain.id,
            ...     description="Sarah cannot access context from IDE...",
            ...     story_arc_id=None,
            ...     session=session,
            ...     publisher=publisher
            ... )
        """
        Conflict._validate_description(description)

        from src.narrative.aggregates.hero import Hero
        from src.narrative.aggregates.villain import Villain

        hero = session.query(Hero).filter(Hero.id == hero_id).first()
        if not hero:
            raise DomainException(f"Hero with id {hero_id} does not exist")

        villain = session.query(Villain).filter(Villain.id == villain_id).first()
        if not villain:
            raise DomainException(f"Villain with id {villain_id} does not exist")

        conflict = Conflict(
            workspace_id=workspace_id,
            user_id=user_id,
            hero_id=hero_id,
            villain_id=villain_id,
            description=description,
            status=ConflictStatus.OPEN.value,
            story_arc_id=story_arc_id,
        )

        session.add(conflict)
        session.flush()

        event = DomainEvent(
            user_id=user_id,
            event_type="ConflictCreated",
            aggregate_id=conflict.id,
            payload={
                "workspace_id": str(workspace_id),
                "hero_id": str(hero_id),
                "villain_id": str(villain_id),
                "description": description,
                "story_arc_id": str(story_arc_id) if story_arc_id else None,
            },
        )
        publisher.publish(event, workspace_id=str(workspace_id))

        return conflict

    def update_conflict(
        self,
        description: str,
        story_arc_id: uuid.UUID | None,
        publisher: "EventPublisher",
    ) -> None:
        """Update an existing conflict.

        This method updates the conflict's description and story_arc_id after validation
        and emits a ConflictUpdated domain event.

        Args:
            description: Updated conflict description (1-2000 characters)
            story_arc_id: Updated story arc ID (can be None to unlink)
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If description violates validation rules

        Example:
            >>> conflict.update_conflict(
            ...     description="Updated description of the conflict...",
            ...     story_arc_id=theme.id,
            ...     publisher=publisher
            ... )
        """
        Conflict._validate_description(description)

        self.description = description
        self.story_arc_id = story_arc_id
        self.updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            user_id=self.user_id,
            event_type="ConflictUpdated",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "description": description,
                "story_arc_id": str(story_arc_id) if story_arc_id else None,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))

    def mark_resolving(
        self,
        publisher: "EventPublisher",
    ) -> None:
        """Mark this conflict as being actively resolved.

        This method sets status to RESOLVING and emits a ConflictResolving domain event.

        Args:
            publisher: EventPublisher instance for emitting domain events

        Example:
            >>> conflict.mark_resolving(publisher)
        """
        self.status = ConflictStatus.RESOLVING.value
        self.updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            user_id=self.user_id,
            event_type="ConflictResolving",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "conflict_id": str(self.id),
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))

    def mark_resolved(
        self,
        resolved_by_initiative_id: uuid.UUID | None,
        publisher: "EventPublisher",
    ) -> None:
        """Mark this conflict as resolved.

        This method sets status to RESOLVED, sets resolved_at timestamp,
        optionally sets resolved_by_initiative_id, and emits a ConflictResolved domain event.

        Args:
            resolved_by_initiative_id: Optional UUID of initiative that resolved it
            publisher: EventPublisher instance for emitting domain events

        Example:
            >>> conflict.mark_resolved(
            ...     resolved_by_initiative_id=initiative.id,
            ...     publisher=publisher
            ... )
        """
        self.status = ConflictStatus.RESOLVED.value
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by_initiative_id = resolved_by_initiative_id
        self.updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            user_id=self.user_id,
            event_type="ConflictResolved",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "conflict_id": str(self.id),
                "resolved_by_initiative_id": (
                    str(resolved_by_initiative_id)
                    if resolved_by_initiative_id
                    else None
                ),
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))
