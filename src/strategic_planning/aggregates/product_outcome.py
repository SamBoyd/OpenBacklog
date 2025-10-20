"""ProductOutcome aggregate for workspace product outcome management.

This module contains the ProductOutcome aggregate that encapsulates
business logic for defining, updating, and linking product outcomes.
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
from src.strategic_planning.models import DomainEvent, OutcomePillarLink

if TYPE_CHECKING:
    from src.models import Workspace
    from src.strategic_planning.aggregates.roadmap_theme import RoadmapTheme
    from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
    from src.strategic_planning.services.event_publisher import EventPublisher


class ProductOutcome(Base):
    """ProductOutcome aggregate for workspace product outcome lifecycle.

    This aggregate encapsulates the business logic for creating, updating,
    and linking product outcomes to strategic pillars. It enforces invariants
    like max 10 outcomes per workspace, unique names, and field length limits.

    Attributes:
        id: Unique identifier for the outcome
        workspace_id: Foreign key to workspace
        name: Outcome name (1-150 characters, unique per workspace)
        description: Optional outcome description (max 1500 characters)
        metrics: How to measure this outcome (max 1000 characters)
        time_horizon_months: Time horizon in months (6-36)
        display_order: Display order within workspace
        created_at: Timestamp when outcome was created
        updated_at: Timestamp when outcome was last modified
        workspace: Relationship to Workspace entity
        pillars: Relationship to StrategicPillar entities (many-to-many)
        themes: Relationship to RoadmapTheme entities (many-to-many)
    """

    __tablename__ = "product_outcomes"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "name",
            name="uq_product_outcomes_workspace_id_name",
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
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    metrics: Mapped[str | None] = mapped_column(
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
        back_populates="product_outcomes",
    )

    pillars: Mapped[List["StrategicPillar"]] = relationship(
        "StrategicPillar",
        secondary="dev.outcome_pillar_links",
        back_populates="outcomes",
    )

    themes: Mapped[List["RoadmapTheme"]] = relationship(
        "RoadmapTheme",
        secondary="dev.theme_outcome_links",
        back_populates="outcomes",
    )

    @staticmethod
    def validate_outcome_limit(workspace_id: uuid.UUID, session: Session) -> None:
        """Validate that workspace has not reached max 10 outcome limit.

        Args:
            workspace_id: ID of the workspace to check
            session: SQLAlchemy database session

        Raises:
            DomainException: If workspace already has 10 outcomes
        """
        count = (
            session.query(ProductOutcome)
            .filter(ProductOutcome.workspace_id == workspace_id)
            .count()
        )
        if count >= 10:
            raise DomainException(
                "Workspace has reached maximum of 10 product outcomes"
            )

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate outcome name meets character limit requirements.

        Args:
            name: The outcome name to validate

        Raises:
            DomainException: If name is not between 1-150 characters
        """
        if not name or len(name) < 1:
            raise DomainException("Outcome name must be at least 1 character")
        if len(name) > 150:
            raise DomainException(
                f"Outcome name must be 150 characters or less (got {len(name)})"
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
            DomainException: If time_horizon_months is not between 6-36
        """
        if time_horizon_months is not None and (
            time_horizon_months < 6 or time_horizon_months > 36
        ):
            raise DomainException(
                f"Time horizon must be between 6-36 months (got {time_horizon_months})"
            )

    @staticmethod
    def map_outcome(
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        description: str | None,
        metrics: str | None,
        time_horizon_months: int | None,
        display_order: int,
        session: Session,
        publisher: "EventPublisher",
    ) -> "ProductOutcome":
        """Map a new product outcome with business validation.

        This static factory method creates a new ProductOutcome, validates
        all fields, persists to database, and emits an OutcomeMapped domain event.

        Args:
            workspace_id: UUID of the workspace
            user_id: UUID of the user creating the outcome
            name: Outcome name (1-150 characters, unique per workspace)
            description: Optional outcome description (max 1500 characters)
            metrics: How to measure this outcome (max 1000 characters)
            time_horizon_months: Time horizon in months (6-36)
            display_order: Display order within workspace
            session: SQLAlchemy database session
            publisher: EventPublisher instance for emitting domain events

        Returns:
            The created ProductOutcome instance

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> outcome = ProductOutcome.map_outcome(
            ...     workspace_id=workspace.id,
            ...     user_id=user.id,
            ...     name="80% of users use AI weekly",
            ...     description="Measure AI adoption",
            ...     metrics="Weekly AI usage %",
            ...     time_horizon_months=12,
            ...     display_order=0,
            ...     session=session,
            ...     publisher=publisher
            ... )
        """
        ProductOutcome._validate_name(name)
        ProductOutcome._validate_text_field("Description", description, 1500)
        ProductOutcome._validate_text_field("Metrics", metrics, 1000)
        ProductOutcome._validate_time_horizon(time_horizon_months)

        outcome = ProductOutcome(
            user_id=user_id,
            workspace_id=workspace_id,
            name=name,
            description=description,
            metrics=metrics,
            time_horizon_months=time_horizon_months,
            display_order=display_order,
        )

        session.add(outcome)
        session.flush()

        event = DomainEvent(
            user_id=user_id,
            event_type="OutcomeMapped",
            aggregate_id=outcome.id,
            payload={
                "workspace_id": str(workspace_id),
                "name": name,
                "description": description,
                "metrics": metrics,
                "time_horizon_months": time_horizon_months,
                "display_order": display_order,
            },
        )
        publisher.publish(event, workspace_id=str(workspace_id))

        return outcome

    def update_outcome(
        self,
        name: str,
        description: str | None,
        metrics: str | None,
        time_horizon_months: int | None,
        publisher: "EventPublisher",
    ) -> None:
        """Update an existing product outcome.

        This method updates the outcome's fields after validation and emits
        an OutcomeUpdated domain event.

        Args:
            name: Updated outcome name (1-150 characters, unique per workspace)
            description: Updated outcome description (max 1500 characters)
            metrics: Updated metrics (max 1000 characters)
            time_horizon_months: Updated time horizon (6-36 months)
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> outcome.update_outcome(
            ...     name="Updated outcome",
            ...     description="Updated description",
            ...     metrics="Updated metrics",
            ...     time_horizon_months=18,
            ...     publisher=publisher
            ... )
        """
        self._validate_name(name)
        self._validate_text_field("Description", description, 1500)
        self._validate_text_field("Metrics", metrics, 1000)
        self._validate_time_horizon(time_horizon_months)

        self.name = name
        self.description = description
        self.metrics = metrics
        self.time_horizon_months = time_horizon_months
        self.updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="OutcomeUpdated",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "name": name,
                "description": description,
                "metrics": metrics,
                "time_horizon_months": time_horizon_months,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))

    def link_to_pillars(
        self,
        pillar_ids: List[uuid.UUID],
        user_id: uuid.UUID,
        session: Session,
        publisher: "EventPublisher",
    ) -> None:
        """Update pillar linkages for this outcome.

        This method replaces all existing pillar links with the new set
        and emits an OutcomePillarsLinked domain event.

        Args:
            pillar_ids: List of pillar IDs to link to this outcome
            user_id: UUID of the user creating the links
            session: SQLAlchemy database session
            publisher: EventPublisher instance for emitting domain events

        Example:
            >>> outcome.link_to_pillars([pillar1.id, pillar2.id], user.id, session, publisher)
        """
        session.query(OutcomePillarLink).filter(
            OutcomePillarLink.outcome_id == self.id
        ).delete()

        for pillar_id in pillar_ids:
            link = OutcomePillarLink(
                outcome_id=self.id, pillar_id=pillar_id, user_id=user_id
            )
            session.add(link)

        self.updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="OutcomePillarsLinked",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "outcome_id": str(self.id),
                "pillar_ids": [str(pid) for pid in pillar_ids],
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))
