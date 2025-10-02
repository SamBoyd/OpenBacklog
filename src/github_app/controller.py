from typing import Annotated, Any, Dict, List

import sentry_sdk
from fastapi import HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.config import settings
from src.github_app.github_service import GitHubService
from src.github_app.models import RepositoryFileIndex

# Import helper functions from webhook_controller (avoiding circular imports)
from src.github_app.webhook_controller import _create_repository_file_index
from src.main import templates
from src.models import GitHubInstallation, User


def get_repositories_template(request: Request, user: User, db: Session):
    # Check if user has a GitHub installation
    github_installation = (
        db.query(GitHubInstallation)
        .filter(GitHubInstallation.user_id == user.id)
        .first()
    )

    repositories: List[Dict[str, Any]] = []
    if github_installation:
        repositories = GitHubService.get_user_repositories(
            github_installation.installation_id
        )

    return templates.TemplateResponse(
        request,
        "pages/repositories.html",
        {
            "user": user,
            "has_github_installation": github_installation is not None,
            "repositories": repositories,
        },
    )


def install_github_app_redirect() -> RedirectResponse:
    github_install_url = (
        f"https://github.com/apps/{settings.github_app_name}/installations/new"
    )
    return RedirectResponse(github_install_url)


class GithubAppInstallationCallback(BaseModel):
    installation_id: str
    code: str
    setup_action: str


def populate_initial_file_index(
    github_installation: GitHubInstallation, session: Session
) -> None:
    """
    Populate initial file index for all accessible repositories.

    This function is called during GitHub installation to provide immediate
    autocomplete functionality. It's designed to be non-blocking - failures
    won't prevent successful installation.

    Args:
        github_installation: The GitHub installation record
        session: Database session (same as installation creation)
    """
    try:
        # Get accessible repositories
        repositories = GitHubService.get_user_repositories(
            github_installation.installation_id
        )

        if not repositories:
            # No repositories accessible, skip file indexing
            return

        # Create file indexes for all accessible repositories using the helper function
        success_count = 0
        for repo in repositories:
            try:
                repo_full_name = repo.get("full_name")
                if repo_full_name:
                    # Use the reusable helper function to create file index
                    # Pass commit=True to ensure records are available for prefixing strategy update
                    if _create_repository_file_index(
                        github_installation.installation_id,
                        repo_full_name,
                        session,
                        commit=True,
                    ):
                        success_count += 1

            except Exception as e:
                # Non-blocking: Log error but continue with other repositories
                sentry_sdk.capture_exception(e)
                continue

        # Update prefixing strategy to ensure consistent @ prefixing across all repositories
        # This fixes the issue where the first repo gets single-repo prefixing while
        # subsequent repos get multi-repo prefixing during initial installation
        if success_count > 0:
            from src.github_app.webhook_controller import _update_prefixing_strategy

            _update_prefixing_strategy(github_installation.installation_id, session)

    except Exception as e:
        # Non-blocking: Log error but don't fail installation
        sentry_sdk.capture_exception(e)
        pass


def handle_installation_callback(
    callback_payload: Annotated[GithubAppInstallationCallback, Query()],
    user: User,
    session: Session,
) -> Response:
    user = session.merge(user)  # merge user to attach it to the current session

    # Verify the installation exists and is accessible by attempting to get a token
    try:
        GitHubService.get_installation_token(callback_payload.installation_id)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=400,
            detail="Invalid installation ID or installation not accessible",
        )

    # Check if installation already exists in database
    existing_installation = (
        session.query(GitHubInstallation)
        .filter(GitHubInstallation.installation_id == callback_payload.installation_id)
        .first()
    )

    if existing_installation:
        # Update existing installation with current user if different
        if existing_installation.user_id != user.id:
            existing_installation.user_id = user.id
            existing_installation.user = user
            session.commit()
        github_installation = existing_installation
    else:
        # Create new installation
        github_installation = GitHubInstallation(
            user=user, installation_id=callback_payload.installation_id
        )
        session.add(github_installation)
        session.commit()
        session.refresh(github_installation)

    # Populate initial file index for immediate autocomplete functionality
    populate_initial_file_index(github_installation, session)
    session.commit()  # Commit file index changes

    # Redirect based on onboarding status
    # If user hasn't completed onboarding, return them to the onboarding flow
    # Otherwise, redirect to account settings
    if not user.account_details.onboarding_completed:
        return RedirectResponse(url="/workspace/onboarding", status_code=302)
    else:
        return RedirectResponse(url="/account", status_code=302)


def uninstall_github_app(user: User, db: Session) -> RedirectResponse | HTTPException:
    """
    Revoke GitHub app access for the current user.

    Args:
        user: The current user
        db: Database session

    Returns:
        RedirectResponse: Redirect to repositories page
    """
    # Find the user's GitHub installation
    github_installation = (
        db.query(GitHubInstallation)
        .filter(GitHubInstallation.user_id == user.id)
        .first()
    )

    # If an installation exists, revoke access and delete it
    if github_installation:
        try:
            # Attempt to revoke the GitHub installation access
            GitHubService.revoke_installation_access(
                github_installation.installation_id
            )
        except Exception:
            # Continue with deletion even if revocation fails
            return HTTPException(
                status_code=500,
                detail="Failed to revoke GitHub installation access",
            )

        # Delete the installation record
        db.delete(github_installation)
        db.commit()

    # Redirect back to repositories page
    return RedirectResponse(url="/repositories", status_code=302)


# These functions are still exposed for backward compatibility
def get_installation_token(installation_id: str) -> Dict[str, Any]:
    """
    Get a GitHub App installation token for the specified installation ID.

    This is a wrapper around the GitHubService method for backward compatibility.
    """
    return GitHubService.get_installation_token(installation_id)


def fetch_token_for_installation(installation_id: str) -> Dict[str, Any]:
    """
    Fetch a GitHub App installation token for the specified installation ID.

    This is a wrapper around the GitHubService method for backward compatibility.
    """
    return GitHubService.fetch_token_for_installation(installation_id)


def get_user_repositories(installation_id: str) -> List[Dict[str, Any]]:
    """
    Get a list of repositories accessible to the GitHub App installation.

    This is a wrapper around the GitHubService method for backward compatibility.
    """
    return GitHubService.get_user_repositories(installation_id)


def revoke_installation_access(installation_id: str) -> bool:
    """
    Revoke a GitHub App installation access by deleting the installation.

    This is a wrapper around the GitHubService method for backward compatibility.
    """
    return GitHubService.revoke_installation_access(installation_id)


def get_file_search_string_for_user(user: User, repository_full_name: str, db: Session):
    """
    Get file search string for a repository that the user has access to.

    Args:
        user: The authenticated user
        repository_full_name: Repository in "owner/repo" format
        db: Database session

    Returns:
        FileSearchStringResponse: Response with file search string data

    Raises:
        HTTPException: 404 if repository not found, 403 if unauthorized, 422 if invalid format
    """
    # Import here to avoid circular import
    from src.github_app.views import FileSearchStringResponse

    # Validate repository name format (should be owner/repo)
    if "/" not in repository_full_name or repository_full_name.count("/") != 1:
        raise HTTPException(
            status_code=422, detail="Repository name must be in 'owner/repo' format"
        )

    # Find user's GitHub installation
    github_installation = (
        db.query(GitHubInstallation)
        .filter(GitHubInstallation.user_id == user.id)
        .first()
    )

    if not github_installation:
        raise HTTPException(
            status_code=403, detail="No GitHub installation found for user"
        )

    # Find the repository file index
    repository_file_index = (
        db.query(RepositoryFileIndex)
        .filter(
            RepositoryFileIndex.github_installation_id == github_installation.id,
            RepositoryFileIndex.repository_full_name == repository_full_name,
        )
        .first()
    )

    if not repository_file_index:
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{repository_full_name}' not found or not indexed",
        )

    return FileSearchStringResponse(
        repository_full_name=repository_file_index.repository_full_name,
        file_search_string=repository_file_index.file_search_string,
        updated_at=repository_file_index.updated_at,
        success=True,
    )


def get_all_file_search_strings_for_user(user: User, db: Session):
    """
    Get all file search strings for repositories that the user has access to.

    Args:
        user: The authenticated user
        db: Database session

    Returns:
        AllFileSearchStringsResponse: Response with all file search string data

    Raises:
        HTTPException: 403 if no GitHub installation found
    """
    # Import here to avoid circular import
    from src.github_app.views import AllFileSearchStringsResponse, RepositoryFileData

    # Find user's GitHub installation
    github_installation = (
        db.query(GitHubInstallation)
        .filter(GitHubInstallation.user_id == user.id)
        .first()
    )

    if not github_installation:
        # Return empty data instead of 403 when no GitHub installation
        return AllFileSearchStringsResponse(
            repositories=[],
            total_repositories=0,
            success=True,
        )

    # Get all repository file indexes for this installation
    repository_file_indexes = (
        db.query(RepositoryFileIndex)
        .filter(RepositoryFileIndex.github_installation_id == github_installation.id)
        .order_by(RepositoryFileIndex.repository_full_name)
        .all()
    )

    # Convert to response format
    repositories = [
        RepositoryFileData(
            repository_full_name=repo_index.repository_full_name,
            file_search_string=repo_index.file_search_string,
            updated_at=repo_index.updated_at,
        )
        for repo_index in repository_file_indexes
    ]

    return AllFileSearchStringsResponse(
        repositories=repositories,
        total_repositories=len(repositories),
        success=True,
    )


def get_installation_status(user: User, db: Session):
    """
    Get GitHub installation status for the user.

    Args:
        user: The authenticated user
        db: Database session

    Returns:
        dict: Installation status with has_installation and repository_count
    """
    # Find user's GitHub installation
    github_installation = (
        db.query(GitHubInstallation)
        .filter(GitHubInstallation.user_id == user.id)
        .first()
    )

    if not github_installation:
        return {
            "has_installation": False,
            "repository_count": 0,
        }

    # Count repositories for this installation
    repository_count = (
        db.query(RepositoryFileIndex)
        .filter(RepositoryFileIndex.github_installation_id == github_installation.id)
        .count()
    )

    return {
        "has_installation": True,
        "repository_count": repository_count,
    }


def get_repository_names_for_user(user: User, db: Session):
    """
    Get repository names and timestamps for cache validation - minimal data transfer.

    Returns only repository names and updated_at timestamps (~2KB) instead of full
    file search strings (~100KB+) for efficient cache invalidation detection.

    Args:
        user: The authenticated user
        db: Database session

    Returns:
        RepositoryNamesResponse: Response with repository names and timestamps

    Raises:
        HTTPException: 403 if no GitHub installation found
    """
    # Import here to avoid circular import
    from src.github_app.views import RepositoryNamesResponse

    # Find user's GitHub installation
    github_installation = (
        db.query(GitHubInstallation)
        .filter(GitHubInstallation.user_id == user.id)
        .first()
    )

    if not github_installation:
        # Return empty data instead of 403 when no GitHub installation
        return RepositoryNamesResponse(
            repository_names=[],
            repository_timestamps={},
            total_repositories=0,
            success=True,
        )

    # Get repository names and timestamps (minimal query for cache validation)
    repository_data = (
        db.query(
            RepositoryFileIndex.repository_full_name, RepositoryFileIndex.updated_at
        )
        .filter(RepositoryFileIndex.github_installation_id == github_installation.id)
        .order_by(RepositoryFileIndex.repository_full_name)
        .all()
    )

    # Extract names and build timestamp mapping
    names_list = [row[0] for row in repository_data]
    timestamps_dict = {row[0]: row[1].isoformat() for row in repository_data}

    return RepositoryNamesResponse(
        repository_names=names_list,
        repository_timestamps=timestamps_dict,
        total_repositories=len(names_list),
        success=True,
    )
