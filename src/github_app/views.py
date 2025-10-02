import hashlib
import hmac
import logging
from datetime import datetime
from typing import Annotated, Any, Dict, List

from fastapi import (
    Body,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    Security,
)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from src.config import settings
from src.db import get_db
from src.github_app import controller as github_app_controller
from src.github_app import webhook_controller
from src.main import app
from src.models import User
from src.views import dependency_to_override

# Security scheme for GitHub webhook signature validation
# auto_error=True ensures FastAPI handles missing header (403 Forbidden)
webhook_security = APIKeyHeader(name="X-Hub-Signature-256", auto_error=True)

logger = logging.getLogger(__name__)

# Removed GithubWebhookPayload - using raw dict payload for flexibility


@app.post("/github/webhook", response_class=Response)
async def github_webhook(
    request: Request,
    payload: dict = Body(...),  # Use dict instead of Pydantic model to access raw JSON
    x_hub_signature_256: str = Security(webhook_security),
    x_github_event: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> Response:
    # The webhook_security dependency (auto_error=True) handles missing X-Hub-Signature-256

    # Check for missing event header
    if not x_github_event:
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Event header")

    # Verify webhook signature
    raw_body = await request.body()
    expected_signature = (
        "sha256="
        + hmac.new(
            settings.github_webhook_secret.encode(), raw_body, hashlib.sha256
        ).hexdigest()
    )

    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    logger.info(f"Received GitHub webhook: {x_github_event}")
    logger.debug(f"GitHub webhook payload: {payload}")

    # Process the webhook with raw payload
    return webhook_controller.handle_github_webhook(payload, str(x_github_event), db)


@app.get("/repositories", response_class=HTMLResponse)
async def repositories(
    request: Request,
    user=Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return github_app_controller.get_repositories_template(request, user, db)


@app.get("/github/install", response_class=RedirectResponse)
async def github_app_install(
    request: Request, user=Depends(dependency_to_override)
) -> RedirectResponse:
    return github_app_controller.install_github_app_redirect()


@app.get("/auth/github-app-callback", response_class=Response)
async def github_app_callback(
    payload: Annotated[github_app_controller.GithubAppInstallationCallback, Query()],
    user=Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> Response:
    return github_app_controller.handle_installation_callback(payload, user, db)


@app.get("/github/uninstall", response_class=RedirectResponse)
async def github_app_uninstall(
    request: Request,
    user=Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    return github_app_controller.uninstall_github_app(user, db)


# Response models for file search string API
class FileSearchStringResponse(BaseModel):
    repository_full_name: str
    file_search_string: str
    updated_at: datetime
    success: bool

    class Config:
        from_attributes = True


class RepositoryFileData(BaseModel):
    repository_full_name: str
    file_search_string: str
    updated_at: datetime

    class Config:
        from_attributes = True


class AllFileSearchStringsResponse(BaseModel):
    repositories: List[RepositoryFileData]
    total_repositories: int
    success: bool

    class Config:
        from_attributes = True


class RepositoryNamesResponse(BaseModel):
    repository_names: List[str]
    repository_timestamps: Dict[str, str]  # repo_name -> ISO timestamp string
    total_repositories: int
    success: bool

    class Config:
        from_attributes = True


@app.get("/api/github/file-search-string", response_class=JSONResponse)
async def get_file_search_string(
    repository_full_name: str = Query(
        ..., description="Repository in owner/repo format"
    ),
    user=Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Return file search string for autocomplete"""
    try:
        result = github_app_controller.get_file_search_string_for_user(
            user, repository_full_name, db
        )
        return JSONResponse(content=result.model_dump(mode="json"))
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_file_search_string: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/github/file-search-strings", response_class=JSONResponse)
async def get_all_file_search_strings(
    user=Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Return all file search strings for user's repositories"""
    try:
        result = github_app_controller.get_all_file_search_strings_for_user(user, db)
        return JSONResponse(content=result.model_dump(mode="json"))
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_all_file_search_strings: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/github/repository-names", response_class=JSONResponse)
async def get_user_repository_names(
    user=Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Return lightweight list of repository names for cache validation"""
    try:
        result = github_app_controller.get_repository_names_for_user(user, db)
        return JSONResponse(content=result.model_dump(mode="json"))
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user_repository_names: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/github/installation-status", response_class=JSONResponse)
async def get_github_installation_status(
    user=Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Return GitHub installation status for the user"""
    try:
        result = github_app_controller.get_installation_status(user, db)
        return JSONResponse(content=result)
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_github_installation_status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
