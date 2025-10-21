"""Controller for product strategy operations."""

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session, selectinload

from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.product_vision import ProductVision
from src.strategic_planning.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.aggregates.strategic_initiative import StrategicInitiative
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.models import DomainEvent
from src.strategic_planning.services.event_publisher import EventPublisher


def get_workspace_vision(
    workspace_id: uuid.UUID, session: Session
) -> Optional[ProductVision]:
    """Get the product vision for a workspace.

    Args:
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        ProductVision if exists, None otherwise
    """
    return session.query(ProductVision).filter_by(workspace_id=workspace_id).first()


def upsert_workspace_vision(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    vision_text: str,
    session: Session,
) -> ProductVision:
    """Create or update workspace vision.

    Args:
        workspace_id: UUID of the workspace
        user_id: UUID of the user making the change
        vision_text: The vision text (1-1000 characters)
        session: Database session

    Returns:
        The created or updated ProductVision

    Raises:
        DomainException: If vision_text violates validation rules
    """
    # Check if vision already exists
    vision = get_workspace_vision(workspace_id, session)
    publisher = EventPublisher(session)

    if vision:
        # Update existing vision
        vision.refine_vision(vision_text, publisher)
    else:
        # Validate vision text first
        ProductVision._validate_vision_text(vision_text)  # type: ignore[attr-defined]

        # Create new vision with vision_text to satisfy NOT NULL constraint
        vision = ProductVision(
            workspace_id=workspace_id, user_id=user_id, vision_text=vision_text
        )
        session.add(vision)
        session.flush()

        # Emit the domain event
        publisher.publish(
            DomainEvent(
                user_id=user_id,
                event_type="VisionDraftCreated",
                aggregate_id=vision.id,
                payload={
                    "workspace_id": str(workspace_id),
                    "vision_text": vision_text,
                },
            ),
            workspace_id=str(workspace_id),
        )

    session.commit()
    session.refresh(vision)
    return vision


def get_strategic_pillars(
    workspace_id: uuid.UUID, session: Session
) -> List[StrategicPillar]:
    """Get all strategic pillars for a workspace.

    Args:
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        List of StrategicPillar instances ordered by display_order
    """
    return (
        session.query(StrategicPillar)
        .options(selectinload(StrategicPillar.outcomes))
        .filter_by(workspace_id=workspace_id)
        .order_by(StrategicPillar.display_order)
        .all()
    )


def create_strategic_pillar(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    description: Optional[str],
    anti_strategy: Optional[str],
    session: Session,
) -> StrategicPillar:
    """Create a new strategic pillar for a workspace.

    Args:
        workspace_id: UUID of the workspace
        user_id: UUID of the user creating the pillar
        name: Pillar name (1-100 characters, unique per workspace)
        description: Optional pillar description (max 1000 characters)
        anti_strategy: Optional anti-strategy text (max 1000 characters)
        session: Database session

    Returns:
        The created StrategicPillar

    Raises:
        DomainException: If validation fails or pillar limit exceeded
    """
    # Validate workspace hasn't reached 5 pillar limit
    StrategicPillar.validate_pillar_limit(workspace_id, session)

    # Calculate display order based on existing pillars
    current_pillars = get_strategic_pillars(workspace_id, session)
    display_order = len(current_pillars)

    # Use factory method - handles validation, persistence, and event emission
    publisher = EventPublisher(session)
    pillar = StrategicPillar.define_pillar(
        workspace_id=workspace_id,
        user_id=user_id,
        name=name,
        description=description,
        anti_strategy=anti_strategy,
        display_order=display_order,
        session=session,
        publisher=publisher,
    )

    # Commit and return
    session.commit()
    session.refresh(pillar)
    return pillar


def update_strategic_pillar(
    pillar_id: uuid.UUID,
    workspace_id: uuid.UUID,
    name: str,
    description: Optional[str],
    anti_strategy: Optional[str],
    session: Session,
) -> StrategicPillar:
    """Update an existing strategic pillar.

    Args:
        pillar_id: UUID of the pillar to update
        workspace_id: UUID of the workspace (for verification)
        name: Updated pillar name (1-100 characters, unique per workspace)
        description: Updated pillar description (max 1000 characters)
        anti_strategy: Updated anti-strategy text (max 1000 characters)
        session: Database session

    Returns:
        The updated StrategicPillar

    Raises:
        DomainException: If validation fails or pillar not found
    """
    from src.strategic_planning.exceptions import DomainException

    # Get the pillar
    pillar = (
        session.query(StrategicPillar)
        .filter_by(id=pillar_id, workspace_id=workspace_id)
        .first()
    )

    if not pillar:
        raise DomainException("Strategic pillar not found")

    # Use aggregate method for update - handles validation and event emission
    publisher = EventPublisher(session)
    pillar.update_pillar(
        name=name,
        description=description,
        anti_strategy=anti_strategy,
        publisher=publisher,
    )

    # Commit and return
    session.commit()
    session.refresh(pillar)
    return pillar


def delete_strategic_pillar(
    pillar_id: uuid.UUID,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Session,
) -> None:
    """Delete a strategic pillar and unlink associated initiatives.

    Args:
        pillar_id: UUID of the pillar to delete
        workspace_id: UUID of the workspace (for verification)
        user_id: UUID of the user deleting the pillar
        session: Database session

    Raises:
        DomainException: If pillar not found
    """
    from src.strategic_planning.exceptions import DomainException

    # Get the pillar
    pillar = (
        session.query(StrategicPillar)
        .filter_by(id=pillar_id, workspace_id=workspace_id)
        .first()
    )

    if not pillar:
        raise DomainException("Strategic pillar not found")

    # Unlink initiatives (set pillar_id to NULL) - handled by database CASCADE
    # The relationship is configured with ondelete="CASCADE" which handles this

    # Emit domain event before deletion
    publisher = EventPublisher(session)
    event = DomainEvent(
        user_id=user_id,
        event_type="StrategicPillarDeleted",
        aggregate_id=pillar.id,
        payload={
            "workspace_id": str(workspace_id),
            "name": pillar.name,
        },
    )
    publisher.publish(event, workspace_id=str(workspace_id))

    # Delete the pillar
    session.delete(pillar)
    session.commit()


def reorder_strategic_pillars(
    workspace_id: uuid.UUID,
    pillar_orders: dict[uuid.UUID, int],
    session: Session,
) -> List[StrategicPillar]:
    """Reorder strategic pillars by updating their display order.

    Args:
        workspace_id: UUID of the workspace
        pillar_orders: Dict mapping pillar_id to new display_order.
                      Must include ALL pillars in the workspace.
        session: Database session

    Returns:
        List of updated StrategicPillar instances ordered by display_order

    Raises:
        DomainException: If validation fails or pillars not found
    """
    from src.strategic_planning.exceptions import DomainException

    # Get all existing pillars in the workspace
    existing_pillars = get_strategic_pillars(workspace_id, session)

    # Validate all provided pillar IDs exist FIRST before other validations
    existing_ids = {pillar.id for pillar in existing_pillars}
    provided_ids = set(pillar_orders.keys())

    extra_ids = provided_ids - existing_ids
    if extra_ids:
        raise DomainException(
            f"Strategic pillar not found: {', '.join(str(id) for id in extra_ids)}"
        )

    # Then validate that pillar_orders includes ALL pillars
    if len(pillar_orders) != len(existing_pillars):
        raise DomainException(
            f"Must provide display order for all {len(existing_pillars)} pillars "
            f"(got {len(pillar_orders)})"
        )

    missing_ids = existing_ids - provided_ids
    if missing_ids:
        raise DomainException(
            f"Missing display order for pillars: {', '.join(str(id) for id in missing_ids)}"
        )

    # Validate display orders form complete sequence [0, 1, 2, ... n-1]
    display_orders = sorted(pillar_orders.values())
    expected_orders = list(range(len(existing_pillars)))
    if display_orders != expected_orders:
        raise DomainException(
            f"Display orders must be [0, 1, 2, ... {len(existing_pillars)-1}] "
            f"(got {display_orders})"
        )

    # Update display order for each pillar using aggregate method
    publisher = EventPublisher(session)
    for pillar in existing_pillars:
        new_order = pillar_orders[pillar.id]
        if pillar.display_order != new_order:
            pillar.reorder_pillar(new_order, publisher)

    # Commit and return all workspace pillars in display order
    session.commit()

    # Refresh all pillars and return in display order
    for pillar in existing_pillars:
        session.refresh(pillar)

    return get_strategic_pillars(workspace_id, session)


def get_product_outcomes(
    workspace_id: uuid.UUID, session: Session
) -> List[ProductOutcome]:
    """Get all product outcomes for a workspace.

    Args:
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        List of ProductOutcome instances ordered by display_order
    """
    return (
        session.query(ProductOutcome)
        .options(selectinload(ProductOutcome.pillars))
        .filter_by(workspace_id=workspace_id)
        .order_by(ProductOutcome.display_order)
        .all()
    )


def create_product_outcome(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    description: Optional[str],
    metrics: Optional[str],
    time_horizon_months: Optional[int],
    pillar_ids: List[uuid.UUID],
    session: Session,
) -> ProductOutcome:
    """Create a new product outcome for a workspace.

    Args:
        workspace_id: UUID of the workspace
        user_id: UUID of the user creating the outcome
        name: Outcome name (1-150 characters, unique per workspace)
        description: Optional outcome description (max 1500 characters)
        metrics: How to measure this outcome (max 1000 characters)
        time_horizon_months: Time horizon in months (6-36)
        pillar_ids: List of pillar IDs to link to this outcome
        session: Database session

    Returns:
        The created ProductOutcome

    Raises:
        DomainException: If validation fails or outcome limit exceeded
    """
    ProductOutcome.validate_outcome_limit(workspace_id, session)

    current_outcomes = get_product_outcomes(workspace_id, session)
    display_order = len(current_outcomes)

    publisher = EventPublisher(session)
    outcome = ProductOutcome.map_outcome(
        workspace_id=workspace_id,
        user_id=user_id,
        name=name,
        description=description,
        metrics=metrics,
        time_horizon_months=time_horizon_months,
        display_order=display_order,
        session=session,
        publisher=publisher,
    )

    if pillar_ids:
        outcome.link_to_pillars(pillar_ids, user_id, session, publisher)

    session.commit()
    session.refresh(outcome)
    return outcome


def update_product_outcome(
    outcome_id: uuid.UUID,
    workspace_id: uuid.UUID,
    name: str,
    description: Optional[str],
    metrics: Optional[str],
    time_horizon_months: Optional[int],
    pillar_ids: List[uuid.UUID],
    session: Session,
) -> ProductOutcome:
    """Update an existing product outcome.

    Args:
        outcome_id: UUID of the outcome to update
        workspace_id: UUID of the workspace (for verification)
        name: Updated outcome name (1-150 characters, unique per workspace)
        description: Updated outcome description (max 1500 characters)
        metrics: Updated outcome metrics (max 1000 characters)
        time_horizon_months: Updated time horizon (6-36 months)
        pillar_ids: List of pillar IDs to link to this outcome
        session: Database session

    Returns:
        The updated ProductOutcome

    Raises:
        DomainException: If validation fails or outcome not found
    """
    from src.strategic_planning.exceptions import DomainException

    # Get the outcome
    outcome = (
        session.query(ProductOutcome)
        .filter_by(id=outcome_id, workspace_id=workspace_id)
        .first()
    )

    if not outcome:
        raise DomainException("Product outcome not found")

    # Use aggregate method for update - handles validation and event emission
    publisher = EventPublisher(session)
    outcome.update_outcome(
        name=name,
        description=description,
        metrics=metrics,
        time_horizon_months=time_horizon_months,
        publisher=publisher,
    )

    # Update pillar linkages
    outcome.link_to_pillars(pillar_ids, outcome.user_id, session, publisher)

    # Commit and return
    session.commit()
    session.refresh(outcome)
    return outcome


def delete_product_outcome(
    outcome_id: uuid.UUID,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Session,
) -> None:
    """Delete a product outcome and unlink associated roadmap themes.

    Args:
        outcome_id: UUID of the outcome to delete
        workspace_id: UUID of the workspace (for verification)
        user_id: UUID of the user deleting the outcome
        session: Database session

    Raises:
        DomainException: If outcome not found
    """
    from src.strategic_planning.exceptions import DomainException

    # Get the outcome
    outcome = (
        session.query(ProductOutcome)
        .filter_by(id=outcome_id, workspace_id=workspace_id)
        .first()
    )

    if not outcome:
        raise DomainException("Product outcome not found")

    # Unlink roadmap themes (set outcome_id to NULL) - handled by database CASCADE
    # The relationship is configured with ondelete="CASCADE" which handles this

    # Emit domain event before deletion
    publisher = EventPublisher(session)
    event = DomainEvent(
        user_id=user_id,
        event_type="ProductOutcomeDeleted",
        aggregate_id=outcome.id,
        payload={
            "workspace_id": str(workspace_id),
            "name": outcome.name,
        },
    )
    publisher.publish(event, workspace_id=str(workspace_id))

    # Delete the outcome
    session.delete(outcome)
    session.commit()


def reorder_product_outcomes(
    workspace_id: uuid.UUID,
    outcome_orders: dict[uuid.UUID, int],
    session: Session,
) -> List[ProductOutcome]:
    """Reorder product outcomes by updating their display order.

    Args:
        workspace_id: UUID of the workspace
        outcome_orders: Dict mapping outcome_id to new display_order.
                       Must include ALL outcomes in the workspace.
        session: Database session

    Returns:
        List of updated ProductOutcome instances ordered by display_order

    Raises:
        DomainException: If validation fails or outcomes not found
    """
    from src.strategic_planning.exceptions import DomainException

    # Get all existing outcomes in the workspace
    existing_outcomes = get_product_outcomes(workspace_id, session)

    # Validate all provided outcome IDs exist FIRST before other validations
    existing_ids = {outcome.id for outcome in existing_outcomes}
    provided_ids = set(outcome_orders.keys())

    extra_ids = provided_ids - existing_ids
    if extra_ids:
        raise DomainException(
            f"Product outcome not found: {', '.join(str(id) for id in extra_ids)}"
        )

    # Then validate that outcome_orders includes ALL outcomes
    if len(outcome_orders) != len(existing_outcomes):
        raise DomainException(
            f"Must provide display order for all {len(existing_outcomes)} outcomes "
            f"(got {len(outcome_orders)})"
        )

    missing_ids = existing_ids - provided_ids
    if missing_ids:
        raise DomainException(
            f"Missing display order for outcomes: {', '.join(str(id) for id in missing_ids)}"
        )

    # Validate display orders form complete sequence [0, 1, 2, ... n-1]
    display_orders = sorted(outcome_orders.values())
    expected_orders = list(range(len(existing_outcomes)))
    if display_orders != expected_orders:
        raise DomainException(
            f"Display orders must be [0, 1, 2, ... {len(existing_outcomes)-1}] "
            f"(got {display_orders})"
        )

    # Update display order for each outcome using aggregate method
    publisher = EventPublisher(session)
    for outcome in existing_outcomes:
        new_order = outcome_orders[outcome.id]
        if outcome.display_order != new_order:
            outcome.reorder_outcome(new_order, publisher)

    # Commit and return all workspace outcomes in display order
    session.commit()

    # Refresh all outcomes and return in display order
    for outcome in existing_outcomes:
        session.refresh(outcome)

    return get_product_outcomes(workspace_id, session)


def get_roadmap_themes(workspace_id: uuid.UUID, session: Session) -> List[RoadmapTheme]:
    """Get all roadmap themes for a workspace.

    Args:
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        List of RoadmapTheme instances ordered by display_order
    """
    return (
        session.query(RoadmapTheme)
        .options(selectinload(RoadmapTheme.outcomes))
        .filter_by(workspace_id=workspace_id)
        .order_by(RoadmapTheme.display_order)
        .all()
    )


def create_roadmap_theme(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    problem_statement: str,
    hypothesis: Optional[str],
    indicative_metrics: Optional[str],
    time_horizon_months: Optional[int],
    outcome_ids: List[uuid.UUID],
    session: Session,
) -> RoadmapTheme:
    """Create a new roadmap theme for a workspace.

    Args:
        workspace_id: UUID of the workspace
        user_id: UUID of the user creating the theme
        name: Theme name (1-100 characters, unique per workspace)
        problem_statement: Problem being solved (1-1500 characters, required)
        hypothesis: Expected outcome (max 1500 characters)
        indicative_metrics: Success metrics (max 1000 characters)
        time_horizon_months: Time horizon in months (0-12)
        outcome_ids: List of outcome IDs to link to this theme
        session: Database session

    Returns:
        The created RoadmapTheme

    Raises:
        DomainException: If validation fails or theme limit exceeded
    """
    RoadmapTheme.validate_theme_limit(workspace_id, session)

    current_themes = get_roadmap_themes(workspace_id, session)
    display_order = len(current_themes)

    publisher = EventPublisher(session)
    theme = RoadmapTheme.define_theme(
        workspace_id=workspace_id,
        user_id=user_id,
        name=name,
        problem_statement=problem_statement,
        hypothesis=hypothesis,
        indicative_metrics=indicative_metrics,
        time_horizon_months=time_horizon_months,
        display_order=display_order,
        session=session,
        publisher=publisher,
    )

    if outcome_ids:
        theme.link_to_outcomes(outcome_ids, session, publisher)

    session.commit()
    session.refresh(theme)
    return theme


def update_roadmap_theme(
    theme_id: uuid.UUID,
    workspace_id: uuid.UUID,
    name: str,
    problem_statement: str,
    hypothesis: Optional[str],
    indicative_metrics: Optional[str],
    time_horizon_months: Optional[int],
    outcome_ids: List[uuid.UUID],
    session: Session,
) -> RoadmapTheme:
    """Update an existing roadmap theme.

    Args:
        theme_id: UUID of the theme to update
        workspace_id: UUID of the workspace (for verification)
        name: Updated theme name (1-100 characters, unique per workspace)
        problem_statement: Updated problem statement (1-1500 characters)
        hypothesis: Updated hypothesis (max 1500 characters)
        indicative_metrics: Updated metrics (max 1000 characters)
        time_horizon_months: Updated time horizon (0-12 months)
        outcome_ids: List of outcome IDs to link to this theme
        session: Database session

    Returns:
        The updated RoadmapTheme

    Raises:
        DomainException: If validation fails or theme not found
    """
    from src.strategic_planning.exceptions import DomainException

    # Get the theme
    theme = (
        session.query(RoadmapTheme)
        .filter_by(id=theme_id, workspace_id=workspace_id)
        .first()
    )

    if not theme:
        raise DomainException("Roadmap theme not found")

    # Use aggregate method for update - handles validation and event emission
    publisher = EventPublisher(session)
    theme.update_theme(
        name=name,
        problem_statement=problem_statement,
        hypothesis=hypothesis,
        indicative_metrics=indicative_metrics,
        time_horizon_months=time_horizon_months,
        publisher=publisher,
    )

    # Update outcome linkages
    theme.link_to_outcomes(outcome_ids, session, publisher)

    # Commit and return
    session.commit()
    session.refresh(theme)
    return theme


def delete_roadmap_theme(
    theme_id: uuid.UUID,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Session,
) -> None:
    """Delete a roadmap theme and unlink associated initiatives.

    Args:
        theme_id: UUID of the theme to delete
        workspace_id: UUID of the workspace (for verification)
        user_id: UUID of the user deleting the theme
        session: Database session

    Raises:
        DomainException: If theme not found
    """
    from src.strategic_planning.exceptions import DomainException

    # Get the theme
    theme = (
        session.query(RoadmapTheme)
        .filter_by(id=theme_id, workspace_id=workspace_id)
        .first()
    )

    if not theme:
        raise DomainException("Roadmap theme not found")

    # Unlink initiatives (set theme_id to NULL) - handled by database CASCADE
    # The relationship is configured with ondelete="CASCADE" which handles this

    # Emit domain event before deletion
    publisher = EventPublisher(session)
    event = DomainEvent(
        user_id=user_id,
        event_type="RoadmapThemeDeleted",
        aggregate_id=theme.id,
        payload={
            "workspace_id": str(workspace_id),
            "name": theme.name,
        },
    )
    publisher.publish(event, workspace_id=str(workspace_id))

    # Delete the theme
    session.delete(theme)
    session.commit()


def reorder_roadmap_themes(
    workspace_id: uuid.UUID,
    theme_orders: dict[uuid.UUID, int],
    session: Session,
) -> List[RoadmapTheme]:
    """Reorder roadmap themes by updating their display order.

    Args:
        workspace_id: UUID of the workspace
        theme_orders: Dict mapping theme_id to new display_order.
                     Must include ALL themes in the workspace.
        session: Database session

    Returns:
        List of updated RoadmapTheme instances ordered by display_order

    Raises:
        DomainException: If validation fails or themes not found
    """
    from src.strategic_planning.exceptions import DomainException

    # Get all existing themes in the workspace
    existing_themes = get_roadmap_themes(workspace_id, session)

    # Validate all provided theme IDs exist FIRST before other validations
    existing_ids = {theme.id for theme in existing_themes}
    provided_ids = set(theme_orders.keys())

    extra_ids = provided_ids - existing_ids
    if extra_ids:
        raise DomainException(
            f"Roadmap theme not found: {', '.join(str(id) for id in extra_ids)}"
        )

    # Then validate that theme_orders includes ALL themes
    if len(theme_orders) != len(existing_themes):
        raise DomainException(
            f"Must provide display order for all {len(existing_themes)} themes "
            f"(got {len(theme_orders)})"
        )

    missing_ids = existing_ids - provided_ids
    if missing_ids:
        raise DomainException(
            f"Missing display order for themes: {', '.join(str(id) for id in missing_ids)}"
        )

    # Validate display orders form complete sequence [0, 1, 2, ... n-1]
    display_orders = sorted(theme_orders.values())
    expected_orders = list(range(len(existing_themes)))
    if display_orders != expected_orders:
        raise DomainException(
            f"Display orders must be [0, 1, 2, ... {len(existing_themes)-1}] "
            f"(got {display_orders})"
        )

    # Update display order for each theme using aggregate method
    publisher = EventPublisher(session)
    for theme in existing_themes:
        new_order = theme_orders[theme.id]
        if theme.display_order != new_order:
            theme.reorder_theme(new_order, publisher)

    # Commit and return all workspace themes in display order
    session.commit()

    # Refresh all themes and return in display order
    for theme in existing_themes:
        session.refresh(theme)

    return get_roadmap_themes(workspace_id, session)


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
