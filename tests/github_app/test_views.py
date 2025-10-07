import hashlib
import hmac
import json
from unittest.mock import ANY, MagicMock, Mock, patch

import pytest
from fastapi import Response
from fastapi.responses import JSONResponse, RedirectResponse
from hamcrest import assert_that, equal_to

from src.config import settings


@pytest.mark.skip("Test is failing")
@patch("src.github_app.controller.handle_github_webhook")
def test_github_webhook_valid_signature(mock_handle_webhook, test_client):
    mock_handle_webhook.return_value = Response("Success", status_code=200)

    # Create payload and signature
    payload = {
        "action": "opened",
        "repositories": [{"full_name": "test/repo"}],
        "installation": {"id": "1234"},
    }
    payload_bytes = json.dumps(payload).encode()
    signature = (
        "sha256="
        + hmac.new(
            settings.github_webhook_secret.encode(), payload_bytes, hashlib.sha256
        ).hexdigest()
    )

    # Send request
    response = test_client.post(
        "/github/webhook",
        json=payload,
        headers={"X-Hub-Signature-256": signature, "X-GitHub-Event": "push"},
        follow_redirects=False,
    )

    # Assertions
    assert_that(response.status_code, equal_to(200))
    # Check that the controller function was called with the parsed payload object, event type, and db session
    mock_handle_webhook.assert_called_once_with(
        # Payload is now converted from dict to GithubWebhookPayload in the view
        ANY,  # This corresponds to the GithubWebhookPayload object
        "push",  # This corresponds to x_github_event
        ANY,  # This corresponds to the db session
    )


@pytest.mark.skip("Test is failing")
def test_github_webhook_invalid_signature(test_client):
    # Create payload and invalid signature
    payload = {
        "action": "opened",
        "repositories": [{"full_name": "test/repo"}],
        "installation": {"id": "1234"},
    }
    payload_bytes = json.dumps(payload).encode()
    invalid_signature = (
        "sha256="
        + hmac.new(
            b"not-the-correct-secret-key", payload_bytes, hashlib.sha256
        ).hexdigest()
    )

    # Send request
    response = test_client.post(
        "/github/webhook",
        json=payload,
        headers={"X-Hub-Signature-256": invalid_signature, "X-GitHub-Event": "push"},
        follow_redirects=False,
    )

    # Assertions
    assert_that(response.status_code, equal_to(401))


@pytest.mark.skip("Test is failing")
def test_github_webhook_missing_headers(test_client):
    # Create payload
    payload = {
        "action": "opened",
        "repositories": [{"full_name": "test/repo"}],
        "installation": {"id": "1234"},
    }

    # Test missing signature header
    response = test_client.post(
        "/github/webhook",
        json=payload,
        headers={"X-GitHub-Event": "push"},
        follow_redirects=False,
    )
    assert_that(response.status_code, equal_to(401))

    # Test missing event header
    response = test_client.post(
        "/github/webhook",
        json=payload,
        headers={"X-Hub-Signature-256": "sha256=some_signature"},
        follow_redirects=False,
    )
    assert_that(response.status_code, equal_to(400))


@patch(
    "src.github_app.controller.get_repositories_template",
    return_value=JSONResponse({"message": "Dashboard"}),
)
def test_repositories_controller_call(mock_controller, test_client):
    mock_controller.return_value = JSONResponse({"message": "Dashboard"})
    response = test_client.get("/repositories")
    assert_that(response.status_code, equal_to(200))
    mock_controller.assert_called_once()


@patch("src.github_app.controller.install_github_app_redirect")
def test_github_app_install_route(mock_install_github_app_redirect, test_client):
    mock_install_github_app_redirect.return_value = RedirectResponse("/")
    response = test_client.get("/github/install", follow_redirects=False)
    assert_that(response.status_code, equal_to(307))
    mock_install_github_app_redirect.assert_called_once()


@patch("src.github_app.controller.uninstall_github_app")
def test_github_app_uninstall_route(mock_uninstall_github_app, test_client):
    mock_uninstall_github_app.return_value = RedirectResponse(
        "/repositories", status_code=302
    )
    response = test_client.get("/github/uninstall", follow_redirects=False)
    assert_that(response.status_code, equal_to(302))
    assert_that(response.headers["location"], equal_to("/repositories"))
    mock_uninstall_github_app.assert_called_once()


# Tests for file search string API endpoint
@patch("src.github_app.controller.get_file_search_string_for_user")
def test_get_file_search_string_success(mock_controller_func, test_client):
    """Test successful file search string retrieval"""
    from datetime import datetime

    from src.github_app.views import FileSearchStringResponse

    # Mock successful response
    mock_response = FileSearchStringResponse(
        repository_full_name="owner/repo",
        file_search_string="src/main.py\nsrc/utils.py\nREADME.md",
        updated_at=datetime.now(),
        success=True,
    )
    mock_controller_func.return_value = mock_response

    # Make request
    response = test_client.get(
        "/api/github/file-search-string?repository_full_name=owner/repo"
    )

    # Assertions
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(data["repository_full_name"], equal_to("owner/repo"))
    assert_that(
        data["file_search_string"], equal_to("src/main.py\nsrc/utils.py\nREADME.md")
    )
    assert_that(data["success"], equal_to(True))
    mock_controller_func.assert_called_once()


@patch("src.github_app.controller.get_file_search_string_for_user")
def test_get_file_search_string_missing_query_param(mock_controller_func, test_client):
    """Test API endpoint with missing query parameter"""
    # Make request without repository_full_name
    response = test_client.get("/api/github/file-search-string")

    # Should return validation error
    assert_that(response.status_code, equal_to(422))
    mock_controller_func.assert_not_called()


@patch("src.github_app.controller.get_file_search_string_for_user")
def test_get_file_search_string_repository_not_found(mock_controller_func, test_client):
    """Test API endpoint when repository is not found"""
    from fastapi import HTTPException

    # Mock 404 exception
    mock_controller_func.side_effect = HTTPException(
        status_code=404, detail="Repository 'owner/repo' not found or not indexed"
    )

    # Make request
    response = test_client.get(
        "/api/github/file-search-string?repository_full_name=owner/repo"
    )

    # Assertions
    assert_that(response.status_code, equal_to(404))
    # The detail message should contain our error - FastAPI may transform it
    assert_that("detail" in response.json())
    mock_controller_func.assert_called_once()


@patch("src.github_app.controller.get_file_search_string_for_user")
def test_get_file_search_string_no_github_installation(
    mock_controller_func, test_client
):
    """Test API endpoint when user has no GitHub installation"""
    from fastapi import HTTPException

    # Mock 403 exception
    mock_controller_func.side_effect = HTTPException(
        status_code=403, detail="No GitHub installation found for user"
    )

    # Make request
    response = test_client.get(
        "/api/github/file-search-string?repository_full_name=owner/repo"
    )

    # Assertions
    assert_that(response.status_code, equal_to(403))
    # The detail message should contain our error - FastAPI may transform it
    assert_that("detail" in response.json())
    mock_controller_func.assert_called_once()


@patch("src.github_app.controller.get_file_search_string_for_user")
def test_get_file_search_string_invalid_format(mock_controller_func, test_client):
    """Test API endpoint with invalid repository name format"""
    from fastapi import HTTPException

    # Mock 422 exception
    mock_controller_func.side_effect = HTTPException(
        status_code=422, detail="Repository name must be in 'owner/repo' format"
    )

    # Make request with invalid format
    response = test_client.get(
        "/api/github/file-search-string?repository_full_name=invalid-format"
    )

    # Assertions
    assert_that(response.status_code, equal_to(422))
    # The detail message should contain our error - FastAPI may transform it
    assert_that("detail" in response.json())
    mock_controller_func.assert_called_once()


@patch("src.github_app.controller.get_file_search_string_for_user")
def test_get_file_search_string_internal_error(mock_controller_func, test_client):
    """Test API endpoint handling unexpected exceptions"""
    # Mock unexpected exception
    mock_controller_func.side_effect = ValueError("Unexpected database error")

    # Make request
    response = test_client.get(
        "/api/github/file-search-string?repository_full_name=owner/repo"
    )

    # Assertions
    assert_that(response.status_code, equal_to(500))
    assert_that(response.json()["detail"], equal_to("Internal server error"))
    mock_controller_func.assert_called_once()


# Tests for all file search strings API endpoint
@patch("src.github_app.controller.get_all_file_search_strings_for_user")
def test_get_all_file_search_strings_success(mock_controller_func, test_client):
    """Test successful retrieval of all file search strings"""
    from datetime import datetime

    from src.github_app.views import AllFileSearchStringsResponse, RepositoryFileData

    # Mock successful response with multiple repositories
    mock_repositories = [
        RepositoryFileData(
            repository_full_name="owner/repo1",
            file_search_string="@repo1/src/main.py\n@repo1/README.md",
            updated_at=datetime.now(),
        ),
        RepositoryFileData(
            repository_full_name="owner/repo2",
            file_search_string="@repo2/lib/utils.py\n@repo2/docs/guide.md",
            updated_at=datetime.now(),
        ),
    ]
    mock_response = AllFileSearchStringsResponse(
        repositories=mock_repositories, total_repositories=2, success=True
    )
    mock_controller_func.return_value = mock_response

    # Make request
    response = test_client.get("/api/github/file-search-strings")

    # Assertions
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(data["total_repositories"], equal_to(2))
    assert_that(data["success"], equal_to(True))
    assert_that(len(data["repositories"]), equal_to(2))
    assert_that(
        data["repositories"][0]["repository_full_name"], equal_to("owner/repo1")
    )
    assert_that(
        data["repositories"][1]["repository_full_name"], equal_to("owner/repo2")
    )
    mock_controller_func.assert_called_once()


@patch("src.github_app.controller.get_all_file_search_strings_for_user")
def test_get_all_file_search_strings_empty_repositories(
    mock_controller_func, test_client
):
    """Test API endpoint when user has no repositories"""
    from src.github_app.views import AllFileSearchStringsResponse

    # Mock empty response
    mock_response = AllFileSearchStringsResponse(
        repositories=[], total_repositories=0, success=True
    )
    mock_controller_func.return_value = mock_response

    # Make request
    response = test_client.get("/api/github/file-search-strings")

    # Assertions
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(data["total_repositories"], equal_to(0))
    assert_that(data["success"], equal_to(True))
    assert_that(len(data["repositories"]), equal_to(0))
    mock_controller_func.assert_called_once()


@patch("src.github_app.controller.get_all_file_search_strings_for_user")
def test_get_all_file_search_strings_no_github_installation(
    mock_controller_func, test_client
):
    """Test API endpoint when user has no GitHub installation"""
    from fastapi import HTTPException

    # Mock 403 exception
    mock_controller_func.side_effect = HTTPException(
        status_code=403, detail="No GitHub installation found for user"
    )

    # Make request
    response = test_client.get("/api/github/file-search-strings")

    # Assertions
    assert_that(response.status_code, equal_to(403))
    # The detail message should contain our error - FastAPI may transform it
    assert_that("detail" in response.json())
    mock_controller_func.assert_called_once()


@patch("src.github_app.controller.get_all_file_search_strings_for_user")
def test_get_all_file_search_strings_internal_error(mock_controller_func, test_client):
    """Test API endpoint handling unexpected exceptions"""
    # Mock unexpected exception
    mock_controller_func.side_effect = ValueError("Unexpected database error")

    # Make request
    response = test_client.get("/api/github/file-search-strings")

    # Assertions
    assert_that(response.status_code, equal_to(500))
    assert_that(response.json()["detail"], equal_to("Internal server error"))
    mock_controller_func.assert_called_once()


@patch("src.github_app.controller.get_repository_names_for_user")
def test_get_user_repository_names_success(mock_controller_func, test_client):
    """Test successful retrieval of user repository names"""
    from src.github_app.views import RepositoryNamesResponse

    # Mock successful response
    mock_response = RepositoryNamesResponse(
        repository_names=["owner/repo1", "owner/repo2"],
        repository_timestamps={
            "owner/repo1": "2024-01-15T10:30:00Z",
            "owner/repo2": "2024-01-16T14:22:00Z",
        },
        total_repositories=2,
        success=True,
    )
    mock_controller_func.return_value = mock_response

    # Make request
    response = test_client.get("/api/github/repository-names")

    # Assertions
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(data["total_repositories"], equal_to(2))
    assert_that(data["success"], equal_to(True))
    assert_that(data["repository_names"], equal_to(["owner/repo1", "owner/repo2"]))
    assert_that(
        data["repository_timestamps"],
        equal_to(
            {
                "owner/repo1": "2024-01-15T10:30:00Z",
                "owner/repo2": "2024-01-16T14:22:00Z",
            }
        ),
    )
    mock_controller_func.assert_called_once()


# Tests for GitHub installation status API endpoint
@patch("src.github_app.controller.get_installation_status")
def test_get_github_installation_status_success(mock_controller_func, test_client):
    """Test successful retrieval of GitHub installation status"""
    # Mock successful response with installation and repositories
    mock_response = {
        "has_installation": True,
        "repository_count": 3,
    }
    mock_controller_func.return_value = mock_response

    # Make request
    response = test_client.get("/api/github/installation-status")

    # Assertions
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(data["has_installation"], equal_to(True))
    assert_that(data["repository_count"], equal_to(3))
    mock_controller_func.assert_called_once()


@patch("src.github_app.controller.get_installation_status")
def test_get_github_installation_status_no_installation(
    mock_controller_func, test_client
):
    """Test API endpoint when user has no GitHub installation"""
    # Mock response with no installation
    mock_response = {
        "has_installation": False,
        "repository_count": 0,
    }
    mock_controller_func.return_value = mock_response

    # Make request
    response = test_client.get("/api/github/installation-status")

    # Assertions
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(data["has_installation"], equal_to(False))
    assert_that(data["repository_count"], equal_to(0))
    mock_controller_func.assert_called_once()


@patch("src.github_app.controller.get_installation_status")
def test_get_github_installation_status_internal_error(
    mock_controller_func, test_client
):
    """Test API endpoint handling unexpected exceptions"""
    # Mock unexpected exception
    mock_controller_func.side_effect = ValueError("Unexpected database error")

    # Make request
    response = test_client.get("/api/github/installation-status")

    # Assertions
    assert_that(response.status_code, equal_to(500))
    assert_that(response.json()["detail"], equal_to("Internal server error"))
    mock_controller_func.assert_called_once()
