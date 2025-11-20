"""Controller for Roadmap Intelligence context."""

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session, selectinload

from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.models import DomainEvent
from src.strategic_planning.services.event_publisher import EventPublisher


def get_roadmap_themes(workspace_id: uuid.UUID, session: Session) -> List[RoadmapTheme]:
    """Get all roadmap themes for a workspace.

    Args:
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        List of RoadmapTheme instances ordered by created_at
    """
    return (
        session.query(RoadmapTheme)
        .options(selectinload(RoadmapTheme.outcomes))
        .filter_by(workspace_id=workspace_id)
        .order_by(RoadmapTheme.created_at)
        .all()
    )


def create_roadmap_theme(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    description: str,
    outcome_ids: List[uuid.UUID],
    session: Session,
) -> RoadmapTheme:
    """Create a new roadmap theme for a workspace.

    Args:
        workspace_id: UUID of the workspace
        user_id: UUID of the user creating the theme
        name: Theme name (1-100 characters, unique per workspace)
        description: Theme description (required, no length limit)
        outcome_ids: List of outcome IDs to link to this theme
        session: Database session

    Returns:
        The created RoadmapTheme

    Raises:
        DomainException: If validation fails or theme limit exceeded
    """
    RoadmapTheme.validate_theme_limit(workspace_id, session)

    publisher = EventPublisher(session)
    theme = RoadmapTheme.define_theme(
        workspace_id=workspace_id,
        user_id=user_id,
        name=name,
        description=description,
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
    description: str,
    outcome_ids: List[uuid.UUID],
    session: Session,
) -> RoadmapTheme:
    """Update an existing roadmap theme.

    Args:
        theme_id: UUID of the theme to update
        workspace_id: UUID of the workspace (for verification)
        name: Updated theme name (1-100 characters, unique per workspace)
        description: Updated theme description (required, no length limit)
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
        description=description,
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
    """Reorder prioritized roadmap themes.

    This function now only operates on prioritized themes. To reorder themes,
    they must first be prioritized using prioritize_roadmap_theme().

    Args:
        workspace_id: UUID of the workspace
        theme_orders: Dict mapping theme_id to new position in priority list.
                     Must include ALL prioritized themes.
        session: Database session

    Returns:
        List of prioritized RoadmapTheme instances in new order

    Raises:
        DomainException: If validation fails, themes not found, or themes not prioritized
    """
    from src.roadmap_intelligence.services.prioritization_service import (
        PrioritizationService,
    )
    from src.strategic_planning.exceptions import DomainException

    publisher = EventPublisher(session)
    service = PrioritizationService(session, publisher)

    # Get prioritized roadmap
    roadmap = service.get_prioritized_roadmap(workspace_id)
    if not roadmap:
        raise DomainException("No prioritized roadmap exists for this workspace")

    # Validate all provided theme IDs are prioritized
    prioritized_ids = set(roadmap.get_prioritized_themes())
    provided_ids = set(theme_orders.keys())

    not_prioritized = provided_ids - prioritized_ids
    if not_prioritized:
        raise DomainException(
            f"Themes are not prioritized: {', '.join(str(id) for id in not_prioritized)}"
        )

    # Validate theme_orders includes ALL prioritized themes
    if len(theme_orders) != len(prioritized_ids):
        missing = prioritized_ids - provided_ids
        raise DomainException(
            f"Must provide order for all {len(prioritized_ids)} prioritized themes "
            f"(got {len(theme_orders)}). Missing: {', '.join(str(id) for id in missing)}"
        )

    # Validate display orders form complete sequence [0, 1, 2, ... n-1]
    display_orders = sorted(theme_orders.values())
    expected_orders = list(range(len(prioritized_ids)))
    if display_orders != expected_orders:
        raise DomainException(
            f"Display orders must be [0, 1, 2, ... {len(prioritized_ids)-1}] "
            f"(got {display_orders})"
        )

    # Convert theme_orders dict to ordered list
    ordered_theme_ids = [
        theme_id for theme_id, _ in sorted(theme_orders.items(), key=lambda x: x[1])
    ]

    # Use service to reorder
    service.reorder_prioritized_themes(workspace_id, ordered_theme_ids)

    # Return themes in new order
    return service.get_prioritized_themes_with_details(workspace_id)


def prioritize_roadmap_theme(
    theme_id: uuid.UUID,
    new_order: int,
    workspace_id: uuid.UUID,
    session: Session,
) -> RoadmapTheme:
    """Add theme to prioritized roadmap at specified position.

    Args:
        theme_id: UUID of the theme to prioritize
        new_order: Position in the priority list (0-indexed)
        workspace_id: UUID of the workspace (for verification)
        session: Database session

    Returns:
        The prioritized RoadmapTheme

    Raises:
        DomainException: If validation fails or theme already prioritized
    """
    from src.roadmap_intelligence.services.prioritization_service import (
        PrioritizationService,
    )

    # Get user_id from the theme
    theme = session.query(RoadmapTheme).filter_by(id=theme_id).first()
    if not theme:
        from src.strategic_planning.exceptions import DomainException

        raise DomainException("Roadmap theme not found")

    # Use service to prioritize
    publisher = EventPublisher(session)
    service = PrioritizationService(session, publisher)
    service.prioritize_theme(workspace_id, theme.user_id, theme_id, new_order)

    # Return refreshed theme
    session.refresh(theme)
    return theme


def deprioritize_roadmap_theme(
    theme_id: uuid.UUID,
    workspace_id: uuid.UUID,
    session: Session,
) -> RoadmapTheme:
    """Remove theme from prioritized roadmap.

    Args:
        theme_id: UUID of the theme to deprioritize
        workspace_id: UUID of the workspace (for verification)
        session: Database session

    Returns:
        The deprioritized RoadmapTheme

    Raises:
        DomainException: If validation fails or theme already unprioritized
    """
    from src.roadmap_intelligence.services.prioritization_service import (
        PrioritizationService,
    )

    # Use service to deprioritize
    publisher = EventPublisher(session)
    service = PrioritizationService(session, publisher)
    service.deprioritize_theme(workspace_id, theme_id)

    # Return refreshed theme
    theme = session.query(RoadmapTheme).filter_by(id=theme_id).first()
    if theme:
        session.refresh(theme)
    return theme


def get_prioritized_themes(
    workspace_id: uuid.UUID, session: Session
) -> List[RoadmapTheme]:
    """Get all prioritized themes for workspace in priority order.

    Args:
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        List of prioritized RoadmapTheme instances in priority order
    """
    from src.roadmap_intelligence.services.prioritization_service import (
        PrioritizationService,
    )

    publisher = EventPublisher(session)
    service = PrioritizationService(session, publisher)
    return service.get_prioritized_themes_with_details(workspace_id)


def get_unprioritized_themes(
    workspace_id: uuid.UUID, session: Session
) -> List[RoadmapTheme]:
    """Get all unprioritized themes for workspace.

    Args:
        workspace_id: UUID of the workspace
        session: Database session

    Returns:
        List of unprioritized RoadmapTheme instances
    """
    from src.roadmap_intelligence.services.prioritization_service import (
        PrioritizationService,
    )

    publisher = EventPublisher(session)
    service = PrioritizationService(session, publisher)
    return service.get_unprioritized_themes(workspace_id)
