import datetime
import logging
import uuid
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db import get_db
from src.initiative_management.task_controller import (
    ChecklistItemData,
    TaskController,
    TaskControllerError,
    TaskNotFoundError,
)
from src.main import app
from src.models import ContextType, EntityType, TaskStatus, User
from src.views import dependency_to_override

logger = logging.getLogger(__name__)


class ChecklistItemCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200, description="Checklist item title")
    is_complete: bool = Field(default=False, description="Whether item is complete")
    order: int = Field(default=0, description="Order within checklist")


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200, description="Task title")
    status: TaskStatus = Field(default=TaskStatus.TO_DO, description="Initial status")
    type: Optional[str] = Field(default=None, description="Task type")
    description: Optional[str] = Field(default=None, description="Task description")
    checklist: List[ChecklistItemCreateRequest] = Field(
        default_factory=list, description="Checklist items"
    )
    workspace_id: uuid.UUID = Field(description="Workspace ID")
    initiative_id: uuid.UUID = Field(description="Initiative ID")


class TaskMoveRequest(BaseModel):
    after_id: Optional[uuid.UUID] = Field(
        default=None, description="ID of task to move after"
    )
    before_id: Optional[uuid.UUID] = Field(
        default=None, description="ID of task to move before"
    )


class TaskStatusMoveRequest(BaseModel):
    new_status: TaskStatus = Field(description="New status for task")
    after_id: Optional[uuid.UUID] = Field(
        default=None, description="ID of task to move after"
    )
    before_id: Optional[uuid.UUID] = Field(
        default=None, description="ID of task to move before"
    )


class OrderingResponse(BaseModel):
    id: uuid.UUID
    context_type: ContextType
    context_id: Optional[uuid.UUID]
    entity_type: EntityType
    position: str

    class Config:
        from_attributes = True


class ChecklistItemResponse(BaseModel):
    id: uuid.UUID
    title: str
    is_complete: bool
    order: int
    task_id: uuid.UUID
    user_id: uuid.UUID

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: uuid.UUID
    identifier: str
    title: str
    description: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    status: TaskStatus
    type: Optional[str]
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    initiative_id: uuid.UUID
    checklist: List[ChecklistItemResponse] = Field(default_factory=list)
    orderings: List[OrderingResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


def _handle_controller_error(e: Exception) -> HTTPException:
    if isinstance(e, TaskNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    elif isinstance(e, TaskControllerError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        logger.error(f"Unexpected error: {e}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(
    request: TaskCreateRequest,
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> TaskResponse:
    try:
        controller = TaskController(db)

        # Convert checklist items to data objects
        checklist_items = [
            ChecklistItemData(
                title=item.title,
                is_complete=item.is_complete,
                order=item.order,
            )
            for item in request.checklist
        ]

        task = controller.create_task(
            title=request.title,
            user_id=user.id,
            workspace_id=request.workspace_id,
            initiative_id=request.initiative_id,
            status=request.status,
            task_type=request.type,
            description=request.description,
            checklist=checklist_items if checklist_items else None,
        )

        return TaskResponse.model_validate(task)

    except Exception as e:
        raise _handle_controller_error(e)


@app.delete("/api/tasks/{task_id}")
async def delete_task(
    task_id: uuid.UUID,
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        controller = TaskController(db)
        deleted = controller.delete_task(task_id, user.id)

        if deleted:
            return JSONResponse(content={"message": "Task deleted successfully"})
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

    except Exception as e:
        raise _handle_controller_error(e)


@app.put("/api/tasks/{task_id}/move", response_model=TaskResponse)
async def move_task(
    task_id: uuid.UUID,
    request: TaskMoveRequest,
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> TaskResponse:
    try:
        controller = TaskController(db)
        task = controller.move_task(
            task_id=task_id,
            user_id=user.id,
            after_id=request.after_id,
            before_id=request.before_id,
        )

        return TaskResponse.model_validate(task)

    except Exception as e:
        raise _handle_controller_error(e)


@app.put("/api/tasks/{task_id}/status", response_model=TaskResponse)
async def move_task_to_status(
    task_id: uuid.UUID,
    request: TaskStatusMoveRequest,
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> TaskResponse:
    try:
        controller = TaskController(db)
        task = controller.move_task_to_status(
            task_id=task_id,
            user_id=user.id,
            new_status=request.new_status,
            after_id=request.after_id,
            before_id=request.before_id,
        )

        return TaskResponse.model_validate(task)

    except Exception as e:
        raise _handle_controller_error(e)
