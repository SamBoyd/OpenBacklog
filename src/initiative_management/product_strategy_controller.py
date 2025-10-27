"""Controller for product strategy operations."""

import uuid
from typing import Optional

from sqlalchemy.orm import Session, selectinload

from src.strategic_planning.aggregates.strategic_initiative import StrategicInitiative
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
    user_need: Optional[str],
    connection_to_vision: Optional[str],
    success_criteria: Optional[str],
    out_of_scope: Optional[str],
    session: Session,
) -> StrategicInitiative:
    """Create strategic context for an initiative.

    Args:
        initiative_id: UUID of the initiative
        workspace_id: UUID of the workspace
        user_id: UUID of the user creating the context
        pillar_id: Optional UUID of the strategic pillar
        theme_id: Optional UUID of the roadmap theme
        user_need: What user need or problem this addresses (max 1000 chars)
        connection_to_vision: How this connects to vision (max 1000 chars)
        success_criteria: What success looks like (max 1000 chars)
        out_of_scope: What is explicitly NOT being done (max 1000 chars)
        session: Database session

    Returns:
        The created StrategicInitiative

    Raises:
        DomainException: If validation fails
    """
    publisher = EventPublisher(session)
    strategic_initiative = StrategicInitiative.define_strategic_context(
        initiative_id=initiative_id,
        workspace_id=workspace_id,
        user_id=user_id,
        pillar_id=pillar_id,
        theme_id=theme_id,
        user_need=user_need,
        connection_to_vision=connection_to_vision,
        success_criteria=success_criteria,
        out_of_scope=out_of_scope,
        session=session,
        publisher=publisher,
    )

    session.commit()
    session.refresh(strategic_initiative)
    return strategic_initiative


def update_strategic_initiative(
    initiative_id: uuid.UUID,
    pillar_id: Optional[uuid.UUID],
    theme_id: Optional[uuid.UUID],
    user_need: Optional[str],
    connection_to_vision: Optional[str],
    success_criteria: Optional[str],
    out_of_scope: Optional[str],
    session: Session,
) -> StrategicInitiative:
    """Update strategic context for an initiative.

    Args:
        initiative_id: UUID of the initiative
        pillar_id: Optional UUID of the strategic pillar
        theme_id: Optional UUID of the roadmap theme
        user_need: Updated user need (max 1000 chars)
        connection_to_vision: Updated vision connection (max 1000 chars)
        success_criteria: Updated success criteria (max 1000 chars)
        out_of_scope: Updated out of scope (max 1000 chars)
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
        pillar_id=pillar_id,
        theme_id=theme_id,
        user_need=user_need,
        connection_to_vision=connection_to_vision,
        success_criteria=success_criteria,
        out_of_scope=out_of_scope,
        publisher=publisher,
    )

    session.commit()
    session.refresh(strategic_initiative)
    return strategic_initiative
