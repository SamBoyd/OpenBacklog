"""StrategicPillar aggregate for workspace pillar management.

This module contains the StrategicPillar aggregate that encapsulates
business logic for defining, updating, and reordering strategic pillars.
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
    from src.initiative_management.aggregates.strategic_initiative import (
        StrategicInitiative,
    )
    from src.models import Workspace
    from src.strategic_planning.models import ProductOutcome
    from src.strategic_planning.services.event_publisher import EventPublisher


class StrategicPillar(Base):
    """StrategicPillar aggregate for workspace strategic pillar lifecycle.

    This aggregate encapsulates the business logic for creating, updating,
    and reordering strategic pillars. It enforces invariants like max 5
    pillars per workspace, unique names, and field length limits.

    Attributes:
        id: Unique identifier for the pillar
        identifier: Human-readable identifier (e.g., "P-001")
        workspace_id: Foreign key to workspace
        name: Pillar name (1-100 characters, unique per workspace)
        description: Optional pillar description (1-3000 characters)
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
        UniqueConstraint(
            "workspace_id",
            "identifier",
            name="uq_strategic_pillars_workspace_id_identifier",
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
        back_populates="strategic_pillars",
    )

    outcomes: Mapped[List["ProductOutcome"]] = relationship(
        "ProductOutcome",
        secondary="dev.outcome_pillar_links",
        back_populates="pillars",
    )

    strategic_initiatives: Mapped[List["StrategicInitiative"]] = relationship(
        "StrategicInitiative",
        back_populates="strategic_pillar",
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

    @staticmethod
    def define_pillar(
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        description: str | None,
        display_order: int,
        session: Session,
        publisher: "EventPublisher",
    ) -> "StrategicPillar":
        """Create a new strategic pillar with business validation.

        This factory method validates inputs, creates a fully-initialized pillar,
        persists it to get an ID, and emits the StrategicPillarDefined domain event.

        Args:
            workspace_id: UUID of the workspace
            user_id: UUID of the user creating the pillar
            name: Pillar name (1-100 characters, unique per workspace)
            description: Optional pillar description (1-3000 characters)
            display_order: Display order for pillar list (0-4)
            session: Database session for persistence
            publisher: EventPublisher instance for emitting domain events

        Returns:
            The created and persisted StrategicPillar with ID assigned

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> pillar = StrategicPillar.define_pillar(
            ...     workspace_id=workspace.id,
            ...     user_id=user.id,
            ...     name="Developer Experience",
            ...     description="Make developers love our product",
            ...     display_order=0,
            ...     session=session,
            ...     publisher=publisher
            ... )
        """
        # Validate all inputs
        StrategicPillar._validate_name(name)
        StrategicPillar._validate_description(description)
        StrategicPillar._validate_display_order(display_order)

        # Create fully-initialized instance
        pillar = StrategicPillar(
            workspace_id=workspace_id,
            user_id=user_id,
            name=name,
            description=description,
            display_order=display_order,
        )

        # Persist to get ID
        session.add(pillar)
        session.flush()

        # Emit event now that we have ID
        event = DomainEvent(
            user_id=user_id,
            event_type="StrategicPillarDefined",
            aggregate_id=pillar.id,
            payload={
                "workspace_id": str(workspace_id),
                "name": name,
                "description": description,
                "display_order": display_order,
            },
        )
        publisher.publish(event, workspace_id=str(workspace_id))

        return pillar

    def update_pillar(
        self,
        name: str,
        description: str | None,
        publisher: "EventPublisher",
    ) -> None:
        """Update an existing strategic pillar.

        This method updates the pillar's fields after validation and emits
        a StrategicPillarUpdated domain event.

        Args:
            name: Updated pillar name (1-100 characters, unique per workspace)
            description: Updated pillar description (1-3000 characters)
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> pillar.update_pillar(
            ...     name="Developer Experience",
            ...     description="Updated description",
            ...     publisher=publisher
            ... )
        """
        self._validate_name(name)
        self._validate_description(description)

        self.name = name
        self.description = description
        self.updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="StrategicPillarUpdated",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "name": name,
                "description": description,
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
        self.updated_at = datetime.now(timezone.utc)

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
