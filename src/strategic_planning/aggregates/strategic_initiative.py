"""StrategicInitiative aggregate for initiative strategic context management.

This module contains the StrategicInitiative aggregate that encapsulates
business logic for defining and managing strategic context for initiatives.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.db import Base
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.models import DomainEvent

if TYPE_CHECKING:
    from src.models import Initiative, Workspace
    from src.strategic_planning.aggregates.roadmap_theme import RoadmapTheme
    from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
    from src.strategic_planning.services.event_publisher import EventPublisher


class StrategicInitiative(Base):
    """StrategicInitiative aggregate for initiative strategic context lifecycle.

    This aggregate encapsulates the business logic for creating and managing
    strategic context for initiatives. It enforces invariants like text field
    limits and provides domain event emission for all changes.

    This follows the DDD pattern where StrategicInitiative is an aggregate in
    the Strategic Planning bounded context, separate from the core Initiative
    entity in the Task Management context.

    Attributes:
        id: Unique identifier for the strategic initiative
        user_id: Foreign key to user (for RLS)
        initiative_id: Foreign key to initiative (1:1 relationship)
        workspace_id: Foreign key to workspace
        pillar_id: Optional foreign key to strategic pillar
        theme_id: Optional foreign key to roadmap theme
        user_need: What user need or problem this addresses (max 1000 chars)
        connection_to_vision: How this connects to workspace vision (max 1000 chars)
        success_criteria: What success looks like (max 1000 chars)
        out_of_scope: What is explicitly NOT being done (max 1000 chars)
        created_at: Timestamp when context was created
        updated_at: Timestamp when context was last modified
        initiative: Relationship to Initiative entity
        workspace: Relationship to Workspace entity
        strategic_pillar: Relationship to StrategicPillar entity
        roadmap_theme: Relationship to RoadmapTheme entity
    """

    __tablename__ = "strategic_initiatives"
    __table_args__ = (
        UniqueConstraint(
            "initiative_id",
            name="uq_strategic_initiatives_initiative_id",
        ),
        {"schema": "dev"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("private.get_user_id_from_jwt()"),
    )

    initiative_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.initiative.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.workspace.id", ondelete="CASCADE"),
        nullable=False,
    )

    pillar_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.strategic_pillars.id", ondelete="SET NULL"),
        nullable=True,
    )

    theme_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dev.roadmap_themes.id", ondelete="SET NULL"),
        nullable=True,
    )

    user_need: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    connection_to_vision: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    success_criteria: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    out_of_scope: Mapped[str | None] = mapped_column(
        Text,
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

    # Relationships
    initiative: Mapped["Initiative"] = relationship(
        "Initiative",
        back_populates="strategic_context",
    )

    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="strategic_initiatives",
    )

    strategic_pillar: Mapped["StrategicPillar | None"] = relationship(
        "StrategicPillar",
        back_populates="strategic_initiatives",
    )

    roadmap_theme: Mapped["RoadmapTheme | None"] = relationship(
        "RoadmapTheme",
        back_populates="strategic_initiatives",
    )

    @staticmethod
    def _validate_text_field(field_name: str, text: str | None) -> None:
        """Validate text field meets character limit requirements.

        Args:
            field_name: Name of the field being validated (for error messages)
            text: The text to validate

        Raises:
            DomainException: If text exceeds 1000 characters
        """
        if text is not None and len(text) > 1000:
            raise DomainException(
                f"{field_name} must be 1000 characters or less (got {len(text)})"
            )

    @staticmethod
    def define_strategic_context(
        initiative_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        pillar_id: uuid.UUID | None,
        theme_id: uuid.UUID | None,
        user_need: str | None,
        connection_to_vision: str | None,
        success_criteria: str | None,
        out_of_scope: str | None,
        session: Session,
        publisher: "EventPublisher",
    ) -> "StrategicInitiative":
        """Define strategic context for an initiative with business validation.

        This static factory method validates all inputs, creates a fully-initialized
        StrategicInitiative, persists it to get an ID, and emits the
        StrategicContextCompleted domain event.

        Args:
            initiative_id: UUID of the initiative this context is for
            workspace_id: UUID of the workspace
            user_id: UUID of the user creating the context
            pillar_id: Optional UUID of the strategic pillar
            theme_id: Optional UUID of the roadmap theme
            user_need: What user need or problem this addresses (max 1000 chars)
            connection_to_vision: How this connects to vision (max 1000 chars)
            success_criteria: What success looks like (max 1000 chars)
            out_of_scope: What is explicitly NOT being done (max 1000 chars)
            session: Database session for persistence
            publisher: EventPublisher instance for emitting domain events

        Returns:
            The created and persisted StrategicInitiative with ID assigned

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> strategic_init = StrategicInitiative.define_strategic_context(
            ...     initiative_id=initiative.id,
            ...     workspace_id=workspace.id,
            ...     user_id=user.id,
            ...     pillar_id=pillar.id,
            ...     theme_id=None,
            ...     user_need="Users need to track their work",
            ...     connection_to_vision="Enables productive solo development",
            ...     success_criteria="80% adoption within 30 days",
            ...     out_of_scope="Team collaboration features",
            ...     session=session,
            ...     publisher=publisher
            ... )
        """
        # Validate all text fields
        StrategicInitiative._validate_text_field("User need", user_need)
        StrategicInitiative._validate_text_field(
            "Connection to vision", connection_to_vision
        )
        StrategicInitiative._validate_text_field("Success criteria", success_criteria)
        StrategicInitiative._validate_text_field("Out of scope", out_of_scope)

        # Create fully-initialized instance
        strategic_initiative = StrategicInitiative(
            initiative_id=initiative_id,
            workspace_id=workspace_id,
            user_id=user_id,
            pillar_id=pillar_id,
            theme_id=theme_id,
            user_need=user_need,
            connection_to_vision=connection_to_vision,
            success_criteria=success_criteria,
            out_of_scope=out_of_scope,
        )

        # Persist to get ID
        session.add(strategic_initiative)
        session.flush()

        # Emit event now that we have ID
        event = DomainEvent(
            user_id=user_id,
            event_type="StrategicContextCompleted",
            aggregate_id=strategic_initiative.id,
            payload={
                "workspace_id": str(workspace_id),
                "initiative_id": str(initiative_id),
                "pillar_id": str(pillar_id) if pillar_id else None,
                "theme_id": str(theme_id) if theme_id else None,
                "user_need": user_need,
                "connection_to_vision": connection_to_vision,
                "success_criteria": success_criteria,
                "out_of_scope": out_of_scope,
            },
        )
        publisher.publish(event, workspace_id=str(workspace_id))

        return strategic_initiative

    def update_strategic_context(
        self,
        pillar_id: uuid.UUID | None,
        theme_id: uuid.UUID | None,
        user_need: str | None,
        connection_to_vision: str | None,
        success_criteria: str | None,
        out_of_scope: str | None,
        publisher: "EventPublisher",
    ) -> None:
        """Update an existing strategic context.

        This method updates the strategic context fields after validation and emits
        a StrategicContextUpdated domain event.

        Args:
            pillar_id: Optional UUID of the strategic pillar
            theme_id: Optional UUID of the roadmap theme
            user_need: Updated user need (max 1000 chars)
            connection_to_vision: Updated vision connection (max 1000 chars)
            success_criteria: Updated success criteria (max 1000 chars)
            out_of_scope: Updated out of scope (max 1000 chars)
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> strategic_init.update_strategic_context(
            ...     pillar_id=new_pillar.id,
            ...     theme_id=theme.id,
            ...     user_need="Updated user need",
            ...     connection_to_vision="Updated vision connection",
            ...     success_criteria="Updated success criteria",
            ...     out_of_scope="Updated out of scope",
            ...     publisher=publisher
            ... )
        """
        # Validate all text fields
        self._validate_text_field("User need", user_need)
        self._validate_text_field("Connection to vision", connection_to_vision)
        self._validate_text_field("Success criteria", success_criteria)
        self._validate_text_field("Out of scope", out_of_scope)

        # Update fields
        self.pillar_id = pillar_id
        self.theme_id = theme_id
        self.user_need = user_need
        self.connection_to_vision = connection_to_vision
        self.success_criteria = success_criteria
        self.out_of_scope = out_of_scope
        self.updated_at = datetime.now(timezone.utc)

        # Emit event
        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="StrategicContextUpdated",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "initiative_id": str(self.initiative_id),
                "pillar_id": str(pillar_id) if pillar_id else None,
                "theme_id": str(theme_id) if theme_id else None,
                "user_need": user_need,
                "connection_to_vision": connection_to_vision,
                "success_criteria": success_criteria,
                "out_of_scope": out_of_scope,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))
