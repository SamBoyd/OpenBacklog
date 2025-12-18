from datetime import datetime, timedelta
from unittest.mock import ANY, patch

from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from fastapi_csrf_protect import CsrfProtect
from hamcrest import assert_that, contains_string, equal_to, has_entries, is_

from src.config import settings
from src.main import app
from src.models import OAuthAccount, User
from src.views import dependency_to_override


class PageTester:
    def __init__(self, html_page):
        self.html_page = html_page
        self.soup = BeautifulSoup(html_page, "html.parser")

    def has_element(self, tag, text) -> bool:
        return bool(self.soup.find(tag, string=text) is not None)


def test_healthcheck(test_client: TestClient):
    response = test_client.get("/healthcheck")
    assert_that(response.status_code, equal_to(200))
    assert_that(response.json(), has_entries({"status": "ok"}))


def test_read_root(test_client: TestClient):
    response = test_client.get("/", follow_redirects=False)
    assert_that(response.status_code, equal_to(302))
    assert_that(response.headers["location"], equal_to(settings.static_site_url))


def test_static_files(test_client: TestClient):
    response = test_client.get("/static/css/main.css")
    assert_that(response.status_code, equal_to(200))


def test_non_existent_page(test_client: TestClient):
    response = test_client.get("/non-existent-page")
    assert_that(response.status_code, equal_to(404))
    assert_that(response.content.decode("utf-8"), contains_string("Page not found"))


def test_auth0_logout_callback_route(test_client: TestClient):
    response = test_client.get("/auth/auth0-logout-callback", follow_redirects=False)

    assert_that(response.status_code, equal_to(307))
    assert_that(response.headers["location"], equal_to("/"))
    # TODO - Ensure the cookie is cleared


def test_index_requires_authentication(test_client_no_user: TestClient):
    response = test_client_no_user.get("/workspace", follow_redirects=False)
    assert response.status_code == 302


@patch(
    "src.views.controller.get_react_app",
    return_value=JSONResponse({"message": "Dashboard"}),
)
def test_index_controller_call(mock_controller, test_client: TestClient):
    response = test_client.get("/workspace", follow_redirects=False)
    assert_that(response.status_code, is_(200))
    assert_that(response.json(), equal_to({"message": "Dashboard"}))
    mock_controller.assert_called_once()


@patch(
    "src.controller.get_react_app",
    return_value=JSONResponse({"message": "Dashboard"}),
)
def test_react_app_controller_call(mock_controller, test_client: TestClient):
    test_client.get("/workspace")
    mock_controller.assert_called_once()


@patch(
    "src.controller.get_react_app",
    return_value=JSONResponse({"message": "Dashboard"}),
)
def test_react_app_controller_call_with_child_route(
    mock_controller, test_client: TestClient
):
    test_client.get("/workspace/child-route/3948348/tasks/3948348")
    mock_controller.assert_called_once()


@patch(
    "src.controller.get_changelog_template",
    return_value=JSONResponse({"message": "Dashboard"}),
)
def test_changelog_controller_call(mock_controller, test_client: TestClient):
    test_client.get("/changelog")
    mock_controller.assert_called_once()


@patch(
    "src.controller.get_support_template",
    return_value=JSONResponse({"message": "Dashboard"}),
)
def test_support_controller_call(mock_controller, test_client: TestClient):
    test_client.get("/support")
    mock_controller.assert_called_once()


@patch(
    "src.controller.get_account_template",
    return_value=JSONResponse({"message": "Dashboard"}),
)
def test_account_controller_call(mock_controller, test_client: TestClient):
    test_client.get("/account")
    mock_controller.assert_called_once()


def test_index_authentication_flow(user: User, test_client: TestClient):
    # Unauthenticated: expect 401
    app.dependency_overrides.pop(dependency_to_override, None)
    response = test_client.get("/workspace", follow_redirects=False)
    assert_that(response.status_code, equal_to(302))

    app.dependency_overrides[dependency_to_override] = lambda: user

    response2 = test_client.get("/workspace", follow_redirects=False)
    assert_that(response2.status_code, equal_to(200))


def test_redirect_for_unauthenticated(test_client: TestClient):
    test_client.app.dependency_overrides.pop(dependency_to_override, None)

    response = test_client.get("/workspace", follow_redirects=False)
    assert_that(response.status_code, equal_to(302))
    assert_that(response.headers["location"], equal_to("/"))


@patch(
    "src.controller.get_profile_picture",
    return_value=JSONResponse({"message": "Dashboard"}),
)
def test_can_get_profile_picture_from_storage(mock_controller, test_client: TestClient):
    test_client.get("/profile-picture/filename.png")
    mock_controller.assert_called_once_with("filename.png")


@patch("src.controller.upload_profile_picture", return_value="filename.png")
def test_update_profile_picture_for_user(mock_controller, test_client: TestClient):
    response = test_client.post("/upload-profile-picture", files={"file": "file"})
    assert_that(response.status_code, equal_to(200))
    mock_controller.assert_called_once()


def test_displays_github_oauth_accounts_if_used(test_client, user, session):
    github_oauth_account = OAuthAccount(
        user=user,
        oauth_name="oauth2",
        account_id="github|123",
        expires_at=(datetime.now() + timedelta(days=1)).timestamp(),
        refresh_token="refresh",
        access_token="access",
        account_email=user.email,
    )

    session.add(github_oauth_account)
    session.commit()

    response = test_client.get("/account")
    assert_that(response.status_code, equal_to(200))
    assert_that(response.text, contains_string("Github"))


def test_displays_google_oauth_accounts_if_used(test_client, user, session):
    google_oauth_account = OAuthAccount(
        user=user,
        oauth_name="oauth2",
        account_id="google|123",
        expires_at=(datetime.now() + timedelta(days=1)).timestamp(),
        refresh_token="refresh",
        access_token="access",
        account_email=user.email,
    )

    session.add(google_oauth_account)
    session.commit()

    response = test_client.get("/account")
    assert_that(response.status_code, equal_to(200))
    assert_that(response.text, contains_string("Google"))


@patch("src.controller.confirm_delete_account")
def test_confirm_delete_account_route(mock_confirm_delete_account, user):
    csrf_protect = CsrfProtect()
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

    app.dependency_overrides[CsrfProtect] = lambda: csrf_protect
    app.dependency_overrides[dependency_to_override] = lambda: user

    client = TestClient(app)
    client.cookies.set("access_token", "dummy")
    client.cookies.set("auth0_jwt", "dummy")
    client.cookies.set("refresh_token", "dummy")
    client.cookies.set("fastapi-csrf-token", signed_token)

    response = client.post(
        "/confirm-delete-account",
        data={"reason": "Found a better alternative", "csrftoken": csrf_token},
        follow_redirects=False,
    )

    assert_that(response.status_code, equal_to(302))
    assert_that(response.headers["location"], equal_to("/"))

    mock_confirm_delete_account.assert_called_once_with(
        user, "Found a better alternative", ANY
    )

    set_cookie = response.headers.get_list("set-cookie")
    for cookie in set_cookie:
        assert "Max-Age=0" in cookie or "expires=" in cookie

    app.dependency_overrides.pop(dependency_to_override, None)
    app.dependency_overrides.pop(CsrfProtect, None)


@patch("src.controller.confirm_delete_account")
def test_confirm_delete_account_route_csrf_error(mock_confirm_delete_account, user):
    csrf_protect = CsrfProtect()
    csrf_token, _ = csrf_protect.generate_csrf_tokens()

    app.dependency_overrides[CsrfProtect] = lambda: csrf_protect
    app.dependency_overrides[dependency_to_override] = lambda: user

    client = TestClient(app)
    client.cookies.set("access_token", "dummy")
    client.cookies.set("auth0_jwt", "dummy")
    client.cookies.set("refresh_token", "dummy")
    client.cookies.set("fastapi-csrf-token", "definitely-not-the-right-token")

    response = client.post(
        "/confirm-delete-account",
        data={"reason": "Found a better alternative", "csrftoken": csrf_token},
        follow_redirects=False,
    )

    assert_that(response.status_code, equal_to(302))
    assert_that(response.headers["location"], equal_to("/account"))

    mock_confirm_delete_account.assert_not_called()
