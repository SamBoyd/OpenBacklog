"""Product strategy API endpoints."""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from src.db import get_db
from src.main import app
from src.models import User
from src.strategic_planning import controller as product_strategy_controller
from src.strategic_planning.exceptions import DomainException
from src.views import dependency_to_override

logger = logging.getLogger(__name__)


class VisionUpdateRequest(BaseModel):
    """Request model for creating or updating a vision."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vision_text": "Build the best AI-powered task management tool for solo developers"
            }
        }
    )

    vision_text: str = Field(min_length=1, max_length=1000)


class VisionResponse(BaseModel):
    """Response model for vision."""

    model_config = ConfigDict(
        from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: uuid.UUID
    workspace_id: uuid.UUID
    vision_text: str
    created_at: datetime
    updated_at: datetime


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Developer Experience",
                "description": "Make developers love our product. Not enterprise features.",
            }
        }
    )

    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None)


class PillarResponse(BaseModel):
    """Response model for strategic pillar."""

    model_config = ConfigDict(
        from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: Optional[str]
    display_order: int
    outcome_ids: List[uuid.UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


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
        return [
            PillarResponse(
                id=pillar.id,
                workspace_id=pillar.workspace_id,
                name=pillar.name,
                description=pillar.description,
                display_order=pillar.display_order,
                outcome_ids=[outcome.id for outcome in pillar.outcomes],
                created_at=pillar.created_at,
                updated_at=pillar.updated_at,
            )
            for pillar in pillars
        ]
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
            session,
        )

        return PillarResponse(
            id=pillar.id,
            workspace_id=pillar.workspace_id,
            name=pillar.name,
            description=pillar.description,
            display_order=pillar.display_order,
            outcome_ids=[outcome.id for outcome in pillar.outcomes],
            created_at=pillar.created_at,
            updated_at=pillar.updated_at,
        )
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating pillar: {e}")
        raise HTTPException(status_code=500, detail="Failed to create pillar")


class PillarOrderItem(BaseModel):
    """Model for a single pillar order update."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "display_order": 2,
            }
        }
    )

    id: uuid.UUID
    display_order: int = Field(ge=0, le=4)


class PillarReorderRequest(BaseModel):
    """Request model for reordering strategic pillars."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pillars": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "display_order": 0,
                    },
                    {
                        "id": "223e4567-e89b-12d3-a456-426614174001",
                        "display_order": 1,
                    },
                ]
            }
        }
    )

    pillars: List[PillarOrderItem] = Field(..., min_length=1, max_length=5)


@app.put(
    "/api/workspaces/{workspace_id}/pillars/reorder",
    response_model=List[PillarResponse],
    tags=["product-strategy"],
)
async def reorder_strategic_pillars(
    workspace_id: uuid.UUID,
    request: PillarReorderRequest,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> List[PillarResponse]:
    """Reorder strategic pillars by updating their display order."""
    try:
        # Convert request to dict for controller
        pillar_orders = {item.id: item.display_order for item in request.pillars}

        pillars = product_strategy_controller.reorder_strategic_pillars(
            workspace_id,
            pillar_orders,
            session,
        )

        return [
            PillarResponse(
                id=pillar.id,
                workspace_id=pillar.workspace_id,
                name=pillar.name,
                description=pillar.description,
                display_order=pillar.display_order,
                outcome_ids=[outcome.id for outcome in pillar.outcomes],
                created_at=pillar.created_at,
                updated_at=pillar.updated_at,
            )
            for pillar in pillars
        ]
    except DomainException as e:
        # Check if it's a "not found" error
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error reordering pillars: {e}")
        raise HTTPException(status_code=500, detail="Failed to reorder pillars")


class PillarUpdateRequest(BaseModel):
    """Request model for updating a strategic pillar."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Pillar Name",
                "description": "Updated description",
            }
        }
    )

    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None)


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
            session,
        )

        return PillarResponse(
            id=pillar.id,
            workspace_id=pillar.workspace_id,
            name=pillar.name,
            description=pillar.description,
            display_order=pillar.display_order,
            outcome_ids=[outcome.id for outcome in pillar.outcomes],
            created_at=pillar.created_at,
            updated_at=pillar.updated_at,
        )
    except DomainException as e:
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
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting pillar: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete pillar")


# Product Outcome Endpoints


class OutcomeCreateRequest(BaseModel):
    """Request model for creating a product outcome."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "80% of users use AI weekly",
                "description": "Measure AI adoption as a leading indicator of value",
                "metrics": "% of weekly active users who use AI features",
                "time_horizon_months": 12,
                "pillar_ids": ["123e4567-e89b-12d3-a456-426614174000"],
            }
        }
    )

    name: str = Field(min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=1500)
    pillar_ids: List[uuid.UUID] = Field(default_factory=list)


class OutcomeResponse(BaseModel):
    """Response model for product outcome."""

    model_config = ConfigDict(
        from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: Optional[str]
    display_order: int
    pillar_ids: List[uuid.UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


@app.post(
    "/api/workspaces/{workspace_id}/outcomes",
    response_model=OutcomeResponse,
    tags=["product-strategy"],
    status_code=201,
)
async def create_product_outcome(
    workspace_id: uuid.UUID,
    request: OutcomeCreateRequest,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> OutcomeResponse:
    """Create a new product outcome for a workspace."""
    try:
        outcome = product_strategy_controller.create_product_outcome(
            workspace_id,
            user.id,
            request.name,
            request.description,
            request.pillar_ids,
            session,
        )

        return OutcomeResponse(
            id=outcome.id,
            workspace_id=outcome.workspace_id,
            name=outcome.name,
            description=outcome.description,
            display_order=outcome.display_order,
            pillar_ids=[pillar.id for pillar in outcome.pillars],
            created_at=outcome.created_at,
            updated_at=outcome.updated_at,
        )
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating outcome: {e}")
        raise HTTPException(status_code=500, detail="Failed to create outcome")


class OutcomeOrderItem(BaseModel):
    """Model for a single outcome order update."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "display_order": 2,
            }
        }
    )

    id: uuid.UUID
    display_order: int = Field(ge=0, le=9)


class OutcomeReorderRequest(BaseModel):
    """Request model for reordering product outcomes."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "outcomes": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "display_order": 0,
                    },
                    {
                        "id": "223e4567-e89b-12d3-a456-426614174001",
                        "display_order": 1,
                    },
                ]
            }
        }
    )

    outcomes: List[OutcomeOrderItem] = Field(..., min_length=1, max_length=10)


@app.put(
    "/api/workspaces/{workspace_id}/outcomes/reorder",
    response_model=List[OutcomeResponse],
    tags=["product-strategy"],
)
async def reorder_product_outcomes(
    workspace_id: uuid.UUID,
    request: OutcomeReorderRequest,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> List[OutcomeResponse]:
    """Reorder product outcomes by updating their display order."""
    try:
        # Convert request to dict for controller
        outcome_orders = {item.id: item.display_order for item in request.outcomes}

        outcomes = product_strategy_controller.reorder_product_outcomes(
            workspace_id,
            outcome_orders,
            session,
        )

        return [
            OutcomeResponse(
                id=outcome.id,
                workspace_id=outcome.workspace_id,
                name=outcome.name,
                description=outcome.description,
                display_order=outcome.display_order,
                pillar_ids=[pillar.id for pillar in outcome.pillars],
                created_at=outcome.created_at,
                updated_at=outcome.updated_at,
            )
            for outcome in outcomes
        ]
    except DomainException as e:
        # Check if it's a "not found" error
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error reordering outcomes: {e}")
        raise HTTPException(status_code=500, detail="Failed to reorder outcomes")


class OutcomeUpdateRequest(BaseModel):
    """Request model for updating a product outcome."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated outcome name",
                "description": "Updated description",
                "pillar_ids": ["123e4567-e89b-12d3-a456-426614174000"],
            }
        }
    )

    name: str = Field(min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=1500)
    pillar_ids: List[uuid.UUID] = Field(default_factory=list)


@app.put(
    "/api/workspaces/{workspace_id}/outcomes/{outcome_id}",
    response_model=OutcomeResponse,
    tags=["product-strategy"],
)
async def update_product_outcome(
    workspace_id: uuid.UUID,
    outcome_id: uuid.UUID,
    request: OutcomeUpdateRequest,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> OutcomeResponse:
    """Update an existing product outcome."""
    try:
        outcome = product_strategy_controller.update_product_outcome(
            outcome_id,
            workspace_id,
            request.name,
            request.description,
            request.pillar_ids,
            session,
        )

        return OutcomeResponse(
            id=outcome.id,
            workspace_id=outcome.workspace_id,
            name=outcome.name,
            description=outcome.description,
            display_order=outcome.display_order,
            pillar_ids=[pillar.id for pillar in outcome.pillars],
            created_at=outcome.created_at,
            updated_at=outcome.updated_at,
        )
    except DomainException as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating outcome: {e}")
        raise HTTPException(status_code=500, detail="Failed to update outcome")


@app.delete(
    "/api/workspaces/{workspace_id}/outcomes/{outcome_id}",
    status_code=204,
    tags=["product-strategy"],
)
async def delete_product_outcome(
    workspace_id: uuid.UUID,
    outcome_id: uuid.UUID,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> None:
    """Delete a product outcome."""
    try:
        product_strategy_controller.delete_product_outcome(
            outcome_id,
            workspace_id,
            user.id,
            session,
        )
    except DomainException as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting outcome: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete outcome")
