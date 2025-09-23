from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_key

from src.config import settings
from src.github_app.github_service import GitHubService


class TestGitHubService:
    @patch("src.github_app.github_service.jwt.encode")
    @patch("src.github_app.github_service.requests.post")
    def test_get_installation_token(self, mock_post, mock_jwt_encode):
        # Mock the JWT encoding
        mock_jwt_encode.return_value = "mocked.jwt.token"

        # Mock the GitHub API response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "token": "ghs_16C7e42F292c6912E7710c838347Ae178B4a",
            "expires_at": "2021-07-11T22:14:10Z",
            "permissions": {"issues": "write", "contents": "read"},
            "repository_selection": "all",
        }
        mock_post.return_value = mock_response

        # Call the function
        result = GitHubService.get_installation_token("12345")

        # Verify the JWT was created correctly
        mock_jwt_encode.assert_called_once()

        # Verify the request was made correctly
        mock_post.assert_called_with(
            "https://api.github.com/app/installations/12345/access_tokens",
            headers={
                "Authorization": "Bearer mocked.jwt.token",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=settings.internal_request_timeout,
        )

        # Verify the result contains the expected token
        assert_that(result, has_key("token"))
        assert_that(
            result["token"], equal_to("ghs_16C7e42F292c6912E7710c838347Ae178B4a")
        )

    @patch("src.github_app.github_service.GitHubService.get_installation_token")
    def test_fetch_token_for_installation(self, mock_get_installation_token):
        # Mock the installation token response
        mock_get_installation_token.return_value = {
            "token": "ghs_16C7e42F292c6912E7710c838347Ae178B4a",
            "expires_at": "2021-07-11T22:14:10Z",
            "permissions": {"issues": "write", "contents": "read"},
            "repository_selection": "all",
        }

        # Call the function
        result = GitHubService.fetch_token_for_installation("12345")

        # Verify the token was requested with the correct installation ID
        mock_get_installation_token.assert_called_with("12345")

        # Verify the result contains the expected token and expiration
        assert_that(result, has_key("token"))
        assert_that(
            result["token"], equal_to("ghs_16C7e42F292c6912E7710c838347Ae178B4a")
        )
        assert_that(result, has_key("expires_at"))
        assert_that(result["expires_at"], equal_to("2021-07-11T22:14:10Z"))

    @patch("src.github_app.github_service.GitHubService.get_installation_token")
    def test_fetch_token_for_installation_error(self, mock_get_installation_token):
        # Mock an error in the installation token retrieval
        mock_get_installation_token.side_effect = Exception("API rate limit exceeded")

        # Call the function
        result = GitHubService.fetch_token_for_installation("12345")

        # Verify the error is returned
        assert_that(result, has_key("error"))
        assert_that(result["error"], equal_to("API rate limit exceeded"))

    @patch("src.github_app.github_service.GitHubService.get_installation_token")
    @patch("src.github_app.github_service.requests.get")
    def test_get_user_repositories_success(self, mock_get, mock_get_installation_token):
        # Mock the installation token
        mock_get_installation_token.return_value = {
            "token": "ghs_16C7e42F292c6912E7710c838347Ae178B4a",
        }

        # Mock the GitHub API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "repositories": [
                {"name": "repo1", "full_name": "user/repo1"},
                {"name": "repo2", "full_name": "user/repo2"},
            ]
        }
        mock_get.return_value = mock_response

        # Call the function
        result = GitHubService.get_user_repositories("12345")

        # Verify the result contains the expected repositories
        assert_that(len(result), equal_to(2))
        assert_that(result[0]["name"], equal_to("repo1"))
        assert_that(result[1]["name"], equal_to("repo2"))

        # Verify the API call was made correctly
        mock_get.assert_called_with(
            "https://api.github.com/installation/repositories",
            headers={
                "Authorization": "Bearer ghs_16C7e42F292c6912E7710c838347Ae178B4a",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=settings.internal_request_timeout,
        )

    @patch("src.github_app.github_service.GitHubService.get_installation_token")
    @patch("src.github_app.github_service.requests.get")
    def test_get_user_repositories_error(self, mock_get, mock_get_installation_token):
        # Mock the installation token
        mock_get_installation_token.return_value = {
            "token": "ghs_16C7e42F292c6912E7710c838347Ae178B4a",
        }

        # Mock an error response
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Permission denied"
        mock_get.return_value = mock_response

        # Call the function
        result = GitHubService.get_user_repositories("12345")

        # Verify an empty list is returned on error
        assert_that(len(result), equal_to(0))

    @patch("src.github_app.github_service.jwt.encode")
    @patch("src.github_app.github_service.requests.delete")
    def test_revoke_installation_access_success(self, mock_delete, mock_jwt_encode):
        # Mock the JWT encoding
        mock_jwt_encode.return_value = "mocked.jwt.token"

        # Mock a successful response
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        # Call the function
        result = GitHubService.revoke_installation_access("12345")

        # Verify the JWT was created correctly
        mock_jwt_encode.assert_called_once()

        # Verify the request was made correctly
        mock_delete.assert_called_with(
            "https://api.github.com/app/installations/12345",
            headers={
                "Authorization": "Bearer mocked.jwt.token",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=settings.internal_request_timeout,
        )

        # Verify the result is True for success
        assert_that(result, equal_to(True))

    @patch("src.github_app.github_service.jwt.encode")
    @patch("src.github_app.github_service.requests.delete")
    def test_revoke_installation_access_failure(self, mock_delete, mock_jwt_encode):
        # Mock the JWT encoding
        mock_jwt_encode.return_value = "mocked.jwt.token"

        # Mock a failed response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_delete.return_value = mock_response

        # Call the function
        result = GitHubService.revoke_installation_access("12345")

        # Verify the result is False for failure
        assert_that(result, equal_to(False))

    @patch("src.github_app.github_service.jwt.encode")
    @patch("src.github_app.github_service.requests.delete")
    def test_revoke_installation_access_exception(self, mock_delete, mock_jwt_encode):
        # Mock the JWT encoding
        mock_jwt_encode.return_value = "mocked.jwt.token"

        # Mock an exception
        mock_delete.side_effect = Exception("Network error")

        # Call the function
        result = GitHubService.revoke_installation_access("12345")

        # Verify the result is False when an exception occurs
        assert_that(result, equal_to(False))

    @patch("src.github_app.github_service.GitHubService._get_auth_headers")
    @patch("src.github_app.github_service.requests.get")
    def test_get_repository_metadata_success(self, mock_get, mock_get_auth_headers):
        # Mock the auth headers
        mock_get_auth_headers.return_value = {
            "Authorization": "Bearer ghs_token",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Mock the GitHub API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test-repo",
            "full_name": "owner/test-repo",
            "description": "Test repository",
            "default_branch": "main",
            "private": False,
        }
        mock_get.return_value = mock_response

        # Call the function
        result = GitHubService.get_repository_metadata("12345", "owner", "test-repo")

        # Verify the API call was made correctly
        mock_get.assert_called_with(
            "https://api.github.com/repos/owner/test-repo",
            headers=mock_get_auth_headers.return_value,
            timeout=settings.internal_request_timeout,
        )

        # Verify the result contains the expected metadata
        assert_that(result["name"], equal_to("test-repo"))
        assert_that(result["full_name"], equal_to("owner/test-repo"))
        assert_that(result["default_branch"], equal_to("main"))

    @patch("src.github_app.github_service.GitHubService._get_auth_headers")
    @patch("src.github_app.github_service.requests.get")
    def test_get_repository_metadata_error(self, mock_get, mock_get_auth_headers):
        # Mock the auth headers
        mock_get_auth_headers.return_value = {
            "Authorization": "Bearer ghs_token",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Mock an error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        # Call the function
        result = GitHubService.get_repository_metadata(
            "12345", "owner", "nonexistent-repo"
        )

        # Verify the result contains the error
        assert_that(result, has_key("error"))
        assert_that(
            result["error"],
            equal_to("Failed to get repository metadata: 404 Not Found"),
        )

    @patch("src.github_app.github_service.GitHubService._get_auth_headers")
    @patch("src.github_app.github_service.requests.get")
    def test_get_file_content_success(self, mock_get, mock_get_auth_headers):
        # Mock the auth headers
        mock_get_auth_headers.return_value = {
            "Authorization": "Bearer ghs_token",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Mock the GitHub API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "README.md",
            "path": "README.md",
            "sha": "abc123",
            "size": 100,
            "url": "https://api.github.com/repos/owner/repo/contents/README.md",
            "html_url": "https://github.com/owner/repo/blob/main/README.md",
            "git_url": "https://api.github.com/repos/owner/repo/git/blobs/abc123",
            "download_url": "https://raw.githubusercontent.com/owner/repo/main/README.md",
            "type": "file",
            "content": "IyBUZXN0IFJlcG9zaXRvcnkKClRoaXMgaXMgYSB0ZXN0IHJlcG9zaXRvcnku",
            "encoding": "base64",
        }
        mock_get.return_value = mock_response

        # Call the function
        result = GitHubService.get_file_content("12345", "owner", "repo", "README.md")

        # Verify the API call was made correctly
        mock_get.assert_called_with(
            "https://api.github.com/repos/owner/repo/contents/README.md",
            headers=mock_get_auth_headers.return_value,
            timeout=settings.internal_request_timeout,
        )

        # Verify the result contains the expected content
        assert_that(result["name"], equal_to("README.md"))
        assert_that(result["path"], equal_to("README.md"))
        assert_that(result["type"], equal_to("file"))
        assert_that(result, has_key("decoded_content"))
        assert_that(
            result["decoded_content"],
            equal_to("# Test Repository\n\nThis is a test repository."),
        )

    @patch("src.github_app.github_service.GitHubService._get_auth_headers")
    @patch("src.github_app.github_service.requests.get")
    def test_get_file_content_with_ref(self, mock_get, mock_get_auth_headers):
        # Mock the auth headers
        mock_get_auth_headers.return_value = {
            "Authorization": "Bearer ghs_token",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Mock the GitHub API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "README.md",
            "path": "README.md",
            "content": "IyBUZXN0IFJlcG9zaXRvcnkKClRoaXMgaXMgYSB0ZXN0IHJlcG9zaXRvcnku",
            "encoding": "base64",
        }
        mock_get.return_value = mock_response

        # Call the function with a specific ref
        result = GitHubService.get_file_content(
            "12345", "owner", "repo", "README.md", ref="develop"
        )

        # Verify the API call was made correctly with the ref parameter
        mock_get.assert_called_with(
            "https://api.github.com/repos/owner/repo/contents/README.md?ref=develop",
            headers=mock_get_auth_headers.return_value,
            timeout=settings.internal_request_timeout,
        )

    @patch("src.github_app.github_service.GitHubService._get_auth_headers")
    @patch("src.github_app.github_service.requests.get")
    def test_get_file_content_error(self, mock_get, mock_get_auth_headers):
        # Mock the auth headers
        mock_get_auth_headers.return_value = {
            "Authorization": "Bearer ghs_token",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Mock an error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        # Call the function
        result = GitHubService.get_file_content(
            "12345", "owner", "repo", "nonexistent-file.md"
        )

        # Verify the result contains the error
        assert_that(result, has_key("error"))
        assert_that(
            result["error"], equal_to("Failed to get file content: 404 Not Found")
        )

    @patch("src.github_app.github_service.GitHubService._get_auth_headers")
    @patch("src.github_app.github_service.requests.get")
    def test_get_directory_content_success(self, mock_get, mock_get_auth_headers):
        # Mock the auth headers
        mock_get_auth_headers.return_value = {
            "Authorization": "Bearer ghs_token",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Mock the GitHub API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "name": "README.md",
                "path": "README.md",
                "type": "file",
            },
            {
                "name": "src",
                "path": "src",
                "type": "dir",
            },
        ]
        mock_get.return_value = mock_response

        # Call the function
        result = GitHubService.get_directory_content("12345", "owner", "repo")

        # Verify the API call was made correctly
        mock_get.assert_called_with(
            "https://api.github.com/repos/owner/repo/contents",
            headers=mock_get_auth_headers.return_value,
            timeout=settings.internal_request_timeout,
        )

        # Verify the result contains the expected content
        assert_that(len(result), equal_to(2))
        assert_that(result[0]["name"], equal_to("README.md"))
        assert_that(result[0]["type"], equal_to("file"))
        assert_that(result[1]["name"], equal_to("src"))
        assert_that(result[1]["type"], equal_to("dir"))

    @patch("src.github_app.github_service.GitHubService._get_auth_headers")
    @patch("src.github_app.github_service.requests.get")
    def test_get_directory_content_with_path_and_ref(
        self, mock_get, mock_get_auth_headers
    ):
        # Mock the auth headers
        mock_get_auth_headers.return_value = {
            "Authorization": "Bearer ghs_token",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Mock the GitHub API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "name": "file1.py",
                "path": "src/file1.py",
                "type": "file",
            },
            {
                "name": "file2.py",
                "path": "src/file2.py",
                "type": "file",
            },
        ]
        mock_get.return_value = mock_response

        # Call the function with a specific path and ref
        result = GitHubService.get_directory_content(
            "12345", "owner", "repo", "src", "develop"
        )

        # Verify the API call was made correctly with the path and ref parameters
        mock_get.assert_called_with(
            "https://api.github.com/repos/owner/repo/contents/src?ref=develop",
            headers=mock_get_auth_headers.return_value,
            timeout=settings.internal_request_timeout,
        )

        # Verify the result contains the expected content
        assert_that(len(result), equal_to(2))
        assert_that(result[0]["name"], equal_to("file1.py"))
        assert_that(result[1]["name"], equal_to("file2.py"))

    @patch("src.github_app.github_service.GitHubService._get_auth_headers")
    @patch("src.github_app.github_service.requests.get")
    def test_get_directory_content_error(self, mock_get, mock_get_auth_headers):
        # Mock the auth headers
        mock_get_auth_headers.return_value = {
            "Authorization": "Bearer ghs_token",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Mock an error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        # Call the function
        result = GitHubService.get_directory_content(
            "12345", "owner", "repo", "nonexistent-dir"
        )

        # Verify an empty list is returned on error
        assert_that(len(result), equal_to(0))

    @patch("src.github_app.github_service.GitHubService.get_repository_metadata")
    @patch("src.github_app.github_service.GitHubService._get_auth_headers")
    @patch("src.github_app.github_service.requests.get")
    def test_get_file_tree_success(
        self, mock_get, mock_get_auth_headers, mock_get_repo_metadata
    ):
        # Mock the auth headers
        mock_get_auth_headers.return_value = {
            "Authorization": "Bearer ghs_token",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Mock the repository metadata
        mock_get_repo_metadata.return_value = {"default_branch": "main"}

        # Mock the commit response
        mock_commit_response = MagicMock()
        mock_commit_response.status_code = 200
        mock_commit_response.json.return_value = {"sha": "commit-sha-123"}

        # Mock the tree response
        mock_tree_response = MagicMock()
        mock_tree_response.status_code = 200
        mock_tree_response.json.return_value = {
            "sha": "tree-sha-456",
            "tree": [
                {
                    "path": "README.md",
                    "mode": "100644",
                    "type": "blob",
                    "sha": "file-sha-789",
                    "size": 100,
                    "url": "https://api.github.com/repos/owner/repo/git/blobs/file-sha-789",
                },
                {
                    "path": "src",
                    "mode": "040000",
                    "type": "tree",
                    "sha": "dir-sha-abc",
                    "url": "https://api.github.com/repos/owner/repo/git/trees/dir-sha-abc",
                },
            ],
            "truncated": False,
        }

        # Set up the mock to return different responses for different URLs
        def mock_get_side_effect(url, headers, timeout):
            if "commits" in url:
                return mock_commit_response
            elif "trees" in url:
                return mock_tree_response
            return None

        mock_get.side_effect = mock_get_side_effect

        # Call the function
        result = GitHubService.get_file_tree("12345", "owner", "repo")

        # Verify the API calls were made correctly
        mock_get.assert_any_call(
            "https://api.github.com/repos/owner/repo/commits/main",
            headers=mock_get_auth_headers.return_value,
            timeout=settings.internal_request_timeout,
        )
        mock_get.assert_any_call(
            "https://api.github.com/repos/owner/repo/git/trees/commit-sha-123?recursive=1",
            headers=mock_get_auth_headers.return_value,
            timeout=settings.internal_request_timeout,
        )

        # Verify the result contains the expected tree
        assert_that(result["sha"], equal_to("tree-sha-456"))
        assert_that(len(result["tree"]), equal_to(2))
        assert_that(result["tree"][0]["path"], equal_to("README.md"))
        assert_that(result["tree"][1]["path"], equal_to("src"))

    @patch("src.github_app.github_service.GitHubService.get_repository_metadata")
    @patch("src.github_app.github_service.GitHubService._get_auth_headers")
    @patch("src.github_app.github_service.requests.get")
    def test_get_file_tree_with_ref(
        self, mock_get, mock_get_auth_headers, mock_get_repo_metadata
    ):
        # Mock the auth headers
        mock_get_auth_headers.return_value = {
            "Authorization": "Bearer ghs_token",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Mock the commit response
        mock_commit_response = MagicMock()
        mock_commit_response.status_code = 200
        mock_commit_response.json.return_value = {"sha": "commit-sha-123"}

        # Mock the tree response
        mock_tree_response = MagicMock()
        mock_tree_response.status_code = 200
        mock_tree_response.json.return_value = {
            "sha": "tree-sha-456",
            "tree": [
                {
                    "path": "README.md",
                    "type": "blob",
                },
                {
                    "path": "src",
                    "type": "tree",
                },
            ],
        }

        # Set up the mock to return different responses for different URLs
        def mock_get_side_effect(url, headers):
            if "commits" in url:
                return mock_commit_response
            elif "trees" in url:
                return mock_tree_response
            return None

        mock_get.side_effect = mock_get_side_effect

        # Call the function with a specific ref
        result = GitHubService.get_file_tree("12345", "owner", "repo", True, "develop")

        # Verify the API calls were made correctly with the ref parameter
        mock_get.assert_any_call(
            "https://api.github.com/repos/owner/repo/commits/develop",
            headers=mock_get_auth_headers.return_value,
            timeout=settings.internal_request_timeout,
        )

    @patch("src.github_app.github_service.GitHubService.get_repository_metadata")
    @patch("src.github_app.github_service.GitHubService._get_auth_headers")
    @patch("src.github_app.github_service.requests.get")
    def test_get_file_tree_error(
        self, mock_get, mock_get_auth_headers, mock_get_repo_metadata
    ):
        # Mock the auth headers
        mock_get_auth_headers.return_value = {
            "Authorization": "Bearer ghs_token",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Mock the repository metadata
        mock_get_repo_metadata.return_value = {"default_branch": "main"}

        # Mock an error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        # Call the function
        result = GitHubService.get_file_tree("12345", "owner", "nonexistent-repo")

        # Verify the result contains the error
        assert_that(result, has_key("error"))
        assert_that(result["error"], equal_to("Failed to get commit: 404 Not Found"))

    @patch("src.github_app.github_service.GitHubService._get_auth_headers")
    @patch("src.github_app.github_service.requests.get")
    def test_get_branches_success(self, mock_get, mock_get_auth_headers):
        # Mock the auth headers
        mock_get_auth_headers.return_value = {
            "Authorization": "Bearer ghs_token",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Mock the GitHub API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "name": "main",
                "commit": {
                    "sha": "commit-sha-main",
                    "url": "https://api.github.com/repos/owner/repo/commits/commit-sha-main",
                },
                "protected": True,
            },
            {
                "name": "develop",
                "commit": {
                    "sha": "commit-sha-develop",
                    "url": "https://api.github.com/repos/owner/repo/commits/commit-sha-develop",
                },
                "protected": False,
            },
        ]
        mock_get.return_value = mock_response

        # Call the function
        result = GitHubService.get_branches("12345", "owner", "repo")

        # Verify the API call was made correctly
        mock_get.assert_called_with(
            "https://api.github.com/repos/owner/repo/branches",
            headers=mock_get_auth_headers.return_value,
            timeout=settings.internal_request_timeout,
        )

        # Verify the result contains the expected branches
        assert_that(len(result), equal_to(2))
        assert_that(result[0]["name"], equal_to("main"))
        assert_that(result[1]["name"], equal_to("develop"))

    @patch("src.github_app.github_service.GitHubService._get_auth_headers")
    @patch("src.github_app.github_service.requests.get")
    def test_get_branches_error(self, mock_get, mock_get_auth_headers):
        # Mock the auth headers
        mock_get_auth_headers.return_value = {
            "Authorization": "Bearer ghs_token",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Mock an error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        # Call the function
        result = GitHubService.get_branches("12345", "owner", "nonexistent-repo")

        # Verify an empty list is returned on error
        assert_that(len(result), equal_to(0))

    def test_extract_file_paths_success(self):
        # Mock a GitHub tree API response with mixed files and directories
        tree_response = {
            "sha": "tree-sha-456",
            "tree": [
                {
                    "path": "src/main.py",
                    "type": "blob",
                    "sha": "file-sha-1",
                },
                {
                    "path": "README.md",
                    "type": "blob",
                    "sha": "file-sha-2",
                },
                {
                    "path": "src",
                    "type": "tree",
                    "sha": "dir-sha-1",
                },
                {
                    "path": "tests/test_example.py",
                    "type": "blob",
                    "sha": "file-sha-3",
                },
                {
                    "path": "docs",
                    "type": "tree",
                    "sha": "dir-sha-2",
                },
                {
                    "path": "package.json",
                    "type": "blob",
                    "sha": "file-sha-4",
                },
            ],
        }

        # Call the function
        result = GitHubService.extract_file_paths(tree_response)

        # Verify only files are included, sorted alphabetically
        expected = ["README.md", "package.json", "src/main.py", "tests/test_example.py"]
        assert_that(result, equal_to(expected))

    def test_extract_file_paths_empty_tree(self):
        # Mock a response with empty tree
        tree_response = {"sha": "tree-sha-456", "tree": []}

        # Call the function
        result = GitHubService.extract_file_paths(tree_response)

        # Verify empty list is returned
        assert_that(result, equal_to([]))

    def test_extract_file_paths_no_files(self):
        # Mock a response with only directories
        tree_response = {
            "sha": "tree-sha-456",
            "tree": [
                {
                    "path": "src",
                    "type": "tree",
                    "sha": "dir-sha-1",
                },
                {
                    "path": "tests",
                    "type": "tree",
                    "sha": "dir-sha-2",
                },
            ],
        }

        # Call the function
        result = GitHubService.extract_file_paths(tree_response)

        # Verify empty list is returned when no files are present
        assert_that(result, equal_to([]))

    def test_extract_file_paths_missing_tree_key(self):
        # Mock a malformed response without 'tree' key
        tree_response = {"sha": "tree-sha-456"}

        # Call the function
        result = GitHubService.extract_file_paths(tree_response)

        # Verify empty list is returned for malformed input
        assert_that(result, equal_to([]))

    def test_extract_file_paths_missing_path(self):
        # Mock a response with items missing path field
        tree_response = {
            "tree": [
                {
                    "type": "blob",
                    "sha": "file-sha-1",
                    # Missing 'path' field
                },
                {
                    "path": "valid/file.py",
                    "type": "blob",
                    "sha": "file-sha-2",
                },
            ]
        }

        # Call the function
        result = GitHubService.extract_file_paths(tree_response)

        # Verify only valid files with paths are included
        assert_that(result, equal_to(["valid/file.py"]))

    def test_extract_file_paths_malformed_input(self):
        # Test with completely malformed input
        malformed_inputs = [
            None,
            {},
            {"tree": None},
            {"tree": "not-a-list"},
            {"tree": [None]},
            {"tree": ["not-a-dict"]},
        ]

        for malformed_input in malformed_inputs:
            result = GitHubService.extract_file_paths(malformed_input)
            assert_that(result, equal_to([]))

    def test_extract_file_paths_sorting(self):
        # Test sorting behavior with various file names
        tree_response = {
            "tree": [
                {"path": "z-last.py", "type": "blob"},
                {"path": "a-first.py", "type": "blob"},
                {"path": "src/nested/deep.py", "type": "blob"},
                {"path": "README.md", "type": "blob"},
                {"path": "package.json", "type": "blob"},
            ]
        }

        # Call the function
        result = GitHubService.extract_file_paths(tree_response)

        # Verify alphabetical sorting
        expected = [
            "README.md",
            "a-first.py",
            "package.json",
            "src/nested/deep.py",
            "z-last.py",
        ]
        assert_that(result, equal_to(expected))

    def test_generate_file_search_string_single_repo(self):
        # Test single repository mode (no repo prefix)
        tree_response = {
            "tree": [
                {"path": "src/main.py", "type": "blob"},
                {"path": "README.md", "type": "blob"},
                {"path": "src", "type": "tree"},  # Should be excluded
                {"path": "tests/test_main.py", "type": "blob"},
            ]
        }

        # Call the function
        result = GitHubService.generate_file_search_string(
            tree_response, "myrepo", use_repo_prefix=False
        )

        # Verify output format and sorting
        expected = "@README.md\n@src/main.py\n@tests/test_main.py"
        assert_that(result, equal_to(expected))

    def test_generate_file_search_string_multi_repo(self):
        # Test multi-repository mode (with repo prefix)
        tree_response = {
            "tree": [
                {"path": "src/main.py", "type": "blob"},
                {"path": "README.md", "type": "blob"},
            ]
        }

        # Call the function
        result = GitHubService.generate_file_search_string(
            tree_response, "myrepo", use_repo_prefix=True
        )

        # Verify output format with repo prefix
        expected = "@myrepo/README.md\n@myrepo/src/main.py"
        assert_that(result, equal_to(expected))

    def test_generate_file_search_string_empty_tree(self):
        # Test with empty tree
        tree_response = {"tree": []}

        # Call the function
        result = GitHubService.generate_file_search_string(
            tree_response, "myrepo", use_repo_prefix=False
        )

        # Verify empty string is returned
        assert_that(result, equal_to(""))

    def test_generate_file_search_string_no_files(self):
        # Test with only directories (no files)
        tree_response = {
            "tree": [
                {"path": "src", "type": "tree"},
                {"path": "tests", "type": "tree"},
            ]
        }

        # Call the function
        result = GitHubService.generate_file_search_string(
            tree_response, "myrepo", use_repo_prefix=False
        )

        # Verify empty string is returned when no files are present
        assert_that(result, equal_to(""))

    def test_generate_file_search_string_malformed_input(self):
        # Test with malformed input
        malformed_inputs = [
            None,
            {},
            {"tree": None},
            {"tree": "not-a-list"},
        ]

        for malformed_input in malformed_inputs:
            result = GitHubService.generate_file_search_string(
                malformed_input, "myrepo", use_repo_prefix=False
            )
            assert_that(result, equal_to(""))

    def test_generate_file_search_string_special_characters(self):
        # Test with file paths containing special characters
        tree_response = {
            "tree": [
                {"path": "files with spaces.txt", "type": "blob"},
                {"path": "special-chars@#$.py", "type": "blob"},
                {"path": "unicode_文件.txt", "type": "blob"},
            ]
        }

        # Call the function
        result = GitHubService.generate_file_search_string(
            tree_response, "myrepo", use_repo_prefix=False
        )

        # Verify special characters are preserved
        expected = "@files with spaces.txt\n@special-chars@#$.py\n@unicode_文件.txt"
        assert_that(result, equal_to(expected))
