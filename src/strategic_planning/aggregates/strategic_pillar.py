"""StrategicPillar aggregate for workspace pillar management.

This module contains the StrategicPillar aggregate that encapsulates
business logic for defining, updating, and reordering strategic pillars.
"""

import uuid
from datetime import datetime
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
    from src.strategic_planning.models import ProductOutcome
    from src.strategic_planning.services.event_publisher import EventPublisher


class StrategicPillar(Base):
    """StrategicPillar aggregate for workspace strategic pillar lifecycle.

    This aggregate encapsulates the business logic for creating, updating,
    and reordering strategic pillars. It enforces invariants like max 5
    pillars per workspace, unique names, and field length limits.

    Attributes:
        id: Unique identifier for the pillar
        workspace_id: Foreign key to workspace
        name: Pillar name (1-100 characters, unique per workspace)
        description: Optional pillar description (max 1000 characters)
        anti_strategy: Optional anti-strategy text (max 1000 characters)
        display_order: Display order for pillar list (0-4)
        created_at: Timestamp when pillar was created
        updated_at: Timestamp when pillar was last modified
        workspace: Relationship to Workspace entity
        initiatives: Relationship to Initiative entities linked to this pillar
    """

    __tablename__ = "strategic_pillars"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "name",
            name="uq_strategic_pillars_workspace_id_name",
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

    anti_strategy: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow,
    )

    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="strategic_pillars",
    )

    outcomes: Mapped[List["ProductOutcome"]] = relationship(
        "ProductOutcome",
        secondary="dev.outcome_pillar_links",
        back_populates="pillars",
    )

    @staticmethod
    def validate_pillar_limit(workspace_id: uuid.UUID, session: Session) -> None:
        """Validate that workspace has not reached max 5 pillar limit.

        Args:
            workspace_id: ID of the workspace to check
            session: SQLAlchemy database session

        Raises:
            DomainException: If workspace already has 5 pillars
        """
        count = (
            session.query(StrategicPillar)
            .filter(StrategicPillar.workspace_id == workspace_id)
            .count()
        )
        if count >= 5:
            raise DomainException(
                "Workspace has reached maximum of 5 strategic pillars"
            )

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate pillar name meets character limit requirements.

        Args:
            name: The pillar name to validate

        Raises:
            DomainException: If name is not between 1-100 characters
        """
        if not name or len(name) < 1:
            raise DomainException("Pillar name must be at least 1 character")
        if len(name) > 100:
            raise DomainException(
                f"Pillar name must be 100 characters or less (got {len(name)})"
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
    def _validate_display_order(display_order: int) -> None:
        """Validate display order is within valid range.

        Args:
            display_order: The display order to validate

        Raises:
            DomainException: If display_order is not between 0-4
        """
        if display_order < 0 or display_order > 4:
            raise DomainException(
                f"Display order must be between 0-4 (got {display_order})"
            )

    def define_pillar(
        self,
        name: str,
        description: str | None,
        anti_strategy: str | None,
        display_order: int,
        publisher: "EventPublisher",
    ) -> None:
        """Define a new strategic pillar with business validation.

        This method sets the pillar's fields after validation and emits
        a StrategicPillarDefined domain event.

        Args:
            name: Pillar name (1-100 characters, unique per workspace)
            description: Optional pillar description (max 1000 characters)
            anti_strategy: Optional anti-strategy text (max 1000 characters)
            display_order: Display order for pillar list (0-4)
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> pillar = StrategicPillar(workspace_id=workspace.id)
            >>> pillar.define_pillar(
            ...     name="Developer Experience",
            ...     description="Make developers love our product",
            ...     anti_strategy="Not enterprise features",
            ...     display_order=0,
            ...     publisher=publisher
            ... )
        """
        self._validate_name(name)
        self._validate_text_field("Description", description)
        self._validate_text_field("Anti-strategy", anti_strategy)
        self._validate_display_order(display_order)

        self.name = name
        self.description = description
        self.anti_strategy = anti_strategy
        self.display_order = display_order
        self.updated_at = datetime.utcnow()

        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="StrategicPillarDefined",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "name": name,
                "description": description,
                "anti_strategy": anti_strategy,
                "display_order": display_order,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))

    def update_pillar(
        self,
        name: str,
        description: str | None,
        anti_strategy: str | None,
        publisher: "EventPublisher",
    ) -> None:
        """Update an existing strategic pillar.

        This method updates the pillar's fields after validation and emits
        a StrategicPillarUpdated domain event.

        Args:
            name: Updated pillar name (1-100 characters, unique per workspace)
            description: Updated pillar description (max 1000 characters)
            anti_strategy: Updated anti-strategy text (max 1000 characters)
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> pillar.update_pillar(
            ...     name="Developer Experience",
            ...     description="Updated description",
            ...     anti_strategy="Updated anti-strategy",
            ...     publisher=publisher
            ... )
        """
        self._validate_name(name)
        self._validate_text_field("Description", description)
        self._validate_text_field("Anti-strategy", anti_strategy)

        self.name = name
        self.description = description
        self.anti_strategy = anti_strategy
        self.updated_at = datetime.utcnow()

        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="StrategicPillarUpdated",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "name": name,
                "description": description,
                "anti_strategy": anti_strategy,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))

    def reorder_pillar(self, new_order: int, publisher: "EventPublisher") -> None:
        """Reorder a pillar by updating its display order.

        This method updates the pillar's display_order and emits a
        StrategicPillarsReordered domain event.

        Args:
            new_order: New display order (0-4)
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If new_order is not between 0-4

        Example:
            >>> pillar.reorder_pillar(2, publisher)
        """
        self._validate_display_order(new_order)

        old_order = self.display_order
        self.display_order = new_order
        self.updated_at = datetime.utcnow()

        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="StrategicPillarsReordered",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "pillar_id": str(self.id),
                "old_order": old_order,
                "new_order": new_order,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))
