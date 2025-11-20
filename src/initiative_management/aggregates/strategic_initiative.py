"""StrategicInitiative aggregate for initiative strategic context management.

This module contains the StrategicInitiative aggregate that encapsulates
business logic for defining and managing strategic context for initiatives.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.db import Base
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.models import DomainEvent

if TYPE_CHECKING:
    from src.models import Initiative, Workspace
    from src.narrative.aggregates.conflict import Conflict
    from src.narrative.aggregates.hero import Hero
    from src.narrative.aggregates.villain import Villain
    from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
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
        description: Strategic context description (1-3000 chars)
        narrative_intent: Optional text describing why this initiative matters narratively
        created_at: Timestamp when context was created
        updated_at: Timestamp when context was last modified
        initiative: Relationship to Initiative entity
        workspace: Relationship to Workspace entity
        strategic_pillar: Relationship to StrategicPillar entity
        roadmap_theme: Relationship to RoadmapTheme entity
        heroes: Many-to-many relationship to Hero entities
        villains: Many-to-many relationship to Villain entities
        conflicts: Many-to-many relationship to Conflict entities
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

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    narrative_intent: Mapped[str | None] = mapped_column(
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

    heroes: Mapped[List["Hero"]] = relationship(
        "Hero",
        secondary="dev.strategic_initiative_heroes",
        back_populates="strategic_initiatives",
    )

    villains: Mapped[List["Villain"]] = relationship(
        "Villain",
        secondary="dev.strategic_initiative_villains",
        back_populates="strategic_initiatives",
    )

    conflicts: Mapped[List["Conflict"]] = relationship(
        "Conflict",
        secondary="dev.strategic_initiative_conflicts",
        back_populates="strategic_initiatives",
    )

    @staticmethod
    def _validate_description(description: str | None) -> None:
        """Validate description field meets character limit requirements.

        Args:
            description: The description text to validate

        Raises:
            DomainException: If description is not between 1-3000 characters when provided
        """
        if description is not None:
            if len(description) < 1:
                raise DomainException(
                    "Description must be at least 1 character when provided"
                )
            if len(description) > 3000:
                raise DomainException(
                    f"Description must be 3000 characters or less (got {len(description)})"
                )

    @staticmethod
    def define_strategic_context(
        session: Session,
        publisher: "EventPublisher",
        initiative_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        pillar_id: uuid.UUID | None,
        theme_id: uuid.UUID | None,
        description: str | None,
        narrative_intent: str | None,
        hero_ids: List[uuid.UUID] | None = None,
        villain_ids: List[uuid.UUID] | None = None,
        conflict_ids: List[uuid.UUID] | None = None,
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
            description: Strategic context description (1-3000 chars)
            narrative_intent: Narrative intent (1-3000 chars)
            hero_ids: Optional list of hero UUIDs this initiative serves
            villain_ids: Optional list of villain UUIDs this initiative confronts
            conflict_ids: Optional list of conflict UUIDs this initiative addresses
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
            ...     description="Users need to track their work...",
            ...     narrative_intent="To improve productivity in...",
            ...     session=session,
            ...     publisher=publisher
            ... )
        """
        # Validate description
        StrategicInitiative._validate_description(description)

        # Create fully-initialized instance
        strategic_initiative = StrategicInitiative(
            initiative_id=initiative_id,
            workspace_id=workspace_id,
            user_id=user_id,
            pillar_id=pillar_id,
            theme_id=theme_id,
            description=description,
            narrative_intent=narrative_intent,
        )

        # Persist to get ID
        session.add(strategic_initiative)
        session.flush()

        # Link heroes, villains, and conflicts if provided
        if hero_ids:
            strategic_initiative.link_heroes(hero_ids, session)
        if villain_ids:
            strategic_initiative.link_villains(villain_ids, session)
        if conflict_ids:
            strategic_initiative.link_conflicts(conflict_ids, session)

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
                "description": description,
            },
        )
        publisher.publish(event, workspace_id=str(workspace_id))

        return strategic_initiative

    def update_strategic_context(
        self,
        publisher: "EventPublisher",
        pillar_id: uuid.UUID | None,
        theme_id: uuid.UUID | None,
        description: str | None,
        narrative_intent: str | None,
        hero_ids: List[uuid.UUID] | None = None,
        villain_ids: List[uuid.UUID] | None = None,
        conflict_ids: List[uuid.UUID] | None = None,
        session: Session | None = None,
    ) -> None:
        """Update an existing strategic context.

        This method updates the strategic context fields after validation and emits
        a StrategicContextUpdated domain event.

        Args:
            publisher: EventPublisher instance for emitting domain events
            pillar_id: Optional UUID of the strategic pillar
            theme_id: Optional UUID of the roadmap theme
            description: Updated strategic context description (1-3000 chars)
            narrative_intent: Updated narrative intent (1-3000 chars)
            hero_ids: Optional list of hero UUIDs to replace existing links
            villain_ids: Optional list of villain UUIDs to replace existing links
            conflict_ids: Optional list of conflict UUIDs to replace existing links
            session: Database session (required if hero_ids, villain_ids, or conflict_ids provided)

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> strategic_init.update_strategic_context(
            ...     publisher=publisher,
            ...     pillar_id=new_pillar.id,
            ...     theme_id=theme.id,
            ...     description="Updated strategic context...",
            ... )
        """
        # Validate description
        self._validate_description(description)

        # Update fields
        self.pillar_id = pillar_id
        self.theme_id = theme_id
        self.description = description
        self.narrative_intent = narrative_intent
        self.updated_at = datetime.now(timezone.utc)

        # Update many-to-many relationships if provided
        if hero_ids is not None and session is not None:
            self.link_heroes(hero_ids, session)
        if villain_ids is not None and session is not None:
            self.link_villains(villain_ids, session)
        if conflict_ids is not None and session is not None:
            self.link_conflicts(conflict_ids, session)

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
                "description": description,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))

    def link_heroes(
        self,
        hero_ids: List[uuid.UUID],
        session: Session,
    ) -> None:
        """Link heroes to this strategic initiative.

        This method replaces all existing hero links with the new set.

        Args:
            hero_ids: List of hero IDs to link
            session: Database session

        Example:
            >>> strategic_init.link_heroes([hero1.id, hero2.id], session)
        """
        from src.initiative_management.models import StrategicInitiativeHero
        from src.narrative.aggregates.hero import Hero

        session.query(StrategicInitiativeHero).filter(
            StrategicInitiativeHero.strategic_initiative_id == self.id
        ).delete()

        for hero_id in hero_ids:
            hero = session.query(Hero).filter_by(id=hero_id).first()
            if not hero:
                raise DomainException(f"Hero with id {hero_id} does not exist")
            link = StrategicInitiativeHero(
                strategic_initiative_id=self.id,
                hero_id=hero_id,
                user_id=self.user_id,
            )
            session.add(link)

        self.updated_at = datetime.now(timezone.utc)

    def link_villains(
        self,
        villain_ids: List[uuid.UUID],
        session: Session,
    ) -> None:
        """Link villains to this strategic initiative.

        This method replaces all existing villain links with the new set.

        Args:
            villain_ids: List of villain IDs to link
            session: Database session

        Example:
            >>> strategic_init.link_villains([villain1.id, villain2.id], session)
        """
        from src.initiative_management.models import StrategicInitiativeVillain
        from src.narrative.aggregates.villain import Villain

        session.query(StrategicInitiativeVillain).filter(
            StrategicInitiativeVillain.strategic_initiative_id == self.id
        ).delete()

        for villain_id in villain_ids:
            villain = session.query(Villain).filter_by(id=villain_id).first()
            if not villain:
                raise DomainException(f"Villain with id {villain_id} does not exist")
            link = StrategicInitiativeVillain(
                strategic_initiative_id=self.id,
                villain_id=villain_id,
                user_id=self.user_id,
            )
            session.add(link)

        self.updated_at = datetime.now(timezone.utc)

    def link_conflicts(
        self,
        conflict_ids: List[uuid.UUID],
        session: Session,
    ) -> None:
        """Link conflicts to this strategic initiative.

        This method replaces all existing conflict links with the new set.

        Args:
            conflict_ids: List of conflict IDs to link
            session: Database session

        Example:
            >>> strategic_init.link_conflicts([conflict1.id, conflict2.id], session)
        """
        from src.initiative_management.models import StrategicInitiativeConflict
        from src.narrative.aggregates.conflict import Conflict

        session.query(StrategicInitiativeConflict).filter(
            StrategicInitiativeConflict.strategic_initiative_id == self.id
        ).delete()

        for conflict_id in conflict_ids:
            conflict = session.query(Conflict).filter_by(id=conflict_id).first()
            if not conflict:
                raise DomainException(f"Conflict with id {conflict_id} does not exist")
            link = StrategicInitiativeConflict(
                strategic_initiative_id=self.id,
                conflict_id=conflict_id,
                user_id=self.user_id,
            )
            session.add(link)

        self.updated_at = datetime.now(timezone.utc)
