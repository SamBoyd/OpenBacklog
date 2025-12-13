"""Identifier resolution utilities for MCP tools.

This module provides helper functions to resolve human-readable identifiers
(e.g., "P-001", "O-002", "T-001") to UUIDs for database queries.
"""

import uuid
from typing import List

from sqlalchemy.orm import Session

from src.models import Initiative
from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException


def resolve_pillar_identifier(
    identifier: str, workspace_id: uuid.UUID, session: Session
) -> uuid.UUID:
    """Resolve a pillar identifier to its UUID.

    Args:
        identifier: Human-readable pillar identifier (e.g., "P-001")
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        UUID of the pillar

    Raises:
        DomainException: If pillar not found or doesn't belong to workspace
    """
    pillar = (
        session.query(StrategicPillar)
        .filter_by(identifier=identifier, workspace_id=workspace_id)
        .first()
    )

    if not pillar:
        raise DomainException(
            f"Strategic pillar with identifier '{identifier}' not found or does not belong to workspace"
        )

    return pillar.id


def resolve_outcome_identifier(
    identifier: str, workspace_id: uuid.UUID, session: Session
) -> uuid.UUID:
    """Resolve an outcome identifier to its UUID.

    Args:
        identifier: Human-readable outcome identifier (e.g., "O-002")
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        UUID of the outcome

    Raises:
        DomainException: If outcome not found or doesn't belong to workspace
    """
    outcome = (
        session.query(ProductOutcome)
        .filter_by(identifier=identifier, workspace_id=workspace_id)
        .first()
    )

    if not outcome:
        raise DomainException(
            f"Product outcome with identifier '{identifier}' not found or does not belong to workspace"
        )

    return outcome.id


def resolve_theme_identifier(
    identifier: str, workspace_id: uuid.UUID, session: Session
) -> uuid.UUID:
    """Resolve a theme identifier to its UUID.

    Args:
        identifier: Human-readable theme identifier (e.g., "T-001")
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        UUID of the theme

    Raises:
        DomainException: If theme not found or doesn't belong to workspace
    """
    theme = (
        session.query(RoadmapTheme)
        .filter_by(identifier=identifier, workspace_id=workspace_id)
        .first()
    )

    if not theme:
        raise DomainException(
            f"Roadmap theme with identifier '{identifier}' not found or does not belong to workspace"
        )

    return theme.id


def resolve_initiative_identifier(
    identifier: str, workspace_id: uuid.UUID, session: Session
) -> uuid.UUID:
    """Resolve an initiative identifier to its UUID.

    Args:
        identifier: Human-readable initiative identifier (e.g., "I-1001")
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        UUID of the initiative

    Raises:
        DomainException: If initiative not found or doesn't belong to workspace
    """
    initiative = (
        session.query(Initiative)
        .filter_by(identifier=identifier, workspace_id=workspace_id)
        .first()
    )

    if not initiative:
        raise DomainException(
            f"Initiative with identifier '{identifier}' not found or does not belong to workspace"
        )

    return initiative.id


def resolve_pillar_identifiers(
    identifiers: List[str], workspace_id: uuid.UUID, session: Session
) -> List[uuid.UUID]:
    """Batch resolve multiple pillar identifiers to UUIDs.

    Args:
        identifiers: List of human-readable pillar identifiers
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        List of UUIDs in the same order as the input identifiers

    Raises:
        DomainException: If any pillar not found or doesn't belong to workspace
    """
    pillars = (
        session.query(StrategicPillar)
        .filter(
            StrategicPillar.identifier.in_(identifiers),
            StrategicPillar.workspace_id == workspace_id,
        )
        .all()
    )

    found_identifiers = {pillar.identifier for pillar in pillars}
    missing_identifiers = set(identifiers) - found_identifiers

    if missing_identifiers:
        raise DomainException(
            f"Strategic pillars with identifiers {sorted(missing_identifiers)} not found or do not belong to workspace"
        )

    identifier_to_uuid = {pillar.identifier: pillar.id for pillar in pillars}
    return [identifier_to_uuid[identifier] for identifier in identifiers]


def resolve_outcome_identifiers(
    identifiers: List[str], workspace_id: uuid.UUID, session: Session
) -> List[uuid.UUID]:
    """Batch resolve multiple outcome identifiers to UUIDs.

    Args:
        identifiers: List of human-readable outcome identifiers
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        List of UUIDs in the same order as the input identifiers

    Raises:
        DomainException: If any outcome not found or doesn't belong to workspace
    """
    outcomes = (
        session.query(ProductOutcome)
        .filter(
            ProductOutcome.identifier.in_(identifiers),
            ProductOutcome.workspace_id == workspace_id,
        )
        .all()
    )

    found_identifiers = {outcome.identifier for outcome in outcomes}
    missing_identifiers = set(identifiers) - found_identifiers

    if missing_identifiers:
        raise DomainException(
            f"Product outcomes with identifiers {sorted(missing_identifiers)} not found or do not belong to workspace"
        )

    identifier_to_uuid = {outcome.identifier: outcome.id for outcome in outcomes}
    return [identifier_to_uuid[identifier] for identifier in identifiers]


def resolve_hero_identifiers(
    identifiers: List[str], workspace_id: uuid.UUID, session: Session
) -> List[uuid.UUID]:
    """Batch resolve multiple hero identifiers to UUIDs.

    Args:
        identifiers: List of human-readable hero identifiers
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        List of UUIDs in the same order as the input identifiers

    Raises:
        DomainException: If any hero not found or doesn't belong to workspace
    """
    from src.narrative.services.hero_service import HeroService
    from src.strategic_planning.services.event_publisher import EventPublisher

    hero_service = HeroService(session, EventPublisher(session))
    heroes = [
        hero_service.get_hero_by_identifier(identifier, workspace_id)
        for identifier in identifiers
    ]
    return [hero.id for hero in heroes]


def resolve_villain_identifiers(
    identifiers: List[str], workspace_id: uuid.UUID, session: Session
) -> List[uuid.UUID]:
    """Batch resolve multiple villain identifiers to UUIDs.

    Args:
        identifiers: List of human-readable villain identifiers
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        List of UUIDs in the same order as the input identifiers

    Raises:
        DomainException: If any villain not found or doesn't belong to workspace
    """
    from src.narrative.services.villain_service import VillainService
    from src.strategic_planning.services.event_publisher import EventPublisher

    villain_service = VillainService(session, EventPublisher(session))
    villains = [
        villain_service.get_villain_by_identifier(identifier, workspace_id)
        for identifier in identifiers
    ]
    return [villain.id for villain in villains]
