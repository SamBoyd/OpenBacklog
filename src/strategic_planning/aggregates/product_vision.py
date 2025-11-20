"""ProductVision aggregate for workspace vision management.

This module contains the ProductVision aggregate that encapsulates
business logic for defining and refining a workspace's product vision.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.models import DomainEvent

if TYPE_CHECKING:
    from src.models import Workspace
    from src.strategic_planning.services.event_publisher import EventPublisher


class ProductVision(Base):
    """ProductVision aggregate for workspace vision lifecycle.

    This aggregate encapsulates the business logic for creating and refining
    a workspace's product vision. It requires non-empty vision text and emits
    domain events for all vision changes.

    Attributes:
        id: Unique identifier for the vision
        workspace_id: Foreign key to workspace (1:1 relationship)
        vision_text: The product vision text (must be non-empty)
        created_at: Timestamp when vision was first created
        updated_at: Timestamp when vision was last modified
        workspace: Relationship to Workspace entity
    """

    __tablename__ = "workspace_vision"
    __table_args__ = {"schema": "dev"}

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
        unique=True,
    )

    vision_text: Mapped[str] = mapped_column(
        Text,
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
        back_populates="vision",
    )

    @staticmethod
    def _validate_vision_text(vision_text: str) -> None:
        """Validate vision text is non-empty.

        Args:
            vision_text: The vision text to validate

        Raises:
            DomainException: If vision text is empty
        """
        if not vision_text or len(vision_text) < 1:
            raise DomainException("Vision text must be at least 1 character")

    def refine_vision(self, refined_text: str, publisher: "EventPublisher") -> None:
        """Refine the existing product vision with updated text.

        This method updates the vision text and emits a VisionRefined
        domain event.

        Args:
            refined_text: The refined product vision text (must be non-empty)
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If refined_text is empty

        Example:
            >>> vision.refine_vision("Build the best product for developers", publisher)
        """
        self._validate_vision_text(refined_text)
        self.vision_text = refined_text
        self.updated_at = datetime.utcnow()

        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="VisionRefined",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "vision_text": refined_text,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))
