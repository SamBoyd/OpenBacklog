"""Controller for product strategy operations."""

import uuid
from typing import Optional

from sqlalchemy.orm import Session, selectinload

from src.initiative_management.aggregates.strategic_initiative import (
    StrategicInitiative,
)
from src.strategic_planning.services.event_publisher import EventPublisher


def get_strategic_initiative(
    initiative_id: uuid.UUID, session: Session
) -> Optional[StrategicInitiative]:
    """Get strategic initiative context for an initiative.

    Args:
        initiative_id: UUID of the initiative
        session: Database session

    Returns:
        StrategicInitiative if exists, None otherwise
    """
    return (
        session.query(StrategicInitiative)
        .options(
            selectinload(StrategicInitiative.strategic_pillar),
            selectinload(StrategicInitiative.roadmap_theme),
        )
        .filter_by(initiative_id=initiative_id)
        .first()
    )


def create_strategic_initiative(
    initiative_id: uuid.UUID,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    pillar_id: Optional[uuid.UUID],
    theme_id: Optional[uuid.UUID],
    description: Optional[str],
    narrative_intent: Optional[str],
    session: Session,
    hero_ids: Optional[list[uuid.UUID]] = None,
    villain_ids: Optional[list[uuid.UUID]] = None,
    conflict_ids: Optional[list[uuid.UUID]] = None,
) -> StrategicInitiative:
    """Create strategic context for an initiative.

    Args:
        initiative_id: UUID of the initiative
        workspace_id: UUID of the workspace
        user_id: UUID of the user creating the context
        pillar_id: Optional UUID of the strategic pillar
        theme_id: Optional UUID of the roadmap theme
        description: Strategic context description (no length limit)
        narrative_intent: Narrative intent (no length limit)
        hero_ids: Optional list of hero UUIDs this initiative serves
        villain_ids: Optional list of villain UUIDs this initiative confronts
        conflict_ids: Optional list of conflict UUIDs this initiative addresses
        session: Database session

    Returns:
        The created StrategicInitiative

    Raises:
        DomainException: If validation fails
    """
    publisher = EventPublisher(session)
    strategic_initiative = StrategicInitiative.define_strategic_context(
        session=session,
        publisher=publisher,
        initiative_id=initiative_id,
        workspace_id=workspace_id,
        user_id=user_id,
        pillar_id=pillar_id,
        theme_id=theme_id,
        description=description,
        narrative_intent=narrative_intent,
        hero_ids=hero_ids,
        villain_ids=villain_ids,
        conflict_ids=conflict_ids,
    )

    session.commit()
    session.refresh(strategic_initiative)
    return strategic_initiative


def update_strategic_initiative(
    initiative_id: uuid.UUID,
    pillar_id: Optional[uuid.UUID],
    theme_id: Optional[uuid.UUID],
    description: Optional[str],
    narrative_intent: Optional[str],
    session: Session,
    hero_ids: Optional[list[uuid.UUID]] = None,
    villain_ids: Optional[list[uuid.UUID]] = None,
    conflict_ids: Optional[list[uuid.UUID]] = None,
) -> StrategicInitiative:
    """Update strategic context for an initiative.

    Args:
        initiative_id: UUID of the initiative
        pillar_id: Optional UUID of the strategic pillar
        theme_id: Optional UUID of the roadmap theme
        description: Updated strategic context description (no length limit)
        narrative_intent: Updated narrative intent (no length limit)
        hero_ids: Optional list of hero UUIDs to replace existing links
        villain_ids: Optional list of villain UUIDs to replace existing links
        conflict_ids: Optional list of conflict UUIDs to replace existing links
        session: Database session

    Returns:
        The updated StrategicInitiative

    Raises:
        DomainException: If validation fails or strategic initiative not found
    """
    from src.strategic_planning.exceptions import DomainException

    strategic_initiative = get_strategic_initiative(initiative_id, session)

    if not strategic_initiative:
        raise DomainException("Strategic initiative context not found")

    publisher = EventPublisher(session)
    strategic_initiative.update_strategic_context(
        publisher=publisher,
        pillar_id=pillar_id,
        theme_id=theme_id,
        description=description,
        narrative_intent=narrative_intent,
        hero_ids=hero_ids,
        villain_ids=villain_ids,
        conflict_ids=conflict_ids,
        session=session,
    )

    session.commit()
    session.refresh(strategic_initiative)
    return strategic_initiative
