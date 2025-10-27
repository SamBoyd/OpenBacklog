"""Product strategy API endpoints."""

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.controllers import product_strategy_controller
from src.controllers.initiative_controller import (
    InitiativeController,
    InitiativeControllerError,
    InitiativeNotFoundError,
)
from src.db import get_db
from src.main import app
from src.models import ContextType, EntityType, InitiativeStatus, User
from src.strategic_planning.exceptions import DomainException
from src.views import dependency_to_override
from src.views.task_views import TaskResponse

logger = logging.getLogger(__name__)


# Initiative Management Endpoints


class InitiativeCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200, description="Initiative title")
    description: str | None = Field(default="", description="Initiative description")
    status: InitiativeStatus = Field(
        default=InitiativeStatus.BACKLOG, description="Initial status"
    )
    type: Optional[str] = Field(default=None, description="Initiative type")
    workspace_id: uuid.UUID = Field(description="Workspace ID")


class InitiativeMoveRequest(BaseModel):
    after_id: Optional[uuid.UUID] = Field(
        default=None, description="ID of initiative to move after"
    )
    before_id: Optional[uuid.UUID] = Field(
        default=None, description="ID of initiative to move before"
    )


class InitiativeStatusMoveRequest(BaseModel):
    new_status: InitiativeStatus = Field(description="New status for initiative")
    after_id: Optional[uuid.UUID] = Field(
        default=None, description="ID of initiative to move after"
    )
    before_id: Optional[uuid.UUID] = Field(
        default=None, description="ID of initiative to move before"
    )


class InitiativeGroupRequest(BaseModel):
    group_id: uuid.UUID = Field(description="Group ID to add initiative to")
    after_id: Optional[uuid.UUID] = Field(
        default=None, description="ID of initiative to move after in group"
    )
    before_id: Optional[uuid.UUID] = Field(
        default=None, description="ID of initiative to move before in group"
    )


class OrderingResponse(BaseModel):
    id: uuid.UUID
    context_type: ContextType
    context_id: Optional[uuid.UUID]
    entity_type: EntityType
    position: str

    class Config:
        from_attributes = True


class InitiativeResponse(BaseModel):
    id: uuid.UUID
    identifier: str
    title: str
    description: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    status: InitiativeStatus
    type: Optional[str]
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    properties: Dict[str, Any]
    orderings: List[OrderingResponse] = Field(default_factory=list)
    tasks: List[TaskResponse]

    class Config:
        from_attributes = True


def _handle_controller_error(e: Exception) -> HTTPException:
    if isinstance(e, InitiativeNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    elif isinstance(e, InitiativeControllerError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        logger.error(f"Unexpected error: {e}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@app.post("/api/initiatives", response_model=InitiativeResponse)
async def create_initiative(
    request: InitiativeCreateRequest,
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> InitiativeResponse:
    try:
        controller = InitiativeController(db)
        initiative = controller.create_initiative(
            title=request.title,
            description=request.description,
            user_id=user.id,
            workspace_id=request.workspace_id,
            status=request.status,
            initiative_type=request.type,
        )

        return InitiativeResponse.model_validate(initiative)

    except Exception as e:
        raise _handle_controller_error(e)


@app.delete("/api/initiatives/{initiative_id}")
async def delete_initiative(
    initiative_id: uuid.UUID,
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        controller = InitiativeController(db)
        deleted = controller.delete_initiative(initiative_id, user.id)

        if deleted:
            return JSONResponse(content={"message": "Initiative deleted successfully"})
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Initiative not found"
            )

    except Exception as e:
        raise _handle_controller_error(e)


@app.put("/api/initiatives/{initiative_id}/move", response_model=InitiativeResponse)
async def move_initiative(
    initiative_id: uuid.UUID,
    request: InitiativeMoveRequest,
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> InitiativeResponse:
    try:
        controller = InitiativeController(db)
        initiative = controller.move_initiative(
            initiative_id=initiative_id,
            user_id=user.id,
            after_id=request.after_id,
            before_id=request.before_id,
        )

        return InitiativeResponse.model_validate(initiative)

    except Exception as e:
        raise _handle_controller_error(e)


@app.put("/api/initiatives/{initiative_id}/status", response_model=InitiativeResponse)
async def move_initiative_to_status(
    initiative_id: uuid.UUID,
    request: InitiativeStatusMoveRequest,
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> InitiativeResponse:
    try:
        controller = InitiativeController(db)
        initiative = controller.move_initiative_to_status(
            initiative_id=initiative_id,
            user_id=user.id,
            new_status=request.new_status,
            after_id=request.after_id,
            before_id=request.before_id,
        )

        return InitiativeResponse.model_validate(initiative)

    except Exception as e:
        raise _handle_controller_error(e)


@app.put("/api/initiatives/{initiative_id}/groups", response_model=InitiativeResponse)
async def add_initiative_to_group(
    initiative_id: uuid.UUID,
    request: InitiativeGroupRequest,
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> InitiativeResponse:
    try:
        controller = InitiativeController(db)
        initiative = controller.add_initiative_to_group(
            initiative_id=initiative_id,
            user_id=user.id,
            group_id=request.group_id,
            after_id=request.after_id,
            before_id=request.before_id,
        )

        return InitiativeResponse.model_validate(initiative)

    except Exception as e:
        raise _handle_controller_error(e)


@app.delete("/api/initiatives/{initiative_id}/groups/{group_id}")
async def remove_initiative_from_group(
    initiative_id: uuid.UUID,
    group_id: uuid.UUID,
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        controller = InitiativeController(db)
        removed = controller.remove_initiative_from_group(
            initiative_id=initiative_id,
            user_id=user.id,
            group_id=group_id,
        )

        if removed:
            return JSONResponse(
                content={"message": "Initiative removed from group successfully"}
            )
        else:
            return JSONResponse(
                content={"message": "Initiative was not in the specified group"}
            )

    except Exception as e:
        raise _handle_controller_error(e)


@app.put(
    "/api/initiatives/{initiative_id}/groups/{group_id}/move",
    response_model=InitiativeResponse,
)
async def move_initiative_in_group(
    initiative_id: uuid.UUID,
    group_id: uuid.UUID,
    request: InitiativeMoveRequest,
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> InitiativeResponse:
    try:
        controller = InitiativeController(db)
        initiative = controller.move_initiative_in_group(
            initiative_id=initiative_id,
            user_id=user.id,
            group_id=group_id,
            after_id=request.after_id,
            before_id=request.before_id,
        )

        return InitiativeResponse.model_validate(initiative)

    except Exception as e:
        raise _handle_controller_error(e)


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
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime.datetime: lambda v: v.isoformat()}


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
