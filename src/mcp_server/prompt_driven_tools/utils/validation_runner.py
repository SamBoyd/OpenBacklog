"""Validation runners for draft mode workflows.

This module provides functions to validate entity constraints without persisting
to the database. Used in draft mode to catch validation errors early.
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.mcp_server.prompt_driven_tools.utils.identifier_resolvers import (
    resolve_conflict_identifiers,
    resolve_hero_identifiers,
    resolve_pillar_identifier,
    resolve_theme_identifier,
    resolve_villain_identifiers,
)
from src.models import InitiativeStatus
from src.narrative.aggregates.hero import Hero
from src.narrative.aggregates.villain import Villain
from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.product_vision import ProductVision
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException


def validate_vision_constraints(vision_text: str) -> None:
    """Validate vision text constraints.

    Args:
        vision_text: The vision text to validate

    Raises:
        DomainException: If validation fails
    """
    ProductVision._validate_vision_text(vision_text)  # type: ignore[attr-defined]


def validate_pillar_constraints(
    workspace_id: uuid.UUID,
    name: str,
    description: Optional[str],
    session: Session,
) -> None:
    """Validate pillar constraints: uniqueness, limit, format.

    Args:
        workspace_id: UUID of the workspace
        name: Pillar name
        description: Optional pillar description
        session: SQLAlchemy database session

    Raises:
        DomainException: If validation fails
    """
    # Validate format
    StrategicPillar._validate_name(name)  # pyright: ignore[reportPrivateUsage]
    StrategicPillar._validate_description(description)  # type: ignore[attr-defined]

    # Check limit (max 5 pillars)
    StrategicPillar.validate_pillar_limit(workspace_id, session)

    # Check uniqueness
    existing = (
        session.query(StrategicPillar)
        .filter_by(workspace_id=workspace_id, name=name)
        .first()
    )
    if existing:
        raise DomainException(f"Pillar with name '{name}' already exists")


def validate_outcome_constraints(
    workspace_id: uuid.UUID,
    name: str,
    description: str,
    pillar_identifiers: Optional[List[str]],
    session: Session,
) -> None:
    """Validate outcome constraints: uniqueness, limit, format, pillar_identifiers exist.

    Args:
        workspace_id: UUID of the workspace
        name: Outcome name
        description: Outcome description
        pillar_identifiers: Optional list of pillar identifiers (e.g., "P-001") to link
        session: SQLAlchemy database session

    Raises:
        DomainException: If validation fails
    """
    # Validate format
    ProductOutcome._validate_name(name)  # type: ignore[attr-defined]
    ProductOutcome._validate_description(description)  # type: ignore[attr-defined]

    # Check limit (max 10 outcomes)
    ProductOutcome.validate_outcome_limit(workspace_id, session)

    # Check uniqueness
    existing = (
        session.query(ProductOutcome)
        .filter_by(workspace_id=workspace_id, name=name)
        .first()
    )
    if existing:
        raise DomainException(f"Outcome with name '{name}' already exists")

    # Validate pillar_identifiers if provided
    if pillar_identifiers:
        for pillar_identifier in pillar_identifiers:
            pillar = (
                session.query(StrategicPillar)
                .filter_by(identifier=pillar_identifier, workspace_id=workspace_id)
                .first()
            )
            if not pillar:
                raise DomainException(
                    f"Strategic pillar with identifier '{pillar_identifier}' not found or does not belong to workspace"
                )


def validate_hero_constraints(
    workspace_id: uuid.UUID,
    name: str,
    description: Optional[str],
    is_primary: bool,
    session: Session,
) -> None:
    """Validate hero constraints: uniqueness, format, primary hero logic.

    Args:
        workspace_id: UUID of the workspace
        name: Hero name
        description: Optional hero description
        is_primary: Whether this is the primary hero
        session: SQLAlchemy database session

    Raises:
        DomainException: If validation fails
    """
    # Validate format
    Hero._validate_name(name)  # pyright: ignore[reportPrivateUsage]
    Hero._validate_description(description)  # pyright: ignore[reportPrivateUsage]

    # Check uniqueness
    existing = (
        session.query(Hero).filter_by(workspace_id=workspace_id, name=name).first()
    )
    if existing:
        raise DomainException(f"Hero with name '{name}' already exists")

    # If marking as primary, verify no other primary exists
    if is_primary:
        existing_primary = (
            session.query(Hero)
            .filter_by(workspace_id=workspace_id, is_primary=True)
            .first()
        )
        if existing_primary:
            raise DomainException(
                f"Workspace already has a primary hero: {existing_primary.name}"
            )


def validate_villain_constraints(
    workspace_id: uuid.UUID,
    name: str,
    villain_type: str,
    description: str,
    severity: int,
    session: Session,
) -> None:
    """Validate villain constraints: uniqueness, format, severity range.

    Args:
        workspace_id: UUID of the workspace
        name: Villain name
        villain_type: Villain type
        description: Villain description
        severity: Severity rating (1-5)
        session: SQLAlchemy database session

    Raises:
        DomainException: If validation fails
    """
    # Validate format
    Villain._validate_name(name)  # pyright: ignore[reportPrivateUsage]
    Villain._validate_description(description)  # pyright: ignore[reportPrivateUsage]
    Villain._validate_severity(severity)  # pyright: ignore[reportPrivateUsage]
    Villain._validate_villain_type(villain_type)  # pyright: ignore[reportPrivateUsage]

    # Check uniqueness
    existing = (
        session.query(Villain).filter_by(workspace_id=workspace_id, name=name).first()
    )
    if existing:
        raise DomainException(f"Villain with name '{name}' already exists")


def validate_theme_constraints(
    workspace_id: uuid.UUID,
    name: str,
    description: str,
    outcome_ids: Optional[List[str]],
    hero_identifier: Optional[str],
    primary_villain_identifier: Optional[str],
    session: Session,
) -> None:
    """Validate theme constraints: uniqueness, limit, format, linked IDs exist.

    Args:
        workspace_id: UUID of the workspace
        name: Theme name
        description: Theme description
        outcome_ids: Optional list of outcome UUIDs to link
        hero_identifier: Optional hero identifier to link
        primary_villain_identifier: Optional villain identifier to link
        session: SQLAlchemy database session

    Raises:
        DomainException: If validation fails
    """
    # Validate format
    RoadmapTheme._validate_name(name)  # type: ignore[attr-defined]
    RoadmapTheme._validate_description(description)  # type: ignore[attr-defined]

    # Check limit (max 5 themes)
    RoadmapTheme.validate_theme_limit(workspace_id, session)

    # Check uniqueness
    existing = (
        session.query(RoadmapTheme)
        .filter_by(workspace_id=workspace_id, name=name)
        .first()
    )
    if existing:
        raise DomainException(f"Theme with name '{name}' already exists")

    # Validate outcome_ids if provided
    if outcome_ids:
        for outcome_id_str in outcome_ids:
            try:
                outcome_uuid = uuid.UUID(outcome_id_str)
            except ValueError:
                raise DomainException(f"Invalid outcome ID format: {outcome_id_str}")

            outcome = (
                session.query(ProductOutcome)
                .filter_by(id=outcome_uuid, workspace_id=workspace_id)
                .first()
            )
            if not outcome:
                raise DomainException(f"Outcome with ID {outcome_id_str} not found")

    # Validate hero_identifier if provided
    if hero_identifier:
        hero = (
            session.query(Hero)
            .filter_by(workspace_id=workspace_id, identifier=hero_identifier)
            .first()
        )
        if not hero:
            raise DomainException(f"Hero with identifier '{hero_identifier}' not found")

    # Validate primary_villain_identifier if provided
    if primary_villain_identifier:
        villain = (
            session.query(Villain)
            .filter_by(workspace_id=workspace_id, identifier=primary_villain_identifier)
            .first()
        )
        if not villain:
            raise DomainException(
                f"Villain with identifier '{primary_villain_identifier}' not found"
            )


def validate_initiative_constraints(
    workspace_id: uuid.UUID,
    title: str,
    description: str,
    status: InitiativeStatus,
    session: Session,
) -> None:
    return None


def validate_strategic_initiative_constraints(
    workspace_id: uuid.UUID,
    title: str,
    description: str,
    hero_identifiers: List[str],
    villain_identifiers: List[str],
    conflict_identifiers: List[str],
    pillar_identifier: Optional[str],
    theme_identifier: Optional[str],
    narrative_intent: Optional[str],
    session: Session,
) -> Dict[str, Any]:
    """Validate strategic initiative constraints with graceful degradation.

    Instead of failing on invalid identifiers, this function returns valid UUIDs
    and warnings for invalid ones. This enables partial creation when some
    narrative links are missing or incorrect.

    Args:
        workspace_id: UUID of the workspace
        title: Initiative title
        description: Initiative description
        hero_identifiers: List of hero identifiers to validate (e.g., ["H-001"])
        villain_identifiers: List of villain identifiers to validate (e.g., ["V-001"])
        conflict_identifiers: List of conflict identifiers to validate (e.g., ["C-001"])
        pillar_identifier: Optional pillar identifier to validate (e.g., "P-001")
        theme_identifier: Optional theme identifier to validate (e.g., "T-001")
        narrative_intent: Optional narrative intent text
        session: SQLAlchemy database session

    Returns:
        Dictionary with:
        - valid_hero_ids: List of valid hero UUIDs
        - valid_villain_ids: List of valid villain UUIDs
        - valid_conflict_ids: List of valid conflict UUIDs
        - valid_pillar_id: Valid pillar UUID or None
        - valid_theme_id: Valid theme UUID or None
        - warnings: List of warning messages for invalid identifiers

    Raises:
        DomainException: If title or description validation fails
    """

    warnings: List[str] = []
    valid_hero_ids: List[uuid.UUID] = []
    valid_villain_ids: List[uuid.UUID] = []
    valid_conflict_ids: List[uuid.UUID] = []
    valid_pillar_id: Optional[uuid.UUID] = None
    valid_theme_id: Optional[uuid.UUID] = None

    if not title or len(title.strip()) == 0:
        raise DomainException("Title is required")
    if len(title) > 200:
        raise DomainException(
            f"Title must be 200 characters or less (got {len(title)})"
        )

    if not description or len(description.strip()) == 0:
        raise DomainException("Description is required")
    if len(description) > 4000:
        raise DomainException(
            f"Description must be 4000 characters or less (got {len(description)})"
        )

    if narrative_intent and len(narrative_intent) > 1000:
        raise DomainException(
            f"Narrative intent must be 1000 characters or less (got {len(narrative_intent)})"
        )

    hero_ids = resolve_hero_identifiers(hero_identifiers, workspace_id, session)
    valid_hero_ids.extend(hero_ids)

    villain_ids = resolve_villain_identifiers(
        villain_identifiers, workspace_id, session
    )
    valid_villain_ids.extend(villain_ids)

    conflict_ids = resolve_conflict_identifiers(
        conflict_identifiers, workspace_id, session
    )
    valid_conflict_ids.extend(conflict_ids)

    if pillar_identifier:
        valid_pillar_id = resolve_pillar_identifier(
            pillar_identifier, workspace_id, session
        )
    else:
        valid_pillar_id = None

    if theme_identifier:
        valid_theme_id = resolve_theme_identifier(
            theme_identifier, workspace_id, session
        )
    else:
        valid_theme_id = None

    return {
        "valid_hero_ids": valid_hero_ids,
        "valid_villain_ids": valid_villain_ids,
        "valid_conflict_ids": valid_conflict_ids,
        "valid_pillar_id": valid_pillar_id,
        "valid_theme_id": valid_theme_id,
        "warnings": warnings,
    }
