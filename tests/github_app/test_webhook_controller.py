from datetime import datetime
from unittest.mock import patch

from fastapi import Response
from sqlalchemy.orm import Session

from src.github_app.models import RepositoryFileIndex
from src.github_app.webhook_controller import (
    _handle_installation_suspended,
    _handle_installation_target_renamed,
    _handle_installation_unsuspended,
    handle_github_webhook,
    handle_installation_event,
    handle_installation_repositories_event,
    handle_installation_target_event,
    handle_push_event,
    handle_repository_event,
)
from src.models import GitHubInstallation, User


class TestHandleGithubWebhook:
    """Test the main webhook dispatcher."""

    def test_dispatch_installation_event(self, session: Session):
        """Test that installation events are dispatched correctly."""
        payload = {"action": "deleted", "installation": {"id": 12345}}

        with patch(
            "src.github_app.webhook_controller.handle_installation_event"
        ) as mock_handler:
            mock_handler.return_value = Response(content="test", status_code=200)

            response = handle_github_webhook(payload, "installation", session)

            mock_handler.assert_called_once_with(payload, session)
            assert response.status_code == 200

    def test_dispatch_installation_repositories_event(self, session: Session):
        """Test that installation_repositories events are dispatched correctly."""
        payload = {
            "action": "added",
            "installation": {"id": 12345},
            "repositories_added": [],
        }

        with patch(
            "src.github_app.webhook_controller.handle_installation_repositories_event"
        ) as mock_handler:
            mock_handler.return_value = Response(content="test", status_code=200)

            response = handle_github_webhook(
                payload, "installation_repositories", session
            )

            mock_handler.assert_called_once_with(payload, session)
            assert response.status_code == 200

    def test_dispatch_repository_event(self, session: Session):
        """Test that repository events are dispatched correctly."""
        payload = {"action": "deleted", "repository": {"full_name": "owner/repo"}}

        with patch(
            "src.github_app.webhook_controller.handle_repository_event"
        ) as mock_handler:
            mock_handler.return_value = Response(content="test", status_code=200)

            response = handle_github_webhook(payload, "repository", session)

            mock_handler.assert_called_once_with(payload, session)
            assert response.status_code == 200

    def test_dispatch_push_event(self, session: Session):
        """Test that push events are dispatched correctly."""
        payload = {
            "repository": {"full_name": "owner/repo"},
            "after": "abc123def456",
            "ref": "refs/heads/main",
        }

        with patch(
            "src.github_app.webhook_controller.handle_push_event"
        ) as mock_handler:
            mock_handler.return_value = Response(content="test", status_code=200)

            response = handle_github_webhook(payload, "push", session)

            mock_handler.assert_called_once_with(payload, session)
            assert response.status_code == 200

    def test_dispatch_installation_target_event(self, session: Session):
        """Test that installation_target events are dispatched correctly."""
        payload = {
            "action": "renamed",
            "installation": {"id": 12345},
            "changes": {"login": {"from": "oldname"}},
            "account": {"login": "newname"},
        }

        with patch(
            "src.github_app.webhook_controller.handle_installation_target_event"
        ) as mock_handler:
            mock_handler.return_value = Response(content="test", status_code=200)

            response = handle_github_webhook(payload, "installation_target", session)

            mock_handler.assert_called_once_with(payload, session)
            assert response.status_code == 200

    def test_unknown_event_type(self, session: Session):
        """Test handling of unknown event types."""
        payload = {"some": "data"}

        response = handle_github_webhook(payload, "unknown_event", session)

        assert response.status_code == 200
        assert "not handled" in response.body.decode()

    def test_exception_handling(self, session: Session):
        """Test that exceptions are handled gracefully."""
        payload = {"action": "deleted", "installation": {"id": 12345}}

        with patch(
            "src.github_app.webhook_controller.handle_installation_event"
        ) as mock_handler:
            mock_handler.side_effect = Exception("Test error")

            response = handle_github_webhook(payload, "installation", session)

            assert response.status_code == 500
            assert "Error processing webhook" in response.body.decode()


class TestHandleInstallationEvent:
    """Test installation event handling."""

    def test_installation_deleted_success(self, session: Session, user: User):
        """Test successful installation deletion."""
        # Create a GitHub installation
        installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(installation)
        session.commit()

        payload = {"action": "deleted", "installation": {"id": 12345}}

        with patch(
            "src.github_app.webhook_controller.GitHubService.revoke_installation_access"
        ) as mock_revoke:
            response = handle_installation_event(payload, session)

            # Verify response
            assert response.status_code == 200
            assert "deleted successfully" in response.body.decode()

            # Verify installation was deleted
            assert (
                session.query(GitHubInstallation)
                .filter(GitHubInstallation.installation_id == "12345")
                .first()
                is None
            )

            # Verify revoke was called
            mock_revoke.assert_called_once_with("12345")

    def test_installation_deleted_not_found(self, session: Session):
        """Test installation deletion when installation not found."""
        payload = {"action": "deleted", "installation": {"id": 99999}}

        response = handle_installation_event(payload, session)

        assert response.status_code == 200
        assert "not found" in response.body.decode()

    def test_installation_created(self, session: Session):
        """Test installation created event."""
        payload = {"action": "created", "installation": {"id": 12345}}

        response = handle_installation_event(payload, session)

        assert response.status_code == 200
        assert "created notification" in response.body.decode()

    def test_installation_suspend_success(self, session: Session, user: User):
        """Test successful installation suspension removes all repository file indexes."""
        # Create a GitHub installation
        installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(installation)
        session.commit()
        session.refresh(installation)

        # Create some repository file indexes
        repo_index1 = RepositoryFileIndex(
            github_installation_id=installation.id,
            repository_full_name="owner/repo1",
            file_search_string="@file1.py",
        )
        repo_index2 = RepositoryFileIndex(
            github_installation_id=installation.id,
            repository_full_name="owner/repo2",
            file_search_string="@file2.py",
        )
        session.add_all([repo_index1, repo_index2])
        session.commit()

        payload = {"action": "suspend", "installation": {"id": 12345}}

        response = handle_installation_event(payload, session)

        # Verify response
        assert response.status_code == 200
        assert "removed 2 repository file indexes" in response.body.decode()

        # Verify all repository file indexes were deleted
        remaining_indexes = (
            session.query(RepositoryFileIndex)
            .filter(RepositoryFileIndex.github_installation_id == installation.id)
            .all()
        )
        assert len(remaining_indexes) == 0

    def test_installation_suspend_not_found(self, session: Session):
        """Test installation suspension when installation not found."""
        payload = {"action": "suspend", "installation": {"id": 99999}}

        response = handle_installation_event(payload, session)

        assert response.status_code == 200
        assert "Installation not found" in response.body.decode()

    def test_installation_unsuspend_success(self, session: Session, user: User):
        """Test successful installation unsuspension recreates repository file indexes."""
        # Create a GitHub installation
        installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(installation)
        session.commit()

        payload = {"action": "unsuspend", "installation": {"id": 12345}}

        # Mock GitHub API responses
        mock_repositories = [
            {"full_name": "owner/repo1"},
            {"full_name": "owner/repo2"},
        ]

        with (
            patch(
                "src.github_app.webhook_controller.GitHubService.get_user_repositories"
            ) as mock_get_repos,
            patch(
                "src.github_app.webhook_controller._create_repository_file_index"
            ) as mock_create_index,
            patch(
                "src.github_app.webhook_controller._update_prefixing_strategy"
            ) as mock_update_prefixing,
        ):
            mock_get_repos.return_value = mock_repositories
            mock_create_index.return_value = True

            response = handle_installation_event(payload, session)

            # Verify response
            assert response.status_code == 200
            assert "recreated 2/2 repository file indexes" in response.body.decode()

            # Verify GitHub API was called
            mock_get_repos.assert_called_once_with("12345")

            # Verify helper functions were called
            assert mock_create_index.call_count == 2
            mock_create_index.assert_any_call(
                "12345", "owner/repo1", session, commit=False
            )
            mock_create_index.assert_any_call(
                "12345", "owner/repo2", session, commit=False
            )
            mock_update_prefixing.assert_called_once_with("12345", session)

    def test_installation_unsuspend_not_found(self, session: Session):
        """Test installation unsuspension when installation not found."""
        payload = {"action": "unsuspend", "installation": {"id": 99999}}

        response = handle_installation_event(payload, session)

        assert response.status_code == 200
        assert "Installation not found" in response.body.decode()

    def test_installation_unsuspend_no_repositories(self, session: Session, user: User):
        """Test installation unsuspension when no repositories found."""
        # Create a GitHub installation
        installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(installation)
        session.commit()

        payload = {"action": "unsuspend", "installation": {"id": 12345}}

        with patch(
            "src.github_app.webhook_controller.GitHubService.get_user_repositories"
        ) as mock_get_repos:
            mock_get_repos.return_value = []

            response = handle_installation_event(payload, session)

            # Verify response
            assert response.status_code == 200
            assert "No repositories found for installation" in response.body.decode()

    def test_installation_unsuspend_github_api_error(
        self, session: Session, user: User
    ):
        """Test installation unsuspension when GitHub API fails."""
        # Create a GitHub installation
        installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(installation)
        session.commit()

        payload = {"action": "unsuspend", "installation": {"id": 12345}}

        with patch(
            "src.github_app.webhook_controller.GitHubService.get_user_repositories"
        ) as mock_get_repos:
            mock_get_repos.side_effect = Exception("GitHub API error")

            response = handle_installation_event(payload, session)

            # Verify graceful error handling
            assert response.status_code == 200
            assert "Error retrieving repositories from GitHub" in response.body.decode()

    def test_missing_installation_id(self, session: Session):
        """Test handling when installation ID is missing."""
        payload = {"action": "deleted", "installation": {}}

        response = handle_installation_event(payload, session)

        assert response.status_code == 400
        assert "missing installation ID" in response.body.decode()

    def test_unknown_action(self, session: Session):
        """Test handling of unknown installation actions."""
        payload = {"action": "unknown_action", "installation": {"id": 12345}}

        response = handle_installation_event(payload, session)

        assert response.status_code == 200
        assert "unknown_action" in response.body.decode()


class TestHandleInstallationRepositoriesEvent:
    """Test installation repositories event handling."""

    def test_repositories_added(self, session: Session):
        """Test repositories added event."""
        payload = {
            "action": "added",
            "installation": {"id": 12345},
            "repositories_added": [
                {"full_name": "owner/repo1"},
                {"full_name": "owner/repo2"},
            ],
        }

        # Mock the helper functions to avoid GitHub API calls
        with (
            patch(
                "src.github_app.webhook_controller._create_repository_file_index"
            ) as mock_create_index,
            patch(
                "src.github_app.webhook_controller._update_prefixing_strategy"
            ) as mock_update_prefixing,
        ):
            mock_create_index.return_value = True

            response = handle_installation_repositories_event(payload, session)

            assert response.status_code == 200
            assert "2/2 repositories processed successfully" in response.body.decode()

    def test_repositories_removed(self, session: Session):
        """Test repositories removed event."""
        payload = {
            "action": "removed",
            "installation": {"id": 12345},
            "repositories_removed": [{"full_name": "owner/repo1"}],
        }

        # Mock the helper functions to avoid database operations
        with (
            patch(
                "src.github_app.webhook_controller._delete_repository_file_index"
            ) as mock_delete_index,
            patch(
                "src.github_app.webhook_controller._update_prefixing_strategy"
            ) as mock_update_prefixing,
        ):
            mock_delete_index.return_value = True

            response = handle_installation_repositories_event(payload, session)

            assert response.status_code == 200
            assert "1/1 repositories processed successfully" in response.body.decode()

    def test_missing_installation_id(self, session: Session):
        """Test handling when installation ID is missing."""
        payload = {"action": "added", "installation": {}, "repositories_added": []}

        response = handle_installation_repositories_event(payload, session)

        assert response.status_code == 400
        assert "missing installation ID" in response.body.decode()

    def test_unknown_action(self, session: Session):
        """Test handling of unknown repository actions."""
        payload = {"action": "unknown_action", "installation": {"id": 12345}}

        response = handle_installation_repositories_event(payload, session)

        assert response.status_code == 200
        assert "unknown_action" in response.body.decode()


class TestHandleRepositoryEvent:
    """Test repository event handling."""

    def test_repository_deleted(self, session: Session):
        """Test repository deleted event."""
        payload = {"action": "deleted", "repository": {"full_name": "owner/repo"}}

        # Mock the helper functions to avoid database operations
        with (
            patch(
                "src.github_app.webhook_controller._delete_repository_file_index"
            ) as mock_delete_index,
            patch(
                "src.github_app.webhook_controller._update_prefixing_strategy"
            ) as mock_update_prefixing,
        ):
            mock_delete_index.return_value = True

            response = handle_repository_event(payload, session)

            assert response.status_code == 200
            assert (
                "Repository deletion processed successfully: owner/repo"
                in response.body.decode()
            )

    def test_repository_transferred(self, session: Session):
        """Test repository transferred event."""
        payload = {
            "action": "transferred",
            "repository": {"full_name": "newowner/repo"},
        }

        response = handle_repository_event(payload, session)

        assert response.status_code == 200
        # Should return "No file index found" since no index exists in test
        assert (
            "No file index found for repository: newowner/repo"
            in response.body.decode()
        )

    def test_repository_renamed(self, session: Session):
        """Test repository renamed event."""
        payload = {"action": "renamed", "repository": {"full_name": "owner/newrepo"}}

        response = handle_repository_event(payload, session)

        assert response.status_code == 200
        # Should return "No file index found" since no index exists in test
        assert (
            "No file index found for repository: owner/newrepo"
            in response.body.decode()
        )

    def test_missing_repository_full_name(self, session: Session):
        """Test handling when repository full_name is missing."""
        payload = {"action": "deleted", "repository": {}}

        response = handle_repository_event(payload, session)

        assert response.status_code == 400
        assert "missing repository full_name" in response.body.decode()

    def test_unknown_action(self, session: Session):
        """Test handling of unknown repository actions."""
        payload = {
            "action": "unknown_action",
            "repository": {"full_name": "owner/repo"},
        }

        response = handle_repository_event(payload, session)

        assert response.status_code == 200
        assert "unknown_action" in response.body.decode()


class TestHandlePushEvent:
    """Test push event handling for file index updates."""

    def test_push_event_success(self, session: Session, user: User):
        """Test successful push event handling with file index update."""
        # Create GitHub installation
        installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(installation)
        session.commit()

        # Create repository file index
        repo_index = RepositoryFileIndex(
            github_installation_id=installation.id,
            repository_full_name="owner/repo",
            file_search_string="@old/file.py\n@README.md",
            last_indexed_commit_sha="old_commit_sha",
        )
        session.add(repo_index)
        session.commit()

        # Mock push payload
        payload = {
            "repository": {"full_name": "owner/repo"},
            "after": "new_commit_sha",
            "ref": "refs/heads/main",
        }

        # Mock GitHub API response
        mock_file_tree_response = {
            "sha": "tree_sha",
            "tree": [
                {"path": "src/main.py", "type": "blob"},
                {"path": "README.md", "type": "blob"},
            ],
        }

        with (
            patch(
                "src.github_app.webhook_controller.GitHubService.get_file_tree"
            ) as mock_get_file_tree,
            patch(
                "src.github_app.webhook_controller.GitHubService.generate_file_search_string"
            ) as mock_generate_search_string,
        ):
            mock_get_file_tree.return_value = mock_file_tree_response
            mock_generate_search_string.return_value = "@README.md\n@src/main.py"

            now = datetime.now()
            response = handle_push_event(payload, session)

            # Verify response
            assert response.status_code == 200
            assert "File index updated successfully" in response.body.decode()

            # Verify GitHub API was called
            mock_get_file_tree.assert_called_once_with(
                "12345", "owner", "repo", recursive=True
            )
            mock_generate_search_string.assert_called_once_with(
                mock_file_tree_response, "repo", False
            )

            # Verify database was updated
            session.refresh(repo_index)
            assert repo_index.last_indexed_commit_sha == "new_commit_sha"
            assert repo_index.file_search_string == "@README.md\n@src/main.py"
            assert repo_index.updated_at >= now

    def test_push_event_no_changes(self, session: Session, user: User):
        """Test push event when commit SHA hasn't changed."""
        # Create GitHub installation
        installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(installation)
        session.commit()

        # Create repository file index with same commit SHA
        repo_index = RepositoryFileIndex(
            github_installation_id=installation.id,
            repository_full_name="owner/repo",
            file_search_string="@old/file.py\n@README.md",
            last_indexed_commit_sha="same_commit_sha",
        )
        session.add(repo_index)
        session.commit()

        # Mock push payload with same commit SHA
        payload = {
            "repository": {"full_name": "owner/repo"},
            "after": "same_commit_sha",
            "ref": "refs/heads/main",
        }

        with patch(
            "src.github_app.webhook_controller.GitHubService.get_file_tree"
        ) as mock_get_file_tree:
            response = handle_push_event(payload, session)

            # Verify response indicates no update needed
            assert response.status_code == 200
            assert "already up to date" in response.body.decode()

            # Verify GitHub API was NOT called (performance optimization)
            mock_get_file_tree.assert_not_called()

            # Verify database was NOT changed
            session.refresh(repo_index)
            assert repo_index.last_indexed_commit_sha == "same_commit_sha"
            assert repo_index.file_search_string == "@old/file.py\n@README.md"

    def test_push_event_repository_not_found(self, session: Session):
        """Test push event for repository not in file index."""
        payload = {
            "repository": {"full_name": "owner/nonexistent-repo"},
            "after": "new_commit_sha",
            "ref": "refs/heads/main",
        }

        response = handle_push_event(payload, session)

        # Verify response indicates repository not found
        assert response.status_code == 200
        assert "No file index found for repository" in response.body.decode()

    def test_push_event_branch_deletion(self, session: Session):
        """Test push event for branch deletion (commit SHA is all zeros)."""
        payload = {
            "repository": {"full_name": "owner/repo"},
            "after": "0000000000000000000000000000000000000000",
            "ref": "refs/heads/feature-branch",
        }

        response = handle_push_event(payload, session)

        # Verify branch deletion is handled gracefully
        assert response.status_code == 200
        assert "Branch deletion processed" in response.body.decode()

    def test_push_event_missing_repository_name(self, session: Session):
        """Test push event with missing repository full_name."""
        payload = {
            "repository": {},  # Missing full_name
            "after": "new_commit_sha",
            "ref": "refs/heads/main",
        }

        response = handle_push_event(payload, session)

        # Verify error response
        assert response.status_code == 400
        assert "missing repository full_name" in response.body.decode()

    def test_push_event_missing_commit_sha(self, session: Session):
        """Test push event with missing commit SHA."""
        payload = {
            "repository": {"full_name": "owner/repo"},
            # Missing "after" field
            "ref": "refs/heads/main",
        }

        response = handle_push_event(payload, session)

        # Verify error response
        assert response.status_code == 400
        assert "missing commit SHA" in response.body.decode()

    def test_push_event_github_api_error(self, session: Session, user: User):
        """Test push event when GitHub API returns an error."""
        # Create GitHub installation
        installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(installation)
        session.commit()

        # Create repository file index
        repo_index = RepositoryFileIndex(
            github_installation_id=installation.id,
            repository_full_name="owner/repo",
            file_search_string="@old/file.py",
            last_indexed_commit_sha="old_commit_sha",
        )
        session.add(repo_index)
        session.commit()

        payload = {
            "repository": {"full_name": "owner/repo"},
            "after": "new_commit_sha",
            "ref": "refs/heads/main",
        }

        # Mock GitHub API error
        with patch(
            "src.github_app.webhook_controller.GitHubService.get_file_tree"
        ) as mock_get_file_tree:
            mock_get_file_tree.return_value = {"error": "Repository not found"}

            response = handle_push_event(payload, session)

            # Verify graceful error handling
            assert response.status_code == 200
            assert "GitHub API error" in response.body.decode()

            # Verify database was NOT updated due to API error
            session.refresh(repo_index)
            assert repo_index.last_indexed_commit_sha == "old_commit_sha"

    def test_push_event_multi_repo_prefixing(self, session: Session, user: User):
        """Test push event with multi-repository prefixing strategy."""
        # Create GitHub installation
        installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(installation)
        session.commit()

        # Create multiple repository file indexes to trigger multi-repo prefixing
        repo_index1 = RepositoryFileIndex(
            github_installation_id=installation.id,
            repository_full_name="owner/repo1",
            file_search_string="@repo1/file.py",
            last_indexed_commit_sha="old_commit_sha",
        )
        repo_index2 = RepositoryFileIndex(
            github_installation_id=installation.id,
            repository_full_name="owner/repo2",
            file_search_string="@repo2/file.py",
            last_indexed_commit_sha="old_commit_sha",
        )
        session.add_all([repo_index1, repo_index2])
        session.commit()

        payload = {
            "repository": {"full_name": "owner/repo1"},
            "after": "new_commit_sha",
            "ref": "refs/heads/main",
        }

        # Mock GitHub API response
        mock_file_tree_response = {"tree": [{"path": "src/main.py", "type": "blob"}]}

        with (
            patch(
                "src.github_app.webhook_controller.GitHubService.get_file_tree"
            ) as mock_get_file_tree,
            patch(
                "src.github_app.webhook_controller.GitHubService.generate_file_search_string"
            ) as mock_generate_search_string,
        ):
            mock_get_file_tree.return_value = mock_file_tree_response
            mock_generate_search_string.return_value = "@repo1/src/main.py"

            response = handle_push_event(payload, session)

            # Verify response
            assert response.status_code == 200

            # Verify multi-repo prefixing was used (use_repo_prefix=True)
            mock_generate_search_string.assert_called_once_with(
                mock_file_tree_response, "repo1", True
            )


# Tests for new helper functions and enhanced webhook handlers


class TestInstallationSuspensionHelpers:
    """Test the installation suspension/unsuspension helper functions."""

    def test_handle_installation_suspended_success(self, session: Session, user: User):
        """Test successful installation suspension helper function."""
        # Create GitHub installation with repository file indexes
        github_installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(github_installation)
        session.commit()
        session.refresh(github_installation)

        # Create repository file indexes
        repo_index1 = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/repo1",
            file_search_string="@file1.py",
        )
        repo_index2 = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/repo2",
            file_search_string="@file2.py",
        )
        session.add_all([repo_index1, repo_index2])
        session.commit()

        # Suspend installation
        response = _handle_installation_suspended(12345, session)

        # Verify response
        assert response.status_code == 200
        assert "removed 2 repository file indexes" in response.body.decode()

        # Verify all repository file indexes were deleted
        remaining_indexes = (
            session.query(RepositoryFileIndex)
            .filter(
                RepositoryFileIndex.github_installation_id == github_installation.id
            )
            .all()
        )
        assert len(remaining_indexes) == 0

    def test_handle_installation_suspended_not_found(self, session: Session):
        """Test installation suspension helper when installation not found."""
        response = _handle_installation_suspended(99999, session)

        assert response.status_code == 200
        assert "Installation not found" in response.body.decode()

    def test_handle_installation_unsuspended_success(
        self, session: Session, user: User
    ):
        """Test successful installation unsuspension helper function."""
        # Create GitHub installation
        github_installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(github_installation)
        session.commit()

        # Mock GitHub API responses
        mock_repositories = [
            {"full_name": "owner/repo1"},
            {"full_name": "owner/repo2"},
        ]

        with (
            patch(
                "src.github_app.webhook_controller.GitHubService.get_user_repositories"
            ) as mock_get_repos,
            patch(
                "src.github_app.webhook_controller._create_repository_file_index"
            ) as mock_create_index,
            patch(
                "src.github_app.webhook_controller._update_prefixing_strategy"
            ) as mock_update_prefixing,
        ):
            mock_get_repos.return_value = mock_repositories
            mock_create_index.return_value = True

            response = _handle_installation_unsuspended(12345, session)

            # Verify response
            assert response.status_code == 200
            assert "recreated 2/2 repository file indexes" in response.body.decode()

            # Verify helper functions were called correctly
            mock_get_repos.assert_called_once_with("12345")
            assert mock_create_index.call_count == 2
            mock_update_prefixing.assert_called_once_with("12345", session)

    def test_handle_installation_unsuspended_not_found(self, session: Session):
        """Test installation unsuspension helper when installation not found."""
        response = _handle_installation_unsuspended(99999, session)

        assert response.status_code == 200
        assert "Installation not found" in response.body.decode()

    def test_handle_installation_unsuspended_github_error(
        self, session: Session, user: User
    ):
        """Test installation unsuspension helper when GitHub API fails."""
        # Create GitHub installation
        github_installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(github_installation)
        session.commit()

        with patch(
            "src.github_app.webhook_controller.GitHubService.get_user_repositories"
        ) as mock_get_repos:
            mock_get_repos.side_effect = Exception("GitHub API error")

            response = _handle_installation_unsuspended(12345, session)

            # Verify graceful error handling
            assert response.status_code == 200
            assert "Error retrieving repositories from GitHub" in response.body.decode()


class TestRepositoryFileIndexHelpers:
    """Test the new helper functions for repository file index management."""

    def test_get_repository_count_for_installation(self, session: Session, user: User):
        """Test getting repository count for an installation."""
        from src.github_app.webhook_controller import (
            _get_repository_count_for_installation,
        )

        # Create GitHub installation
        github_installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(github_installation)
        session.commit()
        session.refresh(github_installation)

        # Initially should be 0 repositories
        count = _get_repository_count_for_installation("12345", session)
        assert count == 0

        # Add repository file indexes
        repo_index1 = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/repo1",
            file_search_string="@file1.py",
        )
        repo_index2 = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/repo2",
            file_search_string="@file2.py",
        )
        session.add_all([repo_index1, repo_index2])
        session.commit()

        # Should now return 2
        count = _get_repository_count_for_installation("12345", session)
        assert count == 2

        # Test with non-existent installation
        count = _get_repository_count_for_installation("99999", session)
        assert count == 0

    def test_create_repository_file_index_success(self, session: Session, user: User):
        """Test successful creation of repository file index."""
        from src.github_app.webhook_controller import _create_repository_file_index

        # Create GitHub installation
        github_installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(github_installation)
        session.commit()

        # Mock GitHub API response
        mock_file_tree_response = {
            "tree": [
                {"path": "src/main.py", "type": "blob"},
                {"path": "README.md", "type": "blob"},
            ],
            "sha": "abc123",
        }

        with (
            patch(
                "src.github_app.webhook_controller.GitHubService.get_file_tree"
            ) as mock_get_file_tree,
            patch(
                "src.github_app.webhook_controller.GitHubService.generate_file_search_string"
            ) as mock_generate_search_string,
        ):
            mock_get_file_tree.return_value = mock_file_tree_response
            mock_generate_search_string.return_value = "@README.md\n@src/main.py"

            # Create file index
            result = _create_repository_file_index("12345", "owner/repo1", session)
            assert result is True

            # Verify the file index was created
            repo_index = (
                session.query(RepositoryFileIndex)
                .filter(RepositoryFileIndex.repository_full_name == "owner/repo1")
                .first()
            )
            assert repo_index is not None
            assert repo_index.file_search_string == "@README.md\n@src/main.py"
            assert repo_index.last_indexed_commit_sha == "abc123"

    def test_create_repository_file_index_already_exists(
        self, session: Session, user: User
    ):
        """Test creating file index when it already exists."""
        from src.github_app.webhook_controller import _create_repository_file_index

        # Create GitHub installation
        github_installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(github_installation)
        session.commit()
        session.refresh(github_installation)

        # Create existing file index
        existing_index = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/repo1",
            file_search_string="@existing.py",
        )
        session.add(existing_index)
        session.commit()

        # Attempt to create again
        result = _create_repository_file_index("12345", "owner/repo1", session)
        assert result is True  # Should return True (already exists)

        # Verify only one index exists
        repo_indexes = (
            session.query(RepositoryFileIndex)
            .filter(RepositoryFileIndex.repository_full_name == "owner/repo1")
            .all()
        )
        assert len(repo_indexes) == 1

    def test_delete_repository_file_index_success(self, session: Session, user: User):
        """Test successful deletion of repository file index."""
        from src.github_app.webhook_controller import _delete_repository_file_index

        # Create GitHub installation and file index
        github_installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(github_installation)
        session.commit()
        session.refresh(github_installation)

        repo_index = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/repo1",
            file_search_string="@file1.py",
        )
        session.add(repo_index)
        session.commit()

        # Delete the file index
        result = _delete_repository_file_index("owner/repo1", session)
        assert result is True

        # Verify it was deleted
        repo_index = (
            session.query(RepositoryFileIndex)
            .filter(RepositoryFileIndex.repository_full_name == "owner/repo1")
            .first()
        )
        assert repo_index is None

    def test_delete_repository_file_index_not_found(self, session: Session):
        """Test deleting non-existent repository file index."""
        from src.github_app.webhook_controller import _delete_repository_file_index

        # Should succeed even if index doesn't exist
        result = _delete_repository_file_index("owner/nonexistent", session)
        assert result is True

    def test_update_prefixing_strategy(self, session: Session, user: User):
        """Test updating prefixing strategy for multiple repositories."""
        from src.github_app.webhook_controller import _update_prefixing_strategy

        # Create GitHub installation
        github_installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(github_installation)
        session.commit()
        session.refresh(github_installation)

        # Create multiple repository file indexes
        repo_index1 = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/repo1",
            file_search_string="@old_file1.py",
        )
        repo_index2 = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/repo2",
            file_search_string="@old_file2.py",
        )
        session.add_all([repo_index1, repo_index2])
        session.commit()

        # Mock GitHub API responses
        mock_file_tree_response1 = {
            "tree": [{"path": "src/main.py", "type": "blob"}],
            "sha": "abc123",
        }
        mock_file_tree_response2 = {
            "tree": [{"path": "src/test.py", "type": "blob"}],
            "sha": "def456",
        }

        with (
            patch(
                "src.github_app.webhook_controller.GitHubService.get_file_tree"
            ) as mock_get_file_tree,
            patch(
                "src.github_app.webhook_controller.GitHubService.generate_file_search_string"
            ) as mock_generate_search_string,
        ):
            # Mock file tree responses for each repo
            mock_get_file_tree.side_effect = [
                mock_file_tree_response1,
                mock_file_tree_response2,
            ]
            # Mock search string generation with multi-repo prefix
            mock_generate_search_string.side_effect = [
                "@repo1/src/main.py",
                "@repo2/src/test.py",
            ]

            # Update prefixing strategy
            result = _update_prefixing_strategy("12345", session)
            assert result is True

            # Verify prefixing was updated (multi-repo format)
            session.refresh(repo_index1)
            session.refresh(repo_index2)
            assert repo_index1.file_search_string == "@repo1/src/main.py"
            assert repo_index2.file_search_string == "@repo2/src/test.py"

            # Verify generate_file_search_string was called with use_repo_prefix=True
            assert mock_generate_search_string.call_count == 2
            mock_generate_search_string.assert_any_call(
                mock_file_tree_response1, "repo1", True
            )
            mock_generate_search_string.assert_any_call(
                mock_file_tree_response2, "repo2", True
            )


class TestEnhancedWebhookHandlers:
    """Test the enhanced webhook handlers for repository management."""

    def test_handle_repositories_added_success(self, session: Session, user: User):
        """Test successful handling of repositories added event."""
        from src.github_app.webhook_controller import _handle_repositories_added

        # Create GitHub installation
        github_installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(github_installation)
        session.commit()

        # Mock repository payload
        repositories = [
            {"full_name": "owner/repo1"},
            {"full_name": "owner/repo2"},
        ]

        with (
            patch(
                "src.github_app.webhook_controller._create_repository_file_index"
            ) as mock_create_index,
            patch(
                "src.github_app.webhook_controller._update_prefixing_strategy"
            ) as mock_update_prefixing,
        ):
            mock_create_index.return_value = True

            response = _handle_repositories_added(12345, repositories, session)

            # Verify response
            assert response.status_code == 200
            assert "2/2 repositories processed successfully" in response.body.decode()

            # Verify helper functions were called
            assert mock_create_index.call_count == 2
            mock_create_index.assert_any_call("12345", "owner/repo1", session)
            mock_create_index.assert_any_call("12345", "owner/repo2", session)
            mock_update_prefixing.assert_called_once_with("12345", session)

    def test_handle_repositories_removed_success(self, session: Session, user: User):
        """Test successful handling of repositories removed event."""
        from src.github_app.webhook_controller import _handle_repositories_removed

        # Mock repository payload
        repositories = [
            {"full_name": "owner/repo1"},
            {"full_name": "owner/repo2"},
        ]

        with (
            patch(
                "src.github_app.webhook_controller._delete_repository_file_index"
            ) as mock_delete_index,
            patch(
                "src.github_app.webhook_controller._update_prefixing_strategy"
            ) as mock_update_prefixing,
        ):
            mock_delete_index.return_value = True

            response = _handle_repositories_removed(12345, repositories, session)

            # Verify response
            assert response.status_code == 200
            assert "2/2 repositories processed successfully" in response.body.decode()

            # Verify helper functions were called
            assert mock_delete_index.call_count == 2
            mock_delete_index.assert_any_call("owner/repo1", session)
            mock_delete_index.assert_any_call("owner/repo2", session)
            mock_update_prefixing.assert_called_once_with("12345", session)

    def test_handle_repository_deleted_success(self, session: Session, user: User):
        """Test successful handling of repository deleted event."""
        from src.github_app.webhook_controller import _handle_repository_deleted

        # Create GitHub installation and repository file index
        github_installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(github_installation)
        session.commit()
        session.refresh(github_installation)

        repo_index = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/repo1",
            file_search_string="@file1.py",
        )
        session.add(repo_index)
        session.commit()

        with (
            patch(
                "src.github_app.webhook_controller._delete_repository_file_index"
            ) as mock_delete_index,
            patch(
                "src.github_app.webhook_controller._update_prefixing_strategy"
            ) as mock_update_prefixing,
        ):
            mock_delete_index.return_value = True

            response = _handle_repository_deleted("owner/repo1", session)

            # Verify response
            assert response.status_code == 200
            assert "successfully" in response.body.decode()

            # Verify helper functions were called
            mock_delete_index.assert_called_once_with("owner/repo1", session)
            mock_update_prefixing.assert_called_once_with("12345", session)

    def test_handle_repository_updated_success(self, session: Session, user: User):
        """Test successful handling of repository updated event."""
        from src.github_app.webhook_controller import _handle_repository_updated

        # Create GitHub installation and repository file index
        github_installation = GitHubInstallation(user=user, installation_id="12345")
        session.add(github_installation)
        session.commit()
        session.refresh(github_installation)

        repo_index = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/old-repo",
            file_search_string="@old_file.py",
            last_indexed_commit_sha="old_sha",
        )
        session.add(repo_index)
        session.commit()

        # Mock repository update payload (renamed repository)
        repository_payload = {"full_name": "owner/new-repo"}

        # Mock GitHub API response
        mock_file_tree_response = {
            "tree": [{"path": "src/main.py", "type": "blob"}],
            "sha": "new_sha",
        }

        with (
            patch(
                "src.github_app.webhook_controller.GitHubService.get_file_tree"
            ) as mock_get_file_tree,
            patch(
                "src.github_app.webhook_controller.GitHubService.generate_file_search_string"
            ) as mock_generate_search_string,
            patch(
                "src.github_app.webhook_controller._get_repository_count_for_installation"
            ) as mock_get_count,
        ):
            mock_get_file_tree.return_value = mock_file_tree_response
            mock_generate_search_string.return_value = "@new-repo/src/main.py"
            mock_get_count.return_value = 1

            response = _handle_repository_updated(
                "owner/old-repo", repository_payload, session
            )

            # Verify response
            assert response.status_code == 200
            assert "successfully" in response.body.decode()

            # Verify the repository file index was updated
            session.refresh(repo_index)
            assert repo_index.repository_full_name == "owner/new-repo"
            assert repo_index.file_search_string == "@new-repo/src/main.py"
            assert repo_index.last_indexed_commit_sha == "new_sha"

    def test_handle_repository_updated_not_found(self, session: Session):
        """Test handling repository updated when file index doesn't exist."""
        from src.github_app.webhook_controller import _handle_repository_updated

        repository_payload = {"full_name": "owner/repo"}

        response = _handle_repository_updated(
            "owner/nonexistent", repository_payload, session
        )

        # Should return 200 with info message
        assert response.status_code == 200
        assert "No file index found" in response.body.decode()


class TestHandleInstallationTargetEvent:
    """Test installation target event handling."""

    def test_handle_installation_target_renamed_action(self, session: Session):
        """Test that installation_target renamed actions are handled correctly."""
        payload = {
            "action": "renamed",
            "installation": {"id": 12345},
            "changes": {"login": {"from": "oldname"}},
            "account": {"login": "newname"},
        }

        with patch(
            "src.github_app.webhook_controller._handle_installation_target_renamed"
        ) as mock_handler:
            mock_handler.return_value = Response(content="test", status_code=200)

            response = handle_installation_target_event(payload, session)

            mock_handler.assert_called_once_with(payload, session)
            assert response.status_code == 200

    def test_handle_installation_target_unknown_action(self, session: Session):
        """Test handling of unknown installation_target actions."""
        payload = {
            "action": "unknown_action",
            "installation": {"id": 12345},
        }

        response = handle_installation_target_event(payload, session)

        assert response.status_code == 200
        assert "received" in response.body.decode()

    def test_handle_installation_target_missing_installation_id(self, session: Session):
        """Test handling of installation_target event missing installation ID."""
        payload = {
            "action": "renamed",
            "changes": {"login": {"from": "oldname"}},
            "account": {"login": "newname"},
        }

        response = handle_installation_target_event(payload, session)

        assert response.status_code == 400
        assert "missing installation ID" in response.body.decode()


class TestHandleInstallationTargetRenamed:
    """Test installation target rename handling."""

    def test_successful_account_rename(self, session: Session, user: User):
        """Test successful account rename updates repository names."""
        # Create GitHub installation
        github_installation = GitHubInstallation(
            installation_id="12345",
            user_id=user.id,
        )
        session.add(github_installation)
        session.commit()

        # Create repository file indexes with old account name
        repo1 = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="oldname/repo1",
            file_search_string="@repo1/src/main.py\n@repo1/README.md",
            last_indexed_commit_sha="abc123",
        )
        repo2 = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="oldname/repo2",
            file_search_string="@repo2/src/app.py",
            last_indexed_commit_sha="def456",
        )
        # Add a repository from different account (should not be updated)
        other_repo = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="othername/repo3",
            file_search_string="@repo3/src/util.py",
            last_indexed_commit_sha="ghi789",
        )
        session.add_all([repo1, repo2, other_repo])
        session.commit()

        # Create webhook payload
        payload = {
            "action": "renamed",
            "installation": {"id": 12345},
            "changes": {"login": {"from": "oldname"}},
            "account": {"login": "newname"},
        }

        response = _handle_installation_target_renamed(payload, session)

        # Verify response
        assert response.status_code == 200
        assert "updated 2 repositories" in response.body.decode()
        assert "oldname" in response.body.decode()
        assert "newname" in response.body.decode()

        # Verify repository names were updated
        session.refresh(repo1)
        session.refresh(repo2)
        session.refresh(other_repo)

        assert repo1.repository_full_name == "newname/repo1"
        assert repo2.repository_full_name == "newname/repo2"
        assert other_repo.repository_full_name == "othername/repo3"  # Unchanged

        # Verify file search strings are preserved
        assert repo1.file_search_string == "@repo1/src/main.py\n@repo1/README.md"
        assert repo2.file_search_string == "@repo2/src/app.py"
        assert other_repo.file_search_string == "@repo3/src/util.py"

    def test_missing_required_fields(self, session: Session):
        """Test handling of payload missing required fields."""
        # Missing old account name
        payload1 = {
            "action": "renamed",
            "installation": {"id": 12345},
            "account": {"login": "newname"},
        }

        response1 = _handle_installation_target_renamed(payload1, session)
        assert response1.status_code == 400
        assert "missing required fields" in response1.body.decode()

        # Missing new account name
        payload2 = {
            "action": "renamed",
            "installation": {"id": 12345},
            "changes": {"login": {"from": "oldname"}},
        }

        response2 = _handle_installation_target_renamed(payload2, session)
        assert response2.status_code == 400
        assert "missing required fields" in response2.body.decode()

        # Missing installation ID
        payload3 = {
            "action": "renamed",
            "changes": {"login": {"from": "oldname"}},
            "account": {"login": "newname"},
        }

        response3 = _handle_installation_target_renamed(payload3, session)
        assert response3.status_code == 400
        assert "missing required fields" in response3.body.decode()

    def test_installation_not_found(self, session: Session):
        """Test handling when GitHub installation is not found in database."""
        payload = {
            "action": "renamed",
            "installation": {"id": 99999},  # Non-existent installation
            "changes": {"login": {"from": "oldname"}},
            "account": {"login": "newname"},
        }

        response = _handle_installation_target_renamed(payload, session)

        assert response.status_code == 200
        assert "Installation not found" in response.body.decode()

    def test_no_repositories_to_update(self, session: Session, user: User):
        """Test handling when no repositories match the old account name."""
        # Create GitHub installation
        github_installation = GitHubInstallation(
            installation_id="12345",
            user_id=user.id,
        )
        session.add(github_installation)
        session.commit()

        # Create repository with different account name
        repo = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="differentname/repo1",
            file_search_string="@repo1/src/main.py",
            last_indexed_commit_sha="abc123",
        )
        session.add(repo)
        session.commit()

        # Create webhook payload for different account
        payload = {
            "action": "renamed",
            "installation": {"id": 12345},
            "changes": {"login": {"from": "oldname"}},
            "account": {"login": "newname"},
        }

        response = _handle_installation_target_renamed(payload, session)

        # Should still return success with 0 repositories updated
        assert response.status_code == 200
        assert "updated 0 repositories" in response.body.decode()

        # Verify repository name was not changed
        session.refresh(repo)
        assert repo.repository_full_name == "differentname/repo1"

    def test_exception_handling(self, session: Session):
        """Test that exceptions are handled gracefully."""
        payload = {
            "action": "renamed",
            "installation": {"id": 12345},
            "changes": {"login": {"from": "oldname"}},
            "account": {"login": "newname"},
        }

        # Force an exception by mocking db.query to raise
        with patch.object(session, "query", side_effect=Exception("Database error")):
            response = _handle_installation_target_renamed(payload, session)

            assert response.status_code == 500
            assert (
                "Error processing installation target rename" in response.body.decode()
            )
