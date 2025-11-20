""" API endpoints."""

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
from src.roadmap_intelligence import controller
from src.strategic_planning.exceptions import DomainException
from src.views import dependency_to_override

logger = logging.getLogger(__name__)


class ThemeCreateRequest(BaseModel):
    """Request model for creating a roadmap theme."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "First Week Magic",
                "description": "Users fail to integrate in first week. Quick wins drive adoption. % users active in week 1",
                "outcome_ids": ["123e4567-e89b-12d3-a456-426614174000"],
            }
        }
    )

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    outcome_ids: List[uuid.UUID] = Field(default_factory=list)


class ThemeResponse(BaseModel):
    """Response model for roadmap theme."""

    model_config = ConfigDict(
        from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str
    outcome_ids: List[uuid.UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


@app.get(
    "/api/workspaces/{workspace_id}/themes",
    response_model=List[ThemeResponse],
    tags=["product-strategy"],
)
async def get_workspace_themes(
    workspace_id: uuid.UUID,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> List[ThemeResponse]:
    """Get all roadmap themes for a workspace."""
    try:
        themes = controller.get_roadmap_themes(workspace_id, session)
        return [
            ThemeResponse(
                id=theme.id,
                workspace_id=theme.workspace_id,
                name=theme.name,
                description=theme.description,
                outcome_ids=[outcome.id for outcome in theme.outcomes],
                created_at=theme.created_at,
                updated_at=theme.updated_at,
            )
            for theme in themes
        ]
    except Exception as e:
        logger.error(f"Error getting themes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get themes")


@app.post(
    "/api/workspaces/{workspace_id}/themes",
    response_model=ThemeResponse,
    tags=["product-strategy"],
    status_code=201,
)
async def create_roadmap_theme(
    workspace_id: uuid.UUID,
    request: ThemeCreateRequest,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> ThemeResponse:
    """Create a new roadmap theme for a workspace."""
    try:
        theme = controller.create_roadmap_theme(
            workspace_id,
            user.id,
            request.name,
            request.description,
            request.outcome_ids,
            session,
        )

        return ThemeResponse(
            id=theme.id,
            workspace_id=theme.workspace_id,
            name=theme.name,
            description=theme.description,
            outcome_ids=[outcome.id for outcome in theme.outcomes],
            created_at=theme.created_at,
            updated_at=theme.updated_at,
        )
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating theme: {e}")
        raise HTTPException(status_code=500, detail="Failed to create theme")


class ThemeOrderItem(BaseModel):
    """Model for a single theme order update."""

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


class ThemeReorderRequest(BaseModel):
    """Request model for reordering roadmap themes."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "themes": [
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

    themes: List[ThemeOrderItem] = Field(..., min_length=1, max_length=5)


@app.put(
    "/api/workspaces/{workspace_id}/themes/reorder",
    response_model=List[ThemeResponse],
    tags=["product-strategy"],
)
async def reorder_roadmap_themes(
    workspace_id: uuid.UUID,
    request: ThemeReorderRequest,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> List[ThemeResponse]:
    """Reorder prioritized roadmap themes.

    Note: Only prioritized themes can be reordered. Themes must first be prioritized
    using the /prioritize endpoint. Including unprioritized themes will result in an error.
    """
    try:
        # Convert request to dict for controller
        theme_orders = {item.id: item.display_order for item in request.themes}

        themes = controller.reorder_roadmap_themes(
            workspace_id,
            theme_orders,
            session,
        )

        return [
            ThemeResponse(
                id=theme.id,
                workspace_id=theme.workspace_id,
                name=theme.name,
                description=theme.description,
                outcome_ids=[outcome.id for outcome in theme.outcomes],
                created_at=theme.created_at,
                updated_at=theme.updated_at,
            )
            for theme in themes
        ]
    except DomainException as e:
        # Check if it's a "not found" error
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error reordering themes: {e}")
        raise HTTPException(status_code=500, detail="Failed to reorder themes")


class ThemeUpdateRequest(BaseModel):
    """Request model for updating a roadmap theme."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated theme name",
                "description": "Updated description",
                "outcome_ids": ["123e4567-e89b-12d3-a456-426614174000"],
            }
        }
    )

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    outcome_ids: List[uuid.UUID] = Field(default_factory=list)


@app.put(
    "/api/workspaces/{workspace_id}/themes/{theme_id}",
    response_model=ThemeResponse,
    tags=["product-strategy"],
)
async def update_roadmap_theme(
    workspace_id: uuid.UUID,
    theme_id: uuid.UUID,
    request: ThemeUpdateRequest,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> ThemeResponse:
    """Update an existing roadmap theme."""
    try:
        theme = controller.update_roadmap_theme(
            theme_id,
            workspace_id,
            request.name,
            request.description,
            request.outcome_ids,
            session,
        )

        return ThemeResponse(
            id=theme.id,
            workspace_id=theme.workspace_id,
            name=theme.name,
            description=theme.description,
            outcome_ids=[outcome.id for outcome in theme.outcomes],
            created_at=theme.created_at,
            updated_at=theme.updated_at,
        )
    except DomainException as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating theme: {e}")
        raise HTTPException(status_code=500, detail="Failed to update theme")


@app.delete(
    "/api/workspaces/{workspace_id}/themes/{theme_id}",
    status_code=204,
    tags=["product-strategy"],
)
async def delete_roadmap_theme(
    workspace_id: uuid.UUID,
    theme_id: uuid.UUID,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> None:
    """Delete a roadmap theme."""
    try:
        controller.delete_roadmap_theme(
            theme_id,
            workspace_id,
            user.id,
            session,
        )
    except DomainException as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting theme: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete theme")


# Theme Prioritization Endpoints


@app.get(
    "/api/workspaces/{workspace_id}/themes/prioritized",
    response_model=List[ThemeResponse],
    tags=["product-strategy"],
)
async def get_prioritized_themes(
    workspace_id: uuid.UUID,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> List[ThemeResponse]:
    """Get all prioritized themes for a workspace in priority order.

    Prioritized themes are those currently being actively worked on.
    """
    try:
        themes = controller.get_prioritized_themes(workspace_id, session)
        return [
            ThemeResponse(
                id=theme.id,
                workspace_id=theme.workspace_id,
                name=theme.name,
                description=theme.description,
                outcome_ids=[outcome.id for outcome in theme.outcomes],
                created_at=theme.created_at,
                updated_at=theme.updated_at,
            )
            for theme in themes
        ]
    except Exception as e:
        logger.error(f"Error getting prioritized themes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get prioritized themes")


@app.get(
    "/api/workspaces/{workspace_id}/themes/unprioritized",
    response_model=List[ThemeResponse],
    tags=["product-strategy"],
)
async def get_unprioritized_themes(
    workspace_id: uuid.UUID,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> List[ThemeResponse]:
    """Get all unprioritized (backlog) themes for a workspace.

    Unprioritized themes are in the backlog and not currently being worked on.
    """
    try:
        themes = controller.get_unprioritized_themes(workspace_id, session)
        return [
            ThemeResponse(
                id=theme.id,
                workspace_id=theme.workspace_id,
                name=theme.name,
                description=theme.description,
                outcome_ids=[outcome.id for outcome in theme.outcomes],
                created_at=theme.created_at,
                updated_at=theme.updated_at,
            )
            for theme in themes
        ]
    except Exception as e:
        logger.error(f"Error getting unprioritized themes: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get unprioritized themes"
        )


class ThemePrioritizeRequest(BaseModel):
    """Request model for prioritizing a theme."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "position": 0,
            }
        }
    )

    position: int = Field(ge=0, description="Position in the priority list (0-indexed)")


@app.post(
    "/api/workspaces/{workspace_id}/themes/{theme_id}/prioritize",
    response_model=ThemeResponse,
    tags=["product-strategy"],
)
async def prioritize_theme(
    workspace_id: uuid.UUID,
    theme_id: uuid.UUID,
    request: ThemePrioritizeRequest,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> ThemeResponse:
    """Add a theme to the prioritized roadmap at the specified position.

    Moves a theme from the backlog to active work.
    """
    try:
        theme = controller.prioritize_roadmap_theme(
            theme_id,
            request.position,
            workspace_id,
            session,
        )

        return ThemeResponse(
            id=theme.id,
            workspace_id=theme.workspace_id,
            name=theme.name,
            description=theme.description,
            outcome_ids=[outcome.id for outcome in theme.outcomes],
            created_at=theme.created_at,
            updated_at=theme.updated_at,
        )
    except DomainException as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error prioritizing theme: {e}")
        raise HTTPException(status_code=500, detail="Failed to prioritize theme")


@app.post(
    "/api/workspaces/{workspace_id}/themes/{theme_id}/deprioritize",
    response_model=ThemeResponse,
    tags=["product-strategy"],
)
async def deprioritize_theme(
    workspace_id: uuid.UUID,
    theme_id: uuid.UUID,
    user: User = Depends(dependency_to_override),
    session: Session = Depends(get_db),
) -> ThemeResponse:
    """Remove a theme from the prioritized roadmap.

    Moves a theme from active work back to the backlog.
    """
    try:
        theme = controller.deprioritize_roadmap_theme(
            theme_id,
            workspace_id,
            session,
        )

        return ThemeResponse(
            id=theme.id,
            workspace_id=theme.workspace_id,
            name=theme.name,
            description=theme.description,
            outcome_ids=[outcome.id for outcome in theme.outcomes],
            created_at=theme.created_at,
            updated_at=theme.updated_at,
        )
    except DomainException as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deprioritizing theme: {e}")
        raise HTTPException(status_code=500, detail="Failed to deprioritize theme")
