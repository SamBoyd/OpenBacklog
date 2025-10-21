"""RoadmapTheme aggregate for workspace roadmap theme management.

This module contains the RoadmapTheme aggregate that encapsulates
business logic for defining, updating, and linking roadmap themes.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.db import Base
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.models import DomainEvent

if TYPE_CHECKING:
    from src.models import Initiative, Workspace
    from src.strategic_planning.aggregates.product_outcome import ProductOutcome
    from src.strategic_planning.aggregates.strategic_initiative import (
        StrategicInitiative,
    )
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
        problem_statement: Problem being solved (1-1500 characters, required)
        hypothesis: Expected outcome (max 1500 characters)
        indicative_metrics: Success metrics (max 1000 characters)
        time_horizon_months: Time horizon in months (0-12)
        display_order: Display order within workspace
        created_at: Timestamp when theme was created
        updated_at: Timestamp when theme was last modified
        workspace: Relationship to Workspace entity
        outcomes: Relationship to ProductOutcome entities (many-to-many)
        initiatives: Relationship to Initiative entities (one-to-many)
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

    problem_statement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    hypothesis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    indicative_metrics: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    time_horizon_months: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
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
    def _validate_problem_statement(problem_statement: str) -> None:
        """Validate problem statement meets character limit requirements.

        Args:
            problem_statement: The problem statement to validate

        Raises:
            DomainException: If problem_statement is not between 1-1500 characters
        """
        if not problem_statement or len(problem_statement) < 1:
            raise DomainException("Problem statement must be at least 1 character")
        if len(problem_statement) > 1500:
            raise DomainException(
                f"Problem statement must be 1500 characters or less (got {len(problem_statement)})"
            )

    @staticmethod
    def _validate_text_field(
        field_name: str, text: str | None, max_length: int
    ) -> None:
        """Validate text field meets character limit requirements.

        Args:
            field_name: Name of the field being validated (for error messages)
            text: The text to validate
            max_length: Maximum allowed length

        Raises:
            DomainException: If text exceeds max_length
        """
        if text is not None and len(text) > max_length:
            raise DomainException(
                f"{field_name} must be {max_length} characters or less (got {len(text)})"
            )

    @staticmethod
    def _validate_time_horizon(time_horizon_months: int | None) -> None:
        """Validate time horizon is within valid range.

        Args:
            time_horizon_months: The time horizon to validate

        Raises:
            DomainException: If time_horizon_months is not between 0-12
        """
        if time_horizon_months is not None and (
            time_horizon_months < 0 or time_horizon_months > 12
        ):
            raise DomainException(
                f"Time horizon must be between 0-12 months (got {time_horizon_months})"
            )

    @staticmethod
    def define_theme(
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        problem_statement: str,
        hypothesis: str | None,
        indicative_metrics: str | None,
        time_horizon_months: int | None,
        display_order: int,
        session: Session,
        publisher: "EventPublisher",
    ) -> "RoadmapTheme":
        """Define a new roadmap theme with business validation.

        This static factory method creates a new RoadmapTheme, validates
        all fields, persists to database, and emits a ThemeDefined domain event.

        Args:
            workspace_id: UUID of the workspace
            user_id: UUID of the user creating the theme
            name: Theme name (1-100 characters, unique per workspace)
            problem_statement: Problem being solved (1-1500 characters, required)
            hypothesis: Expected outcome (max 1500 characters)
            indicative_metrics: Success metrics (max 1000 characters)
            time_horizon_months: Time horizon in months (0-12)
            display_order: Display order within workspace
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
            ...     problem_statement="Users fail to integrate in first week",
            ...     hypothesis="Quick wins drive adoption",
            ...     indicative_metrics="% users active in week 1",
            ...     time_horizon_months=6,
            ...     display_order=0,
            ...     session=session,
            ...     publisher=publisher
            ... )
        """
        RoadmapTheme._validate_name(name)
        RoadmapTheme._validate_problem_statement(problem_statement)
        RoadmapTheme._validate_text_field("Hypothesis", hypothesis, 1500)
        RoadmapTheme._validate_text_field(
            "Indicative metrics", indicative_metrics, 1000
        )
        RoadmapTheme._validate_time_horizon(time_horizon_months)

        theme = RoadmapTheme(
            user_id=user_id,
            workspace_id=workspace_id,
            name=name,
            problem_statement=problem_statement,
            hypothesis=hypothesis,
            indicative_metrics=indicative_metrics,
            time_horizon_months=time_horizon_months,
            display_order=display_order,
        )

        session.add(theme)
        session.flush()

        event = DomainEvent(
            user_id=user_id,
            event_type="ThemeDefined",
            aggregate_id=theme.id,
            payload={
                "workspace_id": str(workspace_id),
                "name": name,
                "problem_statement": problem_statement,
                "hypothesis": hypothesis,
                "indicative_metrics": indicative_metrics,
                "time_horizon_months": time_horizon_months,
                "display_order": display_order,
            },
        )
        publisher.publish(event, workspace_id=str(workspace_id))

        return theme

    def update_theme(
        self,
        name: str,
        problem_statement: str,
        hypothesis: str | None,
        indicative_metrics: str | None,
        time_horizon_months: int | None,
        publisher: "EventPublisher",
    ) -> None:
        """Update an existing roadmap theme.

        This method updates the theme's fields after validation and emits
        a ThemeUpdated domain event.

        Args:
            name: Updated theme name (1-100 characters, unique per workspace)
            problem_statement: Updated problem statement (1-1500 characters)
            hypothesis: Updated hypothesis (max 1500 characters)
            indicative_metrics: Updated metrics (max 1000 characters)
            time_horizon_months: Updated time horizon (0-12 months)
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> theme.update_theme(
            ...     name="Updated theme",
            ...     problem_statement="Updated problem",
            ...     hypothesis="Updated hypothesis",
            ...     indicative_metrics="Updated metrics",
            ...     time_horizon_months=9,
            ...     publisher=publisher
            ... )
        """
        self._validate_name(name)
        self._validate_problem_statement(problem_statement)
        self._validate_text_field("Hypothesis", hypothesis, 1500)
        self._validate_text_field("Indicative metrics", indicative_metrics, 1000)
        self._validate_time_horizon(time_horizon_months)

        self.name = name
        self.problem_statement = problem_statement
        self.hypothesis = hypothesis
        self.indicative_metrics = indicative_metrics
        self.time_horizon_months = time_horizon_months
        self.updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="ThemeUpdated",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "name": name,
                "problem_statement": problem_statement,
                "hypothesis": hypothesis,
                "indicative_metrics": indicative_metrics,
                "time_horizon_months": time_horizon_months,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))

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

    def reorder_theme(self, new_order: int, publisher: "EventPublisher") -> None:
        """Reorder a theme by updating its display order.

        This method updates the theme's display_order and emits a
        ThemesReordered domain event.

        Args:
            new_order: New display order (0-4)
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If new_order is not between 0-4

        Example:
            >>> theme.reorder_theme(2, publisher)
        """
        if new_order < 0 or new_order > 4:
            raise DomainException(
                f"Display order must be between 0-4 (got {new_order})"
            )

        old_order = self.display_order
        self.display_order = new_order
        self.updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="ThemesReordered",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "theme_id": str(self.id),
                "old_order": old_order,
                "new_order": new_order,
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
