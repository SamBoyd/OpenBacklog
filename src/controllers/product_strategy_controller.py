"""Controller for product strategy operations."""

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from src.strategic_planning.aggregates.product_vision import ProductVision
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
