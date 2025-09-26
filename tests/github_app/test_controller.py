from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from hamcrest import assert_that, equal_to, is_, not_
from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.github_app.controller import (
    GithubAppInstallationCallback,
    fetch_token_for_installation,
    get_installation_token,
    get_repositories_template,
    handle_installation_callback,
    install_github_app_redirect,
    populate_initial_file_index,
    revoke_installation_access,
    uninstall_github_app,
)
from src.github_app.models import RepositoryFileIndex
from src.github_app.webhook_controller import handle_github_webhook
from src.models import GitHubInstallation, User, Workspace


@pytest.fixture
def github_installation(session: Session, user: User, workspace: Workspace):
    installation = GitHubInstallation(
        user=user,
        installation_id="12345",
        workspace=workspace,
        workspace_id=workspace.id,
        user_id=user.id,
    )
    session.add(installation)
    session.commit()
    yield installation
    session.delete(installation)


class TestGetRepositoriesTemplate:
    @patch(
        "src.main.templates.TemplateResponse",
        return_value=HTMLResponse("<html></html>"),
    )
    @patch(
        "src.github_app.github_service.GitHubService.get_user_repositories",
        return_value=[{"name": "test-repo"}],
    )
    def test_get_repositories_template_with_installation(
        self, mock_get_repos: MagicMock, mock_template_response: MagicMock, user: User
    ):
        request = MagicMock()
        db = MagicMock()

        # Mock a GitHub installation
        github_installation = MagicMock()
        github_installation.installation_id = "12345"

        # Setup the db query to return the installation
        db.query.return_value.filter.return_value.first.return_value = (
            github_installation
        )

        result = get_repositories_template(request, user, db)

        # Verify the template was called with correct parameters
        mock_template_response.assert_called_once_with(
            request,
            "pages/repositories.html",
            {
                "user": user,
                "has_github_installation": True,
                "repositories": [{"name": "test-repo"}],
            },
        )
        assert isinstance(result, HTMLResponse)

        # Verify the GitHub API was called
        mock_get_repos.assert_called_once_with("12345")

    @patch(
        "src.main.templates.TemplateResponse",
        return_value=HTMLResponse("<html></html>"),
    )
    def test_get_repositories_template_without_installation(
        self, mock_template_response: MagicMock, user: User
    ):
        request = MagicMock()
        db = MagicMock()

        # Setup the db query to return no installation
        db.query.return_value.filter.return_value.first.return_value = None

        result = get_repositories_template(request, user, db)

        # Verify the template was called with correct parameters
        mock_template_response.assert_called_once_with(
            request,
            "pages/repositories.html",
            {"user": user, "has_github_installation": False, "repositories": []},
        )
        assert isinstance(result, HTMLResponse)

    @patch("src.main.templates.TemplateResponse")
    @patch("src.github_app.github_service.GitHubService.get_user_repositories")
    def test_rendering_the_user_repositories(
        self,
        mockGetUserRepos: MagicMock,
        mockTemplateResponse: MagicMock,
        user: User,
        session: Session,
        github_installation: GitHubInstallation,
    ):
        request = MagicMock()

        mockGetUserRepos.return_value = [{"name": "test-repo"}]

        get_repositories_template(request, user, session)

        mockTemplateResponse.assert_called_once_with(
            request,
            "pages/repositories.html",
            {
                "user": user,
                "has_github_installation": True,
                "repositories": [{"name": "test-repo"}],
            },
        )

        mockGetUserRepos.assert_called_once_with("12345")


class TestInstallGithubAppRedirect:
    def test_install_github_app_redirect(self):
        response = install_github_app_redirect()
        assert_that(response.status_code, equal_to(307))

        expected_url = (
            "https://github.com/apps/samboyd-taskmanagement-dev/installations/new"
        )
        assert_that(response.headers.get("Location"), equal_to(expected_url))


class TestHandleInstallationCallback:
    @patch("src.github_app.controller.populate_initial_file_index")
    @patch("src.github_app.github_service.GitHubService.get_installation_token")
    def test_handle_installation_callback(
        self,
        mock_get_token: MagicMock,
        mock_populate_index: MagicMock,
        session: Session,
        user: User,
    ):
        # Mock successful token retrieval
        mock_get_token.return_value = {"token": "ghs_valid_token"}

        response = handle_installation_callback(
            callback_payload=GithubAppInstallationCallback(
                installation_id="12345", code="abc", setup_action="install"
            ),
            user=user,
            session=session,
        )
        assert_that(response.status_code, equal_to(302))
        # Verify the redirect location is the repositories route
        assert_that(response.headers.get("location"), equal_to("/account"))

        loaded_installation = session.query(GitHubInstallation).first()
        assert_that(loaded_installation.installation_id, equal_to("12345"))
        assert_that(loaded_installation.user, equal_to(user))

        with pytest.raises(ValidationError):
            handle_installation_callback(
                callback_payload=GithubAppInstallationCallback(
                    installation_id=None, code="abc", setup_action="install"  # type: ignore
                ),
                user=user,
                session=session,
            )


class TestGetInstallationToken:
    @patch("src.github_app.github_service.GitHubService.get_installation_token")
    def test_get_installation_token(self, mock_get_service_token: MagicMock):
        # Mock the service method
        mock_get_service_token.return_value = {
            "token": "ghs_16C7e42F292c6912E7710c838347Ae178B4a",
            "expires_at": "2021-07-11T22:14:10Z",
        }

        # Call the controller wrapper function
        result = get_installation_token("12345")

        # Verify service was called with correct params
        mock_get_service_token.assert_called_once_with("12345")

        # Verify result was passed through
        assert_that(
            result["token"], equal_to("ghs_16C7e42F292c6912E7710c838347Ae178B4a")
        )


class TestFetchTokenForInstallation:
    @patch("src.github_app.github_service.GitHubService.fetch_token_for_installation")
    def test_fetch_token_for_installation(self, mock_fetch_token: MagicMock):
        # Mock the service method
        mock_fetch_token.return_value = {
            "token": "ghs_16C7e42F292c6912E7710c838347Ae178B4a",
            "expires_at": "2021-07-11T22:14:10Z",
        }

        # Call the controller wrapper function
        result = fetch_token_for_installation("12345")

        # Verify service was called with correct params
        mock_fetch_token.assert_called_once_with("12345")

        # Verify result was passed through
        assert_that(
            result["token"], equal_to("ghs_16C7e42F292c6912E7710c838347Ae178B4a")
        )


class TestUninstallGithubApp:
    def test_uninstall_github_app(
        self, session: Session, user: User, github_installation: GitHubInstallation
    ):
        # Verify the installation exists before uninstalling
        installation_before = (
            session.query(GitHubInstallation)
            .filter(GitHubInstallation.user_id == user.id)
            .first()
        )
        assert_that(installation_before is not None)
        assert_that(installation_before.installation_id, equal_to("12345"))

        # Call the function to uninstall
        response = uninstall_github_app(user, session)

        # Verify the response is a redirect to repositories page
        assert_that(response.status_code, equal_to(302))
        assert_that(response.headers.get("location"), equal_to("/repositories"))

        # Verify the installation was deleted
        installation_after = (
            session.query(GitHubInstallation)
            .filter(GitHubInstallation.user_id == user.id)
            .first()
        )
        assert_that(installation_after is None)


class TestRevokeInstallationAccess:
    @patch("src.github_app.github_service.GitHubService.revoke_installation_access")
    def test_revoke_installation_access(self, mock_service_revoke: MagicMock):
        # Mock the service method
        mock_service_revoke.return_value = True

        # Call the wrapper function
        result = revoke_installation_access("12345")

        # Verify service was called with correct params
        mock_service_revoke.assert_called_once_with("12345")

        # Verify result was passed through
        assert_that(result, equal_to(True))


class TestUninstallGithubAppWithRevocation:
    @patch("src.github_app.github_service.GitHubService.revoke_installation_access")
    def test_uninstall_github_app_with_revocation(
        self,
        mock_revoke_access: MagicMock,
        session: Session,
        user: User,
        github_installation: GitHubInstallation,
    ):
        # Mock the access revocation
        mock_revoke_access.return_value = True

        # Call the function to uninstall
        uninstall_github_app(user, session)

        # Verify the access was revoked with the correct installation ID
        mock_revoke_access.assert_called_with("12345")

        # Verify the installation was deleted
        installation_after = (
            session.query(GitHubInstallation)
            .filter(GitHubInstallation.user_id == user.id)
            .first()
        )
        assert_that(installation_after is None)

    @patch("src.github_app.github_service.GitHubService.revoke_installation_access")
    def test_uninstall_github_app_with_revocation_error(
        self,
        mock_revoke_access: MagicMock,
        session: Session,
        user: User,
        github_installation: GitHubInstallation,
    ):
        # Mock an error in access revocation
        mock_revoke_access.side_effect = Exception("API rate limit exceeded")

        # Call the function to uninstall
        uninstall_github_app(user, session)

        # Verify the installation was still deleted despite the revocation error
        installation_after = (
            session.query(GitHubInstallation)
            .filter(GitHubInstallation.user_id == user.id)
            .first()
        )
        assert_that(installation_after, is_(not_(None)))


class TestHandleGithubWebhook:
    @patch("src.github_app.github_service.GitHubService.revoke_installation_access")
    def test_handle_github_webhook_installation_deleted(
        self,
        mock_revoke_access: MagicMock,
        session: Session,
        github_installation: GitHubInstallation,
    ):
        installation_id = github_installation.installation_id

        # Mock the revoke access method
        mock_revoke_access.return_value = True

        # Create a webhook payload for installation deletion
        payload = {
            "action": "deleted",
            "installation": {"id": int(installation_id)},
            "repositories": [],
        }

        # Call the webhook handler
        response = handle_github_webhook(payload, "installation", session)

        # Verify the response
        assert_that(response.status_code, equal_to(200))
        assert_that(
            response.body.decode(), equal_to("Installation deleted successfully")
        )

        # Verify the installation was deleted from the database
        installation_after = (
            session.query(GitHubInstallation)
            .filter(GitHubInstallation.installation_id == installation_id)
            .first()
        )
        assert_that(installation_after, equal_to(None))

        # Verify the service was called to revoke access
        mock_revoke_access.assert_called_once_with(installation_id)

    @patch("src.github_app.github_service.GitHubService.revoke_installation_access")
    def test_handle_github_webhook_installation_deleted_error(
        self,
        mock_revoke_access: MagicMock,
        session: Session,
        user: User,
        github_installation: GitHubInstallation,
    ):
        # Mock the revoke access method to raise an exception
        mock_revoke_access.side_effect = Exception("API error")

        # Create a webhook payload for installation deletion
        payload = {
            "action": "deleted",
            "installation": {"id": int(github_installation.installation_id)},
            "repositories": [],
        }

        # Call the webhook handler
        response = handle_github_webhook(payload, "installation", session)

        # Verify the response indicates an error
        assert_that(response.status_code, equal_to(500))
        assert_that("Error processing installation deletion" in response.body.decode())

        # Verify the installation still exists in the database
        installation_after = (
            session.query(GitHubInstallation)
            .filter(
                GitHubInstallation.installation_id
                == github_installation.installation_id
            )
            .first()
        )
        assert_that(installation_after, equal_to(github_installation))

    def test_handle_github_webhook_other_events(self, session: Session):
        # Test handling of other webhook events
        payload = {"action": "created", "repositories": [], "installation": {}}

        # Call the webhook handler with a different event type
        response = handle_github_webhook(payload, "fork", session)

        # Verify the response
        assert_that(response.status_code, equal_to(200))
        assert_that("fork" in response.body.decode(), is_(True))

    def test_handle_github_webhook_installation_other_action(self, session: Session):
        # Test handling of installation events with actions other than "deleted"
        payload = {
            "action": "created",
            "repositories": [],
            "installation": {"id": 12345},
        }

        # Call the webhook handler
        response = handle_github_webhook(payload, "installation", session)

        # Verify the response
        assert_that(response.status_code, equal_to(200))
        assert_that("created" in response.body.decode(), is_(True))


class TestPopulateInitialFileIndex:
    @patch("src.github_app.github_service.GitHubService.generate_file_search_string")
    @patch("src.github_app.github_service.GitHubService.get_user_repositories")
    @patch("src.github_app.github_service.GitHubService.get_file_tree")
    @patch("src.github_app.github_service.GitHubService.extract_file_paths")
    def test_populate_initial_file_index_multiple_repos(
        self,
        mock_extract_file_paths: MagicMock,
        mock_get_file_tree: MagicMock,
        mock_get_repositories: MagicMock,
        mock_generate_file_search_string: MagicMock,
        session: Session,
        user: User,
        workspace: Workspace,
    ):
        """Test successful file index population for multiple repositories with @RepoName/ prefix."""
        # Setup test data
        github_installation = GitHubInstallation(
            user=user,
            installation_id="12345",
            workspace=workspace,
            workspace_id=workspace.id,
            user_id=user.id,
        )
        session.add(github_installation)
        session.commit()
        session.refresh(github_installation)

        # Mock repository data
        mock_repositories = [
            {"full_name": "test-user/test-repo", "name": "test-repo"},
            {"full_name": "test-user/another-repo", "name": "another-repo"},
        ]
        mock_get_repositories.return_value = mock_repositories

        # Mock file tree response
        mock_file_tree = {
            "sha": "abc123",
            "tree": [
                {"path": "src/main.py", "type": "blob"},
                {"path": "README.md", "type": "blob"},
            ],
        }
        mock_get_file_tree.return_value = mock_file_tree

        # Mock search string generation
        mock_extract_file_paths.return_value = ["README.md", "src/main.py"]

        # Mock generate_file_search_string to return different values based on prefixing
        def generate_search_string_side_effect(
            file_tree_response, repo_name, use_repo_prefix
        ):
            files = ["README.md", "src/main.py"]
            if use_repo_prefix:
                return "\n".join([f"@{repo_name}/{file}" for file in files])
            else:
                return "\n".join([f"@{file}" for file in files])

        mock_generate_file_search_string.side_effect = (
            generate_search_string_side_effect
        )

        # Call the function
        populate_initial_file_index(github_installation, session)
        session.commit()

        # Verify API calls were made correctly - should be called for both repos during initial creation
        # and then again for each repo during prefixing strategy update (4 total)
        mock_get_repositories.assert_called_once_with("12345")
        assert (
            mock_get_file_tree.call_count == 4
        )  # 2 initial + 2 during prefixing update
        mock_get_file_tree.assert_any_call(
            "12345", "test-user", "test-repo", recursive=True
        )
        mock_get_file_tree.assert_any_call(
            "12345", "test-user", "another-repo", recursive=True
        )
        assert mock_generate_file_search_string.call_count == 4

        # Verify two repository file indexes were created
        repo_indexes = session.query(RepositoryFileIndex).all()
        assert_that(len(repo_indexes), equal_to(2))

        # Verify first repository index
        repo_index_1 = next(
            r for r in repo_indexes if r.repository_full_name == "test-user/test-repo"
        )
        assert_that(
            repo_index_1.github_installation_id, equal_to(github_installation.id)
        )
        assert_that(
            repo_index_1.file_search_string,
            equal_to("@test-repo/README.md\n@test-repo/src/main.py"),
        )
        assert_that(repo_index_1.last_indexed_commit_sha, equal_to("abc123"))

        # Verify second repository index
        repo_index_2 = next(
            r
            for r in repo_indexes
            if r.repository_full_name == "test-user/another-repo"
        )
        assert_that(
            repo_index_2.github_installation_id, equal_to(github_installation.id)
        )
        assert_that(
            repo_index_2.file_search_string,
            equal_to("@another-repo/README.md\n@another-repo/src/main.py"),
        )
        assert_that(repo_index_2.last_indexed_commit_sha, equal_to("abc123"))

    @patch("src.github_app.webhook_controller._update_prefixing_strategy")
    @patch("src.github_app.github_service.GitHubService.get_user_repositories")
    @patch("src.github_app.github_service.GitHubService.get_file_tree")
    @patch("src.github_app.github_service.GitHubService.extract_file_paths")
    def test_populate_initial_file_index_single_repo(
        self,
        mock_generate_search_string: MagicMock,
        mock_get_file_tree,
        mock_get_repositories,
        mock_update_prefixing: MagicMock,
        session,
        user,
        workspace,
    ):
        """Test successful file index population for single repository with @ prefix."""
        # Setup test data
        github_installation = GitHubInstallation(
            user=user,
            installation_id="12345",
            workspace=workspace,
            workspace_id=workspace.id,
            user_id=user.id,
        )
        session.add(github_installation)
        session.commit()
        session.refresh(github_installation)

        # Mock repository data - single repository
        mock_repositories = [
            {"full_name": "test-user/test-repo", "name": "test-repo"},
        ]
        mock_get_repositories.return_value = mock_repositories

        # Mock file tree response
        mock_file_tree = {
            "sha": "def456",
            "tree": [
                {"path": "app.py", "type": "blob"},
                {"path": "config.json", "type": "blob"},
            ],
        }
        mock_get_file_tree.return_value = mock_file_tree

        # Mock search string generation
        mock_generate_search_string.return_value = ["app.py", "config.json"]

        # Call the function
        populate_initial_file_index(github_installation, session)
        session.commit()

        # Verify API calls were made correctly
        mock_get_repositories.assert_called_once_with("12345")
        mock_get_file_tree.assert_called_once_with(
            "12345", "test-user", "test-repo", recursive=True
        )
        mock_generate_search_string.assert_called_once_with(mock_file_tree)

        # Verify prefixing strategy update was called after processing single repo
        mock_update_prefixing.assert_called_once_with("12345", session)

        # Verify single repository file index was created
        repo_index: RepositoryFileIndex = session.query(RepositoryFileIndex).first()
        assert repo_index is not None
        assert_that(repo_index.github_installation_id, equal_to(github_installation.id))
        assert_that(repo_index.repository_full_name, equal_to("test-user/test-repo"))
        assert_that(repo_index.file_search_string, equal_to("@app.py\n@config.json"))
        assert_that(repo_index.last_indexed_commit_sha, equal_to("def456"))

    @patch("src.github_app.webhook_controller._update_prefixing_strategy")
    @patch("src.github_app.github_service.GitHubService.get_user_repositories")
    def test_populate_initial_file_index_no_repositories(
        self,
        mock_get_repositories: MagicMock,
        mock_update_prefixing: MagicMock,
        session: Session,
        user: User,
        workspace: Workspace,
    ):
        """Test graceful handling when no repositories are accessible."""
        # Setup test data
        github_installation = GitHubInstallation(
            user=user,
            installation_id="12345",
            workspace=workspace,
            workspace_id=workspace.id,
            user_id=user.id,
        )
        session.add(github_installation)
        session.commit()
        session.refresh(github_installation)

        # Mock empty repository list
        mock_get_repositories.return_value = []

        # Call the function
        populate_initial_file_index(github_installation, session)
        session.commit()

        # Verify no repository file index was created
        repo_index = session.query(RepositoryFileIndex).first()
        assert_that(repo_index is None)

        # Verify API was called but prefixing update was not (no repos to process)
        mock_get_repositories.assert_called_once_with("12345")
        mock_update_prefixing.assert_not_called()

    @patch("src.github_app.webhook_controller._update_prefixing_strategy")
    @patch("src.github_app.github_service.GitHubService.get_user_repositories")
    @patch("src.github_app.github_service.GitHubService.get_file_tree")
    def test_populate_initial_file_index_api_error(
        self,
        mock_get_file_tree: MagicMock,
        mock_get_repositories: MagicMock,
        mock_update_prefixing: MagicMock,
        session: Session,
        user: User,
        workspace: Workspace,
    ):
        """Test graceful handling when GitHub API returns an error."""
        # Setup test data
        github_installation = GitHubInstallation(
            user=user,
            installation_id="12345",
            workspace=workspace,
            workspace_id=workspace.id,
            user_id=user.id,
        )
        session.add(github_installation)
        session.commit()
        session.refresh(github_installation)

        # Mock repository data
        mock_repositories = [{"full_name": "test-user/test-repo", "name": "test-repo"}]
        mock_get_repositories.return_value = mock_repositories

        # Mock API error response
        mock_get_file_tree.return_value = {"error": "Repository not found"}

        # Call the function
        populate_initial_file_index(github_installation, session)
        session.commit()

        # Verify no repository file index was created due to API error
        repo_index = session.query(RepositoryFileIndex).first()
        assert_that(repo_index is None)

        # Verify API calls were made but prefixing update was not (no successful repos)
        mock_get_repositories.assert_called_once_with("12345")
        mock_get_file_tree.assert_called_once_with(
            "12345", "test-user", "test-repo", recursive=True
        )
        mock_update_prefixing.assert_not_called()

    @patch("src.github_app.webhook_controller._update_prefixing_strategy")
    @patch("src.github_app.github_service.GitHubService.get_user_repositories")
    def test_populate_initial_file_index_exception_handling(
        self,
        mock_get_repositories: MagicMock,
        mock_update_prefixing: MagicMock,
        session: Session,
        user: User,
        workspace: Workspace,
    ):
        """Test that exceptions don't prevent installation completion."""
        # Setup test data
        github_installation = GitHubInstallation(
            user=user,
            installation_id="12345",
            workspace=workspace,
            workspace_id=workspace.id,
            user_id=user.id,
        )
        session.add(github_installation)
        session.commit()
        session.refresh(github_installation)

        # Mock exception in repository fetching
        mock_get_repositories.side_effect = Exception("API rate limit exceeded")

        # Call the function - should not raise exception
        populate_initial_file_index(github_installation, session)
        session.commit()

        # Verify no repository file index was created
        repo_index = session.query(RepositoryFileIndex).first()
        assert_that(repo_index is None)

        # Verify API was called (and failed) but prefixing update was not (no successful repos)
        mock_get_repositories.assert_called_once_with("12345")
        mock_update_prefixing.assert_not_called()

    @patch("src.github_app.controller.populate_initial_file_index")
    @patch("src.github_app.github_service.GitHubService.get_installation_token")
    def test_handle_installation_callback_with_file_indexing(
        self,
        mock_get_token: MagicMock,
        mock_populate_index: MagicMock,
        session: Session,
        user: User,
    ):
        """Test that installation callback calls file index population."""
        # Mock successful token retrieval
        mock_get_token.return_value = {"token": "ghs_valid_token"}

        # Call the function
        response = handle_installation_callback(
            callback_payload=GithubAppInstallationCallback(
                installation_id="12345", code="abc", setup_action="install"
            ),
            user=user,
            session=session,
        )

        # Verify response
        assert_that(response.status_code, equal_to(302))
        assert_that(response.headers.get("location"), equal_to("/account"))

        # Verify installation was created
        loaded_installation = session.query(GitHubInstallation).first()
        assert_that(loaded_installation.installation_id, equal_to("12345"))
        assert_that(loaded_installation.user, equal_to(user))

        # Verify file index population was called
        mock_populate_index.assert_called_once_with(loaded_installation, session)

    @patch("src.github_app.github_service.GitHubService.get_installation_token")
    @patch("src.github_app.github_service.GitHubService.get_user_repositories")
    @patch("src.github_app.github_service.GitHubService.get_file_tree")
    @patch("src.github_app.github_service.GitHubService.extract_file_paths")
    def test_handle_installation_callback_full_integration(
        self,
        mock_generate_search_string: MagicMock,
        mock_get_file_tree: MagicMock,
        mock_get_repositories: MagicMock,
        mock_get_token: MagicMock,
        session: Session,
        user: User,
    ):
        """Test full integration of installation callback with file indexing."""
        # Mock token retrieval
        mock_get_token.return_value = {"token": "ghs_valid_token"}

        # Mock all dependencies
        mock_repositories = [{"full_name": "test-user/test-repo", "name": "test-repo"}]
        mock_get_repositories.return_value = mock_repositories

        mock_file_tree = {
            "sha": "def456",
            "tree": [{"path": "app.py", "type": "blob"}],
        }
        mock_get_file_tree.return_value = mock_file_tree

        mock_generate_search_string.return_value = ["app.py"]

        # Call the function
        response = handle_installation_callback(
            callback_payload=GithubAppInstallationCallback(
                installation_id="67890", code="xyz", setup_action="install"
            ),
            user=user,
            session=session,
        )

        # Verify response
        assert_that(response.status_code, equal_to(302))

        # Verify installation was created
        installation = session.query(GitHubInstallation).first()
        assert_that(installation.installation_id, equal_to("67890"))

        # Verify repository file index was created
        repo_index: RepositoryFileIndex = session.query(RepositoryFileIndex).first()
        assert repo_index is not None
        assert_that(repo_index.github_installation_id, equal_to(installation.id))
        assert_that(repo_index.repository_full_name, equal_to("test-user/test-repo"))
        assert_that(repo_index.file_search_string, equal_to("@app.py"))
        assert_that(repo_index.last_indexed_commit_sha, equal_to("def456"))


class TestHandleInstallationCallbackValidation:
    @patch("src.github_app.controller.populate_initial_file_index")
    @patch("src.github_app.github_service.GitHubService.get_installation_token")
    def test_handle_installation_callback_with_api_validation_success(
        self,
        mock_get_token: MagicMock,
        mock_populate_index: MagicMock,
        session: Session,
        user: User,
    ):
        """Test successful installation callback with GitHub API validation."""
        # Mock successful token retrieval
        mock_get_token.return_value = {
            "token": "ghs_16C7e42F292c6912E7710c838347Ae178B4a",
            "expires_at": "2021-07-11T22:14:10Z",
        }

        response = handle_installation_callback(
            callback_payload=GithubAppInstallationCallback(
                installation_id="valid_installation_id",
                code="abc",
                setup_action="install",
            ),
            user=user,
            session=session,
        )

        # Verify response
        assert_that(response.status_code, equal_to(302))
        assert_that(response.headers.get("location"), equal_to("/account"))

        # Verify API validation was called exactly once
        mock_get_token.assert_called_once_with("valid_installation_id")

        # Verify installation was created
        installation = session.query(GitHubInstallation).first()
        assert_that(installation.installation_id, equal_to("valid_installation_id"))
        assert_that(installation.user, equal_to(user))

    @patch("src.github_app.github_service.GitHubService.get_installation_token")
    def test_handle_installation_callback_with_api_validation_failure(
        self, mock_get_token: MagicMock, session: Session, user: User
    ):
        """Test installation callback with GitHub API validation failure."""
        # Mock token retrieval failure
        mock_get_token.side_effect = Exception("Installation not found")

        with pytest.raises(HTTPException) as exc_info:
            handle_installation_callback(
                callback_payload=GithubAppInstallationCallback(
                    installation_id="invalid_installation_id",
                    code="abc",
                    setup_action="install",
                ),
                user=user,
                session=session,
            )

        # Verify correct error response
        assert_that(exc_info.value.status_code, equal_to(400))
        assert_that(
            exc_info.value.detail,
            equal_to("Invalid installation ID or installation not accessible"),
        )

        # Verify API validation was called
        mock_get_token.assert_called_once_with("invalid_installation_id")

        # Verify no installation was created
        installation = session.query(GitHubInstallation).first()
        assert_that(installation, equal_to(None))

    @patch("src.github_app.controller.populate_initial_file_index")
    @patch("src.github_app.github_service.GitHubService.get_installation_token")
    def test_handle_installation_callback_duplicate_installation_same_user(
        self,
        mock_get_token: MagicMock,
        mock_populate_index: MagicMock,
        session: Session,
        user: User,
    ):
        """Test handling duplicate installation for same user."""
        # Mock successful token retrieval
        mock_get_token.return_value = {"token": "ghs_valid_token"}

        # Create existing installation
        existing_installation = GitHubInstallation(
            user=user, installation_id="duplicate_installation_id"
        )
        session.add(existing_installation)
        session.commit()
        existing_id = existing_installation.id

        response = handle_installation_callback(
            callback_payload=GithubAppInstallationCallback(
                installation_id="duplicate_installation_id",
                code="abc",
                setup_action="install",
            ),
            user=user,
            session=session,
        )

        # Verify response
        assert_that(response.status_code, equal_to(302))

        # Verify no new installation was created, existing one was used
        installations = session.query(GitHubInstallation).all()
        assert_that(len(installations), equal_to(1))
        assert_that(installations[0].id, equal_to(existing_id))
        assert_that(installations[0].user, equal_to(user))

    @patch("src.github_app.controller.populate_initial_file_index")
    @patch("src.github_app.github_service.GitHubService.get_installation_token")
    def test_handle_installation_callback_duplicate_installation_different_user(
        self,
        mock_get_token: MagicMock,
        mock_populate_index: MagicMock,
        session: Session,
        user: User,
        other_user: User,
    ):
        """Test handling duplicate installation for different user."""
        # Mock successful token retrieval
        mock_get_token.return_value = {"token": "ghs_valid_token"}

        # Create existing installation for other user
        existing_installation = GitHubInstallation(
            user=other_user, installation_id="transferred_installation_id"
        )
        session.add(existing_installation)
        session.commit()
        existing_id = existing_installation.id

        response = handle_installation_callback(
            callback_payload=GithubAppInstallationCallback(
                installation_id="transferred_installation_id",
                code="abc",
                setup_action="install",
            ),
            user=user,
            session=session,
        )

        # Verify response
        assert_that(response.status_code, equal_to(302))

        # Verify installation was transferred to new user
        installation = session.query(GitHubInstallation).first()
        assert_that(installation.id, equal_to(existing_id))
        assert_that(installation.user, equal_to(user))
        assert_that(installation.user_id, equal_to(user.id))


class TestGetFileSearchStringForUser:
    """Test the new get_file_search_string_for_user controller function."""

    def test_get_file_search_string_success(
        self, session: Session, user: User, github_installation: GitHubInstallation
    ):
        """Test successful file search string retrieval."""
        from datetime import datetime

        from src.github_app.controller import get_file_search_string_for_user

        # Create a repository file index
        repo_index = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/test-repo",
            file_search_string="src/main.py\nsrc/utils.py\nREADME.md",
            last_indexed_commit_sha="abc123",
            updated_at=datetime.now(),
        )
        session.add(repo_index)
        session.commit()

        # Call the function
        result = get_file_search_string_for_user(user, "owner/test-repo", session)

        # Verify response
        assert_that(result.repository_full_name, equal_to("owner/test-repo"))
        assert_that(
            result.file_search_string, equal_to("src/main.py\nsrc/utils.py\nREADME.md")
        )
        assert_that(result.success, equal_to(True))
        assert_that(result.updated_at, equal_to(repo_index.updated_at))

    def test_get_file_search_string_invalid_format(self, session: Session, user: User):
        """Test function with invalid repository name format."""
        from src.github_app.controller import get_file_search_string_for_user

        # Test various invalid formats
        invalid_formats = ["invalid", "too/many/slashes", "", "no-slash"]

        for invalid_format in invalid_formats:
            with pytest.raises(HTTPException) as exc_info:
                get_file_search_string_for_user(user, invalid_format, session)

            assert_that(exc_info.value.status_code, equal_to(422))
            assert_that(
                exc_info.value.detail,
                equal_to("Repository name must be in 'owner/repo' format"),
            )

    def test_get_file_search_string_no_github_installation(
        self, session: Session, user: User
    ):
        """Test function when user has no GitHub installation."""
        from src.github_app.controller import get_file_search_string_for_user

        with pytest.raises(HTTPException) as exc_info:
            get_file_search_string_for_user(user, "owner/repo", session)

        assert_that(exc_info.value.status_code, equal_to(403))
        assert_that(
            exc_info.value.detail, equal_to("No GitHub installation found for user")
        )

    def test_get_file_search_string_repository_not_found(
        self, session: Session, user: User, github_installation: GitHubInstallation
    ):
        """Test function when repository is not found or not indexed."""
        from src.github_app.controller import get_file_search_string_for_user

        with pytest.raises(HTTPException) as exc_info:
            get_file_search_string_for_user(user, "owner/nonexistent-repo", session)

        assert_that(exc_info.value.status_code, equal_to(404))
        assert_that(
            exc_info.value.detail,
            equal_to("Repository 'owner/nonexistent-repo' not found or not indexed"),
        )

    def test_get_file_search_string_different_user_installation(
        self, session: Session, user: User, other_user: User
    ):
        """Test function when repository belongs to different user's installation."""
        from datetime import datetime

        from src.github_app.controller import get_file_search_string_for_user

        # Create installation for other user
        other_installation = GitHubInstallation(
            user=other_user, installation_id="other-installation"
        )
        session.add(other_installation)
        session.commit()

        # Create repository index for other user's installation
        repo_index = RepositoryFileIndex(
            github_installation_id=other_installation.id,
            repository_full_name="owner/private-repo",
            file_search_string="private/file.py",
            last_indexed_commit_sha="def456",
            updated_at=datetime.now(),
        )
        session.add(repo_index)
        session.commit()

        # User should not be able to access other user's repository
        with pytest.raises(HTTPException) as exc_info:
            get_file_search_string_for_user(user, "owner/private-repo", session)

        assert_that(exc_info.value.status_code, equal_to(403))
        assert_that(
            exc_info.value.detail, equal_to("No GitHub installation found for user")
        )

    def test_get_file_search_string_multiple_repositories(
        self, session: Session, user: User, github_installation: GitHubInstallation
    ):
        """Test function with multiple repositories for same installation."""
        from datetime import datetime

        from src.github_app.controller import get_file_search_string_for_user

        # Create multiple repository file indexes
        repo_index_1 = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/repo-one",
            file_search_string="src/app.py\nREADME.md",
            last_indexed_commit_sha="abc123",
            updated_at=datetime.now(),
        )
        repo_index_2 = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/repo-two",
            file_search_string="lib/utils.py\ndocs/guide.md",
            last_indexed_commit_sha="def456",
            updated_at=datetime.now(),
        )
        session.add_all([repo_index_1, repo_index_2])
        session.commit()

        # Test accessing first repository
        result_1 = get_file_search_string_for_user(user, "owner/repo-one", session)
        assert_that(result_1.repository_full_name, equal_to("owner/repo-one"))
        assert_that(result_1.file_search_string, equal_to("src/app.py\nREADME.md"))

        # Test accessing second repository
        result_2 = get_file_search_string_for_user(user, "owner/repo-two", session)
        assert_that(result_2.repository_full_name, equal_to("owner/repo-two"))
        assert_that(
            result_2.file_search_string, equal_to("lib/utils.py\ndocs/guide.md")
        )


class TestGetAllFileSearchStringsForUser:
    """Test the new get_all_file_search_strings_for_user controller function."""

    def test_get_all_file_search_strings_success(
        self, session: Session, user: User, github_installation: GitHubInstallation
    ):
        """Test successful retrieval of all file search strings."""
        from datetime import datetime

        from src.github_app.controller import get_all_file_search_strings_for_user

        # Create multiple repository file indexes
        repo_index_1 = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/repo-one",
            file_search_string="@repo-one/src/app.py\n@repo-one/README.md",
            last_indexed_commit_sha="abc123",
            updated_at=datetime.now(),
        )
        repo_index_2 = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/repo-two",
            file_search_string="@repo-two/lib/utils.py\n@repo-two/docs/guide.md",
            last_indexed_commit_sha="def456",
            updated_at=datetime.now(),
        )
        session.add_all([repo_index_1, repo_index_2])
        session.commit()

        # Call the function
        result = get_all_file_search_strings_for_user(user, session)

        # Verify response structure
        assert_that(result.total_repositories, equal_to(2))
        assert_that(result.success, equal_to(True))
        assert_that(len(result.repositories), equal_to(2))

        # Verify repositories are sorted by name
        repos = result.repositories
        assert_that(repos[0].repository_full_name, equal_to("owner/repo-one"))
        assert_that(
            repos[0].file_search_string,
            equal_to("@repo-one/src/app.py\n@repo-one/README.md"),
        )
        assert_that(repos[1].repository_full_name, equal_to("owner/repo-two"))
        assert_that(
            repos[1].file_search_string,
            equal_to("@repo-two/lib/utils.py\n@repo-two/docs/guide.md"),
        )

    def test_get_all_file_search_strings_no_repositories(
        self, session: Session, user: User, github_installation: GitHubInstallation
    ):
        """Test function when user has GitHub installation but no repositories."""
        from src.github_app.controller import get_all_file_search_strings_for_user

        # Call the function with no repository indexes
        result = get_all_file_search_strings_for_user(user, session)

        # Verify empty response
        assert_that(result.total_repositories, equal_to(0))
        assert_that(result.success, equal_to(True))
        assert_that(len(result.repositories), equal_to(0))

    def test_get_all_file_search_strings_no_github_installation(
        self, session: Session, user: User
    ):
        """Test function when user has no GitHub installation."""
        from src.github_app.controller import get_all_file_search_strings_for_user

        # Should return empty data instead of raising 403 error
        result = get_all_file_search_strings_for_user(user, session)

        # Verify empty response
        assert_that(result.total_repositories, equal_to(0))
        assert_that(result.success, equal_to(True))
        assert_that(len(result.repositories), equal_to(0))

    def test_get_all_file_search_strings_different_user_installation(
        self, session: Session, user: User, other_user: User
    ):
        """Test function when repositories belong to different user's installation."""
        from datetime import datetime

        from src.github_app.controller import get_all_file_search_strings_for_user

        # Create installation for other user
        other_installation = GitHubInstallation(
            user=other_user, installation_id="other-installation"
        )
        session.add(other_installation)
        session.commit()

        # Create repository index for other user's installation
        repo_index = RepositoryFileIndex(
            github_installation_id=other_installation.id,
            repository_full_name="owner/private-repo",
            file_search_string="@private-repo/private/file.py",
            last_indexed_commit_sha="def456",
            updated_at=datetime.now(),
        )
        session.add(repo_index)
        session.commit()

        # User should not see other user's repositories (returns empty data when no installation)
        result = get_all_file_search_strings_for_user(user, session)

        # Verify empty response since user has no GitHub installation
        assert_that(result.total_repositories, equal_to(0))
        assert_that(result.success, equal_to(True))
        assert_that(len(result.repositories), equal_to(0))

    def test_get_all_file_search_strings_mixed_installations(
        self, session: Session, user: User, other_user: User
    ):
        """Test function returns only user's repositories when multiple installations exist."""
        from datetime import datetime

        from src.github_app.controller import get_all_file_search_strings_for_user

        # Create installation for user
        user_installation = GitHubInstallation(
            user=user, installation_id="user-installation"
        )
        session.add(user_installation)
        session.commit()

        # Create installation for other user
        other_installation = GitHubInstallation(
            user=other_user, installation_id="other-installation"
        )
        session.add(other_installation)
        session.commit()

        # Create repository indexes for both users
        user_repo_index = RepositoryFileIndex(
            github_installation_id=user_installation.id,
            repository_full_name="user/repo",
            file_search_string="@repo/src/main.py",
            last_indexed_commit_sha="abc123",
            updated_at=datetime.now(),
        )
        other_repo_index = RepositoryFileIndex(
            github_installation_id=other_installation.id,
            repository_full_name="other/repo",
            file_search_string="@repo/other/file.py",
            last_indexed_commit_sha="def456",
            updated_at=datetime.now(),
        )
        session.add_all([user_repo_index, other_repo_index])
        session.commit()

        # Call function for user
        result = get_all_file_search_strings_for_user(user, session)

        # Verify only user's repository is returned
        assert_that(result.total_repositories, equal_to(1))
        assert_that(result.success, equal_to(True))
        assert_that(len(result.repositories), equal_to(1))
        assert_that(result.repositories[0].repository_full_name, equal_to("user/repo"))
        assert_that(
            result.repositories[0].file_search_string, equal_to("@repo/src/main.py")
        )


class TestGetRepositoryNamesForUser:
    """Test the get_repository_names_for_user controller function."""

    def test_get_repository_names_success_multiple_repositories(
        self, session: Session, user: User, github_installation: GitHubInstallation
    ):
        """Test successful retrieval of repository names with multiple repositories."""
        from datetime import datetime

        from src.github_app.controller import get_repository_names_for_user

        # Create multiple repository file indexes with different timestamps
        timestamp_1 = datetime(2023, 1, 15, 10, 30, 0)
        timestamp_2 = datetime(2023, 2, 20, 14, 45, 0)

        repo_index_1 = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/zebra-repo",  # Should be last when sorted
            file_search_string="@zebra-repo/src/main.py",
            last_indexed_commit_sha="abc123",
            updated_at=timestamp_1,
        )
        repo_index_2 = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/alpha-repo",  # Should be first when sorted
            file_search_string="@alpha-repo/lib/utils.py",
            last_indexed_commit_sha="def456",
            updated_at=timestamp_2,
        )
        session.add_all([repo_index_1, repo_index_2])
        session.commit()

        # Call the function
        result = get_repository_names_for_user(user, session)

        # Verify response structure
        assert_that(result.total_repositories, equal_to(2))
        assert_that(result.success, equal_to(True))
        assert_that(len(result.repository_names), equal_to(2))
        assert_that(len(result.repository_timestamps), equal_to(2))

        # Verify repositories are sorted alphabetically
        assert_that(result.repository_names[0], equal_to("owner/alpha-repo"))
        assert_that(result.repository_names[1], equal_to("owner/zebra-repo"))

        # Verify timestamp mapping is correct (ISO format)
        assert_that(
            result.repository_timestamps["owner/alpha-repo"],
            equal_to(timestamp_2.isoformat()),
        )
        assert_that(
            result.repository_timestamps["owner/zebra-repo"],
            equal_to(timestamp_1.isoformat()),
        )

    def test_get_repository_names_success_single_repository(
        self, session: Session, user: User, github_installation: GitHubInstallation
    ):
        """Test successful retrieval with only one repository."""
        from datetime import datetime

        from src.github_app.controller import get_repository_names_for_user

        timestamp = datetime(2023, 6, 10, 9, 15, 30)
        repo_index = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/single-repo",
            file_search_string="@single-repo/README.md",
            last_indexed_commit_sha="xyz789",
            updated_at=timestamp,
        )
        session.add(repo_index)
        session.commit()

        # Call the function
        result = get_repository_names_for_user(user, session)

        # Verify response
        assert_that(result.total_repositories, equal_to(1))
        assert_that(result.success, equal_to(True))
        assert_that(len(result.repository_names), equal_to(1))
        assert_that(result.repository_names[0], equal_to("owner/single-repo"))
        assert_that(len(result.repository_timestamps), equal_to(1))
        assert_that(
            result.repository_timestamps["owner/single-repo"],
            equal_to(timestamp.isoformat()),
        )

    def test_get_repository_names_success_no_repositories(
        self, session: Session, user: User, github_installation: GitHubInstallation
    ):
        """Test function when user has GitHub installation but no repositories."""
        from src.github_app.controller import get_repository_names_for_user

        # Call the function with no repository indexes
        result = get_repository_names_for_user(user, session)

        # Verify empty response but success=True
        assert_that(result.total_repositories, equal_to(0))
        assert_that(result.success, equal_to(True))
        assert_that(len(result.repository_names), equal_to(0))
        assert_that(len(result.repository_timestamps), equal_to(0))

    def test_get_repository_names_no_github_installation(
        self, session: Session, user: User
    ):
        """Test function when user has no GitHub installation."""
        from src.github_app.controller import get_repository_names_for_user

        # Should return empty data instead of raising 403 error
        result = get_repository_names_for_user(user, session)

        # Verify empty response but success=True
        assert_that(result.total_repositories, equal_to(0))
        assert_that(result.success, equal_to(True))
        assert_that(len(result.repository_names), equal_to(0))
        assert_that(len(result.repository_timestamps), equal_to(0))

    def test_get_repository_names_different_user_installation(
        self, session: Session, user: User, other_user: User
    ):
        """Test function when repositories belong to different user's installation."""
        from datetime import datetime

        from src.github_app.controller import get_repository_names_for_user

        # Create installation for other user
        other_installation = GitHubInstallation(
            user=other_user, installation_id="other-installation"
        )
        session.add(other_installation)
        session.commit()

        # Create repository index for other user's installation
        repo_index = RepositoryFileIndex(
            github_installation_id=other_installation.id,
            repository_full_name="other-owner/private-repo",
            file_search_string="@private-repo/private/file.py",
            last_indexed_commit_sha="private123",
            updated_at=datetime.now(),
        )
        session.add(repo_index)
        session.commit()

        # User should not see other user's repositories (returns empty data when no installation)
        result = get_repository_names_for_user(user, session)

        # Verify empty response since user has no GitHub installation
        assert_that(result.total_repositories, equal_to(0))
        assert_that(result.success, equal_to(True))
        assert_that(len(result.repository_names), equal_to(0))
        assert_that(len(result.repository_timestamps), equal_to(0))

    def test_get_repository_names_mixed_installations(
        self, session: Session, user: User, other_user: User
    ):
        """Test function returns only user's repositories when multiple installations exist."""
        from datetime import datetime

        from src.github_app.controller import get_repository_names_for_user

        # Create installation for user
        user_installation = GitHubInstallation(
            user=user, installation_id="user-installation"
        )
        session.add(user_installation)
        session.commit()

        # Create installation for other user
        other_installation = GitHubInstallation(
            user=other_user, installation_id="other-installation"
        )
        session.add(other_installation)
        session.commit()

        # Create repository indexes for both users
        user_timestamp = datetime(2023, 3, 15, 12, 0, 0)
        other_timestamp = datetime(2023, 4, 20, 16, 30, 0)

        user_repo_index = RepositoryFileIndex(
            github_installation_id=user_installation.id,
            repository_full_name="user-owner/user-repo",
            file_search_string="@user-repo/src/main.py",
            last_indexed_commit_sha="user123",
            updated_at=user_timestamp,
        )
        other_repo_index = RepositoryFileIndex(
            github_installation_id=other_installation.id,
            repository_full_name="other-owner/other-repo",
            file_search_string="@other-repo/other/file.py",
            last_indexed_commit_sha="other456",
            updated_at=other_timestamp,
        )
        session.add_all([user_repo_index, other_repo_index])
        session.commit()

        # Call function for user
        result = get_repository_names_for_user(user, session)

        # Verify only user's repository is returned
        assert_that(result.total_repositories, equal_to(1))
        assert_that(result.success, equal_to(True))
        assert_that(len(result.repository_names), equal_to(1))
        assert_that(result.repository_names[0], equal_to("user-owner/user-repo"))
        assert_that(len(result.repository_timestamps), equal_to(1))
        assert_that(
            result.repository_timestamps["user-owner/user-repo"],
            equal_to(user_timestamp.isoformat()),
        )

    def test_get_repository_names_timestamp_iso_format_precision(
        self, session: Session, user: User, github_installation: GitHubInstallation
    ):
        """Test that timestamps are correctly converted to ISO format."""
        from datetime import datetime

        from src.github_app.controller import get_repository_names_for_user

        # Create repository with specific timestamp including microseconds
        precise_timestamp = datetime(2023, 7, 4, 15, 30, 45, 123456)
        repo_index = RepositoryFileIndex(
            github_installation_id=github_installation.id,
            repository_full_name="owner/timestamp-test-repo",
            file_search_string="@timestamp-test-repo/file.py",
            last_indexed_commit_sha="timestamp123",
            updated_at=precise_timestamp,
        )
        session.add(repo_index)
        session.commit()

        # Call the function
        result = get_repository_names_for_user(user, session)

        # Verify timestamp conversion preserves precision
        expected_iso = precise_timestamp.isoformat()
        assert_that(
            result.repository_timestamps["owner/timestamp-test-repo"],
            equal_to(expected_iso),
        )

        # Verify the timestamp string is properly formatted ISO
        assert_that(expected_iso, equal_to("2023-07-04T15:30:45.123456"))
