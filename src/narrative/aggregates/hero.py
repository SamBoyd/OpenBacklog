"""Hero aggregate for workspace hero (user persona) management.

This module contains the Hero aggregate that encapsulates
business logic for defining, updating, and managing heroes.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.db import Base
from src.narrative.exceptions import DomainException
from src.strategic_planning.models import DomainEvent

if TYPE_CHECKING:
    from src.models import Workspace
    from src.narrative.aggregates.conflict import Conflict
    from src.strategic_planning.services.event_publisher import EventPublisher


class Hero(Base):
    """Hero aggregate for workspace hero (user persona) lifecycle.

    This aggregate encapsulates the business logic for creating, updating,
    and managing heroes. It enforces invariants like unique names per workspace
    and field length limits.

    Attributes:
        id: Unique identifier for the hero
        identifier: Human-readable identifier (e.g., "H-2003")
        user_id: Foreign key to user (for RLS)
        workspace_id: Foreign key to workspace
        name: Hero name (1-100 characters, unique per workspace)
        description: Rich description of the hero (1-2000 characters)
        is_primary: Whether this is the primary hero
        created_at: Timestamp when hero was created
        updated_at: Timestamp when hero was last modified
        workspace: Relationship to Workspace entity
        conflicts: Relationship to Conflict entities (one-to-many)
    """

    __tablename__ = "heroes"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "identifier",
            name="uq_heroes_workspace_id_identifier",
        ),
        UniqueConstraint(
            "workspace_id",
            "name",
            name="uq_heroes_workspace_id_name",
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

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
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
        back_populates="heroes",
    )

    conflicts: Mapped[List["Conflict"]] = relationship(
        "Conflict",
        back_populates="hero",
    )

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate hero name meets character limit requirements.

        Args:
            name: The hero name to validate

        Raises:
            DomainException: If name is not between 1-100 characters
        """
        if not name or len(name) < 1:
            raise DomainException("Hero name must be at least 1 character")
        if len(name) > 100:
            raise DomainException(
                f"Hero name must be 100 characters or less (got {len(name)})"
            )

    @staticmethod
    def _validate_description(description: str | None) -> None:
        """Validate hero description meets character limit requirements.

        Args:
            description: The description to validate

        Raises:
            DomainException: If description is not between 1-2000 characters
        """
        if description is not None:
            if len(description) < 1:
                raise DomainException("Hero description must be at least 1 character")
            if len(description) > 2000:
                raise DomainException(
                    f"Hero description must be 2000 characters or less (got {len(description)})"
                )

    @staticmethod
    def define_hero(
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        description: str | None,
        is_primary: bool,
        session: Session,
        publisher: "EventPublisher",
    ) -> "Hero":
        """Create a new hero with business validation.

        This factory method validates inputs, creates a fully-initialized hero,
        persists it to get an ID, and emits the HeroDefined domain event.

        Args:
            workspace_id: UUID of the workspace
            user_id: UUID of the user creating the hero
            name: Hero name (1-100 characters, unique per workspace)
            description: Optional hero description (1-2000 characters)
            is_primary: Whether this is the primary hero
            session: Database session for persistence
            publisher: EventPublisher instance for emitting domain events

        Returns:
            The created and persisted Hero with ID assigned

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> hero = Hero.define_hero(
            ...     workspace_id=workspace.id,
            ...     user_id=user.id,
            ...     name="Sarah, The Solo Builder",
            ...     description="Sarah is a solo developer...",
            ...     is_primary=True,
            ...     session=session,
            ...     publisher=publisher
            ... )
        """
        Hero._validate_name(name)
        Hero._validate_description(description)

        hero = Hero(
            workspace_id=workspace_id,
            user_id=user_id,
            name=name,
            description=description,
            is_primary=is_primary,
        )

        session.add(hero)
        session.flush()

        event = DomainEvent(
            user_id=user_id,
            event_type="HeroDefined",
            aggregate_id=hero.id,
            payload={
                "workspace_id": str(workspace_id),
                "name": name,
                "description": description,
                "is_primary": is_primary,
            },
        )
        publisher.publish(event, workspace_id=str(workspace_id))

        return hero

    def update_hero(
        self,
        name: str,
        description: str | None,
        is_primary: bool,
        publisher: "EventPublisher",
    ) -> None:
        """Update an existing hero.

        This method updates the hero's fields after validation and emits
        a HeroUpdated domain event.

        Args:
            name: Updated hero name (1-100 characters, unique per workspace)
            description: Updated hero description (1-2000 characters)
            is_primary: Updated primary status
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> hero.update_hero(
            ...     name="Sarah, The Solo Builder",
            ...     description="Updated description",
            ...     is_primary=True,
            ...     publisher=publisher
            ... )
        """
        Hero._validate_name(name)
        Hero._validate_description(description)

        self.name = name
        self.description = description
        self.is_primary = is_primary
        self.updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            user_id=self.user_id,
            event_type="HeroUpdated",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "name": name,
                "description": description,
                "is_primary": is_primary,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))

    def get_journey_summary(self) -> str:
        """Generate a narrative summary of the hero's journey.

        Returns:
            A narrative summary including name, description, active story arcs count,
            and open conflicts count.
        """
        active_arcs_count = 0
        open_conflicts_count = len([c for c in self.conflicts if c.status == "OPEN"])

        summary_parts = [
            f"Hero: {self.name}",
            f"Description: {self.description or 'No description provided'}",
            f"Active Story Arcs: {active_arcs_count}",
            f"Open Conflicts: {open_conflicts_count}",
        ]

        return "\n".join(summary_parts)
