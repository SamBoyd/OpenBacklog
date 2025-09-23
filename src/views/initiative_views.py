import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.controllers.initiative_controller import (
    InitiativeController,
    InitiativeControllerError,
    InitiativeNotFoundError,
)
from src.db import get_db
from src.main import app
from src.models import ContextType, EntityType, InitiativeStatus, Task, User
from src.views import dependency_to_override
from src.views.task_views import TaskResponse

logger = logging.getLogger(__name__)


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
