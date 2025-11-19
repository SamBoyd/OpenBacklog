"""Narrator service for narrative domain.

This service generates narrative recaps and "Previously on..." summaries.
"""

import uuid
from typing import Dict, List

from sqlalchemy.orm import Session

from src.narrative.aggregates.conflict import Conflict, ConflictStatus
from src.narrative.aggregates.hero import Hero
from src.narrative.aggregates.turning_point import TurningPoint
from src.narrative.aggregates.villain import Villain
from src.narrative.services.conflict_service import ConflictService
from src.narrative.services.hero_service import HeroService
from src.strategic_planning.services.event_publisher import EventPublisher


class NarratorService:
    """Service for generating narrative recaps.

    This service aggregates narrative data to generate "Previously on..."
    style summaries that help users re-enter flow state.

    Attributes:
        session: SQLAlchemy database session
    """

    def __init__(self, session: Session):
        """Initialize the narrator service.

        Args:
            session: SQLAlchemy database session
        """
        from src.strategic_planning.services.event_publisher import EventPublisher

        self.session = session
        publisher = EventPublisher(session)
        self.hero_service = HeroService(session, publisher)
        self.conflict_service = ConflictService(session, publisher)

    def get_recent_turning_points(
        self, workspace_id: uuid.UUID, limit: int = 10
    ) -> List[TurningPoint]:
        """Get recent turning points ordered by created_at DESC.

        Args:
            workspace_id: UUID of the workspace
            limit: Maximum number of turning points to return (default 10)

        Returns:
            List of TurningPoint instances ordered by created_at DESC

        Example:
            >>> turning_points = service.get_recent_turning_points(workspace.id, limit=5)
        """
        return (
            self.session.query(TurningPoint)
            .filter_by(workspace_id=workspace_id)
            .order_by(TurningPoint.created_at.desc())
            .limit(limit)
            .all()
        )

    def generate_previously_on(self, workspace_id: uuid.UUID) -> Dict:
        """Generate 'Previously on...' narrative recap.

        This is the key service method that enables narrative-aware development.
        It generates a story-style summary of recent progress.

        Args:
            workspace_id: UUID of the workspace

        Returns:
            Dictionary containing:
            - recap_text: Narrative summary text
            - primary_hero: Primary hero dict (or None)
            - active_arcs: List of active roadmap themes with hero/villain links
            - recent_turning_points: List of recent turning points
            - open_conflicts: List of open conflicts
            - suggested_next_tasks: List of suggested next tasks (placeholder for future)

        Example:
            >>> recap = service.generate_previously_on(workspace.id)
            >>> print(recap["recap_text"])
        """
        from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme

        primary_hero = self.hero_service.get_primary_hero(workspace_id)
        open_conflicts = self.conflict_service.get_open_conflicts(workspace_id)
        recent_turning_points = self.get_recent_turning_points(workspace_id, limit=5)

        active_arcs = (
            self.session.query(RoadmapTheme)
            .filter_by(workspace_id=workspace_id)
            .filter(
                (RoadmapTheme.hero_id.isnot(None))
                | (RoadmapTheme.primary_villain_id.isnot(None))
            )
            .order_by(RoadmapTheme.created_at.desc())
            .limit(5)
            .all()
        )

        recap_parts = []
        recap_parts.append("Previously on Your Project...\n")

        if primary_hero:
            recap_parts.append(f"\nHero: {primary_hero.name}")
            if primary_hero.description:
                recap_parts.append(f"{primary_hero.description[:200]}...")
        else:
            recap_parts.append("\nNo primary hero defined yet.")

        if active_arcs:
            recap_parts.append(f"\nActive Story Arcs: {len(active_arcs)}")
            for arc in active_arcs:
                arc_info = f"  • {arc.name}"
                if arc.hero_id and primary_hero:
                    arc_info += f" (helps {primary_hero.name})"
                if arc.primary_villain_id:
                    villain = (
                        self.session.query(Villain)
                        .filter_by(id=arc.primary_villain_id)
                        .first()
                    )
                    if villain:
                        arc_info += f" (fights {villain.name})"
                recap_parts.append(arc_info)
        else:
            recap_parts.append("\nNo active story arcs yet.")

        if recent_turning_points:
            recap_parts.append(f"\nRecent Turning Points: {len(recent_turning_points)}")
            for tp in recent_turning_points[:3]:
                recap_parts.append(f"  • {tp.narrative_description[:150]}...")
        else:
            recap_parts.append("\nNo turning points yet.")

        if open_conflicts:
            recap_parts.append(f"\nOpen Conflicts: {len(open_conflicts)}")
            for conflict in open_conflicts[:3]:
                hero = self.session.query(Hero).filter_by(id=conflict.hero_id).first()
                recap_parts.append(
                    f"  • {conflict.description[:100]}..."
                    if conflict.description
                    else f"  • Conflict {conflict.identifier}"
                )
        else:
            recap_parts.append("\nNo open conflicts.")

        recap_text = "\n".join(recap_parts)

        return {
            "type": "narrative_recap",
            "recap_text": recap_text,
            "primary_hero": (
                {
                    "id": str(primary_hero.id),
                    "identifier": primary_hero.identifier,
                    "name": primary_hero.name,
                    "description": primary_hero.description,
                }
                if primary_hero
                else None
            ),
            "active_arcs": [
                {
                    "id": str(arc.id),
                    "name": arc.name,
                    "hero_id": str(arc.hero_id) if arc.hero_id else None,
                    "primary_villain_id": (
                        str(arc.primary_villain_id) if arc.primary_villain_id else None
                    ),
                }
                for arc in active_arcs
            ],
            "recent_turning_points": [
                {
                    "id": str(tp.id),
                    "identifier": tp.identifier,
                    "narrative_description": tp.narrative_description,
                    "significance": tp.significance,
                    "created_at": tp.created_at.isoformat(),
                }
                for tp in recent_turning_points
            ],
            "open_conflicts": [
                {
                    "id": str(conflict.id),
                    "identifier": conflict.identifier,
                    "description": conflict.description,
                    "status": conflict.status,
                    "hero_id": str(conflict.hero_id),
                    "villain_id": str(conflict.villain_id),
                }
                for conflict in open_conflicts
            ],
            "suggested_next_tasks": [],
        }
