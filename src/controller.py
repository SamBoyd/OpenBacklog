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
from src.ai.openai_service import _validate_openai_key
from src.config import settings
from src.github_app.github_service import GitHubService
from src.key_vault import retrieve_api_key_from_vault, store_api_key_in_vault
from src.litellm_service import (
    create_litellm_user,
    get_litellm_user_info,
    retrieve_litellm_master_key,
)
from src.main import templates
from src.models import APIProvider, GitHubInstallation, User, UserKey, Workspace

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


def get_changelog_template(request, user):
    return templates.TemplateResponse(
        request,
        "pages/changelog.html",
        {
            "user": user,
            "request": request,
        },
    )


def get_support_template(request, user):
    return templates.TemplateResponse(
        request,
        "pages/support.html",
        {
            "user": user,
            "request": request,
            "static_site_url": settings.static_site_url,
            "support_email": settings.support_email_address,
            "github_repo_url": settings.github_repo_url,
            "discord_invite_link": settings.discord_invite_link,
            "reddit_launch_thread_url": settings.reddit_launch_thread_url,
        },
    )


def get_account_template(request, user: User, session: Session):
    workspaces = session.query(Workspace).filter(Workspace.user_id == user.id).all()

    openbacklog_tokens = get_openbacklog_tokens_for_user(user, session)

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
            "openbacklog_tokens": openbacklog_tokens,
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


# Tuple describing the number of characters to leave unredacted at the beginning and end of a string
# when redacting sensitive information.
NUM_CHARS_TO_LEAVE_UNREDACTED = (3, 4)


def update_openai_key(key: str, user: User, db: Session):
    """
    Validates and updates the OpenAI API key for a user.

    Validates the key with OpenAI, then creates or updates a UserKey record
    with a redacted version and stores the full version in HashiCorp Vault.
    Updates validation status in the database.

    Args:
        key (str): The OpenAI API key to store
        user (User): The user to update
        db (Session): Database session

    Returns:
        dict: A message indicating success

    Raises:
        HTTPException: If the API key is invalid or validation fails
        RuntimeError: If storing the key in Vault fails
    """
    # Validate the key first
    if not _validate_openai_key(key):
        raise HTTPException(status_code=400, detail="Invalid OpenAI API key provided")

    # Check if user already has an OpenAI key
    user_key = (
        db.query(UserKey)
        .filter(UserKey.user_id == user.id, UserKey.provider == APIProvider.OPENAI)
        .first()
    )

    # Store original values for rollback if needed
    original_redacted_key = user_key.redacted_key if user_key else None
    original_is_valid = user_key.is_valid if user_key else None
    original_validated_at = user_key.last_validated_at if user_key else None

    try:
        # Generate redacted version for display
        redacted_key = (
            key[: NUM_CHARS_TO_LEAVE_UNREDACTED[0]]
            + "***"
            + key[-NUM_CHARS_TO_LEAVE_UNREDACTED[1] :]
        )

        # Current time with timezone for validation timestamp
        now = datetime.now(timezone.utc)

        # Create or update UserKey with validation info
        if not user_key:
            user_key = UserKey(
                user_id=user.id,
                provider=APIProvider.OPENAI,
                redacted_key=redacted_key,
                is_valid=True,  # Key was successfully validated
                last_validated_at=now,
            )
        else:
            user_key.redacted_key = redacted_key
            user_key.is_valid = True
            user_key.last_validated_at = now

        db.add(user_key)
        db.commit()
        db.refresh(user_key)

        # Store in Vault
        vault_path = user_key.vault_path
        stored_path = store_api_key_in_vault(vault_path, key)
        if stored_path is None:
            logger.warning(
                f"Vault unavailable, OpenAI key for user {user.id} stored in DB but not in vault"
            )

        return {"message": "OpenAI key updated and validated successfully"}
    except Exception as e:
        # Rollback DB changes if something went wrong after validation
        db.rollback()

        # Try to restore previous state if this is an update
        if user_key and original_redacted_key is not None:
            existing_user_key = db.query(UserKey).filter_by(id=user_key.id).first()
            if existing_user_key:
                existing_user_key.redacted_key = original_redacted_key
                existing_user_key.is_valid = original_is_valid
                existing_user_key.last_validated_at = original_validated_at
                db.add(existing_user_key)
                db.commit()

        logger.error(f"Failed to store API key after validation: {e}")
        raise RuntimeError(f"Failed to store API key after validation: {str(e)}") from e


def get_openai_key_from_vault(user: User, db: Session) -> str:
    """
    Retrieves the OpenAI API key for a user.

    Args:
        user (User): The user to retrieve the key for

    Returns:
        str: The OpenAI API key
    """
    user_key = (
        db.query(UserKey)
        .filter(UserKey.user_id == user.id, UserKey.provider == APIProvider.OPENAI)
        .first()
    )

    if not user_key:
        raise RuntimeError("User does not have an OpenAI key")

    api_key = retrieve_api_key_from_vault(user_key.vault_path)
    if api_key is None:
        raise RuntimeError("Could not retrieve OpenAI key - vault service unavailable")

    return api_key


def create_litellm_user_and_key(user: User, db: Session):
    """
    Creates a new LiteLLM user and key for a user.

    Args:
        user (User): The user to update
        db (Session): Database session

    Returns:
        dict: A message indicating success

    Raises:
        HTTPException: If the API key is invalid or validation fails
        RuntimeError: If storing the key in Vault fails
    """

    master_key = retrieve_litellm_master_key()
    if not master_key:
        raise HTTPException(status_code=400, detail="LiteLLM master key not found")

    # Ensure the user doesnt already have a LiteLLM user & key
    try:
        user_info = get_litellm_user_info(user, master_key)
        if user_info["keys"] != []:
            return {"message": "LiteLLM user & key already exist"}
    except ValueError as e:
        # User doesnt have a LiteLLM user, so we can create one
        pass
        # TODO probably a better way to handle this
    except Exception as e:
        logger.error(f"Failed to get LiteLLM user info: {e}")
        raise HTTPException(
            status_code=400, detail="Failed to get LiteLLM user info"
        ) from e

    # Check if user already has a UserKey record for LiteLLM
    user_key = (
        db.query(UserKey)
        .filter(UserKey.user_id == user.id, UserKey.provider == APIProvider.LITELLM)
        .first()
    )
    if user_key is not None:
        return {"message": "LiteLLM user & key already exist"}
    # Create the LiteLLM user
    key = create_litellm_user(user, master_key)

    # Generate redacted version for display
    redacted_key = (
        key[: NUM_CHARS_TO_LEAVE_UNREDACTED[0]]
        + "..."
        + key[-NUM_CHARS_TO_LEAVE_UNREDACTED[1] :]
    )

    # Create or update UserKey with validation info
    user_key = UserKey(
        user_id=user.id,
        provider=APIProvider.LITELLM,
        redacted_key=redacted_key,
        is_valid=True,
        last_validated_at=datetime.now(timezone.utc),
    )

    db.add(user_key)
    db.commit()
    db.refresh(user_key)

    # Store in Vault
    vault_path = user_key.vault_path
    stored_path = store_api_key_in_vault(vault_path, key)
    if stored_path is None:
        logger.warning(
            f"Vault unavailable, LiteLLM key for user {user.id} stored in DB but not in vault"
        )

    return {"message": "LiteLLM user & key created successfully"}


def create_openbacklog_token(user: User, db: Session) -> dict:
    """
    Create a new OpenBacklog Personal Access Token for a user.

    Args:
        user (User): The user to create the token for
        db (Session): Database session

    Returns:
        dict: Contains the full token (only returned once) and metadata

    Raises:
        HTTPException: If token creation fails
    """
    from src.auth.jwt_utils import create_unified_jwt

    try:
        # Current time with timezone
        now = datetime.now(timezone.utc)

        # Create UserKey record first to get the key ID
        user_key = UserKey(
            user_id=user.id,
            provider=APIProvider.OPENBACKLOG,
            redacted_key="",  # Will be set after JWT creation
            is_valid=True,
            last_validated_at=now,
            last_used_at=None,  # Will be set when first used
        )

        db.add(user_key)
        db.flush()  # Get the ID without committing

        # Create a JWT token with the key ID for tracking
        # Set to 1 year for PATs (31536000 seconds)
        token = create_unified_jwt(
            user, lifetime_seconds=31536000, key_id=str(user_key.id)
        )

        # Generate redacted version for display
        redacted_token = (
            token[: NUM_CHARS_TO_LEAVE_UNREDACTED[0]]
            + "***"
            + token[-NUM_CHARS_TO_LEAVE_UNREDACTED[1] :]
        )

        # Update the user_key with redacted token and store full token in access_token
        user_key.redacted_key = redacted_token
        user_key.access_token = token  # Store full JWT for identification

        db.commit()
        db.refresh(user_key)

        # Store full token in Vault for future retrieval if needed
        vault_path = user_key.vault_path
        stored_path = store_api_key_in_vault(vault_path, token)
        if stored_path is None:
            logger.warning(
                f"Vault unavailable, OpenBacklog token for user {user.id} stored in DB but not in vault"
            )

        return {
            "message": "OpenBacklog token created successfully",
            "token": token,  # Full token returned only once
            "token_id": str(user_key.id),
            "redacted_key": redacted_token,
            "created_at": now.isoformat(),
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create OpenBacklog token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create token: {str(e)}")


def delete_openbacklog_token(user: User, token_id: str, db: Session) -> dict:
    """
    Delete an OpenBacklog token for a user.

    Args:
        user (User): The user who owns the token
        token_id (str): The ID of the token to delete
        db (Session): Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If token not found or deletion fails
    """
    try:
        # Find the token
        user_key = (
            db.query(UserKey)
            .filter(
                UserKey.id == token_id,
                UserKey.user_id == user.id,
                UserKey.provider == APIProvider.OPENBACKLOG,
            )
            .first()
        )

        if not user_key:
            raise HTTPException(status_code=404, detail="Token not found")

        # Remove from vault
        try:
            vault_path = user_key.vault_path
            # Note: We could implement vault deletion here if needed
            # For now, we'll just mark as invalid in the database
        except Exception as e:
            logger.warning(f"Failed to remove token from vault: {e}")

        # Soft delete: mark as invalid and set deleted_at timestamp
        user_key.is_valid = False
        user_key.deleted_at = datetime.now(timezone.utc)

        db.add(user_key)
        db.commit()

        return {"message": "Token deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete OpenBacklog token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete token: {str(e)}")


def get_openbacklog_tokens_for_user(user: User, db: Session) -> list:
    """
    Get all OpenBacklog tokens for a user with metadata.

    Args:
        user (User): The user to get tokens for
        db (Session): Database session

    Returns:
        list: List of token metadata (no full tokens included)
    """
    user_keys = (
        db.query(UserKey)
        .filter(
            UserKey.user_id == user.id,
            UserKey.provider == APIProvider.OPENBACKLOG,
            UserKey.is_valid == True,
            UserKey.deleted_at.is_(None),
        )
        .order_by(UserKey.last_validated_at.desc())
        .all()
    )

    tokens = []
    for key in user_keys:
        tokens.append(
            {
                "id": str(key.id),
                "redacted_key": key.redacted_key,
                "created_at": (
                    key.last_validated_at.strftime("%Y-%m-%d %H:%M")
                    if key.last_validated_at
                    else None
                ),
                "last_used_at": (
                    key.last_used_at.strftime("%Y-%m-%d %H:%M")
                    if key.last_used_at
                    else None
                ),
                "is_valid": key.is_valid,
            }
        )

    return tokens
