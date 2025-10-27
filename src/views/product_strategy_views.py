"""Product strategy API endpoints."""

import logging
import uuid
from datetime import datetime
from typing import Optional

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


# Strategic Initiative Endpoints


class StrategicInitiativeCreateRequest(BaseModel):
    """Request model for creating strategic initiative context."""

    pillar_id: Optional[uuid.UUID] = Field(default=None)
    theme_id: Optional[uuid.UUID] = Field(default=None)
    user_need: Optional[str] = Field(default=None, max_length=1000)
    connection_to_vision: Optional[str] = Field(default=None, max_length=1000)
    success_criteria: Optional[str] = Field(default=None, max_length=1000)
    out_of_scope: Optional[str] = Field(default=None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "pillar_id": "123e4567-e89b-12d3-a456-426614174000",
                "theme_id": "223e4567-e89b-12d3-a456-426614174001",
                "user_need": "Solo developers need AI-powered assistance",
                "connection_to_vision": "Enables productive AI-assisted development",
                "success_criteria": "80% of users use AI weekly",
                "out_of_scope": "Team collaboration features",
            }
        }


class StrategicInitiativeResponse(BaseModel):
    """Response model for strategic initiative context."""

    id: uuid.UUID
    initiative_id: uuid.UUID
    workspace_id: uuid.UUID
    pillar_id: Optional[uuid.UUID]
    theme_id: Optional[uuid.UUID]
    user_need: Optional[str]
    connection_to_vision: Optional[str]
    success_criteria: Optional[str]
    out_of_scope: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


@app.get(
    "/api/initiatives/{initiative_id}/strategic-context",
    response_model=StrategicInitiativeResponse,
    tags=["product-strategy"],
)
async def get_initiative_strategic_context(
    initiative_id: uuid.UUID,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> StrategicInitiativeResponse:
    """Get strategic context for an initiative."""
    try:
        strategic_initiative = product_strategy_controller.get_strategic_initiative(
            initiative_id, session
        )

        if not strategic_initiative:
            raise HTTPException(
                status_code=404, detail="No strategic context found for initiative"
            )

        return StrategicInitiativeResponse.model_validate(strategic_initiative)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategic initiative: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get strategic initiative"
        )


@app.post(
    "/api/initiatives/{initiative_id}/strategic-context",
    response_model=StrategicInitiativeResponse,
    tags=["product-strategy"],
    status_code=201,
)
async def create_initiative_strategic_context(
    initiative_id: uuid.UUID,
    request: StrategicInitiativeCreateRequest,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> StrategicInitiativeResponse:
    """Create strategic context for an initiative."""
    try:
        from src.models import Initiative

        initiative = session.query(Initiative).filter_by(id=initiative_id).first()
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative not found")

        strategic_initiative = product_strategy_controller.create_strategic_initiative(
            initiative_id=initiative_id,
            workspace_id=initiative.workspace_id,
            user_id=user.id,
            pillar_id=request.pillar_id,
            theme_id=request.theme_id,
            user_need=request.user_need,
            connection_to_vision=request.connection_to_vision,
            success_criteria=request.success_criteria,
            out_of_scope=request.out_of_scope,
            session=session,
        )

        return StrategicInitiativeResponse.model_validate(strategic_initiative)
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating strategic initiative: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create strategic initiative"
        )


class StrategicInitiativeUpdateRequest(BaseModel):
    """Request model for updating strategic initiative context."""

    pillar_id: Optional[uuid.UUID] = Field(default=None)
    theme_id: Optional[uuid.UUID] = Field(default=None)
    user_need: Optional[str] = Field(default=None, max_length=1000)
    connection_to_vision: Optional[str] = Field(default=None, max_length=1000)
    success_criteria: Optional[str] = Field(default=None, max_length=1000)
    out_of_scope: Optional[str] = Field(default=None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "pillar_id": "123e4567-e89b-12d3-a456-426614174000",
                "theme_id": "223e4567-e89b-12d3-a456-426614174001",
                "user_need": "Updated user need",
                "connection_to_vision": "Updated vision connection",
                "success_criteria": "Updated success criteria",
                "out_of_scope": "Updated out of scope",
            }
        }


@app.put(
    "/api/initiatives/{initiative_id}/strategic-context",
    response_model=StrategicInitiativeResponse,
    tags=["product-strategy"],
)
async def update_initiative_strategic_context(
    initiative_id: uuid.UUID,
    request: StrategicInitiativeUpdateRequest,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> StrategicInitiativeResponse:
    """Update strategic context for an initiative."""
    try:
        strategic_initiative = product_strategy_controller.update_strategic_initiative(
            initiative_id=initiative_id,
            pillar_id=request.pillar_id,
            theme_id=request.theme_id,
            user_need=request.user_need,
            connection_to_vision=request.connection_to_vision,
            success_criteria=request.success_criteria,
            out_of_scope=request.out_of_scope,
            session=session,
        )

        return StrategicInitiativeResponse.model_validate(strategic_initiative)
    except DomainException as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating strategic initiative: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update strategic initiative"
        )
