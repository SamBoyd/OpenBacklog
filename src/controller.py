import io
import json
import logging
import sys
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

import requests
from fastapi import HTTPException, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from src import storage_service
from src.config import settings
from src.github_app.github_service import GitHubService
from src.main import templates
from src.models import GitHubInstallation, User, UserAccountDetails, Workspace

if TYPE_CHECKING:
    from src.api import WorkspaceUpdate

logger = logging.getLogger(__name__)

PARAMS_FOR_LOGIN_SCRIPT = {
    "app_domain": settings.app_domain,
    "api_audience": settings.auth0_audience,
    "scope": "openid profile email offline_access",
    "client_id": settings.auth0_client_id,
    "redirect_uri": f"{settings.app_url}/auth/auth0/callback",
    "state": "random_state",
}

ASSETS_FILE_PATH = "static/react-components/webpack-assets.json"


def get_main_js_path() -> str:
    """
    Retrieves the path to the main.js file from the webpack-assets.json file.

    Returns:
        str: The path to the main.js file.
    """
    try:
        with open(ASSETS_FILE_PATH, "r") as f:
            assets = json.load(f)
        main_js_path = assets.get("main", {}).get("js")
        if not main_js_path:
            logger.error("Could not find 'main.js' path in webpack-assets.json")
            # Fallback or raise an error, depending on desired behavior
            main_js_path = "/js/main.js"  # Example fallback
    except FileNotFoundError:
        logger.error(f"webpack-assets.json not found at {ASSETS_FILE_PATH}")
        # Fallback or raise an error
        main_js_path = "/js/main.js"  # Example fallback
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {ASSETS_FILE_PATH}")
        # Fallback or raise an error
        main_js_path = "/js/main.js"  # Example fallback

    return main_js_path


MAIN_JS_FILEPATH = get_main_js_path()


def get_react_app(request, user):
    return templates.TemplateResponse(
        request,
        "pages/app.html",
        {"user": user, "main_js_path": MAIN_JS_FILEPATH},
    )


def get_landing_page(request, user=None):
    return templates.TemplateResponse(
        request,
        "pages/landing_page.html",
        {"user": user},
    )


def get_changelog_template(request, user):
    return templates.TemplateResponse(
        request,
        "pages/changelog.html",
        {
            "user": user,
            "request": request,
        },
    )


def get_account_template(request, user: User, session: Session):
    workspaces = session.query(Workspace).filter(Workspace.user_id == user.id).all()

    # Check if user has a GitHub installation
    github_installation = (
        session.query(GitHubInstallation)
        .filter(GitHubInstallation.user_id == user.id)
        .first()
    )

    repositories = []
    if github_installation:
        repositories = GitHubService.get_user_repositories(
            github_installation.installation_id
        )

    return templates.TemplateResponse(
        request,
        "pages/account.html",
        {
            "user": user,
            "oauth_accounts": user.oauth_accounts,
            "workspaces": workspaces,
            "mcp_server_domain": settings.mcp_server_domain,
            "has_github_installation": github_installation is not None,
            "repositories": repositories,
        },
    )


def get_profile_picture(filename) -> FileResponse:
    return FileResponse(storage_service.get_profile_picture(filename))


def upload_profile_picture(user: User, file, db: Session) -> Response:
    FILE_MAX_SIZE = 1024 * 1024 * 2  # 2MB

    # Determine if 'file' is an UploadFile or a path string and create a file-like object
    if isinstance(file, UploadFile):
        file_obj = file.file
        if file.size is None or file.size > FILE_MAX_SIZE:
            return Response(status_code=400, content="Invalid file size")

        if file.content_type != "image/png":
            return Response(status_code=400, content="Invalid file type")

        logger.error(f"File object: {file.__dict__}")
    else:
        logger.error(f"File path: {file}")
        file_obj = open(str(file), "rb")

    logger.error(f"Uploading profile picture for user {user.id}")

    filename = storage_service.upload_profile_picture(user, file_obj)

    user.profile_picture_url = filename

    # Merge user instance and commit changes
    merged_user = db.merge(user)
    db.commit()
    db.refresh(merged_user)

    return Response(
        status_code=201, content=f"Profile picture uploaded for user {merged_user.id}"
    )


def copy_auth0_provided_profile_picture(
    user: User, profile_picture_url: str, db: Session
):
    if (
        profile_picture_url is None
        or user.profile_picture_url != settings.default_profile_picture
    ):
        return

    # Download the profile picture file from Auth0
    picture_to_copy = requests.get(
        profile_picture_url, timeout=settings.internal_request_timeout
    )
    if picture_to_copy.status_code != 200:
        return

    filename = storage_service.upload_profile_picture(
        user, io.BytesIO(picture_to_copy.content)
    )
    # filename = storage_service.upload_profile_picture(user, picture_to_copy.content)
    user.profile_picture_url = filename
    merged_user = db.merge(user)
    db.commit()
    db.refresh(merged_user)


def update_user(user: User, name: Optional[str], db: Session) -> User:
    if name:
        user.name = name  # type: ignore

    merged_user = db.merge(user)
    db.commit()
    db.refresh(merged_user)
    return merged_user


def get_display_pref(user: User, db: Session):
    return user.display_preferences


def update_display_pref(user: User, field: str, value: str, db: Session):
    user.display_preferences[field] = value
    merged_user = db.merge(user)
    db.commit()
    db.refresh(merged_user)


def get_delete_account_template(request: Request, user: User):
    return templates.TemplateResponse(
        request,
        "pages/delete_account.html",
        {"user": user, "csrf_token": request.session.get_csrf_token()},  # type: ignore
    )


def confirm_delete_account(user: User, reason: str, db: Session) -> None:
    # Log the deletion reason to stdout
    print(f"Deleting user {user.id} because: {reason}", file=sys.stdout)
    # Delete the user
    merged_user = db.merge(user)
    db.commit()
    db.delete(merged_user)
    db.commit()


def create_workspace(
    user: User, name: str, description: str | None, icon: str | None, db: Session
) -> Workspace:
    """Create a new workspace with required dependencies.

    The SQLAlchemy event listener will automatically create:
    - PrioritizedRoadmap (empty prioritized_theme_ids list)
    - ProductVision (empty vision_text)

    Args:
        user: The user creating the workspace
        name: Workspace name (required)
        description: Workspace description (optional)
        icon: Workspace icon filename (optional)
        db: Database session

    Returns:
        The created Workspace instance with all dependencies
    """
    workspace = Workspace(
        name=name,
        description=description,
        icon=icon,
        user_id=user.id,
    )
    db.add(workspace)
    db.commit()  # Event listener fires here and creates dependencies
    db.refresh(workspace)
    return workspace


def update_workspace(
    user: User, workspace_update: "WorkspaceUpdate", db: Session
) -> Workspace:
    workspace = db.query(Workspace).filter(Workspace.id == workspace_update.id).first()
    if workspace is None:
        raise ValueError(f"Workspace with id {workspace_update.id} not found")

    if workspace.user_id != user.id:
        raise ValueError(f"Workspace with id {workspace_update.id} not found")

    workspace.name = workspace_update.name
    if workspace_update.description:
        workspace.description = workspace_update.description
    if workspace_update.icon:
        workspace.icon = workspace_update.icon

    merged_workspace = db.merge(workspace)
    db.commit()
    db.refresh(merged_workspace)
    return merged_workspace


def delete_workspace(user: User, workspace_id: str, db: Session):
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace is None:
        raise ValueError(f"Workspace with id {workspace_id} not found")

    if workspace.user_id != user.id:
        raise ValueError(f"Workspace with id {workspace_id} not found")

    db.delete(workspace)
    db.commit()


def complete_onboarding(user: User, db: Session) -> UserAccountDetails:
    """
    Mark onboarding as completed

    This allows users to complete onboarding and access task management features
    without signing up for a paid subscription (free tier).

    Args:
        user: The user completing onboarding
        db: Database session

    Returns:
        Updated UserAccountDetails with onboarding_completed=True and status=NO_SUBSCRIPTION
    """
    account_details = user.account_details

    # Mark onboarding as completed
    account_details.onboarding_completed = True
    db.add(account_details)
    db.commit()
    db.refresh(account_details)
    return account_details
