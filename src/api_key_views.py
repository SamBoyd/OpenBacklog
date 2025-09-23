import logging

from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src import controller
from src.auth import auth_module
from src.db import get_db
from src.main import app

logger = logging.getLogger(__name__)

dependency_to_override = auth_module.require_auth


@app.post("/api/openbacklog/tokens", response_class=JSONResponse)
async def create_openbacklog_token(
    user=Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Create a new OpenBacklog Personal Access Token."""
    try:
        result = controller.create_openbacklog_token(user, db)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error creating OpenBacklog token: {e}")
        raise HTTPException(status_code=500, detail="Failed to create token")


@app.get("/api/openbacklog/tokens", response_class=JSONResponse)
async def get_openbacklog_tokens(
    user=Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Get all OpenBacklog tokens for the current user."""
    try:
        tokens = controller.get_openbacklog_tokens_for_user(user, db)
        return JSONResponse(content={"tokens": tokens})
    except Exception as e:
        logger.error(f"Error getting OpenBacklog tokens: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tokens")


@app.delete("/api/openbacklog/tokens/{token_id}", response_class=JSONResponse)
async def delete_openbacklog_token(
    token_id: str,
    user=Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Delete an OpenBacklog token."""
    try:
        result = controller.delete_openbacklog_token(user, token_id, db)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting OpenBacklog token: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete token")
