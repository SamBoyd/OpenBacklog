"""Villain service for narrative domain.

This service orchestrates villain operations and handles identifier lookups.
"""

import uuid
from typing import Dict, List

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

    def get_villain_battle_summary(self, villain_id: uuid.UUID) -> Dict[str, int]:
        """Generate battle summary for a villain.

        Returns information about the villain's conflicts, linked themes,
        and initiatives that confront this villain.

        Args:
            villain_id: UUID of the villain

        Returns:
            Dictionary containing:
            - open_conflicts_count: Number of open conflicts
            - escalating_conflicts_count: Number of escalating conflicts
            - resolving_conflicts_count: Number of resolving conflicts
            - resolved_conflicts_count: Number of resolved conflicts
            - total_conflicts_count: Total number of conflicts
            - linked_themes_count: Number of themes targeting this villain
            - initiatives_confronting_count: Number of initiatives confronting villain

        Raises:
            DomainException: If villain not found

        Example:
            >>> summary = service.get_villain_battle_summary(villain.id)
        """
        villain = self.session.query(Villain).filter_by(id=villain_id).first()

        if not villain:
            raise DomainException(f"Villain with id {villain_id} not found")

        open_conflicts = [c for c in villain.conflicts if c.status == "OPEN"]
        escalating_conflicts = [
            c for c in villain.conflicts if c.status == "ESCALATING"
        ]
        resolving_conflicts = [c for c in villain.conflicts if c.status == "RESOLVING"]
        resolved_conflicts = [c for c in villain.conflicts if c.status == "RESOLVED"]

        return {
            "open_conflicts_count": len(open_conflicts),
            "escalating_conflicts_count": len(escalating_conflicts),
            "resolving_conflicts_count": len(resolving_conflicts),
            "resolved_conflicts_count": len(resolved_conflicts),
            "total_conflicts_count": len(villain.conflicts),
            "linked_themes_count": len(villain.roadmap_themes),
            "initiatives_confronting_count": len(villain.strategic_initiatives),
        }
