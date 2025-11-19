"""Hero service for narrative domain.

This service orchestrates hero operations, handles identifier lookups,
and provides journey summaries.
"""

import uuid
from typing import List

from sqlalchemy.orm import Session

from src.narrative.aggregates.hero import Hero
from src.narrative.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class HeroService:
    """Service for managing hero operations.

    This service encapsulates the business logic for querying heroes,
    handling identifier lookups, and generating journey summaries.

    Attributes:
        session: SQLAlchemy database session
        publisher: EventPublisher for emitting domain events
    """

    def __init__(self, session: Session, publisher: EventPublisher):
        """Initialize the hero service.

        Args:
            session: SQLAlchemy database session
            publisher: EventPublisher instance for emitting domain events
        """
        self.session = session
        self.publisher = publisher

    def get_hero_by_identifier(self, identifier: str, workspace_id: uuid.UUID) -> Hero:
        """Lookup hero by identifier (e.g., "H-2003").

        Args:
            identifier: Human-readable hero identifier (e.g., "H-2003")
            workspace_id: UUID of the workspace

        Returns:
            Hero instance

        Raises:
            DomainException: If hero not found or doesn't belong to workspace

        Example:
            >>> hero = service.get_hero_by_identifier("H-2003", workspace.id)
        """
        hero = (
            self.session.query(Hero)
            .filter_by(identifier=identifier, workspace_id=workspace_id)
            .first()
        )

        if not hero:
            raise DomainException(
                f"Hero with identifier '{identifier}' not found or does not belong to workspace"
            )

        return hero

    def get_heroes_for_workspace(self, workspace_id: uuid.UUID) -> List[Hero]:
        """Get all heroes for workspace.

        Args:
            workspace_id: UUID of the workspace

        Returns:
            List of Hero instances

        Example:
            >>> heroes = service.get_heroes_for_workspace(workspace.id)
        """
        return (
            self.session.query(Hero)
            .filter_by(workspace_id=workspace_id)
            .order_by(Hero.created_at)
            .all()
        )

    def get_primary_hero(self, workspace_id: uuid.UUID) -> Hero | None:
        """Get primary hero if exists.

        Args:
            workspace_id: UUID of the workspace

        Returns:
            Primary Hero instance or None if no primary hero exists

        Example:
            >>> primary_hero = service.get_primary_hero(workspace.id)
        """
        return (
            self.session.query(Hero)
            .filter_by(workspace_id=workspace_id, is_primary=True)
            .first()
        )

    def get_hero_journey_summary(self, hero_id: uuid.UUID) -> str:
        """Generate narrative journey summary for a hero.

        Args:
            hero_id: UUID of the hero

        Returns:
            Narrative journey summary string

        Raises:
            DomainException: If hero not found

        Example:
            >>> summary = service.get_hero_journey_summary(hero.id)
        """
        hero = self.session.query(Hero).filter_by(id=hero_id).first()

        if not hero:
            raise DomainException(f"Hero with id {hero_id} not found")

        return hero.get_journey_summary()
