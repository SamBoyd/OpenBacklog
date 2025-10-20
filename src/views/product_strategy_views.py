"""Product strategy API endpoints."""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

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


# Strategic Pillar Endpoints


class PillarCreateRequest(BaseModel):
    """Request model for creating a strategic pillar."""

    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    anti_strategy: Optional[str] = Field(default=None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Developer Experience",
                "description": "Make developers love our product",
                "anti_strategy": "Not enterprise features",
            }
        }


class PillarResponse(BaseModel):
    """Response model for strategic pillar."""

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: Optional[str]
    anti_strategy: Optional[str]
    display_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


@app.get(
    "/api/workspaces/{workspace_id}/pillars",
    response_model=List[PillarResponse],
    tags=["product-strategy"],
)
async def get_workspace_pillars(
    workspace_id: uuid.UUID,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> List[PillarResponse]:
    """Get all strategic pillars for a workspace."""
    try:
        pillars = product_strategy_controller.get_strategic_pillars(
            workspace_id, session
        )
        return [PillarResponse.model_validate(pillar) for pillar in pillars]
    except Exception as e:
        logger.error(f"Error getting pillars: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pillars")


@app.post(
    "/api/workspaces/{workspace_id}/pillars",
    response_model=PillarResponse,
    tags=["product-strategy"],
    status_code=201,
)
async def create_strategic_pillar(
    workspace_id: uuid.UUID,
    request: PillarCreateRequest,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> PillarResponse:
    """Create a new strategic pillar for a workspace."""
    try:
        pillar = product_strategy_controller.create_strategic_pillar(
            workspace_id,
            user.id,
            request.name,
            request.description,
            request.anti_strategy,
            session,
        )

        return PillarResponse.model_validate(pillar)
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating pillar: {e}")
        raise HTTPException(status_code=500, detail="Failed to create pillar")


class PillarUpdateRequest(BaseModel):
    """Request model for updating a strategic pillar."""

    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    anti_strategy: Optional[str] = Field(default=None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Pillar Name",
                "description": "Updated description",
                "anti_strategy": "Updated anti-strategy",
            }
        }


@app.put(
    "/api/workspaces/{workspace_id}/pillars/{pillar_id}",
    response_model=PillarResponse,
    tags=["product-strategy"],
)
async def update_strategic_pillar(
    workspace_id: uuid.UUID,
    pillar_id: uuid.UUID,
    request: PillarUpdateRequest,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> PillarResponse:
    """Update an existing strategic pillar."""
    try:
        pillar = product_strategy_controller.update_strategic_pillar(
            pillar_id,
            workspace_id,
            request.name,
            request.description,
            request.anti_strategy,
            session,
        )

        return PillarResponse.model_validate(pillar)
    except DomainException as e:
        # Check if it's a "not found" error
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating pillar: {e}")
        raise HTTPException(status_code=500, detail="Failed to update pillar")


@app.delete(
    "/api/workspaces/{workspace_id}/pillars/{pillar_id}",
    status_code=204,
    tags=["product-strategy"],
)
async def delete_strategic_pillar(
    workspace_id: uuid.UUID,
    pillar_id: uuid.UUID,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> None:
    """Delete a strategic pillar."""
    try:
        product_strategy_controller.delete_strategic_pillar(
            pillar_id,
            workspace_id,
            user.id,
            session,
        )
    except DomainException as e:
        # Check if it's a "not found" error
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting pillar: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete pillar")
