import base64
import time
from typing import Any, Dict, List, Optional, Union

import jwt
import requests
import sentry_sdk

from src.config import settings


class GitHubService:
    """Service for interacting with GitHub API."""

    @staticmethod
    def _create_jwt_token() -> str:
        """
        Create a JWT token for GitHub App authentication.

        Returns:
            str: The JWT token
        """
        now = int(time.time())
        payload = {
            "iat": now,  # Issued at time
            "exp": now + 60,  # JWT expiration time (1 minute)
            "iss": settings.github_app_id,  # GitHub App ID
        }

        # Create JWT using the private key
        private_key = settings.github_app_private_key.replace("\\n", "\n")
        return jwt.encode(payload, private_key, algorithm="RS256")

    @classmethod
    def get_installation_token(cls, installation_id: str) -> Dict[str, Any]:
        """
        Get a GitHub App installation token for the specified installation ID.

        Args:
            installation_id: The GitHub App installation ID

        Returns:
            dict: The response from GitHub containing the token and other metadata
        """
        jwt_token = cls._create_jwt_token()

        # Request an installation token
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers=headers,
            timeout=settings.internal_request_timeout,
        )

        if response.status_code != 201:
            raise Exception(
                f"Failed to get installation token: {response.status_code} {response.text}"
            )

        return response.json()

    @classmethod
    def fetch_token_for_installation(cls, installation_id: str) -> Dict[str, Any]:
        """
        Fetch a GitHub App installation token for the specified installation ID.

        Args:
            installation_id: The GitHub App installation ID

        Returns:
            dict: A dictionary containing the token and expiration information
        """
        try:
            token_data = cls.get_installation_token(installation_id)
            return {
                "token": token_data["token"],
                "expires_at": token_data["expires_at"],
            }
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return {"error": str(e)}

    @classmethod
    def get_user_repositories(cls, installation_id: str) -> List[Dict[str, Any]]:
        """
        Get a list of repositories accessible to the GitHub App installation.

        Args:
            installation_id: The GitHub App installation ID

        Returns:
            list: A list of repository information dictionaries
        """
        try:
            # Get an installation token
            token_data = cls.get_installation_token(installation_id)
            token = token_data["token"]

            # Use the token to request repositories
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }

            response = requests.get(
                "https://api.github.com/installation/repositories",
                headers=headers,
                timeout=settings.internal_request_timeout,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get repositories: {response.status_code} {response.text}"
                )

            return response.json().get("repositories", [])
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return []

    @classmethod
    def revoke_installation_access(cls, installation_id: str) -> bool:
        """
        Revoke a GitHub App installation access by deleting the installation.

        Args:
            installation_id: The installation ID to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            jwt_token = cls._create_jwt_token()

            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }

            response = requests.delete(
                f"https://api.github.com/app/installations/{installation_id}",
                headers=headers,
                timeout=settings.internal_request_timeout,
            )

            return response.status_code == 204
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return False

    @classmethod
    def _get_auth_headers(cls, installation_id: str) -> Dict[str, str]:
        """
        Get authentication headers for GitHub API requests.

        Args:
            installation_id: The GitHub App installation ID

        Returns:
            Dict[str, str]: Headers with authentication token
        """
        token_data = cls.get_installation_token(installation_id)
        token = token_data["token"]

        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    @classmethod
    def get_repository_metadata(
        cls, installation_id: str, repo_owner: str, repo_name: str
    ) -> Dict[str, Any]:
        """
        Get metadata for a specific repository.

        Args:
            installation_id: The GitHub App installation ID
            repo_owner: The owner of the repository
            repo_name: The name of the repository

        Returns:
            Dict[str, Any]: Repository metadata
        """
        try:
            headers = cls._get_auth_headers(installation_id)

            response = requests.get(
                f"https://api.github.com/repos/{repo_owner}/{repo_name}",
                headers=headers,
                timeout=settings.internal_request_timeout,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get repository metadata: {response.status_code} {response.text}"
                )

            return response.json()
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return {"error": str(e)}

    @classmethod
    def get_file_content(
        cls,
        installation_id: str,
        repo_owner: str,
        repo_name: str,
        file_path: str,
        ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get the content of a specific file from a repository.

        Args:
            installation_id: The GitHub App installation ID
            repo_owner: The owner of the repository
            repo_name: The name of the repository
            file_path: The path to the file within the repository
            ref: The name of the commit/branch/tag (optional)

        Returns:
            Dict[str, Any]: File content and metadata
            Example of the response: https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28#get-repository-content
        """
        try:
            headers = cls._get_auth_headers(installation_id)

            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
            if ref:
                url += f"?ref={ref}"

            response = requests.get(
                url, headers=headers, timeout=settings.internal_request_timeout
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get file content: {response.status_code} {response.text}"
                )

            content_data = response.json()

            # If the content is base64 encoded, decode it
            if (
                isinstance(content_data, dict)
                and content_data.get("encoding") == "base64"
            ):
                content = base64.b64decode(content_data["content"]).decode("utf-8")
                content_data["decoded_content"] = content

            return content_data
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return {"error": str(e)}

    @classmethod
    def get_directory_content(
        cls,
        installation_id: str,
        repo_owner: str,
        repo_name: str,
        directory_path: str = "",
        ref: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get the contents of a directory in a repository.

        Args:
            installation_id: The GitHub App installation ID
            repo_owner: The owner of the repository
            repo_name: The name of the repository
            directory_path: The path to the directory within the repository (default: root)
            ref: The name of the commit/branch/tag (optional)

        Returns:
            List[Dict[str, Any]]: List of files and directories in the specified path
        """
        try:
            headers = cls._get_auth_headers(installation_id)

            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
            if directory_path:
                url += f"/{directory_path}"
            if ref:
                url += f"?ref={ref}"

            response = requests.get(
                url, headers=headers, timeout=settings.internal_request_timeout
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get directory content: {response.status_code} {response.text}"
                )

            return response.json()
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return []

    @classmethod
    def get_file_tree(
        cls,
        installation_id: str,
        repo_owner: str,
        repo_name: str,
        recursive: bool = True,
        ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a tree of files in a repository.

        Args:
            installation_id: The GitHub App installation ID
            repo_owner: The owner of the repository
            repo_name: The name of the repository
            recursive: Whether to get the tree recursively (default: True)
            ref: The name of the commit/branch/tag (optional, default: default branch)

        Returns:
            Dict[str, Any]: Repository file tree
        """
        try:
            headers = cls._get_auth_headers(installation_id)

            # First, get the default branch if ref is not provided
            if not ref:
                repo_data = cls.get_repository_metadata(
                    installation_id, repo_owner, repo_name
                )
                if "error" in repo_data:
                    return {"error": repo_data["error"]}
                ref = repo_data.get("default_branch", "main")

            # Get the latest commit SHA for the specified ref
            response = requests.get(
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{ref}",
                headers=headers,
                timeout=settings.internal_request_timeout,
            )
            if response.status_code != 200:
                raise Exception(
                    f"Failed to get commit: {response.status_code} {response.text}"
                )

            commit_sha = response.json()["sha"]

            # Get the tree using the commit SHA
            recursive_param = "?recursive=1" if recursive else ""
            response = requests.get(
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/trees/{commit_sha}{recursive_param}",
                headers=headers,
                timeout=settings.internal_request_timeout,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get file tree: {response.status_code} {response.text}"
                )

            return response.json()
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return {"error": str(e)}

    @classmethod
    def get_branches(
        cls, installation_id: str, repo_owner: str, repo_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get a list of branches in a repository.

        Args:
            installation_id: The GitHub App installation ID
            repo_owner: The owner of the repository
            repo_name: The name of the repository

        Returns:
            List[Dict[str, Any]]: List of branches
        """
        try:
            headers = cls._get_auth_headers(installation_id)

            response = requests.get(
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/branches",
                headers=headers,
                timeout=settings.internal_request_timeout,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get branches: {response.status_code} {response.text}"
                )

            return response.json()
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return []

    @classmethod
    def extract_file_paths(cls, file_tree_response: Dict[str, Any]) -> List[str]:
        """
        Extract file paths from GitHub's tree API response.

        Extracts only file paths (blobs) from GitHub tree API response and returns them as a
        sorted list for further processing.

        Args:
            file_tree_response: The response from GitHub's git/trees API

        Returns:
            List[str]: Sorted list of file paths

        Example:
            >>> tree_response = {
            ...     "tree": [
            ...         {"path": "src/main.py", "type": "blob"},
            ...         {"path": "README.md", "type": "blob"},
            ...         {"path": "src", "type": "tree"},
            ...     ]
            ... }
            >>> GitHubService.extract_file_paths(tree_response)
            ['README.md', 'src/main.py']
        """
        try:
            file_paths = []
            tree_items = file_tree_response.get("tree", [])

            for item in tree_items:
                if item.get("type") == "blob" and item.get("path"):
                    file_paths.append(item["path"])

            return sorted(file_paths)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return []

    @classmethod
    def generate_file_search_string(
        cls,
        file_tree_response: Dict[str, Any],
        repo_name: str,
        use_repo_prefix: bool = False,
    ) -> str:
        """
        Generate a searchable file string from GitHub's tree API response.

        Transforms GitHub tree API response into a newline-separated string of file paths
        with appropriate @ prefixing for autocomplete functionality.

        Args:
            file_tree_response: The response from GitHub's git/trees API
            repo_name: The name of the repository (used for multi-repo prefixing)
            use_repo_prefix: Whether to prefix with @RepoName/ for multi-repo scenarios

        Returns:
            str: Newline-separated string of prefixed file paths

        Example:
            >>> tree_response = {
            ...     "tree": [
            ...         {"path": "src/main.py", "type": "blob"},
            ...         {"path": "README.md", "type": "blob"},
            ...     ]
            ... }
            >>> GitHubService.generate_file_search_string(tree_response, "myrepo", False)
            '@README.md\\n@src/main.py'
            >>> GitHubService.generate_file_search_string(tree_response, "myrepo", True)
            '@myrepo/README.md\\n@myrepo/src/main.py'
        """
        try:
            # Extract file paths using existing method
            file_paths = cls.extract_file_paths(file_tree_response)

            if not file_paths:
                return ""

            # Apply prefixing based on repository count strategy
            if use_repo_prefix:
                # Multiple repos: prefix with @RepoName/
                prefixed_paths = [f"@{repo_name}/{path}" for path in file_paths]
            else:
                # Single repo: prefix with @
                prefixed_paths = [f"@{path}" for path in file_paths]

            return "\n".join(prefixed_paths)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return ""
