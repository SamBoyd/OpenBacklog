"""PrioritizedRoadmap aggregate for managing theme prioritization.

This aggregate encapsulates the business logic for determining which themes
are prioritized (active work) vs unprioritized (backlog).
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.attributes import flag_modified

from src.db import Base
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.models import DomainEvent

if TYPE_CHECKING:
    from src.models import Workspace
    from src.strategic_planning.services.event_publisher import EventPublisher


class PrioritizedRoadmap(Base):
    """PrioritizedRoadmap aggregate for workspace theme prioritization.

    This aggregate manages which themes are prioritized (being actively worked on)
    and their order. It enforces invariants like no duplicate theme IDs and
    maintains the ordered list of prioritized themes.

    Attributes:
        id: Unique identifier for the prioritized roadmap
        workspace_id: Foreign key to workspace (1:1 relationship)
        user_id: User ID from JWT
        prioritized_theme_ids: Ordered list of theme UUIDs (stored as JSONB array)
        created_at: Timestamp when roadmap was created
        updated_at: Timestamp when roadmap was last modified
        workspace: Relationship to Workspace entity
    """

    __tablename__ = "prioritized_roadmaps"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            name="uq_prioritized_roadmaps_workspace_id",
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
        unique=True,
    )

    prioritized_theme_ids: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
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
        back_populates="prioritized_roadmap",
    )

    def add_theme_to_priority(
        self,
        theme_id: uuid.UUID,
        position: int,
        publisher: "EventPublisher",
    ) -> None:
        """Add a theme to the prioritized roadmap at the specified position.

        Args:
            theme_id: UUID of the theme to prioritize
            position: Position in the priority list (0-indexed)
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If theme is already prioritized or position is invalid

        Example:
            >>> roadmap.add_theme_to_priority(theme.id, 0, publisher)
        """
        theme_id_str = str(theme_id)

        # Validate theme is not already in the list
        if theme_id_str in self.prioritized_theme_ids:
            raise DomainException(f"Theme {theme_id} is already prioritized")

        # Validate position is valid (0 to len(list))
        if position < 0 or position > len(self.prioritized_theme_ids):
            raise DomainException(
                f"Position must be between 0 and {len(self.prioritized_theme_ids)} "
                f"(got {position})"
            )

        # Insert at position
        self.prioritized_theme_ids.insert(position, theme_id_str)
        flag_modified(self, "prioritized_theme_ids")
        self.updated_at = datetime.now(timezone.utc)

        # Emit event
        event = DomainEvent(
            user_id=self.user_id,
            event_type="ThemePrioritized",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "theme_id": theme_id_str,
                "position": position,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))

    def remove_theme_from_priority(
        self,
        theme_id: uuid.UUID,
        publisher: "EventPublisher",
    ) -> None:
        """Remove a theme from the prioritized roadmap.

        Args:
            theme_id: UUID of the theme to deprioritize
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If theme is not currently prioritized

        Example:
            >>> roadmap.remove_theme_from_priority(theme.id, publisher)
        """
        theme_id_str = str(theme_id)

        # Validate theme is in the list
        if theme_id_str not in self.prioritized_theme_ids:
            raise DomainException(f"Theme {theme_id} is already unprioritized")

        # Remove from list
        old_position = self.prioritized_theme_ids.index(theme_id_str)
        self.prioritized_theme_ids.remove(theme_id_str)
        flag_modified(self, "prioritized_theme_ids")
        self.updated_at = datetime.now(timezone.utc)

        # Emit event
        event = DomainEvent(
            user_id=self.user_id,
            event_type="ThemeDeprioritized",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "theme_id": theme_id_str,
                "old_position": old_position,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))

    def reorder_prioritized_themes(
        self,
        new_order: List[uuid.UUID],
        publisher: "EventPublisher",
    ) -> None:
        """Reorder all prioritized themes.

        Args:
            new_order: New ordered list of theme UUIDs
            publisher: EventPublisher instance for emitting domain events

        Raises:
            DomainException: If new_order doesn't contain exactly the same themes

        Example:
            >>> roadmap.reorder_prioritized_themes([theme2.id, theme1.id, theme3.id], publisher)
        """
        new_order_str = [str(tid) for tid in new_order]
        current_set = set(self.prioritized_theme_ids)
        new_set = set(new_order_str)

        # Validate new_order contains exactly the same theme_ids
        if current_set != new_set:
            missing = current_set - new_set
            extra = new_set - current_set
            error_msg = "New order must contain exactly the same themes. "
            if missing:
                error_msg += f"Missing: {', '.join(missing)}. "
            if extra:
                error_msg += f"Extra: {', '.join(extra)}."
            raise DomainException(error_msg.strip())

        # Validate no duplicates in new_order
        if len(new_order_str) != len(new_set):
            raise DomainException("New order contains duplicate theme IDs")

        # Update the list
        old_order = self.prioritized_theme_ids.copy()
        self.prioritized_theme_ids = new_order_str
        flag_modified(self, "prioritized_theme_ids")
        self.updated_at = datetime.now(timezone.utc)

        # Emit event
        event = DomainEvent(
            user_id=self.user_id,
            event_type="PrioritizedThemesReordered",
            aggregate_id=self.id,
            payload={
                "workspace_id": str(self.workspace_id),
                "old_order": old_order,
                "new_order": new_order_str,
            },
        )
        publisher.publish(event, workspace_id=str(self.workspace_id))

    def get_prioritized_themes(self) -> List[uuid.UUID]:
        """Get the ordered list of prioritized theme IDs.

        Returns:
            List of theme UUIDs in priority order

        Example:
            >>> theme_ids = roadmap.get_prioritized_themes()
            >>> print([str(tid) for tid in theme_ids])
            ['uuid1', 'uuid2', 'uuid3']
        """
        return [uuid.UUID(tid) for tid in self.prioritized_theme_ids]

    def is_theme_prioritized(self, theme_id: uuid.UUID) -> bool:
        """Check if a theme is currently prioritized.

        Args:
            theme_id: UUID of the theme to check

        Returns:
            True if theme is prioritized, False otherwise

        Example:
            >>> if roadmap.is_theme_prioritized(theme.id):
            ...     print("Theme is prioritized")
        """
        return str(theme_id) in self.prioritized_theme_ids
