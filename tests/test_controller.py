import datetime
from unittest.mock import ANY, MagicMock, patch

import pytest
from fastapi.responses import HTMLResponse
from freezegun import freeze_time
from hamcrest import assert_that, contains_string, equal_to, is_
from starlette.datastructures import Headers, UploadFile

from src.api import WorkspaceUpdate
from src.config import settings
from src.controller import (
    PARAMS_FOR_LOGIN_SCRIPT,
    confirm_delete_account,
    copy_auth0_provided_profile_picture,
    delete_workspace,
    get_account_template,
    get_changelog_template,
    get_profile_picture,
    get_react_app,
    update_user,
    update_workspace,
    upload_profile_picture,
)
from src.models import GitHubInstallation, OAuthAccount, User, Workspace


@patch(
    "src.main.templates.TemplateResponse", return_value=HTMLResponse("<html></html>")
)
def test_get_react_app_template(mock_template_response, user):
    request = MagicMock()
    with freeze_time("2025-02-28"):
        result = get_react_app(request, user)
        mock_template_response.assert_called_once_with(
            request,
            "pages/app.html",
            {"user": user, "main_js_path": ANY},
        )
        assert isinstance(result, HTMLResponse)


@patch(
    "src.main.templates.TemplateResponse", return_value=HTMLResponse("<html></html>")
)
def test_get_changelog_template(mock_template_response, user):
    request = MagicMock()
    result = get_changelog_template(request, user)
    mock_template_response.assert_called_once_with(
        request, "pages/changelog.html", {"user": user, "request": request}
    )
    assert isinstance(result, HTMLResponse)


@patch(
    "src.main.templates.TemplateResponse", return_value=HTMLResponse("<html></html>")
)
def test_get_account_template(mock_template_response, user, workspace, session):
    oauth_accounts = (
        session.query(OAuthAccount).filter(OAuthAccount.user_id == user.id).all()
    )

    request = MagicMock()
    result = get_account_template(request, user, session)

    mock_template_response.assert_called_once_with(
        request,
        "pages/account.html",
        {
            "user": user,
            "oauth_accounts": oauth_accounts,
            "workspaces": [workspace],
            "mcp_server_domain": settings.mcp_server_domain,
            "has_github_installation": False,
            "repositories": [],
        },
    )
    assert isinstance(result, HTMLResponse)


@patch(
    "src.main.templates.TemplateResponse", return_value=HTMLResponse("<html></html>")
)
@patch("src.controller.GitHubService.get_user_repositories", return_value=[])
def test_get_account_template_with_github_installation(
    mock_get_user_repositories, mock_template_response, user, workspace, session
):
    oauth_accounts = (
        session.query(OAuthAccount).filter(OAuthAccount.user_id == user.id).all()
    )

    github_installation = GitHubInstallation(
        user=user,
        workspace=workspace,
        workspace_id=workspace.id,
        user_id=user.id,
        installation_id="12345",
    )
    session.add(github_installation)
    session.commit()
    session.refresh(github_installation)

    mock_get_user_repositories.return_value = [{"name": "test-repo"}]

    request = MagicMock()
    result = get_account_template(request, user, session)

    mock_template_response.assert_called_once_with(
        request,
        "pages/account.html",
        {
            "user": user,
            "oauth_accounts": oauth_accounts,
            "workspaces": [workspace],
            "mcp_server_domain": settings.mcp_server_domain,
            "has_github_installation": True,
            "repositories": [{"name": "test-repo"}],
        },
    )
    assert isinstance(result, HTMLResponse)


@patch(
    "src.controller.storage_service.get_profile_picture", return_value="temp_filepath"
)
def test_get_profile_picture_returns_file_from_storage_service(
    mock_get_profile_picture,
):
    response = get_profile_picture("filename")

    mock_get_profile_picture.assert_called_once_with("filename")

    assert_that(response.path, equal_to("temp_filepath"))


@patch(
    "src.controller.storage_service.upload_profile_picture",
    return_value="temp_filepath",
)
def test_upload_profile_picture(mock_storage_upload, user):
    mock_storage_upload.return_value = "temp_filepath"
    mock_file = UploadFile(
        file=MagicMock(),
        filename="test.png",
        headers=Headers({"content-type": "image/png"}),
        size=1024 * 1024,
    )

    response = upload_profile_picture(user, mock_file, db=MagicMock())

    mock_storage_upload.assert_called_once_with(user, mock_file.file)
    assert_that(response.status_code, equal_to(201))

    assert_that(user.profile_picture_url, equal_to("temp_filepath"))


@patch(
    "src.controller.storage_service.upload_profile_picture",
    return_value="temp_filepath",
)
def test_profile_picture_max_size(mock_storage_upload, user):
    mock_storage_upload.return_value = "temp_filepath"
    mock_file = UploadFile(
        file=MagicMock(),
        filename="test.png",
        headers=Headers({"content-type": "image/png"}),
        size=1024 * 1024 * 3,  # 3MB
    )

    response = upload_profile_picture(user, mock_file, db=MagicMock())
    mock_storage_upload.assert_not_called()

    assert_that(response.status_code, equal_to(400))


@patch(
    "src.controller.storage_service.upload_profile_picture",
    return_value="temp_filepath",
)
def test_profile_picture_must_be_png(mock_storage_upload, user):
    mock_storage_upload.return_value = "temp_filepath"
    mock_file = UploadFile(
        file=MagicMock(),
        filename="test.jpg",
        headers=Headers({"content-type": "image/jpg"}),
        size=1024 * 1024,  # 3MB
    )

    response = upload_profile_picture(user, mock_file, db=MagicMock())
    mock_storage_upload.assert_not_called()

    assert_that(response.status_code, equal_to(400))


@patch(
    "src.controller.storage_service.upload_profile_picture", return_value="new_filename"
)
@patch("src.controller.requests.get")
def test_copy_auth0_provided_profile_picture_success(
    mock_requests_get, mock_upload, user
):
    # Setup: user with default profile picture to trigger copy.
    user.profile_picture_url = settings.default_profile_picture
    profile_picture_url = "https://example.com/pic.png"

    # Simulate a successful download.
    response_mock = MagicMock()
    response_mock.status_code = 200
    response_mock.content = b"image_data"
    mock_requests_get.return_value = response_mock

    # Use a MagicMock for the db session with merge, commit, refresh.
    db = MagicMock()
    db.merge.return_value = user

    copy_auth0_provided_profile_picture(user, profile_picture_url, db)

    mock_requests_get.assert_called_once_with(profile_picture_url, timeout=15)
    mock_upload.assert_called_once()

    # Assert the user profile_picture_url is updated.
    assert user.profile_picture_url == "new_filename"
    db.merge.assert_called_once_with(user)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(user)


@patch("src.controller.storage_service.upload_profile_picture")
@patch("src.controller.requests.get")
def test_copy_auth0_provided_profile_picture_failed_download(
    mock_requests_get, mock_upload, user
):
    # Setup: user with default profile picture to trigger copy.
    user.profile_picture_url = settings.default_profile_picture
    profile_picture_url = "https://example.com/pic.png"

    # Simulate a failed download.
    response_mock = MagicMock()
    response_mock.status_code = 404
    mock_requests_get.return_value = response_mock

    db = MagicMock()

    copy_auth0_provided_profile_picture(user, profile_picture_url, db)

    mock_requests_get.assert_called_once_with(profile_picture_url, timeout=15)
    mock_upload.assert_not_called()
    # Assert that no changes have been made to the user's profile picture.
    assert user.profile_picture_url == settings.default_profile_picture


def test_update_user():
    user = MagicMock()
    db = MagicMock()
    update_user(user, "John Doe", db)

    assert_that(user.name, equal_to("John Doe"))


def test_confirm_delete_account_function(user, session, capsys):
    # Add user to session for deletion simulation
    session.add(user)
    session.commit()
    # Call the function
    confirm_delete_account(user, "Privacy concerns", session)
    # Verify that the user was deleted from the session.
    # In a real test, you would query the db; here we assume session.delete was called.
    captured = capsys.readouterr().out
    assert f"Deleting user {user.id} because: Privacy concerns" in captured


def test_account_settings_displays_workspace_management(test_client, user, session):
    workspace = Workspace(
        user=user,
        name="User Workspace",
        description="Workspace description",
    )
    session.add(workspace)
    session.commit()
    session.refresh(workspace)

    response = test_client.get("/account")
    assert_that(response.status_code, equal_to(200))
    assert_that(response.text, contains_string("User Workspace"))


def test_update_workspace_success(user, session):
    # Set up a test workspace
    workspace = Workspace(
        user=user,
        name="Original Name",
        description="Original description",
        icon="original-icon",
    )
    session.add(workspace)
    session.commit()
    session.refresh(workspace)

    # Create update data
    workspace_update = WorkspaceUpdate(
        id=str(workspace.id),
        name="Updated Name",
        description="Updated description",
        icon="new-icon",
    )

    # Call function being tested
    updated_workspace = update_workspace(user, workspace_update, session)

    # Verify the workspace was updated correctly
    assert_that(updated_workspace.name, equal_to("Updated Name"))
    assert_that(updated_workspace.description, equal_to("Updated description"))
    assert_that(updated_workspace.icon, equal_to("new-icon"))


def test_update_workspace_with_minimal_changes(user, session):
    # Set up a test workspace
    workspace = Workspace(
        user=user,
        name="Original Name",
        description="Original description",
        icon="original-icon",
    )
    session.add(workspace)
    session.commit()
    session.refresh(workspace)

    # Create update with only name (keeping other fields as None)
    workspace_update = WorkspaceUpdate(
        id=str(workspace.id), name="Updated Name Only", description=None, icon=None
    )

    # Call function being tested
    updated_workspace = update_workspace(user, workspace_update, session)

    # Verify only name was updated
    assert_that(updated_workspace.name, equal_to("Updated Name Only"))
    assert_that(updated_workspace.description, equal_to("Original description"))
    assert_that(updated_workspace.icon, equal_to("original-icon"))


def test_update_workspace_wrong_user(user, session):
    # Create another user
    another_user = User(
        name="Anthony Stevenson",
        email="another@gmail.com",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False,
        is_verified=True,
        last_logged_in=datetime.datetime.now(),
    )
    session.add(another_user)
    session.commit()
    session.refresh(another_user)

    # Set up a test workspace for the other user
    workspace = Workspace(
        user_id=another_user.id,  # Belongs to another user
        name="Original Name",
        description="Original description",
    )
    session.add(workspace)
    session.commit()
    session.refresh(workspace)

    # Create update data
    workspace_update = WorkspaceUpdate(
        id=str(workspace.id), name="Updated Name", description="Updated description"
    )

    # Verify the function raises a ValueError when the original user tries to update it
    with pytest.raises(ValueError) as excinfo:
        update_workspace(user, workspace_update, session)

    assert "not found" in str(excinfo.value)


def test_delete_workspace(user, session):
    # Set up a test workspace
    workspace = Workspace(
        user=user,
        name="Workspace to delete",
        description="Description of workspace to delete",
    )
    session.add(workspace)
    session.commit()
    session.refresh(workspace)

    # Call function being tested
    delete_workspace(user, str(workspace.id), session)

    # Verify the workspace was deleted
    assert_that(
        session.query(Workspace).filter(Workspace.id == workspace.id).first(), is_(None)
    )
