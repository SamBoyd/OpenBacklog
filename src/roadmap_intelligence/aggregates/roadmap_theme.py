"""RoadmapTheme aggregate for workspace roadmap theme management.

This module contains the RoadmapTheme aggregate that encapsulates
business logic for defining, updating, and linking roadmap themes.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.db import Base
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.models import DomainEvent

if TYPE_CHECKING:
    from src.initiative_management.aggregates.strategic_initiative import (
        StrategicInitiative,
    )
    from src.models import Workspace
    from src.narrative.aggregates.hero import Hero
    from src.narrative.aggregates.turning_point import TurningPoint
    from src.narrative.aggregates.villain import Villain
    from src.strategic_planning.aggregates.product_outcome import ProductOutcome
    from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
    from src.strategic_planning.services.event_publisher import EventPublisher


class RoadmapTheme(Base):
    """RoadmapTheme aggregate for workspace roadmap theme lifecycle.

    This aggregate encapsulates the business logic for creating, updating,
    and linking roadmap themes to product outcomes. It enforces invariants
    like max 5 themes per workspace, unique names, and field length limits.

    Attributes:
        id: Unique identifier for the theme
        workspace_id: Foreign key to workspace
        name: Theme name (1-100 characters, unique per workspace)
        description: Theme description (1-4000 characters, required)
        created_at: Timestamp when theme was created
        updated_at: Timestamp when theme was last modified
        workspace: Relationship to Workspace entity
        outcomes: Relationship to ProductOutcome entities (many-to-many)
        initiatives: Relationship to Initiative entities (one-to-many)
        heroes: Many-to-many relationship to Hero entities
        villains: Many-to-many relationship to Villain entities
    """

    __tablename__ = "roadmap_themes"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "name",
            name="uq_roadmap_themes_workspace_id_name",
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

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
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
        back_populates="roadmap_themes",
    )

    outcomes: Mapped[List["ProductOutcome"]] = relationship(
        "ProductOutcome",
        secondary="dev.theme_outcome_links",
        back_populates="themes",
    )

    strategic_initiatives: Mapped[List["StrategicInitiative"]] = relationship(
        "StrategicInitiative",
        back_populates="roadmap_theme",
    )

    heroes: Mapped[List["Hero"]] = relationship(
        "Hero",
        secondary="dev.roadmap_theme_heroes",
        back_populates="roadmap_themes",
    )

    villains: Mapped[List["Villain"]] = relationship(
        "Villain",
        secondary="dev.roadmap_theme_villains",
        back_populates="roadmap_themes",
    )

    turning_points: Mapped[List["TurningPoint"]] = relationship(
        "TurningPoint",
        secondary="dev.turning_point_story_arcs",
        back_populates="story_arcs",
    )

    @staticmethod
    def validate_theme_limit(workspace_id: uuid.UUID, session: Session) -> None:
        """Validate that workspace has not reached max 5 theme limit.

        Args:
            workspace_id: ID of the workspace to check
            session: SQLAlchemy database session

        Raises:
            DomainException: If workspace already has 5 themes
        """
        count = (
            session.query(RoadmapTheme)
            .filter(RoadmapTheme.workspace_id == workspace_id)
            .count()
        )
        if count >= 5:
            raise DomainException(
                "Workspace has reached maximum of 5 active roadmap themes"
            )

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate theme name meets character limit requirements.

        Args:
            name: The theme name to validate

        Raises:
            DomainException: If name is not between 1-100 characters
        """
        if not name or len(name) < 1:
            raise DomainException("Theme name must be at least 1 character")
        if len(name) > 100:
            raise DomainException(
                f"Theme name must be 100 characters or less (got {len(name)})"
            )

    @staticmethod
    def _validate_description(description: str) -> None:
        """Validate description meets character limit requirements.

        Args:
            description: The description to validate

        Raises:
            DomainException: If description is not between 1-4000 characters
        """
        if not description or len(description) < 1:
            raise DomainException("Description must be at least 1 character")
        if len(description) > 4000:
            raise DomainException(
                f"Description must be 4000 characters or less (got {len(description)})"
            )

    @staticmethod
    def define_theme(
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        description: str,
        session: Session,
        publisher: "EventPublisher",
        hero_ids: List[uuid.UUID] | None = None,
        villain_ids: List[uuid.UUID] | None = None,
    ) -> "RoadmapTheme":
        """Define a new roadmap theme with business validation.

        This static factory method creates a new RoadmapTheme, validates
        all fields, persists to database, and emits a ThemeDefined domain event.

        Args:
            workspace_id: UUID of the workspace
            user_id: UUID of the user creating the theme
            name: Theme name (1-100 characters, unique per workspace)
            description: Theme description (1-4000 characters, required)
            hero_ids: Optional list of hero UUIDs this theme concerns
            villain_ids: Optional list of villain UUIDs this theme opposes
            session: SQLAlchemy database session
            publisher: EventPublisher instance for emitting domain events

        Returns:
            The created RoadmapTheme instance

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> theme = RoadmapTheme.define_theme(
            ...     workspace_id=workspace.id,
            ...     user_id=user.id,
            ...     name="First Week Magic",
            ...     description="Users fail to integrate in first week...",
            ...     session=session,
            ...     publisher=publisher
            ... )
        """
        RoadmapTheme._validate_name(name)
        RoadmapTheme._validate_description(description)

        theme = RoadmapTheme(
            user_id=user_id,
            workspace_id=workspace_id,
            name=name,
            description=description,
        )

        session.add(theme)
        session.flush()

        # Link heroes and villains if provided
        if hero_ids:
            theme.link_heroes(hero_ids, session)
        if villain_ids:
            theme.link_villains(villain_ids, session)

        event = DomainEvent(
            user_id=user_id,
            event_type="ThemeDefined",
            aggregate_id=theme.id,
            payload={
                "workspace_id": str(workspace_id),
                "name": name,
                "description": description,
            },
        )
        publisher.publish(event, workspace_id=str(workspace_id))

        return theme

    def update_theme(
        self,
        name: str,
        description: str,
        publisher: "EventPublisher",
        hero_ids: List[uuid.UUID] | None = None,
        villain_ids: List[uuid.UUID] | None = None,
        session: Session | None = None,
    ) -> None:
        """Update an existing roadmap theme.

        This method updates the theme's fields after validation and emits
        a ThemeUpdated domain event.

        Args:
            name: Updated theme name (1-100 characters, unique per workspace)
            description: Updated theme description (1-4000 characters)
            hero_ids: Optional list of hero UUIDs to replace existing links
            villain_ids: Optional list of villain UUIDs to replace existing links
            session: Database session (required if hero_ids or villain_ids provided)
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> theme.update_theme(
            ...     name="Updated theme",
            ...     description="Updated description",
            ...     publisher=publisher
            ... )
        """
        self._validate_name(name)
        self._validate_description(description)

        self.name = name
        self.description = description
        self.updated_at = datetime.now(timezone.utc)

        # Update many-to-many relationships if provided
        if hero_ids is not None and session is not None:
            self.link_heroes(hero_ids, session)
        if villain_ids is not None and session is not None:
            self.link_villains(villain_ids, session)

        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="ThemeUpdated",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "name": name,
                "description": description,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))

    def link_heroes(
        self,
        hero_ids: List[uuid.UUID],
        session: Session,
    ) -> None:
        """Link heroes to this roadmap theme.

        This method replaces all existing hero links with the new set.

        Args:
            hero_ids: List of hero IDs to link
            session: Database session

        Example:
            >>> theme.link_heroes([hero1.id, hero2.id], session)
        """
        from src.narrative.aggregates.hero import Hero
        from src.roadmap_intelligence.models import RoadmapThemeHero

        session.query(RoadmapThemeHero).filter(
            RoadmapThemeHero.roadmap_theme_id == self.id
        ).delete()

        for hero_id in hero_ids:
            hero = session.query(Hero).filter_by(id=hero_id).first()
            if not hero:
                raise DomainException(f"Hero with id {hero_id} does not exist")
            link = RoadmapThemeHero(
                roadmap_theme_id=self.id,
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
        """Link villains to this roadmap theme.

        This method replaces all existing villain links with the new set.

        Args:
            villain_ids: List of villain IDs to link
            session: Database session

        Example:
            >>> theme.link_villains([villain1.id, villain2.id], session)
        """
        from src.narrative.aggregates.villain import Villain
        from src.roadmap_intelligence.models import RoadmapThemeVillain

        session.query(RoadmapThemeVillain).filter(
            RoadmapThemeVillain.roadmap_theme_id == self.id
        ).delete()

        for villain_id in villain_ids:
            villain = session.query(Villain).filter_by(id=villain_id).first()
            if not villain:
                raise DomainException(f"Villain with id {villain_id} does not exist")
            link = RoadmapThemeVillain(
                roadmap_theme_id=self.id,
                villain_id=villain_id,
                user_id=self.user_id,
            )
            session.add(link)

        self.updated_at = datetime.now(timezone.utc)

    def link_to_outcomes(
        self,
        outcome_ids: List[uuid.UUID],
        session: Session,
        publisher: "EventPublisher",
    ) -> None:
        """Update outcome linkages for this theme.

        This method replaces all existing outcome links with the new set
        and emits a ThemeOutcomesLinked domain event.

        Args:
            outcome_ids: List of outcome IDs to link to this theme
            session: SQLAlchemy database session
            publisher: EventPublisher instance for emitting domain events

        Example:
            >>> theme.link_to_outcomes([outcome1.id, outcome2.id], session, publisher)
        """
        from src.strategic_planning.models import ThemeOutcomeLink

        session.query(ThemeOutcomeLink).filter(
            ThemeOutcomeLink.theme_id == self.id
        ).delete()

        for outcome_id in outcome_ids:
            link = ThemeOutcomeLink(
                theme_id=self.id, outcome_id=outcome_id, user_id=self.user_id
            )
            session.add(link)

        self.updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="ThemeOutcomesLinked",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "theme_id": str(self.id),
                "outcome_ids": [str(oid) for oid in outcome_ids],
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))

    def get_derived_pillars(self) -> List["StrategicPillar"]:
        """Get strategic pillars connected through outcome linkages.

        This method traverses the theme → outcomes → pillars relationship
        to derive which pillars this theme supports.

        Returns:
            List of unique StrategicPillar instances linked via outcomes

        Example:
            >>> pillars = theme.get_derived_pillars()
            >>> print([p.name for p in pillars])
            ['Developer Experience', 'AI-Native Product']
        """
        seen_pillar_ids = set()
        derived_pillars = []

        for outcome in self.outcomes:
            for pillar in outcome.pillars:
                if pillar.id not in seen_pillar_ids:
                    seen_pillar_ids.add(pillar.id)
                    derived_pillars.append(pillar)

        return derived_pillars
