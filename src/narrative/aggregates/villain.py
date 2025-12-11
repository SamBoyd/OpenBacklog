"""Villain aggregate for workspace villain (problem/obstacle) management.

This module contains the Villain aggregate that encapsulates
business logic for defining, updating, and managing villains.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    Boolean,
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
from src.narrative.exceptions import DomainException
from src.strategic_planning.models import DomainEvent

if TYPE_CHECKING:
    from src.initiative_management.aggregates.strategic_initiative import (
        StrategicInitiative,
    )
    from src.models import Workspace
    from src.narrative.aggregates.conflict import Conflict
    from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
    from src.strategic_planning.services.event_publisher import EventPublisher


class VillainType(str, Enum):
    """Villain type enumeration."""

    EXTERNAL = "EXTERNAL"
    INTERNAL = "INTERNAL"
    TECHNICAL = "TECHNICAL"
    WORKFLOW = "WORKFLOW"
    OTHER = "OTHER"


class Villain(Base):
    """Villain aggregate for workspace villain (problem/obstacle) lifecycle.

    This aggregate encapsulates the business logic for creating, updating,
    and managing villains. It enforces invariants like unique names per workspace,
    field length limits, and severity ranges.

    Attributes:
        id: Unique identifier for the villain
        identifier: Human-readable identifier (e.g., "V-2003")
        user_id: Foreign key to user (for RLS)
        workspace_id: Foreign key to workspace
        name: Villain name (1-100 characters, unique per workspace)
        villain_type: Type of villain (enum)
        description: Rich description of the villain (1-2000 characters, required)
        severity: How big a threat (1-5, default 3)
        is_defeated: Whether this villain has been defeated
        created_at: Timestamp when villain was created
        updated_at: Timestamp when villain was last modified
        workspace: Relationship to Workspace entity
        conflicts: Relationship to Conflict entities (one-to-many)
    """

    __tablename__ = "villains"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "identifier",
            name="uq_villains_workspace_id_identifier",
        ),
        UniqueConstraint(
            "workspace_id",
            "name",
            name="uq_villains_workspace_id_name",
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

    villain_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    severity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("3"),
    )

    is_defeated: Mapped[bool] = mapped_column(
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
        back_populates="villains",
    )

    conflicts: Mapped[List["Conflict"]] = relationship(
        "Conflict",
        back_populates="villain",
    )

    strategic_initiatives: Mapped[List["StrategicInitiative"]] = relationship(
        "StrategicInitiative",
        secondary="dev.strategic_initiative_villains",
        back_populates="villains",
    )

    roadmap_themes: Mapped[List["RoadmapTheme"]] = relationship(
        "RoadmapTheme",
        secondary="dev.roadmap_theme_villains",
        back_populates="villains",
    )

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate villain name meets character limit requirements.

        Args:
            name: The villain name to validate

        Raises:
            DomainException: If name is not between 1-100 characters
        """
        if not name or len(name) < 1:
            raise DomainException("Villain name must be at least 1 character")
        if len(name) > 100:
            raise DomainException(
                f"Villain name must be 100 characters or less (got {len(name)})"
            )

    @staticmethod
    def _validate_description(description: str) -> None:
        """Validate villain description meets character limit requirements.

        Args:
            description: The description to validate

        Raises:
            DomainException: If description is not between 1-2000 characters
        """
        if not description or len(description) < 1:
            raise DomainException("Villain description must be at least 1 character")
        if len(description) > 2000:
            raise DomainException(
                f"Villain description must be 2000 characters or less (got {len(description)})"
            )

    @staticmethod
    def _validate_severity(severity: int) -> None:
        """Validate severity is within valid range.

        Args:
            severity: The severity to validate (1-5)

        Raises:
            DomainException: If severity is not between 1-5
        """
        if severity < 1 or severity > 5:
            raise DomainException(f"Severity must be between 1-5 (got {severity})")

    @staticmethod
    def _validate_villain_type(villain_type: str) -> None:
        """Validate villain type is valid.

        Args:
            villain_type: The villain type to validate
        """
        if villain_type not in VillainType.__members__:
            raise DomainException(f"Invalid villain type: {villain_type}")

    @staticmethod
    def define_villain(
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        villain_type: VillainType,
        description: str,
        severity: int,
        session: Session,
        publisher: "EventPublisher",
    ) -> "Villain":
        """Create a new villain with business validation.

        This factory method validates inputs, creates a fully-initialized villain,
        persists it to get an ID, and emits the VillainIdentified domain event.

        Args:
            workspace_id: UUID of the workspace
            user_id: UUID of the user creating the villain
            name: Villain name (1-100 characters, unique per workspace)
            villain_type: Type of villain (enum)
            description: Villain description (1-2000 characters, required)
            severity: How big a threat (1-5)
            session: Database session for persistence
            publisher: EventPublisher instance for emitting domain events

        Returns:
            The created and persisted Villain with ID assigned

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> villain = Villain.define_villain(
            ...     workspace_id=workspace.id,
            ...     user_id=user.id,
            ...     name="Context Switching",
            ...     villain_type=VillainType.WORKFLOW,
            ...     description="Jumping between tools breaks flow...",
            ...     severity=5,
            ...     session=session,
            ...     publisher=publisher
            ... )
        """
        Villain._validate_name(name)
        Villain._validate_description(description)
        Villain._validate_severity(severity)

        villain = Villain(
            workspace_id=workspace_id,
            user_id=user_id,
            name=name,
            villain_type=villain_type.value,
            description=description,
            severity=severity,
        )

        session.add(villain)
        session.flush()

        event = DomainEvent(
            user_id=user_id,
            event_type="VillainIdentified",
            aggregate_id=villain.id,
            payload={
                "workspace_id": str(workspace_id),
                "name": name,
                "villain_type": villain_type.value,
                "description": description,
                "severity": severity,
            },
        )
        publisher.publish(event, workspace_id=str(workspace_id))

        return villain

    def update_villain(
        self,
        name: str,
        villain_type: VillainType,
        description: str,
        severity: int,
        is_defeated: bool,
        publisher: "EventPublisher",
    ) -> None:
        """Update an existing villain.

        This method updates the villain's fields after validation and emits
        a VillainUpdated domain event.

        Args:
            name: Updated villain name (1-100 characters, unique per workspace)
            villain_type: Updated villain type (enum)
            description: Updated villain description (1-2000 characters)
            severity: Updated severity (1-5)
            is_defeated: Whether the villain is defeated
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If any field violates validation rules

        Example:
            >>> villain.update_villain(
            ...     name="Context Switching",
            ...     villain_type=VillainType.WORKFLOW,
            ...     description="Updated description...",
            ...     severity=4,
            ...     is_defeated=False,
            ...     publisher=publisher
            ... )
        """
        Villain._validate_name(name)
        Villain._validate_description(description)
        Villain._validate_severity(severity)

        self.name = name
        self.villain_type = villain_type.value
        self.description = description
        self.severity = severity
        self.is_defeated = is_defeated
        self.updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            user_id=self.user_id,
            event_type="VillainUpdated",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "name": name,
                "villain_type": villain_type.value,
                "description": description,
                "severity": severity,
                "is_defeated": is_defeated,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))

    def mark_defeated(
        self,
        publisher: "EventPublisher",
    ) -> None:
        """Mark this villain as defeated.

        This method sets is_defeated to True and emits a VillainDefeated domain event.

        Args:
            publisher: EventPublisher instance for emitting domain events

        Example:
            >>> villain.mark_defeated(publisher)
        """
        self.is_defeated = True
        self.updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            user_id=self.user_id,
            event_type="VillainDefeated",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "villain_id": str(self.id),
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))
