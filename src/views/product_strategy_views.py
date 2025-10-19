"""Product strategy API endpoints."""

import logging
import uuid
from datetime import datetime

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.controllers import product_strategy_controller
from src.db import get_db
from src.main import app
from src.models import User
from src.strategic_planning.exceptions import DomainException
from src.views import dependency_to_override

logger = logging.getLogger(__name__)


class VisionUpdateRequest(BaseModel):
    """Request model for creating or updating a vision."""

    vision_text: str = Field(min_length=1, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "vision_text": "Build the best AI-powered task management tool for solo developers"
            }
        }


class VisionResponse(BaseModel):
    """Response model for vision."""

    id: uuid.UUID
    workspace_id: uuid.UUID
    vision_text: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


@app.get(
    "/api/workspaces/{workspace_id}/vision",
    response_model=VisionResponse,
    tags=["product-strategy"],
)
async def get_workspace_vision(
    workspace_id: uuid.UUID,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> VisionResponse:
    """Get the product vision for a workspace."""
    try:
        vision = product_strategy_controller.get_workspace_vision(workspace_id, session)

        if not vision:
            raise HTTPException(status_code=404, detail="No vision found for workspace")

        return VisionResponse.model_validate(vision)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vision: {e}")
        raise HTTPException(status_code=500, detail="Failed to get vision")


@app.put(
    "/api/workspaces/{workspace_id}/vision",
    response_model=VisionResponse,
    tags=["product-strategy"],
)
async def upsert_workspace_vision(
    workspace_id: uuid.UUID,
    request: VisionUpdateRequest,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> VisionResponse:
    """Create or update the product vision for a workspace."""
    try:
        vision = product_strategy_controller.upsert_workspace_vision(
            workspace_id,
            user.id,
            request.vision_text,
            session,
        )

        return VisionResponse.model_validate(vision)
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error upserting vision: {e}")
        raise HTTPException(status_code=500, detail="Failed to save vision")
