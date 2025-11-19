"""Villain service for narrative domain.

This service orchestrates villain operations and handles identifier lookups.
"""

import uuid
from typing import List

from sqlalchemy.orm import Session

from src.narrative.aggregates.villain import Villain
from src.narrative.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class VillainService:
    """Service for managing villain operations.

    This service encapsulates the business logic for querying villains
    and handling identifier lookups.

    Attributes:
        session: SQLAlchemy database session
        publisher: EventPublisher for emitting domain events
    """

    def __init__(self, session: Session, publisher: EventPublisher):
        """Initialize the villain service.

        Args:
            session: SQLAlchemy database session
            publisher: EventPublisher instance for emitting domain events
        """
        self.session = session
        self.publisher = publisher

    def get_villain_by_identifier(
        self, identifier: str, workspace_id: uuid.UUID
    ) -> Villain:
        """Lookup villain by identifier (e.g., "V-2003").

        Args:
            identifier: Human-readable villain identifier (e.g., "V-2003")
            workspace_id: UUID of the workspace

        Returns:
            Villain instance

        Raises:
            DomainException: If villain not found or doesn't belong to workspace

        Example:
            >>> villain = service.get_villain_by_identifier("V-2003", workspace.id)
        """
        villain = (
            self.session.query(Villain)
            .filter_by(identifier=identifier, workspace_id=workspace_id)
            .first()
        )

        if not villain:
            raise DomainException(
                f"Villain with identifier '{identifier}' not found or does not belong to workspace"
            )

        return villain

    def get_villains_for_workspace(self, workspace_id: uuid.UUID) -> List[Villain]:
        """Get all villains for workspace.

        Args:
            workspace_id: UUID of the workspace

        Returns:
            List of Villain instances

        Example:
            >>> villains = service.get_villains_for_workspace(workspace.id)
        """
        return (
            self.session.query(Villain)
            .filter_by(workspace_id=workspace_id)
            .order_by(Villain.created_at)
            .all()
        )

    def get_active_villains(self, workspace_id: uuid.UUID) -> List[Villain]:
        """Get non-defeated villains for workspace.

        Args:
            workspace_id: UUID of the workspace

        Returns:
            List of active (non-defeated) Villain instances

        Example:
            >>> active_villains = service.get_active_villains(workspace.id)
        """
        return (
            self.session.query(Villain)
            .filter_by(workspace_id=workspace_id, is_defeated=False)
            .order_by(Villain.created_at)
            .all()
        )
