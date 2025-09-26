import logging
from datetime import datetime
from typing import Any, Dict

import sentry_sdk
from fastapi import Response
from sqlalchemy.orm import Session

from src.github_app.github_service import GitHubService
from src.github_app.models import RepositoryFileIndex
from src.models import GitHubInstallation

logger = logging.getLogger(__name__)


def handle_github_webhook(
    payload: Dict[str, Any], event_type: str, db: Session
) -> Response:
    """
    Handle GitHub webhook events.

    Args:
        payload: The raw webhook payload as a dictionary
        event_type: The GitHub event type (from X-GitHub-Event header)
        db: Database session

    Returns:
        Response: HTTP response
    """
    logger.info(f"Processing GitHub webhook: {event_type}")
    logger.debug(f"Webhook payload: {payload}")

    try:
        # Dispatch to appropriate handler based on event type
        if event_type == "installation":
            return handle_installation_event(payload, db)
        elif event_type == "installation_repositories":
            return handle_installation_repositories_event(payload, db)
        elif event_type == "repository":
            return handle_repository_event(payload, db)
        elif event_type == "push":
            return handle_push_event(payload, db)
        elif event_type == "installation_target":
            return handle_installation_target_event(payload, db)
        else:
            # Log unknown events but don't fail
            sentry_sdk.capture_message(
                f"Received unhandled webhook event: {event_type}"
            )
            logger.info(f"Received unhandled webhook event: {event_type}")
            return Response(
                content=f"Webhook event '{event_type}' received but not handled",
                status_code=200,
            )

    except Exception as e:
        logger.error(f"Error processing webhook {event_type}: {str(e)}")
        sentry_sdk.capture_exception(e)
        return Response(content=f"Error processing webhook: {str(e)}", status_code=500)


def handle_installation_event(payload: Dict[str, Any], db: Session) -> Response:
    """
    Handle GitHub App installation events.

    Supports: created, deleted, suspend, unsuspend
    """
    action = payload.get("action")
    installation = payload.get("installation", {})
    installation_id = installation.get("id")

    if not installation_id:
        logger.warning("Installation event missing installation ID")
        return Response(
            content="Installation event missing installation ID", status_code=400
        )

    logger.info(f"Processing installation {action} for installation {installation_id}")

    if action == "deleted":
        return _handle_installation_deleted(installation_id, db)
    elif action == "created":
        return _handle_installation_created(installation_id, db)
    if action == "suspend":
        return _handle_installation_suspended(installation_id, db)
    elif action == "unsuspend":
        return _handle_installation_unsuspended(installation_id, db)
    else:
        logger.info(f"Installation action '{action}' not handled")
        return Response(
            content=f"Installation action '{action}' received", status_code=200
        )


def handle_installation_repositories_event(
    payload: Dict[str, Any], db: Session
) -> Response:
    """
    Handle repository access changes for GitHub App installations.

    Supports: added, removed
    """
    action = payload.get("action")
    installation = payload.get("installation", {})
    installation_id = installation.get("id")

    if not installation_id:
        logger.warning("Installation repositories event missing installation ID")
        return Response(
            content="Installation repositories event missing installation ID",
            status_code=400,
        )

    logger.info(
        f"Processing installation_repositories {action} for installation {installation_id}"
    )

    if action == "added":
        repositories_added = payload.get("repositories_added", [])
        return _handle_repositories_added(installation_id, repositories_added, db)
    elif action == "removed":
        repositories_removed = payload.get("repositories_removed", [])
        return _handle_repositories_removed(installation_id, repositories_removed, db)
    else:
        logger.info(f"Installation repositories action '{action}' not handled")
        return Response(
            content=f"Installation repositories action '{action}' received",
            status_code=200,
        )


def handle_repository_event(payload: Dict[str, Any], db: Session) -> Response:
    """
    Handle repository-level events.

    Supports: deleted, transferred, renamed
    """
    action = payload.get("action")
    repository = payload.get("repository", {})
    repo_full_name = repository.get("full_name")

    if not repo_full_name:
        logger.warning("Repository event missing repository full_name")
        return Response(
            content="Repository event missing repository full_name", status_code=400
        )

    logger.info(f"Processing repository {action} for repository {repo_full_name}")

    if action == "deleted":
        return _handle_repository_deleted(repo_full_name, db)
    elif action in ["transferred", "renamed"]:
        return _handle_repository_updated(repo_full_name, repository, db)
    else:
        logger.info(f"Repository action '{action}' not handled")
        return Response(
            content=f"Repository action '{action}' received", status_code=200
        )


def _handle_installation_deleted(installation_id: int, db: Session) -> Response:
    """Handle GitHub App installation deletion."""
    try:
        github_installation = (
            db.query(GitHubInstallation)
            .filter(GitHubInstallation.installation_id == str(installation_id))
            .first()
        )

        if github_installation:
            # Revoke access using the service
            GitHubService.revoke_installation_access(str(installation_id))
            # Delete the installation record (cascades to repository file indexes)
            db.delete(github_installation)
            db.commit()
            logger.info(f"Successfully deleted installation {installation_id}")
            return Response(
                content="Installation deleted successfully", status_code=200
            )
        else:
            logger.info(f"Installation {installation_id} not found in database")
            return Response(content="Installation not found", status_code=200)
    except Exception as e:
        logger.error(f"Error deleting installation {installation_id}: {str(e)}")
        sentry_sdk.capture_exception(e)
        return Response(
            content=f"Error processing installation deletion: {str(e)}", status_code=500
        )


def _handle_installation_created(installation_id: int, db: Session) -> Response:
    """Handle GitHub App installation creation."""
    logger.info(f"GitHub App installed for installation {installation_id}")
    # Installation creation is handled via the callback flow in controller.py
    # This webhook just provides notification
    return Response(
        content="Installation created notification received", status_code=200
    )


def _handle_installation_suspended(installation_id: int, db: Session) -> Response:
    """Handle GitHub App installation suspension by removing all repository file indexes."""
    try:
        # Find the GitHub installation
        github_installation = (
            db.query(GitHubInstallation)
            .filter(GitHubInstallation.installation_id == str(installation_id))
            .first()
        )

        if not github_installation:
            logger.info(f"Installation {installation_id} not found in database")
            return Response(content="Installation not found", status_code=200)

        # Get all repository file indexes for this installation
        repo_file_indexes = (
            db.query(RepositoryFileIndex)
            .filter(
                RepositoryFileIndex.github_installation_id == github_installation.id
            )
            .all()
        )

        # Delete all repository file indexes
        deleted_count = 0
        for repo_file_index in repo_file_indexes:
            db.delete(repo_file_index)
            deleted_count += 1

        db.commit()

        logger.info(
            f"Successfully removed {deleted_count} repository file indexes for suspended installation {installation_id}"
        )
        return Response(
            content=f"Installation suspended: removed {deleted_count} repository file indexes",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error suspending installation {installation_id}: {str(e)}")
        sentry_sdk.capture_exception(e)
        return Response(
            content=f"Error processing installation suspension: {str(e)}",
            status_code=500,
        )


def _handle_installation_unsuspended(installation_id: int, db: Session) -> Response:
    """Handle GitHub App installation unsuspension by recreating repository file indexes."""
    try:
        # Find the GitHub installation
        github_installation = (
            db.query(GitHubInstallation)
            .filter(GitHubInstallation.installation_id == str(installation_id))
            .first()
        )

        if not github_installation:
            logger.info(f"Installation {installation_id} not found in database")
            return Response(content="Installation not found", status_code=200)

        # Get list of repositories for this installation from GitHub API
        try:
            repo_list = GitHubService.get_user_repositories(str(installation_id))
            if not repo_list:
                logger.info(f"No repositories found for installation {installation_id}")
                return Response(
                    content="No repositories found for installation",
                    status_code=200,
                )
        except Exception as e:
            logger.error(
                f"Error fetching repositories for installation {installation_id}: {str(e)}"
            )
            sentry_sdk.capture_exception(e)
            return Response(
                content="Error retrieving repositories from GitHub",
                status_code=200,
            )

        # Recreate file indexes for all repositories
        success_count = 0

        for repo in repo_list:
            repo_full_name = repo.get("full_name")
            if repo_full_name:
                if _create_repository_file_index(
                    str(installation_id), repo_full_name, db, commit=False
                ):
                    success_count += 1

        # Update prefixing strategy if repositories were added successfully
        if success_count > 0:
            _update_prefixing_strategy(str(installation_id), db)

        db.commit()

        logger.info(
            f"Successfully recreated {success_count}/{len(repo_list)} repository file indexes for unsuspended installation {installation_id}"
        )
        return Response(
            content=f"Installation unsuspended: recreated {success_count}/{len(repo_list)} repository file indexes",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error unsuspending installation {installation_id}: {str(e)}")
        sentry_sdk.capture_exception(e)
        return Response(
            content=f"Error processing installation unsuspension: {str(e)}",
            status_code=500,
        )


def _handle_repositories_added(
    installation_id: int, repositories: list, db: Session
) -> Response:
    """Handle repositories being added to GitHub App installation."""
    repo_names = [repo.get("full_name", "unknown") for repo in repositories]
    logger.info(f"Repositories added to installation {installation_id}: {repo_names}")

    # Create file indexes for all newly added repositories
    success_count = 0
    for repo in repositories:
        repo_full_name = repo.get("full_name")
        if repo_full_name:
            if _create_repository_file_index(str(installation_id), repo_full_name, db):
                success_count += 1

    # Update prefixing strategy if repositories were added successfully
    if success_count > 0:
        _update_prefixing_strategy(str(installation_id), db)

    logger.info(
        f"Successfully processed {success_count}/{len(repositories)} repository additions"
    )
    return Response(
        content=f"Repositories added: {success_count}/{len(repositories)} repositories processed successfully",
        status_code=200,
    )


def _handle_repositories_removed(
    installation_id: int, repositories: list, db: Session
) -> Response:
    """Handle repositories being removed from GitHub App installation."""
    repo_names = [repo.get("full_name", "unknown") for repo in repositories]
    logger.info(
        f"Repositories removed from installation {installation_id}: {repo_names}"
    )

    # Delete file indexes for all removed repositories
    success_count = 0
    for repo in repositories:
        repo_full_name = repo.get("full_name")
        if repo_full_name:
            if _delete_repository_file_index(repo_full_name, db):
                success_count += 1

    # Update prefixing strategy for remaining repositories
    if success_count > 0:
        _update_prefixing_strategy(str(installation_id), db)

    logger.info(
        f"Successfully processed {success_count}/{len(repositories)} repository removals"
    )
    return Response(
        content=f"Repositories removed: {success_count}/{len(repositories)} repositories processed successfully",
        status_code=200,
    )


def _handle_repository_deleted(repo_full_name: str, db: Session) -> Response:
    """Handle repository deletion."""
    logger.info(f"Repository deleted: {repo_full_name}")

    # Get the installation ID before deleting the file index
    repo_file_index = (
        db.query(RepositoryFileIndex)
        .filter(RepositoryFileIndex.repository_full_name == repo_full_name)
        .first()
    )

    installation_id = None
    if repo_file_index and repo_file_index.github_installation:
        installation_id = repo_file_index.github_installation.installation_id

    # Delete the file index for this repository
    success = _delete_repository_file_index(repo_full_name, db)

    # Update prefixing strategy for remaining repositories if we found the installation
    if success and installation_id:
        _update_prefixing_strategy(installation_id, db)

    status_message = "successfully" if success else "with errors"
    logger.info(f"Repository deletion processed {status_message}: {repo_full_name}")
    return Response(
        content=f"Repository deletion processed {status_message}: {repo_full_name}",
        status_code=200,
    )


def _handle_repository_updated(
    repo_full_name: str, repository: Dict[str, Any], db: Session
) -> Response:
    """Handle repository updates (rename, transfer)."""
    logger.info(f"Repository updated: {repo_full_name}")

    # Extract the new repository information
    new_repo_full_name = repository.get("full_name", repo_full_name)

    # Find existing file index (could be under old name or new name)
    repo_file_index = (
        db.query(RepositoryFileIndex)
        .filter(
            (RepositoryFileIndex.repository_full_name == repo_full_name)
            | (RepositoryFileIndex.repository_full_name == new_repo_full_name)
        )
        .first()
    )

    if not repo_file_index:
        logger.info(f"No file index found for repository {repo_full_name}")
        return Response(
            content=f"No file index found for repository: {repo_full_name}",
            status_code=200,
        )

    installation_id = repo_file_index.github_installation.installation_id

    try:
        # Update the repository full name if it changed
        if repo_file_index.repository_full_name != new_repo_full_name:
            logger.info(
                f"Updating repository name from {repo_file_index.repository_full_name} to {new_repo_full_name}"
            )
            repo_file_index.repository_full_name = new_repo_full_name

        # Parse new repository owner and name
        repo_owner, repo_name = new_repo_full_name.split("/", 1)

        # Get updated file tree for the repository
        file_tree_response = GitHubService.get_file_tree(
            installation_id,
            repo_owner,
            repo_name,
            recursive=True,
        )

        # Check for API errors
        if "error" in file_tree_response:
            logger.error(
                f"GitHub API error for {new_repo_full_name}: {file_tree_response.get('error')}"
            )
            return Response(
                content=f"GitHub API error for repository: {new_repo_full_name}",
                status_code=200,
            )

        # Determine repository count for prefixing strategy
        total_repos = _get_repository_count_for_installation(installation_id, db)
        use_repo_prefix = total_repos > 1

        # Generate new file search string
        new_file_search_string = GitHubService.generate_file_search_string(
            file_tree_response, repo_name, use_repo_prefix
        )

        # Update the repository file index
        repo_file_index.file_search_string = new_file_search_string
        repo_file_index.last_indexed_commit_sha = file_tree_response.get("sha")

        db.commit()

        logger.info(
            f"Successfully updated file index for repository {new_repo_full_name}"
        )
        return Response(
            content=f"Repository update processed successfully: {new_repo_full_name}",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error updating repository {repo_full_name}: {str(e)}")
        sentry_sdk.capture_exception(e)
        return Response(
            content=f"Repository update processed with errors: {repo_full_name}",
            status_code=200,
        )


def handle_push_event(payload: Dict[str, Any], db: Session) -> Response:
    """
    Handle GitHub push events to update repository file indexes.

    Updates the file index for the repository when code changes are pushed,
    ensuring autocomplete suggestions stay synchronized with the current codebase.

    Args:
        payload: The GitHub push webhook payload
        db: Database session

    Returns:
        Response: HTTP response
    """
    repository = payload.get("repository", {})
    repo_full_name = repository.get("full_name")
    commit_sha = payload.get("after")

    if not repo_full_name:
        logger.warning("Push event missing repository full_name")
        return Response(
            content="Push event missing repository full_name", status_code=400
        )

    if not commit_sha:
        logger.warning("Push event missing commit SHA")
        return Response(content="Push event missing commit SHA", status_code=400)

    # Handle branch deletion (commit SHA is all zeros)
    if commit_sha == "0000000000000000000000000000000000000000":
        logger.info(f"Branch deletion detected for repository {repo_full_name}")
        return Response(
            content=f"Branch deletion processed: {repo_full_name}", status_code=200
        )

    logger.info(
        f"Processing push event for repository {repo_full_name}, commit {commit_sha[:8]}"
    )

    try:
        return _update_repository_file_index(repo_full_name, commit_sha, db)
    except Exception as e:
        logger.error(f"Error updating file index for {repo_full_name}: {str(e)}")
        sentry_sdk.capture_exception(e)
        # Return success to avoid webhook retries, but log the error
        return Response(
            content=f"Push event processed with errors: {repo_full_name}",
            status_code=200,
        )


def _update_repository_file_index(
    repo_full_name: str, commit_sha: str, db: Session
) -> Response:
    """
    Update the file index for a specific repository.

    Args:
        repo_full_name: Repository identifier in "owner/repo" format
        commit_sha: The new commit SHA after the push
        db: Database session

    Returns:
        Response: HTTP response
    """
    # Find existing repository file index
    repo_file_index = (
        db.query(RepositoryFileIndex)
        .filter(RepositoryFileIndex.repository_full_name == repo_full_name)
        .first()
    )

    if not repo_file_index:
        logger.info(f"No file index found for repository {repo_full_name}")
        return Response(
            content=f"No file index found for repository: {repo_full_name}",
            status_code=200,
        )

    # Check if the commit SHA has changed (performance optimization)
    if repo_file_index.last_indexed_commit_sha == commit_sha:
        logger.info(
            f"File index for {repo_full_name} already up to date (commit {commit_sha[:8]})"
        )
        return Response(
            content=f"File index already up to date: {repo_full_name}", status_code=200
        )

    # Get the GitHub installation for API access
    github_installation = repo_file_index.github_installation
    if not github_installation:
        logger.error(f"No GitHub installation found for repository {repo_full_name}")
        return Response(
            content=f"No GitHub installation found: {repo_full_name}", status_code=200
        )

    # Parse repository owner and name
    try:
        repo_owner, repo_name = repo_full_name.split("/", 1)
    except ValueError:
        logger.error(f"Invalid repository full name format: {repo_full_name}")
        return Response(
            content=f"Invalid repository name format: {repo_full_name}", status_code=200
        )

    # Fetch updated file tree from GitHub
    file_tree_response = GitHubService.get_file_tree(
        github_installation.installation_id,
        repo_owner,
        repo_name,
        recursive=True,
    )

    # Check for API errors
    if "error" in file_tree_response:
        logger.error(
            f"GitHub API error for {repo_full_name}: {file_tree_response.get('error')}"
        )
        return Response(content=f"GitHub API error: {repo_full_name}", status_code=200)

    # Determine repository count for prefixing strategy
    total_repos = (
        db.query(RepositoryFileIndex)
        .filter(RepositoryFileIndex.github_installation_id == github_installation.id)
        .count()
    )
    use_repo_prefix = total_repos > 1

    # Generate new file search string
    new_file_search_string = GitHubService.generate_file_search_string(
        file_tree_response, repo_name, use_repo_prefix
    )

    # Update the repository file index
    repo_file_index.file_search_string = new_file_search_string
    repo_file_index.last_indexed_commit_sha = commit_sha
    # Explicitly update timestamp for cache invalidation
    repo_file_index.updated_at = datetime.now()

    db.commit()

    logger.info(
        f"Successfully updated file index for {repo_full_name} (commit {commit_sha[:8]})"
    )
    return Response(
        content=f"File index updated successfully: {repo_full_name}", status_code=200
    )


def handle_installation_target_event(payload: Dict[str, Any], db: Session) -> Response:
    """
    Handle GitHub App installation target events.

    Supports: renamed
    """
    action = payload.get("action")
    installation = payload.get("installation", {})
    installation_id = installation.get("id")

    if not installation_id:
        logger.warning("Installation target event missing installation ID")
        return Response(
            content="Installation target event missing installation ID", status_code=400
        )

    logger.info(
        f"Processing installation_target {action} for installation {installation_id}"
    )

    if action == "renamed":
        return _handle_installation_target_renamed(payload, db)
    else:
        logger.info(f"Installation target action '{action}' not handled")
        return Response(
            content=f"Installation target action '{action}' received", status_code=200
        )


def _handle_installation_target_renamed(
    payload: Dict[str, Any], db: Session
) -> Response:
    """
    Handle GitHub App installation target rename events.

    Updates all repository full names when the account (user/org) is renamed.
    """
    try:
        # Extract rename information from payload
        changes = payload.get("changes", {}).get("login", {})
        old_account_name = changes.get("from")
        account = payload.get("account", {})
        new_account_name = account.get("login")
        installation = payload.get("installation", {})
        installation_id = installation.get("id")

        # Validate required fields
        if not old_account_name or not new_account_name or not installation_id:
            sentry_sdk.capture_message(
                f"Installation target rename missing required fields: "
                f"old_name={old_account_name}, new_name={new_account_name}, "
                f"installation_id={installation_id}"
            )
            logger.warning(
                f"Installation target rename missing required fields: "
                f"old_name={old_account_name}, new_name={new_account_name}, "
                f"installation_id={installation_id}"
            )
            return Response(
                content="Installation target rename missing required fields",
                status_code=400,
            )

        logger.info(
            f"Processing account rename from '{old_account_name}' to '{new_account_name}' "
            f"for installation {installation_id}"
        )

        # Find the GitHub installation record
        github_installation = (
            db.query(GitHubInstallation)
            .filter(GitHubInstallation.installation_id == str(installation_id))
            .first()
        )

        if not github_installation:
            logger.info(f"Installation {installation_id} not found in database")
            return Response(content="Installation not found", status_code=200)

        # Find all repository file indexes that need updating
        repo_file_indexes = (
            db.query(RepositoryFileIndex)
            .filter(
                RepositoryFileIndex.github_installation_id == github_installation.id
            )
            .filter(
                RepositoryFileIndex.repository_full_name.like(f"{old_account_name}/%")
            )
            .all()
        )

        # Update each repository's full name
        updated_count = 0
        for repo_file_index in repo_file_indexes:
            old_name = repo_file_index.repository_full_name
            new_name = old_name.replace(
                f"{old_account_name}/", f"{new_account_name}/", 1
            )

            logger.info(f"Updating repository name from '{old_name}' to '{new_name}'")
            repo_file_index.repository_full_name = new_name
            db.add(repo_file_index)
            updated_count += 1

        db.commit()

        logger.info(
            f"Successfully updated {updated_count} repository names for account rename "
            f"from '{old_account_name}' to '{new_account_name}'"
        )
        return Response(
            content=f"Account rename processed: updated {updated_count} repositories "
            f"from '{old_account_name}' to '{new_account_name}'",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error processing installation target rename: {str(e)}")
        sentry_sdk.capture_exception(e)
        return Response(
            content=f"Error processing installation target rename: {str(e)}",
            status_code=500,
        )


def _get_repository_count_for_installation(installation_id: str, db: Session) -> int:
    """
    Get the count of repositories with file indexes for a GitHub installation.

    Args:
        installation_id: The GitHub App installation ID
        db: Database session

    Returns:
        int: Number of repositories with file indexes
    """
    try:
        github_installation = (
            db.query(GitHubInstallation)
            .filter(GitHubInstallation.installation_id == installation_id)
            .first()
        )

        if not github_installation:
            return 0

        return (
            db.query(RepositoryFileIndex)
            .filter(
                RepositoryFileIndex.github_installation_id == github_installation.id
            )
            .count()
        )
    except Exception as e:
        logger.error(
            f"Error getting repository count for installation {installation_id}: {str(e)}"
        )
        sentry_sdk.capture_exception(e)
        return 0


def _create_repository_file_index(
    installation_id: str, repo_full_name: str, db: Session, commit: bool = True
) -> bool:
    """
    Create a file index for a single repository.

    Args:
        installation_id: The GitHub App installation ID
        repo_full_name: Repository identifier in "owner/repo" format
        db: Database session
        commit: Whether to commit the transaction (default: True)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Find the GitHub installation
        github_installation = (
            db.query(GitHubInstallation)
            .filter(GitHubInstallation.installation_id == installation_id)
            .first()
        )

        if not github_installation:
            logger.error(f"No GitHub installation found for ID {installation_id}")
            return False

        # Check if file index already exists
        existing_index = (
            db.query(RepositoryFileIndex)
            .filter(RepositoryFileIndex.repository_full_name == repo_full_name)
            .filter(
                RepositoryFileIndex.github_installation_id == github_installation.id
            )
            .first()
        )

        if existing_index:
            logger.info(f"File index already exists for repository {repo_full_name}")
            return True

        # Parse repository owner and name
        try:
            repo_owner, repo_name = repo_full_name.split("/", 1)
        except ValueError:
            logger.error(f"Invalid repository full name format: {repo_full_name}")
            return False

        # Get file tree for the repository
        file_tree_response = GitHubService.get_file_tree(
            installation_id,
            repo_owner,
            repo_name,
            recursive=True,
        )

        # Check for API errors
        if "error" in file_tree_response:
            logger.error(
                f"GitHub API error for {repo_full_name}: {file_tree_response.get('error')}"
            )
            return False

        # Determine repository count for prefixing strategy
        total_repos = (
            _get_repository_count_for_installation(installation_id, db) + 1
        )  # +1 for the new repo
        use_repo_prefix = total_repos > 1

        # Generate file search string
        file_search_string = GitHubService.generate_file_search_string(
            file_tree_response, repo_name, use_repo_prefix
        )

        # Create repository file index record
        repo_file_index = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name=repo_full_name,
            file_search_string=file_search_string,
            last_indexed_commit_sha=file_tree_response.get("sha"),
        )

        db.add(repo_file_index)
        if commit:
            db.commit()

        logger.info(f"Successfully created file index for repository {repo_full_name}")
        return True

    except Exception as e:
        logger.error(f"Error creating file index for {repo_full_name}: {str(e)}")
        sentry_sdk.capture_exception(e)
        return False


def _delete_repository_file_index(repo_full_name: str, db: Session) -> bool:
    """
    Delete the file index for a specific repository.

    Args:
        repo_full_name: Repository identifier in "owner/repo" format
        db: Database session

    Returns:
        bool: True if successful (including if no index existed), False on error
    """
    try:
        repo_file_index = (
            db.query(RepositoryFileIndex)
            .filter(RepositoryFileIndex.repository_full_name == repo_full_name)
            .first()
        )

        if repo_file_index:
            db.delete(repo_file_index)
            db.commit()
            logger.info(
                f"Successfully deleted file index for repository {repo_full_name}"
            )
        else:
            logger.info(f"No file index found for repository {repo_full_name}")

        return True

    except Exception as e:
        logger.error(f"Error deleting file index for {repo_full_name}: {str(e)}")
        sentry_sdk.capture_exception(e)
        return False


def _update_prefixing_strategy(installation_id: str, db: Session) -> bool:
    """
    Update the prefixing strategy for all repositories in an installation.

    This should be called when the number of repositories changes to ensure
    consistent @ prefixing (single repo vs multi-repo scenarios).

    Args:
        installation_id: The GitHub App installation ID
        db: Database session

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Find the GitHub installation
        github_installation = (
            db.query(GitHubInstallation)
            .filter(GitHubInstallation.installation_id == installation_id)
            .first()
        )

        if not github_installation:
            logger.error(f"No GitHub installation found for ID {installation_id}")
            return False

        # Get all repository file indexes for this installation
        repo_file_indexes = (
            db.query(RepositoryFileIndex)
            .filter(
                RepositoryFileIndex.github_installation_id == github_installation.id
            )
            .all()
        )

        if not repo_file_indexes:
            logger.info(f"No file indexes found for installation {installation_id}")
            return True

        # Determine new prefixing strategy
        use_repo_prefix = len(repo_file_indexes) > 1

        # Update each repository's file search string with correct prefixing
        for repo_file_index in repo_file_indexes:
            try:
                repo_full_name = repo_file_index.repository_full_name
                repo_owner, repo_name = repo_full_name.split("/", 1)

                # Get fresh file tree to regenerate with correct prefixing
                file_tree_response = GitHubService.get_file_tree(
                    installation_id,
                    repo_owner,
                    repo_name,
                    recursive=True,
                )

                # Check for API errors
                if "error" in file_tree_response:
                    logger.error(
                        f"GitHub API error for {repo_full_name}: {file_tree_response.get('error')}"
                    )
                    continue

                # Generate new file search string with updated prefixing
                new_file_search_string = GitHubService.generate_file_search_string(
                    file_tree_response, repo_name, use_repo_prefix
                )

                # Update the file search string
                repo_file_index.file_search_string = new_file_search_string

            except Exception as e:
                logger.error(
                    f"Error updating prefixing for {repo_file_index.repository_full_name}: {str(e)}"
                )
                sentry_sdk.capture_exception(e)
                continue

        db.commit()
        logger.info(
            f"Successfully updated prefixing strategy for installation {installation_id}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Error updating prefixing strategy for installation {installation_id}: {str(e)}"
        )
        sentry_sdk.capture_exception(e)
        return False
