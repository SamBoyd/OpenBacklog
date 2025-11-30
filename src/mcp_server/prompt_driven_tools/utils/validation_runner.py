"""Validation runners for draft mode workflows.

This module provides functions to validate entity constraints without persisting
to the database. Used in draft mode to catch validation errors early.
"""

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

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
    StrategicPillar._validate_description(
        description
    )  # pyright: ignore[reportPrivateUsage]

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
    pillar_ids: Optional[List[str]],
    session: Session,
) -> None:
    """Validate outcome constraints: uniqueness, limit, format, pillar_ids exist.

    Args:
        workspace_id: UUID of the workspace
        name: Outcome name
        description: Outcome description
        pillar_ids: Optional list of pillar UUIDs to link
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

    # Validate pillar_ids if provided
    if pillar_ids:
        for pillar_id_str in pillar_ids:
            try:
                pillar_uuid = uuid.UUID(pillar_id_str)
            except ValueError:
                raise DomainException(f"Invalid pillar ID format: {pillar_id_str}")

            pillar = (
                session.query(StrategicPillar)
                .filter_by(id=pillar_uuid, workspace_id=workspace_id)
                .first()
            )
            if not pillar:
                raise DomainException(f"Pillar with ID {pillar_id_str} not found")


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
    Villain._validate_villain_type(villain_type)

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
