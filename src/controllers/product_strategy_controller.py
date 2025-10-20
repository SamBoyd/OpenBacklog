"""Controller for product strategy operations."""

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from src.strategic_planning.aggregates.product_vision import ProductVision
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
        ProductVision._validate_vision_text(vision_text)

        # Create new vision with vision_text to satisfy NOT NULL constraint
        vision = ProductVision(
            workspace_id=workspace_id, user_id=user_id, vision_text=vision_text
        )
        session.add(vision)
        session.flush()  # Flush to assign ID before emitting event

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
