"""Prioritization service for Roadmap Intelligence Context.

This service orchestrates operations across the PrioritizedRoadmap aggregate
and RoadmapTheme entities, handling cross-context validation and coordination.
"""

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from src.models import Workspace
from src.roadmap_intelligence.aggregates.prioritized_roadmap import PrioritizedRoadmap
from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class PrioritizationService:
    """Service for managing theme prioritization operations.

    This service encapsulates the business logic for prioritizing and
    deprioritizing themes, coordinating between the PrioritizedRoadmap
    aggregate and RoadmapTheme entities.

    Attributes:
        session: SQLAlchemy database session
        publisher: EventPublisher for emitting domain events
    """

    def __init__(self, session: Session, publisher: EventPublisher):
        """Initialize the prioritization service.

        Args:
            session: SQLAlchemy database session
            publisher: EventPublisher instance for emitting domain events
        """
        self.session = session
        self.publisher = publisher

    def _validate_theme_exists(
        self, theme_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> RoadmapTheme:
        """Validate that theme exists and belongs to workspace.

        Args:
            theme_id: UUID of the theme
            workspace_id: UUID of the workspace

        Returns:
            RoadmapTheme instance

        Raises:
            DomainException: If theme not found or doesn't belong to workspace
        """
        theme = (
            self.session.query(RoadmapTheme)
            .filter_by(id=theme_id, workspace_id=workspace_id)
            .first()
        )

        if not theme:
            raise DomainException(
                f"Roadmap theme not found or does not belong to workspace"
            )

        return theme

    def prioritize_theme(
        self,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        theme_id: uuid.UUID,
        position: int,
    ) -> PrioritizedRoadmap:
        """Add theme to prioritized roadmap at specified position.

        Args:
            workspace_id: UUID of the workspace
            user_id: UUID of the user
            theme_id: UUID of the theme to prioritize
            position: Position in the priority list (0-indexed)

        Returns:
            Updated PrioritizedRoadmap instance

        Raises:
            DomainException: If validation fails

        Example:
            >>> service.prioritize_theme(workspace.id, user.id, theme.id, 0)
        """
        # Validate theme exists and belongs to workspace
        self._validate_theme_exists(theme_id, workspace_id)

        # Get or create prioritized roadmap
        roadmap = self.get_prioritized_roadmap(workspace_id)

        # Add theme to priority list
        roadmap.add_theme_to_priority(theme_id, position, self.publisher)

        # Commit changes
        self.session.commit()
        self.session.refresh(roadmap)

        return roadmap

    def deprioritize_theme(
        self,
        workspace_id: uuid.UUID,
        theme_id: uuid.UUID,
    ) -> PrioritizedRoadmap:
        """Remove theme from prioritized roadmap.

        Args:
            workspace_id: UUID of the workspace
            theme_id: UUID of the theme to deprioritize

        Returns:
            Updated PrioritizedRoadmap instance

        Raises:
            DomainException: If validation fails or theme already unprioritized

        Example:
            >>> service.deprioritize_theme(workspace.id, theme.id)
        """
        # Validate theme exists and belongs to workspace
        self._validate_theme_exists(theme_id, workspace_id)

        # Get prioritized roadmap
        roadmap = self.get_prioritized_roadmap(workspace_id)

        # If no roadmap exists or theme not in it, it's already unprioritized
        if not roadmap or not roadmap.is_theme_prioritized(theme_id):
            raise DomainException(f"Theme {theme_id} is already unprioritized")

        # Remove theme from priority list
        roadmap.remove_theme_from_priority(theme_id, self.publisher)

        # Commit changes
        self.session.commit()
        self.session.refresh(roadmap)

        return roadmap

    def reorder_prioritized_themes(
        self,
        workspace_id: uuid.UUID,
        new_order: List[uuid.UUID],
    ) -> PrioritizedRoadmap:
        """Reorder all prioritized themes.

        Args:
            workspace_id: UUID of the workspace
            new_order: New ordered list of theme UUIDs

        Returns:
            Updated PrioritizedRoadmap instance

        Raises:
            DomainException: If validation fails

        Example:
            >>> service.reorder_prioritized_themes(
            ...     workspace.id,
            ...     [theme2.id, theme1.id, theme3.id]
            ... )
        """
        # Get prioritized roadmap
        roadmap = self.get_prioritized_roadmap(workspace_id)
        if not roadmap:
            raise DomainException("No prioritized roadmap exists for this workspace")

        # Validate all theme IDs belong to this workspace
        for theme_id in new_order:
            self._validate_theme_exists(theme_id, workspace_id)

        # Reorder themes
        roadmap.reorder_prioritized_themes(new_order, self.publisher)

        # Commit changes
        self.session.commit()
        self.session.refresh(roadmap)

        return roadmap

    def get_prioritized_roadmap(self, workspace_id: uuid.UUID) -> PrioritizedRoadmap:
        """Get prioritized roadmap for workspace (read-only, does not create).

        Args:
            workspace_id: UUID of the workspace

        Returns:
            PrioritizedRoadmap instance
        """
        return (
            self.session.query(PrioritizedRoadmap)
            .filter_by(workspace_id=workspace_id)
            .first()
        )

    def get_prioritized_themes_with_details(
        self, workspace_id: uuid.UUID
    ) -> List[RoadmapTheme]:
        """Get full RoadmapTheme objects in priority order.

        Args:
            workspace_id: UUID of the workspace

        Returns:
            List of RoadmapTheme instances in priority order

        Example:
            >>> themes = service.get_prioritized_themes_with_details(workspace.id)
            >>> for theme in themes:
            ...     print(f"{theme.name}: {theme.problem_statement}")
        """
        roadmap = self.get_prioritized_roadmap(workspace_id)
        if not roadmap or not roadmap.prioritized_theme_ids:
            return []

        # Get theme IDs in order
        theme_ids = roadmap.get_prioritized_themes()

        # Query themes and maintain order
        themes = (
            self.session.query(RoadmapTheme)
            .filter(RoadmapTheme.id.in_(theme_ids))
            .all()
        )

        # Sort themes according to priority order
        theme_dict = {theme.id: theme for theme in themes}
        ordered_themes = [theme_dict[tid] for tid in theme_ids if tid in theme_dict]

        return ordered_themes

    def get_unprioritized_themes(self, workspace_id: uuid.UUID) -> List[RoadmapTheme]:
        """Get all unprioritized themes for workspace.

        Args:
            workspace_id: UUID of the workspace

        Returns:
            List of unprioritized RoadmapTheme instances

        Example:
            >>> backlog_themes = service.get_unprioritized_themes(workspace.id)
            >>> print(f"Backlog has {len(backlog_themes)} themes")
        """
        roadmap = self.get_prioritized_roadmap(workspace_id)
        if not roadmap:
            return []

        prioritized_ids = set(roadmap.get_prioritized_themes()) if roadmap else set()

        # Get all themes for workspace
        all_themes = (
            self.session.query(RoadmapTheme)
            .filter_by(workspace_id=workspace_id)
            .order_by(RoadmapTheme.created_at)
            .all()
        )

        # Filter out prioritized themes
        unprioritized_themes = [
            theme for theme in all_themes if theme.id not in prioritized_ids
        ]

        return unprioritized_themes
