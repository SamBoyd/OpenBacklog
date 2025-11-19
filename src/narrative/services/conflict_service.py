"""Conflict service for narrative domain.

This service orchestrates conflict operations, handles identifier lookups,
and filters by status.
"""

import uuid
from typing import List

from sqlalchemy.orm import Session

from src.narrative.aggregates.conflict import Conflict, ConflictStatus
from src.narrative.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class ConflictService:
    """Service for managing conflict operations.

    This service encapsulates the business logic for querying conflicts,
    handling identifier lookups, and filtering by status.

    Attributes:
        session: SQLAlchemy database session
        publisher: EventPublisher for emitting domain events
    """

    def __init__(self, session: Session, publisher: EventPublisher):
        """Initialize the conflict service.

        Args:
            session: SQLAlchemy database session
            publisher: EventPublisher instance for emitting domain events
        """
        self.session = session
        self.publisher = publisher

    def get_conflict_by_identifier(
        self, identifier: str, workspace_id: uuid.UUID
    ) -> Conflict:
        """Lookup conflict by identifier (e.g., "C-2003").

        Args:
            identifier: Human-readable conflict identifier (e.g., "C-2003")
            workspace_id: UUID of the workspace

        Returns:
            Conflict instance

        Raises:
            DomainException: If conflict not found or doesn't belong to workspace

        Example:
            >>> conflict = service.get_conflict_by_identifier("C-2003", workspace.id)
        """
        conflict = (
            self.session.query(Conflict)
            .filter_by(identifier=identifier, workspace_id=workspace_id)
            .first()
        )

        if not conflict:
            raise DomainException(
                f"Conflict with identifier '{identifier}' not found or does not belong to workspace"
            )

        return conflict

    def get_conflicts_for_workspace(
        self, workspace_id: uuid.UUID, status: ConflictStatus | None = None
    ) -> List[Conflict]:
        """Get conflicts for workspace with optional status filter.

        Args:
            workspace_id: UUID of the workspace
            status: Optional ConflictStatus to filter by

        Returns:
            List of Conflict instances

        Example:
            >>> all_conflicts = service.get_conflicts_for_workspace(workspace.id)
            >>> open_conflicts = service.get_conflicts_for_workspace(workspace.id, ConflictStatus.OPEN)
        """
        query = self.session.query(Conflict).filter_by(workspace_id=workspace_id)

        if status:
            query = query.filter_by(status=status.value)

        return query.order_by(Conflict.created_at.desc()).all()

    def get_conflicts_for_hero(
        self, hero_id: uuid.UUID, status: ConflictStatus | None = None
    ) -> List[Conflict]:
        """Get conflicts for specific hero with optional status filter.

        Args:
            hero_id: UUID of the hero
            status: Optional ConflictStatus to filter by

        Returns:
            List of Conflict instances for the hero

        Example:
            >>> hero_conflicts = service.get_conflicts_for_hero(hero.id)
            >>> open_hero_conflicts = service.get_conflicts_for_hero(hero.id, ConflictStatus.OPEN)
        """
        query = self.session.query(Conflict).filter_by(hero_id=hero_id)

        if status:
            query = query.filter_by(status=status.value)

        return query.order_by(Conflict.created_at.desc()).all()

    def get_open_conflicts(self, workspace_id: uuid.UUID) -> List[Conflict]:
        """Get all open conflicts for workspace.

        Args:
            workspace_id: UUID of the workspace

        Returns:
            List of open Conflict instances

        Example:
            >>> open_conflicts = service.get_open_conflicts(workspace.id)
        """
        return self.get_conflicts_for_workspace(workspace_id, ConflictStatus.OPEN)
